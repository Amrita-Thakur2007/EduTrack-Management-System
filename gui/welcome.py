import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DBManager
from gui.theme import apply_theme, COLORS, FONTS

class WelcomeWindow(tk.Tk):
    """Main Application Welcome / Landing Window."""
    def __init__(self, db_manager: DBManager):
        super().__init__()
        self.db = db_manager
        self.title("Student Management & Performance Prediction System")
        self.geometry("960x680")
        self.minsize(900, 620)

        apply_theme(self)
        self.center_window()
        self._build_ui()
        self._check_first_run_admin()

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws // 2) - (w // 2)
        y = (hs // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _check_first_run_admin(self):
        """
        Startup Logic:
        Query SQLite database: SELECT COUNT(*) FROM users WHERE role = 'Admin'.
        If NO Admin exists -> Prompt First-Time Admin Account Creation.
        ELSE -> Skip Admin Creation completely and show normal Login portal.
        """
        if not self.db.has_admin():
            self.after(300, self.open_admin_setup)

    def open_admin_setup(self):
        if not self.db.has_admin():
            from gui.register import AdminSetupDialog
            AdminSetupDialog(self, self.db, on_complete_callback=self.on_admin_setup_complete)

    def on_admin_setup_complete(self, new_admin_username: str):
        """Called immediately after first Admin account creation."""
        from gui.login import LoginWindow
        login_win = LoginWindow(self, self.db, "Admin")
        login_win.entry_username.delete(0, tk.END)
        login_win.entry_username.insert(0, new_admin_username)

    def _build_ui(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header Banner
        banner = tk.Frame(main_frame, bg="#0f172a", height=130)
        banner.pack(fill=tk.X)
        banner.pack_propagate(False)

        title_lbl = tk.Label(
            banner, 
            text="🎓 Student Management & Performance Prediction System", 
            font=("Segoe UI", 19, "bold"), 
            bg="#0f172a", 
            fg="#ffffff"
        )
        title_lbl.pack(expand=True, pady=(15, 0))

        sub_lbl = tk.Label(
            banner, 
            text="AI Student Analytics, Face Attendance & Academic Evaluation Portal", 
            font=("Segoe UI", 10), 
            bg="#0f172a", 
            fg="#94a3b8"
        )
        sub_lbl.pack(pady=(0, 15))

        # Content Body
        body = ttk.Frame(main_frame, padding=20)
        body.pack(fill=tk.BOTH, expand=True)

        # Top Action Bar
        action_bar = ttk.Frame(body)
        action_bar.pack(fill=tk.X, pady=(0, 15))

        welcome_title = ttk.Label(action_bar, text="Select your portal to Login or Register:", font=FONTS["h2"])
        welcome_title.pack(side=tk.LEFT)

        btn_global_reg = tk.Button(
            action_bar,
            text="✨ Create New Account",
            font=("Segoe UI", 10, "bold"),
            bg="#059669",
            fg="#ffffff",
            activebackground="#047857",
            activeforeground="#ffffff",
            bd=0,
            cursor="hand2",
            command=self.open_role_selector
        )
        btn_global_reg.pack(side=tk.RIGHT, ipadx=12, ipady=6)

        # Portals Grid Frame
        portals_frame = ttk.Frame(body)
        portals_frame.pack(fill=tk.BOTH, expand=True)

        roles_config = [
            ("🛡️ Admin Portal", "System Setup, Student/Teacher CRUD & Analytics", "Admin", "#2563eb"),
            ("👨‍🏫 Teacher Portal", "Attendance Scanner, Marks Entry & Class Predictions", "Teacher", "#0d9488"),
            ("🎓 Student Portal", "Personal Attendance, Marks Summary & ML Risk Analysis", "Student", "#7c3aed"),
            ("👨‍👩‍👧 Parent Portal", "Linked Child Academic Progress & Attendance Tracker", "Parent", "#059669")
        ]

        for i, (title, desc, role, color) in enumerate(roles_config):
            row = i // 2
            col = i % 2

            card = tk.Frame(portals_frame, bg=COLORS["bg_card"], bd=1, relief="solid", highlightthickness=0)
            card.grid(row=row, column=col, padx=12, pady=10, sticky="nsew")
            portals_frame.columnconfigure(col, weight=1)
            portals_frame.rowconfigure(row, weight=1)

            c_header = tk.Label(card, text=title, font=("Segoe UI", 12, "bold"), bg=COLORS["bg_card"], fg=color, anchor="w")
            c_header.pack(fill=tk.X, padx=15, pady=(12, 4))

            c_desc = tk.Label(card, text=desc, font=("Segoe UI", 9), bg=COLORS["bg_card"], fg=COLORS["text_muted"], wraplength=340, justify="left", anchor="w")
            c_desc.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

            btn_box = tk.Frame(card, bg=COLORS["bg_card"])
            btn_box.pack(fill=tk.X, padx=15, pady=(0, 12))

            btn_login = tk.Button(
                btn_box, 
                text=f"🔑 Login", 
                font=("Segoe UI", 9, "bold"), 
                bg=color, 
                fg="#ffffff", 
                activebackground="#1e293b", 
                activeforeground="#ffffff", 
                bd=0, 
                cursor="hand2", 
                command=lambda r=role: self.open_login(r)
            )
            btn_login.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4), ipady=5)

            if role != "Admin":
                btn_reg = tk.Button(
                    btn_box,
                    text="📝 Register",
                    font=("Segoe UI", 9, "bold"),
                    bg="#f1f5f9",
                    fg=COLORS["text_dark"],
                    activebackground="#e2e8f0",
                    bd=1,
                    relief="solid",
                    cursor="hand2",
                    command=lambda r=role: self.open_register(r)
                )
                btn_reg.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(4, 0), ipady=4)

        # Footer
        footer = ttk.Frame(main_frame, padding=12)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        btn_exit = ttk.Button(footer, text="❌ Exit Application", style="Danger.TButton", command=self.quit)
        btn_exit.pack(side=tk.RIGHT)

        lbl_version = ttk.Label(footer, text="System Version 1.2.0 | SQLite & Scikit-Learn Engine", style="Subtitle.TLabel")
        lbl_version.pack(side=tk.LEFT)

    def open_role_selector(self):
        from gui.register import RoleSelectModal
        RoleSelectModal(self, self.db)

    def open_login(self, role: str):
        from gui.login import LoginWindow
        LoginWindow(self, self.db, role)

    def open_register(self, role: str):
        from gui.register import AccountRegistrationWindow
        AccountRegistrationWindow(self, self.db, role)
