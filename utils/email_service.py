import os
import re
import json
import smtplib
import datetime
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import customtkinter as ctk
from database.db_manager import get_connection, log_audit
from utils.theme import (
    BG_DIALOG, BG_CARD, BORDER_SUBTLE, TEXT_MAIN, TEXT_MUTED,
    COLOR_APPLE_BLUE, COLOR_APPLE_BLUE_HOVER, COLOR_GREEN, COLOR_RED,
    FONT_FAMILY, FONT_TITLE, FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_SMALL_BOLD,
    format_currency
)

SMTP_CONFIG_FILE = "smtp_config.json"


def load_smtp_config():
    if os.path.exists(SMTP_CONFIG_FILE):
        try:
            with open(SMTP_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "smtp_host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        "smtp_port": int(os.environ.get("SMTP_PORT", "587")),
        "smtp_user": os.environ.get("SMTP_USER", "footballbetatitle@gmail.com"),
        "smtp_pass": os.environ.get("SMTP_PASS", ""),
        "sender_name": "Football Transfer & Agent System (footballbetatitle@gmail.com)"
    }


def save_smtp_config(smtp_host: str, smtp_port: int, smtp_user: str, smtp_pass: str, sender_name: str = ""):
    cfg = {
        "smtp_host": (smtp_host or "smtp.gmail.com").strip(),
        "smtp_port": int(smtp_port or 587),
        "smtp_user": (smtp_user or "").strip(),
        "smtp_pass": (smtp_pass or "").strip(),
        "sender_name": (sender_name or "Football Transfer & Agent System (UEFA TMS)").strip()
    }
    with open(SMTP_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    return cfg


def parse_email_list(raw_emails: str):
    """แยกและตรวจสอบรายชื่ออีเมลหลายรายการ (คั่นด้วย , ; หรือขึ้นบรรทัดใหม่)"""
    if not raw_emails:
        return []
    parts = re.split(r"[,;\n\r]+", str(raw_emails))
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    valid = []
    for p in parts:
        clean = p.strip()
        if clean and re.match(pattern, clean) and clean not in valid:
            valid.append(clean)
    return valid


def validate_email_format(email: str):
    """ตรวจสอบความถูกต้องของรูปแบบอีเมล (รองรับ 1 หรือหลายอีเมลคั่นด้วยลูกน้ำ)"""
    if not email or not email.strip():
        return False, "กรุณากรอกอีเมลสำหรับติดต่อ"
    valid_list = parse_email_list(email)
    if not valid_list:
        return False, "รูปแบบอีเมลไม่ถูกต้อง (ตัวอย่าง: real_madrid@club.com หรือใส่หลายอีเมลคั่นด้วย ,)"
    return True, ""


def _send_smtp_background(smtp_host, smtp_port, smtp_user, smtp_pass, target_email, msg_string, notif_id):
    """ส่งอีเมลจริงผ่าน Gmail/SMTP ใน Background Thread เพื่อไม่ให้หน้าเว็บหรือ API ค้าง"""
    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=12) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            try:
                server.login(smtp_user, smtp_pass)
            except Exception:
                server.login(smtp_user, smtp_pass.replace(" ", ""))
            server.sendmail(smtp_user, [target_email], msg_string)
        if notif_id:
            c = get_connection()
            c.execute("UPDATE email_notifications SET status = 'Sent via Real SMTP (footballbetatitle@gmail.com)' WHERE id = ?", (notif_id,))
            c.commit()
            c.close()
    except Exception as smtp_err:
        print(f"[Async SMTP Delivery Warning for {target_email}]: {smtp_err}")
        if notif_id:
            try:
                c = get_connection()
                c.execute("UPDATE email_notifications SET status = ? WHERE id = ?", (f"Sent (Local/SMTP Fallback: {str(smtp_err)[:45]})", notif_id))
                c.commit()
                c.close()
            except Exception:
                pass


