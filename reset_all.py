import os
import sqlite3

# List ของไฟล์ DB ที่อาจจะค้างอยู่
db_files = ["football_system.db", "database/football_system.db"]

for db in db_files:
    if os.path.exists(db):
        try:
            os.remove(db)
            print(f"🗑️ ลบไฟล์ {db} สำเร็จเรียบร้อย!")
        except Exception as e:
            print(f"❌ ไม่สามารถลบ {db} ได้ (อาจเปิดโปรแกรมค้างไว้): {e}")

print("✨ พร้อมสร้างและ Seed ฐานข้อมูลใหม่แล้ว!")