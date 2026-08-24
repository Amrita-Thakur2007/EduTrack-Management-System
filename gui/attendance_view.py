import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DBManager
from gui.theme import COLORS, FONTS
from utils.helpers import get_current_date, get_current_time

class AttendanceViewFrame(ttk.Frame):
    """Frame for viewing & monitoring Attendance Records for Students and Teachers."""
    def __init__(self, parent, db_manager: DBManager, student_id: str = None, is_admin_or_teacher: bool = True):
        super().__init__(parent, padding=15)
        self.db = db_manager
        self.student_id = student_id
        self.is_admin_or_teacher = is_admin_or_teacher

        self._build_ui()
        self.refresh_table()

    def _build_ui(self):
        # Header / Filters Bar
        hdr_frame = ttk.Frame(self)
        hdr_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(hdr_frame, text="📅 Attendance Monitoring & Face Verification", font=FONTS["h2"]).pack(side=tk.LEFT)

        if not self.student_id:
            m_frame = ttk.Frame(hdr_frame)
            m_frame.pack(side=tk.LEFT, padx=(20, 0))
            ttk.Label(m_frame, text="Mode:", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(0, 4))
            self.combo_category = ttk.Combobox(m_frame, values=["School", "College"], state="readonly", width=10)
            self.combo_category.set("School")
            self.combo_category.pack(side=tk.LEFT)
            self.combo_category.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())

        if self.is_admin_or_teacher and not self.student_id:
            btn_t_scan = ttk.Button(hdr_frame, text="📸 Teacher Face Scan", style="Primary.TButton", command=self.open_teacher_scanner)
            btn_t_scan.pack(side=tk.RIGHT, padx=4)

            btn_s_scan = ttk.Button(hdr_frame, text="📸 Student Face Scan", style="Accent.TButton", command=self.open_student_scanner)
            btn_s_scan.pack(side=tk.RIGHT, padx=4)

        if self.student_id:
            # Single Student View
            student = self.db.get_student(self.student_id)
            is_college = student and student.get('education_type') == 'College'

            tbl_frame = ttk.Frame(self)
            tbl_frame.pack(fill=tk.BOTH, expand=True)

            if is_college:
                cols = ("date", "student_id", "student_name", "course", "status")
                self.tree_single = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=15)
                self.tree_single.heading("date", text="Date")
                self.tree_single.heading("student_id", text="Student ID / Enrollment No")
                self.tree_single.heading("student_name", text="Student Name")
                self.tree_single.heading("course", text="Course")
                self.tree_single.heading("status", text="Status")

                self.tree_single.column("date", width=120, anchor="center")
                self.tree_single.column("student_id", width=150, anchor="center")
                self.tree_single.column("student_name", width=180, anchor="w")
                self.tree_single.column("course", width=150, anchor="w")
                self.tree_single.column("status", width=110, anchor="center")
            else:
                cols = ("date", "student_id", "student_name", "class", "section", "status")
                self.tree_single = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=15)
                self.tree_single.heading("date", text="Date")
                self.tree_single.heading("student_id", text="Student ID")
                self.tree_single.heading("student_name", text="Student Name")
                self.tree_single.heading("class", text="Class")
                self.tree_single.heading("section", text="Section")
                self.tree_single.heading("status", text="Status")

                self.tree_single.column("date", width=120, anchor="center")
                self.tree_single.column("student_id", width=120, anchor="center")
                self.tree_single.column("student_name", width=180, anchor="w")
                self.tree_single.column("class", width=100, anchor="center")
                self.tree_single.column("section", width=100, anchor="center")
                self.tree_single.column("status", width=110, anchor="center")

            sb = ttk.Scrollbar(tbl_frame, orient="vertical", command=self.tree_single.yview)
            self.tree_single.configure(yscroll=sb.set)
            self.tree_single.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            sb.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            # Tabbed Admin/Teacher/Parent Monitoring View (Students & Teachers)
            self.notebook = ttk.Notebook(self)
            self.notebook.pack(fill=tk.BOTH, expand=True)

            # TAB 1: Student Attendance Tab
            self.tab_students = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(self.tab_students, text=" 👨‍🎓 Student Attendance ")

            # Student Stat Cards
            stu_cards_frame = ttk.Frame(self.tab_students)
            stu_cards_frame.pack(fill=tk.X, pady=(0, 8))

            self.lbl_stu_present = ttk.Label(stu_cards_frame, text="Present Students: 0", font=FONTS["body_bold"], foreground=COLORS["success"])
            self.lbl_stu_present.pack(side=tk.LEFT, padx=15)

            self.lbl_stu_absent = ttk.Label(stu_cards_frame, text="Absent Students: 0", font=FONTS["body_bold"], foreground=COLORS["danger"])
            self.lbl_stu_absent.pack(side=tk.LEFT, padx=15)

            # Student Tree Container Frame
            self.s_tbl_frame = ttk.Frame(self.tab_students)
            self.s_tbl_frame.pack(fill=tk.BOTH, expand=True)
            self.tree_stu = None
            self._setup_student_tree()

            # TAB 2: Teacher Attendance Tab
            self.tab_teachers = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(self.tab_teachers, text=" 👨‍🏫 Teacher Attendance ")

            # Teacher Stat Cards
            t_cards_frame = ttk.Frame(self.tab_teachers)
            t_cards_frame.pack(fill=tk.X, pady=(0, 8))

            self.lbl_teach_present = ttk.Label(t_cards_frame, text="Present Teachers: 0", font=FONTS["body_bold"], foreground=COLORS["success"])
            self.lbl_teach_present.pack(side=tk.LEFT, padx=15)

            self.lbl_teach_absent = ttk.Label(t_cards_frame, text="Absent Teachers: 0", font=FONTS["body_bold"], foreground=COLORS["danger"])
            self.lbl_teach_absent.pack(side=tk.LEFT, padx=15)

            # Teacher Tree
            t_tbl_frame = ttk.Frame(self.tab_teachers)
            t_tbl_frame.pack(fill=tk.BOTH, expand=True)

            t_cols = ("date", "id", "name", "dept", "status")
            self.tree_teach = ttk.Treeview(t_tbl_frame, columns=t_cols, show="headings", height=12)
            self.tree_teach.heading("date", text="Date")
            self.tree_teach.heading("id", text="Teacher ID")
            self.tree_teach.heading("name", text="Teacher Name")
            self.tree_teach.heading("dept", text="Department")
            self.tree_teach.heading("status", text="Status")

            self.tree_teach.column("date", width=120, anchor="center")
            self.tree_teach.column("id", width=120, anchor="center")
            self.tree_teach.column("name", width=180, anchor="w")
            self.tree_teach.column("dept", width=150, anchor="w")
            self.tree_teach.column("status", width=100, anchor="center")

            sb_t = ttk.Scrollbar(t_tbl_frame, orient="vertical", command=self.tree_teach.yview)
            self.tree_teach.configure(yscroll=sb_t.set)
            self.tree_teach.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            sb_t.pack(side=tk.RIGHT, fill=tk.Y)

    def _setup_student_tree(self):
        """Builds student tree based on selected mode (School vs College) without Time column."""
        if hasattr(self, 's_tbl_frame') and self.s_tbl_frame:
            for widget in self.s_tbl_frame.winfo_children():
                widget.destroy()

        mode = self.combo_category.get() if hasattr(self, 'combo_category') else "School"

        if mode == "School":
            s_cols = ("date", "id", "name", "class", "section", "status")
            self.tree_stu = ttk.Treeview(self.s_tbl_frame, columns=s_cols, show="headings", height=12)
            self.tree_stu.heading("date", text="Date")
            self.tree_stu.heading("id", text="Student ID")
            self.tree_stu.heading("name", text="Student Name")
            self.tree_stu.heading("class", text="Class")
            self.tree_stu.heading("section", text="Section")
            self.tree_stu.heading("status", text="Status")

            self.tree_stu.column("date", width=110, anchor="center")
            self.tree_stu.column("id", width=120, anchor="center")
            self.tree_stu.column("name", width=180, anchor="w")
            self.tree_stu.column("class", width=100, anchor="center")
            self.tree_stu.column("section", width=100, anchor="center")
            self.tree_stu.column("status", width=100, anchor="center")
        else:
            s_cols = ("date", "id", "name", "course", "status")
            self.tree_stu = ttk.Treeview(self.s_tbl_frame, columns=s_cols, show="headings", height=12)
            self.tree_stu.heading("date", text="Date")
            self.tree_stu.heading("id", text="Student ID / Enrollment No")
            self.tree_stu.heading("name", text="Student Name")
            self.tree_stu.heading("course", text="Course")
            self.tree_stu.heading("status", text="Status")

            self.tree_stu.column("date", width=110, anchor="center")
            self.tree_stu.column("id", width=160, anchor="center")
            self.tree_stu.column("name", width=180, anchor="w")
            self.tree_stu.column("course", width=160, anchor="w")
            self.tree_stu.column("status", width=100, anchor="center")

        sb_s = ttk.Scrollbar(self.s_tbl_frame, orient="vertical", command=self.tree_stu.yview)
        self.tree_stu.configure(yscroll=sb_s.set)
        self.tree_stu.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_s.pack(side=tk.RIGHT, fill=tk.Y)

    def refresh_table(self):
        if self.student_id:
            for item in self.tree_single.get_children():
                self.tree_single.delete(item)
            logs = self.db.get_student_attendance(self.student_id)
            student = self.db.get_student(self.student_id)
            sname = student['name'] if student else self.student_id
            is_college = student and student.get('education_type') == 'College'
            
            for l in logs:
                if is_college:
                    enr_no = student.get('enrollment_number') or self.student_id
                    scourse = student.get('course') or student.get('current_class') or "N/A"
                    self.tree_single.insert("", tk.END, values=(l['date'], enr_no, sname, scourse, l['status']))
                else:
                    sclass = student.get('current_class') or "N/A"
                    ssec = student.get('section') or "N/A"
                    self.tree_single.insert("", tk.END, values=(l['date'], self.student_id, sname, sclass, ssec, l['status']))
        else:
            self._setup_student_tree()

            for item in self.tree_stu.get_children():
                self.tree_stu.delete(item)
            for item in self.tree_teach.get_children():
                self.tree_teach.delete(item)

            today = get_current_date()
            summary = self.db.get_attendance_dashboard_summary(today)

            self.lbl_stu_present.config(text=f"Present Students ({today}): {summary['students_present_count']}")
            self.lbl_stu_absent.config(text=f"Absent Students ({today}): {summary['students_absent_count']}")
            self.lbl_teach_present.config(text=f"Present Teachers ({today}): {summary['teachers_present_count']}")
            self.lbl_teach_absent.config(text=f"Absent Teachers ({today}): {summary['teachers_absent_count']}")

            mode = self.combo_category.get() if hasattr(self, 'combo_category') else "School"

            # Populate Students: Present first, then Absent
            for row in summary['students_present']:
                stu = self.db.get_student(row['student_id']) or {}
                if mode == "School":
                    sclass = stu.get('current_class') or row.get('course') or "N/A"
                    ssec = stu.get('section') or "N/A"
                    self.tree_stu.insert("", tk.END, values=(row['date'], row['student_id'], row['name'], sclass, ssec, "Present"))
                else:
                    enr_no = stu.get('enrollment_number') or row['student_id']
                    scourse = stu.get('course') or row.get('course') or "N/A"
                    self.tree_stu.insert("", tk.END, values=(row['date'], enr_no, row['name'], scourse, "Present"))

            for row in summary['students_absent']:
                stu = self.db.get_student(row['student_id']) or {}
                if mode == "School":
                    sclass = stu.get('current_class') or row.get('course') or "N/A"
                    ssec = stu.get('section') or "N/A"
                    self.tree_stu.insert("", tk.END, values=(row['date'], row['student_id'], row['name'], sclass, ssec, "Absent"))
                else:
                    enr_no = stu.get('enrollment_number') or row['student_id']
                    scourse = stu.get('course') or row.get('course') or "N/A"
                    self.tree_stu.insert("", tk.END, values=(row['date'], enr_no, row['name'], scourse, "Absent"))

            # Populate Teachers: Present first, then Absent
            for row in summary['teachers_present']:
                self.tree_teach.insert("", tk.END, values=(row['date'], row['teacher_id'], row['name'], row['department'], "Present"))
            for row in summary['teachers_absent']:
                self.tree_teach.insert("", tk.END, values=(row['date'], row['teacher_id'], row['name'], row['department'], "Absent"))

    def open_student_scanner(self):
        from face_attendance.face_recognition import FaceAttendanceScannerWindow
        FaceAttendanceScannerWindow(self.winfo_toplevel(), self.db, target_role="Student", on_attendance_marked=self.refresh_table)

    def open_teacher_scanner(self):
        from face_attendance.face_recognition import FaceAttendanceScannerWindow
        FaceAttendanceScannerWindow(self.winfo_toplevel(), self.db, target_role="Teacher", on_attendance_marked=self.refresh_table)

    def open_manual_mark(self):
        all_students = self.db.get_all_students()
        if not all_students:
            messagebox.showinfo("Notice", "No students registered in database.")
            return

        dlg = tk.Toplevel(self)
        dlg.title("Mark Manual Attendance")
        dlg.geometry("400x300")
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()

        ttk.Label(dlg, text="Select Student:", font=FONTS["body_bold"]).pack(pady=(15, 2))
        s_list = [f"{s['student_id']} - {s['name']}" for s in all_students]
        combo = ttk.Combobox(dlg, values=s_list, state="readonly", width=32)
        combo.pack(pady=(0, 10))
        if s_list:
            combo.current(0)

        ttk.Label(dlg, text="Attendance Status:", font=FONTS["body_bold"]).pack(pady=(5, 2))
        combo_status = ttk.Combobox(dlg, values=["Present", "Absent"], state="readonly", width=32)
        combo_status.set("Present")
        combo_status.pack(pady=(0, 15))

        def save_manual():
            sel = combo.get()
            if not sel:
                return
            sid = sel.split(" - ")[0]
            st = combo_status.get()
            today = get_current_date()
            now_t = get_current_time()

            ok, msg = self.db.mark_attendance(sid, today, now_t, st)
            if ok:
                messagebox.showinfo("Success", f"Attendance marked '{st}' for {sid}.")
                self.refresh_table()
                dlg.destroy()
            else:
                messagebox.showwarning("Notice", msg)

        ttk.Button(dlg, text="Save Attendance", style="Primary.TButton", command=save_manual).pack(pady=10)
