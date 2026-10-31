import customtkinter as ctk
from database.db_manager import (
    get_connection, log_audit, complete_transfer_deal,
    negotiate_or_respond_offer, OFFER_STATUS_MEANINGS
)
from utils.security import hash_password
from utils.theme import (
    BG_APP, BG_TOPBAR, BG_CARD, BG_CARD_HOVER, BG_INPUT, BG_DIALOG,
    BORDER_SUBTLE, BORDER_FOCUS, COLOR_APPLE_BLUE, COLOR_APPLE_BLUE_HOVER,
    COLOR_APPLE_DARK, COLOR_APPLE_DARK_HOVER, COLOR_APPLE_GRAY,
    COLOR_GREEN, COLOR_GOLD, COLOR_RED, TEXT_MAIN, TEXT_MUTED, TEXT_DIM,
    FONT_FAMILY, FONT_HERO, FONT_TITLE, FONT_SUBTITLE, FONT_CARD_TITLE,
    FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_SMALL_BOLD,
    format_currency, create_badge, create_stat_card, get_player_image,
    create_stadium_banner, open_quick_switch_modal, clear_player_image_cache,
    bind_black_card_hover, open_player_video_modal
)
from tkinter import messagebox, filedialog
from PIL import Image
import os
import shutil
from utils.financial_docs import open_document_preview_modal
from utils.email_service import send_club_verification_email

