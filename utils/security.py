import bcrypt

def hash_password(password: str) -> str:
    # เข้ารหัสผ่านด้วย bcrypt
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    # ตรวจสอบรหัสผ่าน
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))