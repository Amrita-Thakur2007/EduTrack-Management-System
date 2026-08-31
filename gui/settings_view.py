import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DBManager
from gui.theme import COLORS, FONTS
from utils.validators import validate_email, validate_phone

class SettingsViewFrame(ttk.Frame):
    """Real, fully-functional Account Settings view for all user roles."""
    def __init__(self, parent, db_manager: DBManager, user_data: dict, role: str, on_cancel=None):
        super().__init__(parent, padding=20)
        self.db = db_manager
        self.user_data = user_data
        self.user_id = user_data['id']
        self.role = role
        self.on_cancel = on_cancel

        self._load_profile_data()
        self._build_ui()

    def _load_profile_data(self):
        """Fetch current profile record from database based on user role."""
        self.profile_record = None
        if self.role == "Teacher":
            teachers = self.db.get_all_teachers()
            for t in teachers:
                if t.get('user_id') == self.user_id:
                    self.profile_record = t
                    break
        elif self.role == "Student":
            self.profile_record = self.db.get_student_by_user_id(self.user_id)
            if not self.profile_record:
                self.profile_record = self.db.get_student(self.user_data['username'])
        elif self.role == "Parent":
            self.profile_record = self.db.get_parent_by_user_id(self.user_id)

    def _build_ui(self):
        # Header
        hdr = ttk.Frame(self)
        hdr.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(hdr, text=f"⚙️ Account Settings - {self.role} Portal", font=FONTS["h1"]).pack(anchor=tk.W)
        ttk.Label(hdr, text="Manage your authorized profile information and change your login password.", style="Subtitle.TLabel").pack(anchor=tk.W)

        # Main Scrollable Form Container
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(container, bg=COLORS["bg_main"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        form = ttk.Frame(canvas)

        form.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=form, anchor="nw", width=620)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- SECTION 1: PROFILE DETAILS ---
        ttk.Label(form, text="👤 AUTHORIZED PROFILE INFORMATION", font=FONTS["h3"], foreground=COLORS["primary"]).pack(anchor=tk.W, pady=(5, 10))

        prof_box = ttk.Frame(form, style="Card.TFrame", padding=15)
        prof_box.pack(fill=tk.X, pady=(0, 15))

        if self.role == "Admin":
            self._build_admin_profile_fields(prof_box)
        elif self.role == "Teacher":
            self._build_teacher_profile_fields(prof_box)
        elif self.role == "Student":
            self._build_student_profile_fields(prof_box)
        elif self.role == "Parent":
            self._build_parent_profile_fields(prof_box)

        # --- SECTION 2: PASSWORD CHANGE ---
        ttk.Label(form, text="🔒 SECURITY & PASSWORD CHANGE", font=FONTS["h3"], foreground=COLORS["primary"]).pack(anchor=tk.W, pady=(10, 10))

        pwd_box = ttk.Frame(form, style="Card.TFrame", padding=15)
        pwd_box.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(pwd_box, text="Current Password:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=6)
        self.entry_curr_pwd = ttk.Entry(pwd_box, show="*", width=30)
        self.entry_curr_pwd.grid(row=0, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(pwd_box, text="New Password:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=6)
        self.entry_new_pwd = ttk.Entry(pwd_box, show="*", width=30)
        self.entry_new_pwd.grid(row=1, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(pwd_box, text="Confirm New Password:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=6)
        self.entry_confirm_pwd = ttk.Entry(pwd_box, show="*", width=30)
        self.entry_confirm_pwd.grid(row=2, column=1, sticky="w", pady=6, padx=10)

        # --- SCHOOL WORKING TIMINGS SECTION ---
        timings_box = ttk.LabelFrame(form, text=" 🕒 Official School Working Timings ", padding=15, style="Card.TLabelframe")
        timings_box.pack(fill=tk.X, pady=(0, 15))

        curr_timings = self.db.get_school_timings()
        is_admin = self.role == "Admin"

        def notify_protected_time(event=None):
            if not is_admin:
                messagebox.showwarning("Protected Timing", "You are not allowed to change this time. Only Admin can change the official school working time.")

        ttk.Label(timings_box, text="Official Start Time:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=6)
        self.entry_start_time = ttk.Entry(timings_box, width=15)
        self.entry_start_time.insert(0, curr_timings["start_time"])
        if not is_admin:
            self.entry_start_time.config(state="readonly")
            self.entry_start_time.bind("<Button-1>", notify_protected_time)
        self.entry_start_time.grid(row=0, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(timings_box, text="Official End Time:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=0, column=2, sticky="w", pady=6, padx=(15, 0))
        self.entry_end_time = ttk.Entry(timings_box, width=15)
        self.entry_end_time.insert(0, curr_timings["end_time"])
        if not is_admin:
            self.entry_end_time.config(state="readonly")
            self.entry_end_time.bind("<Button-1>", notify_protected_time)
        self.entry_end_time.grid(row=0, column=3, sticky="w", pady=6, padx=10)

        if is_admin:
            def save_timings():
                st = self.entry_start_time.get().strip()
                et = self.entry_end_time.get().strip()
                if st and et:
                    self.db.update_school_timings(st, et)
                    messagebox.showinfo("Settings Saved", f"✓ School Official Timings updated:\nStart Time: {st}\nEnd Time: {et}")

            ttk.Button(timings_box, text="💾 Save Timings", command=save_timings).grid(row=0, column=4, padx=15)
        else:
            ttk.Button(timings_box, text="💾 Save Timings", command=notify_protected_time).grid(row=0, column=4, padx=15)

        # --- BOTTOM ACTIONS ---
        btn_bar = ttk.Frame(form)
        btn_bar.pack(fill=tk.X, pady=(15, 10))

        btn_save = ttk.Button(btn_bar, text="💾 Save Changes", style="Primary.TButton", command=self.save_settings)
        btn_save.pack(side=tk.RIGHT, padx=5)

        if self.on_cancel:
            btn_cancel = ttk.Button(btn_bar, text="Cancel / Back", command=self.on_cancel)
            btn_cancel.pack(side=tk.RIGHT, padx=5)

    def _build_admin_profile_fields(self, f):
        ttk.Label(f, text="Username:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=6)
        self.entry_username = ttk.Entry(f, width=30)
        self.entry_username.insert(0, self.user_data['username'])
        self.entry_username.grid(row=0, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(f, text="Role:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Label(f, text="Administrator (Full Access)", font=FONTS["body"], style="Card.TLabel", foreground=COLORS["primary"]).grid(row=1, column=1, sticky="w", pady=6, padx=10)

    def _build_teacher_profile_fields(self, f):
        p = self.profile_record or {}
        
        ttk.Label(f, text="Teacher ID:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Label(f, text=f"{p.get('teacher_id', 'N/A')} (Protected ID)", font=FONTS["body_bold"], style="Card.TLabel", foreground=COLORS["text_muted"]).grid(row=0, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(f, text="Full Name *:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=6)
        self.entry_name = ttk.Entry(f, width=30)
        self.entry_name.insert(0, p.get('name', ''))
        self.entry_name.grid(row=1, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(f, text="Phone Number *:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=6)
        self.entry_phone = ttk.Entry(f, width=30)
        self.entry_phone.insert(0, p.get('phone', ''))
        self.entry_phone.grid(row=2, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(f, text="Email Address:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=6)
        self.entry_email = ttk.Entry(f, width=30)
        self.entry_email.insert(0, p.get('email', ''))
        self.entry_email.grid(row=3, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(f, text="Address:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=4, column=0, sticky="w", pady=6)
        self.entry_address = ttk.Entry(f, width=35)
        self.entry_address.insert(0, p.get('address', ''))
        self.entry_address.grid(row=4, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(f, text="Department / Designation:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=5, column=0, sticky="w", pady=6)
        ttk.Label(f, text=f"{p.get('department', 'N/A')} - {p.get('designation', 'N/A')}", font=FONTS["body"], style="Card.TLabel").grid(row=5, column=1, sticky="w", pady=6, padx=10)

    def _build_student_profile_fields(self, f):
        p = self.profile_record or {}

        ttk.Label(f, text="Student ID:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Label(f, text=f"{p.get('student_id', 'N/A')} (Protected ID)", font=FONTS["body_bold"], style="Card.TLabel", foreground=COLORS["text_muted"]).grid(row=0, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(f, text="Full Name:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Label(f, text=f"{p.get('name', 'N/A')}", font=FONTS["body"], style="Card.TLabel").grid(row=1, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(f, text="Class / Course:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=6)
        ttk.Label(f, text=f"{p.get('current_class', 'N/A')} | {p.get('course', 'N/A')}", font=FONTS["body"], style="Card.TLabel").grid(row=2, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(f, text="Phone Number:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=6)
        self.entry_phone = ttk.Entry(f, width=30)
        self.entry_phone.insert(0, p.get('phone', ''))
        self.entry_phone.grid(row=3, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(f, text="Email Address:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=4, column=0, sticky="w", pady=6)
        self.entry_email = ttk.Entry(f, width=30)
        self.entry_email.insert(0, p.get('email', ''))
        self.entry_email.grid(row=4, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(f, text="Address:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=5, column=0, sticky="w", pady=6)
        self.entry_address = ttk.Entry(f, width=35)
        self.entry_address.insert(0, p.get('address', ''))
        self.entry_address.grid(row=5, column=1, sticky="w", pady=6, padx=10)

    def _build_parent_profile_fields(self, f):
        p = self.profile_record or {}

        ttk.Label(f, text="Parent ID Code:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Label(f, text=f"{p.get('parent_id_code', 'N/A')} (Protected Code)", font=FONTS["body_bold"], style="Card.TLabel", foreground=COLORS["text_muted"]).grid(row=0, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(f, text="Parent Full Name *:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=6)
        self.entry_name = ttk.Entry(f, width=30)
        self.entry_name.insert(0, p.get('name', ''))
        self.entry_name.grid(row=1, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(f, text="Phone Number *:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=6)
        self.entry_phone = ttk.Entry(f, width=30)
        self.entry_phone.insert(0, p.get('phone', ''))
        self.entry_phone.grid(row=2, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(f, text="Email Address:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=6)
        self.entry_email = ttk.Entry(f, width=30)
        self.entry_email.insert(0, p.get('email', ''))
        self.entry_email.grid(row=3, column=1, sticky="w", pady=6, padx=10)

        ttk.Label(f, text="Address:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=4, column=0, sticky="w", pady=6)
        self.entry_address = ttk.Entry(f, width=35)
        self.entry_address.insert(0, p.get('address', ''))
        self.entry_address.grid(row=4, column=1, sticky="w", pady=6, padx=10)

        children = self.db.get_parent_students(self.user_id)
        child_str = ", ".join([f"{c['name']} ({c['student_id']})" for c in children]) if children else "N/A"

        ttk.Label(f, text="Linked Children:", font=FONTS["body_bold"], style="Card.TLabel").grid(row=5, column=0, sticky="w", pady=6)
        ttk.Label(f, text=child_str, font=FONTS["body"], style="Card.TLabel", foreground=COLORS["primary"], wraplength=350, justify="left").grid(row=5, column=1, sticky="w", pady=6, padx=10)

    def save_settings(self):
        """Validates input, updates SQLite database records, and changes password if requested."""
        changes_applied = False

        # --- 1. HANDLE PASSWORD CHANGE ---
        curr_pwd = self.entry_curr_pwd.get()
        new_pwd = self.entry_new_pwd.get()
        confirm_pwd = self.entry_confirm_pwd.get()

        if new_pwd or confirm_pwd or curr_pwd:
            if not curr_pwd:
                messagebox.showwarning("Validation Error", "Please enter your Current Password to make security changes.")
                return
            if not new_pwd or not confirm_pwd:
                messagebox.showwarning("Validation Error", "New Password and Confirm New Password cannot be empty.")
                return
            if new_pwd != confirm_pwd:
                messagebox.showerror("Validation Error", "New Password and Confirm New Password do not match.")
                return
            if len(new_pwd) < 4:
                messagebox.showwarning("Validation Error", "New Password must be at least 4 characters long.")
                return

            ok_pwd, msg_pwd = self.db.change_user_password(self.user_id, curr_pwd, new_pwd)
            if not ok_pwd:
                messagebox.showerror("Security Error", msg_pwd)
                return
            changes_applied = True

        # --- 2. HANDLE ROLE PROFILE UPDATE ---
        if self.role == "Admin":
            new_username = self.entry_username.get().strip()
            if not new_username:
                messagebox.showwarning("Validation Error", "Username cannot be empty.")
                return
            if new_username.lower() != self.user_data['username'].lower():
                ok_u, msg_u = self.db.update_user_username(self.user_id, new_username)
                if not ok_u:
                    messagebox.showerror("Error", msg_u)
                    return
                self.user_data['username'] = new_username
                changes_applied = True

        elif self.role == "Teacher" and self.profile_record:
            name = self.entry_name.get().strip()
            phone = self.entry_phone.get().strip()
            email = self.entry_email.get().strip()
            address = self.entry_address.get().strip()

            if not name or not phone:
                messagebox.showwarning("Validation Error", "Name and Phone Number are required.")
                return
            if not validate_phone(phone):
                messagebox.showwarning("Validation Error", "Phone number must contain exactly 10 digits.")
                return
            if email and not validate_email(email):
                messagebox.showwarning("Validation Error", "Please enter a valid Email Address.")
                return

            teacher_data = {
                "name": name,
                "phone": phone,
                "email": email,
                "address": address,
                "department": self.profile_record.get('department', ''),
                "designation": self.profile_record.get('designation', ''),
                "joining_date": self.profile_record.get('joining_date', '')
            }
            self.db.update_teacher(self.profile_record['teacher_id'], teacher_data)
            changes_applied = True

        elif self.role == "Student" and self.profile_record:
            phone = self.entry_phone.get().strip()
            email = self.entry_email.get().strip()
            address = self.entry_address.get().strip()

            if phone and not validate_phone(phone):
                messagebox.showwarning("Validation Error", "Phone number must contain exactly 10 digits.")
                return
            if email and not validate_email(email):
                messagebox.showwarning("Validation Error", "Please enter a valid Email Address.")
                return

            student_data = dict(self.profile_record)
            student_data['phone'] = phone
            student_data['email'] = email
            student_data['address'] = address

            self.db.update_student(self.profile_record['student_id'], student_data)
            changes_applied = True

        elif self.role == "Parent" and self.profile_record:
            name = self.entry_name.get().strip()
            phone = self.entry_phone.get().strip()
            email = self.entry_email.get().strip()
            address = self.entry_address.get().strip()

            if not name or not phone:
                messagebox.showwarning("Validation Error", "Name and Phone Number are required.")
                return
            if not validate_phone(phone):
                messagebox.showwarning("Validation Error", "Phone number must contain exactly 10 digits.")
                return
            if email and not validate_email(email):
                messagebox.showwarning("Validation Error", "Please enter a valid Email Address.")
                return

            parent_data = {
                "name": name,
                "phone": phone,
                "email": email,
                "address": address
            }
            self.db.update_parent_profile(self.user_id, parent_data, self.profile_record.get('parent_id_code', ''))
            changes_applied = True

        # Clear password fields
        self.entry_curr_pwd.delete(0, tk.END)
        self.entry_new_pwd.delete(0, tk.END)
        self.entry_confirm_pwd.delete(0, tk.END)

        if changes_applied:
            messagebox.showinfo("Success", "Settings updated successfully.")
            self._load_profile_data()
        else:
            messagebox.showinfo("Notice", "No changes were made.")
