"""
Apple-Inspired Design System for Football Agent & Transfer Management System
Clean, minimalist, light aesthetic modeled after the Apple Store interface.
"""
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw
import os

# ==================== APPLE COLOR PALETTE ====================
# Backgrounds
BG_APP = "#F5F6F8"            # Soft Studio Frosted Light Gray
BG_TOPBAR = "#FFFFFF"         # Pure White Top Navigation Bar
BG_CARD = "#FFFFFF"           # Crisp White Card with subtle border
BG_CARD_HOVER = "#F0F0F3"     # Apple Card Hover
BG_INPUT = "#FFFFFF"          # Pure White Input fields
BG_DIALOG = "#FFFFFF"         # Dialog background

# Borders
BORDER_SUBTLE = "#E5E5EA"     # Apple Hairline border
BORDER_FOCUS = "#0071E3"      # Apple Blue Focus border

# Accents
COLOR_APPLE_BLUE = "#0071E3"  # Signature Apple Blue (Buttons, Links)
COLOR_APPLE_BLUE_HOVER = "#0077ED"
COLOR_APPLE_DARK = "#1D1D1F"  # Apple Jet Black for primary buttons & text
COLOR_APPLE_DARK_HOVER = "#333336"
COLOR_APPLE_GRAY = "#86868B"  # Apple Secondary Slate Gray
COLOR_GREEN = "#34C759"       # Apple Success Green
COLOR_GOLD = "#FF9500"        # Apple Amber Gold
COLOR_RED = "#FF3B30"         # Apple Warning Red

# Text Colors
TEXT_MAIN = "#1D1D1F"         # Apple Jet Black
TEXT_MUTED = "#86868B"        # Apple Secondary Gray
TEXT_DIM = "#AEAEB2"          # Apple Tertiary Gray
TEXT_WHITE = "#FFFFFF"        # Pure White

# Typography - Modern Kanit with Segoe UI Fallback
FONT_FAMILY = "Kanit"
FONT_HERO = (FONT_FAMILY, 30, "bold")
FONT_TITLE = (FONT_FAMILY, 24, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 18, "bold")
FONT_CARD_TITLE = (FONT_FAMILY, 16, "bold")
FONT_BODY = (FONT_FAMILY, 13)
FONT_BODY_BOLD = (FONT_FAMILY, 13, "bold")
FONT_SMALL = (FONT_FAMILY, 11)
FONT_SMALL_BOLD = (FONT_FAMILY, 11, "bold")

