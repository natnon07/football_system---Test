import customtkinter as ctk
from database.db_manager import (
    get_connection, log_audit, complete_transfer_deal,
    negotiate_or_respond_offer, OFFER_STATUS_MEANINGS
)
from utils.session import CurrentSession
from utils.theme import (
    BG_APP, BG_TOPBAR, BG_CARD, BG_CARD_HOVER, BG_INPUT, BG_DIALOG,
    BORDER_SUBTLE, BORDER_FOCUS, COLOR_APPLE_BLUE, COLOR_APPLE_BLUE_HOVER,
    COLOR_APPLE_DARK, COLOR_APPLE_DARK_HOVER, COLOR_APPLE_GRAY,
    COLOR_GREEN, COLOR_GOLD, COLOR_RED, TEXT_MAIN, TEXT_MUTED, TEXT_DIM,
    FONT_FAMILY, FONT_HERO, FONT_TITLE, FONT_SUBTITLE, FONT_CARD_TITLE,
    FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_SMALL_BOLD,
    format_currency, create_badge, create_stat_card, get_player_image,
    create_stadium_banner, open_quick_switch_modal,
    bind_black_card_hover, open_player_video_modal
)
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk, ImageEnhance
import os
import shutil
from utils.contract_generator import generate_player_employment_contract_pdf

