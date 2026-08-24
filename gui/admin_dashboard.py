import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DBManager
from gui.theme import COLORS, FONTS, StatCard
from gui.student_forms import StudentFormDialog
from gui.teacher_forms import TeacherFormDialog
from gui.parent_forms import ParentFormDialog
from gui.marks_view import MarksEntryDialog
from gui.attendance_view import AttendanceViewFrame
from gui.charts_view import AnalyticsChartsFrame
from reports.report_manager import ReportManager
from ml.prediction import PerformancePredictor
from utils.helpers import get_current_date

class AdminDashboard(tk.Toplevel):
    """Primary Control Center for Administrator Role."""
    def __init__(self, welcome_win: tk.Tk, db_manager: DBManager, user_data: dict):
        super().__init__(welcome_win)
        self.welcome_win = welcome_win
        self.db = db_manager
        self.user_data = user_data
        self.reports = ReportManager(db_manager)
        self.predictor = PerformancePredictor()

        self.title("Admin Dashboard - Student Management System")
        self.geometry("1120x730")
        self.minsize(1000, 650)
        self.protocol("WM_DELETE_WINDOW", self.on_logout)

        self._build_ui()
        self.refresh_all_data()

    def _build_ui(self):
        # Main Layout: Sidebar (Left) + Content (Right)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. Top Header Bar
        top_bar = tk.Frame(self, bg="#0f172a", height=60)
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        top_bar.pack_propagate(False)

        lbl_title = tk.Label(top_bar, text="🛡️ Admin Control Panel", font=("Segoe UI", 14, "bold"), bg="#0f172a", fg="#ffffff")
        lbl_title.pack(side=tk.LEFT, padx=20)

        btn_logout = tk.Button(top_bar, text="🚪 Logout", font=("Segoe UI", 9, "bold"), bg="#dc2626", fg="#ffffff", activebackground="#b91c1c", activeforeground="#ffffff", bd=0, cursor="hand2", command=self.on_logout)
        btn_logout.pack(side=tk.RIGHT, padx=20, ipadx=10, ipady=4)

        lbl_user = tk.Label(top_bar, text=f"LoggedIn: {self.user_data['username']} (Admin)", font=("Segoe UI", 9), bg="#0f172a", fg="#94a3b8")
        lbl_user.pack(side=tk.RIGHT, padx=10)

        # 2. Sidebar Navigation
        sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=220)
        sidebar.grid(row=1, column=0, sticky="nsew")

        nav_buttons = [
            ("📊 Dashboard Overview", self.show_overview),
            ("🎓 Student Management", self.show_students),
            ("👨‍🏫 Teacher Management", self.show_teachers),
            ("💵 Teacher Payroll & Salaries", self.show_teacher_salaries),
            ("👨‍👩‍👧 Parent Management", self.show_parents),
            ("📅 Attendance Records", self.show_attendance),
            ("📑 Marks & Evaluation", self.show_marks),
            ("🤖 ML Prediction Center", self.show_ml_center),
            ("⚙️ Settings", self.show_settings),
            ("📅 Holiday Management", self.show_holidays),
            ("🚪 Logout", self.on_logout)
        ]

        for text, cmd in nav_buttons:
            btn = ttk.Button(sidebar, text=text, style="Sidebar.TButton", command=cmd)
            btn.pack(fill=tk.X, pady=2)

        # 3. Dynamic Content Area
        self.content_frame = ttk.Frame(self, padding=15)
        self.content_frame.grid(row=1, column=1, sticky="nsew")

        self.show_overview()

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    # --- OVERVIEW SCREEN ---
    def show_overview(self):
        self.clear_content()

        ttk.Label(self.content_frame, text="System Statistics & Live Metrics", font=FONTS["h1"]).pack(anchor=tk.W, pady=(0, 10))

        # Metrics Cards Frame
        cards_frame = ttk.Frame(self.content_frame)
        cards_frame.pack(fill=tk.X, pady=(0, 15))
        cards_frame.columnconfigure((0,1,2,3,4,5,6), weight=1)

        summary = self.db.get_dashboard_summary()

        StatCard(cards_frame, "Total Students", summary['total_students'], "🎓", "#2563eb").grid(row=0, column=0, padx=4, sticky="ew")
        StatCard(cards_frame, "Total Teachers", summary['total_teachers'], "👨‍🏫", "#0d9488").grid(row=0, column=1, padx=4, sticky="ew")
        StatCard(cards_frame, "Total Parents", summary.get('total_parents', 0), "👨‍👩‍👧", "#059669").grid(row=0, column=2, padx=4, sticky="ew")
        StatCard(cards_frame, "Today Present", summary['today_present'], "✅", "#16a34a").grid(row=0, column=3, padx=4, sticky="ew")
        StatCard(cards_frame, "Today Absent", summary['today_absent'], "❌", "#dc2626").grid(row=0, column=4, padx=4, sticky="ew")
        StatCard(cards_frame, "Avg Attendance", f"{summary['avg_attendance']}%", "📈", "#7c3aed").grid(row=0, column=5, padx=4, sticky="ew")
        StatCard(cards_frame, "Avg Performance", f"{summary['avg_performance']}%", "⭐", "#d97706").grid(row=0, column=6, padx=4, sticky="ew")

        # System Charts
        charts_frame = AnalyticsChartsFrame(self.content_frame, self.db)
        charts_frame.pack(fill=tk.BOTH, expand=True)

    # --- STUDENT MANAGEMENT ---
    def show_students(self):
        self.clear_content()

        hdr = ttk.Frame(self.content_frame)
        hdr.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(hdr, text="🎓 Student Management", font=FONTS["h1"]).pack(side=tk.LEFT)

        btn_export = ttk.Button(hdr, text="📥 Export CSV", style="Accent.TButton", command=self.export_students_csv)
        btn_export.pack(side=tk.RIGHT, padx=5)

        # Top Action Bar & Search (Add, Edit, Delete, Search together at top)
        action_frame = ttk.Frame(self.content_frame)
        action_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(action_frame, text="➕ Add Student", style="Primary.TButton", command=self.add_student_dialog).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="✏️ Edit Student", command=self.edit_selected_student).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="🗑️ Delete Student", style="Danger.TButton", command=self.delete_selected_student).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="📷 Register Face", style="Accent.TButton", command=self.register_selected_face).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="📊 Enter Marks", command=self.enter_selected_marks).pack(side=tk.LEFT, padx=3)

        ttk.Label(action_frame, text="🔍 Search:", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(15, 2))
        self.entry_search = ttk.Entry(action_frame, width=22)
        self.entry_search.pack(side=tk.LEFT, padx=3)
        self.entry_search.bind("<KeyRelease>", lambda e: self.load_students_table())

        ttk.Label(action_frame, text="Dept:", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(10, 2))
        self.combo_dept_filter = ttk.Combobox(action_frame, values=["All", "Computer Science & Engineering", "Information Technology", "Artificial Intelligence"], state="readonly", width=18)
        self.combo_dept_filter.set("All")
        self.combo_dept_filter.pack(side=tk.LEFT, padx=3)
        self.combo_dept_filter.bind("<<ComboboxSelected>>", lambda e: self.load_students_table())

        # Table
        tbl_frame = ttk.Frame(self.content_frame)
        tbl_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "name", "email", "phone", "course", "dept", "class")
        self.tree_students = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=14)

        self.tree_students.heading("id", text="Student ID")
        self.tree_students.heading("name", text="Full Name")
        self.tree_students.heading("email", text="Email")
        self.tree_students.heading("phone", text="Phone")
        self.tree_students.heading("course", text="Course / Program")
        self.tree_students.heading("dept", text="Department")
        self.tree_students.heading("class", text="Class")

        self.tree_students.column("id", width=95, anchor="center")
        self.tree_students.column("name", width=140, anchor="w")
        self.tree_students.column("email", width=150, anchor="w")
        self.tree_students.column("phone", width=105, anchor="center")
        self.tree_students.column("course", width=140, anchor="w")
        self.tree_students.column("dept", width=140, anchor="w")
        self.tree_students.column("class", width=90, anchor="center")

        scrollbar = ttk.Scrollbar(tbl_frame, orient="vertical", command=self.tree_students.yview)
        self.tree_students.configure(yscroll=scrollbar.set)
        self.tree_students.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_students.bind("<Double-1>", lambda e: self.edit_selected_student())

        self.load_students_table()

    def load_students_table(self):
        for item in self.tree_students.get_children():
            self.tree_students.delete(item)

        st = self.entry_search.get().strip() if hasattr(self, 'entry_search') else ""
        dept = self.combo_dept_filter.get() if hasattr(self, 'combo_dept_filter') else "All"

        students = self.db.get_all_students(search_term=st, filter_dept=dept)
        for s in students:
            self.tree_students.insert("", tk.END, values=(
                s['student_id'], s['name'], s.get('email', ''), s.get('phone', ''),
                s.get('course', ''), s.get('department', ''), s.get('current_class', '')
            ))

    def add_student_dialog(self):
        StudentFormDialog(self, self.db, on_save_callback=self.load_students_table)

    def edit_selected_student(self):
        sel = self.tree_students.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a student from the table.")
            return
        item_vals = self.tree_students.item(sel[0])['values']
        if not item_vals:
            return
        sid = str(item_vals[0]).strip()
        StudentFormDialog(self, self.db, student_id=sid, on_save_callback=self.load_students_table)

    def register_selected_face(self):
        sel = self.tree_students.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a student from the table to register face.")
            return
        sid = self.tree_students.item(sel[0])['values'][0]
        sname = self.tree_students.item(sel[0])['values'][1]

        from face_attendance.face_registration import FaceRegisterWindow
        FaceRegisterWindow(self, sid, sname, self.db)

    def enter_selected_marks(self):
        sel = self.tree_students.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a student from the table.")
            return
        sid = self.tree_students.item(sel[0])['values'][0]
        sname = self.tree_students.item(sel[0])['values'][1]
        MarksEntryDialog(self, self.db, sid, sname)

    def delete_selected_student(self):
        sel = self.tree_students.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a student from the table.")
            return
        sid = self.tree_students.item(sel[0])['values'][0]
        sname = self.tree_students.item(sel[0])['values'][1]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete Student '{sname}' ({sid})?\nAll attendance and marks records will be permanently removed."):
            self.db.delete_student(sid)
            messagebox.showinfo("Deleted", f"Student '{sname}' deleted.")
            self.load_students_table()

    def export_students_csv(self):
        df = self.reports.generate_student_list_dataframe()
        ok, msg = self.reports.export_dataframe_to_csv(df, "data/student_report.csv")
        if ok:
            messagebox.showinfo("Export Successful", msg)
        else:
            messagebox.showerror("Export Failed", msg)

    # --- TEACHER MANAGEMENT ---
    def show_teachers(self):
        self.clear_content()

        hdr = ttk.Frame(self.content_frame)
        hdr.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(hdr, text="👨‍🏫 Teacher Management", font=FONTS["h1"]).pack(side=tk.LEFT)

        # Top Action Bar & Search (Add, Edit, Delete, Search together at top)
        action_frame = ttk.Frame(self.content_frame)
        action_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(action_frame, text="➕ Add Teacher", style="Primary.TButton", command=self.add_teacher_dialog).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="✏️ Edit Teacher", command=self.edit_selected_teacher).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="🗑️ Delete Teacher", style="Danger.TButton", command=self.delete_selected_teacher).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="📷 Register Face", style="Accent.TButton", command=self.register_selected_teacher_face).pack(side=tk.LEFT, padx=3)

        ttk.Label(action_frame, text="🔍 Search:", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(15, 2))
        self.entry_teacher_search = ttk.Entry(action_frame, width=25)
        self.entry_teacher_search.pack(side=tk.LEFT, padx=3)
        self.entry_teacher_search.bind("<KeyRelease>", lambda e: self.load_teachers_table())

        # Table
        tbl_frame = ttk.Frame(self.content_frame)
        tbl_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "name", "email", "phone", "dept", "desig")
        self.tree_teachers = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=14)

        self.tree_teachers.heading("id", text="Teacher ID")
        self.tree_teachers.heading("name", text="Full Name")
        self.tree_teachers.heading("email", text="Email")
        self.tree_teachers.heading("phone", text="Phone")
        self.tree_teachers.heading("dept", text="Department")
        self.tree_teachers.heading("desig", text="Designation")

        self.tree_teachers.column("id", width=110, anchor="center")
        self.tree_teachers.column("name", width=180, anchor="w")
        self.tree_teachers.column("email", width=180, anchor="w")
        self.tree_teachers.column("phone", width=120, anchor="center")
        self.tree_teachers.column("dept", width=160, anchor="w")
        self.tree_teachers.column("desig", width=140, anchor="w")

        scrollbar = ttk.Scrollbar(tbl_frame, orient="vertical", command=self.tree_teachers.yview)
        self.tree_teachers.configure(yscroll=scrollbar.set)
        self.tree_teachers.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.load_teachers_table()

    def load_teachers_table(self):
        for item in self.tree_teachers.get_children():
            self.tree_teachers.delete(item)
        st = self.entry_teacher_search.get().strip() if hasattr(self, 'entry_teacher_search') else ""
        teachers = self.db.get_all_teachers(search_term=st)
        for t in teachers:
            self.tree_teachers.insert("", tk.END, values=(
                t['teacher_id'], t['name'], t.get('email', ''), t.get('phone', ''),
                t.get('department', ''), t.get('designation', '')
            ))

    def add_teacher_dialog(self):
        TeacherFormDialog(self, self.db, on_save_callback=self.load_teachers_table)

    def edit_selected_teacher(self):
        sel = self.tree_teachers.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a teacher from the table.")
            return
        tid = self.tree_teachers.item(sel[0])['values'][0]
        TeacherFormDialog(self, self.db, teacher_id=tid, on_save_callback=self.load_teachers_table)

    def delete_selected_teacher(self):
        sel = self.tree_teachers.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a teacher from the table.")
            return
        tid = self.tree_teachers.item(sel[0])['values'][0]
        tname = self.tree_teachers.item(sel[0])['values'][1]

        if messagebox.askyesno("Confirm Delete", f"Delete Teacher '{tname}' ({tid})?"):
            self.db.delete_teacher(tid)
            messagebox.showinfo("Deleted", f"Teacher '{tname}' removed.")
            self.load_teachers_table()

    def register_selected_teacher_face(self):
        sel = self.tree_teachers.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a teacher from the table to register face.")
            return
        tid = self.tree_teachers.item(sel[0])['values'][0]
        tname = self.tree_teachers.item(sel[0])['values'][1]

        from face_attendance.face_registration import FaceRegisterWindow
        FaceRegisterWindow(self, tid, tname, self.db)

    def show_teacher_salaries(self):
        self.clear_content()
        ttk.Label(self.content_frame, text="💵 Teacher Salary Management", font=FONTS["h1"]).pack(anchor=tk.W, pady=(0, 10))

        # Admin Edit Form Box (Set/Update Individual Teacher Salary)
        form_card = ttk.LabelFrame(self.content_frame, text=" Set / Edit Individual Teacher Salary ", padding=15)
        form_card.pack(fill=tk.X, pady=(0, 15))

        f_row = ttk.Frame(form_card)
        f_row.pack(fill=tk.X, pady=5)

        ttk.Label(f_row, text="Select Teacher Name *:", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(0, 5))
        
        teachers = self.db.get_all_teachers()
        teacher_options = [f"{t['name']} ({t['teacher_id']})" for t in teachers]
        self.combo_teacher_salary = ttk.Combobox(f_row, values=teacher_options, state="readonly", width=30)
        self.combo_teacher_salary.pack(side=tk.LEFT, padx=5)

        ttk.Label(f_row, text="Monthly Salary (₹) *:", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(15, 5))
        self.entry_teacher_monthly_salary = ttk.Entry(f_row, width=15)
        self.entry_teacher_monthly_salary.pack(side=tk.LEFT, padx=5)

        btn_save = ttk.Button(f_row, text="💾 Save Salary", style="Primary.TButton", command=self.save_teacher_salary)
        btn_save.pack(side=tk.LEFT, padx=15)

        def _on_teacher_selected(event=None):
            sel = self.combo_teacher_salary.get()
            if not sel:
                return
            try:
                tid = sel.split("(")[-1].rstrip(")").strip()
                t_rec = self.db.get_teacher(tid)
                if t_rec:
                    curr_sal = t_rec.get("monthly_salary", 35000.0)
                    self.entry_teacher_monthly_salary.delete(0, tk.END)
                    self.entry_teacher_monthly_salary.insert(0, f"{float(curr_sal):g}")
            except Exception as ex:
                print("Error loading teacher salary:", ex)

        self.combo_teacher_salary.bind("<<ComboboxSelected>>", _on_teacher_selected)
        if teacher_options:
            self.combo_teacher_salary.set(teacher_options[0])
            _on_teacher_selected()

        # Records Table Frame
        tbl_frame = ttk.Frame(self.content_frame)
        tbl_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "name", "dept", "base_sal", "present_days", "work_hrs", "late_mins", "overtime", "total_sal")
        self.tree_salaries = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=12)

        self.tree_salaries.heading("id", text="Teacher ID")
        self.tree_salaries.heading("name", text="Teacher Name")
        self.tree_salaries.heading("dept", text="Department")
        self.tree_salaries.heading("base_sal", text="Monthly Salary (Base)")
        self.tree_salaries.heading("present_days", text="Present Days")
        self.tree_salaries.heading("work_hrs", text="Total Work Hrs")
        self.tree_salaries.heading("late_mins", text="Late Mins")
        self.tree_salaries.heading("overtime", text="Overtime Hrs")
        self.tree_salaries.heading("total_sal", text="Total Net Salary")

        self.tree_salaries.column("id", width=100, anchor="center")
        self.tree_salaries.column("name", width=160, anchor="w")
        self.tree_salaries.column("dept", width=130, anchor="w")
        self.tree_salaries.column("base_sal", width=140, anchor="center")
        self.tree_salaries.column("present_days", width=100, anchor="center")
        self.tree_salaries.column("work_hrs", width=110, anchor="center")
        self.tree_salaries.column("late_mins", width=95, anchor="center")
        self.tree_salaries.column("overtime", width=100, anchor="center")
        self.tree_salaries.column("total_sal", width=120, anchor="center")

        sb = ttk.Scrollbar(tbl_frame, orient="vertical", command=self.tree_salaries.yview)
        self.tree_salaries.configure(yscroll=sb.set)
        self.tree_salaries.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.load_teacher_salaries_table()

    def load_teacher_salaries_table(self):
        if not hasattr(self, 'tree_salaries'):
            return
        for item in self.tree_salaries.get_children():
            self.tree_salaries.delete(item)

        salaries = self.db.get_all_teachers_salary_summary()
        for s in salaries:
            self.tree_salaries.insert("", tk.END, values=(
                s['teacher_id'], s['teacher_name'], s['department'],
                f"₹{s['base_salary']:,.2f}",
                f"{s['present_days']} / {s['working_days']}",
                f"{s['total_working_hours']:.2f}h",
                f"{s['late_summary_mins']}m",
                f"{s['overtime_hours']:.2f}h",
                f"₹{s['total_salary']:,.2f}"
            ))

    def save_teacher_salary(self):
        sel = self.combo_teacher_salary.get()
        if not sel:
            messagebox.showwarning("Validation Error", "Please select a teacher from the dropdown list.")
            return

        sal_str = self.entry_teacher_monthly_salary.get().strip()
        try:
            val = float(sal_str)
            if val < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid positive numeric salary.")
            return

        try:
            tid = sel.split("(")[-1].rstrip(")").strip()
            t_rec = self.db.get_teacher(tid)
            tname = t_rec['name'] if t_rec else sel
        except Exception:
            messagebox.showerror("Error", "Could not identify teacher record.")
            return

        ok = self.db.update_teacher_salary(tid, val)
        if ok:
            messagebox.showinfo("Salary Updated", f"Monthly salary for Teacher '{tname}' ({tid}) updated successfully to ₹{val:,.2f}.")
            self.load_teacher_salaries_table()
        else:
            messagebox.showerror("Database Error", f"Failed to update salary for Teacher '{tname}'.")

    # --- PARENT MANAGEMENT ---
    def show_parents(self):
        self.clear_content()

        hdr = ttk.Frame(self.content_frame)
        hdr.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(hdr, text="👨‍👩‍👧 Parent Management", font=FONTS["h1"]).pack(side=tk.LEFT)

        # Top Action Bar & Search (Add, Edit, Delete, Search together at top)
        action_frame = ttk.Frame(self.content_frame)
        action_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(action_frame, text="➕ Add Parent", style="Primary.TButton", command=self.add_parent_dialog).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="✏️ Edit Parent", command=self.edit_selected_parent).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="🗑️ Delete Parent", style="Danger.TButton", command=self.delete_selected_parent).pack(side=tk.LEFT, padx=3)

        ttk.Label(action_frame, text="🔍 Search:", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(15, 2))
        self.entry_parent_search = ttk.Entry(action_frame, width=25)
        self.entry_parent_search.pack(side=tk.LEFT, padx=3)
        self.entry_parent_search.bind("<KeyRelease>", lambda e: self.load_parents_table())

        # Table
        tbl_frame = ttk.Frame(self.content_frame)
        tbl_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("pid", "name", "phone", "email", "relation", "student")
        self.tree_parents = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=14)

        self.tree_parents.heading("pid", text="Parent ID Code")
        self.tree_parents.heading("name", text="Parent Full Name")
        self.tree_parents.heading("phone", text="Phone")
        self.tree_parents.heading("email", text="Email")
        self.tree_parents.heading("relation", text="Relationship")
        self.tree_parents.heading("student", text="Linked Child Student ID")

        self.tree_parents.column("pid", width=120, anchor="center")
        self.tree_parents.column("name", width=180, anchor="w")
        self.tree_parents.column("phone", width=120, anchor="center")
        self.tree_parents.column("email", width=180, anchor="w")
        self.tree_parents.column("relation", width=110, anchor="center")
        self.tree_parents.column("student", width=150, anchor="center")

        scrollbar = ttk.Scrollbar(tbl_frame, orient="vertical", command=self.tree_parents.yview)
        self.tree_parents.configure(yscroll=scrollbar.set)
        self.tree_parents.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.load_parents_table()

    def load_parents_table(self):
        for item in self.tree_parents.get_children():
            self.tree_parents.delete(item)
        st = self.entry_parent_search.get().strip() if hasattr(self, 'entry_parent_search') else ""
        parents = self.db.get_all_parents(search_term=st)
        for p in parents:
            self.tree_parents.insert("", tk.END, values=(
                p.get('parent_id_code', ''), p['name'], p.get('phone', ''),
                p.get('email', ''), p.get('relationship', 'Parent'), p.get('student_id', '')
            ))

    def add_parent_dialog(self):
        ParentFormDialog(self, self.db, on_save_callback=self.load_parents_table)

    def edit_selected_parent(self):
        sel = self.tree_parents.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a parent from the table.")
            return
        pid = self.tree_parents.item(sel[0])['values'][0]
        ParentFormDialog(self, self.db, parent_id_code=pid, on_save_callback=self.load_parents_table)

    def delete_selected_parent(self):
        sel = self.tree_parents.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a parent from the table.")
            return
        pid = self.tree_parents.item(sel[0])['values'][0]
        pname = self.tree_parents.item(sel[0])['values'][1]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete Parent '{pname}' ({pid})?"):
            self.db.delete_parent(pid)
            messagebox.showinfo("Deleted", f"Parent '{pname}' removed.")
            self.load_parents_table()

    # --- ATTENDANCE RECORDS ---
    def show_attendance(self):
        self.clear_content()
        AttendanceViewFrame(self.content_frame, self.db, is_admin_or_teacher=True).pack(fill=tk.BOTH, expand=True)

    # --- MARKS & EVALUATION ---
    def show_marks(self):
        self.clear_content()

        hdr = ttk.Frame(self.content_frame)
        hdr.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(hdr, text="📑 Academic Marks & Grades", font=FONTS["h1"]).pack(side=tk.LEFT)

        # Table
        tbl_frame = ttk.Frame(self.content_frame)
        tbl_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "name", "class", "subject", "internal", "mid", "proj", "viva", "final", "total", "pct", "grade", "status")
        tree = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=15)

        tree.heading("id", text="Student ID")
        tree.heading("name", text="Name")
        tree.heading("class", text="Class")
        tree.heading("subject", text="Subject")
        tree.heading("internal", text="Internal")
        tree.heading("mid", text="MidTerm")
        tree.heading("proj", text="Project")
        tree.heading("viva", text="Viva")
        tree.heading("final", text="Final")
        tree.heading("total", text="Total")
        tree.heading("pct", text="Pct %")
        tree.heading("grade", text="Grade")
        tree.heading("status", text="Status")

        for c in cols:
            tree.column(c, width=75, anchor="center")
        tree.column("name", width=140, anchor="w")
        tree.column("subject", width=130, anchor="w")

        students = self.db.get_all_students()
        for s in students:
            all_m = self.db.get_all_student_marks(s['student_id'])
            for m in all_m:
                tree.insert("", tk.END, values=(
                    s['student_id'], s['name'], s.get('current_class', ''),
                    m['subject'], m['internal_marks'], m['mid_term_marks'], m['project_marks'],
                    m['viva_marks'], m['final_exam_marks'], m['total_marks'], f"{m['percentage']:.1f}%",
                    m['grade'], m['status']
                ))

        tree.pack(fill=tk.BOTH, expand=True)

    # --- ML PREDICTION CENTER ---
    def show_ml_center(self):
        self.clear_content()

        hdr = ttk.Frame(self.content_frame)
        hdr.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(hdr, text="🤖 Machine Learning Performance Predictions", font=FONTS["h1"]).pack(side=tk.LEFT)

        btn_retrain = ttk.Button(hdr, text="⚡ Retrain ML Model", style="Primary.TButton", command=self.retrain_model)
        btn_retrain.pack(side=tk.RIGHT)

        tbl_frame = ttk.Frame(self.content_frame)
        tbl_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "name", "att", "study", "pred_score", "category", "risk")
        tree = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=15)

        tree.heading("id", text="Student ID")
        tree.heading("name", text="Full Name")
        tree.heading("att", text="Att %")
        tree.heading("study", text="Study Hrs")
        tree.heading("pred_score", text="Predicted %")
        tree.heading("category", text="Performance Category")
        tree.heading("risk", text="Risk Level")

        tree.column("id", width=110, anchor="center")
        tree.column("name", width=180, anchor="w")
        tree.column("att", width=90, anchor="center")
        tree.column("study", width=100, anchor="center")
        tree.column("pred_score", width=120, anchor="center")
        tree.column("category", width=170, anchor="center")
        tree.column("risk", width=130, anchor="center")

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

        tree.pack(fill=tk.BOTH, expand=True)

    def retrain_model(self):
        df = self.reports.generate_student_list_dataframe()
        metrics = self.predictor.train_model(df)
        messagebox.showinfo("Model Retrained", f"ML Model trained successfully!\n\nR2 Score: {metrics['r2']:.2f}\nMAE: {metrics['mae']:.2f}")

    # --- NOTIFICATIONS ---
    def show_notifications(self):
        self.clear_content()

        ttk.Label(self.content_frame, text="🔔 System Notifications & Logs", font=FONTS["h1"]).pack(anchor=tk.W, pady=(0, 10))

        notifs = self.db.get_notifications("Admin")
        
        container = ttk.Frame(self.content_frame)
        container.pack(fill=tk.BOTH, expand=True)

        if not notifs:
            ttk.Label(container, text="No system notifications recorded yet.", font=FONTS["body_bold"]).pack(pady=20)
            return

        for n in notifs:
            card = ttk.Frame(container, style="Card.TFrame", padding=10)
            card.pack(fill=tk.X, pady=5)

            title = f"[{n['date']}] {n['title']} ({n['recipient_role']})"
            ttk.Label(card, text=title, font=FONTS["body_bold"], style="Card.TLabel").pack(anchor=tk.W)
            ttk.Label(card, text=n['message'], font=FONTS["body"], style="Card.TLabel").pack(anchor=tk.W, pady=(2, 0))

    def refresh_all_data(self):
        pass

    def show_settings(self):
        self.clear_content()
        from gui.settings_view import SettingsViewFrame
        SettingsViewFrame(self.content_frame, self.db, self.user_data, "Admin", on_cancel=self.show_overview).pack(fill=tk.BOTH, expand=True)

    def _open_date_picker(self, entry_widget):
        win = tk.Toplevel(self)
        win.title("📅 Select Date")
        win.geometry("300x220")
        win.grab_set()

        ttk.Label(win, text="Select Date", font=FONTS["h3"]).pack(pady=10)

        f = ttk.Frame(win, padding=10)
        f.pack(fill=tk.BOTH, expand=True)

        import datetime
        now = datetime.datetime.now()

        curr_val = entry_widget.get().strip()
        curr_d, curr_m, curr_y = str(now.day).zfill(2), str(now.month).zfill(2), str(now.year)
        if curr_val:
            parts = curr_val.replace('/', '-').split('-')
            if len(parts) == 3:
                if len(parts[0]) == 4: # YYYY-MM-DD
                    curr_y, curr_m, curr_d = parts[0], parts[1].zfill(2), parts[2].zfill(2)
                elif len(parts[2]) == 4: # DD-MM-YYYY
                    curr_d, curr_m, curr_y = parts[0].zfill(2), parts[1].zfill(2), parts[2]

        ttk.Label(f, text="Day:").grid(row=0, column=0, padx=5, pady=5)
        cb_day = ttk.Combobox(f, values=[str(i).zfill(2) for i in range(1, 32)], width=5, state="readonly")
        cb_day.set(curr_d)
        cb_day.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(f, text="Month:").grid(row=1, column=0, padx=5, pady=5)
        cb_month = ttk.Combobox(f, values=[str(i).zfill(2) for i in range(1, 13)], width=5, state="readonly")
        cb_month.set(curr_m)
        cb_month.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(f, text="Year:").grid(row=2, column=0, padx=5, pady=5)
        cb_year = ttk.Combobox(f, values=[str(y) for y in range(2024, 2036)], width=8, state="readonly")
        cb_year.set(curr_y)
        cb_year.grid(row=2, column=1, padx=5, pady=5)

        def set_date():
            d = cb_day.get()
            m = cb_month.get()
            y = cb_year.get()
            selected = f"{d}-{m}-{y}"
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, selected)
            win.destroy()

        ttk.Button(win, text="✓ Confirm Date", style="Primary.TButton", command=set_date).pack(pady=10)

    def show_holidays(self):
        self.clear_content()

        hdr = ttk.Frame(self.content_frame)
        hdr.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(hdr, text="📅 Holiday & Activity Management", font=FONTS["h1"]).pack(side=tk.LEFT)

        notebook = ttk.Notebook(self.content_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # TAB 1: School Holidays
        tab_holidays = ttk.Frame(notebook, padding=10)
        notebook.add(tab_holidays, text="📅 School Holidays")

        action_frame = ttk.Frame(tab_holidays)
        action_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(action_frame, text="➕ Add Holiday", style="Primary.TButton", command=self.add_holiday_dialog).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="✏️ Edit Holiday", command=self.edit_selected_holiday).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="🗑️ Delete Holiday", style="Danger.TButton", command=self.delete_selected_holiday).pack(side=tk.LEFT, padx=3)

        ttk.Label(action_frame, text="🔍 Search:", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(15, 2))
        self.entry_holiday_search = ttk.Entry(action_frame, width=25)
        self.entry_holiday_search.pack(side=tk.LEFT, padx=3)
        self.entry_holiday_search.bind("<KeyRelease>", lambda e: self.load_holidays_table())

        tbl_frame = ttk.Frame(tab_holidays)
        tbl_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "title", "date", "description")
        self.tree_holidays = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=12)

        self.tree_holidays.heading("id", text="ID")
        self.tree_holidays.heading("title", text="Holiday Name")
        self.tree_holidays.heading("date", text="Holiday Date")
        self.tree_holidays.heading("description", text="Description")

        self.tree_holidays.column("id", width=0, stretch=tk.NO)
        self.tree_holidays.column("title", width=220, anchor="w")
        self.tree_holidays.column("date", width=140, anchor="center")
        self.tree_holidays.column("description", width=420, anchor="w")

        sb = ttk.Scrollbar(tbl_frame, orient="vertical", command=self.tree_holidays.yview)
        self.tree_holidays.configure(yscroll=sb.set)
        self.tree_holidays.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.load_holidays_table()

        # TAB 2: School Activities
        tab_activities = ttk.Frame(notebook, padding=10)
        notebook.add(tab_activities, text="🎈 School Activities")

        act_action_frame = ttk.Frame(tab_activities)
        act_action_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(act_action_frame, text="➕ Add Activity", style="Primary.TButton", command=self.add_activity_dialog).pack(side=tk.LEFT, padx=3)
        ttk.Button(act_action_frame, text="✏️ Edit Activity", command=self.edit_selected_activity).pack(side=tk.LEFT, padx=3)
        ttk.Button(act_action_frame, text="🗑️ Delete Activity", style="Danger.TButton", command=self.delete_selected_activity).pack(side=tk.LEFT, padx=3)

        ttk.Label(act_action_frame, text="🔍 Search:", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(15, 2))
        self.entry_activity_search = ttk.Entry(act_action_frame, width=25)
        self.entry_activity_search.pack(side=tk.LEFT, padx=3)
        self.entry_activity_search.bind("<KeyRelease>", lambda e: self.load_activities_table())

        act_tbl_frame = ttk.Frame(tab_activities)
        act_tbl_frame.pack(fill=tk.BOTH, expand=True)

        act_cols = ("id", "title", "date", "description")
        self.tree_activities = ttk.Treeview(act_tbl_frame, columns=act_cols, show="headings", height=12)

        self.tree_activities.heading("id", text="ID")
        self.tree_activities.heading("title", text="Activity Name")
        self.tree_activities.heading("date", text="Activity Date")
        self.tree_activities.heading("description", text="Description")

        self.tree_activities.column("id", width=0, stretch=tk.NO)
        self.tree_activities.column("title", width=220, anchor="w")
        self.tree_activities.column("date", width=140, anchor="center")
        self.tree_activities.column("description", width=420, anchor="w")

        act_sb = ttk.Scrollbar(act_tbl_frame, orient="vertical", command=self.tree_activities.yview)
        self.tree_activities.configure(yscroll=act_sb.set)
        self.tree_activities.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        act_sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.load_activities_table()

    def load_holidays_table(self):
        for row in self.tree_holidays.get_children():
            self.tree_holidays.delete(row)

        q = self.entry_holiday_search.get().strip().lower() if hasattr(self, 'entry_holiday_search') else ""
        holidays = self.db.get_all_holidays()

        for h in holidays:
            if q and q not in h['title'].lower() and q not in h['date'].lower() and q not in h.get('description', '').lower():
                continue
            self.tree_holidays.insert("", tk.END, values=(
                h['id'], h['title'], h['date'], h.get('description', '')
            ))

    def load_activities_table(self):
        for row in self.tree_activities.get_children():
            self.tree_activities.delete(row)

        q = self.entry_activity_search.get().strip().lower() if hasattr(self, 'entry_activity_search') else ""
        activities = self.db.get_all_activities()

        for a in activities:
            if q and q not in a['title'].lower() and q not in a['date'].lower() and q not in a.get('description', '').lower():
                continue
            self.tree_activities.insert("", tk.END, values=(
                a['id'], a['title'], a['date'], a.get('description', '')
            ))

    def add_holiday_dialog(self):
        win = tk.Toplevel(self)
        win.title("➕ Add Holiday")
        win.geometry("520x460")
        win.grab_set()

        ttk.Label(win, text="Add Holiday", font=FONTS["h2"]).pack(pady=10)

        f = ttk.Frame(win, padding=15)
        f.pack(fill=tk.BOTH, expand=True)

        # Field 1: Holiday Name
        ttk.Label(f, text="Holiday Name *:").grid(row=0, column=0, sticky="w", pady=8)
        entry_title = ttk.Entry(f, width=32)
        entry_title.grid(row=0, column=1, columnspan=2, sticky="w", pady=8)

        # Field 2: Holiday Date
        ttk.Label(f, text="Holiday Date *:").grid(row=1, column=0, sticky="w", pady=8)
        entry_date = ttk.Entry(f, width=22)
        entry_date.insert(0, get_current_date())
        entry_date.grid(row=1, column=1, sticky="w", pady=8)

        btn_picker = ttk.Button(f, text="📅 Pick Date", command=lambda: self._open_date_picker(entry_date))
        btn_picker.grid(row=1, column=2, sticky="w", padx=(5, 0), pady=8)

        # Field 3: Description (Multi-line text area)
        ttk.Label(f, text="Description *:").grid(row=2, column=0, sticky="nw", pady=8)
        txt_desc = tk.Text(f, width=32, height=6, font=("Segoe UI", 9))
        txt_desc.grid(row=2, column=1, columnspan=2, sticky="w", pady=8)

        def save():
            title = entry_title.get().strip()
            dt = entry_date.get().strip()
            desc = txt_desc.get("1.0", tk.END).strip()

            if not title:
                messagebox.showerror("Validation Error", "Please enter Holiday Name.")
                entry_title.focus()
                return

            if not dt:
                messagebox.showerror("Validation Error", "Please enter Holiday Date.")
                entry_date.focus()
                return

            if not desc:
                messagebox.showerror("Validation Error", "Please enter Description.")
                txt_desc.focus()
                return

            # Check duplicate for same title and date
            existing = self.db.get_all_holidays()
            for ex in existing:
                if ex['title'].lower() == title.lower() and ex['date'] == dt:
                    messagebox.showwarning("Duplicate Holiday", f"A holiday named '{title}' on {dt} already exists.")
                    return

            ok = self.db.add_holiday(title, dt, desc)
            if ok:
                messagebox.showinfo("Success", "Holiday added successfully.")
                win.destroy()
                self.load_holidays_table()

        ttk.Button(win, text="Save Holiday", style="Accent.TButton", command=save).pack(pady=12)

    def edit_selected_holiday(self):
        sel = self.tree_holidays.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a holiday to edit.")
            return

        item = self.tree_holidays.item(sel[0])['values']
        hid, htitle, hdate, hdesc = item[0], item[1], item[2], item[3]

        win = tk.Toplevel(self)
        win.title(f"✏️ Edit Holiday - {htitle}")
        win.geometry("520x460")
        win.grab_set()

        ttk.Label(win, text="Edit Holiday", font=FONTS["h2"]).pack(pady=10)

        f = ttk.Frame(win, padding=15)
        f.pack(fill=tk.BOTH, expand=True)

        # Field 1: Holiday Name
        ttk.Label(f, text="Holiday Name *:").grid(row=0, column=0, sticky="w", pady=8)
        entry_title = ttk.Entry(f, width=32)
        entry_title.insert(0, htitle)
        entry_title.grid(row=0, column=1, columnspan=2, sticky="w", pady=8)

        # Field 2: Holiday Date
        ttk.Label(f, text="Holiday Date *:").grid(row=1, column=0, sticky="w", pady=8)
        entry_date = ttk.Entry(f, width=22)
        entry_date.insert(0, hdate)
        entry_date.grid(row=1, column=1, sticky="w", pady=8)

        btn_picker = ttk.Button(f, text="📅 Pick Date", command=lambda: self._open_date_picker(entry_date))
        btn_picker.grid(row=1, column=2, sticky="w", padx=(5, 0), pady=8)

        # Field 3: Description (Multi-line text area)
        ttk.Label(f, text="Description *:").grid(row=2, column=0, sticky="nw", pady=8)
        txt_desc = tk.Text(f, width=32, height=6, font=("Segoe UI", 9))
        txt_desc.insert("1.0", hdesc)
        txt_desc.grid(row=2, column=1, columnspan=2, sticky="w", pady=8)

        def save():
            title = entry_title.get().strip()
            dt = entry_date.get().strip()
            desc = txt_desc.get("1.0", tk.END).strip()

            if not title:
                messagebox.showerror("Validation Error", "Holiday Name cannot be empty.")
                entry_title.focus()
                return

            if not dt:
                messagebox.showerror("Validation Error", "Holiday Date cannot be empty.")
                entry_date.focus()
                return

            if not desc:
                messagebox.showerror("Validation Error", "Description cannot be empty.")
                txt_desc.focus()
                return

            ok = self.db.update_holiday(int(hid), title, dt, desc)
            if ok:
                messagebox.showinfo("Success", f"✓ Holiday '{title}' updated successfully!")
                win.destroy()
                self.load_holidays_table()

        ttk.Button(win, text="Update Holiday", style="Accent.TButton", command=save).pack(pady=12)

    def delete_selected_holiday(self):
        sel = self.tree_holidays.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a holiday to delete.")
            return

        item = self.tree_holidays.item(sel[0])['values']
        hid, htitle = item[0], item[1]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete Holiday '{htitle}'?"):
            self.db.delete_holiday(int(hid))
            messagebox.showinfo("Deleted", f"Holiday '{htitle}' deleted.")
            self.load_holidays_table()

    def add_activity_dialog(self):
        win = tk.Toplevel(self)
        win.title("➕ Add Activity")
        win.geometry("520x460")
        win.grab_set()

        ttk.Label(win, text="Add Activity", font=FONTS["h2"]).pack(pady=10)

        f = ttk.Frame(win, padding=15)
        f.pack(fill=tk.BOTH, expand=True)

        # Field 1: Activity Name
        ttk.Label(f, text="Activity Name *:").grid(row=0, column=0, sticky="w", pady=8)
        entry_title = ttk.Entry(f, width=32)
        entry_title.grid(row=0, column=1, columnspan=2, sticky="w", pady=8)

        # Field 2: Activity Date
        ttk.Label(f, text="Activity Date *:").grid(row=1, column=0, sticky="w", pady=8)
        entry_date = ttk.Entry(f, width=22)
        entry_date.insert(0, get_current_date())
        entry_date.grid(row=1, column=1, sticky="w", pady=8)

        btn_picker = ttk.Button(f, text="📅 Pick Date", command=lambda: self._open_date_picker(entry_date))
        btn_picker.grid(row=1, column=2, sticky="w", padx=(5, 0), pady=8)

        # Field 3: Description (Multi-line text area)
        ttk.Label(f, text="Description *:").grid(row=2, column=0, sticky="nw", pady=8)
        txt_desc = tk.Text(f, width=32, height=6, font=("Segoe UI", 9))
        txt_desc.grid(row=2, column=1, columnspan=2, sticky="w", pady=8)

        def save():
            title = entry_title.get().strip()
            dt = entry_date.get().strip()
            desc = txt_desc.get("1.0", tk.END).strip()

            if not title:
                messagebox.showerror("Validation Error", "Please enter Activity Name.")
                entry_title.focus()
                return

            if not dt:
                messagebox.showerror("Validation Error", "Please enter Activity Date.")
                entry_date.focus()
                return

            if not desc:
                messagebox.showerror("Validation Error", "Please enter Description.")
                txt_desc.focus()
                return

            ok = self.db.add_activity(title, dt, desc)
            if ok:
                messagebox.showinfo("Success", "Activity added successfully.")
                win.destroy()
                self.load_activities_table()

        ttk.Button(win, text="Save Activity", style="Accent.TButton", command=save).pack(pady=12)

    def edit_selected_activity(self):
        sel = self.tree_activities.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select an activity to edit.")
            return

        item = self.tree_activities.item(sel[0])['values']
        aid, atitle, adate, adesc = item[0], item[1], item[2], item[3]

        win = tk.Toplevel(self)
        win.title(f"✏️ Edit Activity - {atitle}")
        win.geometry("520x460")
        win.grab_set()

        ttk.Label(win, text="Edit Activity", font=FONTS["h2"]).pack(pady=10)

        f = ttk.Frame(win, padding=15)
        f.pack(fill=tk.BOTH, expand=True)

        # Field 1: Activity Name
        ttk.Label(f, text="Activity Name *:").grid(row=0, column=0, sticky="w", pady=8)
        entry_title = ttk.Entry(f, width=32)
        entry_title.insert(0, atitle)
        entry_title.grid(row=0, column=1, columnspan=2, sticky="w", pady=8)

        # Field 2: Activity Date
        ttk.Label(f, text="Activity Date *:").grid(row=1, column=0, sticky="w", pady=8)
        entry_date = ttk.Entry(f, width=22)
        entry_date.insert(0, adate)
        entry_date.grid(row=1, column=1, sticky="w", pady=8)

        btn_picker = ttk.Button(f, text="📅 Pick Date", command=lambda: self._open_date_picker(entry_date))
        btn_picker.grid(row=1, column=2, sticky="w", padx=(5, 0), pady=8)

        # Field 3: Description (Multi-line text area)
        ttk.Label(f, text="Description *:").grid(row=2, column=0, sticky="nw", pady=8)
        txt_desc = tk.Text(f, width=32, height=6, font=("Segoe UI", 9))
        txt_desc.insert("1.0", adesc)
        txt_desc.grid(row=2, column=1, columnspan=2, sticky="w", pady=8)

        def save():
            title = entry_title.get().strip()
            dt = entry_date.get().strip()
            desc = txt_desc.get("1.0", tk.END).strip()

            if not title:
                messagebox.showerror("Validation Error", "Activity Name cannot be empty.")
                entry_title.focus()
                return

            if not dt:
                messagebox.showerror("Validation Error", "Activity Date cannot be empty.")
                entry_date.focus()
                return

            if not desc:
                messagebox.showerror("Validation Error", "Description cannot be empty.")
                txt_desc.focus()
                return

            ok = self.db.update_activity(int(aid), title, dt, desc)
            if ok:
                messagebox.showinfo("Success", f"✓ Activity '{title}' updated successfully!")
                win.destroy()
                self.load_activities_table()

        ttk.Button(win, text="Update Activity", style="Accent.TButton", command=save).pack(pady=12)

    def delete_selected_activity(self):
        sel = self.tree_activities.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select an activity to delete.")
            return

        item = self.tree_activities.item(sel[0])['values']
        aid, atitle = item[0], item[1]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete Activity '{atitle}'?"):
            self.db.delete_activity(int(aid))
            messagebox.showinfo("Deleted", f"Activity '{atitle}' deleted.")
            self.load_activities_table()

    def on_logout(self):
        if messagebox.askyesno("Confirm Logout", "Are you sure you want to log out of your session?"):
            self.destroy()
            self.welcome_win.deiconify()