# Apple Status Styles
STATUS_STYLES = {
    "Active": {"fg": "#E8F8EE", "text": "#34C759", "border": "#A3E6B7"},
    "Approved": {"fg": "#E8F8EE", "text": "#34C759", "border": "#A3E6B7"},
    "Completed": {"fg": "#E8F8EE", "text": "#34C759", "border": "#A3E6B7"},
    "Accepted": {"fg": "#E8F8EE", "text": "#34C759", "border": "#A3E6B7"},
    "Accepted by Club": {"fg": "#E8F8EE", "text": "#34C759", "border": "#A3E6B7"},
    "Agent Accepted": {"fg": "#E8F8EE", "text": "#34C759", "border": "#A3E6B7"},
    "Fee Verified": {"fg": "#E8F8EE", "text": "#34C759", "border": "#A3E6B7"},
    "พร้อมย้ายทีม (Available)": {"fg": "#E8F8EE", "text": "#34C759", "border": "#A3E6B7"},

    "Pending": {"fg": "#FFF7EB", "text": "#FF9500", "border": "#FCD39D"},
    "Pending Agent": {"fg": "#FFF7EB", "text": "#FF9500", "border": "#FCD39D"},
    "Pending Price": {"fg": "#FFF7EB", "text": "#FF9500", "border": "#FCD39D"},
    "Negotiating": {"fg": "#EBF4FF", "text": "#0071E3", "border": "#BBD7FC"},
    "กำลังเจรจา (Negotiating)": {"fg": "#EBF4FF", "text": "#0071E3", "border": "#BBD7FC"},
    "Price Negotiation": {"fg": "#EBF4FF", "text": "#0071E3", "border": "#BBD7FC"},
    "Contract Pending": {"fg": "#F3EBFF", "text": "#8E44AD", "border": "#D8B4F8"},
    "Pending Approval": {"fg": "#EFF6FF", "text": "#1D4ED8", "border": "#93C5FD"},
    "Fee Payment Submitted": {"fg": "#F3EBFF", "text": "#8E44AD", "border": "#D8B4F8"},
    "Agent Payment Submitted": {"fg": "#F3EBFF", "text": "#8E44AD", "border": "#D8B4F8"},

    "Suspended": {"fg": "#FFEEEE", "text": "#FF3B30", "border": "#FFB8B8"},
    "Rejected": {"fg": "#FFEEEE", "text": "#FF3B30", "border": "#FFB8B8"},
    "Cancelled": {"fg": "#F5F5F7", "text": "#86868B", "border": "#E5E5EA"},
    "Expired": {"fg": "#F5F5F7", "text": "#86868B", "border": "#E5E5EA"},
    "ไม่พร้อมย้ายทีม (Not Available)": {"fg": "#FFEEEE", "text": "#FF3B30", "border": "#FFB8B8"},
    "Free Agent": {"fg": "#F5F5F7", "text": "#86868B", "border": "#E5E5EA"},
}

def format_currency(amount):
    """ฟังก์ชันแปลงตัวเลขเป็นสกุลเงิน € สไตล์มินิมอล"""
    try:
        val = float(amount or 0)
        if val >= 1_000_000:
            return f"€{val / 1_000_000:,.1f}M".replace(".0M", "M")
        elif val >= 1_000:
            return f"€{val / 1_000:,.0f}K"
        return f"€{val:,.0f}"
    except:
        return "€0"

def create_badge(parent, text, status_key=None):
    """สร้างสถานะแบบมินิมอลสไตล์ Apple Tag / Pill"""
    key = status_key if status_key else text
    style = STATUS_STYLES.get(key, {"fg": "#F5F5F7", "text": "#86868B", "border": "#E5E5EA"})
    
    badge = ctk.CTkFrame(
        parent,
        fg_color=style["fg"],
        corner_radius=12,
        border_width=1,
        border_color=style["border"]
    )
    label = ctk.CTkLabel(
        badge,
        text=f" {text} ",
        font=FONT_SMALL_BOLD,
        text_color=style["text"]
    )
    label.pack(padx=6, pady=2)
    return badge

def create_stat_card(parent, title, value, icon="📊", accent_color=COLOR_APPLE_BLUE):
    """การ์ดสถิติแบบ Apple Card มินิมอล โค้งมน สบายตา"""
    card = ctk.CTkFrame(
        parent,
        fg_color=BG_CARD,
        corner_radius=18,
        border_width=0
    )
    card.grid_columnconfigure(0, weight=1)

    top_row = ctk.CTkFrame(card, fg_color="transparent")
    top_row.pack(fill="x", padx=20, pady=(18, 4))
    
    ctk.CTkLabel(
        top_row,
        text=title,
        font=FONT_SMALL_BOLD,
        text_color=TEXT_MUTED
    ).pack(side="left")
    
    ctk.CTkLabel(
        top_row,
        text=icon,
        font=("Arial", 16)
    ).pack(side="right")

    ctk.CTkLabel(
        card,
        text=str(value),
        font=(FONT_FAMILY, 26, "bold"),
        text_color=TEXT_MAIN
    ).pack(anchor="w", padx=20, pady=(0, 18))

    return card

# ==================== HIGH PERFORMANCE IN-MEMORY IMAGE CACHE ====================
_IMAGE_CACHE = {}
_RAW_PIL_CACHE = {}

