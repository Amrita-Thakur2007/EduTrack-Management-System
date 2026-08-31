import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DBManager
from gui.theme import COLORS, FONTS
from gui.marks_view import MarksEntryDialog
from gui.student_forms import StudentFormDialog
from gui.attendance_view import AttendanceViewFrame
from gui.charts_view import AnalyticsChartsFrame
from ml.prediction import PerformancePredictor

class WorkTimeSummaryDialog(tk.Toplevel):
    """Modal dialog displaying the Work Time Dashboard summary after teacher logout."""
    def __init__(self, parent, teacher_name: str, teacher_id: str, department: str, work_log: dict):
        super().__init__(parent)
        self.title("MY ATTENDANCE / WORK TIME DASHBOARD")
        self.geometry("540x500")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        from datetime import datetime
        today_display = datetime.now().strftime("%d-%m-%Y")

        date_val = work_log.get('date', today_display)
        try:
            if '-' in date_val and len(date_val.split('-')[0]) == 4:
                parts = date_val.split('-')
                date_val = f"{parts[2]}-{parts[1]}-{parts[0]}"
        except Exception:
            pass

        start_val = work_log.get('actual_start_time') or work_log.get('check_in_time') or "--"
        end_val = work_log.get('actual_end_time') or work_log.get('check_out_time') or "--"
        total_val = work_log.get('total_work_time') or "--"
        status_val = work_log.get('status') or ("Work Session Completed" if (start_val != "--" and end_val != "--") else "Work Session In Progress")

        main_frame = ttk.Frame(self, padding=25)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="⏰ MY ATTENDANCE / WORK TIME DASHBOARD", font=("Segoe UI", 13, "bold"), foreground="#0d9488").pack(anchor=tk.W, pady=(0, 2))
        ttk.Label(main_frame, text="Final Work Session Summary", font=("Segoe UI", 10, "italic"), foreground="#475569").pack(anchor=tk.W, pady=(0, 15))

        # Teacher Details Card
        t_card = ttk.LabelFrame(main_frame, text=" 👨‍🏫 Teacher Details ", padding=12)
        t_card.pack(fill=tk.X, pady=(0, 15))

        f1 = ttk.Frame(t_card)
        f1.pack(fill=tk.X, pady=3)
        ttk.Label(f1, text="Teacher Name:", font=("Segoe UI", 10, "bold"), width=16).pack(side=tk.LEFT)
        ttk.Label(f1, text=teacher_name, font=("Segoe UI", 10)).pack(side=tk.LEFT)

        f2 = ttk.Frame(t_card)
        f2.pack(fill=tk.X, pady=3)
        ttk.Label(f2, text="Teacher ID:", font=("Segoe UI", 10, "bold"), width=16).pack(side=tk.LEFT)
        ttk.Label(f2, text=teacher_id, font=("Segoe UI", 10)).pack(side=tk.LEFT)

        f3 = ttk.Frame(t_card)
        f3.pack(fill=tk.X, pady=3)
        ttk.Label(f3, text="Department:", font=("Segoe UI", 10, "bold"), width=16).pack(side=tk.LEFT)
        ttk.Label(f3, text=department, font=("Segoe UI", 10)).pack(side=tk.LEFT)

        # Work Details Card
        w_card = ttk.LabelFrame(main_frame, text=" 📋 Work Details ", padding=12)
        w_card.pack(fill=tk.X, pady=(0, 20))

        w1 = ttk.Frame(w_card)
        w1.pack(fill=tk.X, pady=3)
        ttk.Label(w1, text="Date:", font=("Segoe UI", 10, "bold"), width=18).pack(side=tk.LEFT)
        ttk.Label(w1, text=date_val, font=("Segoe UI", 10)).pack(side=tk.LEFT)

        w2 = ttk.Frame(w_card)
        w2.pack(fill=tk.X, pady=3)
        ttk.Label(w2, text="Start Time:", font=("Segoe UI", 10, "bold"), width=18).pack(side=tk.LEFT)
        ttk.Label(w2, text=start_val, font=("Segoe UI", 10, "bold"), foreground="#15803d").pack(side=tk.LEFT)

        w3 = ttk.Frame(w_card)
        w3.pack(fill=tk.X, pady=3)
        ttk.Label(w3, text="End Time:", font=("Segoe UI", 10, "bold"), width=18).pack(side=tk.LEFT)
        ttk.Label(w3, text=end_val, font=("Segoe UI", 10, "bold"), foreground="#15803d").pack(side=tk.LEFT)

        w4 = ttk.Frame(w_card)
        w4.pack(fill=tk.X, pady=3)
        ttk.Label(w4, text="Total Working Time:", font=("Segoe UI", 10, "bold"), width=18).pack(side=tk.LEFT)
        ttk.Label(w4, text=total_val, font=("Segoe UI", 11, "bold"), foreground="#0284c7").pack(side=tk.LEFT)

        w5 = ttk.Frame(w_card)
        w5.pack(fill=tk.X, pady=3)
        ttk.Label(w5, text="Status:", font=("Segoe UI", 10, "bold"), width=18).pack(side=tk.LEFT)
        ttk.Label(w5, text=status_val, font=("Segoe UI", 10, "bold"), foreground="#059669").pack(side=tk.LEFT)

        btn_ok = ttk.Button(main_frame, text="🔒 Complete Logout", style="Primary.TButton", command=self._close)
        btn_ok.pack(side=tk.RIGHT)

    def _close(self):
        self.grab_release()
        self.destroy()