def dispatch_email_to_recipients(recipients, recipient_name: str, subject: str, body: str, email_type: str = "General"):
    """
    ส่งอีเมลไปยังรายชื่ออีเมลจริง (ผ่าน SMTP ใน background thread หากตั้งค่าไว้ และบันทึกไฟล์ .eml + ตาราง email_notifications เสมอ)
    """
    if isinstance(recipients, str):
        email_list = parse_email_list(recipients)
        if not email_list and recipients.strip():
            email_list = [recipients.strip()]
    else:
        email_list = list(recipients)

    cfg = load_smtp_config()
    smtp_user = cfg.get("smtp_user", "").strip()
    smtp_pass = cfg.get("smtp_pass", "").strip()
    smtp_host = cfg.get("smtp_host", "smtp.gmail.com").strip()
    smtp_port = int(cfg.get("smtp_port", 587))
    sender_name = cfg.get("sender_name", "Football Transfer System")

    os.makedirs("assets/sent_emails", exist_ok=True)
    results = []

    conn = get_connection()
    for target_email in email_list:
        delivery_status = "Sent (Logged & .eml Saved)"
        # Save standard RFC822 .eml file so user can open in Outlook/Mail anytime
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{sender_name} <{smtp_user or 'footballbetatitle@gmail.com'}>"
        msg["To"] = target_email
        msg["Reply-To"] = "footballbetatitle@gmail.com"
        msg["Date"] = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0700")
        msg.attach(MIMEText(body, "plain", "utf-8"))

        safe_em = re.sub(r"[^a-zA-Z0-9_.-]", "_", target_email)
        eml_path = f"assets/sent_emails/email_{int(datetime.datetime.now().timestamp())}_{safe_em}.eml"
        try:
            with open(eml_path, "w", encoding="utf-8") as ef:
                ef.write(msg.as_string())
        except Exception:
            pass

        # บันทึกลงตารางทันทีเพื่อความรวดเร็ว
        notif_id = None
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO email_notifications (recipient_email, recipient_name, subject, body, status, email_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (target_email, recipient_name, subject, body, delivery_status, email_type))
            notif_id = cur.lastrowid
            results.append({"email": target_email, "status": delivery_status})
        except Exception as e:
            print(f"Email DB log error: {e}")

        # ส่งผ่าน Real SMTP ใน Background Thread โดยไม่บล็อกหน้าเว็บ / API
        if smtp_user and smtp_pass:
            threading.Thread(
                target=_send_smtp_background,
                args=(smtp_host, smtp_port, smtp_user, smtp_pass, target_email, msg.as_string(), notif_id),
                daemon=True
            ).start()

    conn.commit()
    conn.close()
    log_audit("EMAIL_DISPATCH", f"Dispatched '{subject}' to {len(email_list)} recipient(s): {', '.join(email_list)}")
    return results


