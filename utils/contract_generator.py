import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

CONTRACTS_DIR = os.path.join("assets", "contracts")

# ตรวจสอบและลงทะเบียนฟอนต์ภาษาไทย Tahoma หรือ Leelawadee
_thai_font_registered = False

def _register_thai_fonts():
    global _thai_font_registered
    if _thai_font_registered:
        return "Tahoma", "Tahoma-Bold"

    font_dir = r"C:\Windows\Fonts"
    regular_name = "Helvetica"
    bold_name = "Helvetica-Bold"

    # ลองค้นหา Tahoma หรือ Leelawadee บน Windows
    candidates = [
        ("Tahoma", os.path.join(font_dir, "tahoma.ttf"), "Tahoma-Bold", os.path.join(font_dir, "tahomabd.ttf")),
        ("Leelawadee", os.path.join(font_dir, "leelawad.ttf"), "Leelawadee-Bold", os.path.join(font_dir, "leelawdb.ttf"))
    ]

    for reg_alias, reg_path, bld_alias, bld_path in candidates:
        if os.path.exists(reg_path) and os.path.exists(bld_path):
            try:
                pdfmetrics.registerFont(TTFont(reg_alias, reg_path))
                pdfmetrics.registerFont(TTFont(bld_alias, bld_path))
                regular_name = reg_alias
                bold_name = bld_alias
                _thai_font_registered = True
                break
            except Exception:
                pass

    return regular_name, bold_name

