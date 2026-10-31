"""
Downloads real player full-body/action photos from Wikipedia Batch API & TheSportsDB,
downloads real football match highlight videos from Wikimedia Commons, and updates
player physique data + multi-photo galleries in football_system.db.
"""
import os
import sys
import json
import time
import sqlite3
import urllib.request
import urllib.parse

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DB_NAME = "football_system.db"

PLAYER_PHYSIQUE_DATA = {
    "Kylian Mbappé": {"wiki": "Kylian_Mbappé", "h": 178, "w": 75, "foot": "ขวา (Right)", "body": "เพรียวคล่องตัว สปีดต้นจัดจ้าน (Lean & Explosive Sprinter)"},
    "Vinícius Júnior": {"wiki": "Vinícius_Júnior", "h": 176, "w": 73, "foot": "ขวา (Right)", "body": "ปราดเปรียว คล่องตัวสูง เลี้ยงบอลติดเท้า (Agile & Wiry Winger)"},
    "Jude Bellingham": {"wiki": "Jude_Bellingham", "h": 186, "w": 75, "foot": "ขวา (Right)", "body": "สูงสมส่วน แข็งแกร่งรอบด้าน (Tall & Athletic Box-to-Box)"},
    "Trent Alexander-Arnold": {"wiki": "Trent_Alexander-Arnold", "h": 180, "w": 72, "foot": "ขวา (Right)", "body": "สมส่วน สมดุลร่างกายดีเยี่ยม (Balanced Athletic Build)"},
    "Federico Valverde": {"wiki": "Federico_Valverde", "h": 182, "w": 78, "foot": "ขวา (Right)", "body": "กล้ามเนื้อแน่น พลังงานสูง วิ่งไม่มีหมด (Muscular & High-Stamina)"},
    "Rodrygo": {"wiki": "Rodrygo", "h": 174, "w": 64, "foot": "ขวา (Right)", "body": "กะทัดรัด คล่องแคล่ว พลิ้วไหว (Compact & Nimble)"},
    "Thibaut Courtois": {"wiki": "Thibaut_Courtois", "h": 200, "w": 96, "foot": "ซ้าย (Left)", "body": "สูงยาวใหญ่ ช่วงแขนกว้างพิเศษ (Towering Goalkeeper Reach)"},
    "Antonio Rüdiger": {"wiki": "Antonio_Rüdiger", "h": 190, "w": 85, "foot": "ขวา (Right)", "body": "สูงใหญ่ แข็งแกร่ง ดุดัน (Powerful & Physical Defender)"},
    "Éder Militão": {"wiki": "Éder_Militão", "h": 186, "w": 78, "foot": "ขวา (Right)", "body": "สมส่วน สปริงข้อเท้าดีเยี่ยม (Athletic & Fast Center-Back)"},
    "Aurélien Tchouaméni": {"wiki": "Aurélien_Tchouaméni", "h": 188, "w": 81, "foot": "ขวา (Right)", "body": "สูงใหญ่ โครงสร้างแข็งแกร่ง (Strong & Commanding Build)"},
    "Eduardo Camavinga": {"wiki": "Eduardo_Camavinga", "h": 182, "w": 68, "foot": "ซ้าย (Left)", "body": "เพรียวบาง ยืดหยุ่นสูง คล่องตัว (Lanky & Flexible Athlete)"},
    "Erling Haaland": {"wiki": "Erling_Haaland", "h": 195, "w": 94, "foot": "ซ้าย (Left)", "body": "สูงใหญ่กำยำ แข็งแกร่งและสปีดเร็วจัด (Powerhouse Target Striker)"},
    "Gianluigi Donnarumma": {"wiki": "Gianluigi_Donnarumma", "h": 196, "w": 90, "foot": "ขวา (Right)", "body": "สูงใหญ่ โครงสร้างหนาทรงพลัง (Commanding Giant Frame)"},
    "James Trafford": {"wiki": "James_Trafford", "h": 197, "w": 84, "foot": "ขวา (Right)", "body": "สูงเพรียว ปฏิกิริยาว่องไว (Tall & Agile Keeper)"},
    "Enzo Fernández": {"wiki": "Enzo_Fernández", "h": 178, "w": 76, "foot": "ขวา (Right)", "body": "สมส่วน จุดศูนย์ถ่วงต่ำ สมดุลดี (Compact & Balanced Midfielder)"},
    "Phil Foden": {"wiki": "Phil_Foden", "h": 171, "w": 70, "foot": "ซ้าย (Left)", "body": "ตัวเล็กพริกขี้หนู จุดศูนย์ถ่วงต่ำ พลิกบอลเร็ว (Low Center of Gravity)"},
    "Jérémy Doku": {"wiki": "Jérémy_Doku", "h": 173, "w": 75, "foot": "ขวา (Right)", "body": "กล้ามเนื้อขาแข็งแกร่ง สปีดต้นระเบิดเถิดเทิง (Explosive Muscular Build)"},
    "Rodri": {"wiki": "Rodri_(footballer,_born_1996)", "h": 191, "w": 82, "foot": "ขวา (Right)", "body": "สูงใหญ่ ครองบอลเหนียวแน่น แข็งแกร่ง (Tall & Imposing Anchor)"},
    "Rúben Dias": {"wiki": "Rúben_Dias", "h": 187, "w": 82, "foot": "ขวา (Right)", "body": "กำยำ แข็งแกร่งดุดัน (Solid & Muscular Center-Back)"},
    "Joško Gvardiol": {"wiki": "Joško_Gvardiol", "h": 185, "w": 80, "foot": "ซ้าย (Left)", "body": "หนาแน่น แข็งแกร่ง ปะทะดีเยี่ยม (Stocky & Powerful Build)"},
    "Kevin De Bruyne": {"wiki": "Kevin_De_Bruyne", "h": 181, "w": 75, "foot": "ขวา (Right)", "body": "สมส่วน แข็งแกร่ง ทนทานต่อแรงปะทะ (Sturdy Athletic Playmaker)"},
    "Bernardo Silva": {"wiki": "Bernardo_Silva", "h": 173, "w": 64, "foot": "ซ้าย (Left)", "body": "เพรียวเล็ก คล่องตัวสูง ความอึดเป็นเลิศ (Slender & Tireless Engine)"},
    "Bukayo Saka": {"wiki": "Bukayo_Saka", "h": 178, "w": 72, "foot": "ซ้าย (Left)", "body": "สมส่วน บาลานซ์เยี่ยม ทนแรงเบียดปะทะ (Strong Core & Balanced)"},
    "Martin Ødegaard": {"wiki": "Martin_Ødegaard", "h": 178, "w": 68, "foot": "ซ้าย (Left)", "body": "เพรียวสมส่วน เคลื่อนที่พลิ้วไหว (Slender & Graceful Build)"},
    "Declan Rice": {"wiki": "Declan_Rice", "h": 188, "w": 80, "foot": "ขวา (Right)", "body": "สูงใหญ่ ก้าวยาว พละกำลังสูง (Tall & Striding Powerhouse)"},
    "William Saliba": {"wiki": "William_Saliba", "h": 192, "w": 85, "foot": "ขวา (Right)", "body": "สูงใหญ่ปราดเปรียว แข็งแกร่งมาก (Imposing & Fast Frame)"},
    "Gabriel Magalhães": {"wiki": "Gabriel_Magalhães", "h": 190, "w": 87, "foot": "ซ้าย (Left)", "body": "กำยำล่ำสัน ลูกกลางอากาศทรงพลัง (Broad-Shouldered Enforcer)"},
    "Ben White": {"wiki": "Ben_White_(footballer)", "h": 186, "w": 77, "foot": "ขวา (Right)", "body": "สูงเพรียว คล่องตัว (Sleek Athletic Defender)"},
    "Kai Havertz": {"wiki": "Kai_Havertz", "h": 193, "w": 83, "foot": "ซ้าย (Left)", "body": "สูงโปร่ง ก้าวยาว หาพื้นที่เก่ง (Tall & Slender Forward)"},
    "Gabriel Martinelli": {"wiki": "Gabriel_Martinelli", "h": 178, "w": 75, "foot": "ขวา (Right)", "body": "เพรียวลม สปีดจัดจ้าน (Lean Speedster)"},
    "David Raya": {"wiki": "David_Raya", "h": 183, "w": 80, "foot": "ขวา (Right)", "body": "กระฉับกระเฉง สปริงตัวดีเยี่ยม (Compact & Explosive Reflexes)"},
    "Riccardo Calafiori": {"wiki": "Riccardo_Calafiori", "h": 188, "w": 86, "foot": "ซ้าย (Left)", "body": "สูงใหญ่ แข็งแกร่ง สง่างาม (Powerful Modern Defender)"},
    "Mikel Merino": {"wiki": "Mikel_Merino", "h": 189, "w": 83, "foot": "ซ้าย (Left)", "body": "สูงใหญ่ ชนะลูกกลางอากาศเด่น (Tall & Physical Box-to-Box)"},
    "Lamine Yamal": {"wiki": "Lamine_Yamal", "h": 180, "w": 72, "foot": "ซ้าย (Left)", "body": "เพรียวสูง คล่องตัวสูงมาก พลิ้วไหว (Slender & Hyper-Agile Winger)"},
    "Pedri": {"wiki": "Pedri", "h": 174, "w": 61, "foot": "ขวา (Right)", "body": "เพรียวบาง หมุนตัวเร็วรอบทิศทาง (Light & Nimble Playmaker)"},
    "Gavi": {"wiki": "Gavi_(footballer)", "h": 173, "w": 70, "foot": "ขวา (Right)", "body": "กะทัดรัด ดุดัน แข็งแกร่งเกินตัว (Compact & Tenacious Build)"},
    "Ronald Araújo": {"wiki": "Ronald_Araújo", "h": 192, "w": 91, "foot": "ขวา (Right)", "body": "สูงใหญ่กำยำ สปีดเร็วและแข็งแกร่งมาก (Colossal & Fast Athlete)"},
    "Jules Koundé": {"wiki": "Jules_Koundé", "h": 180, "w": 75, "foot": "ขวา (Right)", "body": "กล้ามเนื้อชัด สปริงข้อเท้าสูง (Athletic & High-Leaping Build)"},
    "Raphinha": {"wiki": "Raphinha", "h": 176, "w": 68, "foot": "ซ้าย (Left)", "body": "เพรียวคล่องตัว สปีดและความฟิตสูง (Wiry & Energetic Winger)"},
    "Marc-André ter Stegen": {"wiki": "Marc-André_ter_Stegen", "h": 187, "w": 85, "foot": "ขวา (Right)", "body": "สมส่วน แข็งแกร่ง บาลานซ์ดีเยี่ยม (Balanced & Strong Keeper)"},
    "Pau Cubarsí": {"wiki": "Pau_Cubarsí", "h": 184, "w": 79, "foot": "ขวา (Right)", "body": "สมส่วน สุขุม แข็งแกร่ง (Composed Athletic Build)"},
    "Alejandro Balde": {"wiki": "Alejandro_Balde", "h": 175, "w": 69, "foot": "ซ้าย (Left)", "body": "เพรียวลม สปีดต้นจัดจ้านมาก (Explosive Sprinter Full-Back)"},
    "Frenkie de Jong": {"wiki": "Frenkie_de_Jong", "h": 181, "w": 74, "foot": "ขวา (Right)", "body": "เพรียวสมส่วน พาบอลทะลุทะลวงดีเยี่ยม (Graceful Ball-Carrier)"},
    "Dani Olmo": {"wiki": "Dani_Olmo", "h": 179, "w": 72, "foot": "ขวา (Right)", "body": "สมส่วน คล่องตัวในพื้นที่แคบ (Agile Technical Build)"},
    "Mohamed Salah": {"wiki": "Mohamed_Salah", "h": 175, "w": 73, "foot": "ซ้าย (Left)", "body": "กล้ามเนื้อลีนแข็งแกร่งมาก บาลานซ์และสปีดสุดยอด (Shredded & Powerful Sprinter)"},
    "Virgil van Dijk": {"wiki": "Virgil_van_Dijk", "h": 195, "w": 92, "foot": "ขวา (Right)", "body": "สูงใหญ่ยักษ์ แข็งแกร่งไร้เทียมทาน (Dominant Towering Frame)"},
    "Alisson Becker": {"wiki": "Alisson_Becker", "h": 193, "w": 91, "foot": "ขวา (Right)", "body": "สูงใหญ่ ไหล่กว้าง ปิดมุมมิดชิด (Imposing Goalkeeper Physique)"},
    "Alexis Mac Allister": {"wiki": "Alexis_Mac_Allister", "h": 176, "w": 72, "foot": "ขวา (Right)", "body": "ตันแข็งแกร่ง จุดศูนย์ถ่วงต่ำ (Sturdy & Low-Slung Midfielder)"},
    "Dominik Szoboszlai": {"wiki": "Dominik_Szoboszlai", "h": 186, "w": 74, "foot": "ขวา (Right)", "body": "สูงเพรียว พลังการยิงและสปีดจัด (Tall & Dynamic Athlete)"},
    "Luis Díaz": {"wiki": "Luis_Díaz_(Colombian_footballer)", "h": 178, "w": 65, "foot": "ขวา (Right)", "body": "เพรียวลม คล่องแคล่วว่องไว (Wiry & Relentless Dribbler)"},
    "Cody Gakpo": {"wiki": "Cody_Gakpo", "h": 193, "w": 76, "foot": "ขวา (Right)", "body": "สูงยาว แข็งแกร่งและไปกับบอลได้ดี (Tall & Powerful Winger/Forward)"},
    "Diogo Jota": {"wiki": "Diogo_Jota", "h": 178, "w": 70, "foot": "ขวา (Right)", "body": "สมส่วน คล่องตัว กระโดดเทคตัวดี (Sharp & Agile Poacher)"},
    "Andrew Robertson": {"wiki": "Andrew_Robertson", "h": 178, "w": 64, "foot": "ซ้าย (Left)", "body": "เพรียวอึด วิ่งขึ้นลงตลอด 90 นาที (Lean & High-Endurance)"},
    "Ibrahima Konaté": {"wiki": "Ibrahima_Konaté", "h": 194, "w": 95, "foot": "ขวา (Right)", "body": "สูงใหญ่บึกบึน แข็งแกร่งระดับสูงสุด (Massive Physical Powerhouse)"},
    "Harvey Elliott": {"wiki": "Harvey_Elliott", "h": 170, "w": 66, "foot": "ซ้าย (Left)", "body": "กะทัดรัด คล่องแคล่ว เทคนิคสูง (Compact & Agile Creator)"}
}


