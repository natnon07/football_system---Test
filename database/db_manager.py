import sqlite3
import os
from utils.security import hash_password

DB_NAME = "football_system.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME, timeout=60, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 60000")
    return conn

def log_audit(action, details, conn=None):
    """บันทึกประวัติการทำงานลงในตาราง audit_logs"""
    try:
        if conn is not None:
            conn.execute("INSERT INTO audit_logs (action, details) VALUES (?, ?)", (action, str(details)))
            return
        c = get_connection()
        c.execute("INSERT INTO audit_logs (action, details) VALUES (?, ?)", (action, str(details)))
        c.commit()
        c.close()
    except Exception as e:
        try:
            print(f"[Audit Log Warning]: {e}")
        except Exception:
            pass

def init_db():
    conn = get_connection()
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = -64000")
        conn.execute("PRAGMA temp_store = MEMORY")
    except Exception:
        pass
    cursor = conn.cursor()

    # 1. ตารางผู้ใช้งานระบบ
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('Admin', 'Agent', 'Club')),
            status TEXT DEFAULT 'Active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. ตารางข้อมูลเอเยนต์
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            first_name TEXT,
            last_name TEXT,
            agency_name TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # 3. ตารางข้อมูลสโมสร
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clubs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            club_name TEXT,
            budget REAL DEFAULT 100000000,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # 4. ตารางข้อมูลนักฟุตบอล
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id INTEGER,
            first_name TEXT,
            known_as TEXT,
            dob DATE,
            nationality TEXT,
            main_position TEXT,
            overall_rating INTEGER DEFAULT 75,
            potential INTEGER DEFAULT 80,
            estimated_value REAL DEFAULT 0,
            asking_price REAL DEFAULT 0,
            current_club TEXT DEFAULT 'Free Agent',
            status TEXT DEFAULT 'Approved',
            contract_details TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(agent_id) REFERENCES agents(id)
        )
    """)

    # 5. ตารางระบบซื้อขาย (รวมฟิลด์การจ่ายเงินและสัญญาครบถ้วน)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transfer_offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            club_id INTEGER,
            player_id INTEGER,
            agent_id INTEGER,
            offer_amount REAL DEFAULT 0,
            counter_amount REAL DEFAULT 0,
            wage_offer REAL DEFAULT 0,
            status TEXT DEFAULT 'Pending',
            contract_status TEXT DEFAULT 'Pending Price',
            contract_pdf TEXT DEFAULT NULL,
            fee_payment_method TEXT DEFAULT 'Online',
            fee_slip TEXT DEFAULT NULL,
            agent_payment_method TEXT DEFAULT 'Online',
            agent_slip TEXT DEFAULT NULL,
            rejection_reason TEXT DEFAULT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(club_id) REFERENCES clubs(id),
            FOREIGN KEY(player_id) REFERENCES players(id),
            FOREIGN KEY(agent_id) REFERENCES agents(id)
        )
    """)

    # Migration ตรวจสอบคอลัมน์เพิ่มเติมใน transfer_offers กรณีตารางเดิมยังไม่มี
    cursor.execute("PRAGMA table_info(transfer_offers)")
    existing_cols = [col[1] for col in cursor.fetchall()]
    new_cols = [
        ("wage_offer", "REAL DEFAULT 0"),
        ("contract_years", "INTEGER DEFAULT 4"),
        ("expires_at", " TEXT DEFAULT NULL"),
        ("contract_pdf", "TEXT DEFAULT NULL"),
        ("emp_contract_pdf", "TEXT DEFAULT NULL"),
        ("fee_payment_method", "TEXT DEFAULT 'Online'"),
        ("fee_slip", "TEXT DEFAULT NULL"),
        ("agent_payment_method", "TEXT DEFAULT 'Online'"),
        ("agent_slip", "TEXT DEFAULT NULL"),
        ("rejection_reason", "TEXT DEFAULT NULL"),
        ("selling_club", "TEXT DEFAULT NULL"),
        ("contact_email", "TEXT DEFAULT NULL")
    ]
    for col_name, col_def in new_cols:
        if col_name not in existing_cols:
            try:
                cursor.execute(f"ALTER TABLE transfer_offers ADD COLUMN {col_name} {col_def}")
            except Exception:
                pass

    # 5.1 ตารางประวัติการต่อรองราคาแต่ละรอบ (negotiations - ตามโครงสร้าง 7 ตารางหลัก)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS negotiations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            offer_id INTEGER NOT NULL,
            sender_role TEXT NOT NULL,
            counter_amount REAL DEFAULT 0,
            wage_offer REAL DEFAULT 0,
            contract_years INTEGER DEFAULT 4,
            message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(offer_id) REFERENCES transfer_offers(id) ON DELETE CASCADE
        )
    """)

    # 5.2 ตารางเงื่อนไขและผลการทำสัญญา (contracts - แยกการตกลงค่าตัวกับการยืนยันสัญญา)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            offer_id INTEGER UNIQUE NOT NULL,
            salary REAL DEFAULT 0,
            contract_years INTEGER DEFAULT 4,
            approval_status TEXT DEFAULT 'Contract Pending',
            completed_at DATETIME DEFAULT NULL,
            FOREIGN KEY(offer_id) REFERENCES transfer_offers(id) ON DELETE CASCADE
        )
    """)

    # 5.3 ตารางประวัติการย้ายสังกัดที่สำเร็จแล้ว (transfer_history)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transfer_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            offer_id INTEGER,
            player_id INTEGER,
            player_name TEXT,
            from_club TEXT,
            to_club TEXT,
            transfer_fee REAL DEFAULT 0,
            salary REAL DEFAULT 0,
            contract_years INTEGER DEFAULT 4,
            agent_id INTEGER DEFAULT 1,
            completed_by TEXT DEFAULT 'Admin',
            completed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Backfill selling_club & expires_at for existing transfer_offers if NULL
    try:
        cursor.execute("""
            UPDATE transfer_offers
            SET selling_club = (SELECT p.current_club FROM players p WHERE p.id = transfer_offers.player_id)
            WHERE selling_club IS NULL OR selling_club = ''
        """)
        cursor.execute("""
            UPDATE transfer_offers
            SET contact_email = (SELECT c.email FROM clubs c WHERE c.id = transfer_offers.club_id)
            WHERE contact_email IS NULL OR contact_email = ''
        """)
        cursor.execute("""
            UPDATE transfer_offers
            SET expires_at = date('now', '+14 days')
            WHERE expires_at IS NULL OR expires_at = ''
        """)
    except Exception:
        pass

    # Migration ตรวจสอบคอลัมน์เพิ่มเติมใน users (email)
    cursor.execute("PRAGMA table_info(users)")
    existing_user_cols = [col[1] for col in cursor.fetchall()]
    if "email" not in existing_user_cols:
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT DEFAULT NULL")
        except Exception:
            pass

    # Migration ตรวจสอบคอลัมน์เพิ่มเติมใน agents (full_name, contact, photo_path, email, phone, license_no, bio, country)
    cursor.execute("PRAGMA table_info(agents)")
    existing_agent_cols = [col[1] for col in cursor.fetchall()]
    for col_name, col_def in [
        ("full_name", "TEXT DEFAULT NULL"),
        ("contact", "TEXT DEFAULT 'agent@gestifute.com'"),
        ("photo_path", "TEXT DEFAULT NULL"),
        ("email", "TEXT DEFAULT NULL"),
        ("phone", "TEXT DEFAULT NULL"),
        ("license_no", "TEXT DEFAULT NULL"),
        ("bio", "TEXT DEFAULT NULL"),
        ("country", "TEXT DEFAULT 'International'")
    ]:
        if col_name not in existing_agent_cols:
            try:
                cursor.execute(f"ALTER TABLE agents ADD COLUMN {col_name} {col_def}")
            except Exception:
                pass
    try:
        cursor.execute("UPDATE agents SET full_name = TRIM(COALESCE(first_name,'') || ' ' || COALESCE(last_name,'')) WHERE full_name IS NULL OR full_name = ''")
    except Exception:
        pass

    # Migration ตรวจสอบคอลัมน์เพิ่มเติมใน clubs สำหรับการยืนยันสถานะการเงิน (Proof of Funds), league และ logo_path
    cursor.execute("PRAGMA table_info(clubs)")
    existing_club_cols = [col[1] for col in cursor.fetchall()]
    new_club_cols = [
        ("financial_doc", "TEXT DEFAULT NULL"),
        ("verification_status", "TEXT DEFAULT 'Approved'"),
        ("country", "TEXT DEFAULT 'International'"),
        ("league", "TEXT DEFAULT 'First Division'"),
        ("bank_name", "TEXT DEFAULT NULL"),
        ("submitted_budget", "REAL DEFAULT 0"),
        ("verified_at", "DATETIME DEFAULT NULL"),
        ("rejection_reason", "TEXT DEFAULT NULL"),
        ("email", "TEXT DEFAULT NULL"),
        ("logo_path", "TEXT DEFAULT NULL")
    ]
    for col_name, col_def in new_club_cols:
        if col_name not in existing_club_cols:
            try:
                cursor.execute(f"ALTER TABLE clubs ADD COLUMN {col_name} {col_def}")
            except Exception:
                pass

    # Migration ตรวจสอบคอลัมน์เพิ่มเติมใน players สำหรับ availability_status, current_club_id, image_path, image_path_2, video_path
    cursor.execute("PRAGMA table_info(players)")
    existing_player_cols = [col[1] for col in cursor.fetchall()]
    for p_col, p_def in [
        ("image_path", "TEXT DEFAULT NULL"),
        ("image_path_2", "TEXT DEFAULT NULL"),
        ("video_path", "TEXT DEFAULT NULL"),
        ("availability_status", "TEXT DEFAULT 'พร้อมย้ายทีม (Available)'"),
        ("current_club_id", "INTEGER DEFAULT NULL")
    ]:
        if p_col not in existing_player_cols:
            try:
                cursor.execute(f"ALTER TABLE players ADD COLUMN {p_col} {p_def}")
            except Exception:
                pass
    try:
        cursor.execute("UPDATE players SET agent_id = 1 WHERE agent_id IS NULL")
        cursor.execute("UPDATE players SET availability_status = 'พร้อมย้ายทีม (Available)' WHERE availability_status IS NULL OR availability_status = ''")
    except Exception:
        pass

    # ตารางการแจ้งเตือนอีเมล (Email Notifications)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_email TEXT NOT NULL,
            recipient_name TEXT,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            status TEXT DEFAULT 'Sent',
            email_type TEXT,
            sent_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # อัปเดตอีเมลเริ่มต้นสำหรับสโมสรที่มีอยู่แล้ว
    default_club_emails = {
        'Real Madrid': 'transfers@realmadrid.com',
        'Manchester City': 'finance@mancity.com',
        'FC Barcelona': 'office@fcbarcelona.cat',
        'Barcelona': 'office@fcbarcelona.cat',
        'Arsenal': 'transfers@arsenal.co.uk',
        'Liverpool': 'contact@liverpoolfc.com',
        'Global FC': 'contact@globalfc.com'
    }
    for c_name, c_em in default_club_emails.items():
        try:
            cursor.execute("UPDATE clubs SET email = ? WHERE club_name = ? AND (email IS NULL OR email = '')", (c_em, c_name))
        except Exception:
            pass

    # 6. ตาราง Audit Logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed ข้อมูลเริ่มต้นหากยังไม่มีข้อมูล
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        default_pwd = hash_password("password123")
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ('admin', default_pwd, 'Admin'))
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ('agent1', default_pwd, 'Agent'))
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ('club1', default_pwd, 'Club'))
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ('liverpool_club', default_pwd, 'Club'))
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ('mancity_club', default_pwd, 'Club'))

        cursor.execute("INSERT INTO agents (user_id, first_name, last_name, agency_name) VALUES (2, 'Jorge', 'Mendes', 'Gestifute Agency')")
        cursor.execute("INSERT INTO clubs (user_id, club_name, budget) VALUES (3, 'Global FC', 100000000)")
        cursor.execute("INSERT INTO clubs (user_id, club_name, budget) VALUES (4, 'Liverpool', 250000000)")
        cursor.execute("INSERT INTO clubs (user_id, club_name, budget) VALUES (5, 'Manchester City', 300000000)")

        cursor.execute("""
            INSERT INTO players (agent_id, first_name, known_as, dob, nationality, main_position, overall_rating, potential, estimated_value, current_club, status) 
            VALUES (1, 'Erling', 'Haaland', '2000-07-21', 'Norway', 'ST', 91, 94, 180000000, 'Manchester City', 'Approved')
        """)

    conn.commit()
    conn.close()