def generate_transfer_agreement_pdf(
    offer_id,
    buyer_club_name,
    seller_club_name,
    player_name,
    player_nationality="International",
    player_dob="15/06/1998",
    transfer_fee=50000000.0,
    date_str=None,
    place_str=None
):
    """
    สร้างเอกสาร PDF: สัญญาโอนสิทธิการเล่นนักฟุตบอลระหว่างสโมสร (Transfer Agreement)
    ตรงตามแบบเอกสารสัญญาทางการระหว่างสโมสรผู้ซื้อและผู้ขาย
    """
    os.makedirs(CONTRACTS_DIR, exist_ok=True)
    pdf_path = os.path.join(CONTRACTS_DIR, f"transfer_agreement_{offer_id}.pdf")

    try:
        transfer_fee = float(transfer_fee or 0)
    except Exception:
        transfer_fee = 0.0

    font_reg, font_bld = _register_thai_fonts()

    today = date_str or datetime.date.today().strftime("%d/%m/%Y")
    place = place_str or f"สำนักงานใหญ่สโมสร {seller_club_name}"
    
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4 # 595.27 x 841.89

    # ==================== PAGE 1 ====================
    # Header Decorative Accent
    c.setFillColor(colors.HexColor("#0F2756"))
    c.rect(0, height - 12, width, 12, fill=True, stroke=False)
    c.setFillColor(colors.HexColor("#185ADB"))
    c.rect(0, height - 16, width, 4, fill=True, stroke=False)

    # Document Title
    c.setFont(font_bld, 16)
    c.setFillColor(colors.HexColor("#0B132B"))
    title_text = "สัญญาโอนสิทธิการเล่นนักฟุตบอลระหว่างสโมสร (Transfer Agreement)"
    c.drawCentredString(width / 2.0, height - 52, title_text)

    # Place & Date Row
    c.setFont(font_reg, 10.5)
    c.setFillColor(colors.HexColor("#334155"))
    c.drawString(60, height - 80, f"ทำที่:  {place}")
    c.drawString(60, height - 98, f"วันที่:  {today}")

    # Intro Section
    c.drawString(60, height - 126, "สัญญานี้ทำขึ้นระหว่าง:")
    
    c.setFont(font_bld, 10.5)
    c.drawString(75, height - 146, f"1. {seller_club_name}")
    c.setFont(font_reg, 10.5)
    c.drawString(75 + c.stringWidth(f"1. {seller_club_name} ", font_bld, 10.5), height - 146, 'ตั้งอยู่ ณ ประเทศต้นทาง ซึ่งต่อไปในสัญญานี้จะเรียกว่า "สโมสรเดิม"')

    c.setFont(font_bld, 10.5)
    c.drawString(75, height - 166, f"2. {buyer_club_name}")
    c.setFont(font_reg, 10.5)
    c.drawString(75 + c.stringWidth(f"2. {buyer_club_name} ", font_bld, 10.5), height - 166, 'ตั้งอยู่ ณ ประเทศปลายทาง ซึ่งต่อไปในสัญญานี้จะเรียกว่า "สโมสรใหม่"')

    y = height - 200

    # Section 1
    c.setFont(font_bld, 11)
    c.setFillColor(colors.HexColor("#0B132B"))
    c.drawString(60, y, "ข้อ 1. วัตถุประสงค์แห่งสัญญา")
    y -= 18
    c.setFont(font_reg, 10)
    c.setFillColor(colors.HexColor("#1E293B"))
    clause1 = (
        f'สโมสรเดิมตกลงโอนสิทธิการเล่นและทะเบียนของนักฟุตบอลชื่อ "{player_name}" สัญชาติ {player_nationality} '
        f'เกิดวันที่ {player_dob} (ต่อไปนี้เรียกว่า "นักฟุตบอล") ให้แก่สโมสรใหม่ และสโมสรใหม่ตกลงรับโอนสิทธิดังกล่าว'
    )
    c.drawString(60, y, clause1)

    y -= 32
    # Section 2
    c.setFont(font_bld, 11)
    c.setFillColor(colors.HexColor("#0B132B"))
    c.drawString(60, y, "ข้อ 2. ค่าธรรมเนียมการโอน (Transfer Fee)")
    y -= 18
    c.setFont(font_reg, 10)
    c.setFillColor(colors.HexColor("#1E293B"))
    
    fee_fmt = f"€{transfer_fee:,.2f}"
    fee_inst1 = f"€{transfer_fee * 0.70:,.2f}"
    fee_inst2 = f"€{transfer_fee * 0.30:,.2f}"

    c.drawString(60, y, f"สโมสรใหม่ตกลงจ่ายค่าธรรมเนียมการโอนสิทธิการเล่นของนักฟุตบอลให้แก่สโมสรเดิม เป็นจำนวนเงินทั้งสิ้น {fee_fmt} ยูโร (EUR)")
    y -= 16
    c.drawString(60, y, "โดยมีกำหนดชำระดังนี้:")
    y -= 18
    c.drawString(85, y, f"● งวดที่ 1: ชำระจำนวน {fee_inst1} (70%) ภายในวันที่ {today}")
    y -= 16
    future_date = (datetime.date.today() + datetime.timedelta(days=180)).strftime("%d/%m/%Y")
    c.drawString(85, y, f"● งวดที่ 2: ชำระจำนวน {fee_inst2} (30%) ภายในวันที่ {future_date}")

    y -= 32
    # Section 3
    c.setFont(font_bld, 11)
    c.setFillColor(colors.HexColor("#0B132B"))
    c.drawString(60, y, "ข้อ 3. เงื่อนไขเพิ่มเติม (Add-ons & Sell-on Clause)")
    y -= 18
    c.setFont(font_reg, 10)
    c.setFillColor(colors.HexColor("#1E293B"))
    c.drawString(60, y, "3.1 หากสโมสรใหม่ได้โอนสิทธิการเล่นของนักฟุตบอลให้แก่สโมสรอื่นในอนาคต สโมสรใหม่ตกลงจ่ายส่วนแบ่งกำไรจากการขาย (Sell-on fee)")
    y -= 15
    c.drawString(82, y, "จำนวน 15% ของส่วนต่างค่าตัวที่ได้รับ ให้แก่สโมสรเดิม")
    y -= 18
    addon_fmt = f"€{transfer_fee * 0.10:,.2f}"
    c.drawString(60, y, f"3.2 โบนัสตามผลงาน: สโมสรใหม่จะจ่ายเงินเพิ่มจำนวน {addon_fmt} หากสโมสรใหม่ผ่านเข้ารอบ ยูฟ่า แชมเปียนส์ลีก ในช่วงที่สัญญาบังคับใช้")

    y -= 32
    # Section 4
    c.setFont(font_bld, 11)
    c.setFillColor(colors.HexColor("#0B132B"))
    c.drawString(60, y, "ข้อ 4. การโอนทะเบียน (International Transfer Certificate - ITC)")
    y -= 18
    c.setFont(font_reg, 10)
    c.setFillColor(colors.HexColor("#1E293B"))
    c.drawString(60, y, "สโมสรเดิมจะดำเนินการขอใบอนุญาตโอนย้ายระหว่างประเทศ (ITC) ผ่านระบบ TMS ของ FIFA และสมาคมฟุตบอลแห่งประเทศ")
    y -= 15
    c.drawString(60, y, "ทันทีที่การตรวจร่างกายของนักฟุตบอลเสร็จสิ้นและสัญญาส่วนตัวของนักฟุตบอลกับสโมสรใหม่มีผลบังคับใช้ตามกฎระเบียบของฟีฟ่า")

    y -= 60
    # Signature Section
    c.setFont(font_reg, 10)
    c.drawString(70, y, "ลงชื่อ ....................................................... สโมสรเดิม")
    c.drawString(330, y, "ลงชื่อ ....................................................... สโมสรใหม่")
    y -= 18
    c.setFont(font_bld, 10)
    c.drawString(100, y, f"( ผู้แทนสโมสร {seller_club_name} )")
    c.drawString(360, y, f"( ผู้แทนสโมสร {buyer_club_name} )")
    y -= 16
    c.setFont(font_reg, 9)
    c.setFillColor(colors.HexColor("#64748B"))
    c.drawString(85, y, "ตำแหน่ง: ประธานสโมสร / ผู้อำนวยการกีฬา")
    c.drawString(345, y, "ตำแหน่ง: ประธานสโมสร / ผู้อำนวยการกีฬา")

    # Footer note
    c.setFont(font_reg, 8)
    c.setFillColor(colors.HexColor("#94A3B8"))
    c.drawCentredString(width / 2.0, 30, f"Football Transfer System • Official Transfer Agreement Deal Ref #{offer_id} • Page 1 of 1")

    c.showPage()
    c.save()
    return pdf_path

