import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DBManager
from gui.theme import COLORS, FONTS
from utils.validators import validate_email, validate_phone, validate_study_hours

class RoleSelectModal(tk.Toplevel):
    """Modal to choose account registration role (Teacher, Student, Parent)."""
    def __init__(self, parent_win, db_manager: DBManager):
        super().__init__(parent_win)
        self.parent_win = parent_win
        self.db = db_manager

        self.title("Select Account Type")
        self.geometry("420x360")
        self.resizable(False, False)
        self.transient(parent_win)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        main = ttk.Frame(self, padding=25)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="✨ Create New Account", font=FONTS["h1"]).pack(anchor=tk.W, pady=(0, 4))
        ttk.Label(main, text="Please select your role to open the registration form:", style="Subtitle.TLabel").pack(anchor=tk.W, pady=(0, 20))

        roles = [
            ("👨‍🏫 Teacher Account", "Teacher", "#0d9488"),
            ("🎓 Student Account", "Student", "#7c3aed"),
            ("👨‍👩‍👧 Parent Account", "Parent", "#059669")
        ]

        for text, role_key, color in roles:
            btn = tk.Button(
                main,
                text=text,
                font=("Segoe UI", 11, "bold"),
                bg=color,
                fg="#ffffff",
                activebackground="#1e293b",
                activeforeground="#ffffff",
                bd=0,
                cursor="hand2",
                command=lambda r=role_key: self.select_role(r)
            )
            btn.pack(fill=tk.X, pady=6, ipady=8)

        btn_back = ttk.Button(main, text="⬅️ Back", command=self.destroy)
        btn_back.pack(fill=tk.X, pady=(15, 0))

    def select_role(self, role: str):
        self.grab_release()
        self.destroy()
        AccountRegistrationWindow(self.parent_win, self.db, role)


class AdminSetupDialog(tk.Toplevel):
    """First-Time Admin Account Setup Dialog."""
    def __init__(self, parent_win: tk.Tk, db_manager: DBManager, on_complete_callback=None):
        super().__init__(parent_win)
        self.parent_win = parent_win
        self.db = db_manager
        self.on_complete = on_complete_callback

        self.title("First-Time Admin Account Setup")
        self.geometry("460x480")
        self.resizable(False, False)
        self.transient(parent_win)
        self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self.on_close_attempt)
        self._build_ui()

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding=25)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="🛡️ First-Time Admin Setup", font=FONTS["h1"]).pack(anchor=tk.W, pady=(0, 4))
        ttk.Label(main_frame, text="No Admin account detected in SQLite. Create primary Administrator credentials to continue.", style="Subtitle.TLabel", wraplength=400, justify="left").pack(anchor=tk.W, pady=(0, 15))

        ttk.Label(main_frame, text="Admin Full Name *:", font=FONTS["body_bold"]).pack(anchor=tk.W, pady=(4, 2))
        self.entry_name = ttk.Entry(main_frame)
        self.entry_name.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(main_frame, text="Admin Username *:", font=FONTS["body_bold"]).pack(anchor=tk.W, pady=(4, 2))
        self.entry_username = ttk.Entry(main_frame)
        self.entry_username.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(main_frame, text="Password *:", font=FONTS["body_bold"]).pack(anchor=tk.W, pady=(4, 2))
        self.entry_pwd = ttk.Entry(main_frame, show="*")
        self.entry_pwd.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(main_frame, text="Confirm Password *:", font=FONTS["body_bold"]).pack(anchor=tk.W, pady=(4, 2))
        self.entry_confirm = ttk.Entry(main_frame, show="*")
        self.entry_confirm.pack(fill=tk.X, pady=(0, 15))

        btn = ttk.Button(main_frame, text="✅ Save & Create Admin Account", style="Primary.TButton", command=self.save_admin)
        btn.pack(fill=tk.X, ipady=5)

    def on_close_attempt(self):
        if not self.db.has_admin():
            messagebox.showwarning("Admin Required", "A primary System Admin account must be created before accessing the system.")
        else:
            self.destroy()

    def save_admin(self):
        name = self.entry_name.get().strip()
        u = self.entry_username.get().strip()
        p = self.entry_pwd.get()
        c = self.entry_confirm.get()

        if not name or not u or not p or not c:
            messagebox.showwarning("Validation Error", "Admin Name, Username, Password, and Confirm Password cannot be empty.")
            return

        if len(p) < 4:
            messagebox.showwarning("Validation Error", "Password must be at least 4 characters long.")
            return

        if p != c:
            messagebox.showerror("Validation Error", "Password and Confirm Password do not match.")
            return

        if self.db.is_username_exists(u):
            messagebox.showerror("Duplicate Error", f"Username '{u}' is already taken. Please enter a different Username.")
            return

        user_id = self.db.create_user(u, p, "Admin")
        if user_id:
            messagebox.showinfo("Success", f"System Admin Account '{name}' ({u}) created and saved to SQLite!\n\nYou can now log in using your newly created Admin credentials.")
            self.grab_release()
            self.destroy()

            if self.on_complete:
                self.on_complete(u)
            else:
                from gui.login import LoginWindow
                login_win = LoginWindow(self.parent_win, self.db, "Admin")
                login_win.entry_username.delete(0, tk.END)
                login_win.entry_username.insert(0, u)
        else:
            messagebox.showerror("Database Error", "Failed to create Admin account in SQLite database.")


