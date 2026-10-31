import urllib.request
import sqlite3
import os
import time

CORRECT_PLAYER_DATA = {
    # Real Madrid
    2: (231747, "Kylian Mbappé"),
    3: (238794, "Vinícius Júnior"),
    4: (252371, "Jude Bellingham"),
    5: (231281, "Trent Alexander-Arnold"),
    6: (239053, "Federico Valverde"),
    7: (243812, "Rodrygo"),
    8: (192119, "Thibaut Courtois"),
    9: (205452, "Antonio Rüdiger"),
    10: (240130, "Éder Militão"),
    11: (241637, "Aurélien Tchouaméni"),
    12: (248243, "Eduardo Camavinga"),

    # Manchester City
    13: (239085, "Erling Haaland"),
    14: (230621, "Gianluigi Donnarumma"),
    15: (263063, "James Trafford"),
    16: (247090, "Enzo Fernández"),
    17: (237692, "Phil Foden"),
    18: (246420, "Jérémy Doku"),
    19: (231866, "Rodri"),
    20: (239818, "Rúben Dias"),
    21: (251517, "Joško Gvardiol"),
    22: (192985, "Kevin De Bruyne"),
    23: (218667, "Bernardo Silva"),

    # Arsenal
    24: (246669, "Bukayo Saka"),
    25: (222665, "Martin Ødegaard"),
    26: (234378, "Declan Rice"),
    27: (243715, "William Saliba"),
    28: (232580, "Gabriel Magalhães"),
    29: (231936, "Ben White"),
    30: (235790, "Kai Havertz"),
    31: (251566, "Gabriel Martinelli"),
    32: (220901, "David Raya"),
    33: (257711, "Riccardo Calafiori"),
    34: (225193, "Mikel Merino"),

    # Barcelona
    35: (277643, "Lamine Yamal"),
    36: (251854, "Pedri"),
    37: (264240, "Gavi"),
    38: (253163, "Ronald Araújo"),
    39: (241486, "Jules Koundé"),
    40: (233419, "Raphinha"),
    41: (192448, "Marc-André ter Stegen"),
    42: (278046, "Pau Cubarsí"),
    43: (263578, "Alejandro Balde"),
    44: (228702, "Frenkie de Jong"),
    45: (244260, "Dani Olmo"),

    # Liverpool
    46: (209331, "Mohamed Salah"),
    47: (203376, "Virgil van Dijk"),
    48: (212831, "Alisson Becker"),
    49: (239837, "Alexis Mac Allister"),
    50: (236772, "Dominik Szoboszlai"),
    51: (241084, "Luis Díaz"),
    52: (242516, "Cody Gakpo"),
    53: (224458, "Diogo Jota"),
    54: (216267, "Andrew Robertson"),
    55: (237678, "Ibrahima Konaté"),
    56: (246174, "Harvey Elliott")
}

def update_db_names():
    conn = sqlite3.connect("football_system.db")
    cursor = conn.cursor()
    print("🔄 กำลังอัปเดตชื่อที่แสดง (known_as) ให้ตรงกับชื่อนักเตะระดับโลก...")
    for db_id, (sofifa_id, display_name) in CORRECT_PLAYER_DATA.items():
        cursor.execute("UPDATE players SET known_as = ? WHERE id = ?", (display_name, db_id))
    conn.commit()
    conn.close()
    print("✅ อัปเดตชื่อในฐานข้อมูลเรียบร้อยแล้ว!")

def download_verified_images():
    os.makedirs("assets/players", exist_ok=True)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://sofifa.com/'
    }

    print("🚀 เริ่มดาวน์โหลดรูปภาพที่ตรวจสอบแล้ว 100% สำหรับนักเตะทุกคน...")
    success = 0
    for db_id, (sofifa_id, name) in CORRECT_PLAYER_DATA.items():
        s = str(sofifa_id).zfill(6)
        part1 = s[:3]
        part2 = s[3:]
        target = f"assets/players/player_{db_id}.png"

        downloaded = False
        for ver in ['25_120.png', '24_120.png', '23_120.png', '25_60.png', '24_60.png']:
            url = f"https://cdn.sofifa.net/players/{part1}/{part2}/{ver}"
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=4) as response:
                    data = response.read()
                    if len(data) > 500:
                        with open(target, "wb") as f:
                            f.write(data)
                        downloaded = True
                        break
            except Exception:
                pass

        if downloaded:
            success += 1
            print(f"✅ ID {db_id}: {name} (SoFIFA {sofifa_id}) -> Success")
        else:
            print(f"❌ ID {db_id}: {name} (SoFIFA {sofifa_id}) -> Failed")
        time.sleep(0.04)

    print(f"\n🎉 สำเร็จ {success}/{len(CORRECT_PLAYER_DATA)} คน!")

if __name__ == "__main__":
    update_db_names()
    download_verified_images()