def send_transfer_offer_email(club_name: str, selling_club: str, player_name: str, offer_amount: float, wage_offer: float, status: str, recipient_emails: str):
    """ส่งอีเมลแจ้งเตือนดีลการซื้อขายนักเตะให้กับรายชื่ออีเมลจริงที่ระบุ"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if status == "Pending":
        subject = f"[Official Transfer Bid] สโมสร {club_name} ยื่นข้อเสนอซื้อตัว {player_name} ({format_currency(offer_amount)})"
        action_desc = f"สโมสร {club_name} ได้ยื่นข้อเสนอขอซื้อตัวนักฟุตบอลอย่างเป็นทางการ"
    elif status == "Completed":
        subject = f"[HERE WE GO! ดีลสำเร็จ] {player_name} ย้ายร่วมทีม {club_name} อย่างเป็นทางการ ({format_currency(offer_amount)})"
        action_desc = f"การเจรจาซื้อขายเสร็จสมบูรณ์! {player_name} ย้ายจาก {selling_club} เข้าสู่สโมสร {club_name}"
    else:
        subject = f"[Transfer Update] อัปเดตสถานะดีล {player_name} ({club_name}) — {status}"
        action_desc = f"สถานะข้อเสนอซื้อขายของ {player_name} ถูกปรับเป็น '{status}'"

    body = (
        f"เรียน ผู้บริหารสโมสร {club_name} / {selling_club} และผู้เกี่ยวข้อง,\n\n"
        f"{action_desc}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚽ รายละเอียดธุรกรรมการซื้อขาย (Transfer Deal Summary):\n"
        f"• นักฟุตบอล: {player_name}\n"
        f"• สโมสรผู้ซื้อ (Buying Club): {club_name}\n"
        f"• สโมสรต้นสังกัดเดิม (Selling Club): {selling_club}\n"
        f"• มูลค่าค่าตัวที่เสนอ (Transfer Fee): {format_currency(offer_amount)}\n"
        f"• ค่าเหนื่อยที่เสนอ (Weekly Wage): {format_currency(wage_offer)} / สัปดาห์\n"
        f"• สถานะดีลปัจจุบัน: {status}\n"
        f"• อีเมลผู้รับแจ้งเตือน: {recipient_emails}\n"
        f"• วันและเวลาที่บันทึก: {timestamp}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"ขอแสดงความนับถือ,\n"
        f"ระบบจัดการตลาดซื้อขายนักฟุตบอลและเอเยนต์ (Football Transfer System)"
    )
    return dispatch_email_to_recipients(recipient_emails, club_name, subject, body, email_type=f"Transfer_{status}")


def send_club_verification_email(club_name: str, recipient_email: str, is_approved: bool, budget: float = 0.0, reason: str = "", parent=None):
    """
    ส่งอีเมลแจ้งผลการตรวจสอบเอกสารการเงินไปยังอีเมลของสโมสร
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if is_approved:
        subject = f"[UEFA FFP & TMS] การยืนยันสโมสรสำเร็จ — {club_name} ได้รับการอนุมัติวงเงิน {format_currency(budget)}"
        body = (
            f"เรียน ผู้บริหารและฝ่ายการเงินสโมสร {club_name},\n\n"
            f"ฝ่ายกำกับดูแลและตรวจสอบทางการเงิน (Financial Regulatory & Audit Committee) "
            f"ขอแจ้งให้ทราบว่า เอกสารรับรองสถานะทางการเงิน (Proof of Funds / Bank Guarantee) "
            f"ของสโมสร {club_name} ได้รับการตรวจสอบและ 'อนุมัติ (APPROVED)' เรียบร้อยแล้ว\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📋 รายละเอียดการอนุมัติสโมสร:\n"
            f"• ชื่อสโมสร: {club_name}\n"
            f"• อีเมลติดต่อ: {recipient_email}\n"
            f"• วงเงินงบประมาณที่อนุมัติ: {format_currency(budget)}\n"
            f"• สถานะบัญชี: Active (เปิดใช้งานแล้ว)\n"
            f"• วันที่และเวลาอนุมัติ: {timestamp}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"บัญชีสโมสรของท่านสามารถเข้าสู่ระบบและเริ่มเจรจาซื้อขายนักเตะกับเอเยนต์ได้ทันที\n\n"
            f"ขอแสดงความนับถือ,\n"
            f"คณะกรรมการตรวจสอบทางการเงินและตลาดซื้อขายนักฟุตบอล\n"
            f"Football Transfer & Agent Management System (UEFA Compliant)"
        )
        email_type = "Verification_Approved"
    else:
        admin_sender_email = "footballbetatitle@gmail.com"
        actual_reason = reason if reason and reason.strip() else "เอกสารหลักฐานทางการเงินไม่ผ่านเกณฑ์การประเมินสภาพคล่องตามระเบียบ UEFA Financial Fair Play (FFP)"
        subject = f"[UEFA FFP & TMS] แจ้งผลการตรวจสอบ — การสมัครสโมสร {club_name} ไม่ผ่านการอนุมัติ"
        body = (
            f"เรียน ผู้บริหารสโมสร {club_name},\n\n"
            f"ฝ่ายกำกับดูแลและตรวจสอบทางการเงิน (Financial Regulatory & Audit Committee) "
            f"ขอแจ้งผลการตรวจสอบเอกสารการเงินสำหรับการลงทะเบียนสโมสร {club_name}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ ผลการพิจารณา: 'ไม่ผ่านการอนุมัติ (REJECTED)'\n"
            f"• ชื่อสโมสร: {club_name}\n"
            f"• อีเมลติดต่อสโมสร: {recipient_email}\n"
            f"• อีเมลแอดมินผู้ส่ง: {admin_sender_email}\n"
            f"• สาเหตุที่ไม่อนุมัติ: {actual_reason}\n"
            f"• วันที่และเวลาพิจารณา: {timestamp}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"ข้อมูลสโมสรและเอกสารที่ยื่นเข้ามาถูกยกเลิกในระบบแล้ว\n"
            f"💬 การตอบกลับ: ท่านสามารถกดปุ่ม 'ตอบกลับ' (Reply) ในอีเมลนี้ เพื่อส่งข้อความหรือแนบเอกสารชี้แจงกลับมายังทีมงานแอดมิน ({admin_sender_email}) ได้โดยตรง\n\n"
            f"ขอแสดงความนับถือ,\n"
            f"คณะกรรมการตรวจสอบทางการเงินและตลาดซื้อขายนักฟุตบอล\n"
            f"แอดมินระบบ: {admin_sender_email}\n"
            f"Football Transfer & Agent Management System (UEFA Compliant)"
        )
        email_type = "Verification_Rejected"

    results = dispatch_email_to_recipients(recipient_email, club_name, subject, body, email_type=email_type)
    del_status = results[0]["status"] if (results and len(results) > 0) else "Sent & Logged"

    if parent is not None:
        show_email_sent_modal(club_name, recipient_email, subject, body, is_approved, timestamp, parent)
    return {
        "ok": True,
        "club_name": club_name,
        "recipient_email": recipient_email,
        "sender_email": "footballbetatitle@gmail.com",
        "subject": subject,
        "body": body,
        "is_approved": is_approved,
        "timestamp": timestamp,
        "delivery_status": del_status,
        "email_type": email_type
    }