class AccountRegistrationWindow(tk.Toplevel):
    """Complete Account Registration Form for Teacher, Student, and Parent roles."""
    def __init__(self, welcome_win: tk.Tk, db_manager: DBManager, role: str = "Student"):
        super().__init__(welcome_win)
        self.welcome_win = welcome_win
        self.db = db_manager
        self.role = role

        self.title(f"{role} Registration - Student Management System")
        self.geometry("650x750")
        self.minsize(600, 680)
        self.transient(welcome_win)
        self.grab_set()

        self._entries = {}
        self.child_entries = [] # for Parent multi-child entries
        self._build_ui()

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(main_frame)
        header.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header, text=f"📝 {self.role} Account Registration", font=FONTS["h1"]).pack(side=tk.LEFT)
        ttk.Label(main_frame, text="Complete all required fields. Username and IDs must be unique.", style="Subtitle.TLabel").pack(anchor=tk.W, pady=(0, 10))

        container = ttk.Frame(main_frame)
        container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        canvas = tk.Canvas(container, bg=COLORS["bg_main"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.form_frame = ttk.Frame(canvas)

        self.form_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.form_frame, anchor="nw", width=580)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if self.role == "Teacher":
            self._build_teacher_fields()
        elif self.role == "Student":
            self._build_student_fields()
        elif self.role == "Parent":
            self._build_parent_fields()

        btn_bar = ttk.Frame(main_frame)
        btn_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

        btn_back = ttk.Button(btn_bar, text="⬅️ Back", command=self.on_back)
        btn_back.pack(side=tk.LEFT, padx=5)

        btn_reset = ttk.Button(btn_bar, text="🔄 Clear / Reset", command=self.reset_fields)
        btn_reset.pack(side=tk.LEFT, padx=5)

        btn_submit = ttk.Button(btn_bar, text="✨ Register / Create Account", style="Primary.TButton", command=self.do_register)
        btn_submit.pack(side=tk.RIGHT, padx=5)

    def _add_field(self, parent_frame, label_text: str, key_name: str, show_char: str = None, is_combo: bool = False, combo_vals: list = None, default_val: str = "", note_text: str = None):
        row_frame = ttk.Frame(parent_frame)
        row_frame.pack(fill=tk.X, pady=4)

        lbl = ttk.Label(row_frame, text=label_text, font=FONTS["body_bold"])
        lbl.pack(anchor=tk.W)

        if note_text:
            note_lbl = ttk.Label(row_frame, text=note_text, font=FONTS["small"], foreground="#0284c7", wraplength=450)
            note_lbl.pack(anchor=tk.W, pady=(1, 3))

        if is_combo:
            widget = ttk.Combobox(row_frame, values=combo_vals or [], state="readonly")
            if combo_vals:
                widget.set(default_val or combo_vals[0])
            widget.pack(fill=tk.X, pady=(2, 0))
        elif show_char:
            entry_container = ttk.Frame(row_frame)
            entry_container.pack(fill=tk.X, pady=(2, 0))

            widget = ttk.Entry(entry_container, show=show_char)
            if default_val:
                widget.insert(0, default_val)
            widget.pack(side=tk.LEFT, fill=tk.X, expand=True)

            def make_toggle_cmd(w, btn):
                def toggle():
                    if w.cget("show") == show_char:
                        w.config(show="")
                        btn.config(text="🙈 Hide")
                    else:
                        w.config(show=show_char)
                        btn.config(text="👁️ Show")
                return toggle

            btn_toggle = ttk.Button(entry_container, text="👁️ Show", width=8)
            btn_toggle.config(command=make_toggle_cmd(widget, btn_toggle))
            btn_toggle.pack(side=tk.RIGHT, padx=(5, 0))
        else:
            widget = ttk.Entry(row_frame)
            if default_val:
                widget.insert(0, default_val)
            widget.pack(fill=tk.X, pady=(2, 0))

        self._entries[key_name] = widget

    def _build_teacher_fields(self):
        f = self.form_frame
        ttk.Label(f, text="ACCOUNT & CREDENTIALS", font=FONTS["h3"], foreground=COLORS["primary"]).pack(anchor=tk.W, pady=(5, 5))
        self._add_field(f, "Username / Login ID (Unique) *:", "username")
        self._add_field(f, "Password *:", "password", show_char="*")
        self._add_field(f, "Confirm Password *:", "confirm_password", show_char="*")
        self._add_field(
            f,
            "Favourite Person Name *:",
            "favourite_person",
            note_text="Enter the name of your favourite person. This will be used to reset your password if you forget it."
        )

        ttk.Label(f, text="PERSONAL & PROFESSIONAL DETAILS", font=FONTS["h3"], foreground=COLORS["primary"]).pack(anchor=tk.W, pady=(15, 5))
        self._add_field(f, "Teacher ID (Unique) *:", "teacher_id")
        self._add_field(f, "Full Name *:", "name")
        self._add_field(f, "Phone Number *:", "phone")
        self._add_field(f, "Email Address *:", "email")
        self._add_field(f, "Address:", "address")
        self._add_field(f, "Department *:", "department", default_val="Computer Science & Engineering")
        self._add_field(f, "Designation:", "designation", default_val="Assistant Professor")
        self._add_field(f, "Joining Date (YYYY-MM-DD):", "joining_date", default_val="2024-01-15")

    def _build_student_fields(self):
        f = self.form_frame

        ttk.Label(f, text="EDUCATION TYPE", font=FONTS["h3"], foreground=COLORS["primary"]).pack(anchor=tk.W, pady=(5, 5))
        
        row_edu = ttk.Frame(f)
        row_edu.pack(fill=tk.X, pady=4)
        ttk.Label(row_edu, text="Currently Studying In *:", font=FONTS["body_bold"]).pack(anchor=tk.W)
        self.combo_edu_type = ttk.Combobox(row_edu, values=["School", "College"], state="readonly", font=FONTS["body"])
        self.combo_edu_type.set("School")
        self.combo_edu_type.pack(fill=tk.X, pady=(2, 0))
        self.combo_edu_type.bind("<<ComboboxSelected>>", self._on_edu_type_changed)

        ttk.Label(f, text="ACCOUNT CREDENTIALS", font=FONTS["h3"], foreground=COLORS["primary"]).pack(anchor=tk.W, pady=(15, 5))
        self._add_field(f, "Username / Login ID (Unique) *:", "username")
        self._add_field(f, "Password *:", "password", show_char="*")
        self._add_field(f, "Confirm Password *:", "confirm_password", show_char="*")
        self._add_field(
            f,
            "Favourite Person Name *:",
            "favourite_person",
            note_text="Enter the name of your favourite person. This will be used to reset your password if you forget it."
        )

        ttk.Label(f, text="STUDENT PERSONAL & ACADEMIC DETAILS", font=FONTS["h3"], foreground=COLORS["primary"]).pack(anchor=tk.W, pady=(15, 5))
        self._add_field(f, "Full Name *:", "name")
        self._add_field(f, "Email Address *:", "email")
        self._add_field(f, "Phone Number *:", "phone")
        self._add_field(f, "Gender *:", "gender", is_combo=True, combo_vals=["Male", "Female", "Other"])
        self._add_field(f, "Date of Birth (YYYY-MM-DD) *:", "dob", default_val="2003-06-15")
        self._add_field(f, "Full Address *:", "address")

        # Container for dynamic School / College fields
        self.edu_dynamic_container = ttk.Frame(f)
        self.edu_dynamic_container.pack(fill=tk.X, pady=5)
        self._build_dynamic_edu_fields("School")

        ttk.Label(f, text="PARENT / GUARDIAN DETAILS", font=FONTS["h3"], foreground=COLORS["primary"]).pack(anchor=tk.W, pady=(15, 5))
        self._add_field(f, "Guardian Name:", "guardian_name")
        self._add_field(f, "Father Name *:", "father_name")
        self._add_field(f, "Father Phone Number *:", "parent_phone")
        self._add_field(f, "Mother Name:", "mother_name")
        self._add_field(f, "Mother Phone Number:", "mother_phone")
        self._add_field(f, "Parent Occupation:", "parent_occupation")
        self._add_field(f, "Emergency Contact Number:", "emergency_contact")
        self._add_field(f, "Relationship with Student:", "relationship", is_combo=True, combo_vals=["Father", "Mother", "Guardian"])
        self._add_field(f, "Study Hours Per Day *:", "study_hours", default_val="3.5")

    def _on_edu_type_changed(self, event=None):
        edu_type = self.combo_edu_type.get()
        self._build_dynamic_edu_fields(edu_type)

    def _build_dynamic_edu_fields(self, edu_type: str):
        # Clear existing dynamic fields
        for widget in self.edu_dynamic_container.winfo_children():
            widget.destroy()

        # Remove previous keys from self._entries if any
        dynamic_keys = ["school_name", "college_name", "student_id", "enrollment_number", "current_class", "section", "course", "semester", "year", "admission_date"]
        for key in dynamic_keys:
            if key in self._entries:
                del self._entries[key]

        if edu_type == "School":
            self._add_field(self.edu_dynamic_container, "School Name *:", "school_name")
            self._add_field(self.edu_dynamic_container, "Class *:", "current_class", default_val="10")
            self._add_field(self.edu_dynamic_container, "Section:", "section", default_val="A")
            self._add_field(self.edu_dynamic_container, "Admission Date (YYYY-MM-DD) *:", "admission_date", default_val="2024-08-01")
            self._add_field(self.edu_dynamic_container, "Unique Student ID *:", "student_id")
        else: # College
            self._add_field(self.edu_dynamic_container, "College Name *:", "college_name")
            self._add_field(self.edu_dynamic_container, "Unique Enrollment Number *:", "enrollment_number")

            # Course / Program with type-your-own support (state="normal")
            row_course = ttk.Frame(self.edu_dynamic_container)
            row_course.pack(fill=tk.X, pady=4)
            ttk.Label(row_course, text="Course / Program *:", font=FONTS["body_bold"]).pack(anchor=tk.W)
            ttk.Label(row_course, text="Select from list or type your own custom course name.", font=FONTS["small"], foreground="#0284c7").pack(anchor=tk.W, pady=(1, 3))
            course_vals = [
                "B.Tech Computer Science", "B.Tech Information Technology", "B.Tech AI & Data Science",
                "B.Sc Computer Science", "B.Com", "B.A", "B.Sc", "BBA", "BCA", "M.Tech", "MBA", "MCA"
            ]
            widget_course = ttk.Combobox(row_course, values=course_vals, state="normal")
            widget_course.set("B.Tech Computer Science")
            widget_course.pack(fill=tk.X, pady=(2, 0))
            self._entries["course"] = widget_course

            # Semester and Year - Editable Text Input Fields
            self._add_field(self.edu_dynamic_container, "Semester *:", "semester")
            self._add_field(self.edu_dynamic_container, "Year:", "year")
            self._add_field(self.edu_dynamic_container, "Admission Date (YYYY-MM-DD) *:", "admission_date", default_val="2024-08-01")

    def _build_parent_fields(self):
        f = self.form_frame
        ttk.Label(f, text="ACCOUNT CREDENTIALS", font=FONTS["h3"], foreground=COLORS["primary"]).pack(anchor=tk.W, pady=(5, 5))
        self._add_field(f, "Username / Login ID (Unique) *:", "username")
        self._add_field(f, "Password *:", "password", show_char="*")
        self._add_field(f, "Confirm Password *:", "confirm_password", show_char="*")
        self._add_field(
            f,
            "Favourite Person Name *:",
            "favourite_person",
            note_text="Enter the name of your favourite person. This will be used to reset your password if you forget it."
        )

        ttk.Label(f, text="PARENT / GUARDIAN DETAILS", font=FONTS["h3"], foreground=COLORS["primary"]).pack(anchor=tk.W, pady=(15, 5))
        self._add_field(f, "Parent ID (Unique Code) *:", "parent_id_code")
        self._add_field(f, "Parent Full Name *:", "name")

        # Link with Child Student ID Section
        ttk.Label(f, text="LINK WITH CHILD STUDENT ID", font=FONTS["h3"], foreground=COLORS["primary"]).pack(anchor=tk.W, pady=(15, 5))
        
        num_frame = ttk.Frame(f)
        num_frame.pack(fill=tk.X, pady=4)
        ttk.Label(num_frame, text="How many children do you have?", font=FONTS["body_bold"]).pack(anchor=tk.W)
        
        self.combo_num_children = ttk.Combobox(num_frame, values=["1", "2", "3", "4", "5"], state="readonly", width=15)
        self.combo_num_children.set("1")
        self.combo_num_children.pack(anchor=tk.W, pady=(2, 5))
        self.combo_num_children.bind("<<ComboboxSelected>>", self._on_num_children_changed)

        self.children_container = ttk.Frame(f)
        self.children_container.pack(fill=tk.X, pady=5)

        ttk.Label(f, text="CONTACT & OTHER DETAILS", font=FONTS["h3"], foreground=COLORS["primary"]).pack(anchor=tk.W, pady=(15, 5))
        self._add_field(f, "Relationship:", "relationship", is_combo=True, combo_vals=["Father", "Mother", "Guardian"])
        self._add_field(f, "Phone Number *:", "phone")
        self._add_field(f, "Email Address:", "email")
        self._add_field(f, "Address:", "address")
        
        self._on_num_children_changed()


    def _on_num_children_changed(self, event=None):
        for widget in self.children_container.winfo_children():
            widget.destroy()
        
        num_str = self.combo_num_children.get()
        try:
            count = int(num_str)
        except ValueError:
            count = 1

        self.child_entries = []

        for i in range(count):
            slot_idx = i
            card = ttk.Frame(self.children_container, style="Card.TFrame", padding=10)
            card.pack(fill=tk.X, pady=6)

            ttk.Label(card, text=f"Child {i+1} Details", font=FONTS["body_bold"], style="Card.TLabel").pack(anchor=tk.W, pady=(0, 4))
            
            row_edu = ttk.Frame(card, style="Card.TFrame")
            row_edu.pack(fill=tk.X, pady=(0, 6))

            ttk.Label(row_edu, text="Education Type: ", font=FONTS["body_bold"], style="Card.TLabel").pack(side=tk.LEFT)
            combo_edu = ttk.Combobox(row_edu, values=["School", "College", "Both"], state="readonly", width=12)
            combo_edu.set("School")
            combo_edu.pack(side=tk.LEFT, padx=5)

            fields_frame = ttk.Frame(card, style="Card.TFrame")
            fields_frame.pack(fill=tk.X, pady=2)

            lbl_status = ttk.Label(card, text="Waiting for verification...", font=FONTS["small"], style="Card.TLabel", foreground=COLORS["text_muted"])
            lbl_status.pack(anchor=tk.W, pady=(4, 0))

            slot_data = {
                "combo_edu": combo_edu,
                "fields_frame": fields_frame,
                "entry_sid": None,
                "entry_enr": None,
                "lbl_status": lbl_status,
                "verified_student": None
            }

            def render_fields(s_data=slot_data, idx=slot_idx):
                for w in s_data["fields_frame"].winfo_children():
                    w.destroy()

                edu_choice = s_data["combo_edu"].get()
                s_data["entry_sid"] = None
                s_data["entry_enr"] = None

                r = ttk.Frame(s_data["fields_frame"], style="Card.TFrame")
                r.pack(fill=tk.X)

                if edu_choice in ["School", "Both"]:
                    ttk.Label(r, text="Student ID: ", font=FONTS["body"], style="Card.TLabel").pack(side=tk.LEFT)
                    e_sid = ttk.Entry(r, width=15)
                    e_sid.pack(side=tk.LEFT, padx=(2, 10))
                    s_data["entry_sid"] = e_sid

                if edu_choice in ["College", "Both"]:
                    ttk.Label(r, text="Enrollment Number: ", font=FONTS["body"], style="Card.TLabel").pack(side=tk.LEFT)
                    e_enr = ttk.Entry(r, width=15)
                    e_enr.pack(side=tk.LEFT, padx=(2, 10))
                    s_data["entry_enr"] = e_enr

                btn_verify = ttk.Button(r, text="Verify", command=lambda slot_i=idx: self._verify_child_slot(slot_i))
                btn_verify.pack(side=tk.LEFT, padx=5)

            render_fields()

            combo_edu.bind("<<ComboboxSelected>>", lambda e, r_func=render_fields: r_func())

            self.child_entries.append(slot_data)

    def _verify_child_slot(self, idx: int):
        if idx >= len(self.child_entries):
            return

        slot = self.child_entries[idx]
        edu_choice = slot["combo_edu"].get()
        entry_sid = slot.get("entry_sid")
        entry_enr = slot.get("entry_enr")

        sid = entry_sid.get().strip() if entry_sid else ""
        enr = entry_enr.get().strip() if entry_enr else ""

        if edu_choice == "School":
            if not sid:
                slot["lbl_status"].config(text="❌ Please enter a Student ID.", foreground=COLORS["danger"])
                slot["verified_student"] = None
                return
            lookup_id = sid
        elif edu_choice == "College":
            if not enr:
                slot["lbl_status"].config(text="❌ Please enter an Enrollment Number.", foreground=COLORS["danger"])
                slot["verified_student"] = None
                return
            lookup_id = enr
        else: # Both
            if not sid and not enr:
                slot["lbl_status"].config(text="❌ Please enter Student ID or Enrollment Number.", foreground=COLORS["danger"])
                slot["verified_student"] = None
                return
            lookup_id = sid or enr

        # Check duplicate lookup in other child slots
        for other_idx, other_slot in enumerate(self.child_entries):
            if other_idx != idx:
                o_sid = other_slot["entry_sid"].get().strip() if other_slot.get("entry_sid") else ""
                o_enr = other_slot["entry_enr"].get().strip() if other_slot.get("entry_enr") else ""
                if (sid and ((o_sid and o_sid.lower() == sid.lower()) or (o_enr and o_enr.lower() == sid.lower()))) or \
                   (enr and ((o_sid and o_sid.lower() == enr.lower()) or (o_enr and o_enr.lower() == enr.lower()))):
                    slot["lbl_status"].config(text="❌ This child has already been selected.", foreground=COLORS["danger"])
                    slot["verified_student"] = None
                    return

        # Check in DB students table
        student = self.db.get_student(lookup_id)
        if not student and enr:
            student = self.db.get_student(enr)

        if student:
            s_id_disp = student.get("student_id", "")
            e_id_disp = student.get("enrollment_number", "")
            disp_id = f"ID: {s_id_disp}" if s_id_disp else f"Enr: {e_id_disp}"
            msg = f"✓ Student Found: {student['name']} | {disp_id} | Class/Course: {student.get('current_class') or student.get('course', 'N/A')}"
            slot["lbl_status"].config(text=msg, foreground=COLORS["success"])
            slot["verified_student"] = student
        else:
            slot["lbl_status"].config(text=f"❌ Student record not found for '{lookup_id}'.", foreground=COLORS["danger"])
            slot["verified_student"] = None

    def reset_fields(self):
        for widget in self._entries.values():
            if isinstance(widget, ttk.Entry):
                widget.delete(0, tk.END)

        if hasattr(self, 'child_entries'):
            for slot in self.child_entries:
                if slot.get("entry_sid"):
                    slot["entry_sid"].delete(0, tk.END)
                if slot.get("entry_enr"):
                    slot["entry_enr"].delete(0, tk.END)
                slot["lbl_status"].config(text="Waiting for verification...", foreground=COLORS["text_muted"])
                slot["verified_student"] = None

    def on_back(self):
        self.grab_release()
        self.destroy()
        from gui.login import LoginWindow
        LoginWindow(self.welcome_win, self.db, self.role)

    def do_register(self):
        data = {key: widget.get().strip() for key, widget in self._entries.items()}

        password = data.get("password", "")
        confirm = data.get("confirm_password", "")
        fav_person = data.get("favourite_person", "").strip()

        username = data.get("username", "").strip()
        if not username or not password or not confirm:
            messagebox.showwarning("Validation Error", "Username, Password, and Confirm Password are required fields.")
            return

        if not fav_person:
            messagebox.showwarning("Validation Error", "Favourite Person Name is required for password recovery.")
            return

        if password != confirm:
            messagebox.showerror("Validation Error", "Password and Confirm Password do not match.")
            return

        if len(password) < 4:
            messagebox.showwarning("Validation Error", "Password must be at least 4 characters long.")
            return

        if data.get("email") and not validate_email(data["email"]):
            messagebox.showwarning("Validation Error", "Please enter a valid Email Address (e.g. user@domain.com).")
            return

        if data.get("phone") and not validate_phone(data["phone"]):
            messagebox.showwarning("Validation Error", "Phone number must contain exactly 10 digits.")
            return

        if self.db.is_username_exists(username):
            messagebox.showerror("Duplicate Error", f"Username '{username}' already exists. Please choose another username.")
            return

        if self.role == "Teacher":
            tid = data.get("teacher_id", "")
            name = data.get("name", "")
            phone = data.get("phone", "")

            if not tid or not name or not phone:
                messagebox.showwarning("Validation Error", "Teacher ID, Name, and Phone Number are required.")
                return

            if self.db.is_teacher_id_exists(tid):
                messagebox.showerror("Duplicate Error", f"Teacher ID '{tid}' already exists in database.")
                return

            user_id = self.db.create_user(username, password, "Teacher", fav_person)
            if not user_id:
                messagebox.showerror("Database Error", "Failed to create user login credentials.")
                return

            ok = self.db.add_teacher({
                "teacher_id": tid,
                "name": name,
                "phone": phone,
                "email": data.get("email", ""),
                "address": data.get("address", ""),
                "department": data.get("department", ""),
                "designation": data.get("designation", ""),
                "joining_date": data.get("joining_date", "")
            }, user_id)

            if ok:
                messagebox.showinfo("Registration Successful", f"Teacher Account created successfully!\n\nUsername: {username}\nTeacher ID: {tid}\n\nYou can now log in immediately.")
                self._finish_registration(username)
            else:
                messagebox.showerror("Database Error", "Failed to save Teacher profile.")

        elif self.role == "Student":
            edu_type = self.combo_edu_type.get() if hasattr(self, 'combo_edu_type') else "School"

            # Common required fields
            name = data.get("name", "").strip()
            email = data.get("email", "").strip()
            phone = data.get("phone", "").strip()
            gender = data.get("gender", "Male").strip()
            dob = data.get("dob", "").strip()
            address = data.get("address", "").strip()
            father_name = data.get("father_name", "").strip()
            parent_phone = data.get("parent_phone", "").strip()
            study_hours = data.get("study_hours", "3.5").strip()

            if not name or not email or not phone or not dob or not address or not father_name or not parent_phone or not study_hours:
                messagebox.showwarning("Validation Error", "Please fill in all common required fields:\nFull Name, Email, Phone Number, Date of Birth, Address, Father Name, Father Phone, and Study Hours.")
                return

            if not validate_email(email):
                messagebox.showwarning("Validation Error", "Please enter a valid Email Address (e.g. user@domain.com).")
                return

            if not validate_phone(phone):
                messagebox.showwarning("Validation Error", "Student Phone Number must contain exactly 10 numeric digits.")
                return

            if not validate_phone(parent_phone):
                messagebox.showwarning("Validation Error", "Father Phone Number must contain exactly 10 numeric digits.")
                return

            mother_phone = data.get("mother_phone", "").strip()
            if mother_phone and not validate_phone(mother_phone):
                messagebox.showwarning("Validation Error", "Mother Phone Number must contain exactly 10 numeric digits.")
                return

            emergency_contact = data.get("emergency_contact", "").strip()
            if emergency_contact and not validate_phone(emergency_contact):
                messagebox.showwarning("Validation Error", "Emergency Contact Number must contain exactly 10 numeric digits.")
                return

            val_sh_ok, sh_msg = validate_study_hours(study_hours)
            if not val_sh_ok:
                messagebox.showwarning("Validation Error", sh_msg)
                return

            if edu_type == "School":
                sid = data.get("student_id", "").strip()
                school_name = data.get("school_name", "").strip()
                curr_class = data.get("current_class", "").strip()
                section = data.get("section", "").strip()
                admission_date = data.get("admission_date", "").strip()

                if not sid or not school_name or not curr_class or not admission_date:
                    messagebox.showwarning("Validation Error", "School Name, Class, Admission Date, and Student ID are required for School students.")
                    return

                if self.db.is_student_id_exists(sid):
                    messagebox.showerror("Duplicate Error", f"Student ID '{sid}' already exists in database.")
                    return

                username_to_create = username
                student_id_val = sid
                school_name_val = school_name
                enrollment_number_val = ""
                college_name_val = ""
                course_val = ""
                semester_val = ""
                year = ""

            else: # College
                enr = data.get("enrollment_number", "").strip()
                college_name = data.get("college_name", "").strip()
                course = data.get("course", "").strip()
                semester = data.get("semester", "").strip()
                year = data.get("year", "").strip()
                admission_date = data.get("admission_date", "").strip()

                if not enr or not college_name or not course or not semester or not admission_date:
                    messagebox.showwarning("Validation Error", "College Name, Enrollment Number, Course/Program, Semester, and Admission Date are required for College students.")
                    return

                if self.db.is_enrollment_number_exists(enr):
                    messagebox.showerror("Duplicate Error", f"Enrollment Number '{enr}' already exists in database.")
                    return

                username_to_create = username
                student_id_val = enr # Primary Key saved as Enrollment Number for College student
                enrollment_number_val = enr
                college_name_val = college_name
                course_val = course
                semester_val = f"{semester} ({year})" if year else semester
                school_name_val = ""
                curr_class = ""
                section = ""

            user_id = self.db.create_user(username_to_create, password, "Student", fav_person)
            if not user_id:
                messagebox.showerror("Database Error", "Failed to create user login credentials.")
                return

            mother_name = data.get("mother_name", "").strip()
            parent_email = data.get("parent_email", "").strip()
            guardian_name = data.get("guardian_name", "").strip()

            ok = self.db.add_student({
                "student_id": student_id_val,
                "name": name,
                "father_name": father_name,
                "mother_name": mother_name,
                "father_phone": parent_phone,
                "mother_phone": mother_phone,
                "parent_phone": parent_phone,
                "parent_email": parent_email,
                "guardian_phone": parent_phone,
                "guardian_email": parent_email,
                "dob": dob,
                "gender": gender,
                "phone": phone,
                "email": email,
                "address": address,
                "course": course_val if edu_type == "College" else "",
                "current_class": curr_class if edu_type == "School" else "",
                "section": section if edu_type == "School" else "",
                "admission_date": admission_date,
                "academic_year": year if year else data.get("academic_year", "2024-2025"),
                "study_hours": study_hours,
                "education_type": edu_type,
                "school_name": school_name_val if edu_type == "School" else "",
                "college_name": college_name_val if edu_type == "College" else "",
                "enrollment_number": enrollment_number_val if edu_type == "College" else "",
                "semester": semester_val if edu_type == "College" else "",
                "guardian_name": guardian_name
            }, user_id)

            if ok:
                if father_name or mother_name or parent_phone or mother_phone or parent_email:
                    p_name = father_name or mother_name or guardian_name or "Parent/Guardian"
                    parent_data = {
                        "student_id": student_id_val,
                        "name": p_name,
                        "mother_name": mother_name,
                        "phone": parent_phone,
                        "mother_phone": mother_phone,
                        "email": parent_email,
                        "occupation": data.get("parent_occupation", ""),
                        "emergency_contact": emergency_contact,
                        "relationship": data.get("relationship", "Father"),
                        "address": address
                    }
                    self.db.add_parent(parent_data)
                    self.db.auto_link_parent_account(student_id_val, parent_phone, parent_email, mother_phone)

                id_display = f"Student ID: {student_id_val}" if edu_type == "School" else f"Enrollment Number: {enrollment_number_val}"
                messagebox.showinfo("Registration Successful", f"Student Account created successfully!\n\nEducation Type: {edu_type}\n{id_display}\n\nYou can now log in immediately.")
                self._finish_registration(username_to_create)
            else:
                messagebox.showerror("Database Error", "Failed to save Student record.")

        elif self.role == "Parent":
            pid_code = data.get("parent_id_code", "").strip()
            name = data.get("name", "").strip()
            phone = data.get("phone", "").strip()

            if not pid_code:
                pid_code = f"PID_{phone}"

            if not name or not phone:
                messagebox.showwarning("Validation Error", "Parent Name and Phone are required.")
                return

            if not hasattr(self, 'child_entries') or not self.child_entries:
                messagebox.showwarning("Validation Error", "Please select at least 1 child and verify their Student ID.")
                return

            # Auto-run verify for any unverified slots
            verified_students = []
            for i, slot in enumerate(self.child_entries):
                sid = slot["entry_sid"].get().strip() if slot.get("entry_sid") else ""
                enr = slot["entry_enr"].get().strip() if slot.get("entry_enr") else ""
                if not sid and not enr:
                    messagebox.showwarning("Validation Error", f"Please enter Student ID / Enrollment Number for Child {i+1}.")
                    return
                self._verify_child_slot(i)
                if not slot["verified_student"]:
                    lookup_val = sid or enr
                    messagebox.showerror("Verification Failed", f"Child {i+1} credentials '{lookup_val}' could not be verified.\nPlease enter a valid Student ID or Enrollment Number.")
                    return
                verified_students.append(slot["verified_student"])

            user_id = self.db.create_user(username, password, "Parent", fav_person)
            if not user_id:
                messagebox.showerror("Database Error", "Failed to create user login credentials.")
                return

            # Save ALL verified child relationships
            saved_count = 0
            for student in verified_students:
                s_id = student.get("student_id") or student.get("enrollment_number")
                ok = self.db.add_parent({
                    "parent_id_code": pid_code,
                    "student_id": s_id,
                    "name": name,
                    "relationship": data.get("relationship", "Parent"),
                    "phone": phone,
                    "email": data.get("email", ""),
                    "address": data.get("address", "")
                }, user_id)
                if ok:
                    saved_count += 1
                    self.db.auto_link_parent_account(s_id, phone, data.get("email", ""))

            if saved_count > 0:
                child_names = "\n• ".join([f"{s['name']} (ID: {s.get('student_id') or s.get('enrollment_number')})" for s in verified_students])
                messagebox.showinfo(
                    "Registration Successful",
                    f"Parent Account created and linked to {saved_count} child(ren):\n• {child_names}\n\nUsername: {username}\nParent ID: {pid_code}\n\nYou can now log in immediately."
                )
                self._finish_registration(username)
            else:
                messagebox.showerror("Database Error", "Failed to save Parent profile.")

    def _finish_registration(self, prefill_username: str):
        self.grab_release()
        self.destroy()
        from gui.login import LoginWindow
        login_win = LoginWindow(self.welcome_win, self.db, self.role)
        login_win.entry_username.delete(0, tk.END)
        login_win.entry_username.insert(0, prefill_username)
