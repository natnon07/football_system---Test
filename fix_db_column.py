import sqlite3

def add_current_club_column():
    conn = sqlite3.connect("football_system.db")
    cursor = conn.cursor()
    
    try:
        # ตรวจสอบและเพิ่มคอลัมน์ current_club ในตาราง players
        cursor.execute("PRAGMA table_info(players)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "current_club" not in columns:
            cursor.execute("ALTER TABLE players ADD COLUMN current_club TEXT DEFAULT 'Free Agent'")
            conn.commit()
            print("✅ เพิ่มคอลัมน์ current_club สำเร็จเรียบร้อยแล้ว!")
        else:
            print("ℹ️ คอลัมน์ current_club มีอยู่แล้วในฐานข้อมูล")
            
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_current_club_column()