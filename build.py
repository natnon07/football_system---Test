import os

files_to_create = {
    "requirements.txt": """
customtkinter==5.2.2
Pillow==10.2.0
bcrypt==4.1.2
    """,

    "run.bat": """
@echo off
echo Starting Football Agent Management System...
pip install -r requirements.txt
python main.py
pause
    """,

    "utils/__init__.py": "",
    "ui/__init__.py": "",
    "database/__init__.py": "",

    "utils/security.py": """
import bcrypt

def hash_password(password: str) -> str:
    # เข้ารหัสผ่านด้วย bcrypt
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    # ตรวจสอบรหัสผ่าน
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    """,

    "utils/session.py": """
class CurrentSession:
    user_id = None
    username = None
    role = None
    
    @classmethod
    def login(cls, user_id, username, role):
        cls.user_id = user_id
        cls.username = username
        cls.role = role

    @classmethod
    def logout(cls):
        cls.user_id = None
        cls.username = None
        cls.role = None
    """,

    "database/db_manager.py": """
import sqlite3
import os
from utils.security import hash_password

DB_NAME = "football_system.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('Admin', 'Agent', 'Club')), status TEXT DEFAULT 'Active', created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
    cursor.execute("CREATE TABLE IF NOT EXISTS agents (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER UNIQUE, first_name TEXT, last_name TEXT, agency_name TEXT, FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)")
    cursor.execute("CREATE TABLE IF NOT EXISTS clubs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER UNIQUE, club_name TEXT, budget REAL, FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)")
    cursor.execute("CREATE TABLE IF NOT EXISTS players (id INTEGER PRIMARY KEY AUTOINCREMENT, agent_id INTEGER, first_name TEXT, known_as TEXT, dob DATE, nationality TEXT, main_position TEXT, estimated_value REAL, status TEXT DEFAULT 'Pending Approval', FOREIGN KEY(agent_id) REFERENCES agents(id))")
    cursor.execute("CREATE TABLE IF NOT EXISTS transfer_offers (id INTEGER PRIMARY KEY AUTOINCREMENT, club_id INTEGER, player_id INTEGER, agent_id INTEGER, offer_amount REAL, status TEXT DEFAULT 'Pending', created_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(club_id) REFERENCES clubs(id), FOREIGN KEY(player_id) REFERENCES players(id), FOREIGN KEY(agent_id) REFERENCES agents(id))")
    cursor.execute("CREATE TABLE IF NOT EXISTS player_media (id INTEGER PRIMARY KEY, player_id INTEGER, file_path TEXT)")

    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        print("Initializing Database with Dummy Data...")
        default_pwd = hash_password("password123")
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ('admin', default_pwd, 'Admin'))
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ('agent1', default_pwd, 'Agent'))
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ('club1', default_pwd, 'Club'))
        cursor.execute("INSERT INTO agents (user_id, first_name, last_name, agency_name) VALUES (2, 'Mino', 'Raiola Jr.', 'Global Sports')")
        cursor.execute("INSERT INTO clubs (user_id, club_name, budget) VALUES (3, 'Manchester United', 150000000)")
        cursor.execute("INSERT INTO players (agent_id, first_name, known_as, dob, nationality, main_position, estimated_value, status) VALUES (1, 'Erling', 'Haaland', '2000-07-21', 'Norway', 'ST', 180000000, 'Approved')")

    conn.commit()
    conn.close()
    """,

    "ui/login_ui.py": """
import customtkinter as ctk
from database.db_manager import get_connection
from utils.security import verify_password
from utils.session import CurrentSession
from tkinter import messagebox

class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, login_success_callback):
        super().__init__(master)
        self.login_success_callback = login_success_callback
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Football Agent Management", font=ctk.CTkFont(size=24, weight="bold")).grid(row=1, column=0, pady=(0, 20))
        self.username_entry = ctk.CTkEntry(self, placeholder_text="Username", width=250)
        self.username_entry.grid(row=2, column=0, pady=10)
        self.password_entry = ctk.CTkEntry(self, placeholder_text="Password", show="*", width=250)
        self.password_entry.grid(row=3, column=0, pady=10)
        self.login_btn = ctk.CTkButton(self, text="Login", command=self.attempt_login, width=250, fg_color="#1F6AA5")
        self.login_btn.grid(row=4, column=0, pady=20)
        ctk.CTkLabel(self, text="Default Accounts: admin / agent1 / club1\\nPassword: password123", text_color="gray").grid(row=5, column=0, pady=10)

    def attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password.")
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash, role, status FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and verify_password(password, user['password_hash']):
            if user['status'] != 'Active':
                messagebox.showerror("Access Denied", "Your account has been suspended.")
                return
            CurrentSession.login(user['id'], user['username'], user['role'])
            self.login_success_callback(user['role'])
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")
    """,

    "ui/admin_ui.py": """
import customtkinter as ctk
from database.db_manager import get_connection
from tkinter import messagebox, ttk

class AdminFrame(ctk.CTkFrame):
    def __init__(self, master, logout_callback):
        super().__init__(master)
        self.logout_callback = logout_callback
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#1e1e24")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(self.sidebar, text="ADMIN PANEL", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=30)
        ctk.CTkButton(self.sidebar, text="Dashboard", anchor="w", command=self.show_dashboard).grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkButton(self.sidebar, text="Manage Users", anchor="w", command=self.show_users).grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkButton(self.sidebar, text="Logout", fg_color="#d63031", hover_color="#ff7675", anchor="w", command=self.logout_callback).grid(row=5, column=0, padx=20, pady=20, sticky="ew")

        self.main_content = ctk.CTkFrame(self, corner_radius=0, fg_color="#2d3436")
        self.main_content.grid(row=0, column=1, sticky="nsew")
        self.show_dashboard()

    def clear_main_content(self):
        for widget in self.main_content.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_main_content()
        ctk.CTkLabel(self.main_content, text="System Dashboard", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=30, padx=30, anchor="w")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM players")
        player_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM transfer_offers")
        offer_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM transfer_offers WHERE status='Completed' OR status='Accepted'")
        completed_deals = cursor.fetchone()[0]
        conn.close()

        cards_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        cards_frame.pack(fill="x", padx=30)
        cards_frame.grid_columnconfigure((0,1,2,3), weight=1)

        self.create_stat_card(cards_frame, "Total Users", user_count, "#0984e3").grid(row=0, column=0, padx=10, sticky="ew")
        self.create_stat_card(cards_frame, "Total Players", player_count, "#00b894").grid(row=0, column=1, padx=10, sticky="ew")
        self.create_stat_card(cards_frame, "Total Offers", offer_count, "#fdcb6e").grid(row=0, column=2, padx=10, sticky="ew")
        self.create_stat_card(cards_frame, "Completed Deals", completed_deals, "#d63031").grid(row=0, column=3, padx=10, sticky="ew")

    def create_stat_card(self, parent, title, value, color):
        card = ctk.CTkFrame(parent, fg_color="#353b48", corner_radius=10, border_width=2, border_color=color)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=16), text_color="gray").pack(pady=(15, 5))
        ctk.CTkLabel(card, text=str(value), font=ctk.CTkFont(size=36, weight="bold"), text_color=color).pack(pady=(0, 15))
        return card

    def show_users(self):
        self.clear_main_content()
        ctk.CTkLabel(self.main_content, text="Manage Users", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(30, 10), padx=30, anchor="w")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2d3436", foreground="white", rowheight=30, fieldbackground="#2d3436", borderwidth=0)
        style.configure("Treeview.Heading", background="#1e1e24", foreground="white", font=('Arial', 11, 'bold'))
        style.map('Treeview', background=[('selected', '#0984e3')])

        columns = ("id", "username", "role", "status", "created_at")
        self.tree = ttk.Treeview(self.main_content, columns=columns, show="headings", height=15)
        
        headers = ["ID", "Username", "Role", "Status", "Joined Date"]
        for col, head in zip(columns, headers):
            self.tree.heading(col, text=head)
            self.tree.column(col, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=30, pady=10)
        self.load_users_to_tree()

        control_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        control_frame.pack(fill="x", padx=30, pady=20)
        ctk.CTkButton(control_frame, text="Toggle Account Status", command=self.toggle_user_status).pack(side="left")
        ctk.CTkButton(control_frame, text="Refresh", command=self.load_users_to_tree, fg_color="gray").pack(side="left", padx=10)

    def load_users_to_tree(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role, status, created_at FROM users")
        for user in cursor.fetchall():
            self.tree.insert("", "end", values=(user['id'], user['username'], user['role'], user['status'], user['created_at']))
        conn.close()

    def toggle_user_status(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a user from the table first.")
            return
        item = self.tree.item(selected_item[0])
        user_id = item['values'][0]
        current_status = item['values'][3]
        role = item['values'][2]

        if role == 'Admin':
            messagebox.showerror("Permission Denied", "Cannot modify Admin account status.")
            return

        new_status = 'Suspended' if current_status == 'Active' else 'Active'
        if messagebox.askyesno("Confirm", f"Change status to {new_status}?"):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET status = ? WHERE id = ?", (new_status, user_id))
            conn.commit()
            conn.close()
            self.load_users_to_tree()
    """,

    "ui/agent_ui.py": """
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from database.db_manager import get_connection
from utils.session import CurrentSession
from PIL import Image
import os
import shutil

class AgentFrame(ctk.CTkFrame):
    def __init__(self, master, logout_callback):
        super().__init__(master)
        self.logout_callback = logout_callback
        self.agent_id = self.get_or_create_agent_profile()
        os.makedirs("assets/players", exist_ok=True)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#1e1e24")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(self.sidebar, text="AGENT PORTAL", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=30)
        ctk.CTkButton(self.sidebar, text="Dashboard", anchor="w", command=self.show_dashboard).grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkButton(self.sidebar, text="My Players", anchor="w", command=self.show_players).grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkButton(self.sidebar, text="Transfer Offers", anchor="w", command=self.show_offers).grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkButton(self.sidebar, text="Logout", fg_color="#d63031", hover_color="#ff7675", anchor="w", command=self.logout_callback).grid(row=6, column=0, padx=20, pady=20, sticky="ew")

        self.main_content = ctk.CTkFrame(self, corner_radius=0, fg_color="#2d3436")
        self.main_content.grid(row=0, column=1, sticky="nsew")
        self.show_dashboard()

    def get_or_create_agent_profile(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM agents WHERE user_id=?", (CurrentSession.user_id,))
        result = cursor.fetchone()
        if not result:
            cursor.execute("INSERT INTO agents (user_id, first_name, last_name, agency_name) VALUES (?, ?, ?, ?)", (CurrentSession.user_id, 'New', 'Agent', 'Independent'))
            conn.commit()
            agent_id = cursor.lastrowid
        else:
            agent_id = result['id']
        conn.close()
        return agent_id

    def clear_main_content(self):
        for widget in self.main_content.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_main_content()
        ctk.CTkLabel(self.main_content, text="Agent Dashboard", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=30, padx=30, anchor="w")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM players WHERE agent_id=?", (self.agent_id,))
        player_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM transfer_offers WHERE agent_id=? AND status='Pending'", (self.agent_id,))
        pending_offers = cursor.fetchone()[0]
        conn.close()

        cards_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        cards_frame.pack(fill="x", padx=30)
        cards_frame.grid_columnconfigure((0,1), weight=1)
        self.create_stat_card(cards_frame, "Players in Agency", player_count, "#00b894").grid(row=0, column=0, padx=10, sticky="ew")
        self.create_stat_card(cards_frame, "Pending Offers", pending_offers, "#fdcb6e").grid(row=0, column=1, padx=10, sticky="ew")

    def create_stat_card(self, parent, title, value, color):
        card = ctk.CTkFrame(parent, fg_color="#353b48", corner_radius=10, border_width=2, border_color=color)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=16), text_color="gray").pack(pady=(15, 5))
        ctk.CTkLabel(card, text=str(value), font=ctk.CTkFont(size=36, weight="bold"), text_color=color).pack(pady=(0, 15))
        return card

    def show_players(self):
        self.clear_main_content()
        ctk.CTkLabel(self.main_content, text="My Players", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(30, 10), padx=30, anchor="w")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2d3436", foreground="white", rowheight=30, fieldbackground="#2d3436", borderwidth=0)
        style.configure("Treeview.Heading", background="#1e1e24", foreground="white", font=('Arial', 11, 'bold'))
        style.map('Treeview', background=[('selected', '#0984e3')])

        columns = ("id", "name", "position", "value", "status")
        self.tree = ttk.Treeview(self.main_content, columns=columns, show="headings", height=12)
        
        headers = ["ID", "Known As", "Position", "Estimated Value", "Status"]
        for col, head in zip(columns, headers):
            self.tree.heading(col, text=head)
            self.tree.column(col, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=30, pady=10)
        self.load_players()

        control_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        control_frame.pack(fill="x", padx=30, pady=20)
        ctk.CTkButton(control_frame, text="Add New Player", command=self.open_add_player_dialog).pack(side="left")

    def load_players(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, known_as, main_position, estimated_value, status FROM players WHERE agent_id=?", (self.agent_id,))
        for p in cursor.fetchall():
            val = f"EUR {p['estimated_value']:,.2f}" if p['estimated_value'] else "N/A"
            self.tree.insert("", "end", values=(p['id'], p['known_as'], p['main_position'], val, p['status']))
        conn.close()

    def open_add_player_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Player")
        dialog.geometry("400x550")
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Player Details", font=("Arial", 20, "bold")).pack(pady=15)
        entries = {}
        fields = [("first_name", "First Name"), ("known_as", "Known As"), ("dob", "Date of Birth"), ("nationality", "Nationality"), ("main_position", "Position"), ("estimated_value", "Value")]
        for key, label in fields:
            ctk.CTkLabel(dialog, text=label).pack(anchor="w", padx=40)
            ent = ctk.CTkEntry(dialog, width=320)
            ent.pack(padx=40, pady=(0, 10))
            entries[key] = ent

        self.selected_image_path = None
        def select_image():
            filepath = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
            if filepath:
                self.selected_image_path = filepath
                btn_img.configure(text="Image Selected")

        btn_img = ctk.CTkButton(dialog, text="Upload Picture", fg_color="gray", command=select_image)
        btn_img.pack(pady=10)

        def save_player():
            try:
                val = float(entries['estimated_value'].get()) if entries['estimated_value'].get() else 0.0
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO players (agent_id, first_name, known_as, dob, nationality, main_position, estimated_value, status) VALUES (?, ?, ?, ?, ?, ?, ?, 'Approved')", (self.agent_id, entries['first_name'].get(), entries['known_as'].get(), entries['dob'].get(), entries['nationality'].get(), entries['main_position'].get(), val))
                player_id = cursor.lastrowid
                if self.selected_image_path:
                    ext = self.selected_image_path.split('.')[-1]
                    new_path = f"assets/players/player_{player_id}.{ext}"
                    shutil.copy(self.selected_image_path, new_path)
                    cursor.execute("INSERT INTO player_media (player_id, file_path) VALUES (?, ?)", (player_id, new_path))
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", "Player added successfully!")
                dialog.destroy()
                self.load_players()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(dialog, text="Save Player", fg_color="#00b894", command=save_player).pack(pady=20)

    def show_offers(self):
        self.clear_main_content()
        ctk.CTkLabel(self.main_content, text="Transfer Offers", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(30, 10), padx=30, anchor="w")

        columns = ("offer_id", "club", "player", "amount", "status")
        self.offer_tree = ttk.Treeview(self.main_content, columns=columns, show="headings", height=10)
        
        headers = ["Offer ID", "Club", "Player", "Amount", "Status"]
        for col, head in zip(columns, headers):
            self.offer_tree.heading(col, text=head)
            self.offer_tree.column(col, anchor="center")

        self.offer_tree.pack(fill="both", expand=True, padx=30, pady=10)
        self.load_offers()

        control_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        control_frame.pack(fill="x", padx=30, pady=20)
        ctk.CTkButton(control_frame, text="Accept Offer", fg_color="#00b894", command=lambda: self.update_offer_status('Accepted')).pack(side="left", padx=5)
        ctk.CTkButton(control_frame, text="Reject Offer", fg_color="#d63031", command=lambda: self.update_offer_status('Rejected')).pack(side="left", padx=5)

    def load_offers(self):
        for row in self.offer_tree.get_children():
            self.offer_tree.delete(row)
        conn = get_connection()
        cursor = conn.cursor()
        query = "SELECT t.id, c.club_name, p.known_as, t.offer_amount, t.status FROM transfer_offers t JOIN clubs c ON t.club_id = c.id JOIN players p ON t.player_id = p.id WHERE t.agent_id = ?"
        cursor.execute(query, (self.agent_id,))
        for o in cursor.fetchall():
            val = f"EUR {o['offer_amount']:,.2f}"
            self.offer_tree.insert("", "end", values=(o['id'], o['club_name'], o['known_as'], val, o['status']))
        conn.close()

    def update_offer_status(self, new_status):
        selected = self.offer_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an offer.")
            return
        offer_id = self.offer_tree.item(selected[0])['values'][0]
        current_status = self.offer_tree.item(selected[0])['values'][4]
        if current_status != 'Pending':
            messagebox.showinfo("Notice", f"This offer is already {current_status}.")
            return
        if messagebox.askyesno("Confirm", f"Are you sure you want to {new_status} this offer?"):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE transfer_offers SET status=? WHERE id=?", (new_status, offer_id))
            if new_status == 'Accepted':
                cursor.execute("SELECT player_id FROM transfer_offers WHERE id=?", (offer_id,))
                pid = cursor.fetchone()['player_id']
                cursor.execute("UPDATE players SET status='Transferred' WHERE id=?", (pid,))
            conn.commit()
            conn.close()
            self.load_offers()
    """,

    "ui/club_ui.py": """
import customtkinter as ctk
from tkinter import ttk, messagebox
from database.db_manager import get_connection
from utils.session import CurrentSession
from PIL import Image
import os

class ClubFrame(ctk.CTkFrame):
    def __init__(self, master, logout_callback):
        super().__init__(master)
        self.logout_callback = logout_callback
        self.club_id = self.get_or_create_club_profile()

        os.makedirs("assets", exist_ok=True)
        self.default_avatar_path = "assets/default_avatar.png"
        if not os.path.exists(self.default_avatar_path):
            img = Image.new('RGB', (200, 200), color=(73, 109, 137))
            img.save(self.default_avatar_path)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#1e1e24")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(self.sidebar, text="CLUB PORTAL", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=30)
        ctk.CTkButton(self.sidebar, text="Dashboard", anchor="w", command=self.show_dashboard).grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkButton(self.sidebar, text="Transfer Market", anchor="w", command=self.show_market).grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkButton(self.sidebar, text="My Offers", anchor="w", command=self.show_offers).grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkButton(self.sidebar, text="Logout", fg_color="#d63031", hover_color="#ff7675", anchor="w", command=self.logout_callback).grid(row=6, column=0, padx=20, pady=20, sticky="ew")

        self.main_content = ctk.CTkFrame(self, corner_radius=0, fg_color="#2d3436")
        self.main_content.grid(row=0, column=1, sticky="nsew")
        self.show_dashboard()

    def get_or_create_club_profile(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM clubs WHERE user_id=?", (CurrentSession.user_id,))
        result = cursor.fetchone()
        if not result:
            cursor.execute("INSERT INTO clubs (user_id, club_name, budget) VALUES (?, ?, ?)", (CurrentSession.user_id, 'New Club F.C.', 50000000))
            conn.commit()
            club_id = cursor.lastrowid
        else:
            club_id = result['id']
        conn.close()
        return club_id

    def clear_main_content(self):
        for widget in self.main_content.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_main_content()
        ctk.CTkLabel(self.main_content, text="Club Dashboard", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=30, padx=30, anchor="w")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT budget FROM clubs WHERE id=?", (self.club_id,))
        budget = cursor.fetchone()['budget']
        cursor.execute("SELECT COUNT(*) FROM transfer_offers WHERE club_id=?", (self.club_id,))
        total_offers = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM transfer_offers WHERE club_id=? AND status='Accepted'", (self.club_id,))
        accepted_offers = cursor.fetchone()[0]
        conn.close()

        cards_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        cards_frame.pack(fill="x", padx=30)
        cards_frame.grid_columnconfigure((0,1,2), weight=1)
        self.create_stat_card(cards_frame, "Transfer Budget", f"EUR {budget:,.0f}", "#00b894").grid(row=0, column=0, padx=10, sticky="ew")
        self.create_stat_card(cards_frame, "Offers Sent", total_offers, "#0984e3").grid(row=0, column=1, padx=10, sticky="ew")
        self.create_stat_card(cards_frame, "Deals Completed", accepted_offers, "#fdcb6e").grid(row=0, column=2, padx=10, sticky="ew")

    def create_stat_card(self, parent, title, value, color):
        card = ctk.CTkFrame(parent, fg_color="#353b48", corner_radius=10, border_width=2, border_color=color)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=16), text_color="gray").pack(pady=(15, 5))
        ctk.CTkLabel(card, text=str(value), font=ctk.CTkFont(size=28, weight="bold"), text_color=color).pack(pady=(0, 15))
        return card

    def show_market(self):
        self.clear_main_content()
        ctk.CTkLabel(self.main_content, text="Transfer Market (Scouting)", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(30, 10), padx=30, anchor="w")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2d3436", foreground="white", rowheight=30, fieldbackground="#2d3436", borderwidth=0)
        style.configure("Treeview.Heading", background="#1e1e24", foreground="white", font=('Arial', 11, 'bold'))
        style.map('Treeview', background=[('selected', '#0984e3')])

        columns = ("id", "name", "position", "value", "agent_name", "agent_id")
        self.tree = ttk.Treeview(self.main_content, columns=columns, show="headings", height=12)
        self.tree.column("agent_id", width=0, stretch=False)
        
        headers = ["ID", "Player Name", "Position", "Est. Value", "Agent Agency", ""]
        for col, head in zip(columns, headers):
            self.tree.heading(col, text=head)
            if col != "agent_id":
                self.tree.column(col, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=30, pady=10)
        self.load_market_players()

        control_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        control_frame.pack(fill="x", padx=30, pady=20)
        ctk.CTkButton(control_frame, text="View Details & Make Offer", font=ctk.CTkFont(weight="bold"), fg_color="#00b894", command=self.open_offer_dialog).pack(side="left")

    def load_market_players(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = get_connection()
        cursor = conn.cursor()
        query = "SELECT p.id, p.known_as, p.main_position, p.estimated_value, a.id as agent_id, a.agency_name FROM players p JOIN agents a ON p.agent_id = a.id WHERE p.status = 'Approved'"
        cursor.execute(query)
        for p in cursor.fetchall():
            val = f"EUR {p['estimated_value']:,.2f}" if p['estimated_value'] else "N/A"
            self.tree.insert("", "end", values=(p['id'], p['known_as'], p['main_position'], val, p['agency_name'], p['agent_id']))
        conn.close()

    def open_offer_dialog(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Notice", "Please select a player to view and make an offer.")
            return

        item = self.tree.item(selected[0])['values']
        player_id = item[0]
        player_name = item[1]
        agent_id = item[5]

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Make Transfer Offer: {player_name}")
        dialog.geometry("500x550")
        dialog.grab_set()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM player_media WHERE player_id=?", (player_id,))
        media = cursor.fetchone()
        conn.close()

        img_path = media['file_path'] if media else self.default_avatar_path
        try:
            pil_image = Image.open(img_path)
            ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(150, 150))
            img_label = ctk.CTkLabel(dialog, image=ctk_image, text="")
            img_label.pack(pady=20)
        except Exception:
            ctk.CTkLabel(dialog, text="[ Image Not Found ]", text_color="red").pack(pady=20)

        ctk.CTkLabel(dialog, text=f"Target: {player_name}", font=("Arial", 22, "bold")).pack()
        ctk.CTkLabel(dialog, text=f"Est. Value: {item[3]}", font=("Arial", 14), text_color="gray").pack(pady=5)
        ctk.CTkLabel(dialog, text="Your Offer Amount (EUR):").pack(pady=(20, 5))
        offer_entry = ctk.CTkEntry(dialog, width=250, placeholder_text="e.g. 50000000")
        offer_entry.pack()

        def submit_offer():
            try:
                amount = float(offer_entry.get())
                if amount <= 0: raise ValueError
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO transfer_offers (club_id, player_id, agent_id, offer_amount, status) VALUES (?, ?, ?, ?, 'Pending')", (self.club_id, player_id, agent_id, amount))
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", "Offer sent to agent successfully!")
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid amount.")

        ctk.CTkButton(dialog, text="Submit Official Offer", fg_color="#0984e3", font=("Arial", 14, "bold"), command=submit_offer).pack(pady=30)

    def show_offers(self):
        self.clear_main_content()
        ctk.CTkLabel(self.main_content, text="My Transfer Offers", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(30, 10), padx=30, anchor="w")

        columns = ("offer_id", "player", "agency", "amount", "status")
        self.offer_tree = ttk.Treeview(self.main_content, columns=columns, show="headings", height=12)
        
        headers = ["Offer ID", "Player", "Agent/Agency", "Amount", "Status"]
        for col, head in zip(columns, headers):
            self.offer_tree.heading(col, text=head)
            self.offer_tree.column(col, anchor="center")

        self.offer_tree.pack(fill="both", expand=True, padx=30, pady=10)
        
        conn = get_connection()
        cursor = conn.cursor()
        query = "SELECT t.id, p.known_as, a.agency_name, t.offer_amount, t.status FROM transfer_offers t JOIN players p ON t.player_id = p.id JOIN agents a ON t.agent_id = a.id WHERE t.club_id = ?"
        cursor.execute(query, (self.club_id,))
        for o in cursor.fetchall():
            val = f"EUR {o['offer_amount']:,.2f}"
            self.offer_tree.insert("", "end", values=(o['id'], o['known_as'], o['agency_name'], val, o['status']))
        conn.close()
    """,

    "main.py": """
import customtkinter as ctk
from database.db_manager import init_db
from ui.login_ui import LoginFrame
from utils.session import CurrentSession
from ui.admin_ui import AdminFrame
from ui.agent_ui import AgentFrame
from ui.club_ui import ClubFrame

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Football Agent Management System")
        self.geometry("1200x800")
        self.minsize(1000, 600)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

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

        if role == 'Admin':
            self.current_frame = AdminFrame(self, self.logout)
        elif role == 'Agent':
            self.current_frame = AgentFrame(self, self.logout)
        elif role == 'Club':
            self.current_frame = ClubFrame(self, self.logout)
            
        self.current_frame.grid(row=0, column=0, sticky="nsew")

    def logout(self):
        CurrentSession.logout()
        self.show_login()

if __name__ == "__main__":
    init_db()
    app = App()
    app.mainloop()
    """
}

def create_project():
    print("="*50)
    print("🚀 Auto-Building Football Agent Management System")
    print("="*50)
    
    for file_path, content in files_to_create.items():
        # สร้างโฟลเดอร์ถ้าไม่มี
        dir_name = os.path.dirname(file_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)
            
        # เขียนไฟล์
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\\n")
        print(f"✅ Created: {file_path}")
    
    # สร้างโฟลเดอร์สำหรับเก็บรูปนักเตะ
    os.makedirs("assets/players", exist_ok=True)
    print("✅ Created: assets/players (Directory for images)")
    
    print("="*50)
    print("🎉 Project built successfully!")
    print("Next Steps in Terminal:")
    print("1. pip install -r requirements.txt")
    print("2. python main.py")
    print("="*50)

if __name__ == "__main__":
    create_project()