class AgentFrame(ctk.CTkFrame):
    def __init__(self, master, logout_callback, switch_callback=None):
        super().__init__(master, fg_color=BG_APP)
        self.logout_callback = logout_callback
        self.switch_callback = switch_callback or getattr(master, 'switch_user', None)
        self.agent_id, self.agent_name, self.agency_name = self.get_logged_in_agent_info()
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.hero_photo = None
        self._build_top_navbar()
        self._build_content_area()
        self.show_my_players()

    def get_logged_in_agent_info(self):
        user_id = CurrentSession.get_user_id()
        conn = get_connection()
        cursor = conn.cursor()
        if user_id:
            cursor.execute("SELECT id, first_name, last_name, agency_name FROM agents WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                conn.close()
                name = f"{row['first_name']} {row['last_name']}".strip()
                return row['id'], name if name else "Agent", row['agency_name'] or "Agency"

        cursor.execute("SELECT id, first_name, last_name, agency_name FROM agents LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            name = f"{row['first_name']} {row['last_name']}".strip()
            return row['id'], name if name else "Agent", row['agency_name'] or "Agency"
        return 1, "Jorge Mendes", "Gestifute"

    # ==================== TOP NAVIGATION BAR ====================
    def _build_top_navbar(self):
        self.topbar = ctk.CTkFrame(self, height=52, fg_color=BG_TOPBAR, corner_radius=0, border_width=1, border_color=BORDER_SUBTLE)
        self.topbar.grid(row=0, column=0, sticky="ew")
        self.topbar.grid_propagate(False)

        logo_box = ctk.CTkFrame(self.topbar, fg_color="transparent")
        logo_box.pack(side="left", padx=(30, 20))
        ctk.CTkLabel(logo_box, text=f"💼  {self.agency_name}", font=(FONT_FAMILY, 15, "bold"), text_color=TEXT_MAIN).pack(side="left")

        # Right Actions & Logout (Pack right FIRST so it is NEVER squeezed or cut off)
        right_box = ctk.CTkFrame(self.topbar, fg_color="transparent")
        right_box.pack(side="right", padx=(0, 25))

        ctk.CTkLabel(
            right_box,
            text=f"เอเยนต์: {self.agent_name}",
            font=FONT_SMALL_BOLD,
            text_color=TEXT_MAIN,
            fg_color=BG_CARD,
            corner_radius=14,
            padx=12,
            pady=4
        ).pack(side="left", padx=8)

        # Switch Portal button
        ctk.CTkButton(
            right_box,
            text="⚡ สลับพอร์ทัล",
            font=FONT_SMALL_BOLD,
            fg_color=BG_CARD_HOVER,
            hover_color=BORDER_SUBTLE,
            text_color=COLOR_APPLE_BLUE,
            height=30,
            corner_radius=15,
            command=lambda: open_quick_switch_modal(self, self.switch_callback)
        ).pack(side="left", padx=6)

        def do_logout():
            from utils.session import CurrentSession
            CurrentSession.logout()
            if self.logout_callback:
                self.logout_callback()

        ctk.CTkButton(
            right_box,
            text="ออกจากระบบ",
            font=FONT_SMALL_BOLD,
            fg_color="transparent",
            hover_color=BG_CARD_HOVER,
            text_color=COLOR_RED,
            height=30,
            command=do_logout
        ).pack(side="left", padx=4)

        # Center Navigation Menu (เมนูภาษาไทยทั้งหมด)
        self.nav_buttons = {}
        center_box = ctk.CTkFrame(self.topbar, fg_color="transparent")
        center_box.pack(side="left", expand=True)

        menus = [
            ("clients", "นักเตะในสังกัด", self.show_my_players),
            ("offers", "ข้อเสนอ & เจรจาสัญญา", self.show_offers),
            ("overview", "ภาพรวมพอร์ตโฟลิโอ", self.show_agency_overview)
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
            btn.pack(side="left", padx=8)
            self.nav_buttons[key] = btn

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

    # ==================== 1. REPRESENTED PLAYERS (APPLE STORE GRID) ====================
    def show_my_players(self):
        self._highlight_nav("clients")
        self.clear_content()

        scroll = ctk.CTkScrollableFrame(self.main_content, fg_color=BG_APP)
        scroll.pack(fill="both", expand=True)

        def add_reg(p):
            ctk.CTkButton(
                p,
                text="+ เพิ่มนักเตะในสังกัด",
                font=FONT_SMALL_BOLD,
                fg_color=COLOR_APPLE_BLUE,
                hover_color=COLOR_APPLE_BLUE_HOVER,
                corner_radius=17,
                height=34,
                command=self.open_register_player_dialog
            ).pack(side="right")

        create_stadium_banner(scroll, "นักเตะในสังกัด (Clients)", "จัดการนักเตะในความดูแล ตรวจสอบมูลค่าตลาด และสถานะสัญญา", right_widget_fn=add_reg)

        # Grid Container (3 Columns like Image 2)
        grid = ctk.CTkFrame(scroll, fg_color=BG_APP)
        grid.pack(fill="x", padx=40, pady=(0, 40))
        grid.grid_columnconfigure((0, 1, 2), weight=1)

        conn = get_connection()
        players = conn.execute("SELECT * FROM players WHERE agent_id = ? ORDER BY overall_rating DESC", (self.agent_id,)).fetchall()
        conn.close()

        if not players:
            ctk.CTkLabel(grid, text="ยังไม่มีนักเตะในความดูแล", font=FONT_BODY, text_color=TEXT_MUTED).grid(row=0, column=1, pady=60)
            return

        for idx, p in enumerate(players):
            card = ctk.CTkFrame(grid, fg_color=BG_CARD, corner_radius=22, border_width=1, border_color=BORDER_SUBTLE, height=390)
            card.grid(row=idx // 3, column=idx % 3, padx=12, pady=12, sticky="nsew")
            card.pack_propagate(False)

            p_img = p['image_path'] if 'image_path' in p.keys() else None
            photo = get_player_image(p['id'], size=(130, 130), image_path=p_img)
            lbl = ctk.CTkLabel(card, text="⚽" if not photo else "", image=photo, font=("Arial", 48))
            lbl.image = photo
            lbl.pack(pady=(16, 6))

            name_lbl = ctk.CTkLabel(card, text=p['known_as'], font=(FONT_FAMILY, 18, "bold"), text_color=TEXT_MAIN)
            name_lbl.pack(pady=(0, 2))

            pos_row = ctk.CTkFrame(card, fg_color="transparent")
            pos_row.pack(pady=(0, 6))

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

            ovr = p['overall_rating'] or 75
            tier_col = "#FF9500" if ovr >= 90 else ("#0071E3" if ovr >= 85 else ("#34C759" if ovr >= 80 else "#86868B"))

            rating_box = ctk.CTkFrame(card, fg_color="transparent")
            rating_box.pack(fill="x", padx=36, pady=(0, 6))
            r_top = ctk.CTkFrame(rating_box, fg_color="transparent")
            r_top.pack(fill="x")
            ovr_lbl = ctk.CTkLabel(r_top, text=f"OVR {ovr}", font=FONT_SMALL_BOLD, text_color=TEXT_MAIN)
            ovr_lbl.pack(side="left")
            ctk.CTkLabel(r_top, text=f"มูลค่า: {format_currency(p['estimated_value'])}", font=FONT_SMALL_BOLD, text_color=tier_col).pack(side="right")

            prog = ctk.CTkProgressBar(rating_box, height=5, corner_radius=3, fg_color="#E5E5EA", progress_color=tier_col)
            prog.set(min(1.0, ovr / 100.0))
            prog.pack(fill="x", pady=(3, 0))

            avail = p['availability_status'] if 'availability_status' in p.keys() and p['availability_status'] else 'พร้อมย้ายทีม (Available)'
            av_row = ctk.CTkFrame(card, fg_color="transparent")
            av_row.pack(fill="x", padx=28, pady=(4, 2))
            create_badge(av_row, avail).pack(side="left")
            ctk.CTkButton(
                av_row,
                text="⚙️ ตั้งค่าสถานะ/ข้อมูล",
                font=FONT_SMALL_BOLD,
                fg_color=BG_CARD_HOVER,
                hover_color=BORDER_SUBTLE,
                text_color=COLOR_APPLE_BLUE,
                height=26,
                width=115,
                corner_radius=13,
                command=lambda pl=p: self.open_edit_agent_player_dialog(pl)
            ).pack(side="right")

            ctk.CTkButton(
                card,
                text="🎬 เปิดข้อมูล & อัปโหลดวิดีโอไฮไลท์",
                font=FONT_SMALL_BOLD,
                fg_color="#1B9AE5",
                hover_color="#1583C7",
                text_color="#FFFFFF",
                height=32,
                corner_radius=16,
                command=lambda pid=p['id']: open_player_video_modal(self, pid, can_upload=True, can_download=True, on_updated=self.show_my_players)
            ).pack(fill="x", padx=28, pady=(4, 10))

            bind_black_card_hover(
                card,
                text_labels=[(name_lbl, TEXT_MAIN, "#FFFFFF"), (club_lbl, TEXT_MUTED, "#CBD5E1"), (ovr_lbl, TEXT_MAIN, "#38BDF8")],
                on_click=lambda pid=p['id']: open_player_video_modal(self, pid, can_upload=True, can_download=True, on_updated=self.show_my_players)
            )

    def open_edit_agent_player_dialog(self, player):
        """
        จัดการข้อมูลนักเตะและสถานะความพร้อมย้ายทีม (Player Availability)
        กฎสำคัญข้อที่ 3: เอเยนต์จัดการได้เฉพาะนักเตะที่ตนดูแล และไม่สามารถเปลี่ยนสังกัดนักเตะให้สำเร็จได้โดยตรงโดยไม่ผ่านกระบวนการซื้อขาย
        """
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"จัดการนักเตะ & สถานะความพร้อม: {player['known_as']}")
        dialog.geometry("460x520")
        dialog.configure(fg_color=BG_DIALOG)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=f"⚙️ จัดการนักเตะ: {player['known_as']}", font=FONT_SUBTITLE, text_color=TEXT_MAIN).pack(pady=(20, 4))
        ctk.CTkLabel(
            dialog,
            text=f"🏟️ สังกัดปัจจุบัน: {player['current_club'] or 'Free Agent'}\n(ตามกฎระบบ: การเปลี่ยนสังกัดต้องผ่านกระบวนการซื้อขายและอนุมัติดีลเท่านั้น)",
            font=FONT_SMALL,
            text_color=TEXT_MUTED,
            justify="center"
        ).pack(pady=(0, 12))

        ctk.CTkLabel(dialog, text="สถานะความพร้อมย้ายทีม (Player Availability):", font=FONT_SMALL_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=36, pady=(4, 2))
        cur_av = player['availability_status'] if 'availability_status' in player.keys() and player['availability_status'] else "พร้อมย้ายทีม (Available)"
        av_var = ctk.StringVar(value=cur_av)
        ctk.CTkOptionMenu(
            dialog,
            variable=av_var,
            values=["พร้อมย้ายทีม (Available)", "กำลังเจรจา (Negotiating)", "ไม่พร้อมย้ายทีม (Not Available)"],
            fg_color=BG_CARD,
            button_color=COLOR_APPLE_BLUE,
            text_color=TEXT_MAIN,
            height=36
        ).pack(fill="x", padx=36, pady=(0, 8))

        ctk.CTkLabel(dialog, text="ตำแหน่งหลัก:", font=FONT_SMALL_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=36, pady=(4, 2))
        pos_ent = ctk.CTkEntry(dialog, fg_color=BG_CARD, text_color=TEXT_MAIN, height=34)
        pos_ent.insert(0, str(player['main_position'] or 'ST'))
        pos_ent.pack(fill="x", padx=36, pady=(0, 8))

        ctk.CTkLabel(dialog, text="มูลค่าประเมินตลาด (€):", font=FONT_SMALL_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=36, pady=(4, 2))
        val_ent = ctk.CTkEntry(dialog, fg_color=BG_CARD, text_color=TEXT_MAIN, height=34)
        val_ent.insert(0, str(int(player['estimated_value'] or 30000000)))
        val_ent.pack(fill="x", padx=36, pady=(0, 12))

        def save_av():
            try:
                nv = float(val_ent.get().strip())
            except Exception:
                nv = float(player['estimated_value'] or 30000000)
            np = pos_ent.get().strip().upper() or player['main_position']
            nav = av_var.get()
            conn = get_connection()
            conn.execute(
                "UPDATE players SET main_position = ?, estimated_value = ?, asking_price = ?, availability_status = ? WHERE id = ? AND agent_id = ?",
                (np, nv, nv, nav, player['id'], self.agent_id)
            )
            conn.commit()
            conn.close()
            log_audit("AGENT_PLAYER_AVAILABILITY_UPDATED", f"Agent {self.agent_name} updated {player['known_as']} availability to '{nav}', value={format_currency(nv)}")
            messagebox.showinfo("สำเร็จ", f"อัปเดตสถานะความพร้อมของ {player['known_as']} เป็น '{nav}' เรียบร้อยแล้ว!", parent=dialog)
            dialog.destroy()
            self.show_my_players()

        ctk.CTkButton(dialog, text="💾 บันทึกข้อมูลและสถานะความพร้อม", font=FONT_BODY_BOLD, fg_color=COLOR_APPLE_BLUE, hover_color=COLOR_APPLE_BLUE_HOVER, height=40, corner_radius=20, command=save_av).pack(fill="x", padx=36, pady=16)

    def open_register_player_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("ลงทะเบียนนักเตะในสังกัด")
        dialog.geometry("420x520")
        dialog.configure(fg_color=BG_DIALOG)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="ลงทะเบียนนักเตะในสังกัด", font=FONT_SUBTITLE, text_color=TEXT_MAIN).pack(pady=(24, 12))

        fields = [
            ("ชื่อนักเตะ", "เช่น Lamine Yamal"),
            ("สัญชาติ", "เช่น Spain"),
            ("ตำแหน่ง", "เช่น RW, ST, CM"),
            ("เรตติ้งโดยรวม (1-99)", "เช่น 84"),
            ("มูลค่าประเมิน (€)", "เช่น 120000000"),
            ("สโมสรปัจจุบัน", "เช่น Barcelona หรือ Free Agent")
        ]
        entries = {}
        for title, ph in fields:
            ctk.CTkLabel(dialog, text=title, font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=36, pady=(3, 1))
            e = ctk.CTkEntry(dialog, placeholder_text=ph, fg_color=BG_CARD, border_width=0, text_color=TEXT_MAIN, height=34, corner_radius=8)
            e.pack(fill="x", padx=36)
            entries[title] = e

        def save():
            name = entries["ชื่อนักเตะ"].get().strip()
            nat = entries["สัญชาติ"].get().strip() or "Unknown"
            pos = entries["ตำแหน่ง"].get().strip().upper() or "ST"
            club = entries["สโมสรปัจจุบัน"].get().strip() or "Free Agent"
            try: ovr = int(entries["เรตติ้งโดยรวม (1-99)"].get().strip() or 75)
            except: ovr = 75
            try: val = float(entries["มูลค่าประเมิน (€)"].get().strip() or 10000000)
            except: val = 10000000

            if not name:
                messagebox.showwarning("ข้อมูลไม่ครบถ้วน", "กรุณากรอกชื่อนักเตะ", parent=dialog)
                return

            conn = get_connection()
            conn.execute("""
                INSERT INTO players (agent_id, first_name, known_as, nationality, main_position, overall_rating, potential, estimated_value, current_club, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Approved')
            """, (self.agent_id, name, name, nat, pos, ovr, min(99, ovr+5), val, club))
            conn.commit()
            conn.close()

            log_audit("PLAYER_REGISTERED", f"Agent {self.agent_name} registered player {name}")
            messagebox.showinfo("สำเร็จ", f"ลงทะเบียน {name} เรียบร้อยแล้ว!", parent=dialog)
            dialog.destroy()
            self.show_my_players()

        ctk.CTkButton(dialog, text="ลงทะเบียนนักเตะ", font=FONT_BODY_BOLD, fg_color=COLOR_APPLE_BLUE, hover_color=COLOR_APPLE_BLUE_HOVER, height=40, corner_radius=20, command=save).pack(fill="x", padx=36, pady=22)

    # ==================== 2. CONTRACT & WAGE OFFERS ====================
    def show_offers(self):
        self._highlight_nav("offers")
        self.clear_content()

        scroll = ctk.CTkScrollableFrame(self.main_content, fg_color=BG_APP)
        scroll.pack(fill="both", expand=True)

        create_stadium_banner(scroll, "ข้อเสนอสัญญา & เจรจาค่าเหนื่อย", "พิจารณาข้อเสนอซื้อขายจากสโมสร เจรจาค่าเหนื่อย และลงนามสัญญาจ้างนักเตะ")

        conn = get_connection()
        offers = conn.execute("""
            SELECT t.*, p.known_as, p.nationality, p.dob, p.overall_rating, p.current_club as seller_club,
                   c.club_name as buyer_club, u.username as buyer_username
            FROM transfer_offers t
            JOIN players p ON t.player_id = p.id
            JOIN clubs c ON t.club_id = c.id
            JOIN users u ON c.user_id = u.id
            WHERE p.agent_id = ?
            ORDER BY t.id DESC
        """, (self.agent_id,)).fetchall()
        conn.close()

        valid_offers = offers

        container = ctk.CTkFrame(scroll, fg_color=BG_APP)
        container.pack(fill="x", padx=40, pady=(0, 40))

        if not valid_offers:
            ctk.CTkLabel(container, text="ยังไม่มีข้อเสนอสัญญาในขณะนี้", font=FONT_BODY, text_color=TEXT_MUTED).pack(pady=40)
            return

        for o in valid_offers:
            card = ctk.CTkFrame(container, fg_color=BG_CARD, corner_radius=18, border_width=1, border_color=BORDER_SUBTLE)
            card.pack(fill="x", pady=8)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=22, pady=(16, 4))
            ctk.CTkLabel(top, text=f"ข้อเสนอซื้อขาย #{o['id']}  —  {o['known_as']}", font=FONT_CARD_TITLE, text_color=TEXT_MAIN).pack(side="left")
            create_badge(top, o['status']).pack(side="right")

            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(fill="x", padx=22, pady=(0, 4))
            years_txt = f"{o['contract_years'] if 'contract_years' in o.keys() and o['contract_years'] else 4} ปี"
            ctk.CTkLabel(info, text=f"สโมสรผู้ซื้อ: {o['buyer_club']}  |  ค่าตัวที่เสนอ: {format_currency(o['offer_amount'])}  |  ค่าเหนื่อย: {format_currency(o['wage_offer'])}/สัปดาห์  |  สัญญา: {years_txt}", font=FONT_BODY, text_color=TEXT_MUTED).pack(side="left")

            meaning_txt = OFFER_STATUS_MEANINGS.get(o['status'], o['status'])
            ctk.CTkLabel(card, text=f"📌 สถานะระบบ: {o['status']} — {meaning_txt}", font=FONT_SMALL_BOLD, text_color=COLOR_APPLE_BLUE).pack(anchor="w", padx=22, pady=(0, 8))

            act = ctk.CTkFrame(card, fg_color="transparent")
            act.pack(fill="x", padx=22, pady=(0, 16))

            # Buttons to view/download Transfer Agreement PDF if present
            if o['contract_pdf'] and os.path.exists(o['contract_pdf']):
                def make_open_t(p): return lambda: os.startfile(os.path.abspath(p))
                def make_dl_t(p, kn): return lambda: self.download_contract_file(p, f"Transfer_Agreement_{kn.replace(' ', '_')}.pdf")

                ctk.CTkButton(act, text="📜 สัญญาโอนย้าย (PDF)", font=FONT_SMALL_BOLD, fg_color=BG_CARD_HOVER, hover_color=BORDER_SUBTLE, text_color=TEXT_MAIN, corner_radius=15, height=32, command=make_open_t(o['contract_pdf'])).pack(side="left", padx=3)

            emp_pdf = o.get('emp_contract_pdf') if hasattr(o, 'get') else (o['emp_contract_pdf'] if 'emp_contract_pdf' in o.keys() else None)
            if emp_pdf and os.path.exists(emp_pdf):
                def make_open_e(p): return lambda: os.startfile(os.path.abspath(p))
                ctk.CTkButton(act, text="📄 สัญญาจ้างนักเตะ (PDF)", font=FONT_SMALL_BOLD, fg_color=BG_CARD_HOVER, hover_color=BORDER_SUBTLE, text_color=TEXT_MAIN, corner_radius=15, height=32, command=make_open_e(emp_pdf)).pack(side="left", padx=3)

            ctk.CTkButton(
                act,
                text="💬 เจรจาต่อรอง / ตอบรับข้อเสนอ",
                font=FONT_SMALL_BOLD,
                fg_color="#EFF6FF",
                hover_color="#DBEAFE",
                text_color="#1D4ED8",
                corner_radius=15,
                height=32,
                command=lambda offer_row=o: self.open_agent_negotiation_modal(offer_row)
            ).pack(side="left", padx=4)

            if o['status'] in ('Pending', 'Pending Agent', 'Negotiating', 'Accepted', 'Contract Pending'):
                ctk.CTkButton(
                    act,
                    text="✍️ พิจารณาสัญญา & ยืนยันดีล 🏁",
                    font=FONT_SMALL_BOLD,
                    fg_color=COLOR_APPLE_BLUE,
                    hover_color=COLOR_APPLE_BLUE_HOVER,
                    text_color="#FFFFFF",
                    corner_radius=15,
                    height=32,
                    command=lambda oid=o['id']: self.open_agent_confirm_modal(oid)
                ).pack(side="left", padx=4)

                ctk.CTkButton(
                    act,
                    text="❌ ปฏิเสธ",
                    font=FONT_SMALL_BOLD,
                    fg_color=BG_CARD_HOVER,
                    hover_color=BORDER_SUBTLE,
                    text_color=COLOR_RED,
                    corner_radius=15,
                    height=32,
                    command=lambda oid=o['id']: self.update_deal_status(oid, 'Rejected')
                ).pack(side="left", padx=4)

            elif o['status'] == 'Pending Approval':
                ctk.CTkLabel(act, text="🛡️ ยืนยันสัญญาแล้ว รอผู้ดูแลระบบ (Admin) อนุมัติปิดดีล", font=FONT_SMALL_BOLD, text_color=COLOR_APPLE_BLUE).pack(side="left", padx=6)
            elif o['status'] == 'Completed':
                ctk.CTkLabel(act, text=f"✨ ดีลสำเร็จ! นักเตะเข้าสู่ทีม {o['buyer_club']} แล้ว", font=FONT_SMALL_BOLD, text_color=COLOR_GREEN).pack(side="left", padx=6)

    def open_agent_negotiation_modal(self, offer):
        """หน้าต่างเจรจาต่อรองค่าตัว ระยะเวลาสัญญา และค่าเหนื่อยของเอเยนต์ (Steps 04-05)"""
        oid = offer['id']
        conn = get_connection()
        rounds = conn.execute("SELECT * FROM negotiations WHERE offer_id = ? ORDER BY round_no ASC, id ASC", (oid,)).fetchall()
        conn.close()

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"เจรจาค่าตัว & สัญญา — ดีล #{oid} ({offer['known_as']})")
        dialog.geometry("620x640")
        dialog.configure(fg_color=BG_DIALOG)
        dialog.grab_set()

        scroll = ctk.CTkScrollableFrame(dialog, fg_color=BG_DIALOG)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(scroll, text=f"💼 เจรจาข้อเสนอ: {offer['known_as']} (จาก {offer['buyer_club']})", font=FONT_TITLE, text_color=TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(scroll, text=f"สถานะปัจจุบัน: {offer['status']} — {OFFER_STATUS_MEANINGS.get(offer['status'], '')}", font=FONT_SMALL_BOLD, text_color=COLOR_APPLE_BLUE).pack(anchor="w", pady=(2, 12))

        hist_box = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=16, border_width=1, border_color=BORDER_SUBTLE)
        hist_box.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(hist_box, text="📋 ประวัติการต่อรองแต่ละรอบ (Negotiations)", font=FONT_BODY_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=16, pady=(12, 6))

        for r in rounds:
            r_row = ctk.CTkFrame(hist_box, fg_color="#F8FAFC", corner_radius=10, border_width=1, border_color=BORDER_SUBTLE)
            r_row.pack(fill="x", padx=14, pady=4)
            who = "🏟️ สโมสร (Club)" if r['proposer_role'] == "Club" else ("💼 เอเยนต์ (Agent)" if r['proposer_role'] == "Agent" else "👑 Admin")
            ctk.CTkLabel(
                r_row,
                text=f"รอบที่ {r['round_no']} โดย {who} [{r['action_type']}]: ค่าตัว {format_currency(r['proposed_fee'])} | ค่าเหนื่อย {format_currency(r['proposed_wage'])}/wk | สัญญา {r['proposed_years']} ปี",
                font=FONT_SMALL_BOLD,
                text_color=TEXT_MAIN
            ).pack(anchor="w", padx=12, pady=(8, 2))
            if r['message']:
                ctk.CTkLabel(r_row, text=f"หมายเหตุ: {r['message']}", font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w", padx=12, pady=(0, 6))

        form = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=16, border_width=1, border_color=BORDER_SUBTLE)
        form.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(form, text="✍️ ตอบกลับข้อเสนอ / เสนอราคาและสัญญาใหม่ (Counter-Offer)", font=FONT_BODY_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=16, pady=(12, 8))

        ctk.CTkLabel(form, text="ค่าตัวที่ต้องการ (€):", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=16)
        f_ent = ctk.CTkEntry(form, fg_color=BG_INPUT, border_color=BORDER_SUBTLE, text_color=TEXT_MAIN, height=34)
        f_ent.insert(0, str(int(offer['offer_amount'] or 0)))
        f_ent.pack(fill="x", padx=16, pady=(2, 6))

        ctk.CTkLabel(form, text="ค่าเหนื่อยที่ต้องการ (€/สัปดาห์):", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=16)
        w_ent = ctk.CTkEntry(form, fg_color=BG_INPUT, border_color=BORDER_SUBTLE, text_color=TEXT_MAIN, height=34)
        w_ent.insert(0, str(int(offer['wage_offer'] or 0)))
        w_ent.pack(fill="x", padx=16, pady=(2, 6))

        ctk.CTkLabel(form, text="ระยะเวลาสัญญา (ปี):", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=16)
        y_ent = ctk.CTkEntry(form, fg_color=BG_INPUT, border_color=BORDER_SUBTLE, text_color=TEXT_MAIN, height=34)
        y_ent.insert(0, str(int(offer['contract_years'] if 'contract_years' in offer.keys() and offer['contract_years'] else 4)))
        y_ent.pack(fill="x", padx=16, pady=(2, 6))

        ctk.CTkLabel(form, text="เงื่อนไขเพิ่มเติมถึงสโมสร:", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=16)
        m_ent = ctk.CTkEntry(form, fg_color=BG_INPUT, border_color=BORDER_SUBTLE, text_color=TEXT_MAIN, height=34, placeholder_text="เช่น ขอเพิ่มโบนัสลงสนามและค่าฉีกสัญญา...")
        m_ent.pack(fill="x", padx=16, pady=(2, 12))

        btn_r = ctk.CTkFrame(form, fg_color="transparent")
        btn_r.pack(fill="x", padx=16, pady=(0, 14))

        def do_counter():
            try:
                nf = float(f_ent.get().strip())
                nw = float(w_ent.get().strip())
                ny = int(y_ent.get().strip() or 4)
            except Exception:
                messagebox.showwarning("ข้อมูลไม่ถูกต้อง", "กรุณาระบุตัวเลขให้ถูกต้อง", parent=dialog)
                return
            ok, msg = negotiate_or_respond_offer(oid, "Agent", "counter", nf, nw, ny, m_ent.get().strip() or f"เอเยนต์ {self.agent_name} ยื่นข้อเสนอใหม่")
            if ok:
                messagebox.showinfo("สำเร็จ", msg, parent=dialog)
                dialog.destroy()
                self.show_offers()
            else:
                messagebox.showerror("ผิดพลาด", msg, parent=dialog)

        def do_accept_step4():
            """กฎข้อที่ 5: การตอบรับข้อเสนอ (Accepted) ยังไม่ทำให้สังกัดนักเตะเปลี่ยนทันที จนกว่าจะยืนยันสัญญาและปิดดีล"""
            ok, msg = negotiate_or_respond_offer(oid, "Agent", "accept", notes=f"เอเยนต์ {self.agent_name} ยอมรับข้อเสนอเบื้องต้น (เข้าสู่ขั้นตอนร่างสัญญา)")
            if ok:
                messagebox.showinfo("ตอบรับข้อเสนอแล้ว (Accepted)", msg, parent=dialog)
                dialog.destroy()
                self.show_offers()
            else:
                messagebox.showerror("ผิดพลาด", msg, parent=dialog)

        def do_confirm_to_admin():
            ok, msg = negotiate_or_respond_offer(oid, "Agent", "confirm_contract", notes=f"เอเยนต์ {self.agent_name} ยืนยันสัญญา ส่งให้ Admin อนุมัติปิดดีล")
            if ok:
                messagebox.showinfo("ส่งให้แอดมินตรวจสอบแล้ว", msg, parent=dialog)
                dialog.destroy()
                self.show_offers()
            else:
                messagebox.showerror("ผิดพลาด", msg, parent=dialog)

        ctk.CTkButton(btn_r, text="💬 ยื่นราคาใหม่ (Negotiating)", font=FONT_SMALL_BOLD, fg_color=COLOR_APPLE_BLUE, hover_color=COLOR_APPLE_BLUE_HOVER, text_color="#FFFFFF", height=36, corner_radius=18, command=do_counter).pack(side="left", expand=True, fill="x", padx=(0, 3))
        ctk.CTkButton(btn_r, text="✅ ยอมรับข้อเสนอ (Accepted)", font=FONT_SMALL_BOLD, fg_color=COLOR_GREEN, hover_color="#2EB34F", text_color="#FFFFFF", height=36, corner_radius=18, command=do_accept_step4).pack(side="left", expand=True, fill="x", padx=3)
        ctk.CTkButton(btn_r, text="🛡️ ส่งแอดมินอนุมัติ (Pending Approval)", font=FONT_SMALL_BOLD, fg_color="#8E44AD", hover_color="#7D3C98", text_color="#FFFFFF", height=36, corner_radius=18, command=do_confirm_to_admin).pack(side="left", expand=True, fill="x", padx=(3, 0))

    def open_agent_confirm_modal(self, offer_id):
        """หน้าต่างตรวจสอบข้อเสนอและเอกสารสัญญาที่สโมสรส่งมา ก่อนเอเยนต์กดยืนยัน (คอมเฟิร์ม)"""
        conn = get_connection()
        deal = conn.execute("""
            SELECT t.*, p.known_as, p.nationality, p.dob, p.overall_rating, p.current_club as seller_club,
                   c.club_name as buyer_club, u.username as buyer_username
            FROM transfer_offers t
            JOIN players p ON t.player_id = p.id
            JOIN clubs c ON t.club_id = c.id
            JOIN users u ON c.user_id = u.id
            WHERE t.id = ?
        """, (offer_id,)).fetchone()
        conn.close()

        if not deal:
            messagebox.showerror("Error", f"ไม่พบข้อมูลดีล #{offer_id}")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"พิจารณาสัญญา: {deal['known_as']}")
        dialog.geometry("520x560")
        dialog.configure(fg_color=BG_DIALOG)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="✍️", font=("Arial", 38)).pack(pady=(20, 2))
        ctk.CTkLabel(dialog, text="พิจารณาข้อเสนอและสัญญาจากสโมสร", font=FONT_TITLE, text_color=TEXT_MAIN).pack(pady=(0, 2))
        ctk.CTkLabel(dialog, text=f"สโมสร {deal['buyer_club']} ยื่นข้อตกลงและแนบเอกสารสัญญามาให้ท่านพิจารณา", font=FONT_SMALL, text_color=TEXT_MUTED).pack(pady=(0, 16))

        card = ctk.CTkFrame(dialog, fg_color=BG_CARD, corner_radius=16, border_width=1, border_color=BORDER_SUBTLE)
        card.pack(fill="x", padx=30, pady=(0, 16))

        ctk.CTkLabel(card, text=f"⚽ นักเตะ: {deal['known_as']} ({deal['seller_club'] or 'ไร้สังกัด (Free Agent)'})", font=FONT_BODY_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(14, 4))
        ctk.CTkLabel(card, text=f"🏟️ สโมสรผู้ยื่นซื้อ: {deal['buyer_club']}", font=FONT_BODY_BOLD, text_color=COLOR_APPLE_BLUE).pack(anchor="w", padx=20, pady=(0, 4))
        ctk.CTkLabel(card, text=f"💰 ค่าตัวสโมสร: {format_currency(deal['offer_amount'])}", font=FONT_BODY, text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(0, 4))
        ctk.CTkLabel(card, text=f"💵 ค่าเหนื่อยที่เสนอ: {format_currency(deal['wage_offer'])} / สัปดาห์", font=FONT_BODY_BOLD, text_color=COLOR_GREEN).pack(anchor="w", padx=20, pady=(0, 14))

        doc_box = ctk.CTkFrame(dialog, fg_color="#F8FAFC", corner_radius=14, border_width=1, border_color=BORDER_SUBTLE)
        doc_box.pack(fill="x", padx=30, pady=(0, 20))

        if deal['contract_pdf'] and os.path.exists(deal['contract_pdf']):
            ctk.CTkLabel(doc_box, text="📄 เอกสารสัญญาที่สโมสรแนบมา: พร้อมเปิดดู", font=FONT_SMALL_BOLD, text_color=COLOR_APPLE_BLUE).pack(anchor="w", padx=16, pady=(12, 4))
            def view_doc():
                os.startfile(os.path.abspath(deal['contract_pdf']))
            ctk.CTkButton(doc_box, text="👁️ เปิดดูเอกสารสัญญาที่สโมสรแนบมา (PDF)", font=FONT_SMALL_BOLD, fg_color=BG_CARD, hover_color=BG_CARD_HOVER, text_color=TEXT_MAIN, height=32, corner_radius=16, command=view_doc).pack(anchor="w", padx=16, pady=(0, 12))
        else:
            ctk.CTkLabel(doc_box, text="ℹ️ ไม่พบไฟล์เอกสารแนบเพิ่มเติม ระบบจะออกสัญญามาตรฐานให้อัตโนมัติ", font=FONT_SMALL, text_color=TEXT_MUTED).pack(padx=16, pady=12)

        def do_confirm():
            dialog.destroy()
            self.agent_accept_and_finalize_deal(offer_id)

        ctk.CTkButton(
            dialog,
            text="✍️ ยืนยันเซ็นสัญญาจ้าง & ย้ายนักเตะเข้าทีมทันที ➔",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_APPLE_BLUE,
            hover_color=COLOR_APPLE_BLUE_HOVER,
            text_color="#FFFFFF",
            height=42,
            corner_radius=21,
            command=do_confirm
        ).pack(fill="x", padx=30, pady=(0, 8))

        ctk.CTkButton(
            dialog,
            text="ยกเลิก / ปิดหน้าต่าง",
            font=FONT_SMALL,
            fg_color="transparent",
            hover_color=BG_CARD_HOVER,
            text_color=TEXT_MUTED,
            height=28,
            command=dialog.destroy
        ).pack()

    def agent_accept_and_finalize_deal(self, offer_id):
        """เอเยนต์ตอบรับสัญญาส่วนตัว ออกเอกสาร PDF และย้ายนักเตะเข้าทีมใหม่ทันที"""
        conn = get_connection()
        deal = conn.execute("""
            SELECT t.*, p.known_as, p.nationality, p.dob, p.overall_rating, p.current_club as seller_club,
                   c.club_name as buyer_club, u.username as buyer_username
            FROM transfer_offers t
            JOIN players p ON t.player_id = p.id
            JOIN clubs c ON t.club_id = c.id
            JOIN users u ON c.user_id = u.id
            WHERE t.id = ?
        """, (offer_id,)).fetchone()

        if not deal:
            conn.close()
            messagebox.showerror("ผิดพลาด", f"ไม่พบข้อมูลดีล #{offer_id}")
            return

        weekly_wage = deal['wage_offer'] if deal['wage_offer'] > 0 else 120000.0

        # 1. Generate Player Employment Contract PDF
        emp_pdf_path = generate_player_employment_contract_pdf(
            offer_id=offer_id,
            club_name=deal['buyer_club'],
            player_name=deal['known_as'],
            weekly_wage=weekly_wage,
            contract_years=4,
            agent_name=self.agent_name
        )

        # 2. Update emp_contract_pdf in transfer_offers
        try:
            conn.execute("UPDATE transfer_offers SET emp_contract_pdf = ? WHERE id = ?", (emp_pdf_path, offer_id))
            conn.commit()
        except Exception:
            pass
        conn.close()

        # 3. Finalize Transfer Deal (Atomic update: updates players.current_club, budget, status = 'Completed')
        success, msg = complete_transfer_deal(offer_id)

        if success:
            log_audit("AGENT_CONTRACT_SIGNED", f"Agent {self.agent_name} signed employment contract for {deal['known_as']} with {deal['buyer_club']}. Deal Completed.")
            self.show_offers()
            self.show_transfer_completed_modal(deal, emp_pdf_path)
        else:
            messagebox.showerror("เกิดข้อผิดพลาดในการย้ายทีม", f"เกิดข้อผิดพลาดในการย้ายนักเตะ: {msg}")

    def show_transfer_completed_modal(self, deal, emp_pdf):
        dialog = ctk.CTkToplevel(self)
        dialog.title("ปิดดีลสำเร็จ!")
        dialog.geometry("520x460")
        dialog.configure(fg_color=BG_DIALOG)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="🎉", font=("Arial", 42)).pack(pady=(22, 2))
        ctk.CTkLabel(dialog, text="ปิดดีลการย้ายทีมสำเร็จ!", font=FONT_TITLE, text_color=TEXT_MAIN).pack(pady=(0, 4))
        ctk.CTkLabel(
            dialog,
            text=f"ปิดดีลเสร็จสมบูรณ์! นักเตะ '{deal['known_as']}' ได้ย้ายเข้าสู่สโมสร '{deal['buyer_club']}' เข้าทีมทันทีเรียบร้อยแล้ว!",
            font=FONT_SMALL,
            text_color=TEXT_MUTED,
            justify="center",
            wraplength=450
        ).pack(pady=(0, 16))

        card = ctk.CTkFrame(dialog, fg_color=BG_CARD, corner_radius=16, border_width=1, border_color=BORDER_SUBTLE)
        card.pack(fill="x", padx=30, pady=(0, 16))

        ctk.CTkLabel(card, text=f"⚽ นักเตะใหม่สังกัด: {deal['buyer_club']}", font=FONT_BODY_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(14, 4))
        ctk.CTkLabel(card, text=f"💵 ค่าเหนื่อยที่ตกลง: {format_currency(deal['wage_offer'])} / สัปดาห์", font=FONT_BODY_BOLD, text_color=COLOR_GREEN).pack(anchor="w", padx=20, pady=(0, 4))
        ctk.CTkLabel(card, text=f"📄 สัญญาจ้างนักฟุตบอลอาชีพ (ตกลงค่าเหนื่อย): ออกเอกสารเรียบร้อย", font=FONT_SMALL_BOLD, text_color=COLOR_APPLE_BLUE).pack(anchor="w", padx=20, pady=(0, 14))

        def open_emp_pdf():
            if emp_pdf and os.path.exists(emp_pdf):
                os.startfile(os.path.abspath(emp_pdf))
            else:
                messagebox.showerror("ผิดพลาด", "ไม่พบไฟล์สัญญา", parent=dialog)

        def dl_emp_pdf():
            if not emp_pdf or not os.path.exists(emp_pdf):
                messagebox.showerror("ผิดพลาด", "ไม่พบไฟล์สัญญา", parent=dialog)
                return
            default_fn = f"Employment_Contract_{deal['known_as'].replace(' ', '_')}_{deal['buyer_club'].replace(' ', '_')}.pdf"
            save_p = filedialog.asksaveasfilename(
                parent=dialog,
                defaultextension=".pdf",
                filetypes=[("เอกสาร PDF", "*.pdf")],
                initialfile=default_fn
            )
            if save_p:
                shutil.copy(emp_pdf, save_p)
                messagebox.showinfo("บันทึกสำเร็จ", f"บันทึกสัญญาลงเครื่องเรียบร้อยแล้วที่:\n{save_p}", parent=dialog)

        b_row = ctk.CTkFrame(dialog, fg_color="transparent")
        b_row.pack(fill="x", padx=30, pady=(0, 10))

        ctk.CTkButton(b_row, text="📄 เปิดดูสัญญาจ้าง (PDF)", font=FONT_SMALL_BOLD, fg_color=BG_CARD_HOVER, hover_color=BORDER_SUBTLE, text_color=TEXT_MAIN, height=36, corner_radius=18, command=open_emp_pdf).pack(side="left", expand=True, padx=4)
        ctk.CTkButton(b_row, text="💾 ดาวน์โหลดสัญญาจ้าง (PDF)", font=FONT_SMALL_BOLD, fg_color=COLOR_GREEN, hover_color="#2EB34F", text_color="#FFFFFF", height=36, corner_radius=18, command=dl_emp_pdf).pack(side="left", expand=True, padx=4)

        ctk.CTkButton(
            dialog,
            text="ตกลง / ปิดหน้าต่าง",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_APPLE_BLUE,
            hover_color=COLOR_APPLE_BLUE_HOVER,
            text_color="#FFFFFF",
            height=40,
            corner_radius=20,
            command=dialog.destroy
        ).pack(fill="x", padx=30, pady=(8, 14))

    def download_contract_file(self, pdf_path, default_fn):
        if not pdf_path or not os.path.exists(pdf_path):
            messagebox.showerror("ผิดพลาด", "ไม่พบไฟล์สัญญา PDF ในระบบ")
            return
        save_p = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("เอกสาร PDF", "*.pdf")],
            initialfile=default_fn
        )
        if save_p:
            shutil.copy(pdf_path, save_p)
            messagebox.showinfo("บันทึกสำเร็จ", f"บันทึกไฟล์สัญญาเรียบร้อยแล้วที่:\n{save_p}")

    def update_deal_status(self, offer_id, new_status):
        conn = get_connection()
        conn.execute("UPDATE transfer_offers SET status = ? WHERE id = ?", (new_status, offer_id))
        conn.commit()
        conn.close()
        log_audit("AGENT_STATUS_UPDATE", f"Deal #{offer_id} status updated to {new_status}")
        self.show_offers()

    # ==================== 3. AGENCY OVERVIEW ====================
    def show_agency_overview(self):
        self._highlight_nav("overview")
        self.clear_content()

        scroll = ctk.CTkScrollableFrame(self.main_content, fg_color=BG_APP)
        scroll.pack(fill="both", expand=True)

        create_stadium_banner(scroll, "ภาพรวมพอร์ตโฟลิโอเอเยนซี่", "สรุปข้อมูลนักเตะในความดูแล มูลค่าสัญญารวม และสถิติการย้ายทีมที่เสร็จสิ้น")

        conn = get_connection()
        total_clients = conn.execute("SELECT COUNT(*) FROM players WHERE agent_id = ?", (self.agent_id,)).fetchone()[0]
        total_val = conn.execute("SELECT IFNULL(SUM(estimated_value), 0) FROM players WHERE agent_id = ?", (self.agent_id,)).fetchone()[0]
        completed = conn.execute("SELECT COUNT(*) FROM transfer_offers t JOIN players p ON t.player_id=p.id WHERE p.agent_id=? AND t.status='Completed'", (self.agent_id,)).fetchone()[0]
        conn.close()

        stat_row = ctk.CTkFrame(scroll, fg_color="transparent")
        stat_row.pack(fill="x", padx=40, pady=(0, 24))
        stat_row.grid_columnconfigure((0, 1, 2), weight=1)

        create_stat_card(stat_row, "นักเตะในความดูแล", total_clients, "👥").grid(row=0, column=0, padx=8, sticky="ew")
        create_stat_card(stat_row, "มูลค่านักเตะรวม", format_currency(total_val), "💎").grid(row=0, column=1, padx=8, sticky="ew")
        create_stat_card(stat_row, "การย้ายทีมสำเร็จ", completed, "🏁").grid(row=0, column=2, padx=8, sticky="ew")