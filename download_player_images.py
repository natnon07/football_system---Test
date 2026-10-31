import urllib.request
import os
import time

PLAYER_SOFIFA_MAP = {
    # Real Madrid
    2: 231747,  # Kylian Mbappé
    3: 238794,  # Vinícius Júnior
    4: 252371,  # Jude Bellingham
    5: 231281,  # Trent Alexander-Arnold
    6: 239053,  # Federico Valverde
    7: 243812,  # Rodrygo Goes
    8: 192119,  # Thibaut Courtois
    9: 205452,  # Antonio Rüdiger
    10: 240130, # Éder Militão
    11: 241721, # Aurélien Tchouaméni
    12: 251570, # Eduardo Camavinga

    # Manchester City
    13: 239085, # Erling Haaland
    14: 230621, # Gianluigi Donnarumma
    15: 257534, # James Trafford
    16: 254278, # Enzo Fernández
    17: 237692, # Phil Foden
    18: 251852, # Jeremy Doku
    19: 231866, # Rodri Hernández
    20: 239818, # Rúben Dias
    21: 253149, # Joško Gvardiol
    22: 192985, # Kevin De Bruyne
    23: 218667, # Bernardo Silva

    # Arsenal
    24: 246669, # Bukayo Saka
    25: 222665, # Martin Ødegaard
    26: 234378, # Declan Rice
    27: 243715, # William Saliba
    28: 232580, # Gabriel Magalhães
    29: 237678, # Ben White
    30: 235790, # Kai Havertz
    31: 251809, # Gabriel Martinelli
    32: 223959, # David Raya
    33: 253306, # Riccardo Calafiori
    34: 229558, # Mikel Merino

    # Barcelona
    35: 277643, # Lamine Yamal
    36: 251854, # Pedri González
    37: 264240, # Gavi Páez
    38: 253002, # Ronald Araújo
    39: 241461, # Jules Koundé
    40: 233419, # Raphinha Belloli
    41: 192448, # Marc-André ter Stegen
    42: 275046, # Pau Cubarsí
    43: 260381, # Alejandro Balde
    44: 228702, # Frenkie de Jong
    45: 234396, # Dani Olmo

    # Liverpool
    46: 209331, # Mohamed Salah
    47: 203376, # Virgil van Dijk
    48: 212831, # Alisson Becker
    49: 256630, # Alexis Mac Allister
    50: 236772, # Dominik Szoboszlai
    51: 241084, # Luis Díaz
    52: 242530, # Cody Gakpo
    53: 224458, # Diogo Jota
    54: 216267, # Andrew Robertson
    55: 237679, # Ibrahima Konaté
    56: 247679  # Harvey Elliott
}

def download_all_players():
    os.makedirs("assets/players", exist_ok=True)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://sofifa.com/'
    }

    success_count = 0
    fail_count = 0

    print("🚀 เริ่มดาวน์โหลดรูปภาพนักเตะทั้ง 55 คน...")
    for db_id, sofifa_id in PLAYER_SOFIFA_MAP.items():
        s = str(sofifa_id).zfill(6)
        part1 = s[:3]
        part2 = s[3:]
        target_path = f"assets/players/player_{db_id}.png"

        downloaded = False
        # ลองเวอร์ชัน 25 ก่อน ถ้าไม่มีลอง 24 และ 23
        for ver in ['25_120.png', '24_120.png', '23_120.png', '25_60.png', '24_60.png']:
            url = f"https://cdn.sofifa.net/players/{part1}/{part2}/{ver}"
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=4) as response:
                    data = response.read()
                    if len(data) > 500:  # มีขนาดข้อมูลรูปภาพจริง
                        with open(target_path, "wb") as f:
                            f.write(data)
                        downloaded = True
                        break
            except Exception:
                pass

        if downloaded:
            success_count += 1
            print(f"✅ Player #{db_id} (SoFIFA {sofifa_id}) -> {target_path}")
        else:
            fail_count += 1
            print(f"⚠️ Player #{db_id} (SoFIFA {sofifa_id}) -> Failed")
        
        # หน่วงเวลาเล็กน้อยเพื่อป้องกัน rate limit
        time.sleep(0.05)

    print(f"\n🎉 ดาวน์โหลดสำเร็จ {success_count}/{len(PLAYER_SOFIFA_MAP)} คน (ล้มเหลว {fail_count})")

if __name__ == "__main__":
    download_all_players()
