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

        # Teacher ID retrieved, work session will start only when teacher clicks START button
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

        ttk.Label(action_frame, text="🔍 Search:", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(15, 2))
        self.entry_search = ttk.Entry(action_frame, width=22)
        self.entry_search.pack(side=tk.LEFT, padx=3)
        self.entry_search.bind("<KeyRelease>", lambda e: self.load_students_table())

        # Table Container Frame
        self.tbl_frame = ttk.Frame(self.content_frame)
        self.tbl_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = None
        self.load_students_table()

    def load_students_table(self):
        cat = self.combo_category.get() if hasattr(self, 'combo_category') else "School"
        st = self.entry_search.get().strip() if hasattr(self, 'entry_search') else ""

        # Recreate tree inside tbl_frame to adapt column layout dynamically
        if hasattr(self, 'tbl_frame'):
            for widget in self.tbl_frame.winfo_children():
                widget.destroy()

        if cat == "School":
            cols = ("id", "name", "school_name", "class", "section", "attendance", "admission_date", "dob", "gender", "phone", "email", "parent_name", "parent_phone", "address")
        else: # College
            cols = ("id", "enrollment", "name", "college_name", "course", "semester", "attendance", "academic_year", "admission_date", "dob", "gender", "phone", "email", "parent_name", "parent_phone", "address")

        self.tree = ttk.Treeview(self.tbl_frame, columns=cols, show="headings", height=14)

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

        students = self.db.get_all_students(search_term=st, filter_edu_type=cat)

        from utils.helpers import get_current_date
        today_date = get_current_date()

        for s in students:
            sid = s.get('student_id', '')
            p_name = s.get('father_name') or s.get('mother_name') or s.get('guardian_name') or ''
            p_phone = s.get('father_phone') or s.get('parent_phone') or s.get('mother_phone') or ''
            att_rec = self.db.get_student_attendance_for_date(sid, today_date) if sid else None
            att_disp = att_rec['status'] if att_rec else "Present"
            sch_name = s.get('school_name') or s.get('previous_school') or ''
            col_name = s.get('college_name') or s.get('school_name') or s.get('previous_school') or ''

            if cat == "School":
                self.tree.insert("", tk.END, values=(
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
                ))
            else: # College
                self.tree.insert("", tk.END, values=(
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
                ))

    def _on_student_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0])['values']
        if not vals:
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
        now_t = get_current_time()

        saved_count = 0
        cat = self.combo_category.get() if hasattr(self, 'combo_category') else "School"
        name_idx = 1 if cat == "School" else 2
        last_name = ""
        last_sid = ""

        for item in sel:
            vals = self.tree.item(item)['values']
            if not vals:
                continue
            sid = str(vals[0]).strip()
            last_sid = sid
            if len(vals) > name_idx:
                last_name = str(vals[name_idx]).strip()
            ok, _ = self.db.mark_attendance(sid, today, now_t, status)
            if ok:
                saved_count += 1

        if saved_count > 0:
            msg_text = f"Attendance saved as '{status}' for '{last_name}' ({last_sid})." if saved_count == 1 else f"Attendance saved as '{status}' for {saved_count} student(s)."
            messagebox.showinfo("Success", msg_text)
            self.load_students_table()
        else:
            messagebox.showerror("Error", "Failed to save attendance.")

    def add_student_dialog(self):
        StudentFormDialog(self, self.db, on_save_callback=self.load_students_table)

    def edit_selected_student(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a student from the table.")
            return
        item_vals = self.tree.item(sel[0])['values']
        if not item_vals:
            return
        sid = str(item_vals[0]).strip()
        StudentFormDialog(self, self.db, student_id=sid, on_save_callback=self.load_students_table)

    def delete_selected_student(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a student from the table.")
            return
        sid = self.tree.item(sel[0])['values'][0]
        sname = self.tree.item(sel[0])['values'][1]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete Student '{sname}' ({sid})?\nAll attendance and marks records will be permanently removed."):
            self.db.delete_student(sid)
            messagebox.showinfo("Deleted", f"Student '{sname}' deleted.")
            self.load_students_table()

    def open_selected_marks(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a student from the table.")
            return
        sid = self.tree.item(sel[0])['values'][0]
        sname = self.tree.item(sel[0])['values'][1]
        MarksEntryDialog(self, self.db, sid, sname)

    def register_selected_face(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a student from the table.")
            return
        sid = self.tree.item(sel[0])['values'][0]
        sname = self.tree.item(sel[0])['values'][1]
        from face_attendance.face_registration import FaceRegisterWindow
        FaceRegisterWindow(self, sid, sname, self.db)

    def show_attendance_scanner(self):
        self.clear_content()
        view_frame = AttendanceViewFrame(self.content_frame, self.db, is_admin_or_teacher=True)
        view_frame.pack(fill=tk.BOTH, expand=True)

        teacher_info = self.db.get_teacher_by_user_id(self.user_data['id'])
        t_id = teacher_info['teacher_id'] if teacher_info else None

        from face_attendance.face_recognition import TeacherFaceAttendanceWindow
        TeacherFaceAttendanceWindow(self, self.db, teacher_id=t_id, on_attendance_marked=view_frame.refresh_table)

    def show_marks(self):
        self.show_students()

    def show_ml_predictions(self):
        self.clear_content()

        ttk.Label(self.content_frame, text="🤖 Class ML Performance Predictor", font=FONTS["h1"]).pack(anchor=tk.W, pady=(0, 10))

        tbl_frame = ttk.Frame(self.content_frame)
        tbl_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "name", "att", "study", "predicted_score", "category", "risk")
        tree = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=14)

        tree.heading("id", text="Student ID")
        tree.heading("name", text="Name")
        tree.heading("att", text="Attendance %")
        tree.heading("study", text="Study Hrs")
        tree.heading("predicted_score", text="Pred Score %")
        tree.heading("category", text="Predicted Category")
        tree.heading("risk", text="Risk Level")

        for c in cols:
            tree.column(c, width=110, anchor="center")
        tree.column("name", width=160, anchor="w")

        scrollbar = ttk.Scrollbar(tbl_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        students = self.db.get_all_students()
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

            tree.insert("", tk.END, values=(
                sid, s['name'], f"{att}%", s.get('study_hours', 2.0),
                f"{pred['predicted_score']}%", pred['category'], pred['risk_level']
            ))

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

        # 1. School Time
        ttk.Label(grid_frame, text="School Time:", font=("Segoe UI", 11, "bold")).grid(row=1, column=0, sticky=tk.W, pady=6, padx=(0, 15))
        ttk.Label(grid_frame, text=school_time_str, font=("Segoe UI", 11)).grid(row=1, column=1, sticky=tk.W, pady=6)

        # 2. Start Time (Editable Manual Input)
        start_disp = astart if astart else ""
        ttk.Label(grid_frame, text="Start Time:", font=("Segoe UI", 11, "bold")).grid(row=2, column=0, sticky=tk.W, pady=6, padx=(0, 15))
        self.ent_start_time = ttk.Entry(grid_frame, font=("Segoe UI", 11), width=20)
        self.ent_start_time.grid(row=2, column=1, sticky=tk.W, pady=6)
        if start_disp:
            self.ent_start_time.insert(0, start_disp)

        # 3. End Time (Editable Manual Input)
        end_disp = aend if aend else ""
        ttk.Label(grid_frame, text="End Time:", font=("Segoe UI", 11, "bold")).grid(row=3, column=0, sticky=tk.W, pady=6, padx=(0, 15))
        self.ent_end_time = ttk.Entry(grid_frame, font=("Segoe UI", 11), width=20)
        self.ent_end_time.grid(row=3, column=1, sticky=tk.W, pady=6)
        if end_disp:
            self.ent_end_time.insert(0, end_disp)

        # Save Button Container Frame
        btn_frame = ttk.Frame(work_card)
        btn_frame.pack(anchor=tk.W, pady=(15, 0))

        btn_save = ttk.Button(
            btn_frame,
            text="Save Work Time",
            command=self.save_manual_work_time
        )
        btn_save.pack(side=tk.LEFT)

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

        sal = self.db.get_teacher_salary_summary(self.teacher_id)

        card = ttk.LabelFrame(self.content_frame, text=f" Monthly Salary Statement - {sal['teacher_name']} ({sal['teacher_id']}) ", padding=20)
        card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        sal_txt = f"""
👨‍🏫 Teacher Name: {sal['teacher_name']}
🆔 Teacher ID: {sal['teacher_id']}
🏢 Department: {sal['department']}

------------------------------------------------------
📅 Present Days: {sal['present_days']} / {sal['working_days']} Working Days
⌛ Total Working Hours: {sal['total_working_hours']:.2f} hrs
⏰ Late Summary: {sal['late_summary_mins']} mins late total
⭐ Overtime Hours: {sal['overtime_hours']:.2f} hrs

------------------------------------------------------
💵 Base Monthly Salary: ${sal['base_salary']:.2f}
💰 Earned Base Salary: ${sal['earned_base_salary']:.2f}
📈 Overtime Allowance: ${sal['overtime_amount']:.2f}
------------------------------------------------------
✨ TOTAL NET SALARY: ${sal['total_salary']:.2f}
        """
        ttk.Label(card, text=sal_txt, font=FONTS["h3"], justify=tk.LEFT, foreground=COLORS["primary"]).pack(anchor=tk.W)

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
            • Phone Number: {t_rec.get('phone', 'N/A')}
            • Email Address: {t_rec.get('email', 'N/A')}
            • Address: {t_rec.get('address', 'N/A')}
            • Department: {t_rec.get('department', 'N/A')}
            • Designation: {t_rec.get('designation', 'N/A')}
            • Joining Date: {t_rec.get('joining_date', 'N/A')}
            """
            ttk.Label(card, text=t_info, font=("Consolas", 11), justify="left").pack(anchor=tk.W, pady=10)
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

            # Phone
            ttk.Label(form_card, text="Phone Number *:", font=FONTS["body_bold"]).grid(row=2, column=0, sticky="w", pady=8)
            entry_phone = ttk.Entry(form_card, width=35)
            entry_phone.insert(0, t_rec.get('phone', ''))
            entry_phone.grid(row=2, column=1, sticky="w", pady=8, padx=10)

            # Email
            ttk.Label(form_card, text="Email Address:", font=FONTS["body_bold"]).grid(row=3, column=0, sticky="w", pady=8)
            entry_email = ttk.Entry(form_card, width=35)
            entry_email.insert(0, t_rec.get('email', ''))
            entry_email.grid(row=3, column=1, sticky="w", pady=8, padx=10)

            # Address
            ttk.Label(form_card, text="Address:", font=FONTS["body_bold"]).grid(row=4, column=0, sticky="w", pady=8)
            entry_address = ttk.Entry(form_card, width=40)
            entry_address.insert(0, t_rec.get('address', ''))
            entry_address.grid(row=4, column=1, sticky="w", pady=8, padx=10)

            # Dept / Designation (Read only)
            ttk.Label(form_card, text="Department / Designation:", font=FONTS["body_bold"]).grid(row=5, column=0, sticky="w", pady=8)
            ttk.Label(form_card, text=f"{t_rec.get('department', 'N/A')} - {t_rec.get('designation', 'N/A')}", font=FONTS["body"]).grid(row=5, column=1, sticky="w", pady=8, padx=10)

            def save_teacher_profile_callback():
                from utils.validators import validate_email, validate_phone
                name = entry_name.get().strip()
                phone = entry_phone.get().strip()
                email = entry_email.get().strip()
                address = entry_address.get().strip()

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
            btn_bar.grid(row=6, column=0, columnspan=2, sticky="w", pady=(15, 0))

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