class AdminFrame(ctk.CTkFrame):
    def __init__(self, master, logout_callback, switch_callback=None):
        super().__init__(master, fg_color=BG_APP)
        self.logout_callback = logout_callback
        self.switch_callback = switch_callback

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_top_navbar()
        self._build_content_area()
        self.show_dashboard()

    # ==================== TOP NAVIGATION BAR ====================
    def _build_top_navbar(self):
        self.topbar = ctk.CTkFrame(self, height=52, fg_color=BG_TOPBAR, corner_radius=0, border_width=1, border_color=BORDER_SUBTLE)
        self.topbar.grid(row=0, column=0, sticky="ew")
        self.topbar.grid_propagate(False)

        # 1. Left Logo
        logo_box = ctk.CTkFrame(self.topbar, fg_color="transparent")
        logo_box.pack(side="left", padx=(25, 10))
        ctk.CTkLabel(logo_box, text="👑  ระบบผู้ดูแลระบบ", font=(FONT_FAMILY, 15, "bold"), text_color=TEXT_MAIN).pack(side="left")

        # 2. Right Dropdown Menu (Packed FIRST on right to guarantee it will never be squeezed or cut off)
        right_box = ctk.CTkFrame(self.topbar, fg_color="transparent")
        right_box.pack(side="right", padx=(0, 20))

        # Admin Account Dropdown Menu with Multiple Options (แบบกดลงมาแล้วมีหลายตัวเลือก)
        self.admin_menu_options = [
            "👑 ผู้ดูแลระบบ ▾",
            "👤 ข้อมูลผู้ดูแลระบบ",
            "⚡ สลับบทบาทผู้ใช้",
            "🔄 รีเฟรชระบบ",
            "🔒 ล็อกหน้าจอ",
            "🚪 ออกจากระบบ"
        ]
        self.admin_account_var = ctk.StringVar(value=self.admin_menu_options[0])

        self.admin_dropdown = ctk.CTkOptionMenu(
            right_box,
            variable=self.admin_account_var,
            values=self.admin_menu_options,
            width=215,
            height=34,
            corner_radius=17,
            fg_color=BG_CARD,
            button_color=COLOR_APPLE_BLUE,
            button_hover_color=COLOR_APPLE_BLUE_HOVER,
            text_color=TEXT_MAIN,
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color=TEXT_MAIN,
            dropdown_hover_color=BG_CARD_HOVER,
            font=FONT_SMALL_BOLD,
            dropdown_font=FONT_SMALL,
            command=self._handle_admin_dropdown_action
        )
        self.admin_dropdown.pack(side="right")

        # 3. Center Navigation Menu (เมนูภาษาไทยทั้งหมด)
        self.nav_buttons = {}
        center_box = ctk.CTkFrame(self.topbar, fg_color="transparent")
        center_box.pack(side="left", expand=True)

        menus = [
            ("dashboard", "ภาพรวมระบบ", self.show_dashboard),
            ("verifications", "ตรวจสอบสโมสร 📑", self.show_club_verifications),
            ("users", "จัดการบัญชีผู้ใช้", self.show_users_management),
            ("players", "จัดการนักเตะ", self.show_players_oversight),
            ("transfers", "ตรวจสอบการซื้อขาย", self.show_transfer_audit),
            ("logs", "บันทึกประวัติระบบ", self.show_audit_logs)
        ]
        for key, label, cmd in menus:
            btn = ctk.CTkButton(
                center_box,
                text=label,
                font=FONT_BODY_BOLD,
                fg_color="transparent",
                hover_color=BG_CARD_HOVER,
                text_color=TEXT_MUTED,
                height=34,
                corner_radius=17,
                command=cmd
            )
            btn.pack(side="left", padx=5)
            self.nav_buttons[key] = btn

    def _handle_admin_dropdown_action(self, choice):
        # Reset dropdown label back to default header so it always displays cleanly
        self.admin_account_var.set(self.admin_menu_options[0])

        if "ออกจากระบบ" in choice or "Sign Out" in choice:
            self.do_logout()
        elif "ล็อกหน้าจอ" in choice or "Lock" in choice:
            self.do_lock_session()
        elif "สลับบทบาท" in choice or "Switch Portal" in choice:
            if self.switch_callback:
                open_quick_switch_modal(self, self.switch_callback)
        elif "ข้อมูลผู้ดูแลระบบ" in choice or "Profile" in choice:
            self.show_admin_profile_modal()
        elif "รีเฟรช" in choice or "Refresh" in choice:
            self.refresh_current_view()

    def do_logout(self):
        if messagebox.askyesno("ยืนยันการออกจากระบบ", "คุณต้องการออกจากระบบ (Sign Out) หรือไม่?"):
            from utils.session import CurrentSession
            CurrentSession.logout()
            if self.logout_callback:
                self.logout_callback()

    def do_lock_session(self):
        from utils.session import CurrentSession
        CurrentSession.logout()
        messagebox.showinfo("Session Locked", "หน้าจอถูกล็อกเรียบร้อยแล้ว กรุณาเข้าสู่ระบบใหม่อีกครั้ง")
        if self.logout_callback:
            self.logout_callback()

    def refresh_current_view(self):
        for key, btn in self.nav_buttons.items():
            if btn.cget("fg_color") != "transparent":
                if key == "dashboard": self.show_dashboard()
                elif key == "verifications": self.show_club_verifications()
                elif key == "users": self.show_users_management()
                elif key == "players": self.show_players_oversight()
                elif key == "transfers": self.show_transfer_audit()
                elif key == "logs": self.show_audit_logs()
                return
        self.show_dashboard()

    def show_admin_profile_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Admin Account Profile")
        modal.geometry("460x490")
        modal.configure(fg_color=BG_DIALOG)
        modal.grab_set()

        modal.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 230
        y = self.winfo_rooty() + (self.winfo_height() // 2) - 245
        modal.geometry(f"+{max(0, x)}+{max(0, y)}")

        card = ctk.CTkFrame(modal, fg_color=BG_CARD, corner_radius=20, border_width=1, border_color=BORDER_SUBTLE)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(card, text="👑", font=(FONT_FAMILY, 44)).pack(pady=(16, 2))
        ctk.CTkLabel(card, text="ผู้ดูแลระบบสูงสุด", font=FONT_TITLE, text_color=TEXT_MAIN).pack()
        ctk.CTkLabel(card, text="ผู้ดูแลระบบส่วนกลาง • มาตรฐาน UEFA FFP & TMS", font=FONT_SMALL, text_color=TEXT_MUTED).pack(pady=(2, 14))

        info_box = ctk.CTkFrame(card, fg_color="#F8FAFC", corner_radius=12, border_width=1, border_color=BORDER_SUBTLE)
        info_box.pack(fill="x", padx=16, pady=(0, 14))

        items = [
            ("ชื่อผู้ใช้งาน:", "admin"),
            ("ระดับสิทธิ์การใช้งาน:", "ผู้ดูแลระบบสูงสุด (Super Admin)"),
            ("การตรวจสอบทางการเงิน:", "อนุมัติ / ปฏิเสธงบประมาณสโมสร"),
            ("การจัดการข้อมูลนักเตะ:", "เพิ่ม / แก้ไข / อัปโหลดรูปภาพ"),
            ("สถานะเซสชัน:", "🟢 กำลังใช้งาน (Active)")
        ]
        for label, val in items:
            row = ctk.CTkFrame(info_box, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=5)
            ctk.CTkLabel(row, text=label, font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(row, text=val, font=FONT_SMALL, text_color=TEXT_MAIN).pack(side="right")

        btn_box = ctk.CTkFrame(card, fg_color="transparent")
        btn_box.pack(fill="x", padx=16, pady=(0, 10))

        if self.switch_callback:
            ctk.CTkButton(
                btn_box,
                text="⚡ สลับผู้ใช้งาน",
                font=FONT_SMALL_BOLD,
                fg_color=BG_CARD_HOVER,
                hover_color=BORDER_SUBTLE,
                text_color=COLOR_APPLE_BLUE,
                height=34,
                corner_radius=17,
                command=lambda: [modal.destroy(), open_quick_switch_modal(self, self.switch_callback)]
            ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(
            btn_box,
            text="🚪 ออกจากระบบ",
            font=FONT_SMALL_BOLD,
            fg_color="#FEE2E2",
            hover_color="#FECACA",
            text_color=COLOR_RED,
            height=34,
            corner_radius=17,
            command=lambda: [modal.destroy(), self.do_logout()]
        ).pack(side="right", fill="x", expand=True, padx=(4, 0))

        ctk.CTkButton(
            card,
            text="ปิดหน้าต่าง",
            font=FONT_SMALL_BOLD,
            fg_color=COLOR_APPLE_DARK,
            hover_color="#000000",
            text_color="#FFFFFF",
            height=36,
            corner_radius=18,
            command=modal.destroy
        ).pack(fill="x", padx=16, pady=(0, 12))

    def _highlight_nav(self, active_key):
        for k, btn in self.nav_buttons.items():
            if k == active_key:
                btn.configure(fg_color=BG_CARD, text_color=TEXT_MAIN)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_MUTED)

    def _build_content_area(self):
        self.main_content = ctk.CTkFrame(self, corner_radius=0, fg_color=BG_APP)
        self.main_content.grid(row=1, column=0, sticky="nsew")

    def clear_content(self):
        for widget in self.main_content.winfo_children():
            widget.destroy()

    # ==================== 1. DASHBOARD ====================
    def show_dashboard(self):
        self._highlight_nav("dashboard")
        self.clear_content()

        scroll = ctk.CTkScrollableFrame(self.main_content, fg_color=BG_APP)
        scroll.pack(fill="both", expand=True)

        create_stadium_banner(
            scroll,
            "ภาพรวมระบบและสถิติ (Dashboard)",
            "สรุปภาพรวมระบบตลาดซื้อขาย สภาพคล่องทางการเงิน บัญชีสโมสร และสถานะการตรวจสอบระเบียบ FFP"
        )

        conn = get_connection()
        cursor = conn.cursor()
        total_users = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        total_players = cursor.execute("SELECT COUNT(*) FROM players").fetchone()[0]
        total_clubs = cursor.execute("SELECT COUNT(*) FROM clubs").fetchone()[0]
        total_agents = cursor.execute("SELECT COUNT(*) FROM agents").fetchone()[0]
        total_market_val = cursor.execute("SELECT IFNULL(SUM(estimated_value), 0) FROM players").fetchone()[0]
        completed_vol = cursor.execute("SELECT IFNULL(SUM(offer_amount), 0) FROM transfer_offers WHERE status='Completed'").fetchone()[0]
        pending_clubs = cursor.execute("SELECT COUNT(*) FROM clubs WHERE verification_status='Pending'").fetchone()[0]
        
        recent_transfers = cursor.execute("""
            SELECT t.id, p.id as pid, p.known_as, p.main_position, c.club_name, t.offer_amount, t.status
            FROM transfer_offers t
            JOIN players p ON t.player_id = p.id
            JOIN clubs c ON t.club_id = c.id
            ORDER BY t.id DESC LIMIT 5
        """).fetchall()

        club_summary_list = cursor.execute("""
            SELECT c.id, c.club_name, c.budget, c.country, c.email, c.verification_status, u.username
            FROM clubs c
            JOIN users u ON c.user_id = u.id
            ORDER BY (CASE WHEN c.verification_status='Pending' THEN 0 ELSE 1 END), c.id DESC LIMIT 6
        """).fetchall()
        conn.close()

        # Alert banner for pending audits
        if pending_clubs > 0:
            alert_box = ctk.CTkFrame(scroll, fg_color="#FFFBEB", border_width=1.5, border_color="#F59E0B", corner_radius=16)
            alert_box.pack(fill="x", padx=40, pady=(0, 20))
            ctk.CTkLabel(
                alert_box,
                text=f"⚠️  มีสโมสรใหม่ {pending_clubs} แห่ง ยื่นเอกสารรับรองการเงินรอการตรวจสอบเพื่อยืนยันวงเงิน",
                font=FONT_BODY_BOLD,
                text_color="#B45309"
            ).pack(side="left", padx=20, pady=14)
            ctk.CTkButton(
                alert_box,
                text="ตรวจสอบเอกสารสโมสรทันที ➔",
                font=FONT_SMALL_BOLD,
                fg_color="#F59E0B",
                hover_color="#D97706",
                text_color="#FFFFFF",
                height=34,
                corner_radius=17,
                command=self.show_club_verifications
            ).pack(side="right", padx=20)

        # Quick Actions Bar
        actions_bar = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=16, border_width=1, border_color=BORDER_SUBTLE)
        actions_bar.pack(fill="x", padx=40, pady=(0, 20))

        ctk.CTkLabel(actions_bar, text="⚡ เมนูลัด:", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(side="left", padx=(16, 8), pady=10)

        for btn_text, btn_cmd in [
            ("🔍 ตรวจสอบเอกสารสโมสร", self.show_club_verifications),
            ("➕ เพิ่มนักเตะใหม่", self.open_add_player_dialog),
            ("⚽ จัดการนักเตะ", self.show_players_oversight),
            ("👥 จัดการบัญชีผู้ใช้", self.show_users_management),
            ("📄 ประวัติระบบ", self.show_audit_logs)
        ]:
            ctk.CTkButton(
                actions_bar,
                text=btn_text,
                font=FONT_SMALL_BOLD,
                fg_color=BG_CARD_HOVER,
                hover_color=BORDER_SUBTLE,
                text_color=TEXT_MAIN,
                height=30,
                corner_radius=15,
                command=btn_cmd
            ).pack(side="left", padx=4, pady=8)

        # Stats Cards Grid (สถิติภาพรวมภาษาไทย)
        stat_row = ctk.CTkFrame(scroll, fg_color="transparent")
        stat_row.pack(fill="x", padx=40, pady=(0, 24))
        stat_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        create_stat_card(stat_row, "บัญชีผู้ใช้ทั้งหมด", f"{total_users} บัญชี", "👥").grid(row=0, column=0, padx=6, sticky="ew")
        create_stat_card(stat_row, "นักเตะในระบบ", f"{total_players} คน ({format_currency(total_market_val)})", "⚽").grid(row=0, column=1, padx=6, sticky="ew")
        create_stat_card(stat_row, "สโมสร / เอเยนต์", f"{total_clubs} สโมสร • {total_agents} เอเยนต์", "🏟️").grid(row=0, column=2, padx=6, sticky="ew")
        create_stat_card(stat_row, "มูลค่าการซื้อขายสำเร็จ", format_currency(completed_vol), "💰").grid(row=0, column=3, padx=6, sticky="ew")

        # Two Columns Split: Left (Recent Transfers) & Right (Club Status & Emails)
        two_col = ctk.CTkFrame(scroll, fg_color="transparent")
        two_col.pack(fill="x", padx=40, pady=(0, 40))
        two_col.grid_columnconfigure(0, weight=6)
        two_col.grid_columnconfigure(1, weight=5)

        # Left Column: Recent Deals
        left_box = ctk.CTkFrame(two_col, fg_color=BG_CARD, corner_radius=18, border_width=1, border_color=BORDER_SUBTLE)
        left_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        head_l = ctk.CTkFrame(left_box, fg_color="transparent")
        head_l.pack(fill="x", padx=20, pady=(16, 12))
        ctk.CTkLabel(head_l, text="⚽ กิจกรรมการซื้อขายล่าสุด", font=FONT_CARD_TITLE, text_color=TEXT_MAIN).pack(side="left")
        ctk.CTkButton(head_l, text="ดูนักเตะทั้งหมด ➔", font=FONT_SMALL, fg_color="transparent", hover_color=BG_CARD_HOVER, text_color=COLOR_APPLE_BLUE, height=24, command=self.show_players_oversight).pack(side="right")

        if not recent_transfers:
            ctk.CTkLabel(left_box, text="ยังไม่มีรายการข้อเสนอในระบบ", font=FONT_BODY, text_color=TEXT_MUTED).pack(pady=40)
        else:
            for deal in recent_transfers:
                row = ctk.CTkFrame(left_box, fg_color="#F8FAFC", corner_radius=12, border_width=1, border_color=BORDER_SUBTLE)
                row.pack(fill="x", padx=16, pady=4)

                photo = get_player_image(deal['pid'], size=(38, 38))
                lbl_pic = ctk.CTkLabel(row, text="⚽" if not photo else "", image=photo, width=38, height=38)
                lbl_pic.image = photo
                lbl_pic.pack(side="left", padx=10, pady=8)

                info_col = ctk.CTkFrame(row, fg_color="transparent")
                info_col.pack(side="left", fill="both", expand=True, padx=4)
                ctk.CTkLabel(info_col, text=deal['known_as'], font=FONT_BODY_BOLD, text_color=TEXT_MAIN, anchor="w").pack(fill="x")
                ctk.CTkLabel(info_col, text=f"สู่: {deal['club_name']}  •  ตำแหน่ง: {deal['main_position']}", font=FONT_SMALL, text_color=TEXT_MUTED, anchor="w").pack(fill="x")

                ctk.CTkLabel(row, text=format_currency(deal['offer_amount']), font=FONT_BODY_BOLD, text_color=COLOR_GREEN).pack(side="left", padx=10)
                create_badge(row, deal['status']).pack(side="right", padx=12)

            ctk.CTkFrame(left_box, height=8, fg_color="transparent").pack()

        # Right Column: Club Financial Status & Contact Emails
        right_box = ctk.CTkFrame(two_col, fg_color=BG_CARD, corner_radius=18, border_width=1, border_color=BORDER_SUBTLE)
        right_box.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        head_r = ctk.CTkFrame(right_box, fg_color="transparent")
        head_r.pack(fill="x", padx=20, pady=(16, 12))
        ctk.CTkLabel(head_r, text="🏛️ สรุปสถานะสโมสร & อีเมลติดต่อ", font=FONT_CARD_TITLE, text_color=TEXT_MAIN).pack(side="left")
        ctk.CTkButton(head_r, text="ตรวจสอบเอกสาร ➔", font=FONT_SMALL, fg_color="transparent", hover_color=BG_CARD_HOVER, text_color=COLOR_APPLE_BLUE, height=24, command=self.show_club_verifications).pack(side="right")

        if not club_summary_list:
            ctk.CTkLabel(right_box, text="ยังไม่มีสโมสรในระบบ", font=FONT_BODY, text_color=TEXT_MUTED).pack(pady=40)
        else:
            for cl in club_summary_list:
                c_row = ctk.CTkFrame(right_box, fg_color="#F8FAFC", corner_radius=12, border_width=1, border_color=BORDER_SUBTLE)
                c_row.pack(fill="x", padx=16, pady=4)

                c_info = ctk.CTkFrame(c_row, fg_color="transparent")
                c_info.pack(side="left", fill="both", expand=True, padx=12, pady=8)

                title_l = ctk.CTkLabel(c_info, text=f"🏟️ {cl['club_name']} (@{cl['username']})", font=FONT_BODY_BOLD, text_color=TEXT_MAIN, anchor="w")
                title_l.pack(fill="x")

                em_display = cl['email'] if cl['email'] else "ยังไม่ได้ระบุอีเมล"
                ctk.CTkLabel(c_info, text=f"✉️ {em_display}  •  งบ: {format_currency(cl['budget'])}", font=FONT_SMALL, text_color=TEXT_MUTED, anchor="w").pack(fill="x")

                st = cl['verification_status'] or 'Approved'
                create_badge(c_row, st).pack(side="right", padx=12)

            ctk.CTkFrame(right_box, height=8, fg_color="transparent").pack()

    # ==================== 2. MANAGE USERS ====================
    def show_users_management(self):
        self._highlight_nav("users")
        self.clear_content()

        scroll = ctk.CTkScrollableFrame(self.main_content, fg_color=BG_APP)
        scroll.pack(fill="both", expand=True)

        def add_create(p):
            ctk.CTkButton(
                p,
                text="+ สร้างบัญชีใหม่",
                font=FONT_SMALL_BOLD,
                fg_color=COLOR_APPLE_BLUE,
                hover_color=COLOR_APPLE_BLUE_HOVER,
                corner_radius=17,
                height=34,
                command=self.open_create_user_dialog
            ).pack(side="right")

        create_stadium_banner(scroll, "จัดการบัญชีผู้ใช้งาน", "จัดการข้อมูลบัญชีสโมสร ตัวแทนนักเตะ (Agent) และผู้ดูแลระบบ", right_widget_fn=add_create)

        # Search Bar
        search_box = ctk.CTkFrame(scroll, fg_color="transparent")
        search_box.pack(fill="x", padx=40, pady=(0, 20))

        self.user_search = ctk.CTkEntry(
            search_box,
            placeholder_text="🔍 ค้นหาบัญชีผู้ใช้ตามชื่อ หรือสโมสร...",
            fg_color=BG_CARD,
            border_width=0,
            text_color=TEXT_MAIN,
            height=38,
            width=320,
            corner_radius=19
        )
        self.user_search.pack(side="left")
        self._user_search_timer = None
        def _on_user_search(e):
            if self._user_search_timer:
                self.after_cancel(self._user_search_timer)
            self._user_search_timer = self.after(200, self._render_users_grid)
        self.user_search.bind("<KeyRelease>", _on_user_search)

        self.users_grid = ctk.CTkFrame(scroll, fg_color=BG_APP)
        self.users_grid.pack(fill="x", padx=40, pady=(0, 40))
        self.users_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._render_users_grid()

    def _render_users_grid(self):
        for widget in self.users_grid.winfo_children():
            widget.destroy()

        q = self.user_search.get().strip().lower() if hasattr(self, 'user_search') else ""
        conn = get_connection()
        sql = """
            SELECT u.id, u.username, u.role, u.status, u.created_at,
                   c.id as club_id, c.club_name, c.email as club_email, c.budget as club_budget, c.verification_status as club_verif,
                   a.id as agent_id, a.first_name, a.last_name, a.agency_name
            FROM users u
            LEFT JOIN clubs c ON u.id = c.user_id
            LEFT JOIN agents a ON u.id = a.user_id
        """
        params = []
        if q:
            sql += " WHERE LOWER(u.username) LIKE ? OR LOWER(IFNULL(c.club_name, '')) LIKE ? OR LOWER(IFNULL(a.agency_name, '')) LIKE ?"
            params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
        sql += " ORDER BY u.id ASC"
        users = conn.execute(sql, tuple(params)).fetchall()
        conn.close()

        for idx, u in enumerate(users):
            card = ctk.CTkFrame(self.users_grid, fg_color=BG_CARD, corner_radius=20, border_width=1, border_color=BORDER_SUBTLE, height=255)
            card.grid(row=idx // 4, column=idx % 4, padx=10, pady=10, sticky="nsew")
            card.pack_propagate(False)

            icon = "👑" if u['role'] == "Admin" else ("🏟️" if u['role'] == "Club" else "💼")
            ctk.CTkLabel(card, text=icon, font=("Arial", 30)).pack(pady=(16, 2))
            ctk.CTkLabel(card, text=u['username'], font=(FONT_FAMILY, 15, "bold"), text_color=TEXT_MAIN).pack(pady=(0, 2))

            b_frame = ctk.CTkFrame(card, fg_color="transparent")
            b_frame.pack(pady=4)
            create_badge(b_frame, u['role'], "Price Negotiation").pack(side="left", padx=2)
            create_badge(b_frame, u['status']).pack(side="left", padx=2)

            # Sub-info line
            if u['role'] == 'Club':
                c_display = u['club_name'] if u['club_name'] else "สโมสรยังไม่ระบุชื่อ"
                ctk.CTkLabel(card, text=f"🏟️ {c_display}", font=FONT_SMALL, text_color=TEXT_MUTED).pack(pady=(2, 0))
            elif u['role'] == 'Agent':
                a_display = u['agency_name'] if u['agency_name'] else f"{u['first_name']} Agency"
                ctk.CTkLabel(card, text=f"💼 {a_display}", font=FONT_SMALL, text_color=TEXT_MUTED).pack(pady=(2, 0))
            else:
                ctk.CTkLabel(card, text="🛡️ ผู้ดูแลระบบส่วนกลาง", font=FONT_SMALL, text_color=TEXT_MUTED).pack(pady=(2, 0))

            # Action Buttons Row
            b_row = ctk.CTkFrame(card, fg_color="transparent")
            b_row.pack(fill="x", padx=12, pady=(6, 12), side="bottom")

            ctk.CTkButton(
                b_row,
                text="✏️ แก้ไข",
                font=FONT_SMALL_BOLD,
                fg_color=BG_CARD_HOVER,
                hover_color=BORDER_SUBTLE,
                text_color=COLOR_APPLE_BLUE,
                height=30,
                corner_radius=15,
                command=lambda user_item=u: self.open_edit_user_dialog(user_item)
            ).pack(side="left", fill="x", expand=True, padx=(0, 4))

            if u['role'] != 'Admin':
                is_active = (u['status'] == "Active")
                ctk.CTkButton(
                    b_row,
                    text="ระงับ" if is_active else "เปิดใช้",
                    font=FONT_SMALL_BOLD,
                    fg_color=BG_CARD_HOVER,
                    hover_color=BORDER_SUBTLE,
                    text_color=COLOR_RED if is_active else COLOR_GREEN,
                    height=30,
                    corner_radius=15,
                    command=lambda uid=u['id'], cur=u['status']: self.toggle_user_status(uid, cur)
                ).pack(side="left", padx=(0, 4))

                ctk.CTkButton(
                    b_row,
                    text="🗑️",
                    font=FONT_SMALL_BOLD,
                    fg_color=BG_CARD_HOVER,
                    hover_color=BORDER_SUBTLE,
                    text_color=COLOR_RED,
                    width=32,
                    height=30,
                    corner_radius=15,
                    command=lambda uid=u['id'], un=u['username'], r=u['role']: self.delete_user_account(uid, un, r)
                ).pack(side="right")

    def open_edit_user_dialog(self, u):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"แก้ไขบัญชีผู้ใช้ - @{u['username']}")
        dialog.geometry("500x640")
        dialog.configure(fg_color=BG_DIALOG)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 250
        y = self.winfo_rooty() + (self.winfo_height() // 2) - 320
        dialog.geometry(f"+{max(0, x)}+{max(0, y)}")

        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(scroll, text="✏️ แก้ไขข้อมูลบัญชีผู้ใช้", font=FONT_SUBTITLE, text_color=TEXT_MAIN).pack(pady=(4, 2))
        ctk.CTkLabel(scroll, text=f"รหัสผู้ใช้ #{u['id']}  •  บทบาท: {u['role']}", font=FONT_SMALL, text_color=TEXT_MUTED).pack(pady=(0, 16))

        # Card 1: ข้อมูลบัญชีพื้นฐาน
        card1 = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=16, border_width=1, border_color=BORDER_SUBTLE)
        card1.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(card1, text="🔑 ข้อมูลบัญชีผู้ใช้", font=FONT_BODY_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=16, pady=(14, 10))

        # Username
        ctk.CTkLabel(card1, text="ชื่อผู้ใช้งาน:", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(2, 2))
        u_entry = ctk.CTkEntry(card1, fg_color="#F8FAFC", border_width=1, border_color=BORDER_SUBTLE, text_color=TEXT_MAIN, height=36, corner_radius=10)
        u_entry.pack(fill="x", padx=16, pady=(0, 8))
        u_entry.insert(0, u['username'])

        # Password
        ctk.CTkLabel(card1, text="รหัสผ่านใหม่ (เว้นว่างไว้หากไม่ต้องการเปลี่ยน):", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(2, 2))
        p_entry = ctk.CTkEntry(card1, fg_color="#F8FAFC", border_width=1, border_color=BORDER_SUBTLE, text_color=TEXT_MAIN, show="•", placeholder_text="กรอกรหัสผ่านใหม่...", height=36, corner_radius=10)
        p_entry.pack(fill="x", padx=16, pady=(0, 8))

        # Status
        ctk.CTkLabel(card1, text="สถานะบัญชี:", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(2, 2))
        status_map = {
            "ใช้งานปกติ (Active)": "Active",
            "ระงับการใช้งาน (Suspended)": "Suspended",
            "รอการตรวจสอบ (Pending)": "Pending_Verification"
        }
        rev_status_map = {v: k for k, v in status_map.items()}
        status_var = ctk.StringVar(value=rev_status_map.get(u['status'], "ใช้งานปกติ (Active)"))
        status_menu = ctk.CTkOptionMenu(
            card1,
            variable=status_var,
            values=list(status_map.keys()),
            fg_color="#F8FAFC",
            button_color=COLOR_APPLE_BLUE,
            button_hover_color=COLOR_APPLE_BLUE_HOVER,
            text_color=TEXT_MAIN,
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color=TEXT_MAIN,
            height=36,
            corner_radius=10
        )
        status_menu.pack(fill="x", padx=16, pady=(0, 14))

        # Card 2: ข้อมูลสโมสร / เอเยนต์
        role = u['role']
        cname_entry = None
        email_entry = None
        budget_entry = None
        verif_var = None
        verif_map = {
            "อนุมัติแล้ว (Approved)": "Approved",
            "รอตรวจสอบ (Pending)": "Pending",
            "ปฏิเสธ (Rejected)": "Rejected"
        }
        rev_verif_map = {v: k for k, v in verif_map.items()}
        fname_entry = None
        lname_entry = None
        agency_entry = None

        if role == "Club":
            card2 = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=16, border_width=1, border_color=BORDER_SUBTLE)
            card2.pack(fill="x", pady=(0, 14))

            ctk.CTkLabel(card2, text="🏟️ ข้อมูลสโมสร", font=FONT_BODY_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=16, pady=(14, 10))

            ctk.CTkLabel(card2, text="ชื่อสโมสร:", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(2, 2))
            cname_entry = ctk.CTkEntry(card2, fg_color="#F8FAFC", border_width=1, border_color=BORDER_SUBTLE, text_color=TEXT_MAIN, height=36, corner_radius=10)
            cname_entry.pack(fill="x", padx=16, pady=(0, 8))
            cname_entry.insert(0, u['club_name'] or '')

            ctk.CTkLabel(card2, text="อีเมลติดต่อสโมสร:", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(2, 2))
            email_entry = ctk.CTkEntry(card2, fg_color="#F8FAFC", border_width=1, border_color=BORDER_SUBTLE, text_color=TEXT_MAIN, height=36, corner_radius=10)
            email_entry.pack(fill="x", padx=16, pady=(0, 8))
            email_entry.insert(0, u['club_email'] or '')

            ctk.CTkLabel(card2, text="งบประมาณสโมสร (€):", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(2, 2))
            budget_entry = ctk.CTkEntry(card2, fg_color="#F8FAFC", border_width=1, border_color=BORDER_SUBTLE, text_color=TEXT_MAIN, height=36, corner_radius=10)
            budget_entry.pack(fill="x", padx=16, pady=(0, 8))
            cur_b = u['club_budget'] if u['club_budget'] is not None else 0
            budget_entry.insert(0, f"{cur_b:,.0f}")

            ctk.CTkLabel(card2, text="สถานะการตรวจสอบการเงิน:", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(2, 2))
            cur_v = u['club_verif'] or "Approved"
            verif_var = ctk.StringVar(value=rev_verif_map.get(cur_v, "อนุมัติแล้ว (Approved)"))
            verif_menu = ctk.CTkOptionMenu(
                card2,
                variable=verif_var,
                values=list(verif_map.keys()),
                fg_color="#F8FAFC",
                button_color=COLOR_APPLE_BLUE,
                button_hover_color=COLOR_APPLE_BLUE_HOVER,
                text_color=TEXT_MAIN,
                dropdown_fg_color="#FFFFFF",
                dropdown_text_color=TEXT_MAIN,
                height=36,
                corner_radius=10
            )
            verif_menu.pack(fill="x", padx=16, pady=(0, 14))

        elif role == "Agent":
            card2 = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=16, border_width=1, border_color=BORDER_SUBTLE)
            card2.pack(fill="x", pady=(0, 14))

            ctk.CTkLabel(card2, text="💼 ข้อมูลเอเยนต์", font=FONT_BODY_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=16, pady=(14, 10))

            ctk.CTkLabel(card2, text="ชื่อจริง:", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(2, 2))
            fname_entry = ctk.CTkEntry(card2, fg_color="#F8FAFC", border_width=1, border_color=BORDER_SUBTLE, text_color=TEXT_MAIN, height=36, corner_radius=10)
            fname_entry.pack(fill="x", padx=16, pady=(0, 8))
            fname_entry.insert(0, u['first_name'] or '')

            ctk.CTkLabel(card2, text="นามสกุล:", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(2, 2))
            lname_entry = ctk.CTkEntry(card2, fg_color="#F8FAFC", border_width=1, border_color=BORDER_SUBTLE, text_color=TEXT_MAIN, height=36, corner_radius=10)
            lname_entry.pack(fill="x", padx=16, pady=(0, 8))
            lname_entry.insert(0, u['last_name'] or '')

            ctk.CTkLabel(card2, text="ชื่อบริษัทเอเยนซี่:", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(2, 2))
            agency_entry = ctk.CTkEntry(card2, fg_color="#F8FAFC", border_width=1, border_color=BORDER_SUBTLE, text_color=TEXT_MAIN, height=36, corner_radius=10)
            agency_entry.pack(fill="x", padx=16, pady=(0, 14))
            agency_entry.insert(0, u['agency_name'] or '')

        # Action Buttons
        btn_box = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_box.pack(fill="x", pady=(8, 16))

        def save_changes():
            new_u = u_entry.get().strip()
            new_p = p_entry.get().strip()
            new_status = status_map.get(status_var.get(), status_var.get())

            if not new_u:
                messagebox.showwarning("ข้อผิดพลาด", "ชื่อผู้ใช้งาน (Username) ต้องไม่ว่างเปล่า", parent=dialog)
                return

            import re
            conn = get_connection()
            cur = conn.cursor()

            # Check duplicate username
            dup = cur.execute("SELECT id FROM users WHERE username = ? AND id != ?", (new_u, u['id'])).fetchone()
            if dup:
                messagebox.showwarning("ชื่อซ้ำ", f"ชื่อผู้ใช้งาน '{new_u}' มีในระบบแล้ว กรุณาใช้ชื่ออื่น", parent=dialog)
                conn.close()
                return

            # Update User Credentials
            if new_p:
                hashed = hash_password(new_p)
                cur.execute("UPDATE users SET username = ?, password_hash = ?, status = ? WHERE id = ?", (new_u, hashed, new_status, u['id']))
            else:
                cur.execute("UPDATE users SET username = ?, status = ? WHERE id = ?", (new_u, new_status, u['id']))

            # Update Role Data
            if role == "Club" and cname_entry:
                new_cname = cname_entry.get().strip() or f"{new_u.capitalize()} F.C."
                new_email = email_entry.get().strip() if email_entry else ""
                raw_b = budget_entry.get().strip() if budget_entry else "0"
                clean_b = re.sub(r"[^\d.]", "", raw_b)
                new_budget = float(clean_b) if clean_b else 0.0
                new_verif = verif_map.get(verif_var.get(), "Approved") if verif_var else "Approved"

                if new_email:
                    from utils.email_service import validate_email_format
                    valid_em, em_err = validate_email_format(new_email)
                    if not valid_em:
                        messagebox.showwarning("รูปแบบอีเมลไม่ถูกต้อง", em_err, parent=dialog)
                        conn.close()
                        return

                old_cname = u['club_name']
                cur.execute("""
                    UPDATE clubs
                    SET club_name = ?, email = ?, budget = ?, verification_status = ?
                    WHERE user_id = ?
                """, (new_cname, new_email, new_budget, new_verif, u['id']))

                if old_cname and old_cname != new_cname:
                    cur.execute("UPDATE players SET current_club = ? WHERE current_club = ?", (new_cname, old_cname))
                    cur.execute("UPDATE transfer_offers SET selling_club = ? WHERE selling_club = ?", (new_cname, old_cname))

            elif role == "Agent" and fname_entry:
                new_fn = fname_entry.get().strip()
                new_ln = lname_entry.get().strip()
                new_ag = agency_entry.get().strip() or f"{new_fn} Agency"
                cur.execute("""
                    UPDATE agents
                    SET first_name = ?, last_name = ?, agency_name = ?
                    WHERE user_id = ?
                """, (new_fn, new_ln, new_ag, u['id']))

            conn.commit()
            conn.close()
            log_audit("USER_UPDATED", f"Admin updated user #{u['id']} ({new_u})")
            messagebox.showinfo("สำเร็จ", f"แก้ไขข้อมูลผู้ใช้ '{new_u}' เรียบร้อยแล้ว!", parent=dialog)
            dialog.destroy()
            self._render_users_grid()

        ctk.CTkButton(
            btn_box,
            text="ยกเลิก",
            font=FONT_SMALL_BOLD,
            fg_color=BG_CARD_HOVER,
            hover_color=BORDER_SUBTLE,
            text_color=TEXT_MAIN,
            height=38,
            corner_radius=19,
            command=dialog.destroy
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            btn_box,
            text="💾 บันทึกข้อมูล",
            font=FONT_SMALL_BOLD,
            fg_color=COLOR_APPLE_BLUE,
            hover_color=COLOR_APPLE_BLUE_HOVER,
            text_color="#FFFFFF",
            height=38,
            corner_radius=19,
            command=save_changes
        ).pack(side="right", fill="x", expand=True, padx=(6, 0))

    def toggle_user_status(self, uid, cur):
        new_st = "Suspended" if cur == "Active" else "Active"
        conn = get_connection()
        conn.execute("UPDATE users SET status = ? WHERE id = ?", (new_st, uid))
        conn.commit()
        conn.close()
        log_audit("USER_STATUS_CHANGE", f"Admin changed user #{uid} status to {new_st}")
        self._render_users_grid()

    def delete_user_account(self, uid, username, role):
        if not messagebox.askyesno("ยืนยันการลบ", f"ต้องการลบบัญชี '{username}' ({role}) ออกจากระบบหรือไม่?"):
            return
        conn = get_connection()
        if role == 'Club':
            conn.execute("UPDATE players SET current_club = 'Free Agent' WHERE current_club = (SELECT club_name FROM clubs WHERE user_id = ?)", (uid,))
            conn.execute("DELETE FROM transfer_offers WHERE club_id IN (SELECT id FROM clubs WHERE user_id = ?)", (uid,))
            conn.execute("DELETE FROM clubs WHERE user_id = ?", (uid,))
        elif role == 'Agent':
            conn.execute("UPDATE players SET agent_id = NULL WHERE agent_id IN (SELECT id FROM agents WHERE user_id = ?)", (uid,))
            conn.execute("DELETE FROM agents WHERE user_id = ?", (uid,))
        conn.execute("DELETE FROM users WHERE id = ?", (uid,))
        conn.commit()
        conn.close()
        log_audit("USER_DELETED", f"Admin deleted user #{uid} ({username})")
        messagebox.showinfo("ลบสำเร็จ", f"ลบบัญชี '{username}' ออกจากระบบเรียบร้อยแล้ว!")
        self._render_users_grid()

    def open_create_user_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("สร้างบัญชีผู้ใช้ใหม่")
        dialog.geometry("420x460")
        dialog.configure(fg_color=BG_DIALOG)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="สร้างบัญชีผู้ใช้ใหม่", font=FONT_SUBTITLE, text_color=TEXT_MAIN).pack(pady=(24, 12))

        ctk.CTkLabel(dialog, text="ชื่อผู้ใช้งาน", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=36, pady=(4, 2))
        u_entry = ctk.CTkEntry(dialog, fg_color=BG_CARD, border_width=0, text_color=TEXT_MAIN, height=36, corner_radius=8)
        u_entry.pack(fill="x", padx=36)

        ctk.CTkLabel(dialog, text="รหัสผ่าน", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=36, pady=(10, 2))
        p_entry = ctk.CTkEntry(dialog, fg_color=BG_CARD, border_width=0, text_color=TEXT_MAIN, show="•", height=36, corner_radius=8)
        p_entry.pack(fill="x", padx=36)

        ctk.CTkLabel(dialog, text="บทบาท", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=36, pady=(10, 2))
        role_map = {"สโมสร (Club)": "Club", "ตัวแทนนักเตะ (Agent)": "Agent", "ผู้ดูแลระบบ (Admin)": "Admin"}
        role_var = ctk.StringVar(value="สโมสร (Club)")
        ctk.CTkOptionMenu(dialog, variable=role_var, values=list(role_map.keys()), fg_color=BG_CARD, button_color=COLOR_APPLE_BLUE, text_color=TEXT_MAIN).pack(fill="x", padx=36)

        ctk.CTkLabel(dialog, text="ชื่อสโมสร / ชื่อเอเยนซี่", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=36, pady=(10, 2))
        extra_entry = ctk.CTkEntry(dialog, fg_color=BG_CARD, border_width=0, text_color=TEXT_MAIN, placeholder_text="เช่น Juventus F.C.", height=36, corner_radius=8)
        extra_entry.pack(fill="x", padx=36)

        def save():
            uname = u_entry.get().strip()
            pwd = p_entry.get().strip()
            role = role_map.get(role_var.get(), "Club")
            extra = extra_entry.get().strip()

            if not uname or not pwd:
                messagebox.showwarning("ข้อมูลไม่ครบถ้วน", "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน", parent=dialog)
                return

            conn = get_connection()
            hashed = hash_password(pwd)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (uname, hashed, role))
            new_uid = cursor.lastrowid

            if role == "Club":
                cname = extra if extra else f"{uname.capitalize()} F.C."
                cursor.execute("INSERT INTO clubs (user_id, club_name, budget) VALUES (?, ?, 200000000)", (new_uid, cname))
            elif role == "Agent":
                agency = extra if extra else f"{uname.capitalize()} Agency"
                cursor.execute("INSERT INTO agents (user_id, first_name, last_name, agency_name) VALUES (?, ?, '', ?)", (new_uid, uname.capitalize(), agency))

            conn.commit()
            conn.close()
            log_audit("USER_CREATED", f"Admin created user {uname} ({role})")
            messagebox.showinfo("สำเร็จ", f"สร้างผู้ใช้ {uname} สำเร็จแล้ว!", parent=dialog)
            dialog.destroy()
            self._render_users_grid()

        ctk.CTkButton(dialog, text="สร้างบัญชีผู้ใช้", font=FONT_BODY_BOLD, fg_color=COLOR_APPLE_BLUE, hover_color=COLOR_APPLE_BLUE_HOVER, height=40, corner_radius=20, command=save).pack(fill="x", padx=36, pady=24)

    # ==================== 3. PLAYER OVERSIGHT (APPLE CARD GRID) ====================
    def show_players_oversight(self):
        self._highlight_nav("players")
        self.clear_content()

        scroll = ctk.CTkScrollableFrame(self.main_content, fg_color=BG_APP)
        scroll.pack(fill="both", expand=True)

        create_stadium_banner(scroll, "จัดการและตรวจสอบนักเตะ", "ตรวจสอบและจัดการนักเตะในระบบ กำหนดสังกัดสโมสร และจัดการรูปภาพ")

        # Search Bar & Club Filter & Add Player Button
        search_box = ctk.CTkFrame(scroll, fg_color="transparent")
        search_box.pack(fill="x", padx=40, pady=(0, 20))

        self.p_search = ctk.CTkEntry(
            search_box,
            placeholder_text="🔍 ค้นหานักเตะ ชื่อ, สัญชาติ, ตำแหน่ง...",
            fg_color=BG_CARD,
            border_width=0,
            text_color=TEXT_MAIN,
            height=38,
            width=280,
            corner_radius=19
        )
        self.p_search.pack(side="left")
        self._p_search_timer = None
        def _on_p_search(e):
            if self._p_search_timer:
                self.after_cancel(self._p_search_timer)
            self._p_search_timer = self.after(200, lambda: self._render_players_grid(keep_limit=False))
        self.p_search.bind("<KeyRelease>", _on_p_search)

        # Club Filter Dropdown (กรองเป็นสโมสรได้)
        conn = get_connection()
        club_rows = [r[0] for r in conn.execute("SELECT DISTINCT current_club FROM players WHERE current_club IS NOT NULL AND current_club != '' ORDER BY current_club ASC").fetchall()]
        conn.close()

        club_opts = ["สโมสรทั้งหมด (All Clubs)"] + club_rows
        self.p_club_filter_var = ctk.StringVar(value=club_opts[0])

        club_menu = ctk.CTkOptionMenu(
            search_box,
            variable=self.p_club_filter_var,
            values=club_opts,
            height=38,
            width=210,
            corner_radius=19,
            fg_color=BG_CARD,
            button_color=COLOR_APPLE_BLUE,
            button_hover_color=COLOR_APPLE_BLUE_HOVER,
            text_color=TEXT_MAIN,
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color=TEXT_MAIN,
            command=lambda v: self._render_players_grid(keep_limit=False)
        )
        club_menu.pack(side="left", padx=10)

        ctk.CTkButton(
            search_box,
            text="+ เพิ่มนักเตะใหม่",
            font=FONT_SMALL_BOLD,
            fg_color=COLOR_APPLE_BLUE,
            hover_color=COLOR_APPLE_BLUE_HOVER,
            text_color="#FFFFFF",
            height=38,
            corner_radius=19,
            command=self.open_add_player_dialog
        ).pack(side="right")

        self.players_grid = ctk.CTkFrame(scroll, fg_color=BG_APP)
        self.players_grid.pack(fill="x", padx=40, pady=(0, 40))
        self.players_grid.grid_columnconfigure((0, 1, 2), weight=1)

        self._render_players_grid()

    def _render_players_grid(self, keep_limit=False):
        if not keep_limit:
            self._p_limit = 24
        limit = getattr(self, '_p_limit', 24)

        for widget in self.players_grid.winfo_children():
            widget.destroy()

        q = self.p_search.get().strip().lower() if hasattr(self, 'p_search') else ""
        sel_club = self.p_club_filter_var.get() if hasattr(self, 'p_club_filter_var') else "สโมสรทั้งหมด (All Clubs)"

        conn = get_connection()
        sql = "SELECT id, known_as, main_position, nationality, overall_rating, estimated_value, current_club, status, image_path FROM players WHERE 1=1"
        params = []
        if q:
            sql += " AND (LOWER(known_as) LIKE ? OR LOWER(nationality) LIKE ? OR LOWER(main_position) LIKE ?)"
            params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
        if sel_club and sel_club != "สโมสรทั้งหมด (All Clubs)":
            sql += " AND current_club = ?"
            params.append(sel_club)

        sql += " ORDER BY id DESC"
        players = conn.execute(sql, tuple(params)).fetchall()
        conn.close()

        if not players:
            empty_box = ctk.CTkFrame(self.players_grid, fg_color=BG_CARD, corner_radius=18, border_width=1, border_color=BORDER_SUBTLE)
            empty_box.grid(row=0, column=0, columnspan=3, pady=40, padx=20, sticky="ew")
            ctk.CTkLabel(empty_box, text="⚽ ไม่พบข้อมูลนักเตะตามเงื่อนไขการค้นหา", font=FONT_BODY_BOLD, text_color=TEXT_MUTED).pack(pady=30)
            return

        total_count = len(players)
        visible_players = players[:limit]

        for idx, p in enumerate(visible_players):
            card = ctk.CTkFrame(self.players_grid, fg_color=BG_CARD, corner_radius=22, border_width=1, border_color=BORDER_SUBTLE, height=435)
            card.grid(row=idx // 3, column=idx % 3, padx=12, pady=12, sticky="nsew")
            card.pack_propagate(False)

            p_img = p['image_path'] if 'image_path' in p.keys() else None
            photo = get_player_image(p['id'], size=(130, 130), image_path=p_img)
            lbl = ctk.CTkLabel(card, text="⚽" if not photo else "", image=photo, font=("Arial", 48))
            lbl.image = photo
            lbl.pack(pady=(16, 6))

            name_lbl = ctk.CTkLabel(card, text=p['known_as'], font=(FONT_FAMILY, 18, "bold"), text_color=TEXT_MAIN)
            name_lbl.pack(pady=(0, 2))

            # Position & Club Row
            pos_row = ctk.CTkFrame(card, fg_color="transparent")
            pos_row.pack(pady=(0, 4))

            pos = p['main_position']
            pos_styles = {
                "ST": ("#FFF0F0", "#FF3B30"), "CF": ("#FFF0F0", "#FF3B30"), "LW": ("#FFF0F0", "#FF3B30"), "RW": ("#FFF0F0", "#FF3B30"),
                "CAM": ("#EBF4FF", "#0071E3"), "CM": ("#EBF4FF", "#0071E3"), "CDM": ("#EBF4FF", "#0071E3"), "LM": ("#EBF4FF", "#0071E3"), "RM": ("#EBF4FF", "#0071E3"),
                "CB": ("#E8F8EE", "#34C759"), "LB": ("#E8F8EE", "#34C759"), "RB": ("#E8F8EE", "#34C759"), "LWB": ("#E8F8EE", "#34C759"), "RWB": ("#E8F8EE", "#34C759"),
                "GK": ("#F3EBFF", "#8E44AD")
            }
            bg_col, txt_col = pos_styles.get(pos, ("#F5F5F7", "#86868B"))
            pos_badge = ctk.CTkFrame(pos_row, fg_color=bg_col, corner_radius=8)
            pos_badge.pack(side="left", padx=4)
            ctk.CTkLabel(pos_badge, text=f" {pos} ", font=FONT_SMALL_BOLD, text_color=txt_col).pack(padx=4, pady=1)

            club_name = p['current_club'] or 'Free Agent'
            club_lbl = ctk.CTkLabel(pos_row, text=f"•  {club_name}", font=FONT_SMALL, text_color=TEXT_MUTED)
            club_lbl.pack(side="left", padx=4)

            # Rating Bar & Tier
            ovr = p['overall_rating'] or 75
            if ovr >= 90:
                tier_text, tier_col = "🌟 World Class", "#FF9500"
            elif ovr >= 85:
                tier_text, tier_col = "⭐ Elite Star", "#0071E3"
            elif ovr >= 80:
                tier_text, tier_col = "🔥 First Team", "#34C759"
            else:
                tier_text, tier_col = "⚡ Talent", "#86868B"

            rating_box = ctk.CTkFrame(card, fg_color="transparent")
            rating_box.pack(fill="x", padx=36, pady=(0, 4))

            r_top = ctk.CTkFrame(rating_box, fg_color="transparent")
            r_top.pack(fill="x")
            ovr_lbl = ctk.CTkLabel(r_top, text=f"OVR {ovr}", font=FONT_SMALL_BOLD, text_color=TEXT_MAIN)
            ovr_lbl.pack(side="left")
            ctk.CTkLabel(r_top, text=tier_text, font=FONT_SMALL_BOLD, text_color=tier_col).pack(side="right")

            prog = ctk.CTkProgressBar(rating_box, height=5, corner_radius=3, fg_color="#E5E5EA", progress_color=tier_col)
            prog.set(min(1.0, ovr / 100.0))
            prog.pack(fill="x", pady=(3, 0))

            # Value & Status
            val_row = ctk.CTkFrame(card, fg_color="transparent")
            val_row.pack(fill="x", padx=36, pady=(4, 8))
            val_lbl = ctk.CTkLabel(val_row, text=format_currency(p['estimated_value']), font=(FONT_FAMILY, 14, "bold"), text_color=TEXT_MAIN)
            val_lbl.pack(side="left")
            create_badge(val_row, p['status']).pack(side="right")

            # Actions Row
            btn_box = ctk.CTkFrame(card, fg_color="transparent")
            btn_box.pack(fill="x", padx=16, pady=(0, 14), side="bottom")

            ctk.CTkButton(
                btn_box,
                text="🎬 วิดีโอ",
                font=FONT_SMALL_BOLD,
                fg_color="#1B9AE5",
                hover_color="#1583C7",
                text_color="#FFFFFF",
                corner_radius=14,
                height=30,
                width=64,
                command=lambda pid=p['id']: open_player_video_modal(self, pid, can_upload=True, can_download=True)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                btn_box,
                text="✏️ แก้ไข",
                font=FONT_SMALL_BOLD,
                fg_color=BG_CARD_HOVER,
                hover_color=BORDER_SUBTLE,
                text_color=COLOR_APPLE_BLUE,
                corner_radius=14,
                height=30,
                width=60,
                command=lambda pid=p['id']: self.open_edit_player_dialog(pid)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                btn_box,
                text="อนุมัติ",
                font=FONT_SMALL_BOLD,
                fg_color=COLOR_GREEN,
                hover_color="#2EB34F",
                text_color="#FFFFFF",
                corner_radius=14,
                height=30,
                command=lambda pid=p['id']: self.update_player_status(pid, "Approved")
            ).pack(side="left", expand=True, padx=2)

            ctk.CTkButton(
                btn_box,
                text="ปฏิเสธ",
                font=FONT_SMALL_BOLD,
                fg_color=BG_CARD_HOVER,
                hover_color=BORDER_SUBTLE,
                text_color=COLOR_RED,
                corner_radius=14,
                height=30,
                command=lambda pid=p['id']: self.update_player_status(pid, "Rejected")
            ).pack(side="left", expand=True, padx=2)

            ctk.CTkButton(
                btn_box,
                text="🗑️",
                font=FONT_SMALL_BOLD,
                fg_color=BG_CARD_HOVER,
                hover_color="#FEE2E2",
                text_color=COLOR_RED,
                corner_radius=14,
                height=30,
                width=34,
                command=lambda pid=p['id'], pn=p['known_as']: self.delete_player(pid, pn)
            ).pack(side="left", padx=2)

            bind_black_card_hover(
                card,
                text_labels=[(name_lbl, TEXT_MAIN, "#FFFFFF"), (club_lbl, TEXT_MUTED, "#CBD5E1"), (ovr_lbl, TEXT_MAIN, "#38BDF8"), (val_lbl, TEXT_MAIN, "#FFFFFF")],
                on_click=lambda pid=p['id']: open_player_video_modal(self, pid, can_upload=True, can_download=True)
            )

        if total_count > limit:
            remaining = total_count - limit
            next_batch = min(24, remaining)
            more_row = (len(visible_players) // 3) + 1
            more_box = ctk.CTkFrame(self.players_grid, fg_color="transparent")
            more_box.grid(row=more_row, column=0, columnspan=3, pady=(20, 10))

            def load_more():
                self._p_limit += 24
                self._render_players_grid(keep_limit=True)

            def load_all():
                self._p_limit = total_count
                self._render_players_grid(keep_limit=True)

            ctk.CTkButton(
                more_box,
                text=f"⬇️ แสดงนักเตะเพิ่มเติม (+{next_batch} คน | เหลือ {remaining} คน)",
                font=FONT_BODY_BOLD,
                fg_color=COLOR_APPLE_BLUE,
                hover_color=COLOR_APPLE_BLUE_HOVER,
                text_color="#FFFFFF",
                height=40,
                corner_radius=20,
                command=load_more
            ).pack(side="left", padx=8)

            ctk.CTkButton(
                more_box,
                text=f"แสดงทั้งหมด ({total_count} คน)",
                font=FONT_SMALL_BOLD,
                fg_color=BG_CARD_HOVER,
                hover_color=BORDER_SUBTLE,
                text_color=TEXT_MAIN,
                height=40,
                corner_radius=20,
                command=load_all
            ).pack(side="left", padx=4)

    def open_add_player_dialog(self):
        """หน้าต่างเพิ่มนักเตะใหม่เข้าสู่ระบบโดยแอดมิน พร้อมอัปโหลดรูปภาพ"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("เพิ่มนักเตะใหม่")
        dialog.geometry("540x740")
        dialog.configure(fg_color=BG_DIALOG)
        dialog.grab_set()

        scroll = ctk.CTkScrollableFrame(dialog, fg_color=BG_DIALOG)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(scroll, text="⚽", font=("Arial", 36)).pack(pady=(6, 2))
        ctk.CTkLabel(scroll, text="เพิ่มนักเตะใหม่เข้าสู่ระบบ", font=FONT_TITLE, text_color=TEXT_MAIN).pack(pady=(0, 2))
        ctk.CTkLabel(scroll, text="กรอกข้อมูลนักเตะและเลือกรูปภาพเพื่อเพิ่มเข้าสู่ระบบและตลาดซื้อขาย", font=FONT_SMALL, text_color=TEXT_MUTED).pack(pady=(0, 16))

        form = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=18, border_width=1, border_color=BORDER_SUBTLE)
        form.pack(fill="x", padx=10, pady=(0, 16))

        # Photo Picker Container
        photo_box = ctk.CTkFrame(form, fg_color="#F8FAFC", corner_radius=14, border_width=1, border_color=BORDER_SUBTLE)
        photo_box.pack(fill="x", padx=20, pady=(16, 10))

        photo_path_var = ctk.StringVar(value="")

        preview_lbl = ctk.CTkLabel(photo_box, text="⚽", font=("Arial", 36), width=90, height=90, fg_color="#E2E8F0", corner_radius=12)
        preview_lbl.pack(side="left", padx=14, pady=12)

        picker_info = ctk.CTkFrame(photo_box, fg_color="transparent")
        picker_info.pack(side="left", fill="both", expand=True, padx=(0, 14), pady=12)

        ctk.CTkLabel(picker_info, text="รูปภาพประจำตัวนักเตะ", font=FONT_BODY_BOLD, text_color=TEXT_MAIN).pack(anchor="w")
        photo_status_lbl = ctk.CTkLabel(picker_info, text="ยังไม่ได้เลือกรูป (ใช้ภาพเริ่มต้น)", font=FONT_SMALL, text_color=TEXT_MUTED)
        photo_status_lbl.pack(anchor="w", pady=(2, 6))

        def choose_photo():
            fpath = filedialog.askopenfilename(
                parent=dialog,
                title="เลือกรูปภาพนักเตะ",
                filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.webp")]
            )
            if fpath:
                photo_path_var.set(fpath)
                photo_status_lbl.configure(text=f"✔️ {os.path.basename(fpath)}", text_color=COLOR_GREEN)
                try:
                    raw = Image.open(fpath)
                    p_img = ctk.CTkImage(light_image=raw, dark_image=raw, size=(90, 90))
                    preview_lbl.configure(image=p_img, text="")
                    preview_lbl.image = p_img
                except Exception as ex:
                    print(f"Error previewing image: {ex}")

        ctk.CTkButton(
            picker_info,
            text="📷 เลือกไฟล์รูปภาพจากเครื่อง...",
            font=FONT_SMALL_BOLD,
            fg_color=COLOR_APPLE_BLUE,
            hover_color=COLOR_APPLE_BLUE_HOVER,
            text_color="#FFFFFF",
            height=30,
            corner_radius=15,
            command=choose_photo
        ).pack(anchor="w")

        fields = {}
        def add_field(label, key, default=""):
            ctk.CTkLabel(form, text=label, font=FONT_SMALL_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(10, 2))
            ent = ctk.CTkEntry(form, fg_color=BG_INPUT, border_color=BORDER_SUBTLE, text_color=TEXT_MAIN, height=36, corner_radius=8)
            ent.insert(0, str(default))
            ent.pack(fill="x", padx=20)
            fields[key] = ent

        add_field("ชื่อนักเตะ", "known_as")
        add_field("สัญชาติ", "nationality", "Spain")

        ctk.CTkLabel(form, text="ตำแหน่งการเล่น", font=FONT_SMALL_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(10, 2))
        pos_var = ctk.StringVar(value="ST")
        ctk.CTkOptionMenu(form, variable=pos_var, values=["ST", "CF", "LW", "RW", "CAM", "CM", "CDM", "LM", "RM", "CB", "LB", "RB", "GK"], fg_color=BG_INPUT, text_color=TEXT_MAIN, button_color=COLOR_APPLE_BLUE).pack(fill="x", padx=20)

        add_field("พลังภาพรวม (OVR: 50-99)", "overall_rating", "82")
        add_field("ราคาประเมินตลาด (€ ยูโร)", "estimated_value", "45000000")

        conn = get_connection()
        clubs = [r[0] for r in conn.execute("SELECT club_name FROM clubs ORDER BY club_name ASC").fetchall()]
        agents = conn.execute("SELECT id, first_name || ' ' || last_name as name, agency_name FROM agents ORDER BY id ASC").fetchall()
        conn.close()

        club_choices = ["Free Agent"] + clubs
        ctk.CTkLabel(form, text="สังกัดสโมสรปัจจุบัน", font=FONT_SMALL_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(10, 2))
        club_var = ctk.StringVar(value=club_choices[0])
        ctk.CTkOptionMenu(form, variable=club_var, values=club_choices, fg_color=BG_INPUT, text_color=TEXT_MAIN, button_color=COLOR_APPLE_BLUE).pack(fill="x", padx=20)

        agent_map = {"ไม่มีเอเยนต์": None}
        for a in agents:
            agent_map[f"{a['name']} ({a['agency_name']})"] = a['id']
        ctk.CTkLabel(form, text="เอเยนต์ผู้ดูแล", font=FONT_SMALL_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(10, 2))
        agent_var = ctk.StringVar(value=list(agent_map.keys())[0] if agent_map else "ไม่มีเอเยนต์")
        ctk.CTkOptionMenu(form, variable=agent_var, values=list(agent_map.keys()), fg_color=BG_INPUT, text_color=TEXT_MAIN, button_color=COLOR_APPLE_BLUE).pack(fill="x", padx=20, pady=(0, 16))

        def save():
            name = fields["known_as"].get().strip()
            nat = fields["nationality"].get().strip()
            pos = pos_var.get()
            try: ovr = int(fields["overall_rating"].get().strip())
            except: ovr = 75
            try: val = float(fields["estimated_value"].get().strip())
            except: val = 10000000
            club = club_var.get()
            ag_id = agent_map.get(agent_var.get())

            if not name:
                messagebox.showwarning("ข้อมูลไม่ครบถ้วน", "กรุณากรอกชื่อนักเตะ", parent=dialog)
                return

            try:
                c = get_connection()
                c.execute("""
                    INSERT INTO players (agent_id, first_name, known_as, nationality, main_position, overall_rating, potential, estimated_value, asking_price, current_club, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Approved')
                """, (ag_id, name, name, nat, pos, ovr, min(99, ovr+5), val, val, club))
                new_id = c.lastrowid

                # บันทึกรูปภาพถ้ามีการเลือก
                chosen_photo = photo_path_var.get()
                if chosen_photo and os.path.exists(chosen_photo):
                    os.makedirs("assets/players", exist_ok=True)
                    dest_path = f"assets/players/player_{new_id}.png"
                    try:
                        raw = Image.open(chosen_photo)
                        raw.save(dest_path, "PNG")
                        c.execute("UPDATE players SET image_path = ? WHERE id = ?", (dest_path, new_id))
                    except Exception:
                        shutil.copy(chosen_photo, dest_path)
                        c.execute("UPDATE players SET image_path = ? WHERE id = ?", (dest_path, new_id))

                c.commit()
                c.close()
                clear_player_image_cache(new_id)

                log_audit("PLAYER_ADDED_BY_ADMIN", f"Admin created player '{name}' (ID #{new_id}, OVR {ovr}) for {club}")
                messagebox.showinfo("สำเร็จ", f"เพิ่มนักเตะ '{name}' สำเร็จแล้ว!", parent=dialog)
                dialog.destroy()
                self._render_players_grid()
            except Exception as e:
                messagebox.showerror("เกิดข้อผิดพลาด", f"เกิดข้อผิดพลาดในการบันทึกนักเตะ: {e}", parent=dialog)

        ctk.CTkButton(scroll, text="บันทึกข้อมูลนักเตะ", font=FONT_BODY_BOLD, fg_color=COLOR_APPLE_BLUE, hover_color=COLOR_APPLE_BLUE_HOVER, height=42, corner_radius=21, command=save).pack(fill="x", padx=10, pady=10)

    def open_edit_player_dialog(self, player_id):
        """หน้าต่างแก้ไขข้อมูลนักเตะโดยแอดมิน พร้อมเปลี่ยนรูปภาพและอัปเดตข้อมูล"""
        conn = get_connection()
        p = conn.execute("SELECT * FROM players WHERE id = ?", (player_id,)).fetchone()
        clubs = [r[0] for r in conn.execute("SELECT club_name FROM clubs ORDER BY club_name ASC").fetchall()]
        agents = conn.execute("SELECT id, first_name || ' ' || last_name as name, agency_name FROM agents ORDER BY id ASC").fetchall()
        conn.close()

        if not p:
            messagebox.showerror("ผิดพลาด", f"ไม่พบข้อมูลนักเตะ ID #{player_id}")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"แก้ไขนักเตะ: {p['known_as']}")
        dialog.geometry("540x740")
        dialog.configure(fg_color=BG_DIALOG)
        dialog.grab_set()

        scroll = ctk.CTkScrollableFrame(dialog, fg_color=BG_DIALOG)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(scroll, text="✏️", font=("Arial", 36)).pack(pady=(6, 2))
        ctk.CTkLabel(scroll, text=f"แก้ไขข้อมูลนักเตะ: {p['known_as']}", font=FONT_TITLE, text_color=TEXT_MAIN).pack(pady=(0, 2))
        ctk.CTkLabel(scroll, text=f"รหัสนักเตะ #{player_id} • แก้ไขข้อมูล รูปภาพ และสังกัดของนักเตะ", font=FONT_SMALL, text_color=TEXT_MUTED).pack(pady=(0, 16))

        form = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=18, border_width=1, border_color=BORDER_SUBTLE)
        form.pack(fill="x", padx=10, pady=(0, 16))

        # Photo Picker Container (แสดงรูปปัจจุบัน และให้เปลี่ยนรูปได้)
        photo_box = ctk.CTkFrame(form, fg_color="#F8FAFC", corner_radius=14, border_width=1, border_color=BORDER_SUBTLE)
        photo_box.pack(fill="x", padx=20, pady=(16, 10))

        new_photo_path_var = ctk.StringVar(value="")

        cur_photo = get_player_image(player_id, size=(90, 90))
        preview_lbl = ctk.CTkLabel(photo_box, text="⚽" if not cur_photo else "", image=cur_photo, width=90, height=90, fg_color="#E2E8F0", corner_radius=12)
        preview_lbl.image = cur_photo
        preview_lbl.pack(side="left", padx=14, pady=12)

        picker_info = ctk.CTkFrame(photo_box, fg_color="transparent")
        picker_info.pack(side="left", fill="both", expand=True, padx=(0, 14), pady=12)

        ctk.CTkLabel(picker_info, text="รูปภาพประจำตัวนักเตะ", font=FONT_BODY_BOLD, text_color=TEXT_MAIN).pack(anchor="w")
        photo_status_lbl = ctk.CTkLabel(picker_info, text="รูปปัจจุบันในระบบ (คลิกปุ่มเพื่อเปลี่ยน)", font=FONT_SMALL, text_color=TEXT_MUTED)
        photo_status_lbl.pack(anchor="w", pady=(2, 6))

        def change_photo():
            fpath = filedialog.askopenfilename(
                parent=dialog,
                title="เลือกรูปภาพใหม่ของนักเตะ",
                filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.webp")]
            )
            if fpath:
                new_photo_path_var.set(fpath)
                photo_status_lbl.configure(text=f"✔️ รูปใหม่: {os.path.basename(fpath)}", text_color=COLOR_GREEN)
                try:
                    raw = Image.open(fpath)
                    p_img = ctk.CTkImage(light_image=raw, dark_image=raw, size=(90, 90))
                    preview_lbl.configure(image=p_img, text="")
                    preview_lbl.image = p_img
                except Exception as ex:
                    print(f"Error previewing image: {ex}")

        ctk.CTkButton(
            picker_info,
            text="📷 เปลี่ยนรูปภาพนักเตะ...",
            font=FONT_SMALL_BOLD,
            fg_color=COLOR_APPLE_BLUE,
            hover_color=COLOR_APPLE_BLUE_HOVER,
            text_color="#FFFFFF",
            height=30,
            corner_radius=15,
            command=change_photo
        ).pack(anchor="w")

        fields = {}
        def add_field(label, key, val):
            ctk.CTkLabel(form, text=label, font=FONT_SMALL_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(10, 2))
            ent = ctk.CTkEntry(form, fg_color=BG_INPUT, border_color=BORDER_SUBTLE, text_color=TEXT_MAIN, height=36, corner_radius=8)
            ent.insert(0, str(val if val is not None else ""))
            ent.pack(fill="x", padx=20)
            fields[key] = ent

        add_field("ชื่อนักเตะ", "known_as", p['known_as'])
        add_field("สัญชาติ", "nationality", p['nationality'])

        ctk.CTkLabel(form, text="ตำแหน่งการเล่น", font=FONT_SMALL_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(10, 2))
        pos_var = ctk.StringVar(value=p['main_position'] or "ST")
        ctk.CTkOptionMenu(form, variable=pos_var, values=["ST", "CF", "LW", "RW", "CAM", "CM", "CDM", "LM", "RM", "CB", "LB", "RB", "GK"], fg_color=BG_INPUT, text_color=TEXT_MAIN, button_color=COLOR_APPLE_BLUE).pack(fill="x", padx=20)

        add_field("พลังภาพรวม (OVR: 50-99)", "overall_rating", p['overall_rating'])
        add_field("ราคาประเมินตลาด (€ ยูโร)", "estimated_value", p['estimated_value'])

        club_choices = ["Free Agent"] + clubs
        cur_club = p['current_club'] if p['current_club'] in club_choices else "Free Agent"
        ctk.CTkLabel(form, text="สังกัดสโมสรปัจจุบัน", font=FONT_SMALL_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(10, 2))
        club_var = ctk.StringVar(value=cur_club)
        ctk.CTkOptionMenu(form, variable=club_var, values=club_choices, fg_color=BG_INPUT, text_color=TEXT_MAIN, button_color=COLOR_APPLE_BLUE).pack(fill="x", padx=20)

        agent_map = {"ไม่มีเอเยนต์": None}
        init_agent_label = "ไม่มีเอเยนต์"
        for a in agents:
            lbl_a = f"{a['name']} ({a['agency_name']})"
            agent_map[lbl_a] = a['id']
            if a['id'] == p['agent_id']:
                init_agent_label = lbl_a

        ctk.CTkLabel(form, text="เอเยนต์ผู้ดูแล", font=FONT_SMALL_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(10, 2))
        agent_var = ctk.StringVar(value=init_agent_label)
        ctk.CTkOptionMenu(form, variable=agent_var, values=list(agent_map.keys()), fg_color=BG_INPUT, text_color=TEXT_MAIN, button_color=COLOR_APPLE_BLUE).pack(fill="x", padx=20)

        ctk.CTkLabel(form, text="สถานะนักเตะในตลาด", font=FONT_SMALL_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(10, 2))
        player_st_map = {
            "อนุมัติแล้ว (Approved)": "Approved",
            "รอการตรวจสอบ (Pending)": "Pending",
            "ปฏิเสธ (Rejected)": "Rejected"
        }
        rev_player_st_map = {v: k for k, v in player_st_map.items()}
        cur_p_st = p['status'] or "Approved"
        st_var = ctk.StringVar(value=rev_player_st_map.get(cur_p_st, "อนุมัติแล้ว (Approved)"))
        ctk.CTkOptionMenu(form, variable=st_var, values=list(player_st_map.keys()), fg_color=BG_INPUT, text_color=TEXT_MAIN, button_color=COLOR_APPLE_BLUE).pack(fill="x", padx=20, pady=(0, 16))

        def update():
            name = fields["known_as"].get().strip()
            nat = fields["nationality"].get().strip()
            pos = pos_var.get()
            try: ovr = int(fields["overall_rating"].get().strip())
            except: ovr = p['overall_rating']
            try: val = float(fields["estimated_value"].get().strip())
            except: val = p['estimated_value']
            club = club_var.get()
            ag_id = agent_map.get(agent_var.get())
            status = player_st_map.get(st_var.get(), "Approved")

            if not name:
                messagebox.showwarning("ข้อมูลไม่ครบถ้วน", "กรุณากรอกชื่อนักเตะ", parent=dialog)
                return

            try:
                c = get_connection()
                # ตรวจสอบและอัปเดตรูปภาพใหม่ถ้ามีการเลือก
                new_photo = new_photo_path_var.get()
                img_path_to_save = p['image_path']
                if new_photo and os.path.exists(new_photo):
                    os.makedirs("assets/players", exist_ok=True)
                    dest_path = f"assets/players/player_{player_id}.png"
                    try:
                        raw = Image.open(new_photo)
                        raw.save(dest_path, "PNG")
                        img_path_to_save = dest_path
                    except Exception:
                        shutil.copy(new_photo, dest_path)
                        img_path_to_save = dest_path

                c.execute("""
                    UPDATE players 
                    SET first_name = ?, known_as = ?, nationality = ?, main_position = ?, overall_rating = ?, estimated_value = ?, asking_price = ?, current_club = ?, agent_id = ?, status = ?, image_path = ?
                    WHERE id = ?
                """, (name, name, nat, pos, ovr, val, val, club, ag_id, status, img_path_to_save, player_id))
                c.commit()
                c.close()
                clear_player_image_cache(player_id)

                log_audit("PLAYER_UPDATED", f"Admin updated player #{player_id} ({name})")
                messagebox.showinfo("สำเร็จ", f"อัปเดตข้อมูลนักเตะ '{name}' สำเร็จแล้ว!", parent=dialog)
                dialog.destroy()
                self._render_players_grid()
            except Exception as e:
                messagebox.showerror("เกิดข้อผิดพลาด", f"เกิดข้อผิดพลาดในการบันทึกการแก้ไข: {e}", parent=dialog)

        ctk.CTkButton(scroll, text="บันทึกการแก้ไข", font=FONT_BODY_BOLD, fg_color=COLOR_APPLE_BLUE, hover_color=COLOR_APPLE_BLUE_HOVER, height=42, corner_radius=21, command=update).pack(fill="x", padx=10, pady=10)

    def delete_player(self, player_id, player_name):
        confirm = messagebox.askyesno(
            "ยืนยันการลบนักเตะ",
            f"คุณต้องการลบข้อมูลนักเตะ '{player_name}' ออกจากระบบหรือไม่?",
            icon="warning"
        )
        if not confirm:
            return

        conn = get_connection()
        conn.execute("DELETE FROM transfer_offers WHERE player_id = ?", (player_id,))
        conn.execute("DELETE FROM players WHERE id = ?", (player_id,))
        conn.commit()
        conn.close()
        clear_player_image_cache(player_id)

        log_audit("PLAYER_DELETED", f"Admin deleted player '{player_name}' (ID #{player_id})")
        messagebox.showinfo("Deleted", f"ลบนักเตะ '{player_name}' ออกจากระบบเรียบร้อยแล้ว!")
        self._render_players_grid()

    def update_player_status(self, player_id, status):
        conn = get_connection()
        conn.execute("UPDATE players SET status = ? WHERE id = ?", (status, player_id))
        conn.commit()
        conn.close()
        log_audit("PLAYER_STATUS_UPDATED", f"Player #{player_id} marked as {status}")
        self._render_players_grid()

    # ==================== 4. TRANSFER AUDIT ====================
    def show_transfer_audit(self):
        self._highlight_nav("transfers")
        self.clear_content()

        scroll = ctk.CTkScrollableFrame(self.main_content, fg_color=BG_APP)
        scroll.pack(fill="both", expand=True)

        create_stadium_banner(scroll, "ตรวจสอบรายการซื้อขายนักเตะ", "บันทึกและตรวจสอบสถานะการเจรจา การโอนย้าย และสัญญาทั้งหมดในระบบ")

        conn = get_connection()
        offers = conn.execute("""
            SELECT t.*, p.known_as, p.current_club as seller_club, c.club_name as buyer_club
            FROM transfer_offers t
            JOIN players p ON t.player_id = p.id
            JOIN clubs c ON t.club_id = c.id
            ORDER BY t.id DESC
        """).fetchall()
        conn.close()

        container = ctk.CTkFrame(scroll, fg_color=BG_APP)
        container.pack(fill="x", padx=40, pady=(0, 40))

        if not offers:
            ctk.CTkLabel(container, text="ยังไม่มีรายการข้อเสนอในระบบ", font=FONT_BODY, text_color=TEXT_MUTED).pack(pady=40)
            return

        for o in offers:
            card = ctk.CTkFrame(container, fg_color=BG_CARD, corner_radius=18, border_width=1, border_color=BORDER_SUBTLE)
            card.pack(fill="x", pady=8)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=22, pady=(16, 4))
            ctk.CTkLabel(top, text=f"ดีล #{o['id']}  —  {o['known_as']}", font=FONT_CARD_TITLE, text_color=TEXT_MAIN).pack(side="left")
            create_badge(top, o['status']).pack(side="right")

            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(fill="x", padx=22, pady=(0, 6))
            ctk.CTkLabel(info, text=f"ผู้ขาย: {o['seller_club'] or 'ไร้สังกัด (Free Agent)'}  ➔  ผู้ซื้อ: {o['buyer_club']}", font=FONT_BODY, text_color=TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(info, text=f"ค่าตัว: {format_currency(o['offer_amount'])}  |  ค่าเหนื่อย: {format_currency(o['wage_offer'])}/สัปดาห์", font=FONT_BODY_BOLD, text_color=TEXT_MAIN).pack(side="right")

            meaning_txt = OFFER_STATUS_MEANINGS.get(o['status'], o['status'])
            ctk.CTkLabel(card, text=f"📌 สถานะระบบ: {o['status']} — {meaning_txt}", font=FONT_SMALL_BOLD, text_color=COLOR_APPLE_BLUE).pack(anchor="w", padx=22, pady=(0, 8))

            act = ctk.CTkFrame(card, fg_color="transparent")
            act.pack(fill="x", padx=22, pady=(0, 14))

            if o['status'] in ('Pending Approval', 'Accepted', 'Contract Pending', 'Pending', 'Negotiating', 'Pending Agent'):
                ctk.CTkButton(
                    act,
                    text="✅ อนุมัติปิดดีล & เปลี่ยนสังกัดนักเตะ (Completed)",
                    font=FONT_SMALL_BOLD,
                    fg_color=COLOR_GREEN,
                    hover_color="#2EB34F",
                    text_color="#FFFFFF",
                    height=32,
                    corner_radius=16,
                    command=lambda oid=o['id']: self._admin_approve_deal(oid)
                ).pack(side="left", padx=(0, 6))

                ctk.CTkButton(
                    act,
                    text="❌ ปฏิเสธดีลผิดปกติ (Reject)",
                    font=FONT_SMALL_BOLD,
                    fg_color=BG_CARD_HOVER,
                    hover_color="#FEE2E2",
                    text_color=COLOR_RED,
                    height=32,
                    corner_radius=16,
                    command=lambda oid=o['id']: self._admin_reject_deal(oid)
                ).pack(side="left", padx=4)
            elif o['status'] == 'Completed':
                ctk.CTkLabel(act, text="🏆 ปิดการซื้อขายสำเร็จ และบันทึกใน Transfer History แล้ว", font=FONT_SMALL_BOLD, text_color=COLOR_GREEN).pack(side="left")

    def _admin_approve_deal(self, offer_id):
        ok, msg = complete_transfer_deal(offer_id, completed_by="Admin")
        if ok:
            messagebox.showinfo("อนุมัติปิดดีลสำเร็จ", f"✅ อนุมัติดีล #{offer_id} สำเร็จ!\nระบบเปลี่ยนสังกัดนักเตะ หัก/เพิ่มงบประมาณสโมสร และบันทึกประวัติการซื้อขายในธุรกรรมเดียวกันเรียบร้อยแล้ว", parent=self)
            self.show_transfer_audit()
        else:
            messagebox.showerror("ไม่สามารถอนุมัติดีลได้", msg, parent=self)

    def _admin_reject_deal(self, offer_id):
        ok, msg = negotiate_or_respond_offer(offer_id, "Admin", "reject", notes="ผู้ดูแลระบบ (Admin) ปฏิเสธรายการเนื่องจากเงื่อนไขไม่ผ่านการตรวจสอบ")
        if ok:
            self.show_transfer_audit()
        else:
            messagebox.showerror("ผิดพลาด", msg, parent=self)

    # ==================== 5. AUDIT LOGS ====================
    def show_audit_logs(self):
        self._highlight_nav("logs")
        self.clear_content()

        scroll = ctk.CTkScrollableFrame(self.main_content, fg_color=BG_APP)
        scroll.pack(fill="both", expand=True)

        create_stadium_banner(scroll, "บันทึกประวัติระบบ", "ประวัติด้านความปลอดภัยและการดำเนินงานทั้งหมดที่บันทึกตามเวลาจริง")

        conn = get_connection()
        logs = conn.execute("SELECT id, action, details, timestamp FROM audit_logs ORDER BY id DESC").fetchall()
        conn.close()

        container = ctk.CTkFrame(scroll, fg_color=BG_APP)
        container.pack(fill="x", padx=40, pady=(0, 40))

        if not logs:
            ctk.CTkLabel(container, text="ยังไม่มีบันทึกประวัติในระบบ", font=FONT_BODY, text_color=TEXT_MUTED).pack(pady=40)
            return

        for item in logs:
            row = ctk.CTkFrame(container, fg_color=BG_CARD, corner_radius=16, border_width=0)
            row.pack(fill="x", pady=6)

            top = ctk.CTkFrame(row, fg_color="transparent")
            top.pack(fill="x", padx=18, pady=(12, 4))
            create_badge(top, item['action'], "Price Negotiation").pack(side="left")
            ctk.CTkLabel(top, text=str(item['timestamp']), font=FONT_SMALL, text_color=TEXT_MUTED).pack(side="right")

            ctk.CTkLabel(row, text=item['details'], font=FONT_BODY, text_color=TEXT_MAIN, wraplength=800, justify="left").pack(anchor="w", padx=18, pady=(0, 12))

    # ==================== 6. CLUB FINANCIAL VERIFICATION AUDITS ====================
    def show_club_verifications(self):
        self._highlight_nav("verifications")
        self.clear_content()

        scroll = ctk.CTkScrollableFrame(self.main_content, fg_color=BG_APP)
        scroll.pack(fill="both", expand=True)

        create_stadium_banner(
            scroll,
            "ตรวจสอบสถานะการเงินสโมสร",
            "ตรวจสอบเอกสารรับรองทางการเงิน (Proof of Funds / Bank Guarantee) และอนุมัติวงเงินสโมสร"
        )

        conn = get_connection()
        clubs = conn.execute("""
            SELECT c.*, u.username, u.status as user_status, u.created_at as reg_date
            FROM clubs c
            JOIN users u ON c.user_id = u.id
            ORDER BY (CASE WHEN c.verification_status='Pending' THEN 0 ELSE 1 END), c.id DESC
        """).fetchall()
        conn.close()

        container = ctk.CTkFrame(scroll, fg_color=BG_APP)
        container.pack(fill="x", padx=40, pady=(0, 40))

        if not clubs:
            ctk.CTkLabel(container, text="ยังไม่มีสโมสรในระบบ", font=FONT_BODY, text_color=TEXT_MUTED).pack(pady=40)
            return

        for c in clubs:
            card = ctk.CTkFrame(container, fg_color=BG_CARD, corner_radius=18, border_width=1, border_color=BORDER_SUBTLE)
            card.pack(fill="x", pady=8)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=22, pady=(16, 6))

            ctk.CTkLabel(top, text=f"🏟️  {c['club_name']}", font=FONT_CARD_TITLE, text_color=TEXT_MAIN).pack(side="left")
            ctk.CTkLabel(top, text=f"@{c['username']}", font=FONT_SMALL, text_color=TEXT_MUTED).pack(side="left", padx=10)

            v_status = c['verification_status'] or 'Approved'
            badge_type = "Pending" if v_status == "Pending" else ("Approved" if v_status == "Approved" else "Rejected")
            create_badge(top, f"Audit: {v_status}", badge_type).pack(side="right")

            mid = ctk.CTkFrame(card, fg_color="transparent")
            mid.pack(fill="x", padx=22, pady=(0, 12))

            country_txt = c['country'] or 'International'
            bank_txt = c['bank_name'] or 'Verified Financial Bank'
            reg_date_str = str(c['reg_date']) if c['reg_date'] else 'Standard Seeded'
            email_txt = c['email'] if ('email' in c.keys() and c['email']) else f"contact@{c['club_name'].lower().replace(' ', '')}.com"
            ctk.CTkLabel(mid, text=f"ลีก: {country_txt}   •   ธนาคาร: {bank_txt}   •   ✉️ {email_txt}", font=FONT_SMALL, text_color=TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(mid, text=f"งบประมาณที่ตรวจสอบ: {format_currency(c['budget'])}", font=FONT_BODY_BOLD, text_color=COLOR_APPLE_BLUE).pack(side="right")

            act_row = ctk.CTkFrame(card, fg_color="transparent")
            act_row.pack(fill="x", padx=22, pady=(0, 16))

            doc_path = c['financial_doc']
            if doc_path:
                ctk.CTkButton(
                    act_row,
                    text="👁️ ตรวจสอบเอกสารการเงิน",
                    font=FONT_SMALL_BOLD,
                    fg_color=BG_CARD_HOVER,
                    hover_color=BORDER_SUBTLE,
                    text_color=COLOR_APPLE_BLUE,
                    height=32,
                    corner_radius=16,
                    command=lambda p=doc_path, cn=c['club_name'], b=c['budget'], st=v_status: open_document_preview_modal(self, p, cn, b, st)
                ).pack(side="left", padx=(0, 8))
            else:
                ctk.CTkLabel(act_row, text="📄 สโมสรทางการในระบบ (สิทธิ์เริ่มต้น)", font=FONT_SMALL, text_color=TEXT_DIM).pack(side="left")

            if v_status == "Pending":
                ctk.CTkButton(
                    act_row,
                    text="✅ อนุมัติสโมสร & ส่งอีเมล",
                    font=FONT_SMALL_BOLD,
                    fg_color=COLOR_GREEN,
                    hover_color="#2EB34F",
                    text_color="#FFFFFF",
                    height=32,
                    corner_radius=16,
                    command=lambda cid=c['id'], uid=c['user_id'], cn=c['club_name'], b=c['budget']: self.approve_club_financial(cid, uid, cn, b)
                ).pack(side="right", padx=4)

                ctk.CTkButton(
                    act_row,
                    text="❌ ปฏิเสธคำขอ & ส่งอีเมล",
                    font=FONT_SMALL_BOLD,
                    fg_color=BG_CARD_HOVER,
                    hover_color=BORDER_SUBTLE,
                    text_color=COLOR_RED,
                    height=32,
                    corner_radius=16,
                    command=lambda cid=c['id'], uid=c['user_id'], cn=c['club_name']: self.reject_club_financial(cid, uid, cn)
                ).pack(side="right", padx=4)
            else:
                ctk.CTkLabel(act_row, text="✔️ ผ่านการอนุมัติแล้ว & พร้อมใช้งานในตลาด", font=FONT_SMALL_BOLD, text_color=COLOR_GREEN).pack(side="left", padx=10)
                ctk.CTkButton(
                    act_row,
                    text="🗑️ ลบสโมสร",
                    font=FONT_SMALL_BOLD,
                    fg_color=BG_CARD_HOVER,
                    hover_color=BORDER_SUBTLE,
                    text_color=COLOR_RED,
                    height=32,
                    corner_radius=16,
                    command=lambda cid=c['id'], uid=c['user_id'], cn=c['club_name']: self.delete_club(cid, uid, cn)
                ).pack(side="right", padx=4)

    def approve_club_financial(self, club_id, user_id, club_name, budget):
        conn = get_connection()
        club_row = conn.execute("SELECT email FROM clubs WHERE id = ?", (club_id,)).fetchone()
        email_addr = club_row['email'] if (club_row and club_row['email']) else f"contact@{club_name.lower().replace(' ', '')}.com"

        conn.execute("UPDATE users SET status = 'Active' WHERE id = ?", (user_id,))
        conn.execute("UPDATE clubs SET verification_status = 'Approved', verified_at = CURRENT_TIMESTAMP WHERE id = ?", (club_id,))
        conn.commit()
        conn.close()

        log_audit("CLUB_FINANCIAL_APPROVED", f"Admin verified financial proof and approved club '{club_name}' (ID #{club_id}) with budget {format_currency(budget)}")
        
        # ส่งอีเมลแจ้งผลการอนุมัติสโมสร พร้อมแสดงใบแจ้งเตือนจำลอง
        send_club_verification_email(club_name, email_addr, is_approved=True, budget=budget, parent=self)
        self.show_club_verifications()

    def reject_club_financial(self, club_id, user_id, club_name):
        conn = get_connection()
        club_row = conn.execute("SELECT email FROM clubs WHERE id = ?", (club_id,)).fetchone()
        email_addr = club_row['email'] if (club_row and club_row['email']) else f"contact@{club_name.lower().replace(' ', '')}.com"

        conn.execute("UPDATE players SET current_club = 'Free Agent' WHERE current_club = ?", (club_name,))
        conn.execute("DELETE FROM transfer_offers WHERE club_id = ?", (club_id,))
        conn.execute("DELETE FROM clubs WHERE id = ?", (club_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()

        log_audit("CLUB_FINANCIAL_REJECTED", f"Admin rejected and deleted club '{club_name}' (ID #{club_id})")

        # ส่งอีเมลแจ้งผลการปฏิเสธสโมสร พร้อมแสดงใบแจ้งเตือนจำลอง
        send_club_verification_email(club_name, email_addr, is_approved=False, reason="เอกสารหลักฐานทางการเงินไม่ผ่านเกณฑ์การประเมินสภาพคล่องตามระเบียบ UEFA Financial Fair Play (FFP)", parent=self)
        self.show_club_verifications()

    def delete_club(self, club_id, user_id, club_name):
        confirm = messagebox.askyesno(
            "Confirm Delete Club",
            f"คุณต้องการลบสโมสร '{club_name}' ออกจากระบบอย่างถาวรหรือไม่?\n(นักเตะในสังกัดสโมสรนี้จะถูกปรับเป็น Free Agent)",
            icon="warning"
        )
        if not confirm:
            return

        conn = get_connection()
        conn.execute("UPDATE players SET current_club = 'Free Agent' WHERE current_club = ?", (club_name,))
        conn.execute("DELETE FROM transfer_offers WHERE club_id = ?", (club_id,))
        conn.execute("DELETE FROM clubs WHERE id = ?", (club_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()

        log_audit("CLUB_DELETED", f"Admin deleted club '{club_name}' (ID #{club_id})")
        messagebox.showinfo("Deleted", f"ลบสโมสร '{club_name}' ออกจากระบบเรียบร้อยแล้ว!")
        self.show_club_verifications()