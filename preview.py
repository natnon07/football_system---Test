import customtkinter as ctk
from database.db_manager import init_db, get_connection
from ui.admin_ui import AdminFrame
from ui.agent_ui import AgentFrame
from ui.club_ui import ClubFrame
from ui.login_ui import LoginFrame
from utils.session import CurrentSession

# ตั้งค่าธีม CustomTkinter ให้เป็น Light Mode สไตล์ Apple Store
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class PreviewApp(ctk.CTk):
    def __init__(self, target_role="Login"):
        super().__init__()
        self.title("Apple Store Aesthetic — Football Portal Previewer")
        self.geometry("1180x740")
        self.minsize(1050, 640)
        self.configure(fg_color="#F5F6F8")
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        init_db()
        self.current_frame = None

        # แถบสลับ Role พรีวิวด้านบนสไตล์มินิมอล
        self.switcher_bar = ctk.CTkFrame(self, height=44, fg_color="#F5F5F7", corner_radius=0, border_width=1, border_color="#E5E5EA")
        self.switcher_bar.grid(row=0, column=0, sticky="ew")
        
        ctk.CTkLabel(self.switcher_bar, text="👁️  PREVIEW SWITCHER:", font=("Segoe UI", 11, "bold"), text_color="#86868B").pack(side="left", padx=20, pady=8)

        self.role_buttons = {}
        for role, label in [
            ("Login", "🔑 Login Screen"),
            ("Admin", "👑 Admin Portal"),
            ("Club", "🏟️ Club Portal (Real Madrid)"),
            ("Agent", "💼 Agent Portal (Jorge Mendes)")
        ]:
            btn = ctk.CTkButton(
                self.switcher_bar,
                text=label,
                font=("Segoe UI", 11, "bold"),
                height=28,
                fg_color="#1D1D1F" if role == target_role else "transparent",
                hover_color="#E8E8ED",
                text_color="#FFFFFF" if role == target_role else "#1D1D1F",
                corner_radius=14,
                command=lambda r=role: self.switch_role(r)
            )
            btn.pack(side="left", padx=4, pady=6)
            self.role_buttons[role] = btn

        self.switch_role(target_role)

    def switch_role(self, role):
        for r, btn in self.role_buttons.items():
            is_active = (r == role)
            btn.configure(
                fg_color="#0071E3" if is_active else "transparent",
                text_color="#FFFFFF" if is_active else "#1D1D1F"
            )

        if self.current_frame:
            self.current_frame.destroy()

        conn = get_connection()
        cursor = conn.cursor()

        if role == "Login":
            CurrentSession.logout()
            self.current_frame = LoginFrame(self, lambda r: self.switch_role(r))
        elif role == "Admin":
            cursor.execute("SELECT id, username FROM users WHERE role='Admin' LIMIT 1")
            u = cursor.fetchone()
            uid = u['id'] if u else 1
            un = u['username'] if u else 'admin'
            CurrentSession.login(uid, un, "Admin")
            self.current_frame = AdminFrame(self, lambda: self.switch_role("Login"), self.switch_user)

        elif role == "Club":
            cursor.execute("SELECT u.id, u.username, c.club_name FROM users u JOIN clubs c ON u.id = c.user_id LIMIT 1")
            u = cursor.fetchone()
            uid = u['id'] if u else 2
            un = u['username'] if u else 'realmadrid'
            CurrentSession.login(uid, un, "Club")
            self.current_frame = ClubFrame(self, lambda: self.switch_role("Login"), self.switch_user)

        elif role == "Agent":
            cursor.execute("SELECT u.id, u.username FROM users u JOIN agents a ON u.id = a.user_id LIMIT 1")
            u = cursor.fetchone()
            uid = u['id'] if u else 7
            un = u['username'] if u else 'agent1'
            CurrentSession.login(uid, un, "Agent")
            self.current_frame = AgentFrame(self, lambda: self.switch_role("Login"), self.switch_user)

        conn.close()
        self.current_frame.grid(row=1, column=0, sticky="nsew")

    def switch_user(self, username):
        conn = get_connection()
        user = conn.execute("SELECT id, username, role, status FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        if user:
            CurrentSession.login(user['id'], user['username'], user['role'])
            if self.current_frame:
                self.current_frame.destroy()

            for r, btn in self.role_buttons.items():
                is_active = (r == user['role'])
                btn.configure(
                    fg_color="#0071E3" if is_active else "transparent",
                    text_color="#FFFFFF" if is_active else "#1D1D1F"
                )

            if user['role'] == "Admin":
                self.current_frame = AdminFrame(self, lambda: self.switch_role("Login"), self.switch_user)
            elif user['role'] == "Club":
                self.current_frame = ClubFrame(self, lambda: self.switch_role("Login"), self.switch_user)
            elif user['role'] == "Agent":
                self.current_frame = AgentFrame(self, lambda: self.switch_role("Login"), self.switch_user)
            self.current_frame.grid(row=1, column=0, sticky="nsew")

if __name__ == "__main__":
    app = PreviewApp(target_role="Club")
    app.mainloop()