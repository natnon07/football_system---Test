import os
import datetime
from PIL import Image, ImageDraw, ImageFont
import customtkinter as ctk
from utils.theme import (
    BG_CARD, BG_CARD_HOVER, BG_DIALOG, BORDER_SUBTLE,
    COLOR_APPLE_BLUE, COLOR_APPLE_BLUE_HOVER, COLOR_GREEN, COLOR_RED,
    TEXT_MAIN, TEXT_MUTED, FONT_FAMILY, FONT_TITLE, FONT_SUBTITLE,
    FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_SMALL_BOLD, format_currency
)

DOCS_DIR = os.path.join("assets", "financial_docs")

def get_font(size, bold=False):
    """โหลดฟอนต์ภาษาอังกฤษ/ตัวเลขมาตรฐาน"""
    try:
        font_name = "arialbd.ttf" if bold else "arial.ttf"
        return ImageFont.truetype(font_name, size)
    except Exception:
        try:
            return ImageFont.truetype("segoeui.ttf", size)
        except Exception:
            return ImageFont.load_default()

def generate_official_bank_statement(club_name, budget, bank_name="Deutsche Sporting & Corporate Bank", country="Europe"):
    """
    สร้างเอกสารรับรองสถานะทางการเงิน (Proof of Funds / Bank Guarantee)
    ด้วยรูปแบบหนังสือค้ำประกันสากลที่สวยงาม เป็นทางการ และมีรายละเอียดชัดเจน
    """
    os.makedirs(DOCS_DIR, exist_ok=True)
    safe_name = "".join(c for c in club_name if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_').lower()
    file_path = os.path.join(DOCS_DIR, f"proof_of_funds_{safe_name}.png")

    width, height = 850, 1150
    img = Image.new("RGB", (width, height), color="#FAFBFC")
    draw = ImageDraw.Draw(img)

    # 1. Outer Border & Margin
    draw.rectangle([(20, 20), (width - 20, height - 20)], outline="#E2E8F0", width=2)
    draw.rectangle([(26, 26), (width - 26, height - 26)], outline="#0071E3", width=1)

    # 2. Header Banner (Deep Navy)
    draw.rectangle([(26, 26), (width - 26, 175)], fill="#0B132B")

    f_title_big = get_font(23, bold=True)
    f_sub = get_font(13, bold=False)
    f_badge = get_font(11, bold=True)

    draw.text((50, 48), "🏛️  DEUTSCHE SPORTING & INVESTMENT BANKING GROUP", fill="#FFFFFF", font=f_title_big)
    draw.text((50, 85), "Global Sports Capital Division • UEFA Financial Fair Play Compliance Escrow", fill="#94A3B8", font=f_sub)
    draw.text((50, 115), "Frankfurt am Main • London • Zurich • Singapore • Tokyo", fill="#64748B", font=get_font(11))

    # Header Gold Badge
    draw.rounded_rectangle([(width - 230, 50), (width - 50, 95)], radius=8, fill="#1E293B", outline="#F59E0B", width=1)
    draw.text((width - 215, 63), "★ AAA RATED GUARANTEE", fill="#F59E0B", font=f_badge)

    # 3. Document Title
    now_str = datetime.datetime.now().strftime("%d %B %Y")
    ref_code = f"UEFA-FFP-2026-{(abs(hash(club_name)) % 90000) + 10000}"

    draw.text((50, 205), "CERTIFICATE OF PROOF OF FUNDS & FINANCIAL GUARANTEE", fill="#0F172A", font=get_font(20, bold=True))
    draw.line([(50, 238), (width - 50, 238)], fill="#E2E8F0", width=1)

    # Metadata Row
    f_meta_lbl = get_font(12, bold=True)
    f_meta_val = get_font(12)
    draw.text((50, 252), "DATE OF ISSUANCE:", fill="#64748B", font=f_meta_lbl)
    draw.text((180, 252), now_str, fill="#0F172A", font=f_meta_val)

    draw.text((450, 252), "REFERENCE ID:", fill="#64748B", font=f_meta_lbl)
    draw.text((560, 252), ref_code, fill="#0071E3", font=f_meta_val)

    # 4. Section 1: Beneficiary Entity Details
    draw.rounded_rectangle([(50, 285), (width - 50, 400)], radius=12, fill="#FFFFFF", outline="#CBD5E1", width=1)
    draw.rectangle([(50, 285), (width - 50, 320)], fill="#F1F5F9")
    draw.text((65, 295), "1. BENEFICIARY ENTITY INFORMATION (สโมสรผู้ขอรับการตรวจสอบ)", fill="#334155", font=get_font(13, bold=True))

    draw.text((70, 335), "Official Club Name:", fill="#64748B", font=get_font(12, bold=True))
    draw.text((220, 335), club_name, fill="#0F172A", font=get_font(15, bold=True))

    draw.text((70, 365), "Country / League:", fill="#64748B", font=get_font(12, bold=True))
    draw.text((220, 365), country, fill="#0F172A", font=get_font(13))

    draw.text((500, 335), "Issuing Bank:", fill="#64748B", font=get_font(12, bold=True))
    draw.text((600, 335), bank_name, fill="#0F172A", font=get_font(12))

    draw.text((500, 365), "Account Category:", fill="#64748B", font=get_font(12, bold=True))
    draw.text((620, 365), "Tier-1 Club Escrow", fill="#10B981", font=get_font(12, bold=True))

    # 5. Section 2: Financial Certification & Capital Verification
    draw.rounded_rectangle([(50, 420), (width - 50, 680)], radius=12, fill="#FFFFFF", outline="#CBD5E1", width=1)
    draw.rectangle([(50, 420), (width - 50, 455)], fill="#F1F5F9")
    draw.text((65, 430), "2. FINANCIAL LIQUIDITY & ESCROW CAPITAL CERTIFICATION", fill="#334155", font=get_font(13, bold=True))

    cert_text = (
        "We, the undersigned authorized compliance officers of the Issuing Financial Institution, "
        "hereby unequivocally certify that the aforementioned Football Club maintains dedicated liquid capital "
        "and unencumbered funds in good standing. These balances are verified, fully cleared, and reserved "
        "for player transfer settlements, contract guarantees, and club administrative operations in full accordance "
        "with UEFA Club Licensing and Financial Sustainability Regulations."
    )
    # Simple multi-line wrap
    words = cert_text.split()
    line = ""
    y_text = 475
    for w in words:
        test_line = line + " " + w if line else w
        bbox = draw.textbbox((0, 0), test_line, font=get_font(12))
        if bbox[2] - bbox[0] > (width - 150):
            draw.text((70, y_text), line, fill="#475569", font=get_font(12))
            y_text += 20
            line = w
        else:
            line = test_line
    if line:
        draw.text((70, y_text), line, fill="#475569", font=get_font(12))

    # Highlighted Balance Box
    draw.rounded_rectangle([(80, 565), (width - 80, 655)], radius=10, fill="#F8FAFC", outline="#0071E3", width=2)
    draw.text((105, 580), "CONFIRMED AUDITED TRANSFER BUDGET / LIQUID ASSETS:", fill="#0071E3", font=get_font(12, bold=True))
    draw.text((105, 602), f"€ {budget:,.2f}  EUR", fill="#0F172A", font=get_font(28, bold=True))
    draw.text((width - 320, 615), "STATUS: FULLY VERIFIED & UNENCUMBERED", fill="#10B981", font=get_font(11, bold=True))

    # 6. Section 3: Official Stamp & Signatures
    draw.rounded_rectangle([(50, 700), (width - 50, 930)], radius=12, fill="#FFFFFF", outline="#CBD5E1", width=1)
    draw.rectangle([(50, 700), (width - 50, 735)], fill="#F1F5F9")
    draw.text((65, 710), "3. AUTHORIZATION, SEAL & REGULATORY ENDORSEMENT", fill="#334155", font=get_font(13, bold=True))

    # Stamp Simulation (Red/Gold circular seal)
    seal_x, seal_y = 120, 830
    draw.ellipse([(seal_x - 45, seal_y - 45), (seal_x + 45, seal_y + 45)], outline="#DC2626", width=3)
    draw.ellipse([(seal_x - 38, seal_y - 38), (seal_x + 38, seal_y + 38)], outline="#DC2626", width=1)
    draw.text((seal_x - 30, seal_y - 20), "FINANCIAL", fill="#DC2626", font=get_font(9, bold=True))
    draw.text((seal_x - 28, seal_y - 8), "INTEGRITY", fill="#DC2626", font=get_font(9, bold=True))
    draw.text((seal_x - 22, seal_y + 4), "AUDIT", fill="#DC2626", font=get_font(9, bold=True))
    draw.text((seal_x - 18, seal_y + 16), "2026", fill="#DC2626", font=get_font(9, bold=True))

    # Signatures
    draw.line([(320, 850), (500, 850)], fill="#94A3B8", width=1)
    draw.text((320, 825), "Marcus Vance", fill="#1E293B", font=get_font(15, bold=True))
    draw.text((320, 858), "Dr. Marcus Vance", fill="#0F172A", font=get_font(12, bold=True))
    draw.text((320, 876), "Head of Global Sports Underwriting", fill="#64748B", font=get_font(11))

    draw.line([(550, 850), (740, 850)], fill="#94A3B8", width=1)
    draw.text((550, 825), "Elena Rostova", fill="#1E293B", font=get_font(15, bold=True))
    draw.text((550, 858), "Elena Rostova, CFA", fill="#0F172A", font=get_font(12, bold=True))
    draw.text((550, 876), "Chief Compliance Officer & Auditor", fill="#64748B", font=get_font(11))

    # 7. Security Notice Footer
    draw.rectangle([(26, height - 120), (width - 26, height - 26)], fill="#F8FAFC")
    draw.line([(26, height - 120), (width - 26, height - 120)], fill="#E2E8F0", width=1)
    draw.text((50, height - 98), "SECURITY & ANTI-FRAUD NOTICE:", fill="#0F172A", font=get_font(10, bold=True))
    draw.text(
        (50, height - 80),
        "This electronic financial certificate is protected by digital hashing and direct interbank verification. "
        "Any fraudulent submission or alteration of financial guarantees shall be reported to the International Football Integrity Unit "
        "and results in immediate suspension of platform trading privileges.",
        fill="#64748B",
        font=get_font(9)
    )

    img.save(file_path, "PNG", quality=95)
    return file_path

def open_document_preview_modal(parent, doc_path, club_name, budget, status="Approved"):
    """หน้าต่างป๊อปอัปดูเอกสารทางการเงินอย่างละเอียด พร้อมเครื่องมือสำหรับ Admin และ Club"""
    dialog = ctk.CTkToplevel(parent)
    dialog.title(f"Financial Proof Document — {club_name}")
    dialog.geometry("740x800")
    dialog.configure(fg_color=BG_DIALOG)
    dialog.grab_set()

    # Top Header
    top = ctk.CTkFrame(dialog, fg_color="#FFFFFF", height=60, corner_radius=0, border_width=1, border_color=BORDER_SUBTLE)
    top.pack(fill="x")
    top.pack_propagate(False)

    ctk.CTkLabel(top, text=f"📑  Financial Statement: {club_name}", font=FONT_BODY_BOLD, text_color=TEXT_MAIN).pack(side="left", padx=20)
    
    status_col = COLOR_GREEN if status == "Approved" else (COLOR_RED if status == "Rejected" else "#F59E0B")
    status_badge = ctk.CTkFrame(top, fg_color="#F8FAFC", corner_radius=12, border_width=1, border_color=status_col)
    status_badge.pack(side="right", padx=20)
    ctk.CTkLabel(status_badge, text=f"Status: {status} • Budget: {format_currency(budget)}", font=FONT_SMALL_BOLD, text_color=status_col).pack(padx=10, pady=4)

    # Scrollable Preview Area
    scroll = ctk.CTkScrollableFrame(dialog, fg_color="#F1F5F9")
    scroll.pack(fill="both", expand=True, padx=20, pady=15)

    if doc_path and os.path.exists(doc_path):
        try:
            pil_img = Image.open(doc_path)
            # Resize for viewing
            target_width = 660
            ratio = target_width / float(pil_img.size[0])
            target_height = int(float(pil_img.size[1]) * float(ratio))
            resized = pil_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=resized, dark_image=resized, size=(target_width, target_height))

            lbl = ctk.CTkLabel(scroll, text="", image=ctk_img)
            lbl.image = ctk_img
            lbl.pack(pady=10)
        except Exception as e:
            ctk.CTkLabel(scroll, text=f"⚠️ ไม่สามารถแสดงผลรูปภาพ: {e}", font=FONT_BODY, text_color=COLOR_RED).pack(pady=40)
    else:
        ctk.CTkLabel(scroll, text=f"⚠️ ไม่พบไฟล์เอกสาร: {doc_path}", font=FONT_BODY, text_color=TEXT_MUTED).pack(pady=60)

    # Bottom Actions
    bot = ctk.CTkFrame(dialog, fg_color="#FFFFFF", height=54, corner_radius=0, border_width=1, border_color=BORDER_SUBTLE)
    bot.pack(fill="x")
    bot.pack_propagate(False)

    ctk.CTkButton(
        bot,
        text="Close Window",
        font=FONT_SMALL_BOLD,
        fg_color=BG_CARD_HOVER,
        hover_color=BORDER_SUBTLE,
        text_color=TEXT_MAIN,
        height=34,
        corner_radius=17,
        command=dialog.destroy
    ).pack(side="right", padx=20)

    if doc_path and os.path.exists(doc_path):
        def open_system_file():
            try:
                os.startfile(os.path.abspath(doc_path))
            except Exception as e:
                print("Error opening file:", e)

        ctk.CTkButton(
            bot,
            text="Open with External Viewer ↗",
            font=FONT_SMALL_BOLD,
            fg_color=COLOR_APPLE_BLUE,
            hover_color=COLOR_APPLE_BLUE_HOVER,
            text_color="#FFFFFF",
            height=34,
            corner_radius=17,
            command=open_system_file
        ).pack(side="right", padx=4)