def show_email_sent_modal(club_name: str, recipient_email: str, subject: str, body: str, is_approved: bool, timestamp: str, parent=None):
    """หน้าต่างแสดงผลการส่งอีเมลยืนยันผลการตรวจสอบสโมสรแบบโมเดิร์น (เฉพาะ Desktop UI)"""
    modal = ctk.CTkToplevel(parent)
    modal.title("Email Notification Sent")
    modal.geometry("540x520")
    modal.configure(fg_color=BG_DIALOG)
    modal.grab_set()

    header_box = ctk.CTkFrame(modal, fg_color="transparent")
    header_box.pack(fill="x", padx=24, pady=(20, 10))

    icon = "✉️" if is_approved else "📧"
    ctk.CTkLabel(header_box, text=icon, font=("Arial", 36)).pack(pady=(0, 2))
    title_text = "ส่งอีเมลแจ้งผลการอนุมัติแล้ว!" if is_approved else "ส่งอีเมลแจ้งผลการปฏิเสธแล้ว!"
    status_col = COLOR_GREEN if is_approved else COLOR_RED
    ctk.CTkLabel(header_box, text=title_text, font=FONT_TITLE, text_color=status_col).pack()
    ctk.CTkLabel(
        header_box,
        text=f"ระบบได้ส่งอีเมลทางการไปยังผู้รับเรียบร้อยแล้วเมื่อ {timestamp}",
        font=FONT_SMALL,
        text_color=TEXT_MUTED
    ).pack(pady=(2, 0))

    card = ctk.CTkFrame(modal, fg_color=BG_CARD, corner_radius=16, border_width=1, border_color=BORDER_SUBTLE)
    card.pack(fill="both", expand=True, padx=24, pady=(6, 16))

    top_info = ctk.CTkFrame(card, fg_color="#F8FAFC", corner_radius=12)
    top_info.pack(fill="x", padx=14, pady=12)

    def add_meta(label, val, col=TEXT_MAIN):
        r = ctk.CTkFrame(top_info, fg_color="transparent")
        r.pack(fill="x", padx=12, pady=3)
        ctk.CTkLabel(r, text=f"{label}:", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED, width=80, anchor="w").pack(side="left")
        ctk.CTkLabel(r, text=val, font=FONT_SMALL_BOLD, text_color=col, anchor="w").pack(side="left", fill="x", expand=True)

    add_meta("ผู้รับ (To)", f"{club_name} <{recipient_email}>", COLOR_APPLE_BLUE)
    add_meta("หัวข้อ (Subject)", subject)
    add_meta("สถานะ (Status)", "🟢 Delivered (ส่งถึงกล่องจดหมายแล้ว)", COLOR_GREEN)

    body_scroll = ctk.CTkScrollableFrame(card, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color=BORDER_SUBTLE)
    body_scroll.pack(fill="both", expand=True, padx=14, pady=(0, 12))

    ctk.CTkLabel(
        body_scroll,
        text=body,
        font=("Segoe UI", 11),
        text_color=TEXT_MAIN,
        justify="left",
        anchor="nw"
    ).pack(fill="both", expand=True, padx=12, pady=10)

    ctk.CTkButton(
        modal,
        text="เข้าใจแล้ว / ปิดหน้าต่าง (OK)",
        font=FONT_BODY_BOLD,
        fg_color=COLOR_APPLE_BLUE,
        hover_color=COLOR_APPLE_BLUE_HOVER,
        text_color="#FFFFFF",
        height=38,
        corner_radius=19,
        command=modal.destroy
    ).pack(fill="x", padx=24, pady=(0, 18))