def get_cached_pil_image(path):
    """โหลดและแคชวัตถุ PIL.Image ในหน่วยความจำ RAM เพื่อลดการเปิดไฟล์ซ้ำซ้อน"""
    if not path:
        return None
    if path in _RAW_PIL_CACHE:
        return _RAW_PIL_CACHE[path]
    if os.path.exists(path):
        try:
            im = Image.open(path)
            im.load()  # บันทึกข้อมูลภาพเข้า RAM ทันที
            _RAW_PIL_CACHE[path] = im
            return im
        except Exception:
            return None
    return None

def clear_player_image_cache(player_id=None):
    """ล้างแคชรูปภาพเมื่อมีการแก้ไขหรืออัปโหลดรูปภาพใหม่"""
    global _IMAGE_CACHE, _RAW_PIL_CACHE
    if player_id is None:
        _IMAGE_CACHE.clear()
        _RAW_PIL_CACHE.clear()
    else:
        prefix = f"player_{player_id}"
        keys = [k for k in _IMAGE_CACHE if str(k[0]).startswith(prefix)]
        for k in keys:
            _IMAGE_CACHE.pop(k, None)

def get_player_image(player_id, size=(140, 140), image_path=None):
    """ดึงหรือสร้างภาพนักเตะสไตล์ Product Showcase ด้วยแคชความเร็วสูง (0ms Latency)"""
    cache_key = (f"player_{player_id}", size[0], size[1])
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]

    raw = None
    # 1. ใช้ image_path ที่ส่งมาจาก SQL ทันที (ไม่ต้อง Query DB ซ้ำ)
    if image_path:
        raw = get_cached_pil_image(image_path)

    # 2. ค้นหาใน DB เฉพาะกรณีที่ไม่ได้ส่ง image_path มา
    if not raw:
        try:
            from database.db_manager import get_connection
            conn = get_connection()
            p_row = conn.execute("SELECT image_path FROM players WHERE id = ?", (player_id,)).fetchone()
            conn.close()
            if p_row and p_row['image_path']:
                raw = get_cached_pil_image(p_row['image_path'])
        except Exception:
            pass

    # 3. ค้นหาจาก assets/players
    if not raw:
        photo_paths = [
            f"assets/players/player_{player_id}.png",
            f"assets/players/player_{player_id}.webp",
            f"assets/players/player_{player_id}.jpg",
            f"assets/players/player_{player_id}.jpeg",
            "assets/default_player_card.png"
        ]
        for p in photo_paths:
            raw = get_cached_pil_image(p)
            if raw:
                break

    if raw:
        ctk_img = ctk.CTkImage(light_image=raw, dark_image=raw, size=size)
        _IMAGE_CACHE[cache_key] = ctk_img
        return ctk_img
    return None

def get_stadium_banner_image(size=(1100, 135)):
    """ดึงภาพแบนเนอร์สนามฟุตบอลแบบ Light Frosted Stadium พร้อมแคช"""
    cache_key = ("stadium_banner", size[0], size[1])
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]
    raw = get_cached_pil_image("assets/bg_light_stadium_banner.jpg")
    if raw:
        ctk_img = ctk.CTkImage(light_image=raw, dark_image=raw, size=size)
        _IMAGE_CACHE[cache_key] = ctk_img
        return ctk_img
    return None

def get_stadium_full_bg(size=(1180, 740)):
    """ดึงภาพพื้นหลังเต็มจอสนามฟุตบอลแบบ Light Frosted Stadium พร้อมแคช"""
    cache_key = ("stadium_full_bg", size[0], size[1])
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]
    raw = get_cached_pil_image("assets/bg_light_stadium_full.jpg")
    if raw:
        ctk_img = ctk.CTkImage(light_image=raw, dark_image=raw, size=size)
        _IMAGE_CACHE[cache_key] = ctk_img
        return ctk_img
    return None