class TeacherDashboard(tk.Toplevel):
    """Dashboard Portal for Teacher Role."""
    def __init__(self, welcome_win: tk.Tk, db_manager: DBManager, user_data: dict):
        super().__init__(welcome_win)
        self.welcome_win = welcome_win
        self.db = db_manager
        self.user_data = user_data
        self.predictor = PerformancePredictor()
        self.timer_after_id = None

        self.title("Teacher Portal - Student Management & Performance Prediction System")
        self.geometry("1050x700")
        self.minsize(950, 600)
        self.protocol("WM_DELETE_WINDOW", self.on_logout)

        # Retrieve logged in teacher details
        t_rec = self.db.get_teacher_by_user_id(self.user_data['id'])
        self.teacher_id = t_rec['teacher_id'] if t_rec else None

        # Capture EXACT CURRENT SYSTEM DATE AND TIME at this login moment
        from datetime import datetime
        from utils.helpers import get_current_date
        self.session_start_time = datetime.now().strftime("%I:%M:%S %p")
        self.session_date = get_current_date()

        # Automatically record login/start time on successful authentication
        if self.teacher_id:
            self.auto_record_start_time(is_login_event=True)

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. Top Header Bar
        top_bar = tk.Frame(self, bg="#0d9488", height=60)
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        top_bar.pack_propagate(False)

        lbl_title = tk.Label(top_bar, text="👨‍🏫 Teacher Workstation", font=("Segoe UI", 14, "bold"), bg="#0d9488", fg="#ffffff")
        lbl_title.pack(side=tk.LEFT, padx=20)

        btn_logout = tk.Button(top_bar, text="🚪 Logout", font=("Segoe UI", 9, "bold"), bg="#dc2626", fg="#ffffff", activebackground="#b91c1c", activeforeground="#ffffff", bd=0, cursor="hand2", command=self.on_logout)
        btn_logout.pack(side=tk.RIGHT, padx=20, ipadx=10, ipady=4)

        lbl_user = tk.Label(top_bar, text=f"LoggedIn: {self.user_data['username']} (Teacher)", font=("Segoe UI", 9), bg="#0d9488", fg="#e6fffa")
        lbl_user.pack(side=tk.RIGHT, padx=10)

        # 2. Sidebar Navigation
        sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=220)
        sidebar.grid(row=1, column=0, sticky="nsew")

        nav_buttons = [
            ("👤 My Profile", lambda: self.show_profile(edit_mode=False)),
            ("👨‍🎓 My Class Students", self.show_students),
            ("📝 Student Leaves", self.show_leave_requests),
            ("⏰ My Attendance / Work Time", self.show_my_work_time),
            ("💵 My Salary", self.show_my_salary),
            ("✍️ Marks Entry", self.show_marks),
            ("🤖 ML Class Predictions", self.show_ml_predictions),
            ("📊 Class Analytics", self.show_analytics),
            ("⚙️ Settings", self.show_settings),
            ("📅 Holiday", self.show_holidays),
            ("🚪 Logout", self.on_logout)
        ]

        for text, cmd in nav_buttons:
            btn = ttk.Button(sidebar, text=text, style="Sidebar.TButton", command=cmd)
            btn.pack(fill=tk.X, pady=2)

        # 3. Content Frame
        self.content_frame = ttk.Frame(self, padding=15)
        self.content_frame.grid(row=1, column=1, sticky="nsew")

        self.show_students()

    def clear_content(self):
        if hasattr(self, 'timer_after_id') and self.timer_after_id:
            try:
                self.after_cancel(self.timer_after_id)
            except Exception:
                pass
            self.timer_after_id = None
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_students(self):
        self.clear_content()

        hdr = ttk.Frame(self.content_frame)
        hdr.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(hdr, text="👨‍🎓 Student Management", font=FONTS["h1"]).pack(side=tk.LEFT)

        # Category Filter Bar (School vs College)
        cat_frame = ttk.Frame(self.content_frame)
        cat_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(cat_frame, text="Category / Education Type: ", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(0, 5))
        self.combo_category = ttk.Combobox(cat_frame, values=["School", "College"], state="readonly", width=12)
        self.combo_category.set("School")
        self.combo_category.pack(side=tk.LEFT, padx=3)
        self.combo_category.bind("<<ComboboxSelected>>", lambda e: self.load_students_table())
        ttk.Button(cat_frame, text="📋 View Individual Monthly Attendance", style="Primary.TButton", command=self.open_selected_student_attendance).pack(side=tk.LEFT, padx=(15, 3))

        # Attendance Control Bar
        att_frame = ttk.Frame(self.content_frame)
        att_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(att_frame, text="📋 Manual Attendance:", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(0, 5))
        self.combo_attendance = ttk.Combobox(att_frame, values=["Present", "Absent"], state="readonly", width=10)
        self.combo_attendance.set("Present")
        self.combo_attendance.pack(side=tk.LEFT, padx=3)

        ttk.Button(att_frame, text="💾 Save Attendance", style="Primary.TButton", command=self.save_selected_attendance).pack(side=tk.LEFT, padx=3)
        ttk.Button(att_frame, text="✅ Mark Present", command=lambda: self.mark_quick_attendance("Present")).pack(side=tk.LEFT, padx=3)
        ttk.Button(att_frame, text="❌ Mark Absent", command=lambda: self.mark_quick_attendance("Absent")).pack(side=tk.LEFT, padx=3)

        # Top Action Bar & Search (Add, Edit, Delete, Search together at top)
        action_frame = ttk.Frame(self.content_frame)
        action_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(action_frame, text="➕ Add Student", style="Primary.TButton", command=self.add_student_dialog).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="✏️ Edit Student", command=self.edit_selected_student).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="🗑️ Delete Student", style="Danger.TButton", command=self.delete_selected_student).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="✍️ Enter Marks", command=self.open_selected_marks).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="📷 Register Face", style="Accent.TButton", command=self.register_selected_face).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="📷 Face Attendance", style="Primary.TButton", command=self.open_selected_face_attendance).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="📋 View Individual Monthly Attendance", style="Primary.TButton", command=self.open_selected_student_attendance).pack(side=tk.LEFT, padx=3)

        ttk.Label(action_frame, text="🔍 Search:", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(15, 2))
        self.entry_search = ttk.Entry(action_frame, width=20)
        self.entry_search.pack(side=tk.LEFT, padx=3)
        btn_search_stu = ttk.Button(action_frame, text="Search", command=self.load_students_table)
        btn_search_stu.pack(side=tk.LEFT, padx=3)
        self.entry_search.bind("<KeyRelease>", lambda e: self.load_students_table())
        self.entry_search.bind("<Return>", lambda e: self.load_students_table())

        # Table Container Frame
        self.tbl_frame = ttk.Frame(self.content_frame)
        self.tbl_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = None
        self.load_students_table()

    def load_students_table(self):
        cat = self.combo_category.get() if hasattr(self, 'combo_category') else "School"
        st = self.entry_search.get().strip().lower() if hasattr(self, 'entry_search') else ""

        # Recreate tree inside tbl_frame to adapt column layout dynamically
        if hasattr(self, 'tbl_frame'):
            for widget in self.tbl_frame.winfo_children():
                widget.destroy()

        if cat == "School":
            cols = ("id", "name", "school_name", "class", "section", "attendance", "admission_date", "dob", "gender", "phone", "email", "parent_name", "parent_phone", "address")
        else: # College
            cols = ("id", "enrollment", "name", "college_name", "course", "semester", "attendance", "academic_year", "admission_date", "dob", "gender", "phone", "email", "parent_name", "parent_phone", "address")

        self.tree = ttk.Treeview(self.tbl_frame, columns=cols, show="headings", height=14)
        self.tree.tag_configure("highlighted", font=FONTS.get("body_bold", ("Segoe UI", 10, "bold")), background="#fef08a", foreground="#0f172a")

        if cat == "School":
            self.tree.heading("id", text="Student ID")
            self.tree.heading("name", text="Student Name")
            self.tree.heading("school_name", text="School Name")
            self.tree.heading("class", text="Class")
            self.tree.heading("section", text="Section")
            self.tree.heading("attendance", text="Attendance")
            self.tree.heading("admission_date", text="Admission Date")
            self.tree.heading("dob", text="Date of Birth")
            self.tree.heading("gender", text="Gender")
            self.tree.heading("phone", text="Phone")
            self.tree.heading("email", text="Email")
            self.tree.heading("parent_name", text="Parent Name")
            self.tree.heading("parent_phone", text="Parent Phone")
            self.tree.heading("address", text="Full Address")

            self.tree.column("id", width=100, anchor="center")
            self.tree.column("name", width=140, anchor="w")
            self.tree.column("school_name", width=140, anchor="w")
            self.tree.column("class", width=70, anchor="center")
            self.tree.column("section", width=70, anchor="center")
            self.tree.column("attendance", width=110, anchor="center")
            self.tree.column("admission_date", width=110, anchor="center")
            self.tree.column("dob", width=100, anchor="center")
            self.tree.column("gender", width=80, anchor="center")
            self.tree.column("phone", width=110, anchor="center")
            self.tree.column("email", width=150, anchor="w")
            self.tree.column("parent_name", width=140, anchor="w")
            self.tree.column("parent_phone", width=110, anchor="center")
            self.tree.column("address", width=180, anchor="w")

        else: # College
            self.tree.heading("id", text="Student ID")
            self.tree.heading("enrollment", text="Enrollment Number")
            self.tree.heading("name", text="Student Name")
            self.tree.heading("college_name", text="College Name")
            self.tree.heading("course", text="Course / Program")
            self.tree.heading("semester", text="Semester")
            self.tree.heading("attendance", text="Attendance")
            self.tree.heading("academic_year", text="Year")
            self.tree.heading("admission_date", text="Admission Date")
            self.tree.heading("dob", text="Date of Birth")
            self.tree.heading("gender", text="Gender")
            self.tree.heading("phone", text="Phone")
            self.tree.heading("email", text="Email")
            self.tree.heading("parent_name", text="Parent Name")
            self.tree.heading("parent_phone", text="Parent Phone")
            self.tree.heading("address", text="Full Address")

            self.tree.column("id", width=100, anchor="center")
            self.tree.column("enrollment", width=130, anchor="center")
            self.tree.column("name", width=140, anchor="w")
            self.tree.column("college_name", width=140, anchor="w")
            self.tree.column("course", width=140, anchor="w")
            self.tree.column("semester", width=100, anchor="center")
            self.tree.column("attendance", width=110, anchor="center")
            self.tree.column("academic_year", width=80, anchor="center")
            self.tree.column("admission_date", width=110, anchor="center")
            self.tree.column("dob", width=100, anchor="center")
            self.tree.column("gender", width=80, anchor="center")
            self.tree.column("phone", width=110, anchor="center")
            self.tree.column("email", width=150, anchor="w")
            self.tree.column("parent_name", width=140, anchor="w")
            self.tree.column("parent_phone", width=110, anchor="center")
            self.tree.column("address", width=180, anchor="w")

        v_scrollbar = ttk.Scrollbar(self.tbl_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(self.tbl_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=v_scrollbar.set, xscroll=h_scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        self.tbl_frame.grid_rowconfigure(0, weight=1)
        self.tbl_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", lambda e: self.edit_selected_student())
        self.tree.bind("<<TreeviewSelect>>", self._on_student_select)

        # Right-click context menu for instant actions
        row_menu = tk.Menu(self, tearoff=0)
        row_menu.add_command(label="📋 View Individual Monthly Attendance", command=self.open_selected_student_attendance)
        row_menu.add_command(label="📷 Face Attendance", command=self.open_selected_face_attendance)
        row_menu.add_command(label="📷 Register Face", command=self.register_selected_face)
        row_menu.add_command(label="✏️ Edit Student", command=self.edit_selected_student)
        row_menu.add_command(label="✍️ Enter Marks", command=self.open_selected_marks)

        def _on_tree_right_click(event):
            row_id = self.tree.identify_row(event.y)
            if row_id:
                self.tree.selection_set(row_id)
                row_menu.post(event.x_root, event.y_root)

        self.tree.bind("<Button-3>", _on_tree_right_click)

        students = self.db.get_all_students(filter_edu_type=cat)

        from utils.helpers import get_current_date
        today_date = get_current_date()
        matched_count = 0

        for s in students:
            sid = s.get('student_id', '')
            p_name = s.get('father_name') or s.get('mother_name') or s.get('guardian_name') or ''
            p_phone = s.get('father_phone') or s.get('parent_phone') or s.get('mother_phone') or ''
            att_rec = self.db.get_student_attendance_for_date(sid, today_date) if sid else None
            att_disp = att_rec['status'] if att_rec else "Present"
            sch_name = s.get('school_name') or s.get('previous_school') or ''
            col_name = s.get('college_name') or s.get('school_name') or s.get('previous_school') or ''

            if cat == "School":
                row_vals = (
                    sid,
                    s.get('name', ''),
                    sch_name,
                    s.get('current_class', ''),
                    s.get('section', ''),
                    att_disp,
                    s.get('admission_date', ''),
                    s.get('dob', ''),
                    s.get('gender', ''),
                    s.get('phone', ''),
                    s.get('email', ''),
                    p_name,
                    p_phone,
                    s.get('address', '')
                )
            else: # College
                row_vals = (
                    sid,
                    s.get('enrollment_number', '') or sid,
                    s.get('name', ''),
                    col_name,
                    s.get('course', ''),
                    s.get('semester', ''),
                    att_disp,
                    s.get('academic_year', ''),
                    s.get('admission_date', ''),
                    s.get('dob', ''),
                    s.get('gender', ''),
                    s.get('phone', ''),
                    s.get('email', ''),
                    p_name,
                    p_phone,
                    s.get('address', '')
                )

            row_str = " ".join(str(v) for v in row_vals).lower()
            tags = []
            if st:
                if st in row_str:
                    tags.append("highlighted")
                    matched_count += 1
                else:
                    continue
            else:
                matched_count += 1

            self.tree.insert("", tk.END, values=row_vals, tags=tuple(tags))

        if st and matched_count == 0:
            blank_row = tuple(["No record found"] + ["-"] * (len(cols) - 1))
            self.tree.insert("", tk.END, values=blank_row)

    def _on_student_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0])['values']
        if not vals or vals[0] == "No record found":
            return
        cat = self.combo_category.get() if hasattr(self, 'combo_category') else "School"
        att_idx = 5 if cat == "School" else 6
        if len(vals) > att_idx:
            att_val = str(vals[att_idx]).strip()
            if att_val in ["Present", "Absent"]:
                self.combo_attendance.set(att_val)

    def mark_quick_attendance(self, status: str):
        if hasattr(self, 'combo_attendance'):
            self.combo_attendance.set(status)
        self.save_selected_attendance(status_override=status)

    def save_selected_attendance(self, status_override: str = None):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a student from the table to mark/save attendance.")
            return
        
        status = status_override or (self.combo_attendance.get() if hasattr(self, 'combo_attendance') else "Present")
        from utils.helpers import get_current_date, get_current_time
        today = get_current_date()
        now_time = get_current_time()

        saved_count = 0
        failed_messages = []

        for item in sel:
            vals = self.tree.item(item)['values']
            if not vals or vals[0] == "No record found":
                continue
            sid = str(vals[0]).strip()
            sname = str(vals[1]).strip() if len(vals) > 1 else sid
            ok, msg = self.db.mark_attendance(sid, today, now_time, status, source="Teacher")
            if ok:
                saved_count += 1
            else:
                failed_messages.append((sid, sname, msg))

        if saved_count > 0 and not failed_messages:
            messagebox.showinfo("Success", f"Attendance marked as '{status}' for {saved_count} student(s).")
            self.load_students_table()
        elif saved_count > 0 and failed_messages:
            err_details = "\n".join([f"• {name} ({sid}): {msg}" for sid, name, msg in failed_messages])
            messagebox.showinfo(
                "Attendance Update",
                f"Attendance marked for {saved_count} student(s).\n\nFor the following student(s):\n{err_details}"
            )
            self.load_students_table()
        else:
            if len(failed_messages) == 1:
                sid, name, msg = failed_messages[0]
                messagebox.showwarning("Notice", msg)
            elif len(failed_messages) > 1:
                err_details = "\n".join([f"• {name} ({sid}): {msg}" for sid, name, msg in failed_messages])
                messagebox.showwarning("Notice", f"Could not update attendance:\n\n{err_details}")
            else:
                messagebox.showerror("Error", "Failed to update attendance.")

    def add_student_dialog(self):
        cat = self.combo_category.get() if hasattr(self, 'combo_category') else "School"
        from gui.student_forms import StudentFormDialog
        StudentFormDialog(self, self.db, on_save_callback=self.load_students_table, default_edu_type=cat)

    def edit_selected_student(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a student from the table.")
            return
        item_vals = self.tree.item(sel[0])['values']
        if not item_vals or item_vals[0] == "No record found":
            return
        sid = str(item_vals[0]).strip()
        from gui.student_forms import StudentFormDialog
        StudentFormDialog(self, self.db, student_id=sid, on_save_callback=self.load_students_table)

    def delete_selected_student(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a student from the table.")
            return
        item_vals = self.tree.item(sel[0])['values']
        if not item_vals or item_vals[0] == "No record found":
            return
        sid = item_vals[0]
        sname = item_vals[1]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete Student '{sname}' ({sid})?\nAll attendance and marks records will be permanently removed."):
            self.db.delete_student(sid)
            messagebox.showinfo("Deleted", f"Student '{sname}' deleted.")
            self.load_students_table()

    def register_selected_face(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a student from the table.")
            return
        item_vals = self.tree.item(sel[0])['values']
        if not item_vals or item_vals[0] == "No record found":
            return
        sid = item_vals[0]
        st_rec = self.db.get_student(sid)
        sname = st_rec.get('name', item_vals[1]) if st_rec else item_vals[1]

        from face_attendance.face_registration import FaceRegisterWindow
        FaceRegisterWindow(self, sid, sname, self.db)

    def open_selected_face_attendance(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a student from the table.")
            return
        item_vals = self.tree.item(sel[0])['values']
        if not item_vals or item_vals[0] == "No record found":
            return
        sid = str(item_vals[0]).strip()
        st_rec = self.db.get_student(sid)
        sname = st_rec.get('name', item_vals[1]) if st_rec else item_vals[1]

        # Check if student has a registered face
        face_blob = self.db.get_face_encoding(sid)
        if not face_blob and st_rec:
            if st_rec.get('student_id'):
                face_blob = self.db.get_face_encoding(st_rec['student_id'])
            if not face_blob and st_rec.get('enrollment_number'):
                face_blob = self.db.get_face_encoding(st_rec['enrollment_number'])

        if not face_blob:
            messagebox.showwarning(
                "Face Not Registered",
                f"No face registered for {sname} ({sid}).\nPlease register {sname}'s face first using 'Register Face'."
            )
            return

        from face_attendance.face_recognition import FaceAttendanceScannerWindow
        FaceAttendanceScannerWindow(
            self,
            self.db,
            target_role="Student",
            student_id=sid,
            on_attendance_marked=self.load_students_table,
            source="Teacher"
        )

    def open_selected_marks(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a student from the table.")
            return
        item_vals = self.tree.item(sel[0])['values']
        if not item_vals or item_vals[0] == "No record found":
            return
        sid = item_vals[0]
        sname = item_vals[1]
        from gui.marks_view import MarksEntryDialog
        MarksEntryDialog(self, self.db, sid, sname)

    def open_selected_student_attendance(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a student from the table.")
            return
        item_vals = self.tree.item(sel[0])['values']
        if not item_vals or item_vals[0] == "No record found":
            return
        sid = str(item_vals[0]).strip()
        from gui.attendance_view import IndividualStudentAttendanceDialog
        IndividualStudentAttendanceDialog(self, self.db, sid)

    open_selected_student_monthly_attendance = open_selected_student_attendance

    def show_marks(self):
        self.show_students()

    def show_ml_predictions(self):
        self.clear_content()

        hdr = ttk.Frame(self.content_frame)
        hdr.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(hdr, text="🤖 Class ML Performance Predictor", font=FONTS["h1"]).pack(side=tk.LEFT)

        # Mode and Search Filter Bar
        ctrl_frame = ttk.Frame(self.content_frame)
        ctrl_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(ctrl_frame, text="Mode:", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(0, 4))
        combo_ml_mode = ttk.Combobox(ctrl_frame, values=["School", "College"], state="readonly", width=12)
        combo_ml_mode.set("School")
        combo_ml_mode.pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(ctrl_frame, text="🔍 Search:", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(0, 4))
        entry_ml_search = ttk.Entry(ctrl_frame, width=20)
        entry_ml_search.pack(side=tk.LEFT, padx=3)
        btn_search_ml = ttk.Button(ctrl_frame, text="Search", command=lambda: refresh_predictions())
        btn_search_ml.pack(side=tk.LEFT, padx=3)

        tbl_frame = ttk.Frame(self.content_frame)
        tbl_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "name", "cat", "att", "study", "predicted_score", "category", "risk")
        tree = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=14)
        tree.tag_configure("highlighted", font=FONTS.get("body_bold", ("Segoe UI", 10, "bold")), background="#fef08a", foreground="#0f172a")

        tree.heading("id", text="Student ID")
        tree.heading("name", text="Name")
        tree.heading("cat", text="Class / Course")
        tree.heading("att", text="Attendance %")
        tree.heading("study", text="Study Hrs")
        tree.heading("predicted_score", text="Pred Score %")
        tree.heading("category", text="Predicted Category")
        tree.heading("risk", text="Risk Level")

        for c in cols:
            tree.column(c, width=105, anchor="center")
        tree.column("name", width=150, anchor="w")
        tree.column("cat", width=130, anchor="w")

        scrollbar = ttk.Scrollbar(tbl_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def refresh_predictions():
            for item in tree.get_children():
                tree.delete(item)

            cat = combo_ml_mode.get()
            q = entry_ml_search.get().strip().lower()

            students = self.db.get_all_students(filter_edu_type=cat)
            matched_count = 0
            for s in students:
                sid = s['student_id']
                att = self.db.get_student_attendance_stats(sid)['percentage']
                marks = self.db.get_student_marks(sid) or {}
                
                pred = self.predictor.predict_performance(
                    attendance_pct=att,
                    study_hours=s.get('study_hours', 2.0),
                    previous_pct=s.get('previous_percentage', 75.0),
                    internal_marks=marks.get('internal_marks', 0),
                    mid_term_marks=marks.get('mid_term_marks', 0),
                    project_marks=marks.get('project_marks', 0),
                    viva_marks=marks.get('viva_marks', 0)
                )

                class_course = s.get('current_class', '') if cat == "School" else s.get('course', '')

                row_vals = (
                    sid, s['name'], class_course, f"{att:.1f}%", s.get('study_hours', 2.0),
                    f"{pred['predicted_score']:.1f}%", pred['category'], pred['risk_level']
                )
                row_str = " ".join(str(v) for v in row_vals).lower()
                tags = []
                if q:
                    if q in row_str:
                        tags.append("highlighted")
                        matched_count += 1
                    else:
                        continue
                else:
                    matched_count += 1

                tree.insert("", tk.END, values=row_vals, tags=tuple(tags))

            if q and matched_count == 0:
                tree.insert("", tk.END, values=("No record found", "-", "-", "-", "-", "-", "-", "-"))

        combo_ml_mode.bind("<<ComboboxSelected>>", lambda e: refresh_predictions())
        entry_ml_search.bind("<Return>", lambda e: refresh_predictions())
        entry_ml_search.bind("<KeyRelease>", lambda e: refresh_predictions())

        refresh_predictions()

    def auto_record_start_time(self, is_login_event=False, start_time_override=None):
        """Automatically log the start of the teacher's work session upon successful login."""
        from datetime import datetime
        from utils.helpers import get_current_date, parse_datetime_helper

        if not self.teacher_id:
            return

        date_str = getattr(self, 'session_date', None) or get_current_date()
        time_str = start_time_override or getattr(self, 'session_start_time', None) or datetime.now().strftime("%I:%M:%S %p")

        if not is_login_event:
            w_log = self.db.get_teacher_work_log(self.teacher_id, date_str) or {}
            astart = w_log.get('start_time') or w_log.get('actual_start_time') or w_log.get('check_in_time')
            # One work session/start time per day: do not overwrite if start time already exists
            if astart and str(astart).strip() not in ("", "--", "None", "NULL"):
                return

        salary_month = datetime.strptime(date_str, "%Y-%m-%d").month
        salary_year = datetime.strptime(date_str, "%Y-%m-%d").year

        t_rec = self.db.get_teacher_by_user_id(self.user_data['id']) or self.db.get_teacher(self.teacher_id) or {}
        tname = t_rec.get('name', self.user_data.get('username', 'Sakshi'))

        # Fetch school timings settings to calculate lateness / deductions
        school_timings = self.db.get_school_timings()
        off_start = school_timings.get('start_time', '07:30 AM')
        off_end = school_timings.get('end_time', '12:30 PM')

        try:
            start_dt = parse_datetime_helper(off_start, date_str) or datetime.now()
            curr_dt = parse_datetime_helper(time_str, date_str) or datetime.now()
            school_end_dt = parse_datetime_helper(off_end, date_str) or datetime.now()

            if curr_dt > school_end_dt:
                salary_eligible = "NO"
                att_status = "Late"
                late_mins = 0
                deduction = 0.0
            else:
                salary_eligible = "YES"
                diff_mins = int((curr_dt - start_dt).total_seconds() // 60)
                
                # Fetch monthly salary to calculate per-minute deduction based on 26 days and 300 mins daily
                monthly_salary = float(t_rec.get('monthly_salary') or 35000.0)
                per_minute_salary = (monthly_salary / 26.0) / 300.0
                
                if diff_mins > 0:
                    att_status = "Late"
                    late_mins = diff_mins
                    deduction = round(late_mins * per_minute_salary, 2)
                else:
                    att_status = "On Time"
                    late_mins = 0
                    deduction = 0.0
        except Exception as e:
            print("Lateness calculation error:", e)
            salary_eligible = "YES"
            att_status = "On Time"
            late_mins = 0
            deduction = 0.0

        # Log attendance in database as Present
        self.db.mark_teacher_attendance(self.teacher_id, date_str, time_str, "Present")

        status_str = self.calculate_status_string(time_str, None, date_str)

        w_log_existing = self.db.get_teacher_work_log(self.teacher_id, date_str)

        # Insert or Update the work log
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if not w_log_existing:
                cursor.execute("""
                    INSERT INTO teacher_work_logs (
                        teacher_id, teacher_name, date, work_date, official_start_time, official_end_time,
                        actual_start_time, check_in_time, start_time, status, session_status, attendance_status,
                        late_minutes, face_verified, salary_deduction, salary_eligible, salary_month, salary_year,
                        actual_end_time, check_out_time, end_time, working_hours, total_work_time, total_work_seconds
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, NULL, NULL, NULL, 0.0, '00:00:00', 0)
                """, (self.teacher_id, tname, date_str, date_str, off_start, off_end, time_str, time_str, time_str, status_str, status_str, att_status, late_mins, deduction, salary_eligible, salary_month, salary_year))
            else:
                cursor.execute("""
                    UPDATE teacher_work_logs SET
                        work_date = ?,
                        actual_start_time = ?,
                        check_in_time = ?,
                        start_time = ?,
                        status = ?,
                        session_status = ?,
                        attendance_status = ?,
                        late_minutes = ?,
                        salary_deduction = ?,
                        salary_eligible = ?,
                        salary_month = ?,
                        salary_year = ?,
                        actual_end_time = NULL,
                        check_out_time = NULL,
                        end_time = NULL,
                        working_hours = 0.0,
                        total_work_time = '00:00:00',
                        total_work_seconds = 0
                    WHERE id = ?
                """, (date_str, time_str, time_str, time_str, status_str, status_str, att_status, late_mins, deduction, salary_eligible, salary_month, salary_year, w_log_existing['id']))
            conn.commit()

    def calculate_status_string(self, start_str, end_str, date_str):
        from utils.helpers import parse_datetime_helper

        if not start_str or str(start_str).strip() in ("", "--", "None", "NULL"):
            return "NOT STARTED"

        school_start_dt = parse_datetime_helper("07:30 AM", date_str)
        school_end_dt = parse_datetime_helper("12:30 PM", date_str)

        start_dt = parse_datetime_helper(start_str, date_str)
        if not start_dt:
            return "NOT STARTED"

        # EXACTLY 07:30 AM
        is_on_time = (start_dt.hour == 7 and start_dt.minute == 30)
        is_early = (start_dt.hour < 7 or (start_dt.hour == 7 and start_dt.minute < 30))
        is_late = (start_dt > school_start_dt and start_dt <= school_end_dt and not is_on_time)
        is_time_over_start = (start_dt > school_end_dt)

        late_mins = 0
        if is_late:
            late_mins = (start_dt.hour * 60 + start_dt.minute) - (7 * 60 + 30)
            if late_mins <= 0:
                is_on_time = True
                is_late = False

        if is_time_over_start:
            return "⏰ SCHOOL TIME IS OVER"

        if not end_str or str(end_str).strip() in ("", "--", "None", "NULL"):
            # Only start time is logged
            if is_on_time:
                return "🎉 Congratulations! You are on time."
            elif is_early:
                return "🟢 You are early."
            elif is_late:
                if late_mins == 1:
                    return "⚠️ You are late by 1 minute."
                else:
                    return f"⚠️ You are late by {late_mins} minutes."
        else:
            # End time is also logged
            end_dt = parse_datetime_helper(end_str, date_str)
            if not end_dt:
                if is_on_time:
                    return "🎉 Congratulations! You are on time."
                elif is_early:
                    return "🟢 You are early."
                elif is_late:
                    if late_mins == 1:
                        return "⚠️ You are late by 1 minute."
                    else:
                        return f"⚠️ You are late by {late_mins} minutes."

            is_end_over = (end_dt > school_end_dt)
            if is_end_over:
                if is_late:
                    return "⚠️ You are late / ⏰ Time is over."
                else:
                    return "⏰ Time is over.\nYou ended after 12:30 PM."
            else:
                return "Work Completed"

    def show_my_work_time(self):
        from utils.helpers import get_current_date
        from datetime import datetime

        self.clear_content()

        ttk.Label(self.content_frame, text="⏰ MY ATTENDANCE / WORK TIME", font=FONTS["h1"]).pack(anchor=tk.W, pady=(0, 15))

        if not self.teacher_id:
            t_rec = self.db.get_teacher_by_user_id(self.user_data['id'])
            if t_rec:
                self.teacher_id = t_rec['teacher_id']

        if not self.teacher_id:
            ttk.Label(self.content_frame, text="Teacher record not linked.", font=FONTS["body_bold"]).pack(anchor=tk.W)
            return

        t_rec = self.db.get_teacher_by_user_id(self.user_data['id']) or self.db.get_teacher(self.teacher_id) or {}

        # 1. TEACHER DETAILS AT THE TOP
        details_card = ttk.LabelFrame(self.content_frame, text=" 👨‍🏫 Teacher Details ", padding=15)
        details_card.pack(fill=tk.X, pady=(0, 15))

        t_name = t_rec.get('name', self.user_data.get('username', 'Sakshi'))
        t_id_val = t_rec.get('teacher_id', self.teacher_id or 'T001')
        t_dept = t_rec.get('department', 'Science')
        if not t_dept or not str(t_dept).strip():
            t_dept = 'Science'

        d_frame = ttk.Frame(details_card)
        d_frame.pack(fill=tk.X)

        f_name = ttk.Frame(d_frame)
        f_name.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        ttk.Label(f_name, text="Teacher Name:", font=("Segoe UI", 9, "bold"), foreground="#64748b").pack(anchor=tk.W)
        ttk.Label(f_name, text=t_name, font=("Segoe UI", 12, "bold"), foreground="#0f172a").pack(anchor=tk.W)

        f_id = ttk.Frame(d_frame)
        f_id.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        ttk.Label(f_id, text="Teacher ID:", font=("Segoe UI", 9, "bold"), foreground="#64748b").pack(anchor=tk.W)
        ttk.Label(f_id, text=t_id_val, font=("Segoe UI", 12, "bold"), foreground="#0f172a").pack(anchor=tk.W)

        f_dept = ttk.Frame(d_frame)
        f_dept.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        ttk.Label(f_dept, text="Department:", font=("Segoe UI", 9, "bold"), foreground="#64748b").pack(anchor=tk.W)
        ttk.Label(f_dept, text=t_dept, font=("Segoe UI", 12, "bold"), foreground="#0f172a").pack(anchor=tk.W)

        # 2. WORK TIME SECTION
        from utils.helpers import get_current_date, parse_datetime_helper
        today_db = get_current_date()
        today_display = datetime.now().strftime("%d-%b-%Y")

        w_log = self.db.get_teacher_work_log(self.teacher_id, today_db) or {}
        sal_summary = self.db.get_teacher_salary_summary(self.teacher_id)
        school_timings = self.db.get_school_timings()
        school_time_str = f"{school_timings.get('start_time', '07:30 AM')} – {school_timings.get('end_time', '12:30 PM')}"

        def clean_val(v):
            if not v or str(v).strip() in ("", "--", "None", "NULL"):
                return None
            return str(v).strip()

        astart = clean_val(w_log.get('start_time') or w_log.get('actual_start_time') or w_log.get('check_in_time'))
        aend = clean_val(w_log.get('end_time') or w_log.get('actual_end_time') or w_log.get('check_out_time'))
        twork = clean_val(w_log.get('total_work_time'))

        work_card = ttk.LabelFrame(self.content_frame, text=" ⏰ Work Time Dashboard ", padding=20)
        work_card.pack(fill=tk.X, pady=(0, 15))

        grid_frame = ttk.Frame(work_card)
        grid_frame.pack(fill=tk.X, pady=(0, 15))

        # 0. Date
        ttk.Label(grid_frame, text="Date:", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky=tk.W, pady=6, padx=(0, 15))
        ttk.Label(grid_frame, text=today_display, font=("Segoe UI", 11)).grid(row=0, column=1, sticky=tk.W, pady=6)

        # 1. Being On Time
        ttk.Label(grid_frame, text="Being On Time:", font=("Segoe UI", 11, "bold")).grid(row=1, column=0, sticky=tk.W, pady=6, padx=(0, 15))
        ttk.Label(grid_frame, text="07:30 AM", font=("Segoe UI", 11)).grid(row=1, column=1, sticky=tk.W, pady=6)

        # 2. School Time Ends
        ttk.Label(grid_frame, text="School Time Ends:", font=("Segoe UI", 11, "bold")).grid(row=2, column=0, sticky=tk.W, pady=6, padx=(0, 15))
        ttk.Label(grid_frame, text="12:30 PM", font=("Segoe UI", 11)).grid(row=2, column=1, sticky=tk.W, pady=6)

        # 3. Start Time
        start_disp = astart if astart else "--"
        ttk.Label(grid_frame, text="Start Time:", font=("Segoe UI", 11, "bold")).grid(row=3, column=0, sticky=tk.W, pady=6, padx=(0, 15))
        self.lbl_start_time = ttk.Label(grid_frame, text=start_disp, font=("Segoe UI", 11))
        self.lbl_start_time.grid(row=3, column=1, sticky=tk.W, pady=6)

        # Determine live time display
        live_time_str = "00:00:00"
        if astart:
            if not aend:
                try:
                    t_in = parse_datetime_helper(astart, w_log.get('date', today_db))
                    t_out = datetime.now()
                    if t_in and t_out:
                        diff_secs = int((t_out - t_in).total_seconds())
                        if diff_secs < 0:
                            diff_secs += 86400
                        hrs = diff_secs // 3600
                        mins = (diff_secs % 3600) // 60
                        secs = diff_secs % 60
                        live_time_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"
                except Exception:
                    live_time_str = "00:00:00"
            else:
                try:
                    t_in = parse_datetime_helper(astart, w_log.get('date', today_db))
                    t_out = parse_datetime_helper(aend, w_log.get('date', today_db))
                    if t_in and t_out:
                        diff_secs = int((t_out - t_in).total_seconds())
                        if diff_secs < 0:
                            diff_secs += 86400
                        hrs = diff_secs // 3600
                        mins = (diff_secs % 3600) // 60
                        secs = diff_secs % 60
                        live_time_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"
                except Exception:
                    if twork and twork != "NOT INCLUDED":
                        live_time_str = twork
                    else:
                        live_time_str = "00:00:00"

        # 4. Live Time
        ttk.Label(grid_frame, text="Live Time:", font=("Segoe UI", 11, "bold")).grid(row=4, column=0, sticky=tk.W, pady=6, padx=(0, 15))
        self.lbl_live_time_val = ttk.Label(grid_frame, text=live_time_str, font=("Segoe UI", 11))
        self.lbl_live_time_val.grid(row=4, column=1, sticky=tk.W, pady=6)

        # 5. End Time
        end_disp = aend if aend else "--"
        ttk.Label(grid_frame, text="End Time:", font=("Segoe UI", 11, "bold")).grid(row=5, column=0, sticky=tk.W, pady=6, padx=(0, 15))
        self.lbl_end_time = ttk.Label(grid_frame, text=end_disp, font=("Segoe UI", 11))
        self.lbl_end_time.grid(row=5, column=1, sticky=tk.W, pady=6)

        # 6. Working Time
        work_disp = twork if (aend and twork and twork != "NOT INCLUDED") else "--"
        ttk.Label(grid_frame, text="Working Time:", font=("Segoe UI", 11, "bold")).grid(row=6, column=0, sticky=tk.W, pady=6, padx=(0, 15))
        self.lbl_work_time_val = ttk.Label(grid_frame, text=work_disp, font=("Segoe UI", 11))
        self.lbl_work_time_val.grid(row=6, column=1, sticky=tk.W, pady=6)

        # 7. Status
        status_disp = self.calculate_status_string(astart, aend, today_db)
        ttk.Label(grid_frame, text="Status:", font=("Segoe UI", 11, "bold")).grid(row=7, column=0, sticky=tk.W, pady=6, padx=(0, 15))
        status_color = "#0284c7"  # light blue for working
        if "Congratulations" in status_disp or "early" in status_disp or "Work Completed" in status_disp:
            status_color = "#15803d"  # green
        elif "late" in status_disp.lower() or "over" in status_disp.lower():
            status_color = "#dc2626"  # red
        elif status_disp == "NOT STARTED":
            status_color = "#64748b"  # gray
        ttk.Label(grid_frame, text=status_disp, font=("Segoe UI", 11, "bold"), foreground=status_color).grid(row=7, column=1, sticky=tk.W, pady=6)

        # Save Button Container Frame (replacing with START / END buttons)
        btn_frame = ttk.Frame(work_card)
        btn_frame.pack(anchor=tk.W, pady=(15, 0))

        self.btn_start_time = ttk.Button(
            btn_frame,
            text="START TIME",
            command=self.click_start_time
        )
        self.btn_start_time.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_end_time = ttk.Button(
            btn_frame,
            text="END TIME",
            command=self.click_end_time
        )
        self.btn_end_time.pack(side=tk.LEFT)

        # Configure button states based on database log
        self.btn_start_time.config(state="normal")
        self.btn_end_time.config(state="normal")
        if astart and not aend:
            # Start the live timer!
            self.update_live_timer()

        # 3. Monthly Summary Section
        m_card = ttk.LabelFrame(self.content_frame, text=" Monthly Summary ", padding=15)
        m_card.pack(fill=tk.X)

        m_txt = f"""
📊 Monthly Present Days: {sal_summary['present_days']} / {sal_summary['working_days']} days
📈 Monthly Total Working Hours: {sal_summary['total_working_hours']:.2f} hrs
⏰ Total Late Summary: {sal_summary['late_summary_mins']} mins
💸 Total Late Deductions: ${sal_summary['late_deduction']:.2f}
        """
        ttk.Label(m_card, text=m_txt, font=FONTS["body"], justify=tk.LEFT).pack(anchor=tk.W)

    def update_live_timer(self):
        """Update the live working time display every second."""
        from datetime import datetime
        from utils.helpers import get_current_date, parse_datetime_helper

        # Cancel any previous timer scheduling to prevent duplicate threads
        if hasattr(self, 'timer_after_id') and self.timer_after_id:
            try:
                self.after_cancel(self.timer_after_id)
            except Exception:
                pass
            self.timer_after_id = None

        if not self.teacher_id:
            return

        date_str = get_current_date()
        w_log = self.db.get_teacher_work_log(self.teacher_id, date_str) or {}
        
        astart = w_log.get('start_time') or w_log.get('actual_start_time') or w_log.get('check_in_time')
        aend = w_log.get('end_time') or w_log.get('actual_end_time') or w_log.get('check_out_time')

        # Clean values
        def clean_val(v):
            if not v or str(v).strip() in ("", "--", "None", "NULL"):
                return None
            return str(v).strip()

        astart = clean_val(astart)
        aend = clean_val(aend)

        if astart and not aend:
            t_in = parse_datetime_helper(astart, w_log.get('date', date_str))
            t_out = datetime.now()
            
            if t_in and t_out:
                diff_secs = int((t_out - t_in).total_seconds())
                if diff_secs < 0:
                    diff_secs += 86400  # Cross-midnight session support
                hrs = diff_secs // 3600
                mins = (diff_secs % 3600) // 60
                secs = diff_secs % 60
                total_work_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"
            else:
                total_work_str = "00:00:00"

            if hasattr(self, 'lbl_live_time_val') and self.lbl_live_time_val.winfo_exists():
                self.lbl_live_time_val.config(text=total_work_str)
                self.timer_after_id = self.after(1000, self.update_live_timer)

    def click_start_time(self):
        """Log the start of the teacher's work session using the real system clock."""
        from datetime import datetime
        from utils.helpers import get_current_date, parse_datetime_helper

        if not self.teacher_id:
            messagebox.showerror("Error", "Teacher record not linked to current user.")
            return

        date_str = getattr(self, 'session_date', None) or get_current_date()
        w_log = self.db.get_teacher_work_log(self.teacher_id, date_str) or {}
        astart = w_log.get('start_time') or w_log.get('actual_start_time') or w_log.get('check_in_time')
        if astart and str(astart).strip() not in ("", "--", "None", "NULL"):
            messagebox.showinfo("Information", "Start Time is already running.")
            self.show_my_work_time()
            return

        time_str = datetime.now().strftime("%I:%M:%S %p")
        self.auto_record_start_time()
        messagebox.showinfo("Success", f"Work session started at {time_str}.")
        self.show_my_work_time()

    def click_face_attendance(self):
        """Perform facial recognition attendance verification for the logged-in teacher."""
        from tkinter import messagebox
        from utils.helpers import get_current_date, get_current_time
        from face_attendance.face_recognition import TeacherFaceAttendanceWindow

        if not self.teacher_id:
            messagebox.showerror("Error", "Teacher record not linked to current user.")
            return

        today = get_current_date()
        att = self.db.get_teacher_today_attendance(self.teacher_id, today)
        if att:
            messagebox.showinfo("Information", "Today's attendance is already marked.")
            return

        # Check if face is registered
        has_face = self.db.get_face_encoding(self.teacher_id)
        if not has_face:
            messagebox.showwarning("Warning", "No registered face found. Please register your face in 'My Profile' first.")
            return

        # Callback on success
        def success_callback(now_t):
            self.auto_record_start_time(start_time_override=now_t)
            messagebox.showinfo("Success", f"Face verification successful. Attendance marked and work session started.")
            self.show_my_work_time()

        # Launch webcam window
        TeacherFaceAttendanceWindow(self, self.db, teacher_id=self.teacher_id, on_attendance_marked=success_callback, custom_db_handling=True)

    def click_end_time(self):
        """Log the end of the teacher's work session and compute duration."""
        from datetime import datetime
        from utils.helpers import get_current_date, parse_datetime_helper

        if not self.teacher_id:
            messagebox.showerror("Error", "Teacher record not linked to current user.")
            return

        date_str = getattr(self, 'session_date', None) or get_current_date()
        time_str = datetime.now().strftime("%I:%M:%S %p")

        w_log = self.db.get_teacher_work_log(self.teacher_id, date_str) or {}
        check_in_str = w_log.get('start_time') or w_log.get('actual_start_time') or w_log.get('check_in_time')
        
        # Clean the value
        if not check_in_str or str(check_in_str).strip() in ("", "--", "None", "NULL"):
            messagebox.showerror("Error", "Please click Start Time first.")
            return

        check_in_str = str(check_in_str).strip()

        # Check if already ended
        aend = w_log.get('end_time') or w_log.get('actual_end_time') or w_log.get('check_out_time')
        if aend and str(aend).strip() not in ("", "--", "None", "NULL"):
            messagebox.showinfo("Information", "End Time has already been recorded for this session.")
            self.show_my_work_time()
            return

        # Calculate working time (accurate to hours, minutes and seconds)
        try:
            t_in = parse_datetime_helper(check_in_str, w_log.get('date', date_str))
            t_out = parse_datetime_helper(time_str, date_str)
            if t_in and t_out:
                diff_secs = int((t_out - t_in).total_seconds())
                if diff_secs < 0:
                    diff_secs += 86400  # Cross-midnight session support
                dur_hours = round(diff_secs / 3600.0, 2)
                hrs = diff_secs // 3600
                mins = (diff_secs % 3600) // 60
                secs = diff_secs % 60
                total_work_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"
            else:
                dur_hours = 0.0
                total_work_str = "00:00:00"
                diff_secs = 0
        except Exception as e:
            print("Logout calculation error:", e)
            dur_hours = 0.0
            total_work_str = "00:00:00"
            diff_secs = 0

        status_str = self.calculate_status_string(check_in_str, time_str, date_str)

        # Update database with work completed status and computed work time
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE teacher_work_logs SET
                    actual_end_time = ?,
                    check_out_time = ?,
                    end_time = ?,
                    working_hours = ?,
                    total_work_time = ?,
                    total_work_seconds = ?,
                    status = ?,
                    session_status = ?
                WHERE teacher_id = ? AND date = ?
            """, (time_str, time_str, time_str, dur_hours, total_work_str, diff_secs, status_str, status_str, self.teacher_id, date_str))
            conn.commit()

        # Stop/cancel the live timer
        if hasattr(self, 'timer_after_id') and self.timer_after_id:
            try:
                self.after_cancel(self.timer_after_id)
            except Exception:
                pass
            self.timer_after_id = None

        messagebox.showinfo("Success", "End Time recorded successfully.")
        self.show_my_work_time()

    def save_manual_work_time(self):
        """Save manually entered Start Time and End Time to database."""
        from utils.helpers import get_current_date
        today = get_current_date()

        if not self.teacher_id:
            t_rec = self.db.get_teacher_by_user_id(self.user_data['id'])
            if t_rec:
                self.teacher_id = t_rec['teacher_id']

        if not self.teacher_id:
            messagebox.showerror("Error", "Teacher record not linked to current user.")
            return

        start_val = self.ent_start_time.get().strip() if hasattr(self, 'ent_start_time') else ""
        end_val = self.ent_end_time.get().strip() if hasattr(self, 'ent_end_time') else ""

        if start_val:
            self.db.mark_teacher_attendance(self.teacher_id, today, start_val, "Present")
            self.db.record_teacher_login(self.teacher_id, start_time_override=start_val)

        if end_val:
            self.db.record_teacher_logout(self.teacher_id, end_time_override=end_val)

        messagebox.showinfo("Success", "Work time saved successfully.")
        self.show_my_work_time()



    def show_my_salary(self):
        self.clear_content()
        ttk.Label(self.content_frame, text="💵 My Salary & Compensation Summary", font=FONTS["h1"]).pack(anchor=tk.W, pady=(0, 10))

        if not self.teacher_id:
            ttk.Label(self.content_frame, text="Teacher record not linked.", font=FONTS["body_bold"]).pack()
            return

        import datetime
        now = datetime.datetime.now()
        if not hasattr(self, 'salary_selected_month') or self.salary_selected_month is None:
            self.salary_selected_month = now.month
        if not hasattr(self, 'salary_selected_year') or self.salary_selected_year is None:
            self.salary_selected_year = now.year

        # Month/Year selection frame
        sel_frame = ttk.Frame(self.content_frame)
        sel_frame.pack(anchor=tk.W, pady=(0, 12))

        ttk.Label(sel_frame, text="Month: ", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(0, 5))
        months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        combo_month = ttk.Combobox(sel_frame, values=months_list, state="readonly", width=12)
        combo_month.set(months_list[self.salary_selected_month - 1])
        combo_month.pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(sel_frame, text="Year: ", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(0, 5))
        years_list = ["2025", "2026", "2027", "2028", "2029", "2030"]
        combo_year = ttk.Combobox(sel_frame, values=years_list, state="readonly", width=8)
        combo_year.set(str(self.salary_selected_year))
        combo_year.pack(side=tk.LEFT)

        def on_selection_changed(e):
            self.salary_selected_month = months_list.index(combo_month.get()) + 1
            self.salary_selected_year = int(combo_year.get())
            self.show_my_salary()

        combo_month.bind("<<ComboboxSelected>>", on_selection_changed)
        combo_year.bind("<<ComboboxSelected>>", on_selection_changed)

        # Check if today's login was after 12:30 PM (School End Time)
        today_db = datetime.date.today().strftime("%Y-%m-%d")
        w_log_today = self.db.get_teacher_work_log(self.teacher_id, today_db)
        
        is_today_over = False
        today_login_time = None
        if w_log_today:
            astart_today = w_log_today.get('start_time') or w_log_today.get('actual_start_time') or w_log_today.get('check_in_time')
            if astart_today and str(astart_today).strip() not in ("", "--", "None", "NULL"):
                try:
                    from utils.helpers import parse_datetime_helper
                    t_in = parse_datetime_helper(astart_today, today_db)
                    t_school_end = datetime.datetime.combine(datetime.date.today(), datetime.time(12, 30))
                    if t_in and t_in > t_school_end:
                        is_today_over = True
                        today_login_time = astart_today
                except Exception:
                    pass

        if is_today_over:
            warn_frame = ttk.LabelFrame(self.content_frame, text=" ⚠️ Attendance Notice ", padding=10)
            warn_frame.pack(fill=tk.X, pady=(0, 10))
            ttk.Label(warn_frame, text=f"Login Time: {today_login_time}", font=FONTS["body_bold"], foreground="#ef4444").pack(anchor=tk.W)
            ttk.Label(warn_frame, text="School Time Is Over.", font=FONTS["body_bold"], foreground="#ef4444").pack(anchor=tk.W)
            ttk.Label(warn_frame, text="This time is not included in my salary calculation.", font=FONTS["body_bold"], foreground="#ef4444").pack(anchor=tk.W)

        # Retrieve salary summary using selected month/year
        sal = self.db.get_teacher_salary_summary(self.teacher_id, month=self.salary_selected_month, year=self.salary_selected_year)

        # Configure columns & label frame headers based on month status
        if sal.get('is_future_month'):
            frame_title = " SALARY & COMPENSATION - MONTH NOT STARTED "
            metrics_col1 = [
                ("Monthly Salary:", f"₹{sal['base_salary']:.2f}"),
                ("Present Days:", "-"),
                ("Absent Days:", "-"),
                ("Paid Sundays:", "-"),
                ("Paid Government Holidays:", "-")
            ]
            metrics_col2 = [
                ("Total Working Hours:", "-"),
                ("Total Working Minutes:", "-"),
                ("Total Late Minutes:", "-"),
                ("Late Deduction:", "-"),
                ("NET SALARY:", "-")
            ]
            net_salary_label = "NET SALARY:"
        elif sal.get('is_current_month'):
            frame_title = " SALARY & COMPENSATION - CURRENT / RUNNING MONTH "
            metrics_col1 = [
                ("Monthly Salary:", f"₹{sal['base_salary']:.2f}"),
                ("Present Days:", f"{sal['present_days']}"),
                ("Absent Days:", f"{sal['absent_days']}"),
                ("Remaining Days:", f"{sal['remaining_days']}"),
                ("Paid Sundays:", f"{sal['paid_sundays']}"),
                ("Paid Government Holidays:", f"{sal['paid_holidays']}")
            ]
            metrics_col2 = [
                ("Total Working Hours:", f"{sal['total_working_hours_formatted']}"),
                ("Total Working Minutes:", f"{sal['total_working_minutes']}"),
                ("Total Late Minutes:", f"{sal['late_summary_mins']}"),
                ("Late Deduction:", f"₹{sal['late_deduction']:.2f}"),
                ("Absent Deduction:", f"₹{sal['absent_deduction']:.2f}"),
                ("RUNNING NET SALARY:", f"₹{sal['total_salary']:.2f}")
            ]
            net_salary_label = "RUNNING NET SALARY:"
        else:
            frame_title = " SALARY & COMPENSATION "
            metrics_col1 = [
                ("Monthly Salary:", f"₹{sal['base_salary']:.2f}"),
                ("Present Days:", f"{sal['present_days']}"),
                ("Absent Days:", f"{sal['absent_days']}"),
                ("Not Joined Days:", f"{sal['not_joined_days']}"),
                ("Paid Sundays:", f"{sal['paid_sundays']}"),
                ("Paid Government Holidays:", f"{sal['paid_holidays']}")
            ]
            metrics_col2 = [
                ("Total Working Hours:", f"{sal['total_working_hours_formatted']}"),
                ("Total Working Minutes:", f"{sal['total_working_minutes']}"),
                ("Total Late Minutes:", f"{sal['late_summary_mins']}"),
                ("Late Deduction:", f"₹{sal['late_deduction']:.2f}"),
                ("Absent Deduction:", f"₹{sal['absent_deduction']:.2f}"),
                ("NET SALARY:", f"₹{sal['total_salary']:.2f}")
            ]
            net_salary_label = "NET SALARY:"

        # Summary Frame (Salary & Compensation)
        card = ttk.LabelFrame(self.content_frame, text=frame_title, padding=20)
        card.pack(fill=tk.X, pady=(0, 15))

        # Layout grid with 2 columns
        grid_left = ttk.Frame(card)
        grid_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        grid_right = ttk.Frame(card)
        grid_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))

        for idx, (label, val) in enumerate(metrics_col1):
            ttk.Label(grid_left, text=label, font=FONTS["body_bold"]).grid(row=idx, column=0, sticky="w", pady=4, padx=5)
            ttk.Label(grid_left, text=val, font=FONTS["body"]).grid(row=idx, column=1, sticky="w", pady=4, padx=5)

        for idx, (label, val) in enumerate(metrics_col2):
            if label == net_salary_label:
                ttk.Label(grid_right, text=label, font=("Segoe UI", 11, "bold"), foreground="#0d9488").grid(row=idx, column=0, sticky="w", pady=4, padx=5)
                ttk.Label(grid_right, text=val, font=("Segoe UI", 12, "bold"), foreground="#0d9488").grid(row=idx, column=1, sticky="w", pady=4, padx=5)
            else:
                ttk.Label(grid_right, text=label, font=FONTS["body_bold"]).grid(row=idx, column=0, sticky="w", pady=4, padx=5)
                ttk.Label(grid_right, text=val, font=FONTS["body"]).grid(row=idx, column=1, sticky="w", pady=4, padx=5)

        # Day-wise Monthly Record Frame
        tbl_card = ttk.LabelFrame(self.content_frame, text=" DAY-WISE MONTHLY RECORD ", padding=10)
        tbl_card.pack(fill=tk.BOTH, expand=True)

        cols = ("date", "day", "attendance", "start_time", "end_time", "working_time", "late_minutes")
        tree = ttk.Treeview(tbl_card, columns=cols, show="headings", height=8)

        tree.heading("date", text="Date")
        tree.heading("day", text="Day")
        tree.heading("attendance", text="Attendance")
        tree.heading("start_time", text="Start Time")
        tree.heading("end_time", text="End Time")
        tree.heading("working_time", text="Working Time")
        tree.heading("late_minutes", text="Late Minutes")

        tree.column("date", width=80, anchor="center")
        tree.column("day", width=100, anchor="center")
        tree.column("attendance", width=180, anchor="w")
        tree.column("start_time", width=100, anchor="center")
        tree.column("end_time", width=100, anchor="center")
        tree.column("working_time", width=100, anchor="center")
        tree.column("late_minutes", width=90, anchor="center")

        scrollbar = ttk.Scrollbar(tbl_card, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for record in sal.get("day_wise_records", []):
            tree.insert("", tk.END, values=(
                record["date"],
                record["day"],
                record["attendance"],
                record["start_time"],
                record["end_time"],
                record["working_time"],
                record["late_minutes"]
            ))

    def show_profile(self, edit_mode: bool = False):
        self.clear_content()

        t_rec = self.db.get_teacher_by_user_id(self.user_data['id']) or (self.db.get_teacher(self.teacher_id) if self.teacher_id else None) or {}

        if not edit_mode:
            # VIEW PROFILE MODE
            hdr = ttk.Frame(self.content_frame)
            hdr.pack(fill=tk.X, pady=(0, 15))

            ttk.Label(hdr, text="👤 Teacher Profile & Workstation", font=FONTS["h1"]).pack(side=tk.LEFT)
            ttk.Button(hdr, text="✏️ Edit Profile", style="Primary.TButton", command=lambda: self.show_profile(edit_mode=True)).pack(side=tk.RIGHT)

            card = ttk.LabelFrame(self.content_frame, text=" Authorized Teacher Profile Details ", padding=20)
            card.pack(fill=tk.BOTH, expand=True)

            t_info = f"""
            • Teacher ID: {t_rec.get('teacher_id', self.teacher_id or 'N/A')}
            • Full Name: {t_rec.get('name', self.user_data.get('username', 'N/A'))}
            • Gender: {t_rec.get('gender', 'N/A') or 'N/A'}
            • Phone Number: {t_rec.get('phone', 'N/A')}
            • Email Address: {t_rec.get('email', 'N/A')}
            • Address: {t_rec.get('address', 'N/A')}
            • Department: {t_rec.get('department', 'N/A')}
            • Designation: {t_rec.get('designation', 'N/A')}
            • Joining Date: {t_rec.get('joining_date', 'N/A')}
            """
            ttk.Label(card, text=t_info, font=("Consolas", 11), justify="left").pack(anchor=tk.W, pady=10)

            # Face status check
            tid_val = t_rec.get('teacher_id', self.teacher_id)
            has_face = False
            if tid_val:
                has_face = self.db.get_face_encoding(tid_val) is not None

            if has_face:
                ttk.Label(card, text="FACE REGISTERED ✓", font=("Segoe UI", 12, "bold"), foreground="#15803d").pack(anchor=tk.W, padx=10, pady=5)
            else:
                def register_profile_face():
                    from face_attendance.face_registration import FaceRegisterWindow
                    def on_complete(success):
                        if success:
                            self.show_profile(edit_mode=False)
                    FaceRegisterWindow(self, tid_val, t_rec.get('name', ''), self.db, on_complete=on_complete)

                ttk.Button(card, text="REGISTER YOUR FACE", command=register_profile_face).pack(anchor=tk.W, padx=10, pady=5)
        else:
            # EDIT PROFILE MODE
            hdr = ttk.Frame(self.content_frame)
            hdr.pack(fill=tk.X, pady=(0, 15))

            ttk.Label(hdr, text="✏️ Edit Teacher Profile", font=FONTS["h1"]).pack(side=tk.LEFT)

            form_card = ttk.LabelFrame(self.content_frame, text=" Edit Authorized Details ", padding=20)
            form_card.pack(fill=tk.BOTH, expand=True)

            # Teacher ID (Read only)
            ttk.Label(form_card, text="Teacher ID:", font=FONTS["body_bold"]).grid(row=0, column=0, sticky="w", pady=8)
            ttk.Label(form_card, text=f"{t_rec.get('teacher_id', self.teacher_id or 'N/A')} (Protected)", font=FONTS["body_bold"], foreground=COLORS["text_muted"]).grid(row=0, column=1, sticky="w", pady=8, padx=10)

            # Name
            ttk.Label(form_card, text="Full Name *:", font=FONTS["body_bold"]).grid(row=1, column=0, sticky="w", pady=8)
            entry_name = ttk.Entry(form_card, width=35)
            entry_name.insert(0, t_rec.get('name', ''))
            entry_name.grid(row=1, column=1, sticky="w", pady=8, padx=10)

            # Gender
            ttk.Label(form_card, text="Gender:", font=FONTS["body_bold"]).grid(row=2, column=0, sticky="w", pady=8)
            combo_gender = ttk.Combobox(form_card, values=["Male", "Female", "Other"], state="readonly", width=33)
            combo_gender.set(t_rec.get('gender', 'Male') or 'Male')
            combo_gender.grid(row=2, column=1, sticky="w", pady=8, padx=10)

            # Phone
            ttk.Label(form_card, text="Phone Number *:", font=FONTS["body_bold"]).grid(row=3, column=0, sticky="w", pady=8)
            entry_phone = ttk.Entry(form_card, width=35)
            entry_phone.insert(0, t_rec.get('phone', ''))
            entry_phone.grid(row=3, column=1, sticky="w", pady=8, padx=10)

            # Email
            ttk.Label(form_card, text="Email Address:", font=FONTS["body_bold"]).grid(row=4, column=0, sticky="w", pady=8)
            entry_email = ttk.Entry(form_card, width=35)
            entry_email.insert(0, t_rec.get('email', ''))
            entry_email.grid(row=4, column=1, sticky="w", pady=8, padx=10)

            # Address
            ttk.Label(form_card, text="Address:", font=FONTS["body_bold"]).grid(row=5, column=0, sticky="w", pady=8)
            entry_address = ttk.Entry(form_card, width=40)
            entry_address.insert(0, t_rec.get('address', ''))
            entry_address.grid(row=5, column=1, sticky="w", pady=8, padx=10)

            # Dept / Designation (Read only)
            ttk.Label(form_card, text="Department / Designation:", font=FONTS["body_bold"]).grid(row=6, column=0, sticky="w", pady=8)
            ttk.Label(form_card, text=f"{t_rec.get('department', 'N/A')} - {t_rec.get('designation', 'N/A')}", font=FONTS["body"]).grid(row=6, column=1, sticky="w", pady=8, padx=10)

            def save_teacher_profile_callback():
                from utils.validators import validate_email, validate_phone
                name = entry_name.get().strip()
                phone = entry_phone.get().strip()
                email = entry_email.get().strip()
                address = entry_address.get().strip()
                gender = combo_gender.get().strip()

                if not name or not phone:
                    messagebox.showwarning("Validation Error", "Name and Phone Number are required.")
                    return
                if not validate_phone(phone):
                    messagebox.showwarning("Validation Error", "Phone number must contain exactly 10 digits.")
                    return
                if email and not validate_email(email):
                    messagebox.showwarning("Validation Error", "Please enter a valid Email Address.")
                    return

                teacher_id_val = t_rec.get('teacher_id', self.teacher_id or '')
                teacher_data = {
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "email": email,
                    "address": address,
                    "department": t_rec.get('department', ''),
                    "designation": t_rec.get('designation', ''),
                    "joining_date": t_rec.get('joining_date', '')
                }
                self.db.update_teacher(teacher_id_val, teacher_data)
                messagebox.showinfo("Success", "Profile updated successfully!")
                self.show_profile(edit_mode=False)

            btn_bar = ttk.Frame(form_card)
            btn_bar.grid(row=7, column=0, columnspan=2, sticky="w", pady=(15, 0))

            ttk.Button(btn_bar, text="💾 Save Profile", style="Primary.TButton", command=save_teacher_profile_callback).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(btn_bar, text="Cancel", command=lambda: self.show_profile(edit_mode=False)).pack(side=tk.LEFT)

    def show_analytics(self):
        self.clear_content()
        AnalyticsChartsFrame(self.content_frame, self.db).pack(fill=tk.BOTH, expand=True)

    def show_settings(self):
        self.clear_content()
        from gui.settings_view import SettingsViewFrame
        SettingsViewFrame(self.content_frame, self.db, self.user_data, "Teacher", on_cancel=self.show_students).pack(fill=tk.BOTH, expand=True)

    def show_holidays(self):
        self.clear_content()
        from gui.holiday_view import HolidayViewFrame
        HolidayViewFrame(self.content_frame, self.db).pack(fill=tk.BOTH, expand=True)

    def show_leave_requests(self):
        self.clear_content()

        hdr = ttk.Frame(self.content_frame)
        hdr.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(hdr, text="📝 Student Leave Requests", font=FONTS["h1"]).pack(side=tk.LEFT)

        # Mode Filter Frame
        m_frame = ttk.Frame(self.content_frame)
        m_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(m_frame, text="Mode:", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(0, 4))
        combo_category = ttk.Combobox(m_frame, values=["School", "College"], state="readonly", width=12)
        combo_category.set("School")
        combo_category.pack(side=tk.LEFT)

        tbl_frame = ttk.Frame(self.content_frame)
        tbl_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "student_id", "name", "date", "reason", "teacher", "admin", "final")
        tree = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=15)
        tree.heading("id", text="Request ID")
        tree.heading("student_id", text="Student ID")
        tree.heading("name", text="Student Name")
        tree.heading("date", text="Leave Date")
        tree.heading("reason", text="Reason")
        tree.heading("teacher", text="Teacher Decision")
        tree.heading("admin", text="Admin Decision")
        tree.heading("final", text="Final Status")

        tree.column("id", width=80, anchor="center")
        tree.column("student_id", width=100, anchor="center")
        tree.column("name", width=140, anchor="w")
        tree.column("date", width=100, anchor="center")
        tree.column("reason", width=180, anchor="w")
        tree.column("teacher", width=110, anchor="center")
        tree.column("admin", width=110, anchor="center")
        tree.column("final", width=110, anchor="center")

        sb = ttk.Scrollbar(tbl_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=sb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        btn_bar = ttk.Frame(self.content_frame, padding=10)
        btn_bar.pack(fill=tk.X)

        def handle_decision(status):
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Warning", "Please select a leave request from the table.")
                return
            req_id = tree.item(sel[0])['values'][0]
            success = self.db.update_leave_request_status(int(req_id), 'Teacher', status)
            if success:
                messagebox.showinfo("Success", f"Leave request status updated to '{status}'.")
                refresh_leaves()
            else:
                messagebox.showerror("Error", "Failed to update leave request status.")

        ttk.Button(btn_bar, text="Accept Request", style="Success.TButton", command=lambda: handle_decision('Accept')).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_bar, text="Reject Request", style="Danger.TButton", command=lambda: handle_decision('Reject')).pack(side=tk.LEFT, padx=5)

        def refresh_leaves():
            for item in tree.get_children():
                tree.delete(item)
            cat = combo_category.get()
            reqs = self.db.get_all_leave_requests()
            for r in reqs:
                stu = self.db.get_student(r['student_id'])
                edu_type = stu.get('education_type', 'School') if stu else 'School'
                if edu_type == cat:
                    tree.insert("", tk.END, values=(r['id'], r['student_id'], r['student_name'], r['leave_date'], r['reason'], r['teacher_status'], r['admin_status'], r['final_status']))

        combo_category.bind("<<ComboboxSelected>>", lambda e: refresh_leaves())
        refresh_leaves()

    def destroy(self):
        if hasattr(self, 'timer_after_id') and self.timer_after_id:
            try:
                self.after_cancel(self.timer_after_id)
            except Exception:
                pass
            self.timer_after_id = None
        try:
            super().destroy()
        except Exception:
            pass

    def on_logout(self):
        """Centralized real logout handler for Logout button and window close (X) event."""
        from utils.helpers import get_current_date
        from datetime import datetime

        today_db = get_current_date()
        w_log = {}
        astart = None
        aend = None

        try:
            if self.db and self.teacher_id:
                w_log = self.db.get_teacher_work_log(self.teacher_id, today_db) or {}
                astart = w_log.get('actual_start_time') or w_log.get('check_in_time')
                aend = w_log.get('actual_end_time') or w_log.get('check_out_time')
        except Exception as e:
            print("Error retrieving teacher work log during logout:", e)

        if astart and not aend:
            if messagebox.askyesno("Work Session Running", "Your work session is currently running. Do you want to end your work session and log out?"):
                try:
                    now_time = datetime.now().strftime("%I:%M:%S %p")
                    self.db.record_teacher_logout(self.teacher_id, end_time_override=now_time)
                    w_log = self.db.get_teacher_work_log(self.teacher_id, today_db) or {}
                except Exception as e:
                    print("Error recording teacher logout time:", e)
            else:
                return
        elif not messagebox.askyesno("Confirm Logout", "Are you sure you want to log out?"):
            return

        try:
            t_rec = {}
            if self.db:
                if self.user_data and 'id' in self.user_data:
                    t_rec = self.db.get_teacher_by_user_id(self.user_data['id']) or {}
                if not t_rec and self.teacher_id:
                    t_rec = self.db.get_teacher(self.teacher_id) or {}

            t_name = t_rec.get('name', self.user_data.get('username', 'Teacher') if self.user_data else 'Teacher')
            t_id_val = t_rec.get('teacher_id', self.teacher_id or 'T001')
            t_dept = t_rec.get('department', 'Science')
            if not t_dept or not str(t_dept).strip():
                t_dept = 'Science'

            astart = w_log.get('actual_start_time') or w_log.get('check_in_time')
            if astart:
                dlg = WorkTimeSummaryDialog(self, t_name, t_id_val, t_dept, w_log)
                self.wait_window(dlg)
        except Exception as e:
            print("Optional work time summary dialog error:", e)

        # Clear active content and timer callbacks
        self.clear_content()

        # Reset session attributes
        self.user_data = None
        self.teacher_id = None

        # Destroy the Teacher Dashboard window
        self.destroy()

        # Restore Welcome Window and open the existing Login Screen for Teacher role
        if hasattr(self, 'welcome_win') and self.welcome_win:
            try:
                self.welcome_win.deiconify()
            except Exception:
                pass
            from gui.login import LoginWindow
            LoginWindow(self.welcome_win, self.db, "Teacher")

