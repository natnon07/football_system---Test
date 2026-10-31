import customtkinter as ctk
from database.db_manager import init_db
from ui.login_ui import LoginFrame
from ui.admin_ui import AdminFrame
from ui.club_ui import ClubFrame
from ui.agent_ui import AgentFrame
from utils.session import CurrentSession

# เพิ่มประสิทธิภาพการเรนเดอร์กราฟิกและความคมชัดของฟอนต์บน Windows
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# ตั้งค่าธีม CustomTkinter ให้เป็น Light Mode สไตล์ Apple Store
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Football Agent & Transfer Store")
        self.geometry("1180x740")
        self.minsize(1050, 640)
        self.configure(fg_color="#F5F6F8")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # เริ่มต้นสร้างและตรวจสอบฐานข้อมูล
        init_db()

        self.current_frame = None
        self.show_login()

    def show_login(self):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = LoginFrame(self, self.on_login_success)
        self.current_frame.grid(row=0, column=0, sticky="nsew")

    def on_login_success(self, role):
        if self.current_frame:
            self.current_frame.destroy()
            
        if role == "Admin":
            self.current_frame = AdminFrame(self, self.logout, self.switch_user)
        elif role == "Club":
            self.current_frame = ClubFrame(self, self.logout, self.switch_user)
        elif role == "Agent":
            self.current_frame = AgentFrame(self, self.logout, self.switch_user)
            
        self.current_frame.grid(row=0, column=0, sticky="nsew")

    def switch_user(self, username):
        from database.db_manager import get_connection, log_audit
        conn = get_connection()
        user = conn.execute("SELECT id, username, role, status FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        if user:
            CurrentSession.login(user['id'], user['username'], user['role'])
            log_audit("USER_SWITCH", f"1-Click switched portal to {user['username']} ({user['role']})")
            self.on_login_success(user['role'])

    def logout(self):
        CurrentSession.logout()
        self.show_login()

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()