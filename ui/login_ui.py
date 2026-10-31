import os
import shutil
import customtkinter as ctk
from tkinter import messagebox, filedialog
from utils.security import hash_password, verify_password
from database.db_manager import get_connection, log_audit
from utils.session import CurrentSession
from utils.theme import (
    BG_APP, BG_CARD, BG_CARD_HOVER, BG_INPUT, BG_DIALOG, BORDER_SUBTLE,
    COLOR_APPLE_BLUE, COLOR_APPLE_BLUE_HOVER, COLOR_APPLE_DARK, COLOR_APPLE_DARK_HOVER,
    COLOR_GREEN, COLOR_GOLD, COLOR_RED, TEXT_MAIN, TEXT_MUTED, TEXT_DIM,
    FONT_FAMILY, FONT_HERO, FONT_TITLE, FONT_SUBTITLE, FONT_CARD_TITLE,
    FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_SMALL_BOLD,
    get_stadium_full_bg, get_login_hero_image, get_login_corner_accent, get_login_outer_bg,
    get_login_pastel_bg, get_login_team_icon,
    format_currency
)
from utils.financial_docs import generate_official_bank_statement, open_document_preview_modal

class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, login_success_callback):
        super().__init__(master, fg_color="#E8F0FA")
        self.login_success_callback = login_success_callback
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_main_view()

    def _build_main_view(self):
        """หน้าล็อกอินโมเดิร์นมินิมอล ตรงตามดีไซน์ Mockup:
        - พื้นหลังไล่เฉดสีพาสเทลละมุน (Warm peach to soft sky blue)
        - ไอคอนกลุ่ม 3 คน (Team silhouette) สีฟ้าตรงกลาง
        - กล่องกรอกข้อมูลทรงแคปซูลสีขาวมนกลม (White rounded capsules)
        - ตัวเลือก Remember me และ Forgot password?
        - ปุ่ม LOGIN แคปซูลสีฟ้าสดใส เด่นสง่าตรงกลาง
        - ปรับดีไซน์เรียบหรู ลดการไกด์ซับซ้อนตามคำขอ
        """
        # 1. Background image (Football Stadium Full Background)
        bg_img = get_stadium_full_bg(size=(1400, 900)) or get_login_pastel_bg(size=(1400, 900))
        if bg_img:
            bg_lbl = ctk.CTkLabel(self, image=bg_img, text="")
            bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)

        # 2. Main Centered Wide Football Portal Card
        self.register_container = None
        self.success_container = None
        container = ctk.CTkFrame(
            self,
            fg_color="#0F172A",
            corner_radius=28,
            border_width=1,
            border_color="#38BDF8"
        )
        container.place(relx=0.5, rely=0.5, anchor="center")
        self.login_container = container

        # 3. Clean Team Icon & Portal Title
        team_icon = get_login_team_icon(size=(130, 78))
        if team_icon:
            icon_lbl = ctk.CTkLabel(container, image=team_icon, text="")
            icon_lbl.pack(padx=54, pady=(28, 10))

        ctk.CTkLabel(
            container,
            text="เข้าสู่ระบบสโมสร & เอเยนต์",
            font=(FONT_FAMILY, 22, "bold"),
            text_color="#FFFFFF"
        ).pack(padx=54, pady=(0, 2))

        ctk.CTkLabel(
            container,
            text="FOOTBALL CLUB • AGENT • ADMIN PORTAL",
            font=(FONT_FAMILY, 11, "bold"),
            text_color="#38BDF8"
        ).pack(padx=54, pady=(0, 20))

        form_width = 480

        # 4. Field 1: USERNAME (Capsule Pill)
        u_box = ctk.CTkFrame(
            container,
            width=form_width,
            height=48,
            corner_radius=24,
            fg_color="#FFFFFF",
            border_width=0
        )
        u_box.pack(pady=(0, 14))
        u_box.pack_propagate(False)

        ctk.CTkLabel(
            u_box,
            text="👤",
            font=("Segoe UI Emoji", 13),
            text_color="#94A3B8"
        ).pack(side="left", padx=(18, 10))

        ctk.CTkFrame(u_box, width=1, height=20, fg_color="#E2E8F0").pack(side="left", padx=(0, 12))

        self.u_entry = ctk.CTkEntry(
            u_box,
            placeholder_text="USERNAME",
            placeholder_text_color="#94A3B8",
            fg_color="transparent",
            border_width=0,
            text_color="#1E293B",
            font=("Segoe UI", 13)
        )
        self.u_entry.pack(side="left", fill="both", expand=True, padx=(0, 18))

        # 5. Field 2: PASSWORD (Capsule Pill)
        p_box = ctk.CTkFrame(
            container,
            width=form_width,
            height=48,
            corner_radius=24,
            fg_color="#FFFFFF",
            border_width=0
        )
        p_box.pack(pady=(0, 12))
        p_box.pack_propagate(False)

        ctk.CTkLabel(
            p_box,
            text="🔒",
            font=("Segoe UI Emoji", 13),
            text_color="#94A3B8"
        ).pack(side="left", padx=(18, 10))

        ctk.CTkFrame(p_box, width=1, height=20, fg_color="#E2E8F0").pack(side="left", padx=(0, 12))

        self.p_entry = ctk.CTkEntry(
            p_box,
            placeholder_text="••••••••",
            placeholder_text_color="#94A3B8",
            show="•",
            fg_color="transparent",
            border_width=0,
            text_color="#1E293B",
            font=("Segoe UI", 13)
        )
        self.p_entry.pack(side="left", fill="both", expand=True)

        self.pwd_visible = False
        def toggle_password_visibility():
            self.pwd_visible = not self.pwd_visible
            if self.pwd_visible:
                self.p_entry.configure(show="")
                eye_btn.configure(text="👁")
            else:
                self.p_entry.configure(show="•")
                eye_btn.configure(text="👁‍🗨")

        eye_btn = ctk.CTkButton(
            p_box,
            text="👁‍🗨",
            font=("Segoe UI Emoji", 12),
            text_color="#94A3B8",
            fg_color="transparent",
            hover_color="#F1F5F9",
            width=32,
            height=32,
            corner_radius=16,
            command=toggle_password_visibility
        )
        eye_btn.pack(side="right", padx=(4, 12))

        # 6. Options Row: Remember Me & Forgot Password?
        opts_row = ctk.CTkFrame(container, width=form_width, fg_color="transparent")
        opts_row.pack(fill="x", pady=(0, 24), padx=6)

        self.remember_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            opts_row,
            text="Remember me",
            variable=self.remember_var,
            font=("Segoe UI", 11),
            text_color="#2563EB",
            checkbox_width=16,
            checkbox_height=16,
            corner_radius=4,
            fg_color="#1B9AE5",
            hover_color="#1583C7",
            border_color="#93C5FD",
            border_width=1.5
        ).pack(side="left")

        ctk.CTkButton(
            opts_row,
            text="Forgot password?",
            font=("Segoe UI", 11),
            text_color="#2563EB",
            hover_color="#E0F2FE",
            fg_color="transparent",
            height=20,
            cursor="hand2",
            command=self.handle_forgot_password
        ).pack(side="right")

        # 7. Primary Action: Centered LOGIN Pill Button
        self.signin_btn = ctk.CTkButton(
            container,
            text="LOGIN",
            font=("Segoe UI", 14, "bold"),
            fg_color="#1B9AE5",
            hover_color="#1583C7",
            text_color="#FFFFFF",
            width=180,
            height=44,
            corner_radius=22,
            command=self.handle_form_submit
        )
        self.signin_btn.pack(pady=(0, 20))

        self.u_entry.bind("<Return>", lambda e: self.handle_form_submit())
        self.p_entry.bind("<Return>", lambda e: self.handle_form_submit())

        # 8. Secondary Actions (สมัครสโมสรใหม่ / บัญชีทดสอบ)
        sub_row = ctk.CTkFrame(container, fg_color="transparent")
        sub_row.pack(fill="x", pady=(0, 4))

        ctk.CTkButton(
            sub_row,
            text="📝 สมัครบัญชีสโมสรใหม่",
            font=("Kanit", 12, "bold"),
            text_color="#1D4ED8",
            hover_color="#DBEAFE",
            fg_color="transparent",
            height=32,
            corner_radius=16,
            cursor="hand2",
            command=self.open_club_register_modal
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            sub_row,
            text="⚡ บัญชีทดสอบด่วน",
            font=("Kanit", 11),
            text_color="#64748B",
            hover_color="#E2E8F0",
            fg_color="transparent",
            height=32,
            corner_radius=16,
            cursor="hand2",
            command=self.open_manual_login_modal
        ).pack(side="right", padx=4)

    def handle_forgot_password(self):
        """แจ้งเตือนขั้นตอนการกู้คืนรหัสผ่าน"""
        messagebox.showinfo(
            "กู้คืนรหัสผ่าน (Forgot Password)",
            "หากท่านลืมรหัสผ่านเข้าสู่ระบบ:\n\n"
            "1. สำหรับสโมสร: กรุณาติดต่อผู้ดูแลระบบ (Admin) หรือตรวจสอบอีเมลที่ใช้ลงทะเบียนสโมสร\n"
            "2. สำหรับผู้ดูแลระบบ: กรุณาตรวจสอบฐานข้อมูลระบบเพื่อกู้คืนหรือรีเซ็ตรหัสผ่าน\n\n"
            "ระบบสามารถช่วยเหลือในการรีเซ็ตรหัสผ่านชั่วคราวได้ผ่าน Admin"
        )

    def handle_form_submit(self):
        """ตรวจสอบและเข้าสู่ระบบจากฟอร์ม Sign In"""
        u = self.u_entry.get().strip()
        p = self.p_entry.get().strip()

        if not u or not p:
            messagebox.showwarning("ข้อมูลไม่ครบถ้วน", "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน")
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash, role, status FROM users WHERE username = ?", (u,))
        user = cursor.fetchone()
        conn.close()

        if user:
            hashed = hash_password(p)
            is_valid = (user['password_hash'] == hashed)
            if not is_valid:
                try:
                    is_valid = verify_password(p, user['password_hash'])
                except Exception:
                    pass

            if is_valid:
                if user['status'] == "Suspended":
                    messagebox.showerror("ระงับการใช้งาน", "บัญชีนี้ถูกระงับการใช้งาน กรุณาติดต่อผู้ดูแลระบบ")
                    return
                elif user['status'] == "Pending_Verification":
                    self.show_pending_verification_modal(user['username'])
                    return
                elif user['status'] == "Rejected":
                    messagebox.showerror("ไม่ผ่านการอนุมัติ", "สโมสรนี้ไม่ผ่านการอนุมัติการตรวจสอบเอกสารการเงิน กรุณาติดต่อผู้ดูแลระบบ")
                    return

                CurrentSession.login(user['id'], user['username'], user['role'])
                log_audit("USER_LOGIN", f"Sign in form: {user['username']} ({user['role']})")
                self.login_success_callback(user['role'])
                return

        messagebox.showerror("เข้าสู่ระบบไม่สำเร็จ", "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    def quick_login(self, username):
        """เข้าสู่ระบบทันที 1-Click ด้วย Username"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role, status FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user:
            if user['status'] == "Suspended":
                messagebox.showerror("ระงับการใช้งาน", "บัญชีนี้ถูกระงับการใช้งาน กรุณาติดต่อผู้ดูแลระบบ")
                return
            elif user['status'] == "Pending_Verification":
                self.show_pending_verification_modal(user['username'])
                return
            elif user['status'] == "Rejected":
                messagebox.showerror("ไม่ผ่านการอนุมัติ", "สโมสรนี้ไม่ผ่านการอนุมัติการตรวจสอบเอกสารการเงิน กรุณาติดต่อผู้ดูแลระบบ")
                return

            CurrentSession.login(user['id'], user['username'], user['role'])
            log_audit("USER_LOGIN", f"1-Click fast sign in: {user['username']} ({user['role']})")
            self.login_success_callback(user['role'])
        else:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่พบบัญชีผู้ใช้ {username}")

    def open_manual_login_modal(self):
        """หน้าต่างป๊อปอัปกรอก Username และ Password แบบคลาสสิก พร้อม Quick Fill Chips"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("เข้าสู่ระบบ")
        dialog.geometry("460x540")
        dialog.configure(fg_color=BG_DIALOG)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="⚽", font=("Arial", 36)).pack(pady=(22, 4))
        ctk.CTkLabel(dialog, text="เข้าสู่ระบบบัญชีผู้ใช้", font=FONT_SUBTITLE, text_color=TEXT_MAIN).pack(pady=(0, 2))
        ctk.CTkLabel(dialog, text="กรุณากรอกชื่อผู้ใช้และรหัสผ่านเพื่อเข้าใช้งาน", font=FONT_SMALL, text_color=TEXT_MUTED).pack(pady=(0, 14))

        # Quick Fill Chips
        chips_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        chips_frame.pack(fill="x", padx=32, pady=(0, 14))
        ctk.CTkLabel(chips_frame, text="เข้าใช้งานด่วน:", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(side="left", padx=(0, 6))

        for icon, label_name, uname in [
            ("👑", "แอดมิน", "admin"),
            ("⚪", "Real Madrid", "realmadrid"),
            ("🔵", "Man City", "mancity"),
            ("🔴", "Barca", "barcelona"),
            ("💼", "เอเยนต์", "agent1")
        ]:
            def make_filler(u):
                def _fill():
                    u_entry.delete(0, "end")
                    u_entry.insert(0, u)
                    p_entry.delete(0, "end")
                    p_entry.insert(0, "password123")
                return _fill

            ctk.CTkButton(
                chips_frame,
                text=f"{icon} {label_name}",
                font=("Segoe UI", 11),
                fg_color=BG_CARD,
                hover_color=BG_CARD_HOVER,
                border_width=1,
                border_color=BORDER_SUBTLE,
                text_color=TEXT_MAIN,
                height=26,
                corner_radius=13,
                command=make_filler(uname)
            ).pack(side="left", padx=2)

        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="x", padx=32)

        ctk.CTkLabel(form, text="ชื่อผู้ใช้งาน", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 4))
        u_entry = ctk.CTkEntry(form, height=40, fg_color=BG_INPUT, border_color=BORDER_SUBTLE, text_color=TEXT_MAIN, placeholder_text="ชื่อผู้ใช้งาน", corner_radius=10)
        u_entry.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(form, text="รหัสผ่าน", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 4))
        p_entry = ctk.CTkEntry(form, height=40, fg_color=BG_INPUT, border_color=BORDER_SUBTLE, text_color=TEXT_MAIN, show="•", placeholder_text="รหัสผ่าน", corner_radius=10)
        p_entry.pack(fill="x", pady=(0, 18))

        def submit():
            u = u_entry.get().strip()
            p = p_entry.get().strip()
            if not u or not p:
                messagebox.showwarning("ข้อมูลไม่ครบถ้วน", "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน", parent=dialog)
                return

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, password_hash, role, status FROM users WHERE username = ?", (u,))
            user = cursor.fetchone()
            conn.close()

            if user:
                hashed = hash_password(p)
                is_valid = (user['password_hash'] == hashed)
                if not is_valid:
                    try: is_valid = verify_password(p, user['password_hash'])
                    except Exception: pass

                if is_valid:
                    if user['status'] == "Suspended":
                        messagebox.showerror("ระงับการใช้งาน", "บัญชีนี้ถูกระงับการใช้งาน", parent=dialog)
                        return
                    elif user['status'] == "Pending_Verification":
                        dialog.destroy()
                        self.show_pending_verification_modal(user['username'])
                        return
                    elif user['status'] == "Rejected":
                        messagebox.showerror("ไม่ผ่านการอนุมัติ", "สโมสรนี้ไม่ผ่านการอนุมัติการตรวจสอบเอกสารการเงิน", parent=dialog)
                        return

                    CurrentSession.login(user['id'], u, user['role'])
                    log_audit("USER_LOGIN", f"Manual sign in: {u} ({user['role']})")
                    dialog.destroy()
                    self.login_success_callback(user['role'])
                    return

            messagebox.showerror("เข้าสู่ระบบไม่สำเร็จ", "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง", parent=dialog)

        u_entry.bind("<Return>", lambda e: submit())
        p_entry.bind("<Return>", lambda e: submit())

        ctk.CTkButton(
            dialog,
            text="เข้าสู่ระบบ ➔",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_APPLE_BLUE,
            hover_color=COLOR_APPLE_BLUE_HOVER,
            height=40,
            corner_radius=20,
            command=submit
        ).pack(fill="x", padx=32, pady=(6, 0))

        hint_box = ctk.CTkFrame(dialog, fg_color="#F5F6F8", corner_radius=10)
        hint_box.pack(fill="x", padx=32, pady=(14, 0))
        ctk.CTkLabel(hint_box, text="🔑 รหัสผ่านเริ่มต้นสำหรับทุกบัญชี: password123", font=FONT_SMALL_BOLD, text_color=COLOR_APPLE_BLUE).pack(pady=6)

    def open_all_accounts_modal(self):
        """หน้าต่างแสดงรายชื่อบัญชีและรหัสผ่านทั้งหมดในระบบ พร้อมปุ่มกดเข้าสู่ระบบทันที"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("รายชื่อบัญชีและรหัสผ่านในระบบ")
        dialog.geometry("680x650")
        dialog.configure(fg_color=BG_DIALOG)
        dialog.grab_set()

        scroll = ctk.CTkScrollableFrame(dialog, fg_color=BG_DIALOG)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(scroll, text="🔑", font=("Arial", 36)).pack(pady=(10, 4))
        ctk.CTkLabel(scroll, text="รายชื่อบัญชีและรหัสผ่านในระบบ", font=FONT_TITLE, text_color=TEXT_MAIN).pack(pady=(0, 2))
        ctk.CTkLabel(
            scroll,
            text="รหัสผ่านเข้าสู่ระบบสำหรับทุกบัญชีในระบบคือ: password123\nท่านสามารถคลิกปุ่ม 'เข้าสู่ระบบ ➔' ที่บัญชีใดก็ได้เพื่อเข้าสู่ระบบทันทีโดยไม่ต้องพิมพ์",
            font=FONT_SMALL,
            text_color=TEXT_MUTED,
            justify="center"
        ).pack(pady=(0, 16))

        # Query all users with their roles and club/agent names
        conn = get_connection()
        users = conn.execute("SELECT id, username, role, status FROM users ORDER BY id ASC").fetchall()
        clubs = {c['user_id']: c['club_name'] for c in conn.execute("SELECT user_id, club_name FROM clubs").fetchall()}
        agents = {a['user_id']: f"{a['first_name']} {a['last_name']} ({a['agency_name']})" for a in conn.execute("SELECT user_id, first_name, last_name, agency_name FROM agents").fetchall()}
        conn.close()

        # Group by role
        roles_data = [
            ("👑 ผู้ดูแลระบบสูงสุด (Administrator)", [u for u in users if u['role'] == 'Admin']),
            ("🏟️ ฝ่ายบริหารสโมสร (Clubs)", [u for u in users if u['role'] == 'Club']),
            ("💼 เอเย่นต์นักเตะ (Agents)", [u for u in users if u['role'] == 'Agent'])
        ]

        for section_title, u_list in roles_data:
            if not u_list:
                continue
            ctk.CTkLabel(scroll, text=section_title, font=FONT_BODY_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=6, pady=(14, 6))

            for u in u_list:
                row = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=14, border_width=1, border_color=BORDER_SUBTLE)
                row.pack(fill="x", pady=4)

                left = ctk.CTkFrame(row, fg_color="transparent")
                left.pack(side="left", padx=16, pady=10)

                sub_desc = ""
                if u['role'] == 'Club':
                    sub_desc = f"สโมสร: {clubs.get(u['id'], u['username'])}"
                elif u['role'] == 'Agent':
                    sub_desc = f"เอเยนต์: {agents.get(u['id'], u['username'])}"
                else:
                    sub_desc = "ผู้ดูแลระบบส่วนกลาง"

                ctk.CTkLabel(left, text=f"ชื่อผู้ใช้: {u['username']}", font=FONT_BODY_BOLD, text_color=TEXT_MAIN).pack(anchor="w")
                ctk.CTkLabel(left, text=f"รหัสผ่าน: password123   •   {sub_desc}", font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w")

                def make_direct_login(un):
                    def _do():
                        dialog.destroy()
                        self.quick_login(un)
                    return _do

                ctk.CTkButton(
                    row,
                    text="เข้าสู่ระบบ ➔",
                    font=FONT_SMALL_BOLD,
                    fg_color=COLOR_APPLE_BLUE if u['role'] == 'Admin' else (COLOR_APPLE_DARK if u['role'] == 'Club' else COLOR_GREEN),
                    hover_color=COLOR_APPLE_BLUE_HOVER,
                    text_color="#FFFFFF",
                    width=90,
                    height=30,
                    corner_radius=15,
                    command=make_direct_login(u['username'])
                ).pack(side="right", padx=14)

        ctk.CTkButton(
            scroll,
            text="ปิดหน้าต่าง",
            font=FONT_SMALL_BOLD,
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            border_width=1,
            border_color=BORDER_SUBTLE,
            text_color=TEXT_MUTED,
            height=34,
            corner_radius=17,
            command=dialog.destroy
        ).pack(fill="x", padx=10, pady=(20, 10))

    # ==================== CLUB REGISTRATION & FINANCIAL VERIFICATION (IN-PAGE VIEW) ====================
    def show_login_view(self, prefill_username=None):
        """สลับกลับมาแสดงหน้าเข้าสู่ระบบหลักโดยไม่ใช้ป๊อปอัป"""
        if self.register_container is not None:
            self.register_container.place_forget()
        if self.success_container is not None:
            self.success_container.place_forget()

        if prefill_username:
            self.u_entry.delete(0, "end")
            self.u_entry.insert(0, prefill_username)
            self.p_entry.delete(0, "end")

        self.login_container.place(relx=0.5, rely=0.5, anchor="center")

    def open_club_register_modal(self):
        """สลับหน้าไปยังฟอร์มลงทะเบียนสโมสรใหม่ภายในหน้าต่างเดิม (ไม่เด้งป๊อปอัป)"""
        self.login_container.place_forget()
        if self.success_container is not None:
            self.success_container.place_forget()

        if self.register_container is not None:
            self.register_container.destroy()

        card = ctk.CTkFrame(
            self,
            width=900,
            height=590,
            corner_radius=26,
            fg_color="#FFFFFF",
            border_width=0
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)
        self.register_container = card

        # Top Header Row with Back Button
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(20, 12))

        ctk.CTkButton(
            header,
            text="⬅ กลับหน้าเข้าสู่ระบบ",
            font=("Kanit", 12, "bold"),
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color="#1E293B",
            width=150,
            height=34,
            corner_radius=17,
            cursor="hand2",
            command=self.show_login_view
        ).pack(side="left")

        title_col = ctk.CTkFrame(header, fg_color="transparent")
        title_col.pack(side="left", padx=18)

        ctk.CTkLabel(
            title_col,
            text="🏟️ ลงทะเบียนสโมสรใหม่ & ตรวจสอบสถานะการเงิน",
            font=(FONT_FAMILY, 19, "bold"),
            text_color="#0F172A"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_col,
            text="กรอกข้อมูลสโมสรและแนบเอกสารทางการเงิน (Proof of Funds / Bank Statement) เพื่อให้ Admin อนุมัติวงเงิน",
            font=FONT_SMALL,
            text_color=TEXT_MUTED
        ).pack(anchor="w")

        ctk.CTkFrame(card, height=1, fg_color="#E2E8F0").pack(fill="x", padx=28, pady=(0, 14))

        # 2-Column Body Container
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        # ---- LEFT COLUMN: Club & Account Info ----
        left_col = ctk.CTkFrame(body, fg_color="#F8FAFC", corner_radius=18, border_width=1, border_color="#E2E8F0")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(left_col, text="1. ข้อมูลสโมสร & บัญชีเข้าใช้งาน", font=FONT_BODY_BOLD, text_color="#0F172A").pack(anchor="w", padx=18, pady=(14, 6))

        # Row: Club Name & League
        cl_row = ctk.CTkFrame(left_col, fg_color="transparent")
        cl_row.pack(fill="x", padx=18, pady=(0, 8))
        cl_row.grid_columnconfigure((0, 1), weight=1)

        c1_box = ctk.CTkFrame(cl_row, fg_color="transparent")
        c1_box.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkLabel(c1_box, text="ชื่อสโมสรอย่างเป็นทางการ", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 2))
        club_entry = ctk.CTkEntry(c1_box, height=36, fg_color="#FFFFFF", border_color=BORDER_SUBTLE, placeholder_text="เช่น AC Milan, Dortmund", text_color=TEXT_MAIN, corner_radius=10)
        club_entry.pack(fill="x")

        c2_box = ctk.CTkFrame(cl_row, fg_color="transparent")
        c2_box.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ctk.CTkLabel(c2_box, text="ประเทศ / ลีกการแข่งขัน", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 2))
        league_opt = ctk.CTkOptionMenu(
            c2_box,
            values=[
                "Germany - Bundesliga",
                "England - Premier League",
                "Spain - La Liga",
                "Italy - Serie A",
                "France - Ligue 1",
                "Netherlands - Eredivisie",
                "Portugal - Primeira Liga",
                "Other International League"
            ],
            fg_color="#FFFFFF",
            button_color="#1B9AE5",
            button_hover_color="#1583C7",
            text_color=TEXT_MAIN,
            height=36,
            corner_radius=10
        )
        league_opt.pack(fill="x")

        ctk.CTkLabel(left_col, text="ชื่อผู้ใช้งานสำหรับเข้าสู่ระบบ (Username)", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=18, pady=(4, 2))
        u_entry = ctk.CTkEntry(left_col, height=36, fg_color="#FFFFFF", border_color=BORDER_SUBTLE, placeholder_text="เช่น dortmund_fc", text_color=TEXT_MAIN, corner_radius=10)
        u_entry.pack(fill="x", padx=18, pady=(0, 8))

        # Email & Confirm Email
        em_row = ctk.CTkFrame(left_col, fg_color="transparent")
        em_row.pack(fill="x", padx=18, pady=(0, 8))
        em_row.grid_columnconfigure((0, 1), weight=1)

        em1_box = ctk.CTkFrame(em_row, fg_color="transparent")
        em1_box.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkLabel(em1_box, text="อีเมลสโมสรสำหรับติดต่อ", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 2))
        email_entry = ctk.CTkEntry(em1_box, height=36, fg_color="#FFFFFF", border_color=BORDER_SUBTLE, placeholder_text="contact@club.com", text_color=TEXT_MAIN, corner_radius=10)
        email_entry.pack(fill="x")

        em2_box = ctk.CTkFrame(em_row, fg_color="transparent")
        em2_box.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ctk.CTkLabel(em2_box, text="ยืนยันอีเมลอีกครั้ง", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 2))
        email_confirm_entry = ctk.CTkEntry(em2_box, height=36, fg_color="#FFFFFF", border_color=BORDER_SUBTLE, placeholder_text="ยืนยันอีเมลให้ตรงกัน", text_color=TEXT_MAIN, corner_radius=10)
        email_confirm_entry.pack(fill="x")

        # Password & Confirm Password
        pw_row = ctk.CTkFrame(left_col, fg_color="transparent")
        pw_row.pack(fill="x", padx=18, pady=(0, 12))
        pw_row.grid_columnconfigure((0, 1), weight=1)

        p1_box = ctk.CTkFrame(pw_row, fg_color="transparent")
        p1_box.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkLabel(p1_box, text="รหัสผ่าน", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 2))
        p1_entry = ctk.CTkEntry(p1_box, height=36, fg_color="#FFFFFF", border_color=BORDER_SUBTLE, show="•", placeholder_text="อย่างน้อย 4 ตัวอักษร", text_color=TEXT_MAIN, corner_radius=10)
        p1_entry.pack(fill="x")

        p2_box = ctk.CTkFrame(pw_row, fg_color="transparent")
        p2_box.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ctk.CTkLabel(p2_box, text="ยืนยันรหัสผ่านอีกครั้ง", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 2))
        p2_entry = ctk.CTkEntry(p2_box, height=36, fg_color="#FFFFFF", border_color=BORDER_SUBTLE, show="•", placeholder_text="ยืนยันรหัสผ่าน", text_color=TEXT_MAIN, corner_radius=10)
        p2_entry.pack(fill="x")

        # ---- RIGHT COLUMN: Financial Proof & Submit ----
        right_col = ctk.CTkFrame(body, fg_color="#F8FAFC", corner_radius=18, border_width=1, border_color="#E2E8F0")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        ctk.CTkLabel(right_col, text="2. วงเงินงบประมาณ & เอกสารการเงิน", font=FONT_BODY_BOLD, text_color="#0F172A").pack(anchor="w", padx=18, pady=(14, 6))

        ctk.CTkLabel(right_col, text="วงเงินงบประมาณที่ต้องการยืนยัน (€ ยูโร)", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=18, pady=(2, 2))
        budget_entry = ctk.CTkEntry(right_col, height=36, fg_color="#FFFFFF", border_color=BORDER_SUBTLE, text_color=TEXT_MAIN, corner_radius=10)
        budget_entry.insert(0, "150000000")
        budget_entry.pack(fill="x", padx=18, pady=(0, 8))

        ctk.CTkLabel(right_col, text="ธนาคารผู้ออกเอกสารรับรอง", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=18, pady=(2, 2))
        bank_opt = ctk.CTkOptionMenu(
            right_col,
            values=[
                "Deutsche Sporting & Corporate Bank",
                "Santander Corporate & Investment Bank",
                "Barclays Corporate Banking",
                "BNP Paribas Wealth & Sports Finance",
                "UBS Switzerland AG",
                "JPMorgan Chase Commercial Banking"
            ],
            fg_color="#FFFFFF",
            button_color="#1B9AE5",
            button_hover_color="#1583C7",
            text_color=TEXT_MAIN,
            height=36,
            corner_radius=10
        )
        bank_opt.pack(fill="x", padx=18, pady=(0, 12))

        # Document Attachment Box
        doc_card = ctk.CTkFrame(right_col, fg_color="#FFFFFF", corner_radius=14, border_width=1, border_color="#CBD5E1")
        doc_card.pack(fill="x", padx=18, pady=(0, 14))

        ctk.CTkLabel(doc_card, text="📎 เอกสารหลักฐานรับรองสถานะทางการเงิน", font=FONT_SMALL_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=14, pady=(10, 2))
        ctk.CTkLabel(
            doc_card,
            text="แนบ Bank Statement หรือกดออกหนังสือค้ำประกันจำลองอัตโนมัติ",
            font=FONT_SMALL,
            text_color=TEXT_MUTED
        ).pack(anchor="w", padx=14, pady=(0, 6))

        doc_path_var = ctk.StringVar(value="")
        doc_status_lbl = ctk.CTkLabel(doc_card, text="⚠️ ยังไม่ได้แนบเอกสารการเงิน", font=FONT_SMALL_BOLD, text_color=COLOR_RED)
        doc_status_lbl.pack(anchor="w", padx=14, pady=(0, 6))

        btn_row = ctk.CTkFrame(doc_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=(0, 10))

        def on_browse_file():
            f = filedialog.askopenfilename(
                title="เลือกเอกสารรับรองสถานะทางการเงิน",
                filetypes=[("Documents & Images", "*.png;*.jpg;*.jpeg;*.pdf")]
            )
            if f:
                dest_dir = os.path.join("assets", "financial_docs")
                os.makedirs(dest_dir, exist_ok=True)
                dest = os.path.join(dest_dir, f"uploaded_{os.path.basename(f)}")
                try:
                    shutil.copy(f, dest)
                    doc_path_var.set(dest)
                    doc_status_lbl.configure(text=f"✔️ แนบไฟล์แล้ว: {os.path.basename(dest)}", text_color=COLOR_GREEN)
                except Exception:
                    doc_path_var.set(f)
                    doc_status_lbl.configure(text=f"✔️ แนบไฟล์แล้ว: {os.path.basename(f)}", text_color=COLOR_GREEN)

        def on_generate_mock():
            cname = club_entry.get().strip() or "New Football Club"
            try:
                bval = float(budget_entry.get().strip().replace(",", ""))
            except Exception:
                bval = 150000000.0
            bname = bank_opt.get()
            cleague = league_opt.get()
            dest = generate_official_bank_statement(cname, bval, bname, cleague)
            doc_path_var.set(dest)
            doc_status_lbl.configure(text=f"✔️ สร้างหนังสือค้ำประกันสำเร็จ: {os.path.basename(dest)}", text_color=COLOR_GREEN)

        ctk.CTkButton(
            btn_row,
            text="📎 เลือกไฟล์...",
            font=FONT_SMALL_BOLD,
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color=TEXT_MAIN,
            width=95,
            height=30,
            corner_radius=15,
            command=on_browse_file
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            btn_row,
            text="⚡ ออกเอกสารจำลองทันที",
            font=FONT_SMALL_BOLD,
            fg_color="#1B9AE5",
            hover_color="#1583C7",
            text_color="#FFFFFF",
            height=30,
            corner_radius=15,
            command=on_generate_mock
        ).pack(side="left", padx=(0, 6))

        def preview_attached():
            p = doc_path_var.get()
            if not p or not os.path.exists(p):
                messagebox.showwarning("ไม่พบเอกสาร", "กรุณาแนบหรือสร้างเอกสารการเงินก่อนดูตัวอย่าง")
                return
            cname = club_entry.get().strip() or "Club"
            try:
                bval = float(budget_entry.get().strip().replace(",", ""))
            except Exception:
                bval = 150000000.0
            open_document_preview_modal(self, p, cname, bval, "Pending Verification")

        ctk.CTkButton(
            btn_row,
            text="👁️ ดูตัวอย่าง",
            font=FONT_SMALL_BOLD,
            fg_color="transparent",
            hover_color="#E0F2FE",
            text_color="#1B9AE5",
            width=80,
            height=30,
            corner_radius=15,
            command=preview_attached
        ).pack(side="left")

        # Submission Handler
        def submit_registration():
            cname = club_entry.get().strip()
            league = league_opt.get()
            uname = u_entry.get().strip().lower()
            email = email_entry.get().strip().lower()
            email_confirm = email_confirm_entry.get().strip().lower()
            pwd1 = p1_entry.get().strip()
            pwd2 = p2_entry.get().strip()
            bank_name = bank_opt.get()
            doc = doc_path_var.get()

            if not cname:
                messagebox.showwarning("ข้อมูลไม่ครบถ้วน", "กรุณากรอกชื่อสโมสร")
                return
            if not uname or not pwd1:
                messagebox.showwarning("ข้อมูลไม่ครบถ้วน", "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน")
                return

            from utils.email_service import validate_email_format
            is_valid_email, err_email = validate_email_format(email)
            if not is_valid_email:
                messagebox.showwarning("อีเมลไม่ถูกต้อง", err_email)
                return

            if email != email_confirm:
                messagebox.showwarning("อีเมลไม่ตรงกัน", "⚠️ อีเมลและช่องยืนยันอีเมลไม่ตรงกัน กรุณาตรวจสอบและพิมพ์ใหม่อีกครั้ง")
                return

            if pwd1 != pwd2:
                messagebox.showwarning("รหัสผ่านไม่ตรงกัน", "รหัสผ่านทั้งสองช่องไม่ตรงกัน")
                return
            if len(pwd1) < 4:
                messagebox.showwarning("รหัสผ่านสั้นเกินไป", "รหัสผ่านต้องมีความยาวอย่างน้อย 4 ตัวอักษร")
                return

            try:
                budget = float(budget_entry.get().strip().replace(",", ""))
                if budget <= 0:
                    raise ValueError()
            except Exception:
                messagebox.showwarning("งบประมาณไม่ถูกต้อง", "กรุณาระบุวงเงินงบประมาณให้ถูกต้อง")
                return

            if not doc or not os.path.exists(doc):
                messagebox.showwarning("ต้องแนบเอกสารการเงิน", "จำเป็นต้องแนบเอกสารรับรองการเงิน (Proof of Funds) เพื่อยืนยันสถานะการเงินของสโมสร")
                return

            conn = get_connection()
            cursor = conn.cursor()

            exists = cursor.execute("SELECT id FROM users WHERE username = ?", (uname,)).fetchone()
            if exists:
                conn.close()
                messagebox.showerror("ชื่อผู้ใช้ซ้ำ", f"ชื่อผู้ใช้ '{uname}' มีผู้ใช้งานแล้ว กรุณาเลือกชื่ออื่น")
                return

            pwd_hash = hash_password(pwd1)
            cursor.execute(
                "INSERT INTO users (username, password_hash, role, status) VALUES (?, ?, 'Club', 'Pending_Verification')",
                (uname, pwd_hash)
            )
            uid = cursor.lastrowid

            cursor.execute("""
                INSERT INTO clubs (user_id, club_name, budget, financial_doc, verification_status, country, bank_name, submitted_budget, email)
                VALUES (?, ?, ?, ?, 'Pending', ?, ?, ?, ?)
            """, (uid, cname, budget, doc, league, bank_name, budget, email))

            conn.commit()
            conn.close()

            log_audit("CLUB_REGISTERED_PENDING", f"New club '{cname}' registered by @{uname} ({email}) with budget €{budget:,.0f} (Awaiting Proof of Funds Verification)")

            self.show_registration_success_modal(cname, uname, budget, doc, email)

        ctk.CTkButton(
            right_col,
            text="🚀 ส่งคำขอลงทะเบียนสโมสร & ยื่นเอกสารการเงิน",
            font=(FONT_FAMILY, 14, "bold"),
            fg_color="#1B9AE5",
            hover_color="#1583C7",
            text_color="#FFFFFF",
            height=44,
            corner_radius=22,
            cursor="hand2",
            command=submit_registration
        ).pack(fill="x", padx=18, pady=(2, 10))

    def show_registration_success_modal(self, cname, uname, budget, doc, email=""):
        """สลับหน้าแสดงผลลงทะเบียนสำเร็จภายในหน้าต่างเดิม (ไม่เด้งป๊อปอัป)"""
        self.login_container.place_forget()
        if self.register_container is not None:
            self.register_container.place_forget()
        if self.success_container is not None:
            self.success_container.destroy()

        card = ctk.CTkFrame(
            self,
            width=520,
            height=430,
            corner_radius=26,
            fg_color="#FFFFFF",
            border_width=0
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)
        self.success_container = card

        ctk.CTkLabel(card, text="🎉", font=("Arial", 44)).pack(pady=(26, 4))
        ctk.CTkLabel(card, text="ยื่นเอกสารการเงินเรียบร้อยแล้ว!", font=FONT_TITLE, text_color=TEXT_MAIN).pack(pady=(0, 4))
        ctk.CTkLabel(card, text=f"สโมสร: {cname}  (@{uname})", font=FONT_BODY_BOLD, text_color="#1B9AE5").pack(pady=(0, 12))

        info_box = ctk.CTkFrame(card, fg_color="#F8FAFC", corner_radius=16, border_width=1, border_color="#E2E8F0")
        info_box.pack(fill="x", padx=32, pady=(0, 20))

        ctk.CTkLabel(info_box, text=f"💰 วงเงินที่ขออนุมัติ: {format_currency(budget)}", font=FONT_BODY_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=18, pady=(12, 3))
        if email:
            ctk.CTkLabel(info_box, text=f"✉️ อีเมลติดต่อที่ลงทะเบียน: {email}", font=FONT_SMALL_BOLD, text_color="#1B9AE5").pack(anchor="w", padx=18, pady=(0, 3))
        ctk.CTkLabel(info_box, text="⏳ สถานะบัญชี: รอแอดมินตรวจสอบเอกสารการเงิน", font=FONT_SMALL_BOLD, text_color="#F59E0B").pack(anchor="w", padx=18, pady=(0, 3))
        ctk.CTkLabel(
            info_box,
            text="เมื่อ Admin ตรวจสอบเอกสารแล้ว ระบบจะส่งอีเมลแจ้งผลการอนุมัติ/ปฏิเสธไปยังอีเมลของท่านโดยอัตโนมัติ",
            font=FONT_SMALL,
            text_color=TEXT_MUTED,
            wraplength=420,
            justify="left"
        ).pack(anchor="w", padx=18, pady=(0, 12))

        ctk.CTkButton(
            card,
            text="⬅ ตกลง / กลับสู่หน้าเข้าสู่ระบบ",
            font=(FONT_FAMILY, 14, "bold"),
            fg_color="#1B9AE5",
            hover_color="#1583C7",
            text_color="#FFFFFF",
            width=260,
            height=44,
            corner_radius=22,
            cursor="hand2",
            command=lambda: self.show_login_view(prefill_username=uname)
        ).pack(pady=(0, 16))

    def show_pending_verification_modal(self, username):
        """แจ้งเตือนเมื่อสโมสรที่ยังไม่ได้รับการอนุมัติพยายามล็อกอิน"""
        modal = ctk.CTkToplevel(self)
        modal.title("อยู่ระหว่างรอการตรวจสอบ")
        modal.geometry("480x360")
        modal.configure(fg_color=BG_DIALOG)
        modal.grab_set()

        ctk.CTkLabel(modal, text="⏳", font=("Arial", 40)).pack(pady=(24, 6))
        ctk.CTkLabel(modal, text="อยู่ระหว่างรอการตรวจสอบเอกสารการเงิน", font=FONT_TITLE, text_color=TEXT_MAIN).pack(pady=(0, 4))
        ctk.CTkLabel(modal, text=f"บัญชีสโมสร: @{username}", font=FONT_BODY_BOLD, text_color=COLOR_APPLE_BLUE).pack(pady=(0, 10))

        ctk.CTkLabel(
            modal,
            text="สโมสรนี้ได้แนบเอกสารรับรองสถานะการเงิน (Proof of Funds) แล้ว และอยู่ระหว่างรอผู้ดูแลระบบ (Admin) ตรวจสอบความถูกต้องของวงเงินงบประมาณเพื่อยืนยันการเป็นสโมสรจริงตามเกณฑ์ UEFA FFP",
            font=FONT_SMALL,
            text_color=TEXT_MUTED,
            justify="center",
            wraplength=380
        ).pack(padx=24, pady=(0, 20))

        ctk.CTkButton(
            modal,
            text="เข้าใจแล้ว / ปิดหน้าต่าง",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_APPLE_BLUE,
            hover_color=COLOR_APPLE_BLUE_HOVER,
            text_color="#FFFFFF",
            height=40,
            corner_radius=20,
            command=modal.destroy
        ).pack(fill="x", padx=30, pady=(0, 14))