import customtkinter as ctk
from database.db_manager import (
    get_connection, log_audit, create_transfer_offer,
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
from utils.contract_generator import generate_transfer_agreement_pdf, generate_player_employment_contract_pdf

class ClubFrame(ctk.CTkFrame):
    def __init__(self, master, logout_callback, switch_callback=None):
        super().__init__(master, fg_color=BG_APP)
        self.logout_callback = logout_callback
        self.switch_callback = switch_callback or getattr(master, 'switch_user', None)
        self.current_club_id, self.current_club_name, self.current_budget = self.get_logged_in_club_info()

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.hero_photo = None
        self._build_top_navbar()
        self._build_content_area()
        self.show_market()

    def get_logged_in_club_info(self):
        user_id = CurrentSession.get_user_id()
        conn = get_connection()
        cursor = conn.cursor()
        if user_id:
            cursor.execute("SELECT id, club_name, budget FROM clubs WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                conn.close()
                return row['id'], row['club_name'], row['budget']
        
        cursor.execute("SELECT id, club_name, budget FROM clubs LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            return row['id'], row['club_name'], row['budget']
        return 1, "Real Madrid", 500000000.0

    def refresh_budget(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT budget FROM clubs WHERE id = ?", (self.current_club_id,))
        row = cursor.fetchone()
        if row:
            self.current_budget = row['budget']
            if hasattr(self, 'budget_pill'):
                self.budget_pill.configure(text=f"งบประมาณ: {format_currency(self.current_budget)}")
        conn.close()

    # ==================== TOP NAVIGATION BAR (APPLE STYLE) ====================
    def _build_top_navbar(self):
        self.topbar = ctk.CTkFrame(self, height=52, fg_color=BG_TOPBAR, corner_radius=0, border_width=1, border_color=BORDER_SUBTLE)
        self.topbar.grid(row=0, column=0, sticky="ew")
        self.topbar.grid_propagate(False)

        # Left Logo
        logo_box = ctk.CTkFrame(self.topbar, fg_color="transparent")
        logo_box.pack(side="left", padx=(30, 20))
        ctk.CTkLabel(logo_box, text=f"⚽  {self.current_club_name}", font=(FONT_FAMILY, 15, "bold"), text_color=TEXT_MAIN).pack(side="left")

        # Right Budget Pill & Logout (Pack right FIRST so it is NEVER squeezed or cut off)
        right_box = ctk.CTkFrame(self.topbar, fg_color="transparent")
        right_box.pack(side="right", padx=(0, 25))

        self.budget_pill = ctk.CTkLabel(
            right_box,
            text=f"งบประมาณ: {format_currency(self.current_budget)}",
            font=FONT_SMALL_BOLD,
            text_color=TEXT_MAIN,
            fg_color=BG_CARD,
            corner_radius=14,
            padx=12,
            pady=4
        )
        self.budget_pill.pack(side="left", padx=8)

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

        ctk.CTkButton(
            right_box,
            text="ออกจากระบบ",
            font=FONT_SMALL_BOLD,
            fg_color="transparent",
            hover_color=BG_CARD_HOVER,
            text_color=COLOR_RED,
            height=30,
            command=self.logout_callback
        ).pack(side="left", padx=4)

        # Center Navigation Menu (เมนูภาษาไทยทั้งหมด)
        self.nav_buttons = {}
        center_box = ctk.CTkFrame(self.topbar, fg_color="transparent")
        center_box.pack(side="left", expand=True)

        menus = [
            ("market", "ตลาดซื้อขายนักเตะ", self.show_market),
            ("squad", "นักเตะในทีม (My Squad)", self.show_my_squad),
            ("sent", "ข้อเสนอ & เจรจาค่าตัว", self.show_my_offers),
            ("incoming", "ข้อเสนอที่ได้รับ (ขาย)", self.show_selling_contracts),
            ("history", "ประวัติการซื้อขาย", self.show_transfer_history)
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

    # ==================== 1. TRANSFER MARKET (APPLE PRODUCT STORE) ====================
    def show_market(self):
        self._highlight_nav("market")
        self.clear_content()
        self.refresh_budget()

        scroll = ctk.CTkScrollableFrame(self.main_content, fg_color=BG_APP)
        scroll.pack(fill="both", expand=True)

        # Stadium Header Banner
        create_stadium_banner(scroll, "ตลาดซื้อขายนักเตะ", "ค้นหานักเตะระดับโลก สเกาต์ผู้เล่นฝีเท้าดี และยื่นข้อเสนอซื้อขายเข้าสู่ระบบ")

        # Search & Category Filter
        filter_box = ctk.CTkFrame(scroll, fg_color="transparent")
        filter_box.pack(pady=(0, 20))

        self.market_search = ctk.CTkEntry(
            filter_box,
            placeholder_text="🔍 ค้นหานักเตะ สโมสร สัญชาติ...",
            fg_color=BG_CARD,
            border_width=0,
            text_color=TEXT_MAIN,
            height=38,
            width=360,
            corner_radius=19
        )
        self.market_search.pack(side="left", padx=10)
        self._market_search_timer = None
        def _on_market_search_key(e):
            if self._market_search_timer:
                self.after_cancel(self._market_search_timer)
            self._market_search_timer = self.after(200, lambda: self._render_market_grid(keep_limit=False))
        self.market_search.bind("<KeyRelease>", _on_market_search_key)

        self.pos_filter = "ALL"
        self.pos_buttons = {}
        pos_display = {"ALL": "ทั้งหมด", "FW": "FW", "MF": "MF", "DF": "DF", "GK": "GK"}
        for pos in ["ALL", "FW", "MF", "DF", "GK"]:
            btn = ctk.CTkButton(
                filter_box,
                text=pos_display[pos],
                width=58 if pos == "ALL" else 50,
                height=34,
                font=FONT_SMALL_BOLD,
                fg_color=COLOR_APPLE_DARK if pos == "ALL" else BG_CARD,
                hover_color=BG_CARD_HOVER,
                text_color="#FFFFFF" if pos == "ALL" else TEXT_MAIN,
                corner_radius=17,
                command=lambda p=pos: self._set_pos_filter(p)
            )
            btn.pack(side="left", padx=3)
            self.pos_buttons[pos] = btn

        # Club Filter Dropdown (กรองเป็นสโมสรได้ โดยไม่แสดงชื่อสโมสรตัวเองในตลาดซื้อขาย)
        conn_c = get_connection()
        club_rows = [
            r[0] for r in conn_c.execute(
                "SELECT DISTINCT current_club FROM players WHERE current_club IS NOT NULL AND current_club != '' AND LOWER(TRIM(current_club)) != LOWER(TRIM(?)) ORDER BY current_club ASC",
                (self.current_club_name or "",)
            ).fetchall()
        ]
        conn_c.close()
        club_opts = ["🏢 สโมสรทั้งหมด (All)"] + club_rows
        self.market_club_filter_var = ctk.StringVar(value=club_opts[0])

        self.market_club_menu = ctk.CTkOptionMenu(
            filter_box,
            variable=self.market_club_filter_var,
            values=club_opts,
            width=180,
            height=34,
            corner_radius=17,
            fg_color=BG_CARD,
            button_color=COLOR_APPLE_BLUE,
            button_hover_color=COLOR_APPLE_BLUE_HOVER,
            text_color=TEXT_MAIN,
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color=TEXT_MAIN,
            command=lambda v: self._render_market_grid(keep_limit=False)
        )
        self.market_club_menu.pack(side="left", padx=(10, 0))

        # Sort Control (Default: Cheapest First as requested)
        sort_box = ctk.CTkFrame(filter_box, fg_color="transparent")
        sort_box.pack(side="left", padx=(12, 0))

        ctk.CTkLabel(sort_box, text="เรียงตาม:", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(side="left", padx=(0, 6))

        self.sort_var = ctk.StringVar(value="🏷️ ราคา: ต่ำไปสูง")
        self.sort_menu = ctk.CTkOptionMenu(
            sort_box,
            variable=self.sort_var,
            values=[
                "🏷️ ราคา: ต่ำไปสูง",
                "💰 ราคา: สูงไปต่ำ",
                "🌟 เรตติ้ง: สูงไปต่ำ",
                "⚡ เรตติ้ง: ต่ำไปสูง",
                "🔤 ชื่อ: ก-ฮ (A-Z)"
            ],
            width=185,
            height=34,
            corner_radius=17,
            fg_color=BG_CARD,
            button_color=COLOR_APPLE_BLUE,
            button_hover_color=COLOR_APPLE_BLUE_HOVER,
            text_color=TEXT_MAIN,
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color=TEXT_MAIN,
            command=lambda v: self._render_market_grid(keep_limit=False)
        )
        self.sort_menu.pack(side="left")

        # Product Grid Container (3 Columns like Image 2)
        self.grid_frame = ctk.CTkFrame(scroll, fg_color=BG_APP)
        self.grid_frame.pack(fill="x", padx=40, pady=(0, 40))
        self.grid_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self._render_market_grid()

    def _set_pos_filter(self, pos):
        self.pos_filter = pos
        for k, btn in self.pos_buttons.items():
            is_sel = (k == pos)
            btn.configure(
                fg_color=COLOR_APPLE_DARK if is_sel else BG_CARD,
                text_color="#FFFFFF" if is_sel else TEXT_MAIN
            )
        self._render_market_grid(keep_limit=False)

    def _render_market_grid(self, keep_limit=False):
        if not keep_limit:
            self._market_limit = 24
        limit = getattr(self, '_market_limit', 24)

        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        search_text = self.market_search.get().strip().lower() if hasattr(self, 'market_search') else ""
        sel_club = self.market_club_filter_var.get() if hasattr(self, 'market_club_filter_var') else "🏢 สโมสรทั้งหมด (All)"

        conn = get_connection()
        cursor = conn.cursor()

        sql = """
            SELECT p.*, IFNULL(a.agency_name, 'No Agent') as agent_name
            FROM players p
            LEFT JOIN agents a ON p.agent_id = a.id
            WHERE LOWER(TRIM(IFNULL(p.current_club, ''))) != LOWER(TRIM(?))
              AND p.status = 'Approved'
        """
        params = [self.current_club_name or ""]

        if self.pos_filter == "FW": sql += " AND (p.main_position IN ('ST', 'CF', 'LW', 'RW'))"
        elif self.pos_filter == "MF": sql += " AND (p.main_position IN ('CAM', 'CM', 'CDM', 'LM', 'RM'))"
        elif self.pos_filter == "DF": sql += " AND (p.main_position IN ('CB', 'LB', 'RB', 'LWB', 'RWB'))"
        elif self.pos_filter == "GK": sql += " AND p.main_position = 'GK'"

        if sel_club and sel_club != "🏢 สโมสรทั้งหมด (All)":
            sql += " AND p.current_club = ?"
            params.append(sel_club)

        if search_text:
            sql += " AND (LOWER(p.known_as) LIKE ? OR LOWER(p.nationality) LIKE ? OR LOWER(IFNULL(p.current_club, '')) LIKE ?)"
            params.extend([f"%{search_text}%", f"%{search_text}%", f"%{search_text}%"])

        # Dynamic Sorting (รองรับทั้งภาษาไทยและอังกฤษ)
        sort_val = self.sort_var.get() if hasattr(self, 'sort_var') else "🏷️ ราคา: ต่ำไปสูง"
        if "ต่ำไปสูง" in sort_val and ("ราคา" in sort_val or "Price" in sort_val):
            sql += " ORDER BY p.estimated_value ASC, p.overall_rating DESC"
        elif "สูงไปต่ำ" in sort_val and ("ราคา" in sort_val or "Price" in sort_val):
            sql += " ORDER BY p.estimated_value DESC, p.overall_rating DESC"
        elif "สูงไปต่ำ" in sort_val and ("เรตติ้ง" in sort_val or "Rating" in sort_val):
            sql += " ORDER BY p.overall_rating DESC, p.estimated_value DESC"
        elif "ต่ำไปสูง" in sort_val and ("เรตติ้ง" in sort_val or "Rating" in sort_val):
            sql += " ORDER BY p.overall_rating ASC, p.estimated_value ASC"
        elif "ชื่อ" in sort_val or "Name" in sort_val:
            sql += " ORDER BY p.known_as ASC"
        else:
            sql += " ORDER BY p.estimated_value ASC, p.overall_rating DESC"

        players = cursor.execute(sql, params).fetchall()
        conn.close()

        if not players:
            ctk.CTkLabel(self.grid_frame, text="ไม่พบนักเตะตามเงื่อนไข", font=FONT_BODY, text_color=TEXT_MUTED).grid(row=0, column=1, pady=60)
            return

        total_count = len(players)
        visible_players = players[:limit]

        for idx, p in enumerate(visible_players):
            self._create_apple_player_card(self.grid_frame, p, idx // 3, idx % 3)

        if total_count > limit:
            remaining = total_count - limit
            next_batch = min(24, remaining)
            more_row = (len(visible_players) // 3) + 1
            more_box = ctk.CTkFrame(self.grid_frame, fg_color="transparent")
            more_box.grid(row=more_row, column=0, columnspan=3, pady=(20, 10))

            def load_more():
                self._market_limit += 24
                self._render_market_grid(keep_limit=True)

            def load_all():
                self._market_limit = total_count
                self._render_market_grid(keep_limit=True)

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

    def _create_apple_player_card(self, parent, p, row, col):
        """การ์ดสินค้าพร้อมแถบพลัง OVR Rating Bar และแท็กสถิติเด่น"""
        card = ctk.CTkFrame(
            parent,
            fg_color=BG_CARD,
            corner_radius=22,
            border_width=1,
            border_color=BORDER_SUBTLE,
            height=395
        )
        card.grid(row=row, column=col, padx=12, pady=12, sticky="nsew")
        card.pack_propagate(False)

        # 1. Product Image Centered with Memory Cache & Direct Image Path
        p_img_path = p['image_path'] if 'image_path' in p.keys() else None
        img_photo = get_player_image(p['id'], size=(130, 130), image_path=p_img_path)
        img_label = ctk.CTkLabel(card, text="⚽" if not img_photo else "", image=img_photo, font=("Arial", 48))
        img_label.image = img_photo
        img_label.pack(pady=(16, 6))

        # 2. Product Title
        name_lbl = ctk.CTkLabel(
            card,
            text=p['known_as'],
            font=(FONT_FAMILY, 18, "bold"),
            text_color=TEXT_MAIN
        )
        name_lbl.pack(pady=(0, 2))

        # 3. Position Badge & Club
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

        # 4. Rating Bar & Tier
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

        # 5. Price & Value Tag
        price_text = f"From {format_currency(p['estimated_value'])}"
        price_row = ctk.CTkFrame(card, fg_color="transparent")
        price_row.pack(pady=(4, 10))

        price_lbl = ctk.CTkLabel(
            price_row,
            text=price_text,
            font=(FONT_FAMILY, 14, "bold"),
            text_color=TEXT_MAIN
        )
        price_lbl.pack(side="left", padx=4)

        if p['estimated_value'] <= 35000000:
            b_val = ctk.CTkFrame(price_row, fg_color="#E8F8EE", corner_radius=6)
            b_val.pack(side="left", padx=4)
            ctk.CTkLabel(b_val, text="🏷️ คุ้มค่าที่สุด", font=("Segoe UI", 10, "bold"), text_color=COLOR_GREEN).pack(padx=4, pady=1)

        # 6. Action Buttons (ดูวิดีโอ & เจรจาสัญญา)
        b_row = ctk.CTkFrame(card, fg_color="transparent")
        b_row.pack(fill="x", padx=22, pady=(0, 16), side="bottom")

        ctk.CTkButton(
            b_row,
            text="🎬 วิดีโอ",
            font=FONT_SMALL_BOLD,
            fg_color="#1E293B",
            hover_color="#334155",
            text_color="#FFFFFF",
            width=76,
            height=34,
            corner_radius=17,
            command=lambda pid=p['id']: open_player_video_modal(self, pid, can_upload=False, can_download=True)
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            b_row,
            text="เจรจาสัญญา",
            font=FONT_SMALL_BOLD,
            fg_color=COLOR_APPLE_BLUE,
            hover_color=COLOR_APPLE_BLUE_HOVER,
            text_color="#FFFFFF",
            height=34,
            corner_radius=17,
            command=lambda: self.open_offer_dialog(p)
        ).pack(side="left", fill="x", expand=True)

        bind_black_card_hover(
            card,
            text_labels=[(name_lbl, TEXT_MAIN, "#FFFFFF"), (club_lbl, TEXT_MUTED, "#CBD5E1"), (ovr_lbl, TEXT_MAIN, "#38BDF8"), (price_lbl, TEXT_MAIN, "#FFFFFF")],
            on_click=lambda pid=p['id']: open_player_video_modal(self, pid, can_upload=False, can_download=True)
        )

    def open_offer_dialog(self, player):
        """
        หน้าต่างยื่นข้อเสนอซื้อนักเตะ:
        - เป็นสโมสรต้องคุยกับเอเยนต์ก่อน (Agent First Negotiation)
        - ต้องแนบเอกสารสัญญาก่อนค่อยสามารถคอมเฟิร์มได้ (Document Attached Required to Confirm)
        """
        conn = get_connection()
        agent_row = conn.execute("""
            SELECT a.id, a.first_name, a.last_name, a.agency_name, u.username as agent_username
            FROM agents a
            JOIN users u ON a.user_id = u.id
            WHERE a.id = ?
        """, (player['agent_id'],)).fetchone()
        conn.close()

        agent_name = f"{agent_row['first_name']} {agent_row['last_name']}" if agent_row else "ตัวแทนนักเตะ"
        agency_name = agent_row['agency_name'] if agent_row else "สังกัดเอเยนซี่"
        agent_username = agent_row['agent_username'] if agent_row else "agent1"

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"เจรจาสัญญากับเอเยนต์: {player['known_as']}")
        dialog.geometry("520x680")
        dialog.configure(fg_color=BG_DIALOG)
        dialog.grab_set()

        scroll = ctk.CTkScrollableFrame(dialog, fg_color=BG_DIALOG)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        ctk.CTkLabel(scroll, text="💼", font=("Arial", 36)).pack(pady=(6, 2))
        ctk.CTkLabel(scroll, text="เจรจาสัญญากับเอเยนต์", font=FONT_TITLE, text_color=TEXT_MAIN).pack(pady=(0, 2))
        ctk.CTkLabel(
            scroll,
            text=f"สโมสร {self.current_club_name} กำลังยื่นข้อตกลงผ่านเอเยนต์เพื่อซื้อ '{player['known_as']}'",
            font=FONT_SMALL,
            text_color=TEXT_MUTED
        ).pack(pady=(0, 14))

        # Agent & Player Info Card
        info_card = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=16, border_width=1, border_color=BORDER_SUBTLE)
        info_card.pack(fill="x", padx=10, pady=(0, 14))

        ctk.CTkLabel(info_card, text=f"⚽ นักเตะเป้าหมาย: {player['known_as']} ({player['main_position']})", font=FONT_BODY_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=18, pady=(12, 3))
        ctk.CTkLabel(info_card, text=f"💼 เอเยนต์ผู้ดูแล: {agent_name} • {agency_name}", font=FONT_SMALL_BOLD, text_color=COLOR_APPLE_BLUE).pack(anchor="w", padx=18, pady=(0, 3))
        ctk.CTkLabel(info_card, text=f"🏟️ สังกัดปัจจุบัน: {player['current_club'] or 'ไร้สังกัด (Free Agent)'}  |  มูลค่าตลาด: {format_currency(player['estimated_value'])}", font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w", padx=18, pady=(0, 3))
        ctk.CTkLabel(info_card, text=f"💰 งบประมาณสโมสรคงเหลือ: {format_currency(self.current_budget)}", font=FONT_SMALL_BOLD, text_color=COLOR_GREEN).pack(anchor="w", padx=18, pady=(0, 12))

        # Inputs Form
        form = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=16, border_width=1, border_color=BORDER_SUBTLE)
        form.pack(fill="x", padx=10, pady=(0, 14))

        # 1. Transfer fee
        ctk.CTkLabel(form, text="1. ค่าตัวที่จะยื่นให้สโมสรต้นสังกัด (€ ยูโร):", font=FONT_SMALL_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=18, pady=(14, 2))
        fee_entry = ctk.CTkEntry(form, fg_color=BG_INPUT, border_color=BORDER_SUBTLE, text_color=TEXT_MAIN, height=36, corner_radius=8)
        fee_entry.insert(0, str(int(player['estimated_value'] or 50000000)))
        fee_entry.pack(fill="x", padx=18, pady=(0, 6))

        calc_lbl = ctk.CTkLabel(form, text="", font=FONT_SMALL, text_color=TEXT_MUTED)
        calc_lbl.pack(anchor="w", padx=18, pady=(0, 6))

        def update_calc(*args):
            try:
                amt = float(fee_entry.get().strip())
                rem = self.current_budget - amt
                if rem < 0:
                    calc_lbl.configure(text=f"⚠️ งบไม่พอ เกินงบอยู่ {format_currency(abs(rem))}", text_color=COLOR_RED)
                else:
                    calc_lbl.configure(text=f"งบประมาณคงเหลือหลังซื้อ: {format_currency(rem)}", text_color=COLOR_GREEN)
            except Exception:
                calc_lbl.configure(text="")

        fee_entry.bind("<KeyRelease>", update_calc)
        update_calc()

        # 2. Wage offer
        default_wage = max(50000.0, round(float(player['estimated_value'] or 50000000) * 0.002, -3))
        ctk.CTkLabel(form, text="2. ค่าเหนื่อยที่จะเสนอกับเอเยนต์ (€ / สัปดาห์):", font=FONT_SMALL_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=18, pady=(6, 2))
        wage_entry = ctk.CTkEntry(form, fg_color=BG_INPUT, border_color=BORDER_SUBTLE, text_color=TEXT_MAIN, height=36, corner_radius=8)
        wage_entry.insert(0, str(int(default_wage)))
        wage_entry.pack(fill="x", padx=18, pady=(0, 10))

        # 3. Contract years
        ctk.CTkLabel(form, text="3. ระยะเวลาสัญญาที่เสนอ:", font=FONT_SMALL_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=18, pady=(2, 2))
        years_var = ctk.StringVar(value="4 ปี")
        years_opt = ctk.CTkOptionMenu(form, values=["2 ปี", "3 ปี", "4 ปี", "5 ปี"], variable=years_var, height=34, corner_radius=8, fg_color=BG_APP, text_color=TEXT_MAIN, button_color=BORDER_SUBTLE)
        years_opt.pack(fill="x", padx=18, pady=(0, 14))

        # 4. Mandatory Document Attachment
        doc_card = ctk.CTkFrame(scroll, fg_color="#F8FAFC", corner_radius=16, border_width=1, border_color="#CBD5E1")
        doc_card.pack(fill="x", padx=10, pady=(0, 16))

        ctk.CTkLabel(doc_card, text="📎 แนบเอกสารสัญญา (จำเป็นต้องแนบก่อนคอมเฟิร์ม)", font=FONT_BODY_BOLD, text_color="#0F172A").pack(anchor="w", padx=18, pady=(12, 2))
        ctk.CTkLabel(doc_card, text="*ตามระเบียบ: สโมสรต้องแนบไฟล์ร่างสัญญา (PDF) ก่อนค่อยสามารถกดยืนยัน (คอมเฟิร์ม) ได้*", font=FONT_SMALL, text_color="#64748B").pack(anchor="w", padx=18, pady=(0, 8))

        doc_path = ctk.StringVar(value="")
        doc_status_lbl = ctk.CTkLabel(
            doc_card,
            text="⚠️ ยังไม่ได้แนบเอกสารสัญญา (ปุ่มคอมเฟิร์มจะยังไม่ทำงาน)",
            font=FONT_SMALL_BOLD,
            text_color=COLOR_RED
        )
        doc_status_lbl.pack(anchor="w", padx=18, pady=(0, 8))

        btn_doc_row = ctk.CTkFrame(doc_card, fg_color="transparent")
        btn_doc_row.pack(fill="x", padx=18, pady=(0, 12))

        def on_select_local_file():
            f = filedialog.askopenfilename(parent=dialog, filetypes=[("PDF Documents", "*.pdf")])
            if f:
                doc_path.set(f)
                doc_status_lbl.configure(text=f"✅ แนบเอกสารแล้ว: {os.path.basename(f)}", text_color=COLOR_GREEN)
                preview_btn.configure(state="normal")

        def on_generate_draft():
            try:
                amt = float(fee_entry.get().strip() or 0)
                wage = float(wage_entry.get().strip() or 100000)
            except Exception:
                amt = float(player['estimated_value'] or 50000000)
                wage = 120000.0

            try:
                years = int(years_var.get().split()[0])
            except Exception:
                years = 4

            # Automatically generate professional PDF proposal
            draft_pdf = generate_player_employment_contract_pdf(
                offer_id=f"draft_{player['id']}_{self.current_club_id}",
                club_name=self.current_club_name,
                player_name=player['known_as'],
                weekly_wage=wage,
                contract_years=years,
                agent_name=agent_name
            )
            doc_path.set(draft_pdf)
            doc_status_lbl.configure(text=f"✅ สร้างและแนบร่างสัญญาเรียบร้อย: {os.path.basename(draft_pdf)}", text_color=COLOR_GREEN)
            preview_btn.configure(state="normal")
            messagebox.showinfo("Draft Created", f"สร้างเอกสารร่างสัญญาเรียบร้อยแล้ว!\nสามารถกดดูเอกสาร (Preview) ได้ทันที", parent=dialog)

        def on_preview_doc():
            p = doc_path.get()
            if p and os.path.exists(p):
                os.startfile(os.path.abspath(p))
            else:
                messagebox.showerror("Error", "ไม่พบไฟล์เอกสาร", parent=dialog)

        ctk.CTkButton(
            btn_doc_row,
            text="📎 แนบไฟล์สัญญา (PDF)",
            font=FONT_SMALL_BOLD,
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            text_color=TEXT_MAIN,
            border_width=1,
            border_color=BORDER_SUBTLE,
            height=34,
            corner_radius=17,
            command=on_select_local_file
        ).pack(side="left", expand=True, padx=(0, 4))

        ctk.CTkButton(
            btn_doc_row,
            text="📄 สร้างร่างสัญญาอัตโนมัติ",
            font=FONT_SMALL_BOLD,
            fg_color="#EFF6FF",
            hover_color="#DBEAFE",
            text_color="#1D4ED8",
            border_width=1,
            border_color="#93C5FD",
            height=34,
            corner_radius=17,
            command=on_generate_draft
        ).pack(side="left", expand=True, padx=4)

        preview_btn = ctk.CTkButton(
            btn_doc_row,
            text="👁️ ดูเอกสาร",
            font=FONT_SMALL_BOLD,
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            text_color=TEXT_MAIN,
            border_width=1,
            border_color=BORDER_SUBTLE,
            height=34,
            corner_radius=17,
            state="disabled",
            command=on_preview_doc
        )
        preview_btn.pack(side="left", expand=True, padx=(4, 0))

        # Submit / Confirm Button
        def submit_offer_to_agent():
            # 1. ENFORCE ATTACHED DOCUMENT REQUIREMENT
            if not doc_path.get() or not os.path.exists(doc_path.get()):
                messagebox.showwarning(
                    "Attach Document Required",
                    "⚠️ ต้องแนบเอกสารก่อนค่อยสามารถคอมเฟิร์มได้!\n\nกรุณาคลิกปุ่ม '📄 สร้างร่างสัญญาอัตโนมัติ' หรือ '📎 แนบไฟล์สัญญา (PDF)' ก่อนกดยืนยัน",
                    parent=dialog
                )
                return

            try:
                amt = float(fee_entry.get().strip())
                wage = float(wage_entry.get().strip())
                if amt <= 0 or wage <= 0: raise ValueError
            except:
                messagebox.showwarning("Invalid", "กรุณากรอกจำนวนเงินค่าตัวและค่าเหนื่อยให้ถูกต้อง", parent=dialog)
                return

            if amt > self.current_budget:
                messagebox.showerror("Budget Exceeded", f"ค่าตัว {format_currency(amt)} เกินงบประมาณคงเหลือของสโมสร ({format_currency(self.current_budget)})", parent=dialog)
                return

            try:
                years = int(years_var.get().split()[0])
            except Exception:
                years = 4

            ok, res = create_transfer_offer(
                club_id=self.current_club_id,
                player_id=player['id'],
                offer_amount=amt,
                wage_offer=wage,
                contract_years=years,
                notes=f"ข้อเสนอซื้อและสัญญาจ้างจากสโมสร {self.current_club_name}"
            )
            if not ok:
                messagebox.showerror("ไม่สามารถยื่นข้อเสนอได้", str(res), parent=dialog)
                return

            new_oid = int(res)
            conn = get_connection()
            cursor = conn.cursor()

            # Save attached contract
            dest = f"assets/contracts/contract_{new_oid}.pdf"
            os.makedirs("assets/contracts", exist_ok=True)
            try:
                shutil.copy(doc_path.get(), dest)
            except Exception:
                dest = doc_path.get()

            cursor.execute("UPDATE transfer_offers SET contract_pdf = ? WHERE id = ?", (dest, new_oid))
            conn.commit()
            conn.close()

            log_audit("OFFER_SENT_TO_AGENT", f"{self.current_club_name} sent offer #{new_oid} with contract to Agent {agent_name} for {player['known_as']} (Fee: {format_currency(amt)}, Wage: {format_currency(wage)}/wk)")
            dialog.destroy()
            self.show_my_offers()

            messagebox.showinfo(
                "ส่งข้อเสนอสำเร็จ",
                f"✅ ส่งข้อเสนอซื้อ #{new_oid} (สถานะ: Pending รอเอเยนต์พิจารณา) และแนบเอกสารสัญญาให้เอเยนต์ '{agent_name}' เรียบร้อยแล้ว!",
                parent=self
            )

        confirm_btn = ctk.CTkButton(
            scroll,
            text="ยืนยันส่งข้อเสนอให้เอเยนต์ ➔",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_APPLE_BLUE,
            hover_color=COLOR_APPLE_BLUE_HOVER,
            text_color="#FFFFFF",
            height=44,
            corner_radius=22,
            command=submit_offer_to_agent
        )
        confirm_btn.pack(fill="x", padx=10, pady=(6, 14))

    # ==================== 2. MY SQUAD (APPLE SHOWCASE) ====================
    def show_my_squad(self):
        self._highlight_nav("squad")
        self.clear_content()

        scroll = ctk.CTkScrollableFrame(self.main_content, fg_color=BG_APP)
        scroll.pack(fill="both", expand=True)

        create_stadium_banner(scroll, f"นักเตะในทีม {self.current_club_name}", "รายชื่อนักเตะชุดใหญ่ทั้งหมดที่มีสัญญาผูกพันกับสโมสร")

        conn = get_connection()
        players = conn.execute("""
            SELECT p.*, IFNULL(a.agency_name, 'No Agent') as agent_name
            FROM players p
            LEFT JOIN agents a ON p.agent_id = a.id
            WHERE p.current_club = ?
            ORDER BY p.overall_rating DESC
        """, (self.current_club_name,)).fetchall()
        conn.close()

        total_value = sum(p['estimated_value'] or 0 for p in players)
        squad_count = len(players)
        avg_rating = int(sum(p['overall_rating'] or 75 for p in players) / squad_count) if squad_count else 0

        # Stats Cards
        stat_row = ctk.CTkFrame(scroll, fg_color="transparent")
        stat_row.pack(fill="x", padx=40, pady=(0, 24))
        stat_row.grid_columnconfigure((0, 1, 2), weight=1)

        create_stat_card(stat_row, "จำนวนนักเตะในทีม", squad_count, "👥").grid(row=0, column=0, padx=8, sticky="ew")
        create_stat_card(stat_row, "มูลค่านักเตะรวม", format_currency(total_value), "💎").grid(row=0, column=1, padx=8, sticky="ew")
        create_stat_card(stat_row, "เรตติ้งเฉลี่ย (OVR)", f"{avg_rating} OVR", "⭐").grid(row=0, column=2, padx=8, sticky="ew")

        # Squad Grid
        grid = ctk.CTkFrame(scroll, fg_color=BG_APP)
        grid.pack(fill="x", padx=40, pady=(0, 40))
        grid.grid_columnconfigure((0, 1, 2), weight=1)

        if not players:
            ctk.CTkLabel(grid, text="ยังไม่มีนักเตะในทีม", font=FONT_BODY, text_color=TEXT_MUTED).pack(pady=40)
            return

        for idx, p in enumerate(players):
            card = ctk.CTkFrame(grid, fg_color=BG_CARD, corner_radius=22, border_width=1, border_color=BORDER_SUBTLE, height=330)
            card.grid(row=idx // 3, column=idx % 3, padx=12, pady=12, sticky="nsew")
            card.pack_propagate(False)

            p_img_path = p['image_path'] if 'image_path' in p.keys() else None
            photo = get_player_image(p['id'], size=(140, 140), image_path=p_img_path)
            lbl = ctk.CTkLabel(card, text="⚽" if not photo else "", image=photo, font=("Arial", 48))
            lbl.image = photo
            lbl.pack(pady=(20, 8))

            ctk.CTkLabel(card, text=p['known_as'], font=(FONT_FAMILY, 18, "bold"), text_color=TEXT_MAIN).pack(pady=(0, 2))
            ctk.CTkLabel(card, text=f"{p['main_position']}  •  OVR {p['overall_rating'] or 75}  •  {p['nationality']}", font=FONT_SMALL, text_color=TEXT_MUTED).pack(pady=(0, 8))
            ctk.CTkLabel(card, text=f"มูลค่า: {format_currency(p['estimated_value'])}", font=(FONT_FAMILY, 14, "bold"), text_color=TEXT_MAIN).pack(pady=(0, 16))

    # ==================== 3. SENT OFFERS (BUYING) ====================
    def show_my_offers(self):
        self._highlight_nav("sent")
        self.clear_content()
        self.refresh_budget()

        scroll = ctk.CTkScrollableFrame(self.main_content, fg_color=BG_APP)
        scroll.pack(fill="both", expand=True)

        create_stadium_banner(scroll, "ข้อเสนอซื้อที่ยื่นไป (Sent Offers)", "ติดตามสถานะข้อเสนอซื้อขาย การชำระเงิน และสัญญาที่ยื่นให้สโมสรอื่น")

        conn = get_connection()
        offers = conn.execute("""
            SELECT t.*, p.known_as, p.current_club as seller_club
            FROM transfer_offers t
            JOIN players p ON t.player_id = p.id
            WHERE t.club_id = ?
            ORDER BY t.id DESC
        """, (self.current_club_id,)).fetchall()
        conn.close()

        container = ctk.CTkFrame(scroll, fg_color=BG_APP)
        container.pack(fill="x", padx=40, pady=(0, 40))

        if not offers:
            ctk.CTkLabel(container, text="ไม่มีรายการข้อเสนอที่คุณยื่นซื้อในขณะนี้", font=FONT_BODY, text_color=TEXT_MUTED).pack(pady=40)
            return

        for o in offers:
            card = ctk.CTkFrame(container, fg_color=BG_CARD, corner_radius=18, border_width=1, border_color=BORDER_SUBTLE)
            card.pack(fill="x", pady=8)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=22, pady=(16, 4))
            ctk.CTkLabel(top, text=f"ดีล #{o['id']}  —  {o['known_as']}", font=FONT_CARD_TITLE, text_color=TEXT_MAIN).pack(side="left")
            create_badge(top, o['status']).pack(side="right")

            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(fill="x", padx=22, pady=(0, 8))
            years_txt = f"{o['contract_years'] if 'contract_years' in o.keys() and o['contract_years'] else 4} ปี"
            ctk.CTkLabel(
                info,
                text=f"สโมสรต้นสังกัด: {o['seller_club'] or 'ไร้สังกัด (Free Agent)'}  |  ค่าตัว: {format_currency(o['offer_amount'])}  |  ค่าเหนื่อย: {format_currency(o['wage_offer'])}/สัปดาห์  |  สัญญา: {years_txt}",
                font=FONT_BODY,
                text_color=TEXT_MUTED
            ).pack(side="left")

            meaning_txt = OFFER_STATUS_MEANINGS.get(o['status'], o['status'])
            ctk.CTkLabel(card, text=f"📌 สถานะระบบ: {o['status']} — {meaning_txt}", font=FONT_SMALL_BOLD, text_color=COLOR_APPLE_BLUE).pack(anchor="w", padx=22, pady=(0, 8))

            act = ctk.CTkFrame(card, fg_color="transparent")
            act.pack(fill="x", padx=22, pady=(0, 16))

            if o['contract_pdf'] and os.path.exists(o['contract_pdf']):
                def make_open_b(p): return lambda: os.startfile(os.path.abspath(p))
                def make_dl_b(p, kn): return lambda: self.download_contract_file(p, f"Transfer_Agreement_{kn.replace(' ', '_')}.pdf")

                ctk.CTkButton(act, text="📄 ดูสัญญา (PDF)", font=FONT_SMALL_BOLD, fg_color=BG_CARD_HOVER, hover_color=BORDER_SUBTLE, text_color=TEXT_MAIN, corner_radius=15, height=32, command=make_open_b(o['contract_pdf'])).pack(side="left", padx=3)
                ctk.CTkButton(act, text="💾 ดาวน์โหลด", font=FONT_SMALL_BOLD, fg_color=BG_CARD_HOVER, hover_color=BORDER_SUBTLE, text_color=COLOR_APPLE_BLUE, corner_radius=15, height=32, command=make_dl_b(o['contract_pdf'], o['known_as'])).pack(side="left", padx=3)

            ctk.CTkButton(
                act,
                text="💬 ประวัติการเจรจา & ต่อรองราคา",
                font=FONT_SMALL_BOLD,
                fg_color="#EFF6FF",
                hover_color="#DBEAFE",
                text_color="#1D4ED8",
                corner_radius=15,
                height=32,
                command=lambda offer_row=o: self.open_club_negotiation_modal(offer_row)
            ).pack(side="left", padx=4)

            if o['status'] in ('Accepted', 'Contract Pending', 'Agent Accepted'):
                ctk.CTkButton(
                    act,
                    text="📝 ยืนยันสัญญาและส่งแอดมินอนุมัติ (Pending Approval)",
                    font=FONT_SMALL_BOLD,
                    fg_color=COLOR_APPLE_BLUE,
                    hover_color=COLOR_APPLE_BLUE_HOVER,
                    text_color="#FFFFFF",
                    corner_radius=15,
                    height=32,
                    command=lambda oid=o['id']: self._club_confirm_contract(oid)
                ).pack(side="left", padx=4)

            if o['status'] in ('Pending', 'Pending Agent', 'Negotiating', 'Accepted', 'Contract Pending'):
                ctk.CTkButton(
                    act,
                    text="🚫 ยกเลิกข้อเสนอ",
                    font=FONT_SMALL_BOLD,
                    fg_color=BG_CARD_HOVER,
                    hover_color="#FEE2E2",
                    text_color=COLOR_RED,
                    corner_radius=15,
                    height=32,
                    command=lambda oid=o['id']: self._club_cancel_offer(oid)
                ).pack(side="right", padx=4)

            if o['status'] == 'Completed':
                ctk.CTkLabel(act, text="✨ ปิดดีลสำเร็จ นักเตะเข้าทีมเรียบร้อยแล้ว!", font=FONT_SMALL_BOLD, text_color=COLOR_GREEN).pack(side="left", padx=6)
                ctk.CTkButton(act, text="🏟️ ดูนักเตะในทีม ➔", font=FONT_SMALL_BOLD, fg_color=COLOR_GREEN, hover_color="#2EB34F", text_color="#FFFFFF", corner_radius=15, height=32, command=self.show_my_squad).pack(side="left", padx=3)
            elif o['status'] == 'Pending Approval':
                ctk.CTkLabel(act, text="🛡️ รอผู้ดูแลระบบ (Admin) ตรวจสอบและอนุมัติปิดดีล", font=FONT_SMALL_BOLD, text_color=COLOR_APPLE_BLUE).pack(side="left", padx=6)
            elif o['status'] in ('Rejected', 'Cancelled', 'Expired'):
                ctk.CTkLabel(act, text=f"❌ ดีลสิ้นสุด ({o['status']})", font=FONT_SMALL_BOLD, text_color=COLOR_RED).pack(side="left", padx=6)

    def _club_confirm_contract(self, offer_id):
        ok, msg = negotiate_or_respond_offer(
            offer_id=offer_id,
            actor_role="Club",
            action="confirm_contract",
            notes=f"สโมสร {self.current_club_name} ยืนยันเงื่อนไขสัญญา ส่งให้ Admin ตรวจสอบและอนุมัติ"
        )
        if ok:
            messagebox.showinfo("สำเร็จ", msg, parent=self)
            self.show_my_offers()
        else:
            messagebox.showerror("ผิดพลาด", msg, parent=self)

    def _club_cancel_offer(self, offer_id):
        if not messagebox.askyesno("ยืนยันการยกเลิก", f"คุณต้องการยกเลิกข้อเสนอ #{offer_id} หรือไม่?"):
            return
        ok, msg = negotiate_or_respond_offer(
            offer_id=offer_id,
            actor_role="Club",
            action="cancel",
            notes=f"สโมสร {self.current_club_name} ยกเลิกข้อเสนอ"
        )
        if ok:
            self.show_my_offers()
        else:
            messagebox.showerror("ผิดพลาด", msg, parent=self)

    def open_club_negotiation_modal(self, offer):
        oid = offer['id']
        conn = get_connection()
        rounds = conn.execute("SELECT * FROM negotiations WHERE offer_id = ? ORDER BY round_no ASC, id ASC", (oid,)).fetchall()
        contract = conn.execute("SELECT * FROM contracts WHERE offer_id = ? ORDER BY id DESC LIMIT 1", (oid,)).fetchone()
        conn.close()

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"ประวัติการเจรจา & ต่อรองราคา — ดีล #{oid} ({offer['known_as']})")
        dialog.geometry("620x640")
        dialog.configure(fg_color=BG_DIALOG)
        dialog.grab_set()

        scroll = ctk.CTkScrollableFrame(dialog, fg_color=BG_DIALOG)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(scroll, text=f"💬 การเจรจาค่าตัว & สัญญา: {offer['known_as']}", font=FONT_TITLE, text_color=TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(scroll, text=f"ดีล #{oid} • สถานะปัจจุบัน: {offer['status']} ({OFFER_STATUS_MEANINGS.get(offer['status'], '')})", font=FONT_SMALL_BOLD, text_color=COLOR_APPLE_BLUE).pack(anchor="w", pady=(2, 12))

        # Rounds list
        hist_box = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=16, border_width=1, border_color=BORDER_SUBTLE)
        hist_box.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(hist_box, text="📋 ประวัติการต่อรองแต่ละรอบ (Negotiations Table)", font=FONT_BODY_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=16, pady=(12, 6))

        if not rounds:
            ctk.CTkLabel(hist_box, text="ยังไม่มีประวัติการต่อรองเพิ่มเติม", font=FONT_SMALL, text_color=TEXT_MUTED).pack(padx=16, pady=(0, 12))
        else:
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

        if contract:
            c_box = ctk.CTkFrame(scroll, fg_color="#EFF6FF", corner_radius=14, border_width=1, border_color="#93C5FD")
            c_box.pack(fill="x", pady=(0, 14))
            ctk.CTkLabel(
                c_box,
                text=f"📄 ข้อมูลสัญญา (Contracts Table): ค่าตัวที่ตกลง {format_currency(contract['agreed_fee'])} • เงินเดือน {format_currency(contract['agreed_salary'])}/wk • {contract['contract_years']} ปี • สถานะสัญญา: {contract['contract_status']}",
                font=FONT_SMALL_BOLD,
                text_color="#1D4ED8",
                wraplength=540
            ).pack(anchor="w", padx=14, pady=10)

        if offer['status'] in ('Pending', 'Pending Agent', 'Negotiating'):
            form = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=16, border_width=1, border_color=BORDER_SUBTLE)
            form.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(form, text="🔄 ยื่นข้อเสนอใหม่ / ตอบรับข้อเสนอจากเอเยนต์", font=FONT_BODY_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=16, pady=(12, 8))

            ctk.CTkLabel(form, text="ค่าตัวใหม่ (€):", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=16)
            f_ent = ctk.CTkEntry(form, fg_color=BG_INPUT, border_color=BORDER_SUBTLE, text_color=TEXT_MAIN, height=34)
            f_ent.insert(0, str(int(offer['offer_amount'] or 0)))
            f_ent.pack(fill="x", padx=16, pady=(2, 6))

            ctk.CTkLabel(form, text="ค่าเหนื่อยใหม่ (€/สัปดาห์):", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=16)
            w_ent = ctk.CTkEntry(form, fg_color=BG_INPUT, border_color=BORDER_SUBTLE, text_color=TEXT_MAIN, height=34)
            w_ent.insert(0, str(int(offer['wage_offer'] or 0)))
            w_ent.pack(fill="x", padx=16, pady=(2, 6))

            ctk.CTkLabel(form, text="ข้อความถึงเอเยนต์:", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=16)
            m_ent = ctk.CTkEntry(form, fg_color=BG_INPUT, border_color=BORDER_SUBTLE, text_color=TEXT_MAIN, height=34, placeholder_text="ระบุเงื่อนไขเพิ่มเติม...")
            m_ent.pack(fill="x", padx=16, pady=(2, 12))

            btn_r = ctk.CTkFrame(form, fg_color="transparent")
            btn_r.pack(fill="x", padx=16, pady=(0, 14))

            def send_counter():
                try:
                    nf = float(f_ent.get().strip())
                    nw = float(w_ent.get().strip())
                except Exception:
                    messagebox.showwarning("ข้อมูลไม่ถูกต้อง", "กรุณาระบุตัวเลขค่าตัวและค่าเหนื่อยให้ถูกต้อง", parent=dialog)
                    return
                ok, msg = negotiate_or_respond_offer(oid, "Club", "counter", nf, nw, 4, m_ent.get().strip() or "สโมสรยื่นข้อเสนอต่อรองใหม่")
                if ok:
                    messagebox.showinfo("สำเร็จ", msg, parent=dialog)
                    dialog.destroy()
                    self.show_my_offers()
                else:
                    messagebox.showerror("ผิดพลาด", msg, parent=dialog)

            def accept_agent_counter():
                ok, msg = negotiate_or_respond_offer(oid, "Club", "accept", notes="สโมสรยอมรับเงื่อนไขที่เอเยนต์เสนอ")
                if ok:
                    messagebox.showinfo("สำเร็จ", msg, parent=dialog)
                    dialog.destroy()
                    self.show_my_offers()
                else:
                    messagebox.showerror("ผิดพลาด", msg, parent=dialog)

            ctk.CTkButton(btn_r, text="💬 ส่งราคาต่อรองใหม่ (Negotiating)", font=FONT_SMALL_BOLD, fg_color=COLOR_APPLE_BLUE, hover_color=COLOR_APPLE_BLUE_HOVER, text_color="#FFFFFF", height=36, corner_radius=18, command=send_counter).pack(side="left", expand=True, fill="x", padx=(0, 4))
            ctk.CTkButton(btn_r, text="✅ ยอมรับราคาปัจจุบัน (Accepted)", font=FONT_SMALL_BOLD, fg_color=COLOR_GREEN, hover_color="#2EB34F", text_color="#FFFFFF", height=36, corner_radius=18, command=accept_agent_counter).pack(side="left", expand=True, fill="x", padx=(4, 0))

    def show_transfer_history(self):
        self._highlight_nav("history")
        self.clear_content()

        scroll = ctk.CTkScrollableFrame(self.main_content, fg_color=BG_APP)
        scroll.pack(fill="both", expand=True)

        create_stadium_banner(
            scroll,
            f"ประวัติการซื้อขายของสโมสร {self.current_club_name}",
            "แสดงรายการซื้อขายนักเตะที่เสร็จสมบูรณ์ (Completed) และประวัติข้อเสนอเฉพาะของสโมสรคุณ"
        )

        conn = get_connection()
        history = conn.execute("""
            SELECT h.*, p.known_as, p.main_position
            FROM transfer_history h
            LEFT JOIN players p ON h.player_id = p.id
            WHERE LOWER(h.from_club) = LOWER(?) OR LOWER(h.to_club) = LOWER(?)
            ORDER BY h.id DESC
        """, (self.current_club_name, self.current_club_name)).fetchall()
        conn.close()

        container = ctk.CTkFrame(scroll, fg_color=BG_APP)
        container.pack(fill="x", padx=40, pady=(0, 40))

        if not history:
            ctk.CTkLabel(container, text="ยังไม่มีประวัติการซื้อขายที่ปิดดีลแล้วสำหรับสโมสรนี้", font=FONT_BODY, text_color=TEXT_MUTED).pack(pady=40)
            return

        for h in history:
            card = ctk.CTkFrame(container, fg_color=BG_CARD, corner_radius=18, border_width=1, border_color=BORDER_SUBTLE)
            card.pack(fill="x", pady=6)
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=22, pady=(14, 4))
            ctk.CTkLabel(top, text=f"🏆 {h['known_as'] or 'นักเตะ'} ({h['main_position'] or '-'})", font=FONT_CARD_TITLE, text_color=TEXT_MAIN).pack(side="left")
            create_badge(top, "Completed").pack(side="right")

            ctk.CTkLabel(
                card,
                text=f"ย้ายจาก: {h['from_club']}  ➔  ไปยัง: {h['to_club']}   |   ค่าตัว: {format_currency(h['transfer_fee'])}   |   ค่าเหนื่อย: {format_currency(h['agreed_wage'])}/สัปดาห์   |   อนุมัติโดย: {h['approved_by']} ({h['completed_at']})",
                font=FONT_SMALL_BOLD,
                text_color=TEXT_MUTED
            ).pack(anchor="w", padx=22, pady=(0, 14))

    def propose_agent(self, offer_id):
        dialog = ctk.CTkToplevel(self)
        dialog.geometry("420x420")
        dialog.title("ยื่นข้อเสนอสัญญาให้เอเยนต์")
        dialog.configure(fg_color=BG_DIALOG)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="ยื่นข้อเสนอสัญญาและค่าเหนื่อย", font=FONT_SUBTITLE, text_color=TEXT_MAIN).pack(pady=(24, 10))
        ctk.CTkLabel(dialog, text="ค่าเหนื่อยรายสัปดาห์ (€):", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", padx=36, pady=(6, 2))
        wage_entry = ctk.CTkEntry(dialog, fg_color=BG_CARD, border_width=0, text_color=TEXT_MAIN, height=38, corner_radius=10)
        wage_entry.pack(fill="x", padx=36)

        pdf_path = ctk.StringVar()
        pdf_lbl = ctk.CTkLabel(dialog, text="ยังไม่ได้แนบเอกสารสัญญา (PDF)", font=FONT_SMALL, text_color=TEXT_DIM)

        def select_pdf():
            f = filedialog.askopenfilename(filetypes=[("PDF Documents", "*.pdf")])
            if f:
                pdf_path.set(f)
                pdf_lbl.configure(text=f"เลือกไฟล์แล้ว: {os.path.basename(f)}", text_color=COLOR_APPLE_BLUE)

        ctk.CTkButton(dialog, text="📎 แนบเอกสารสัญญา (PDF)", fg_color=BG_CARD, hover_color=BG_CARD_HOVER, text_color=TEXT_MAIN, height=36, corner_radius=18, command=select_pdf).pack(fill="x", padx=36, pady=(16, 4))
        pdf_lbl.pack()

        def submit():
            if not pdf_path.get() or not os.path.exists(pdf_path.get()):
                messagebox.showwarning("จำเป็นต้องแนบเอกสาร", "⚠️ กรุณาแนบเอกสารสัญญา (PDF) ก่อนค่อยสามารถคอมเฟิร์มได้!", parent=dialog)
                return

            try: wage = float(wage_entry.get().strip())
            except: wage = 100000

            dest = f"assets/contracts/contract_{offer_id}.pdf"
            os.makedirs("assets/contracts", exist_ok=True)
            try: shutil.copy(pdf_path.get(), dest)
            except Exception: dest = pdf_path.get()

            conn = get_connection()
            conn.execute("UPDATE transfer_offers SET wage_offer = ?, contract_pdf = ?, status = 'Pending Agent', contract_status = 'Awaiting Agent' WHERE id = ?", (wage, dest, offer_id))
            conn.commit()

            deal_info = conn.execute("""
                SELECT t.id, p.known_as, a.agency_name, a.first_name, a.last_name, u.username as agent_username
                FROM transfer_offers t
                JOIN players p ON t.player_id = p.id
                JOIN agents a ON p.agent_id = a.id
                JOIN users u ON a.user_id = u.id
                WHERE t.id = ?
            """, (offer_id,)).fetchone()
            conn.close()

            log_audit("WAGE_PROPOSED", f"Proposed wage of {format_currency(wage)}/wk for Deal #{offer_id}")
            dialog.destroy()
            self.show_my_offers()
            messagebox.showinfo("สำเร็จ", "ส่งข้อเสนอสัญญาให้เอเยนต์เรียบร้อยแล้ว!", parent=self)

        ctk.CTkButton(dialog, text="ส่งข้อเสนอสัญญา", font=FONT_BODY_BOLD, fg_color=COLOR_APPLE_BLUE, hover_color=COLOR_APPLE_BLUE_HOVER, height=40, corner_radius=20, command=submit).pack(fill="x", padx=36, pady=24)

    def open_payment(self, offer_id, amount, target):
        dialog = ctk.CTkToplevel(self)
        dialog.geometry("420x540")
        target_name = "สโมสรผู้ขาย" if target == "Club" else "เอเยนต์นักเตะ"
        dialog.title(f"ชำระเงินไปยัง {target_name}")
        dialog.configure(fg_color=BG_DIALOG)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=f"ชำระเงินไปยัง {target_name}", font=FONT_SUBTITLE, text_color=TEXT_MAIN).pack(pady=(20, 2))
        ctk.CTkLabel(dialog, text=format_currency(amount), font=(FONT_FAMILY, 24, "bold"), text_color=TEXT_MAIN).pack(pady=(0, 10))

        method_var = ctk.StringVar(value="Online")
        methods_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        methods_frame.pack(pady=4)
        ctk.CTkRadioButton(methods_frame, text="โอนเงินออนไลน์", variable=method_var, value="Online").pack(side="left", padx=10)
        ctk.CTkRadioButton(methods_frame, text="ธนาคาร / เงินสด", variable=method_var, value="Cash").pack(side="left", padx=10)

        # Apple Style Clean QR Simulator
        qr_box = ctk.CTkFrame(dialog, width=180, height=160, fg_color=BG_CARD, corner_radius=16)
        qr_box.pack(pady=12)
        qr_box.pack_propagate(False)
        ctk.CTkLabel(qr_box, text="📱 ชำระเงินทางอิเล็กทรอนิกส์\n\n[ จำลอง QR Code ]\n\nสแกนเพื่อทำรายการชำระเงิน", font=FONT_SMALL_BOLD, text_color=TEXT_MAIN).pack(expand=True)

        slip_path = ctk.StringVar()
        slip_lbl = ctk.CTkLabel(dialog, text="ยังไม่ได้อัปโหลดสลิปการโอนเงิน", font=FONT_SMALL, text_color=TEXT_DIM)

        def upload_slip():
            f = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.webp")])
            if f:
                slip_path.set(f)
                slip_lbl.configure(text=f"เลือกไฟล์แล้ว: {os.path.basename(f)}", text_color=COLOR_APPLE_BLUE)

        ctk.CTkButton(dialog, text="📷 อัปโหลดสลิปการโอนเงิน", fg_color=BG_CARD, hover_color=BG_CARD_HOVER, text_color=TEXT_MAIN, height=36, corner_radius=18, command=upload_slip).pack(fill="x", padx=36, pady=(4, 2))
        slip_lbl.pack()

        def confirm():
            if not slip_path.get() or not os.path.exists(slip_path.get()):
                messagebox.showwarning(
                    "ต้องแนบสลิป",
                    "⚠️ กรุณาแนบเอกสาร/สลิปหลักฐานการชำระเงินก่อนค่อยสามารถคอมเฟิร์มได้!",
                    parent=dialog
                )
                return

            dest = f"assets/slips/slip_{target}_{offer_id}.png"
            os.makedirs("assets/slips", exist_ok=True)
            try: shutil.copy(slip_path.get(), dest)
            except Exception: dest = slip_path.get()

            conn = get_connection()
            if target == "Club":
                conn.execute("UPDATE transfer_offers SET fee_payment_method=?, fee_slip=?, status='Fee Payment Submitted' WHERE id=?", (method_var.get(), dest, offer_id))
            else:
                conn.execute("UPDATE transfer_offers SET agent_payment_method=?, agent_slip=?, status='Agent Payment Submitted' WHERE id=?", (method_var.get(), dest, offer_id))
            conn.commit()
            conn.close()

            log_audit("PAYMENT_SUBMITTED", f"Submitted payment for Deal #{offer_id}")
            messagebox.showinfo("สำเร็จ", "ชำระเงินเรียบร้อยแล้ว!", parent=dialog)
            dialog.destroy()
            self.show_my_offers()

        ctk.CTkButton(dialog, text="ยืนยันการชำระเงิน", font=FONT_BODY_BOLD, fg_color=COLOR_APPLE_BLUE, hover_color=COLOR_APPLE_BLUE_HOVER, height=40, corner_radius=20, command=confirm).pack(fill="x", padx=36, pady=18)

    # ==================== 4. INCOMING OFFERS (SELLING) ====================
    def show_selling_contracts(self):
        self._highlight_nav("incoming")
        self.clear_content()

        scroll = ctk.CTkScrollableFrame(self.main_content, fg_color=BG_APP)
        scroll.pack(fill="both", expand=True)

        create_stadium_banner(scroll, "ข้อเสนอซื้อที่ได้รับ (ขายนักเตะ)", "พิจารณาข้อเสนอขอซื้อนักเตะจากสโมสรอื่น และดำเนินการออกสัญญาโอนย้าย")

        conn = get_connection()
        offers = conn.execute("""
            SELECT t.*, p.known_as, c.club_name as buyer_club
            FROM transfer_offers t
            JOIN players p ON t.player_id = p.id
            JOIN clubs c ON t.club_id = c.id
            WHERE p.current_club = ? AND t.club_id != ?
            ORDER BY t.id DESC
        """, (self.current_club_name, self.current_club_id)).fetchall()
        conn.close()

        container = ctk.CTkFrame(scroll, fg_color=BG_APP)
        container.pack(fill="x", padx=40, pady=(0, 40))

        if not offers:
            ctk.CTkLabel(container, text="ไม่มีข้อเสนอขอซื้อนักเตะของคุณในขณะนี้", font=FONT_BODY, text_color=TEXT_MUTED).pack(pady=40)
            return

        for o in offers:
            card = ctk.CTkFrame(container, fg_color=BG_CARD, corner_radius=18, border_width=1, border_color=BORDER_SUBTLE)
            card.pack(fill="x", pady=8)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=22, pady=(16, 4))
            ctk.CTkLabel(top, text=f"ข้อเสนอ #{o['id']}  —  {o['known_as']}", font=FONT_CARD_TITLE, text_color=TEXT_MAIN).pack(side="left")
            create_badge(top, o['status']).pack(side="right")

            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(fill="x", padx=22, pady=(0, 10))
            ctk.CTkLabel(info, text=f"สโมสรผู้ซื้อ: {o['buyer_club']}  |  ราคาที่เสนอ: {format_currency(o['offer_amount'])}", font=FONT_BODY, text_color=TEXT_MUTED).pack(side="left")

            act = ctk.CTkFrame(card, fg_color="transparent")
            act.pack(fill="x", padx=22, pady=(0, 16))

            if o['contract_pdf'] and os.path.exists(o['contract_pdf']):
                def make_open_s(p): return lambda: os.startfile(os.path.abspath(p))
                def make_dl_s(p, kn): return lambda: self.download_contract_file(p, f"Transfer_Agreement_{kn.replace(' ', '_')}.pdf")

                ctk.CTkButton(act, text="📄 ดูสัญญาโอนย้าย (PDF)", font=FONT_SMALL_BOLD, fg_color=BG_CARD_HOVER, hover_color=BORDER_SUBTLE, text_color=TEXT_MAIN, corner_radius=15, height=32, command=make_open_s(o['contract_pdf'])).pack(side="left", padx=3)
                ctk.CTkButton(act, text="💾 ดาวน์โหลดสัญญา", font=FONT_SMALL_BOLD, fg_color=BG_CARD_HOVER, hover_color=BORDER_SUBTLE, text_color=COLOR_APPLE_BLUE, corner_radius=15, height=32, command=make_dl_s(o['contract_pdf'], o['known_as'])).pack(side="left", padx=3)

            if o['status'] == 'Pending':
                ctk.CTkButton(act, text="✅ ตกลงราคา & ออกสัญญา (PDF)", font=FONT_SMALL_BOLD, fg_color=COLOR_APPLE_BLUE, hover_color=COLOR_APPLE_BLUE_HOVER, text_color="#FFFFFF", corner_radius=15, height=32, command=lambda oid=o['id']: self.accept_fee_and_forward_to_agent(oid)).pack(side="left", padx=4)
                ctk.CTkButton(act, text="❌ ปฏิเสธข้อเสนอ", font=FONT_SMALL_BOLD, fg_color=BG_CARD_HOVER, hover_color=BORDER_SUBTLE, text_color=COLOR_RED, corner_radius=15, height=32, command=lambda oid=o['id']: self.update_deal_status(oid, 'Rejected')).pack(side="left", padx=4)
            elif o['status'] == 'Pending Agent':
                ctk.CTkLabel(act, text="⏳ ตกลงค่าตัวแล้ว — ส่งต่อให้เอเยนต์คุยสัญญาค่าเหนื่อย", font=FONT_SMALL_BOLD, text_color=COLOR_GOLD).pack(side="left", padx=6)
            elif o['status'] == 'Completed':
                ctk.CTkLabel(act, text="✨ ย้ายทีมเสร็จสมบูรณ์ — รับค่าตัวเข้าบัญชีสโมสรแล้ว", font=FONT_SMALL_BOLD, text_color=COLOR_GREEN).pack(side="left", padx=6)
            elif o['status'] == 'Rejected':
                ctk.CTkLabel(act, text="❌ ข้อเสนอนี้ถูกปฏิเสธแล้ว", font=FONT_SMALL_BOLD, text_color=COLOR_RED).pack(side="left", padx=6)

    def accept_fee_and_forward_to_agent(self, oid):
        conn = get_connection()
        deal = conn.execute("""
            SELECT t.*, p.known_as, p.nationality, p.dob, p.overall_rating, p.current_club as seller_club,
                   c.club_name as buyer_club, a.id as agent_id, a.first_name, a.last_name, a.agency_name,
                   u.username as agent_username
            FROM transfer_offers t
            JOIN players p ON t.player_id = p.id
            JOIN clubs c ON t.club_id = c.id
            LEFT JOIN agents a ON p.agent_id = a.id
            LEFT JOIN users u ON a.user_id = u.id
            WHERE t.id = ?
        """, (oid,)).fetchone()

        if not deal:
            conn.close()
            messagebox.showerror("ข้อผิดพลาด", f"ไม่พบข้อเสนอ ID #{oid}")
            return

        # 1. Generate Transfer Agreement PDF
        pdf_path = generate_transfer_agreement_pdf(
            offer_id=oid,
            buyer_club_name=deal['buyer_club'],
            seller_club_name=deal['seller_club'] or self.current_club_name,
            player_name=deal['known_as'],
            player_nationality=deal['nationality'] or 'International',
            player_dob=deal['dob'] or '15/06/1998',
            transfer_fee=deal['offer_amount']
        )

        # 2. Update offer status to 'Pending Agent' and save contract_pdf
        default_wage = max(80000.0, round(deal['offer_amount'] * 0.002, -3))
        conn.execute("""
            UPDATE transfer_offers 
            SET status = 'Pending Agent', contract_status = 'Agreed - Forwarded to Agent', 
                contract_pdf = ?, wage_offer = CASE WHEN wage_offer <= 0 THEN ? ELSE wage_offer END
            WHERE id = ?
        """, (pdf_path, default_wage, oid))
        conn.commit()
        conn.close()

        log_audit("FEE_ACCEPTED_FORWARDED_TO_AGENT", f"{self.current_club_name} accepted fee of {format_currency(deal['offer_amount'])} for {deal['known_as']}. Deal forwarded to Agent.")

        self.show_selling_contracts()
        self.show_transfer_agreement_modal(oid, deal, pdf_path)

    def show_transfer_agreement_modal(self, oid, deal, pdf_path):
        dialog = ctk.CTkToplevel(self)
        dialog.title("สัญญาซื้อขายและส่งต่อให้เอเยนต์")
        dialog.geometry("500x520")
        dialog.configure(fg_color=BG_DIALOG)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="📜", font=("Arial", 38)).pack(pady=(20, 2))
        ctk.CTkLabel(dialog, text="ตกลงเงื่อนไขการซื้อขายสำเร็จ!", font=FONT_TITLE, text_color=TEXT_MAIN).pack(pady=(0, 4))
        ctk.CTkLabel(
            dialog,
            text=f"ตกลงราคาซื้อขาย {deal['known_as']} จำนวน {format_currency(deal['offer_amount'])} สำเร็จแล้ว!\nระบบได้จัดทำเอกสารสัญญาซื้อขาย และส่งดีลไปยังเอเยนต์เพื่อคุยสัญญาค่าเหนื่อยเรียบร้อยแล้ว",
            font=FONT_SMALL,
            text_color=TEXT_MUTED,
            justify="center",
            wraplength=440
        ).pack(pady=(0, 16))

        card = ctk.CTkFrame(dialog, fg_color=BG_CARD, corner_radius=16, border_width=1, border_color=BORDER_SUBTLE)
        card.pack(fill="x", padx=30, pady=(0, 16))

        ctk.CTkLabel(card, text=f"⚽ นักเตะ: {deal['known_as']}", font=FONT_BODY_BOLD, text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(14, 4))
        ctk.CTkLabel(card, text=f"🏟️ สโมสรผู้ซื้อ: {deal['buyer_club']}  •  สโมสรผู้ขาย: {self.current_club_name}", font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w", padx=20, pady=(0, 4))
        ctk.CTkLabel(card, text=f"💰 ค่าตัวที่ตกลง: {format_currency(deal['offer_amount'])}", font=FONT_BODY_BOLD, text_color=COLOR_GREEN).pack(anchor="w", padx=20, pady=(0, 4))
        ag_name = f"{deal['first_name']} {deal['last_name']} ({deal['agency_name']})" if deal['first_name'] else "ตัวแทนนักเตะ"
        ctk.CTkLabel(card, text=f"💼 เอเยนต์ที่รับผิดชอบ: {ag_name}", font=FONT_SMALL_BOLD, text_color=COLOR_APPLE_BLUE).pack(anchor="w", padx=20, pady=(0, 14))

        def open_pdf():
            if pdf_path and os.path.exists(pdf_path):
                os.startfile(os.path.abspath(pdf_path))
            else:
                messagebox.showerror("Error", "ไม่พบไฟล์สัญญา PDF", parent=dialog)

        def download_pdf():
            if not pdf_path or not os.path.exists(pdf_path):
                messagebox.showerror("Error", "ไม่พบไฟล์สัญญา PDF", parent=dialog)
                return
            default_fn = f"Transfer_Agreement_{deal['known_as'].replace(' ', '_')}_{deal['buyer_club'].replace(' ', '_')}.pdf"
            save_p = filedialog.asksaveasfilename(
                parent=dialog,
                defaultextension=".pdf",
                filetypes=[("PDF Documents", "*.pdf")],
                initialfile=default_fn
            )
            if save_p:
                shutil.copy(pdf_path, save_p)
                messagebox.showinfo("Saved", f"บันทึกสัญญาลงเครื่องเรียบร้อยแล้วที่:\n{save_p}", parent=dialog)

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(fill="x", padx=30, pady=(0, 10))

        ctk.CTkButton(
            btn_row,
            text="👁️ เปิดดูสัญญา (PDF)",
            font=FONT_SMALL_BOLD,
            fg_color=BG_CARD_HOVER,
            hover_color=BORDER_SUBTLE,
            text_color=TEXT_MAIN,
            height=36,
            corner_radius=18,
            command=open_pdf
        ).pack(side="left", expand=True, padx=4)

        ctk.CTkButton(
            btn_row,
            text="💾 ดาวน์โหลดสัญญา (PDF)",
            font=FONT_SMALL_BOLD,
            fg_color=COLOR_APPLE_BLUE,
            hover_color=COLOR_APPLE_BLUE_HOVER,
            text_color="#FFFFFF",
            height=36,
            corner_radius=18,
            command=save_pdf
        ).pack(side="left", expand=True, padx=4)
        ctk.CTkButton(
            dialog,
            text="ปิดหน้าต่าง",
            font=FONT_SMALL,
            fg_color="transparent",
            hover_color=BG_CARD_HOVER,
            text_color=TEXT_MUTED,
            height=28,
            command=dialog.destroy
        ).pack(pady=(6, 10))

    def download_contract_file(self, pdf_path, default_fn):
        if not pdf_path or not os.path.exists(pdf_path):
            messagebox.showerror("Error", "ไม่พบไฟล์สัญญา PDF ในระบบ")
            return
        save_p = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Documents", "*.pdf")],
            initialfile=default_fn
        )
        if save_p:
            shutil.copy(pdf_path, save_p)
            messagebox.showinfo("Saved", f"บันทึกไฟล์สัญญาเรียบร้อยแล้วที่:\n{save_p}")

    def update_deal_status(self, oid, new_status):
        conn = get_connection()
        conn.execute("UPDATE transfer_offers SET status = ? WHERE id = ?", (new_status, oid))
        conn.commit()
        conn.close()
        log_audit("SELLER_STATUS_UPDATE", f"Deal #{oid} status updated to {new_status}")
        self.show_selling_contracts()