def generate_player_employment_contract_pdf(
    offer_id,
    club_name,
    player_name,
    weekly_wage=150000.0,
    passport_no=None,
    contract_years=4,
    agent_name="Player Representative",
    date_str=None
):
    """
    สร้างเอกสาร PDF: สัญญาจ้างนักฟุตบอลอาชีพ (ตกลงค่าเหนื่อย/สัญญาส่วนตัว)
    ตรงตามแบบเอกสารสัญญาจ้างนักเตะและข้อตกลงค่าเหนื่อยส่วนตัว
    """
    os.makedirs(CONTRACTS_DIR, exist_ok=True)
    pdf_path = os.path.join(CONTRACTS_DIR, f"employment_contract_{offer_id}.pdf")

    try:
        weekly_wage = float(weekly_wage or 0)
    except Exception:
        weekly_wage = 150000.0

    try:
        contract_years = int(contract_years or 4)
    except Exception:
        contract_years = 4

    font_reg, font_bld = _register_thai_fonts()

    today = date_str or datetime.date.today().strftime("%d/%m/%Y")
    end_date = (datetime.date.today() + datetime.timedelta(days=contract_years * 365)).strftime("%d/%m/%Y")
    pass_no = passport_no or f"P-{(abs(hash(player_name)) % 9000000) + 1000000}"

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    # Decorative Top Bar
    c.setFillColor(colors.HexColor("#065F46"))
    c.rect(0, height - 12, width, 12, fill=True, stroke=False)
    c.setFillColor(colors.HexColor("#10B981"))
    c.rect(0, height - 16, width, 4, fill=True, stroke=False)

    # Document Title
    c.setFont(font_bld, 16)
    c.setFillColor(colors.HexColor("#064E3B"))
    c.drawCentredString(width / 2.0, height - 50, "สัญญาจ้างนักฟุตบอลอาชีพ (ตกลงค่าเหนื่อย/สัญญาส่วนตัว)")

    # Metadata
    c.setFont(font_reg, 10.5)
    c.setFillColor(colors.HexColor("#334155"))
    c.drawString(60, height - 78, f"ทำที่:  สำนักงานสโมสร {club_name}")
    c.drawString(60, height - 96, f"วันที่:  {today}")

    c.drawString(60, height - 122, "สัญญานี้ทำขึ้นระหว่าง:")
    c.setFont(font_bld, 10.5)
    c.drawString(75, height - 142, f"1. สโมสร {club_name}")
    c.setFont(font_reg, 10.5)
    c.drawString(75 + c.stringWidth(f"1. สโมสร {club_name} ", font_bld, 10.5), height - 142, '(ต่อไปในสัญญานี้จะเรียกว่า "สโมสร")')

    c.setFont(font_bld, 10.5)
    c.drawString(75, height - 162, f"2. {player_name}")
    c.setFont(font_reg, 10.5)
    c.drawString(75 + c.stringWidth(f"2. {player_name} ", font_bld, 10.5), height - 162, f'ถือหนังสือเดินทางเลขที่ {pass_no} (ต่อไปในสัญญานี้จะเรียกว่า "นักฟุตบอล")')

    y = height - 196

    # Clause 1
    c.setFont(font_bld, 11)
    c.setFillColor(colors.HexColor("#0B132B"))
    c.drawString(60, y, "ข้อ 1. ระยะเวลาของสัญญา")
    y -= 18
    c.setFont(font_reg, 10)
    c.setFillColor(colors.HexColor("#1E293B"))
    c.drawString(60, y, f"สัญญาฉบับนี้มีผลบังคับใช้ตั้งแต่วันที่ {today} และสิ้นสุดในวันที่ {end_date} (รวมระยะเวลา {contract_years} ปี)")

    y -= 30
    # Clause 2
    c.setFont(font_bld, 11)
    c.setFillColor(colors.HexColor("#0B132B"))
    c.drawString(60, y, "ข้อ 2. ค่าตอบแทนและเงินเดือน (Remuneration & Basic Wage)")
    y -= 18
    c.setFont(font_reg, 10)
    c.setFillColor(colors.HexColor("#1E293B"))
    wage_fmt = f"€{weekly_wage:,.2f}"
    c.drawString(60, y, f"สโมสรตกลงจ่ายค่าจ้างพื้นฐานให้แก่นักฟุตบอลในอัตรา {wage_fmt} ยูโร (EUR) ต่อสัปดาห์ ก่อนหักภาษี ณ ที่จ่าย")
    y -= 16
    c.drawString(60, y, "โดยจะคำนวณและจ่ายเป็นรายเดือน ทุกวันทำการสุดท้ายของเดือน เข้าบัญชีธนาคารของนักฟุตบอลโดยตรง")

    y -= 30
    # Clause 3
    c.setFont(font_bld, 11)
    c.setFillColor(colors.HexColor("#0B132B"))
    c.drawString(60, y, "ข้อ 3. เงินโบนัสและสิทธิประโยชน์เพิ่มเติม (Bonuses & Benefits)")
    y -= 18
    c.setFont(font_reg, 10)
    c.setFillColor(colors.HexColor("#1E293B"))
    c.drawString(60, y, "สโมสรตกลงจ่ายเงินโบนัสให้แก่นักฟุตบอลตามเงื่อนไขดังต่อไปนี้:")
    y -= 17
    sign_on = f"€{weekly_wage * 8:,.0f}"
    app_fee = f"€{weekly_wage * 0.15:,.0f}"
    goal_bonus = f"€{weekly_wage * 0.10:,.0f}"
    loyalty = f"€{weekly_wage * 4:,.0f}"
    c.drawString(80, y, f"● ค่าเซ็นสัญญา (Signing-on Fee): จำนวน {sign_on} จ่ายงวดเดียวในวันที่สัญญาเริ่มบังคับใช้")
    y -= 16
    c.drawString(80, y, f"● ค่าลงสนาม (Appearance Fee): จำนวน {app_fee} ต่อการลงเล่นตัวจริง และ 50% ในฐานะตัวสำรอง")
    y -= 16
    c.drawString(80, y, f"● โบนัสทำประตู/แอสซิสต์ (Goal/Assist Bonus): จำนวน {goal_bonus} ต่อ 1 ประตูหรือ 1 แอสซิสต์ในนัดทางการ")
    y -= 16
    c.drawString(80, y, f"● โบนัสความภักดี (Loyalty Bonus): จำนวน {loyalty} จ่ายเมื่อนักฟุตบอลอยู่รับใช้สโมสรจนครบกำหนดวันที่ {end_date}")
    y -= 16
    c.drawString(80, y, "● สวัสดิการอื่น ๆ: สโมสรจัดหาที่พัก, รถยนต์ประจำตำแหน่ง, และตั๋วเครื่องบินไป-กลับประเทศบ้านเกิด 4 เที่ยวต่อปี")

    y -= 30
    # Clause 4
    c.setFont(font_bld, 11)
    c.setFillColor(colors.HexColor("#0B132B"))
    c.drawString(60, y, "ข้อ 4. หน้าที่ของนักฟุตบอล")
    y -= 18
    c.setFont(font_reg, 10)
    c.setFillColor(colors.HexColor("#1E293B"))
    c.drawString(60, y, "4.1 นักฟุตบอลต้องเข้าร่วมการฝึกซ้อม การแข่งขัน และกิจกรรมประชาสัมพันธ์ตามที่สโมสรกำหนดอย่างเคร่งครัด")
    y -= 15
    c.drawString(60, y, "4.2 นักฟุตบอลต้องรักษาสภาพร่างกายให้อยู่ในมาตรฐานระดับสูง และห้ามเข้าร่วมกิจกรรมเสี่ยงอันตรายต่ออาชีพนักฟุตบอล")

    y -= 30
    # Clause 5
    c.setFont(font_bld, 11)
    c.setFillColor(colors.HexColor("#0B132B"))
    c.drawString(60, y, "ข้อ 5. การยกเลิกสัญญา")
    y -= 18
    c.setFont(font_reg, 10)
    c.setFillColor(colors.HexColor("#1E293B"))
    c.drawString(60, y, "การยกเลิกสัญญาก่อนกำหนดสามารถทำได้โดยความยินยอมของทั้งสองฝ่าย หรือกรณีผิดสัญญาอย่างร้ายแรงตามกฎ FIFA")

    y -= 52
    # Signatures
    c.setFont(font_reg, 9.5)
    c.drawString(60, y, "ลงชื่อ ............................................... สโมสร")
    c.drawString(320, y, "ลงชื่อ ............................................... นักฟุตบอล")
    y -= 16
    c.setFont(font_bld, 9.5)
    c.drawString(85, y, f"( ประธานสโมสร {club_name} )")
    c.drawString(345, y, f"( {player_name} )")

    y -= 34
    c.setFont(font_reg, 9.5)
    c.drawString(190, y, "ลงชื่อ ............................................... พยาน / เอเยนต์นักฟุตบอล")
    y -= 16
    c.setFont(font_bld, 9.5)
    c.drawString(225, y, f"( {agent_name} )")

    # Footer note
    c.setFont(font_reg, 8)
    c.setFillColor(colors.HexColor("#94A3B8"))
    c.drawCentredString(width / 2.0, 26, f"Football Transfer System • Official Professional Player Contract Deal #{offer_id} • Page 1 of 1")

    c.showPage()
    c.save()
    return pdf_path