def get_login_hero_image(size=(400, 520)):
    """ดึงภาพฝั่งซ้ายของหน้าจอ Login พร้อมแคช"""
    cache_key = ("login_hero", size[0], size[1])
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]
    raw = get_cached_pil_image("assets/login_left_hero.png")
    if raw:
        ctk_img = ctk.CTkImage(light_image=raw, dark_image=raw, size=size)
        _IMAGE_CACHE[cache_key] = ctk_img
        return ctk_img
    return None

def get_login_corner_accent(size=(90, 90)):
    """ดึงภาพ 3D Sphere เล็กมุมขวาล่างของการ์ดพร้อมแคช"""
    cache_key = ("login_accent", size[0], size[1])
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]
    raw = get_cached_pil_image("assets/login_corner_accent.png")
    if raw:
        ctk_img = ctk.CTkImage(light_image=raw, dark_image=raw, size=size)
        _IMAGE_CACHE[cache_key] = ctk_img
        return ctk_img
    return None

def get_login_outer_bg(size=(1180, 740)):
    """ดึงภาพพื้นหลังเต็มจอสีน้ำเงิน Gradient พร้อมแคช"""
    cache_key = ("login_outer_bg", size[0], size[1])
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]
    raw = get_cached_pil_image("assets/login_outer_bg.png")
    if raw:
        ctk_img = ctk.CTkImage(light_image=raw, dark_image=raw, size=size)
        _IMAGE_CACHE[cache_key] = ctk_img
        return ctk_img
    return None

def get_login_pastel_bg(size=(1400, 900)):
    """ดึงภาพพื้นหลัง Pastel Gradient สไตล์มินิมอล พร้อมแคช"""
    cache_key = ("login_pastel_bg", size[0], size[1])
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]
    raw = get_cached_pil_image("assets/bg_pastel_login.png")
    if raw:
        ctk_img = ctk.CTkImage(light_image=raw, dark_image=raw, size=size)
        _IMAGE_CACHE[cache_key] = ctk_img
        return ctk_img
    return None

def get_login_team_icon(size=(140, 85)):
    """ดึงภาพไอคอนกลุ่ม 3 คน (Team Silhouette) พร้อมแคช"""
    cache_key = ("login_team_icon", size[0], size[1])
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]
    raw = get_cached_pil_image("assets/icon_login_team.png")
    if raw:
        ctk_img = ctk.CTkImage(light_image=raw, dark_image=raw, size=size)
        _IMAGE_CACHE[cache_key] = ctk_img
        return ctk_img
    return None

def create_stadium_banner(parent, title, subtitle, right_widget_fn=None, height=130):
    """สร้างแบนเนอร์หัวข้อมุมมนพร้อมพื้นหลังสนามฟุตบอลสไตล์ Apple Store"""
    banner = ctk.CTkFrame(
        parent,
        height=height,
        corner_radius=20,
        fg_color="#FFFFFF",
        border_width=1,
        border_color=BORDER_SUBTLE
    )
    banner.pack(fill="x", padx=40, pady=(16, 20))
    banner.pack_propagate(False)

    bg_img = get_stadium_banner_image(size=(1100, height))
    if bg_img:
        bg_lbl = ctk.CTkLabel(banner, image=bg_img, text="")
        bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)

    content = ctk.CTkFrame(banner, fg_color="transparent")
    content.place(x=28, y=0, relwidth=0.95, relheight=1.0)

    left_box = ctk.CTkFrame(content, fg_color="transparent")
    left_box.pack(side="left", fill="y", pady=18)

    ctk.CTkLabel(
        left_box,
        text=title,
        font=(FONT_FAMILY, 24, "bold"),
        text_color=TEXT_MAIN
    ).pack(anchor="w")

    ctk.CTkLabel(
        left_box,
        text=subtitle,
        font=FONT_BODY,
        text_color=TEXT_MUTED
    ).pack(anchor="w", pady=(2, 0))

    if right_widget_fn:
        right_box = ctk.CTkFrame(content, fg_color="transparent")
        right_box.pack(side="right", fill="y", pady=18)
        right_widget_fn(right_box)

    return banner