# สถานะข้อเสนอซื้อขายมาตรฐานทั้ง 9 สถานะ (Standard Offer Statuses)
OFFER_STATUS_MEANINGS = {
    "Pending": "รอเอเยนต์พิจารณา",
    "Negotiating": "อยู่ระหว่างเจรจาค่าตัว",
    "Accepted": "เอเยนต์ยอมรับข้อเสนอ แต่ยังไม่ปิดดีล",
    "Rejected": "ข้อเสนอถูกปฏิเสธ",
    "Contract Pending": "รอจัดทำหรือยืนยันสัญญา",
    "Pending Approval": "รอแอดมินตรวจสอบ",
    "Completed": "ซื้อขายสำเร็จและเปลี่ยนสังกัดแล้ว",
    "Cancelled": "ยกเลิกข้อเสนอ",
    "Expired": "ข้อเสนอหมดอายุ"
}


def create_transfer_offer(club_id, player_id, offer_amount, wage_offer=0, contract_years=4, expires_at=None, contact_email="", message="", notes="", actor_name="Club", **kwargs):
    """
    ขั้นตอนที่ 03: สโมสรส่งข้อเสนอซื้อ พร้อมตรวจสอบกฎการทำงาน (Business Rules 1, 2, 4, 8)
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        club = cursor.execute("SELECT id, club_name, budget, email FROM clubs WHERE id = ?", (club_id,)).fetchone()
        if not club:
            conn.close()
            return False, "ไม่พบข้อมูลสโมสรผู้ซื้อในระบบ"

        player = cursor.execute("SELECT * FROM players WHERE id = ?", (player_id,)).fetchone()
        if not player:
            conn.close()
            return False, "ไม่พบข้อมูลนักฟุตบอลในระบบ"

        buyer_name = (club["club_name"] or "").strip()
        seller_name = (player["current_club"] or "Free Agent").strip()
        player_name = player["known_as"] or player["first_name"]

        # กฎข้อที่ 1: สโมสรไม่สามารถซื้อนักเตะจากตัวเองได้
        if buyer_name.lower() == seller_name.lower():
            conn.close()
            return False, f"กฎระบบข้อที่ 1: สโมสร {buyer_name} ไม่สามารถยื่นซื้อนักเตะ ({player_name}) ที่อยู่ในสังกัดของตัวเองได้"

        # กฎข้อที่ 2: นักเตะต้องมีเอเยนต์ผู้ดูแลที่ถูกต้อง และต้องพร้อมรับข้อเสนอ
        agent_id = player["agent_id"] if ("agent_id" in player.keys() and player["agent_id"]) else 1
        avail = (player["availability_status"] if "availability_status" in player.keys() else "พร้อมย้ายทีม (Available)") or ""
        if "ไม่พร้อมย้ายทีม" in avail or avail == "Not Available":
            conn.close()
            return False, f"นักเตะ {player_name} ถูกตั้งสถานะเป็น 'ไม่พร้อมย้ายทีม (Not Available)' โดยเอเยนต์"

        # กฎข้อที่ 4: สโมสรต้องมีงบประมาณเพียงพอ
        offer_val = float(offer_amount or 0)
        if offer_val <= 0:
            conn.close()
            return False, "กรุณาระบุจำนวนเงินค่าตัวที่เสนอซื้อให้ถูกต้อง"

        if float(club["budget"] or 0) < offer_val:
            conn.close()
            return False, f"กฎระบบข้อที่ 4: งบประมาณของสโมสร {buyer_name} (€{club['budget']:,.0f}) ไม่เพียงพอสำหรับข้อเสนอ €{offer_val:,.0f}"

        if not expires_at:
            exp_row = cursor.execute("SELECT date('now', '+14 days') AS d").fetchone()
            expires_at = exp_row["d"]

        final_email = (contact_email or club["email"] or "transfers@club.com").strip()

        cursor.execute("""
            INSERT INTO transfer_offers (
                club_id, player_id, agent_id, offer_amount, counter_amount,
                wage_offer, contract_years, status, contract_status,
                expires_at, selling_club, contact_email
            ) VALUES (?, ?, ?, ?, 0, ?, ?, 'Pending', 'Pending Agent Review', ?, ?, ?)
        """, (club_id, player_id, agent_id, offer_val, float(wage_offer or 0), int(contract_years or 4), expires_at, seller_name, final_email))
        offer_id = cursor.lastrowid

        # บันทึกรอบแรกในตาราง negotiations
        init_msg = (notes or message or "").strip() or f"สโมสร {buyer_name} ยื่นข้อเสนอเริ่มต้นขอซื้อตัว {player_name}"
        cursor.execute("""
            INSERT INTO negotiations (offer_id, sender_role, counter_amount, wage_offer, contract_years, message)
            VALUES (?, 'Club', ?, ?, ?, ?)
        """, (offer_id, offer_val, float(wage_offer or 0), int(contract_years or 4), init_msg))

        # อัปเดตสถานะความพร้อมนักเตะเป็นกำลังเจรจา
        cursor.execute("UPDATE players SET availability_status = 'กำลังเจรจา (Negotiating)' WHERE id = ?", (player_id,))

        # กฎข้อที่ 8: บันทึกผู้ทำรายการและวันเวลาลงใน audit_logs
        cursor.execute("INSERT INTO audit_logs (action, details) VALUES (?, ?)", (
            "OFFER_CREATED",
            f"[{actor_name}] Club '{buyer_name}' submitted offer #{offer_id} for '{player_name}' (€{offer_val:,.0f}, wage €{float(wage_offer or 0):,.0f}/wk, {int(contract_years or 4)} yrs)"
        ))

        conn.commit()
        conn.close()
        return True, offer_id
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)


def negotiate_or_respond_offer(offer_id, sender_role="Club", action_type=None, counter_amount=None, wage_offer=None, contract_years=None, message="", actor_name="", notes="", action=None, proposed_fee=None, proposed_wage=None, proposed_years=None, actor_role=None, **kwargs):
    """
    ขั้นตอนที่ 04, 05, 06:
    - 'counter' -> สถานะ 'Negotiating' (ต่อรองราคาและบันทึกลงตาราง negotiations)
    - 'accept' -> สถานะ 'Accepted' (เอเยนต์/สโมสรยอมรับค่าตัว แต่ยังไม่เปลี่ยนสังกัดตามกฎข้อที่ 5)
    - 'contract_pending' -> สถานะ 'Contract Pending' (เข้าสู่ขั้นตอนจัดทำและยืนยันสัญญา)
    - 'confirm_contract' -> บันทึกตาราง contracts และเปลี่ยนสถานะเป็น 'Pending Approval' (รอแอดมินอนุมัติ)
    - 'reject' -> สถานะ 'Rejected'
    - 'cancel' -> สถานะ 'Cancelled'
    - 'expire' -> สถานะ 'Expired'
    """
    action_type = action_type or action or "counter"
    sender_role = actor_role or sender_role or "Club"
    counter_amount = counter_amount if counter_amount is not None else proposed_fee
    wage_offer = wage_offer if wage_offer is not None else proposed_wage
    contract_years = contract_years if contract_years is not None else proposed_years
    message = (notes or message or "").strip()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        offer = cursor.execute("""
            SELECT t.*, p.known_as AS player_name, c.club_name, c.budget
            FROM transfer_offers t
            JOIN players p ON t.player_id = p.id
            JOIN clubs c ON t.club_id = c.id
            WHERE t.id = ?
        """, (offer_id,)).fetchone()
        if not offer:
            conn.close()
            return False, "ไม่พบข้อเสนอซื้อขายนี้ในระบบ"

        if offer["status"] == "Completed":
            conn.close()
            return False, "ดีลนี้ปิดการซื้อขายเสร็จสมบูรณ์แล้ว ไม่สามารถแก้ไขได้"

        new_amount = float(counter_amount) if counter_amount is not None and float(counter_amount) > 0 else float(offer["offer_amount"] or 0)
        new_wage = float(wage_offer) if wage_offer is not None and float(wage_offer) > 0 else float(offer["wage_offer"] or 0)
        new_years = int(contract_years) if contract_years is not None and int(contract_years) > 0 else int(offer["contract_years"] if "contract_years" in offer.keys() and offer["contract_years"] else 4)
        actor_label = actor_name or sender_role

        if action_type == "counter":
            if sender_role == "Club" and float(offer["budget"] or 0) < new_amount:
                conn.close()
                return False, f"กฎระบบข้อที่ 4: งบประมาณสโมสรไม่เพียงพอสำหรับการยื่นราคาใหม่ (€{new_amount:,.0f})"

            new_status = "Negotiating"
            cursor.execute("""
                UPDATE transfer_offers
                SET offer_amount = ?, counter_amount = ?, wage_offer = ?, contract_years = ?,
                    status = 'Negotiating', contract_status = 'Price Negotiation'
                WHERE id = ?
            """, (new_amount, new_amount, new_wage, new_years, offer_id))

            note = message.strip() if message else f"{sender_role} เสนอต่อรองค่าตัวใหม่เป็น €{new_amount:,.0f} (ค่าเหนื่อย €{new_wage:,.0f}/สัปดาห์, สัญญา {new_years} ปี)"
            cursor.execute("""
                INSERT INTO negotiations (offer_id, sender_role, counter_amount, wage_offer, contract_years, message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (offer_id, sender_role, new_amount, new_wage, new_years, note))

        elif action_type == "accept":
            # กฎข้อที่ 5: การตอบรับข้อเสนอไม่ทำให้สังกัดนักเตะเปลี่ยนทันที (เปลี่ยนเป็น Accepted และสร้างร่างสัญญา)
            new_status = "Accepted"
            cursor.execute("""
                UPDATE transfer_offers
                SET offer_amount = ?, wage_offer = ?, contract_years = ?,
                    status = 'Accepted', contract_status = 'Accepted - Awaiting Contract'
                WHERE id = ?
            """, (new_amount, new_wage, new_years, offer_id))

            note = message.strip() if message else f"{sender_role} ตอบรับข้อเสนอค่าตัว €{new_amount:,.0f} (รอการยืนยันเงื่อนไขสัญญา)"
            cursor.execute("""
                INSERT INTO negotiations (offer_id, sender_role, counter_amount, wage_offer, contract_years, message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (offer_id, sender_role, new_amount, new_wage, new_years, note))

            cursor.execute("""
                INSERT INTO contracts (offer_id, salary, contract_years, approval_status)
                VALUES (?, ?, ?, 'Contract Pending')
                ON CONFLICT(offer_id) DO UPDATE SET
                    salary = excluded.salary,
                    contract_years = excluded.contract_years,
                    approval_status = 'Contract Pending'
            """, (offer_id, new_wage, new_years))

        elif action_type == "contract_pending":
            new_status = "Contract Pending"
            cursor.execute("""
                UPDATE transfer_offers
                SET wage_offer = ?, contract_years = ?, status = 'Contract Pending', contract_status = 'Contract Pending'
                WHERE id = ?
            """, (new_wage, new_years, offer_id))
            cursor.execute("""
                INSERT INTO contracts (offer_id, salary, contract_years, approval_status)
                VALUES (?, ?, ?, 'Contract Pending')
                ON CONFLICT(offer_id) DO UPDATE SET
                    salary = excluded.salary,
                    contract_years = excluded.contract_years,
                    approval_status = 'Contract Pending'
            """, (offer_id, new_wage, new_years))

        elif action_type in ("confirm_contract", "pending_approval"):
            # ยืนยันเงื่อนไขสัญญาและส่งให้ Admin ตรวจสอบอนุมัติ (ขั้นตอนที่ 06)
            new_status = "Pending Approval"
            cursor.execute("""
                UPDATE transfer_offers
                SET offer_amount = ?, wage_offer = ?, contract_years = ?,
                    status = 'Pending Approval', contract_status = 'Pending Admin Approval'
                WHERE id = ?
            """, (new_amount, new_wage, new_years, offer_id))

            cursor.execute("""
                INSERT INTO contracts (offer_id, salary, contract_years, approval_status)
                VALUES (?, ?, ?, 'Pending Approval')
                ON CONFLICT(offer_id) DO UPDATE SET
                    salary = excluded.salary,
                    contract_years = excluded.contract_years,
                    approval_status = 'Pending Approval'
            """, (offer_id, new_wage, new_years))

            note = message.strip() if message else f"{sender_role} ยืนยันเงื่อนไขสัญญาเรียบร้อยแล้ว ส่งต่อให้ Admin ตรวจสอบอนุมัติดีล"
            cursor.execute("""
                INSERT INTO negotiations (offer_id, sender_role, counter_amount, wage_offer, contract_years, message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (offer_id, sender_role, new_amount, new_wage, new_years, note))

        elif action_type in ("reject", "Rejected"):
            new_status = "Rejected"
            cursor.execute("UPDATE transfer_offers SET status = 'Rejected', contract_status = 'Rejected', rejection_reason = ? WHERE id = ?", (message or "Rejected", offer_id))
            cursor.execute("UPDATE players SET availability_status = 'พร้อมย้ายทีม (Available)' WHERE id = ?", (offer["player_id"],))
            cursor.execute("""
                INSERT INTO negotiations (offer_id, sender_role, counter_amount, wage_offer, contract_years, message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (offer_id, sender_role, new_amount, new_wage, new_years, message or f"{sender_role} ปฏิเสธข้อเสนอ"))

        elif action_type in ("cancel", "Cancelled"):
            new_status = "Cancelled"
            cursor.execute("UPDATE transfer_offers SET status = 'Cancelled', contract_status = 'Cancelled' WHERE id = ?", (offer_id,))
            cursor.execute("UPDATE players SET availability_status = 'พร้อมย้ายทีม (Available)' WHERE id = ?", (offer["player_id"],))
            cursor.execute("""
                INSERT INTO negotiations (offer_id, sender_role, counter_amount, wage_offer, contract_years, message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (offer_id, sender_role, new_amount, new_wage, new_years, message or f"{sender_role} ยกเลิกข้อเสนอ"))

        elif action_type in ("expire", "Expired"):
            new_status = "Expired"
            cursor.execute("UPDATE transfer_offers SET status = 'Expired', contract_status = 'Expired' WHERE id = ?", (offer_id,))
        else:
            new_status = action_type
            cursor.execute("UPDATE transfer_offers SET status = ? WHERE id = ?", (new_status, offer_id))

        # กฎข้อที่ 8: บันทึก Audit Log
        cursor.execute("INSERT INTO audit_logs (action, details) VALUES (?, ?)", (
            f"OFFER_{new_status.upper().replace(' ', '_')}",
            f"[{actor_label}] Offer #{offer_id} ({offer['player_name']}) -> {new_status} (€{new_amount:,.0f})"
        ))

        conn.commit()
        conn.close()
        return True, f"อัปเดตสถานะข้อเสนอเป็น '{new_status}' ({OFFER_STATUS_MEANINGS.get(new_status, new_status)}) สำเร็จ"
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)


def complete_transfer_deal(offer_id, completed_by="Admin"):
    """
    ขั้นตอนที่ 07: ปิดการซื้อขายแบบ Atomic Transaction (กฎการทำงานข้อที่ 4, 6, 7, 8):
    - ตรวจสอบงบประมาณสโมสรผู้ซื้อ (Rule 4)
    - ป้องกันการย้ายสังกัดซ้ำซ้อนของนักเตะคนเดียวกัน (Rule 7: ยกเลิกข้อเสนออื่นที่ค้างอยู่ของนักเตะคนนี้โดยอัตโนมัติ)
    - ปรับสถานะ offer เป็น 'Completed' และอนุมัติสัญญาในตาราง contracts
    - ย้ายนักเตะไปยังสังกัดสโมสรผู้ซื้อ และตั้งสถานะความพร้อม
    - ตัดงบประมาณสโมสรผู้ซื้อ และเพิ่มงบประมาณให้กับสโมสรผู้ขาย
    - บันทึกประวัติลงตาราง transfer_history และ audit_logs ในธุรกรรมฐานข้อมูลเดียวกัน (Rule 6 & Rule 8)
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT t.*, p.known_as, p.first_name, p.current_club as seller_club_name,
                   c.club_name as buyer_club_name, c.budget as buyer_budget
            FROM transfer_offers t
            JOIN players p ON t.player_id = p.id
            JOIN clubs c ON t.club_id = c.id
            WHERE t.id = ?
        """, (offer_id,))
        deal = cursor.fetchone()
        if not deal:
            conn.close()
            return False, "ไม่พบข้อเสนอซื้อขายนี้ในระบบ"

        if deal["status"] == "Completed":
            conn.close()
            return False, "ข้อเสนอนี้ถูกปิดดีลและย้ายสังกัดเรียบร้อยแล้ว"

        buyer_club_id = deal['club_id']
        seller_club_name = deal['selling_club'] if ('selling_club' in deal.keys() and deal['selling_club']) else deal['seller_club_name']
        buyer_club_name = deal['buyer_club_name']
        player_id = deal['player_id']
        player_name = deal['known_as'] or deal['first_name']
        amount = float(deal['offer_amount'] or 0)
        wage = float(deal['wage_offer'] if 'wage_offer' in deal.keys() and deal['wage_offer'] else 0)
        c_years = int(deal['contract_years'] if 'contract_years' in deal.keys() and deal['contract_years'] else 4)
        contact_em = deal['contact_email'] if ('contact_email' in deal.keys() and deal['contact_email']) else ''

        # กฎข้อที่ 1 & 7: ป้องกันสโมสรซื้อนักเตะตัวเอง หรือนักเตะเพิ่งถูกย้ายสังกัดไปแล้ว
        if (deal['seller_club_name'] or "").strip().lower() == (buyer_club_name or "").strip().lower():
            conn.close()
            return False, f"นักเตะ {player_name} อยู่ในสังกัดสโมสร {buyer_club_name} อยู่แล้ว"

        # กฎข้อที่ 4: ตรวจสอบงบประมาณของสโมสรผู้ซื้อก่อนปิดดีล
        if float(deal['buyer_budget'] or 0) < amount:
            conn.close()
            return False, f"กฎระบบข้อที่ 4: งบประมาณของ {buyer_club_name} (€{deal['buyer_budget']:,.0f}) ไม่เพียงพอสำหรับปิดดีล €{amount:,.0f}"

        # 1. ปรับสถานะ offer เป็น Completed และบันทึกสโมสรผู้ขายเดิม
        cursor.execute(
            "UPDATE transfer_offers SET status = 'Completed', contract_status = 'Signed & Transferred', selling_club = ? WHERE id = ?",
            (seller_club_name, offer_id)
        )

        # 2. กฎข้อที่ 7: ยกเลิกข้อเสนออื่น ๆ ที่ยังค้างอยู่ของนักเตะคนเดียวกัน เพื่อไม่ให้เกิดการย้ายสังกัดซ้ำซ้อน
        cursor.execute("""
            UPDATE transfer_offers
            SET status = 'Cancelled', contract_status = 'Cancelled (Player Transferred)',
                rejection_reason = 'ยกเลิกอัตโนมัติเนื่องจากนักเตะย้ายสังกัดในดีลอื่นแล้ว'
            WHERE player_id = ? AND id != ? AND status NOT IN ('Completed', 'Rejected', 'Cancelled', 'Expired')
        """, (player_id, offer_id))

        # 3. อัปเดตตาราง contracts เป็น Approved พร้อมเวลาที่ปิดดีล
        cursor.execute("""
            INSERT INTO contracts (offer_id, salary, contract_years, approval_status, completed_at)
            VALUES (?, ?, ?, 'Approved', CURRENT_TIMESTAMP)
            ON CONFLICT(offer_id) DO UPDATE SET
                salary = excluded.salary,
                contract_years = excluded.contract_years,
                approval_status = 'Approved',
                completed_at = CURRENT_TIMESTAMP
        """, (offer_id, wage, c_years))

        # 4. ปรับสโมสรปัจจุบันของนักเตะและสถานะความพร้อม
        cursor.execute(
            "UPDATE players SET current_club = ?, current_club_id = ?, availability_status = 'พร้อมย้ายทีม (Available)' WHERE id = ?",
            (buyer_club_name, buyer_club_id, player_id)
        )

        # 5. ตัดงบประมาณสโมสรผู้ซื้อ และเพิ่มงบให้สโมสรผู้ขาย
        cursor.execute("UPDATE clubs SET budget = MAX(0, budget - ?) WHERE id = ?", (amount, buyer_club_id))
        if seller_club_name and seller_club_name != 'Free Agent':
            cursor.execute("UPDATE clubs SET budget = budget + ? WHERE club_name = ?", (amount, seller_club_name))

        # 6. กฎข้อที่ 6: บันทึกประวัติลงตาราง transfer_history ในธุรกรรมเดียวกัน
        cursor.execute("""
            INSERT INTO transfer_history (
                offer_id, player_id, player_name, from_club, to_club,
                transfer_fee, salary, contract_years, agent_id, completed_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (offer_id, player_id, player_name, seller_club_name, buyer_club_name, amount, wage, c_years, deal['agent_id'] or 1, completed_by))

        # 7. กฎข้อที่ 8: บันทึกประวัติ Audit Log พร้อมผู้ทำรายการ
        cursor.execute("INSERT INTO audit_logs (action, details) VALUES (?, ?)", (
            "TRANSFER_COMPLETED",
            f"[{completed_by}] Completed Offer #{offer_id}: {player_name} transferred from {seller_club_name} to {buyer_club_name} for €{amount:,.0f}"
        ))

        conn.commit()
        conn.close()

        # 8. ส่งอีเมลแจ้งเตือนผลการปิดดีลไปยังอีเมลจริงที่ระบุ (Non-blocking Background Thread)
        if contact_em:
            try:
                import threading
                from utils.email_service import send_transfer_offer_email
                threading.Thread(
                    target=send_transfer_offer_email,
                    kwargs={
                        "club_name": buyer_club_name,
                        "selling_club": seller_club_name or "Free Agent",
                        "player_name": player_name,
                        "offer_amount": amount,
                        "wage_offer": wage,
                        "status": "Completed",
                        "recipient_emails": contact_em
                    },
                    daemon=True
                ).start()
            except Exception:
                pass

        return True, f"ปิดดีลสำเร็จ! {player_name} ย้ายจาก {seller_club_name} เข้าสู่สโมสร {buyer_club_name} เรียบร้อยแล้ว"
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)