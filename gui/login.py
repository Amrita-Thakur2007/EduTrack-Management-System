import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DBManager
from gui.theme import COLORS, FONTS

class LoginWindow(tk.Toplevel):
    """Authentication modal for logging in with prominent Create Account option."""
    def __init__(self, welcome_win: tk.Tk, db_manager: DBManager, initial_role: str = "Student"):
        super().__init__(welcome_win)
        self.welcome_win = welcome_win
        self.db = db_manager
        self.role = initial_role

        self.title(f"{initial_role} Login - Portal")
        self.geometry("450x540")
        self.resizable(False, False)
        self.transient(welcome_win)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding=25)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_lbl = ttk.Label(main_frame, text=f"🔐 {self.role} Login", font=FONTS["h1"])
        title_lbl.pack(anchor=tk.W, pady=(0, 4))

        sub_lbl = ttk.Label(main_frame, text="Enter your credentials or create a new account.", style="Subtitle.TLabel")
        sub_lbl.pack(anchor=tk.W, pady=(0, 15))

        # Role Selector Combo
        ttk.Label(main_frame, text="Select Portal Role:", font=FONTS["body_bold"]).pack(anchor=tk.W, pady=(4, 2))
        self.combo_role = ttk.Combobox(main_frame, values=["Admin", "Teacher", "Student", "Parent"], state="readonly")
        self.combo_role.set(self.role)
        self.combo_role.pack(fill=tk.X, pady=(0, 10))
        self.combo_role.bind("<<ComboboxSelected>>", self._on_role_change)

        # Username / ID
        self.lbl_username = ttk.Label(main_frame, text="Username / Login ID:", font=FONTS["body_bold"])
        self.lbl_username.pack(anchor=tk.W, pady=(4, 2))
        self.entry_username = ttk.Entry(main_frame)
        self.entry_username.pack(fill=tk.X, pady=(0, 2))
        
        self.lbl_hint = ttk.Label(main_frame, text="", font=FONTS["small"], foreground="#0284c7")
        self.lbl_hint.pack(anchor=tk.W, pady=(0, 8))
        self._update_username_label()

        # Password (hides password while typing by default)
        ttk.Label(main_frame, text="Password:", font=FONTS["body_bold"]).pack(anchor=tk.W, pady=(4, 2))
        pass_container = ttk.Frame(main_frame)
        pass_container.pack(fill=tk.X, pady=(0, 4))

        self.entry_password = ttk.Entry(pass_container, show="*")
        self.entry_password.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def toggle_login_pass():
            if self.entry_password.cget("show") == "*":
                self.entry_password.config(show="")
                btn_show_pass.config(text="🙈 Hide")
            else:
                self.entry_password.config(show="*")
                btn_show_pass.config(text="👁️ Show")

        btn_show_pass = ttk.Button(pass_container, text="👁️ Show", width=8, command=toggle_login_pass)
        btn_show_pass.pack(side=tk.RIGHT, padx=(5, 0))

        # Forgot Password Link
        forgot_frame = ttk.Frame(main_frame)
        forgot_frame.pack(fill=tk.X, pady=(0, 12))
        btn_forgot = tk.Button(
            forgot_frame,
            text="❓ Forgot Password?",
            font=("Segoe UI", 9, "underline"),
            fg="#2563eb",
            bd=0,
            cursor="hand2",
            activeforeground="#1d4ed8",
            command=self.open_forgot_password
        )
        btn_forgot.pack(side=tk.RIGHT)

        # LOGIN Button (performs complete login action)
        self.btn_login = ttk.Button(main_frame, text="🔑 LOGIN", style="Primary.TButton", command=self.do_login)
        self.btn_login.pack(fill=tk.X, pady=(0, 12), ipady=5)

        # Keyboard Enter Key Binding to trigger LOGIN
        self.bind("<Return>", lambda e: self.do_login())
        self.entry_username.bind("<Return>", lambda e: self.do_login())
        self.entry_password.bind("<Return>", lambda e: self.do_login())

        # Divider line
        divider = ttk.Separator(main_frame, orient="horizontal")
        divider.pack(fill=tk.X, pady=8)

        # Create Account Section
        reg_box = ttk.Frame(main_frame)
        reg_box.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(reg_box, text="New user? Need an account?", style="Subtitle.TLabel").pack(side=tk.LEFT)

        btn_create = tk.Button(
            reg_box,
            text="✨ Create Account",
            font=("Segoe UI", 9, "bold"),
            bg="#059669",
            fg="#ffffff",
            activebackground="#047857",
            activeforeground="#ffffff",
            bd=0,
            cursor="hand2",
            command=self.open_create_account
        )
        btn_create.pack(side=tk.RIGHT, ipadx=10, ipady=4)

    def _on_role_change(self, event=None):
        self.role = self.combo_role.get()
        self.title(f"{self.role} Login - Portal")
        self._update_username_label()

    def _update_username_label(self):
        if hasattr(self, 'lbl_username'):
            if self.role == "Student":
                self.lbl_username.config(text="Student ID / Enrollment Number *:")
                self.lbl_hint.config(text="School students enter Student ID. College students enter Enrollment Number.")
            else:
                self.lbl_username.config(text="Username / Login ID *:")
                self.lbl_hint.config(text="")

    def do_login(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get()
        role = self.combo_role.get()

        if not username or not password:
            messagebox.showwarning("Validation Error", "Please enter both Username and Password.")
            return

        res = self.db.authenticate_user(username, password, role)
        if isinstance(res, dict) and not res.get("success"):
            err_type = res.get("error_type")
            msg = res.get("message", "Invalid username or password. Please try again.")

            # Clear ONLY the password field and keep Username / User ID filled
            if hasattr(self, 'entry_password'):
                self.entry_password.delete(0, tk.END)

            if err_type == "wrong_password":
                messagebox.showerror("Login Failed", "Invalid username or password. Please try again.")
            else:
                messagebox.showerror("Login Failed", msg)
            return

        user_data = res
        # Login success!
        self.grab_release()
        self.destroy()
        self.welcome_win.withdraw() # Hide welcome screen

        if role == "Admin":
            from gui.admin_dashboard import AdminDashboard
            AdminDashboard(self.welcome_win, self.db, user_data)
        elif role == "Teacher":
            from gui.teacher_dashboard import TeacherDashboard
            TeacherDashboard(self.welcome_win, self.db, user_data)
        elif role == "Student":
            from gui.student_dashboard import StudentDashboard
            StudentDashboard(self.welcome_win, self.db, user_data)
        elif role == "Parent":
            from gui.parent_dashboard import ParentDashboard
            ParentDashboard(self.welcome_win, self.db, user_data)

    def open_forgot_password(self):
        selected_role = self.combo_role.get()
        ForgotPasswordDialog(self, self.db, selected_role)

    def open_create_account(self):
        selected_role = self.combo_role.get()
        self.grab_release()
        self.destroy()

        if selected_role == "Admin":
            from gui.register import RoleSelectModal
            RoleSelectModal(self.welcome_win, self.db)
        else:
            from gui.register import AccountRegistrationWindow
            AccountRegistrationWindow(self.welcome_win, self.db, selected_role)


class ForgotPasswordDialog(tk.Toplevel):
    """Password recovery modal using Favourite Person Name security question."""
    def __init__(self, parent_win, db_manager: DBManager, initial_role: str = "Student"):
        super().__init__(parent_win)
        self.parent_win = parent_win
        self.db = db_manager
        self.role = initial_role

        self.title("🔑 Password Recovery - Forgot Password")
        self.geometry("460x540")
        self.resizable(False, False)
        self.transient(parent_win)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        f = ttk.Frame(self, padding=25)
        f.pack(fill=tk.BOTH, expand=True)

        ttk.Label(f, text="🔑 Reset Password", font=FONTS["h2"]).pack(anchor=tk.W, pady=(0, 4))
        ttk.Label(f, text="Verify your identity to reset your password.", style="Subtitle.TLabel").pack(anchor=tk.W, pady=(0, 15))

        ident_label = "Student ID / Enrollment Number *:" if self.role == "Student" else "User ID or Registered Email *:"
        ttk.Label(f, text=ident_label, font=FONTS["body_bold"]).pack(anchor=tk.W, pady=(4, 2))
        if self.role == "Student":
            ttk.Label(f, text="School students enter Student ID. College students enter Enrollment Number.", font=FONTS["small"], foreground="#0284c7", wraplength=400).pack(anchor=tk.W, pady=(0, 2))
        self.entry_identifier = ttk.Entry(f)
        self.entry_identifier.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(f, text="Favourite Person Name *:", font=FONTS["body_bold"]).pack(anchor=tk.W, pady=(4, 2))
        ttk.Label(f, text="Enter the name of your favourite person provided during registration.", font=FONTS["small"], foreground="#0284c7", wraplength=400).pack(anchor=tk.W, pady=(0, 2))
        self.entry_fav_person = ttk.Entry(f)
        self.entry_fav_person.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(f, text="New Password *:", font=FONTS["body_bold"]).pack(anchor=tk.W, pady=(4, 2))
        self.entry_new_pass = ttk.Entry(f, show="*")
        self.entry_new_pass.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(f, text="Confirm New Password *:", font=FONTS["body_bold"]).pack(anchor=tk.W, pady=(4, 2))
        self.entry_confirm_pass = ttk.Entry(f, show="*")
        self.entry_confirm_pass.pack(fill=tk.X, pady=(0, 20))

        btn_bar = ttk.Frame(f)
        btn_bar.pack(fill=tk.X)

        btn_cancel = ttk.Button(btn_bar, text="Cancel", command=self.destroy)
        btn_cancel.pack(side=tk.LEFT)

        btn_reset = ttk.Button(btn_bar, text="🔑 Reset Password", style="Primary.TButton", command=self.do_reset)
        btn_reset.pack(side=tk.RIGHT)

    def do_reset(self):
        ident = self.entry_identifier.get().strip()
        fav_person = self.entry_fav_person.get().strip()
        new_pass = self.entry_new_pass.get()
        confirm_pass = self.entry_confirm_pass.get()

        if not ident or not fav_person or not new_pass or not confirm_pass:
            messagebox.showwarning("Validation Error", "Please fill in all fields.")
            return

        if new_pass != confirm_pass:
            messagebox.showerror("Validation Error", "Passwords do not match.")
            return

        if len(new_pass) < 4:
            messagebox.showwarning("Validation Error", "New Password must be at least 4 characters long.")
            return

        ok, msg = self.db.reset_password_with_favourite_person(ident, fav_person, new_pass, self.role)
        if ok:
            messagebox.showinfo("Success", "Password reset successfully. Please log in using your new password.")
            if hasattr(self.parent_win, 'entry_username'):
                self.parent_win.entry_username.delete(0, tk.END)
                self.parent_win.entry_username.insert(0, ident)
            self.destroy()
        else:
            messagebox.showerror("Recovery Failed", msg)