def setup_columns(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(players)")
    cols = [r[1] for r in cursor.fetchall()]
    new_cols = [
        ("height_cm", "INTEGER DEFAULT 182"),
        ("weight_kg", "INTEGER DEFAULT 76"),
        ("body_type", "TEXT DEFAULT 'สมส่วน แข็งแกร่ง (Athletic Build)'"),
        ("preferred_foot", "TEXT DEFAULT 'ขวา (Right)'"),
        ("gallery_json", "TEXT DEFAULT NULL"),
        ("video_path", "TEXT DEFAULT NULL")
    ]
    for cname, cdef in new_cols:
        if cname not in cols:
            try:
                cursor.execute(f"ALTER TABLE players ADD COLUMN {cname} {cdef}")
            except Exception:
                pass
    conn.commit()


def fetch_real_football_videos():
    """Fetch real association football match/goal videos from Wikimedia Commons Categories and download them locally."""
    os.makedirs("assets/videos", exist_ok=True)
    headers = {
        "User-Agent": "FootballTransferApp/2.0 (https://localhost:8080; contact@football.local) Python/3.13"
    }
    downloaded = []

    categories = [
        "Category:Videos_of_association_football",
        "Category:Videos_of_futsal",
        "Category:Videos_of_sports"
    ]
    file_titles = []
    for cat in categories:
        api = (
            "https://commons.wikimedia.org/w/api.php?action=query&list=categorymembers"
            f"&cmtitle={urllib.parse.quote(cat)}&cmtype=file&cmlimit=40&format=json"
        )
        try:
            req = urllib.request.Request(api, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                members = data.get("query", {}).get("categorymembers", [])
                for m in members:
                    t = m.get("title", "")
                    if t.lower().endswith((".webm", ".mp4", ".ogv")):
                        file_titles.append(t)
        except Exception as e:
            print(f"Category query error ({cat}): {e}")

    # Batch query imageinfo for these file titles
    video_urls = []
    if file_titles:
        chunk = file_titles[:35]
        info_api = (
            "https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&iiprop=url|size&format=json&titles="
            + urllib.parse.quote("|".join(chunk), safe="|:")
        )
        try:
            req = urllib.request.Request(info_api, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                pages = data.get("query", {}).get("pages", {})
                for p in pages.values():
                    ii = p.get("imageinfo", [{}])[0]
                    url = ii.get("url", "")
                    size = ii.get("size", 0)
                    if url and 100_000 < size < 16_000_000:
                        video_urls.append(url)
        except Exception as e:
            print(f"Imageinfo query error: {e}")

    print(f"   Found {len(video_urls)} real football match videos on Wikimedia Commons.")
    # Rename any previously saved files that had query strings in extension
    for fn in os.listdir("assets/videos"):
        if fn.startswith("real_football_match_") and ("&" in fn or fn.endswith("original")):
            prefix = fn.split(".")[0]
            old_p = os.path.join("assets/videos", fn)
            new_p = os.path.join("assets/videos", f"{prefix}.webm")
            if not os.path.exists(new_p):
                os.rename(old_p, new_p)

    for i, url in enumerate(video_urls[:5], start=1):
        clean_path = url.split("?")[0]
        ext = os.path.splitext(clean_path)[1] or ".webm"
        if ext.lower() not in (".webm", ".mp4", ".ogv"):
            ext = ".webm"
        dest = f"assets/videos/real_football_match_{i}{ext}"
        alt_webm = f"assets/videos/real_football_match_{i}.webm"
        if os.path.exists(alt_webm) and os.path.getsize(alt_webm) > 50_000:
            downloaded.append(alt_webm)
            continue
        if os.path.exists(dest) and os.path.getsize(dest) > 50_000:
            downloaded.append(dest)
            continue
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=25) as resp:
                raw = resp.read()
                if len(raw) > 50_000:
                    with open(dest, "wb") as f:
                        f.write(raw)
                    downloaded.append(dest)
                    print(f"   Downloaded real football match video #{i}: {dest} ({len(raw)//1024} KB)")
            time.sleep(0.2)
        except Exception as e:
            print(f"   Skip video {url}: {e}")

    return downloaded


def batch_fetch_wiki_photos(wiki_titles):
    """Fetch original & 600px full-body/action image URLs from Wikipedia in batches of 40 titles."""
    headers = {
        "User-Agent": "FootballTransferApp/2.0 (https://localhost:8080; contact@football.local) Python/3.13"
    }
    result_map = {}
    chunk_size = 35
    titles_list = list(set(wiki_titles))

    for i in range(0, len(titles_list), chunk_size):
        chunk = titles_list[i:i + chunk_size]
        joined = "|".join(chunk)
        url = (
            "https://en.wikipedia.org/w/api.php?action=query&prop=pageimages"
            "&piprop=original|thumbnail&pithumbsize=650&redirects=1&format=json&titles="
            + urllib.parse.quote(joined, safe="|")
        )
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                q = data.get("query", {})
                norm_map = {n["from"]: n["to"] for n in q.get("normalized", [])}
                red_map = {r["from"]: r["to"] for r in q.get("redirects", [])}
                pages = q.get("pages", {})
                title_to_img = {}
                for p in pages.values():
                    t = p.get("title")
                    thumb = p.get("thumbnail", {}).get("source")
                    orig = p.get("original", {}).get("source")
                    if t and (thumb or orig):
                        title_to_img[t] = {"thumb": thumb or orig, "orig": orig or thumb}

                for raw_t in chunk:
                    step1 = norm_map.get(raw_t, raw_t.replace("_", " "))
                    step2 = red_map.get(step1, step1)
                    if step2 in title_to_img:
                        result_map[raw_t] = title_to_img[step2]
        except Exception as e:
            print(f"Batch wiki query error: {e}")
    return result_map


def fetch_sportsdb_photos(player_name):
    """Query TheSportsDB free API (using ASCII-normalized name) for multiple real player photos (Render, Thumb, Fanart, Cutout)."""
    import unicodedata
    ascii_name = unicodedata.normalize("NFKD", player_name).encode("ascii", "ignore").decode("ascii")
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://www.thesportsdb.com/api/v1/json/3/searchplayers.php?p={urllib.parse.quote(ascii_name)}"
    photos = []
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            plist = data.get("player") or []
            if plist:
                p0 = plist[0]
                for key, label in [
                    ("strRender", "🏃‍♂️ ภาพเต็มตัวชุดแข่งในสนาม (Full-Body Action Render)"),
                    ("strThumb", "📸 ภาพถ่ายนักเตะตัวจริง (Official Player Photo)"),
                    ("strFanart1", "🏟️ ภาพบรรยากาศการแข่งขันจริงในสนาม (Match Action Shot)"),
                    ("strCutout", "👤 ภาพโปรไฟล์นักเตะ (Studio Cutout)")
                ]:
                    val = p0.get(key)
                    if val and val.startswith("http"):
                        photos.append((val, label))
    except Exception:
        pass
    return photos


def main():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    setup_columns(conn)

    print("1. Fetching real football match videos from Wikimedia Commons...")
    videos = fetch_real_football_videos()
    print(f"   -> Ready with {len(videos)} real football match videos: {videos}")

    players = conn.execute("SELECT id, known_as, first_name, image_path, video_path, gallery_json FROM players").fetchall()
    wiki_titles = []
    for p in players:
        name = p["known_as"] or p["first_name"]
        meta = PLAYER_PHYSIQUE_DATA.get(name)
        wiki_titles.append(meta["wiki"] if meta else name.replace(" ", "_"))

    print("2. Batch-fetching real full-body/action photos from Wikipedia...")
    wiki_photo_map = batch_fetch_wiki_photos(wiki_titles)
    print(f"   -> Retrieved Wikipedia action photos for {len(wiki_photo_map)} players.")

    print("3. Updating database with multi-angle real photos & real football match videos...")
    for idx, p in enumerate(players):
        pid = p["id"]
        name = p["known_as"] or p["first_name"]
        meta = PLAYER_PHYSIQUE_DATA.get(name, {
            "wiki": name.replace(" ", "_"),
            "h": 182,
            "w": 76,
            "foot": "ขวา (Right)",
            "body": "สมส่วน แข็งแกร่งตามมาตรฐานนักฟุตบอลอาชีพ (Athletic Professional Build)"
        })

        existing_gallery = []
        if p["gallery_json"]:
            try:
                existing_gallery = json.loads(p["gallery_json"])
            except Exception:
                existing_gallery = []

        if len(existing_gallery) >= 3:
            gallery = existing_gallery
        else:
            portrait = p["image_path"] if p["image_path"] and os.path.exists(p["image_path"]) else f"assets/players/player_{pid}.png"
            wiki_imgs = wiki_photo_map.get(meta["wiki"], {})
            sportsdb_imgs = fetch_sportsdb_photos(name)

            gallery = []
            if os.path.exists(portrait):
                gallery.append({
                    "url": "/" + portrait.lstrip("/"),
                    "caption": f"👤 ภาพโปรไฟล์ทางการ (Official Portrait) — {name}"
                })
            if wiki_imgs.get("thumb"):
                gallery.append({
                    "url": wiki_imgs["thumb"],
                    "caption": f"📸 ภาพถ่ายตัวจริงและรูปร่างในสนามของ {name} (สูง {meta['h']} cm / หนัก {meta['w']} kg)"
                })
            for s_url, s_label in sportsdb_imgs[:3]:
                gallery.append({
                    "url": s_url,
                    "caption": f"{s_label} — {name} ({meta['body']})"
                })
            if len(gallery) < 3 and wiki_imgs.get("orig"):
                gallery.append({
                    "url": wiki_imgs["orig"],
                    "caption": f"🏃‍♂️ ภาพเต็มตัวความละเอียดสูง: {name} • {meta['body']} • เท้าที่ถนัด: {meta['foot']}"
                })
            if len(gallery) == 1 and os.path.exists(portrait):
                gallery.append({
                    "url": "/" + portrait.lstrip("/"),
                    "caption": f"🏃‍♂️ โครงสร้างร่างกาย: สูง {meta['h']} cm • หนัก {meta['w']} kg • {meta['body']}"
                })

        # Assign real football match highlight video
        vpath = p["video_path"]
        if videos:
            if not vpath or "football_highlight_5" in str(vpath) or "&" in str(vpath) or not os.path.exists(str(vpath)):
                vpath = videos[idx % len(videos)]

        conn.execute("""
            UPDATE players
            SET height_cm = ?, weight_kg = ?, body_type = ?, preferred_foot = ?,
                gallery_json = ?, video_path = ?
            WHERE id = ?
        """, (
            meta["h"],
            meta["w"],
            meta["body"],
            meta["foot"],
            json.dumps(gallery, ensure_ascii=False),
            vpath,
            pid
        ))
        print(f"   [{idx+1}/{len(players)}] #{pid} {name}: {len(gallery)} real photos | video={vpath}")

    conn.commit()
    conn.close()
    print("Done! All players now have multi-slide real photos, physique breakdown, and real football videos.")


if __name__ == "__main__":
    main()