def open_quick_switch_modal(parent, switch_callback):
    """เปิดหน้าต่างสลับบทบาทผู้ใช้แบบ 1-Click ได้จากทุกหน้าจอ"""
    dialog = ctk.CTkToplevel(parent)
    dialog.title("สลับบทบาทผู้ใช้งาน")
    dialog.geometry("520x560")
    dialog.configure(fg_color=BG_DIALOG)
    dialog.grab_set()

    ctk.CTkLabel(dialog, text="⚡", font=("Arial", 32)).pack(pady=(20, 2))
    ctk.CTkLabel(dialog, text="สลับบทบาทผู้ใช้งาน", font=FONT_SUBTITLE, text_color=TEXT_MAIN).pack(pady=(0, 2))
    ctk.CTkLabel(dialog, text="เลือกเปลี่ยนไปใช้งานพอร์ทัลของผู้ดูแลระบบ สโมสร หรือเอเยนต์ได้ทันที", font=FONT_SMALL, text_color=TEXT_MUTED).pack(pady=(0, 16))

    scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent", width=460, height=410)
    scroll.pack(fill="both", expand=True, padx=24, pady=(0, 20))

    def do_switch(un):
        dialog.destroy()
        if switch_callback:
            switch_callback(un)

    # 1. Admin
    ctk.CTkLabel(scroll, text="ผู้ดูแลระบบ", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", pady=(6, 4))
    adm_box = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=14, border_width=1, border_color=BORDER_SUBTLE)
    adm_box.pack(fill="x", pady=(0, 14))
    ctk.CTkLabel(adm_box, text="👑 ผู้ดูแลระบบส่วนกลาง (admin)", font=FONT_BODY_BOLD, text_color=TEXT_MAIN).pack(side="left", padx=16, pady=12)
    ctk.CTkButton(adm_box, text="สลับ ➔", font=FONT_SMALL_BOLD, fg_color=COLOR_APPLE_BLUE, hover_color=COLOR_APPLE_BLUE_HOVER, width=80, height=28, corner_radius=14, command=lambda: do_switch("admin")).pack(side="right", padx=14)

    # 2. Clubs
    ctk.CTkLabel(scroll, text="สโมสรฟุตบอล (ตลาดซื้อขายนักเตะ)", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", pady=(6, 4))
    clubs = []
    try:
        from database.db_manager import get_connection
        conn = get_connection()
        db_clubs = conn.execute("""
            SELECT c.club_name, u.username, IFNULL(c.country, 'Europe') as league 
            FROM clubs c 
            JOIN users u ON c.user_id = u.id 
            WHERE u.status = 'Active'
            ORDER BY c.id ASC
        """).fetchall()
        conn.close()
        for r in db_clubs:
            icon = "⚪" if "Madrid" in r['club_name'] else ("🔵" if "City" in r['club_name'] else ("🔴" if any(x in r['club_name'] for x in ['Barcelona', 'Arsenal', 'Liverpool']) else "🏟️"))
            clubs.append((f"{icon} {r['club_name']}", r['username'], r['league']))
    except Exception:
        pass

    if not clubs:
        clubs = [
            ("⚪ Real Madrid", "realmadrid", "La Liga"),
            ("🔵 Manchester City", "mancity", "Premier League"),
            ("🔴 FC Barcelona", "barcelona", "La Liga"),
            ("🔴 Arsenal", "arsenal", "Premier League"),
            ("🔴 Liverpool", "liverpool", "Premier League")
        ]

    for c_name, un, league in clubs:
        box = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=14, border_width=1, border_color=BORDER_SUBTLE)
        box.pack(fill="x", pady=4)
        left = ctk.CTkFrame(box, fg_color="transparent")
        left.pack(side="left", padx=16, pady=10)
        ctk.CTkLabel(left, text=c_name, font=FONT_BODY_BOLD, text_color=TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(left, text=league, font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w")
        ctk.CTkButton(box, text="สลับ ➔", font=FONT_SMALL_BOLD, fg_color=COLOR_APPLE_DARK, hover_color=COLOR_APPLE_DARK_HOVER, width=80, height=28, corner_radius=14, command=lambda u=un: do_switch(u)).pack(side="right", padx=14)

    # 3. Agents
    ctk.CTkLabel(scroll, text="ตัวแทนนักเตะ (เอเยนต์นักเตะ)", font=FONT_SMALL_BOLD, text_color=TEXT_MUTED).pack(anchor="w", pady=(14, 4))
    agents = [
        ("💼 Jorge Mendes", "Gestifute", "agent1"),
        ("💼 Rafaela Pimenta", "One Sarl", "agent2"),
        ("💼 Jonathan Barnett", "ICM Stellar", "agent3"),
        ("💼 Pini Zahavi", "Gol International", "agent4"),
        ("💼 Volker Struth", "Sports360", "agent5")
    ]
    for a_name, agency, un in agents:
        box = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=14, border_width=1, border_color=BORDER_SUBTLE)
        box.pack(fill="x", pady=4)
        left = ctk.CTkFrame(box, fg_color="transparent")
        left.pack(side="left", padx=16, pady=10)
        ctk.CTkLabel(left, text=a_name, font=FONT_BODY_BOLD, text_color=TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(left, text=agency, font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w")
        ctk.CTkButton(box, text="สลับ ➔", font=FONT_SMALL_BOLD, fg_color=COLOR_GREEN, hover_color="#2EB34F", width=80, height=28, corner_radius=14, command=lambda u=un: do_switch(u)).pack(side="right", padx=14)


def bind_black_card_hover(card, text_labels=None, on_click=None):
    """ผูกเอฟเฟกต์เปลี่ยนการ์ดเป็นสีดำ (#0F172A) เมื่อเคอร์เซอร์เมาส์ชี้ และคลิกเปิดดูข้อมูล/วิดีโอ"""
    text_labels = text_labels or []

    def _on_enter(e=None):
        try:
            card.configure(fg_color="#0F172A", border_color="#38BDF8", border_width=2)
            for lbl, _, hover_col in text_labels:
                lbl.configure(text_color=hover_col)
        except Exception:
            pass

    def _on_leave(e=None):
        try:
            # ตรวจสอบว่าเมาส์ยังอยู่ในขอบเขตของการ์ดหรือไม่
            x, y = card.winfo_pointerxy()
            cx, cy = card.winfo_rootx(), card.winfo_rooty()
            cw, ch = card.winfo_width(), card.winfo_height()
            if cx <= x <= cx + cw and cy <= y <= cy + ch:
                return
            card.configure(fg_color=BG_CARD, border_color=BORDER_SUBTLE, border_width=1)
            for lbl, orig_col, _ in text_labels:
                lbl.configure(text_color=orig_col)
        except Exception:
            pass

    def _bind_recursive(w):
        w.bind("<Enter>", _on_enter, add="+")
        w.bind("<Leave>", _on_leave, add="+")
        if on_click and not isinstance(w, ctk.CTkButton):
            w.bind("<Button-1>", lambda e: on_click(), add="+")
        for child in w.winfo_children():
            _bind_recursive(child)

    _bind_recursive(card)


def open_player_video_modal(parent, player_id, can_upload=False, can_download=True, on_updated=None):
    """เปิดหน้าต่างข้อมูลนักเตะพร้อมวิดีโอไฮไลท์ รองรับเอเยนต์อัปโหลดวิดีโอ และแอดมินดาวน์โหลดวิดีโอ"""
    import shutil
    from tkinter import filedialog, messagebox
    from database.db_manager import get_connection, log_audit

    conn = get_connection()
    p = conn.execute("SELECT * FROM players WHERE id = ?", (player_id,)).fetchone()
    conn.close()
    if not p:
        return

    dialog = ctk.CTkToplevel(parent)
    dialog.title(f"🎬 ข้อมูลนักเตะ & วิดีโอไฮไลท์ - {p['known_as']}")
    dialog.geometry("680x560")
    dialog.configure(fg_color="#0F172A")
    dialog.grab_set()

    # Header
    hdr = ctk.CTkFrame(dialog, fg_color="transparent")
    hdr.pack(fill="x", padx=24, pady=(18, 8))
    ctk.CTkLabel(hdr, text=f"🎬 {p['known_as']} ({p['main_position']})", font=(FONT_FAMILY, 20, "bold"), text_color="#FFFFFF").pack(side="left")
    ctk.CTkLabel(hdr, text=f"🏟️ {p['current_club'] or 'Free Agent'}  •  OVR {p['overall_rating']}", font=FONT_BODY_BOLD, text_color="#38BDF8").pack(side="right")

    # Video Stage Frame (Animated Pitch / Video Status)
    stage = ctk.CTkFrame(dialog, fg_color="#090D16", corner_radius=18, border_width=1, border_color="#38BDF8", height=260)
    stage.pack(fill="x", padx=24, pady=10)
    stage.pack_propagate(False)

    import tkinter as tk
    canvas = tk.Canvas(stage, bg="#064E3B", highlightthickness=0, height=210)
    canvas.pack(fill="both", expand=True, padx=10, pady=(10, 4))

    v_path_var = ctk.StringVar(value=p['video_path'] if 'video_path' in p.keys() and p['video_path'] else "")
    status_lbl = ctk.CTkLabel(
        stage,
        text=f"✔️ ไฟล์วิดีโอไฮไลท์: {os.path.basename(v_path_var.get())}" if v_path_var.get() else "🎥 โหมดจำลองฟอร์มการเล่น (ยังไม่ได้แนบไฟล์วิดีโอ .mp4)",
        font=FONT_SMALL_BOLD,
        text_color="#10B981" if v_path_var.get() else "#FBBF24"
    )
    status_lbl.pack(pady=(0, 6))

    # Animate highlight preview on canvas
    state = {"t": 0, "running": True}
    def _animate():
        if not state["running"] or not dialog.winfo_exists():
            return
        try:
            canvas.delete("all")
            w = max(580, canvas.winfo_width())
            h = max(190, canvas.winfo_height())
            canvas.create_rectangle(16, 12, w - 16, h - 12, outline="#34D399", width=2)
            canvas.create_line(w // 2, 12, w // 2, h - 12, fill="#34D399", width=2)
            canvas.create_oval(w // 2 - 30, h // 2 - 30, w // 2 + 30, h // 2 + 30, outline="#34D399", width=2)

            import math
            state["t"] = (state["t"] + 2) % 160
            prog = state["t"] / 160.0
            px = 60 + prog * (w - 140)
            py = h // 2 + math.sin(prog * math.pi * 3) * 45
            canvas.create_oval(px - 9, py - 9, px + 9, py + 9, fill="#38BDF8", outline="#FFFFFF", width=2)
            canvas.create_oval(px + 10, py - 6, px + 18, py + 2, fill="#FFFFFF", outline="#000000")
            canvas.create_text(w // 2, 30, text=f"HIGHLIGHT REEL: {p['known_as']} (OVR {p['overall_rating']})", fill="#FFFFFF", font=("Kanit", 12, "bold"))
            dialog.after(35, _animate)
        except Exception:
            pass
    _animate()

    # Action Buttons (Play / Upload for Agent / Download for Admin)
    btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_row.pack(fill="x", padx=24, pady=10)

    def _open_external_player():
        vp = v_path_var.get()
        if vp and os.path.exists(vp):
            os.startfile(os.path.abspath(vp))
        else:
            messagebox.showinfo("วิดีโอไฮไลท์", "กำลังเล่นวิดีโอไฮไลท์จำลองบนหน้าจอ หากมีไฟล์วิดีโอจริงระบบจะเปิดโปรแกรมเล่นวิดีโอให้ทันที", parent=dialog)

    ctk.CTkButton(
        btn_row,
        text="▶️ เปิดเล่นไฟล์วิดีโอ",
        font=FONT_SMALL_BOLD,
        fg_color="#1B9AE5",
        hover_color="#1583C7",
        height=38,
        corner_radius=19,
        command=_open_external_player
    ).pack(side="left", padx=(0, 8))

    if can_upload:
        def _upload_video():
            f = filedialog.askopenfilename(
                title="เลือกไฟล์วิดีโอไฮไลท์นักเตะ",
                filetypes=[("Video Files", "*.mp4;*.webm;*.mov;*.avi;*.mkv"), ("All Files", "*.*")],
                parent=dialog
            )
            if not f:
                return
            os.makedirs(os.path.join("assets", "videos"), exist_ok=True)
            ext = os.path.splitext(f)[1] or ".mp4"
            dest = os.path.join("assets", "videos", f"player_{player_id}{ext}").replace("\\", "/")
            shutil.copy(f, dest)
            c = get_connection()
            c.execute("UPDATE players SET video_path = ? WHERE id = ?", (dest, player_id))
            c.commit()
            c.close()
            v_path_var.set(dest)
            status_lbl.configure(text=f"✔️ อัปโหลดวิดีโอสำเร็จ: {os.path.basename(dest)}", text_color="#10B981")
            log_audit("VIDEO_UPLOADED", f"Uploaded highlight video for {p['known_as']}: {dest}")
            if on_updated:
                on_updated()
            messagebox.showinfo("อัปโหลดสำเร็จ", f"อัปโหลดวิดีโอของ {p['known_as']} เรียบร้อยแล้ว!", parent=dialog)

        ctk.CTkButton(
            btn_row,
            text="📤 อัปโหลดวิดีโอ (Agent/Admin)",
            font=FONT_SMALL_BOLD,
            fg_color="#8B5CF6",
            hover_color="#7C3AED",
            height=38,
            corner_radius=19,
            command=_upload_video
        ).pack(side="left", padx=(0, 8))

    if can_download:
        def _download_video():
            vp = v_path_var.get()
            ext = os.path.splitext(vp)[1] if vp else ".mp4"
            save_path = filedialog.asksaveasfilename(
                title="บันทึกไฟล์วิดีโอไฮไลท์นักเตะ",
                initialfile=f"highlight_{p['known_as'].replace(' ', '_')}{ext}",
                defaultextension=ext,
                filetypes=[("Video File", f"*{ext}"), ("All Files", "*.*")],
                parent=dialog
            )
            if not save_path:
                return
            if vp and os.path.exists(vp):
                shutil.copy(vp, save_path)
            else:
                # สร้างไฟล์วิดีโอตัวอย่างให้สามารถดาวน์โหลดเก็บไว้ได้ทันที
                os.makedirs(os.path.join("assets", "videos"), exist_ok=True)
                with open(save_path, "wb") as f_out:
                    f_out.write(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42mp41")
            messagebox.showinfo("ดาวน์โหลดสำเร็จ", f"บันทึกไฟล์วิดีโอไปยัง:\n{save_path}\nเรียบร้อยแล้ว!", parent=dialog)

        ctk.CTkButton(
            btn_row,
            text="⬇️ ดาวน์โหลดวิดีโอ (Admin)",
            font=FONT_SMALL_BOLD,
            fg_color="#10B981",
            hover_color="#059669",
            height=38,
            corner_radius=19,
            command=_download_video
        ).pack(side="right")

    ctk.CTkButton(
        dialog,
        text="ปิดหน้าต่าง",
        font=FONT_SMALL_BOLD,
        fg_color="#1E293B",
        hover_color="#334155",
        text_color="#FFFFFF",
        height=36,
        corner_radius=18,
        command=dialog.destroy
    ).pack(fill="x", padx=24, pady=(12, 16))



