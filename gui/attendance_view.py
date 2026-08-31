import calendar
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database.db_manager import DBManager
from gui.theme import COLORS, FONTS
from utils.helpers import get_current_date, get_current_time

MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

def parse_month_input(month_str: str) -> int:
    """Helper to parse a manually typed month string or integer to 1-12."""
    if not month_str:
        return datetime.now().month
    m_clean = month_str.strip()
    if m_clean.isdigit():
        val = int(m_clean)
        if 1 <= val <= 12:
            return val
    for idx, name in enumerate(MONTH_NAMES, 1):
        if name.lower().startswith(m_clean.lower()) and len(m_clean) >= 3:
            return idx
    return datetime.now().month

class IndividualStudentAttendanceDialog(tk.Toplevel):
    """Dialog for viewing complete monthly and yearly date-wise attendance for a single student."""
    def __init__(self, parent, db_manager: DBManager, student_id: str):
        super().__init__(parent)
        self.db = db_manager
        self.student_id = student_id
        self.student = self.db.get_student(self.student_id) or {}
        
        sname = self.student.get('name', self.student_id)
        self.title(f"Individual Student Attendance — {sname} ({self.student_id})")
        self.geometry("820x620")
        self.minsize(700, 520)
        self.transient(parent.winfo_toplevel() if hasattr(parent, 'winfo_toplevel') else parent)
        
        self._build_ui()
        self.load_attendance()

    def _build_ui(self):
        # Header Info Card
        hdr_frame = ttk.LabelFrame(self, text=" Student Details ", padding=10)
        hdr_frame.pack(fill=tk.X, padx=15, pady=(10, 8))

        sname = self.student.get('name', 'N/A')
        sid = self.student.get('student_id', self.student_id)
        edu_type = self.student.get('education_type', 'School')
        adm_date = self.student.get('admission_date') or 'N/A'
        
        row1 = ttk.Frame(hdr_frame)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="Name: ", font=FONTS["body_bold"]).pack(side=tk.LEFT)
        ttk.Label(row1, text=sname, font=FONTS["body"]).pack(side=tk.LEFT, padx=(0, 18))
        
        ttk.Label(row1, text="Student ID: ", font=FONTS["body_bold"]).pack(side=tk.LEFT)
        ttk.Label(row1, text=sid, font=FONTS["body"]).pack(side=tk.LEFT, padx=(0, 18))

        ttk.Label(row1, text="Category: ", font=FONTS["body_bold"]).pack(side=tk.LEFT)
        ttk.Label(row1, text=edu_type, font=FONTS["body"], foreground=COLORS["primary"]).pack(side=tk.LEFT, padx=(0, 18))

        ttk.Label(row1, text="Admission Date: ", font=FONTS["body_bold"]).pack(side=tk.LEFT)
        ttk.Label(row1, text=adm_date, font=FONTS["body"], foreground="#0284c7").pack(side=tk.LEFT)

        row2 = ttk.Frame(hdr_frame)
        row2.pack(fill=tk.X, pady=2)
        if edu_type == "College":
            enr = self.student.get('enrollment_number') or sid
            course = self.student.get('course') or 'N/A'
            col_name = self.student.get('college_name') or 'N/A'
            sem = self.student.get('semester') or 'N/A'
            ttk.Label(row2, text="Enrollment No: ", font=FONTS["body_bold"]).pack(side=tk.LEFT)
            ttk.Label(row2, text=enr, font=FONTS["body"]).pack(side=tk.LEFT, padx=(0, 18))
            ttk.Label(row2, text="College: ", font=FONTS["body_bold"]).pack(side=tk.LEFT)
            ttk.Label(row2, text=col_name, font=FONTS["body"]).pack(side=tk.LEFT, padx=(0, 18))
            ttk.Label(row2, text="Course: ", font=FONTS["body_bold"]).pack(side=tk.LEFT)
            ttk.Label(row2, text=course, font=FONTS["body"]).pack(side=tk.LEFT, padx=(0, 18))
            ttk.Label(row2, text="Semester: ", font=FONTS["body_bold"]).pack(side=tk.LEFT)
            ttk.Label(row2, text=sem, font=FONTS["body"]).pack(side=tk.LEFT)
        else:
            sch_name = self.student.get('school_name') or 'N/A'
            cls_name = self.student.get('current_class') or 'N/A'
            sec_name = self.student.get('section') or 'N/A'
            ttk.Label(row2, text="School: ", font=FONTS["body_bold"]).pack(side=tk.LEFT)
            ttk.Label(row2, text=sch_name, font=FONTS["body"]).pack(side=tk.LEFT, padx=(0, 18))
            ttk.Label(row2, text="Class: ", font=FONTS["body_bold"]).pack(side=tk.LEFT)
            ttk.Label(row2, text=cls_name, font=FONTS["body"]).pack(side=tk.LEFT, padx=(0, 18))
            ttk.Label(row2, text="Section: ", font=FONTS["body_bold"]).pack(side=tk.LEFT)
            ttk.Label(row2, text=sec_name, font=FONTS["body"]).pack(side=tk.LEFT)

        # Filter Card: Month Selection & Year Selection
        flt_frame = ttk.LabelFrame(self, text=" Month & Year Selection ", padding=10)
        flt_frame.pack(fill=tk.X, padx=15, pady=(0, 8))

        row_f = ttk.Frame(flt_frame)
        row_f.pack(fill=tk.X)

        ttk.Label(row_f, text="Month: ", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(0, 4))
        self.entry_month = ttk.Combobox(row_f, values=MONTH_NAMES, width=13)
        current_m_name = MONTH_NAMES[datetime.now().month - 1]
        self.entry_month.set(current_m_name)
        self.entry_month.pack(side=tk.LEFT, padx=(0, 15))
        self.entry_month.bind("<<ComboboxSelected>>", lambda e: self.load_attendance())
        self.entry_month.bind("<Return>", lambda e: self.load_attendance())
        self.entry_month.bind("<KeyRelease>", lambda e: self.load_attendance())

        ttk.Label(row_f, text="Year: ", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(0, 4))
        self.entry_year = ttk.Entry(row_f, width=8)
        self.entry_year.insert(0, str(datetime.now().year))
        self.entry_year.pack(side=tk.LEFT, padx=(0, 15))
        self.entry_year.bind("<Return>", lambda e: self.load_attendance())
        self.entry_year.bind("<KeyRelease>", lambda e: self.load_attendance())

        ttk.Label(row_f, text="🔍 Search:", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(0, 4))
        self.entry_search = ttk.Entry(row_f, width=14)
        self.entry_search.pack(side=tk.LEFT, padx=(0, 8))
        self.entry_search.bind("<Return>", lambda e: self.load_attendance())
        self.entry_search.bind("<KeyRelease>", lambda e: self.load_attendance())

        btn_search = ttk.Button(row_f, text="View Attendance", style="Primary.TButton", command=self.load_attendance)
        btn_search.pack(side=tk.LEFT, padx=(0, 10))

        # Summary Labels
        self.lbl_monthly = ttk.Label(flt_frame, text="Monthly Summary: ...", font=FONTS["body_bold"], foreground="#0284c7")
        self.lbl_monthly.pack(anchor=tk.W, pady=(6, 2))

        self.lbl_yearly = ttk.Label(flt_frame, text="Yearly Summary: ...", font=FONTS["body_bold"], foreground="#7c3aed")
        self.lbl_yearly.pack(anchor=tk.W, pady=(2, 2))

        # Attendance Table
        tbl_frame = ttk.Frame(self)
        tbl_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        cols = ("date", "status", "marked_by", "student_id", "name", "info")
        self.tree = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=13)
        self.tree.heading("date", text="Date")
        self.tree.heading("status", text="Attendance")
        self.tree.heading("marked_by", text="Marked By")
        self.tree.heading("student_id", text="Student ID")
        self.tree.heading("name", text="Student Name")
        self.tree.heading("info", text="Class / Course")

        self.tree.column("date", width=130, anchor="center")
        self.tree.column("status", width=120, anchor="center")
        self.tree.column("marked_by", width=140, anchor="center")
        self.tree.column("student_id", width=110, anchor="center")
        self.tree.column("name", width=160, anchor="w")
        self.tree.column("info", width=140, anchor="w")

        self.tree.tag_configure("highlight", background="#fef08a", font=("Segoe UI", 9, "bold"))
        self.tree.tag_configure("present_tag", foreground=COLORS.get("success", "#16a34a"), font=("Segoe UI", 9, "bold"))
        self.tree.tag_configure("absent_tag", foreground=COLORS.get("danger", "#dc2626"), font=("Segoe UI", 9, "bold"))
        self.tree.tag_configure("leave_tag", foreground="#d97706", font=("Segoe UI", 9, "bold"))
        self.tree.tag_configure("unmarked_tag", foreground="#64748b")

        sb = ttk.Scrollbar(tbl_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    def load_attendance(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        m_text = self.entry_month.get().strip() if hasattr(self, 'entry_month') else ""
        y_text = self.entry_year.get().strip() if hasattr(self, 'entry_year') else ""
        s_term = self.entry_search.get().strip().lower() if hasattr(self, 'entry_search') else ""

        m_idx = parse_month_input(m_text)
        y_val = int(y_text) if (y_text and y_text.isdigit()) else datetime.now().year
        m_name = MONTH_NAMES[m_idx - 1]

        # Refresh student details
        self.student = self.db.get_student(self.student_id) or {}
        sname = self.student.get('name', self.student_id)
        edu_type = self.student.get('education_type', 'School')
        sid_display = (self.student.get('enrollment_number') or self.student_id) if edu_type == "College" else self.student_id
        info_str = f"{self.student.get('course', '')}" if edu_type == "College" else f"{self.student.get('current_class', '')} - {self.student.get('section', '')}"

        # Determine total days in selected month
        _, num_days = calendar.monthrange(y_val, m_idx)

        # Admission Date Rule
        adm_date_raw = str(self.student.get('admission_date', '')).strip()
        start_day = 1
        is_before_admission = False

        if adm_date_raw:
            try:
                clean_adm = adm_date_raw.split(" ")[0].replace("/", "-")
                parts = [int(p) for p in clean_adm.split("-") if p.isdigit()]
                if len(parts) == 3:
                    if parts[0] > 1000: # YYYY-MM-DD
                        adm_y, adm_m, adm_d = parts[0], parts[1], parts[2]
                    else: # DD-MM-YYYY
                        adm_d, adm_m, adm_y = parts[0], parts[1], parts[2]
                    if adm_y < 100:
                        adm_y += 2000

                    if (y_val, m_idx) < (adm_y, adm_m):
                        is_before_admission = True
                        start_day = num_days + 1
                    elif (y_val, m_idx) == (adm_y, adm_m):
                        start_day = max(1, min(adm_d, num_days))
                    else:
                        start_day = 1
            except Exception:
                start_day = 1

        from utils.helpers import get_current_date
        today_iso = get_current_date()

        # Fetch student logs and build date map
        logs = self.db.get_student_attendance(self.student_id)
        att_by_date = {}
        for l in logs:
            dt = str(l.get('date', '')).strip()
            st = str(l.get('status', '')).strip()
            src = str(l.get('source', '')).strip()
            if dt:
                att_by_date[dt] = {'status': st, 'source': src}

        m_present = 0
        m_absent = 0
        m_leave = 0
        matched_count = 0

        # Iterate chronologically 1 -> 2 -> ... -> num_days
        for day in range(start_day, num_days + 1):
            iso_date = f"{y_val:04d}-{m_idx:02d}-{day:02d}"
            display_date = f"{day} {m_name}"
            rec = att_by_date.get(iso_date)

            if rec is not None:
                status = rec['status']
                src = rec.get('source') or ''
                marked_by = f"Marked By: {src}" if src else "-"
            else:
                if iso_date <= today_iso:
                    # Past or Today with no record -> Absent
                    status = "Absent"
                    marked_by = "-"
                else:
                    # Future date -> Not automatically Absent
                    status = "-"
                    marked_by = "-"

            if status == 'Present':
                m_present += 1
            elif status == 'Absent':
                m_absent += 1
            elif status == 'Leave':
                m_leave += 1

            row_vals = (display_date, status, marked_by, sid_display, sname, info_str)
            row_str = f"{display_date} {day} {m_name} {y_val} {iso_date} {status} {marked_by} {sid_display} {sname} {info_str}".lower()

            tags = []
            if s_term:
                if s_term in row_str:
                    tags.append("highlight")
                    matched_count += 1
                else:
                    continue
            else:
                matched_count += 1

            if status == 'Present':
                tags.append("present_tag")
            elif status == 'Absent':
                tags.append("absent_tag")
            elif status == 'Leave':
                tags.append("leave_tag")
            else:
                tags.append("unmarked_tag")

            self.tree.insert("", tk.END, values=row_vals, tags=tuple(tags))

        # Monthly summary
        m_total_marked = m_present + m_absent + m_leave
        active_days = max(0, (num_days - start_day + 1)) if not is_before_admission else 0
        m_pct = (m_present / m_total_marked * 100.0) if m_total_marked > 0 else 0.0

        if is_before_admission:
            self.lbl_monthly.config(text=f"📊 Monthly Summary ({m_name} {y_val}): Student was not enrolled in this month (Admission Date: {adm_date_raw})")
        else:
            self.lbl_monthly.config(text=f"📊 Monthly Summary ({m_name} {y_val}): Total Present: {m_present} | Total Absent: {m_absent} | Total Leave: {m_leave} | Recorded: {m_total_marked}/{active_days} Days | Score: {m_pct:.1f}%")

        # Yearly stats
        y_present = sum(1 for l in logs if str(l.get('date', '')).startswith(f"{y_val:04d}-") and l.get('status') == 'Present')
        y_absent = sum(1 for l in logs if str(l.get('date', '')).startswith(f"{y_val:04d}-") and l.get('status') == 'Absent')
        y_leave = sum(1 for l in logs if str(l.get('date', '')).startswith(f"{y_val:04d}-") and l.get('status') == 'Leave')
        y_total = y_present + y_absent + y_leave
        y_pct = (y_present / y_total * 100.0) if y_total > 0 else 0.0
        self.lbl_yearly.config(text=f"📅 Yearly Summary ({y_val}): Total Present: {y_present} | Total Absent: {y_absent} | Total Leave: {y_leave} | Total Recorded: {y_total} Days | Overall Score: {y_pct:.1f}%")

        if matched_count == 0:
            if is_before_admission:
                self.tree.insert("", tk.END, values=("Before Admission Date", "-", "-", sid_display, sname, f"Admitted on {adm_date_raw}"))
            elif s_term:
                self.tree.insert("", tk.END, values=("No record found", "-", "-", "-", "-", "-"))


class IndividualTeacherAttendanceDialog(tk.Toplevel):
    """Dialog for viewing complete monthly and yearly date-wise attendance for a single teacher."""
    def __init__(self, parent, db_manager: DBManager, teacher_id: str):
        super().__init__(parent)
        self.db = db_manager
        self.teacher_id = teacher_id
        self.teacher = self.db.get_teacher(self.teacher_id) or {}

        tname = self.teacher.get('name', self.teacher_id)
        self.title(f"Individual Teacher Attendance — {tname} ({self.teacher_id})")
        self.geometry("780x600")
        self.minsize(680, 500)
        self.transient(parent.winfo_toplevel() if hasattr(parent, 'winfo_toplevel') else parent)

        self._build_ui()
        self.load_attendance()

    def _build_ui(self):
        # Header Info Card
        hdr_frame = ttk.LabelFrame(self, text=" Teacher Details ", padding=10)
        hdr_frame.pack(fill=tk.X, padx=15, pady=(10, 8))

        tname = self.teacher.get('name', 'N/A')
        tid = self.teacher.get('teacher_id', self.teacher_id)
        dept = self.teacher.get('department', 'N/A')
        desig = self.teacher.get('designation', 'N/A')

        row1 = ttk.Frame(hdr_frame)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="Name: ", font=FONTS["body_bold"]).pack(side=tk.LEFT)
        ttk.Label(row1, text=tname, font=FONTS["body"]).pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(row1, text="Teacher ID: ", font=FONTS["body_bold"]).pack(side=tk.LEFT)
        ttk.Label(row1, text=tid, font=FONTS["body"]).pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(row1, text="Department: ", font=FONTS["body_bold"]).pack(side=tk.LEFT)
        ttk.Label(row1, text=dept, font=FONTS["body"]).pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(row1, text="Designation: ", font=FONTS["body_bold"]).pack(side=tk.LEFT)
        ttk.Label(row1, text=desig, font=FONTS["body"]).pack(side=tk.LEFT)

        # Filter Card: Month (TEXT INPUT) & Year (TEXT INPUT) - NO DROPDOWNS!
        flt_frame = ttk.LabelFrame(self, text=" Monthly & Yearly Filter (Text Input) ", padding=10)
        flt_frame.pack(fill=tk.X, padx=15, pady=(0, 8))

        row_f = ttk.Frame(flt_frame)
        row_f.pack(fill=tk.X)

        ttk.Label(row_f, text="Month: ", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(0, 2))
        self.entry_month = ttk.Entry(row_f, width=14)
        current_m_name = MONTH_NAMES[datetime.now().month - 1]
        self.entry_month.insert(0, current_m_name)
        self.entry_month.pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(row_f, text="Year: ", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(0, 2))
        self.entry_year = ttk.Entry(row_f, width=10)
        self.entry_year.insert(0, str(datetime.now().year))
        self.entry_year.pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(row_f, text="Search: ", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(0, 2))
        self.entry_search = ttk.Entry(row_f, width=14)
        self.entry_search.pack(side=tk.LEFT, padx=(0, 10))

        btn_search = ttk.Button(row_f, text="🔍 Search", style="Primary.TButton", command=self.load_attendance)
        btn_search.pack(side=tk.LEFT, padx=(0, 10))

        self.entry_month.bind("<Return>", lambda e: self.load_attendance())
        self.entry_year.bind("<Return>", lambda e: self.load_attendance())
        self.entry_search.bind("<Return>", lambda e: self.load_attendance())
        self.entry_search.bind("<KeyRelease>", lambda e: self.load_attendance())

        # Summary Labels
        self.lbl_monthly = ttk.Label(flt_frame, text="Monthly Summary: ...", font=FONTS["body_bold"], foreground="#0284c7")
        self.lbl_monthly.pack(anchor=tk.W, pady=(6, 2))

        self.lbl_yearly = ttk.Label(flt_frame, text="Yearly Summary: ...", font=FONTS["body_bold"], foreground="#7c3aed")
        self.lbl_yearly.pack(anchor=tk.W, pady=(2, 2))

        # Attendance Table
        tbl_frame = ttk.Frame(self)
        tbl_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        cols = ("date", "status", "teacher_id", "name", "dept")
        self.tree = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=12)
        self.tree.heading("date", text="Date")
        self.tree.heading("status", text="Status (Present / Absent)")
        self.tree.heading("teacher_id", text="Teacher ID")
        self.tree.heading("name", text="Teacher Name")
        self.tree.heading("dept", text="Department")

        self.tree.column("date", width=120, anchor="center")
        self.tree.column("status", width=160, anchor="center")
        self.tree.column("teacher_id", width=120, anchor="center")
        self.tree.column("name", width=180, anchor="w")
        self.tree.column("dept", width=150, anchor="w")

        self.tree.tag_configure("highlight", background="#fef08a", font=("Segoe UI", 9, "bold"))
        self.tree.tag_configure("present_tag", foreground=COLORS["success"])
        self.tree.tag_configure("absent_tag", foreground=COLORS["danger"])

        sb = ttk.Scrollbar(tbl_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    def load_attendance(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        m_text = self.entry_month.get().strip()
        y_text = self.entry_year.get().strip()
        s_term = self.entry_search.get().strip().lower() if hasattr(self, 'entry_search') else ""

        m_idx = parse_month_input(m_text)
        y_val = y_text if y_text.isdigit() else str(datetime.now().year)
        m_prefix = f"{y_val}-{m_idx:02d}-"
        y_prefix = f"{y_val}-"
        m_name = MONTH_NAMES[m_idx - 1]

        logs = self.db.get_teacher_attendance(self.teacher_id)
        tname = self.teacher.get('name', self.teacher_id)
        dept = self.teacher.get('department', 'N/A')

        m_present = 0
        m_absent = 0

        y_present = 0
        y_absent = 0

        matched_count = 0

        for l in logs:
            ldate = l['date']
            lstatus = l['status']

            if ldate.startswith(y_prefix):
                if lstatus == 'Present':
                    y_present += 1
                elif lstatus == 'Absent':
                    y_absent += 1

            if ldate.startswith(m_prefix):
                if lstatus == 'Present':
                    m_present += 1
                elif lstatus == 'Absent':
                    m_absent += 1

                row_vals = (ldate, lstatus, self.teacher_id, tname, dept)
                row_str = f"{ldate} {lstatus} {self.teacher_id} {tname} {dept}".lower()

                tags = []
                if s_term:
                    if s_term in row_str:
                        tags.append("highlight")
                        matched_count += 1
                    else:
                        continue
                else:
                    matched_count += 1

                if lstatus == 'Present':
                    tags.append("present_tag")
                elif lstatus == 'Absent':
                    tags.append("absent_tag")

                self.tree.insert("", tk.END, values=row_vals, tags=tuple(tags))

        m_total = m_present + m_absent
        m_pct = (m_present / m_total * 100.0) if m_total > 0 else 0.0
        self.lbl_monthly.config(text=f"📊 Monthly Summary ({m_name} {y_val}): Total Present: {m_present} | Total Absent: {m_absent} | Recorded Days: {m_total} | Score: {m_pct:.1f}%")

        y_total = y_present + y_absent
        y_pct = (y_present / y_total * 100.0) if y_total > 0 else 0.0
        self.lbl_yearly.config(text=f"📅 Yearly Summary ({y_val}): Total Present: {y_present} | Total Absent: {y_absent} | Recorded Days: {y_total} | Overall Score: {y_pct:.1f}%")

        if s_term and matched_count == 0:
            self.tree.insert("", tk.END, values=("No record found", "-", "-", "-", "-"))


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

        ttk.Label(hdr_frame, text="📅 Attendance Monitoring", font=FONTS["h2"]).pack(side=tk.LEFT)

        if not self.student_id:
            m_frame = ttk.Frame(hdr_frame)
            m_frame.pack(side=tk.LEFT, padx=(20, 0))
            ttk.Label(m_frame, text="Mode:", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(0, 4))
            self.combo_category = ttk.Combobox(m_frame, values=["School", "College"], state="readonly", width=10)
            self.combo_category.set("School")
            self.combo_category.pack(side=tk.LEFT)
            self.combo_category.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())

        if self.student_id:
            # Single Student View
            student = self.db.get_student(self.student_id)
            is_college = student and student.get('education_type') == 'College'

            # Year + Month + Search filter controls at top
            filter_frame = ttk.LabelFrame(self, text=" Filter & Search (Manual Text Input) ", padding=10)
            filter_frame.pack(fill=tk.X, pady=(0, 10))

            f_row = ttk.Frame(filter_frame)
            f_row.pack(fill=tk.X)

            # Select Year (Text Entry)
            ttk.Label(f_row, text="Year:", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(5, 2))
            self.entry_year = ttk.Entry(f_row, width=10)
            self.entry_year.insert(0, str(datetime.now().year))
            self.entry_year.pack(side=tk.LEFT, padx=(0, 15))

            # Select Month (Text Entry)
            ttk.Label(f_row, text="Month:", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(5, 2))
            self.entry_month = ttk.Entry(f_row, width=15)
            current_month_name = MONTH_NAMES[datetime.now().month - 1]
            self.entry_month.insert(0, current_month_name)
            self.entry_month.pack(side=tk.LEFT, padx=(0, 15))

            # Search Text Input
            ttk.Label(f_row, text="Search:", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(5, 2))
            self.entry_student_search = ttk.Entry(f_row, width=18)
            self.entry_student_search.pack(side=tk.LEFT, padx=(0, 10))

            # Search Button
            btn_apply = ttk.Button(f_row, text="🔍 Search", style="Primary.TButton", command=self.refresh_table)
            btn_apply.pack(side=tk.LEFT, padx=(5, 10))

            # View Individual Monthly Attendance Button
            btn_monthly_view = ttk.Button(f_row, text="📋 View Individual Monthly Attendance", style="Primary.TButton", command=self.open_individual_monthly_view)
            btn_monthly_view.pack(side=tk.LEFT, padx=(0, 5))

            self.entry_year.bind("<Return>", lambda e: self.refresh_table())
            self.entry_month.bind("<Return>", lambda e: self.refresh_table())
            self.entry_student_search.bind("<Return>", lambda e: self.refresh_table())
            self.entry_student_search.bind("<KeyRelease>", lambda e: self.refresh_table())

            # Monthly & Yearly summary labels
            self.lbl_monthly_summary = ttk.Label(filter_frame, text="Monthly Summary: ...", font=FONTS["body_bold"], foreground="#0284c7")
            self.lbl_monthly_summary.pack(anchor=tk.W, pady=(8, 2), padx=5)

            self.lbl_yearly_summary = ttk.Label(filter_frame, text="Yearly Summary: ...", font=FONTS["body_bold"], foreground="#7c3aed")
            self.lbl_yearly_summary.pack(anchor=tk.W, pady=2, padx=5)

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

            self.tree_single.tag_configure("highlight", background="#fef08a", font=("Segoe UI", 9, "bold"))

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

            # Student Action & Search Bar
            stu_bar = ttk.Frame(self.tab_students)
            stu_bar.pack(fill=tk.X, pady=(0, 6))

            ttk.Label(stu_bar, text="🔍 Search Student:", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(0, 4))
            self.entry_stu_tab_search = ttk.Entry(stu_bar, width=20)
            self.entry_stu_tab_search.pack(side=tk.LEFT, padx=(0, 6))
            btn_stu_search = ttk.Button(stu_bar, text="Search", command=self.refresh_table)
            btn_stu_search.pack(side=tk.LEFT, padx=(0, 15))

            self.entry_stu_tab_search.bind("<Return>", lambda e: self.refresh_table())
            self.entry_stu_tab_search.bind("<KeyRelease>", lambda e: self.refresh_table())

            btn_view_stu = ttk.Button(stu_bar, text="📋 View Individual Monthly Attendance", style="Primary.TButton", command=self.open_selected_student_attendance)
            btn_view_stu.pack(side=tk.LEFT, padx=5)

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

            # Teacher Action & Search Bar
            teach_bar = ttk.Frame(self.tab_teachers)
            teach_bar.pack(fill=tk.X, pady=(0, 6))

            ttk.Label(teach_bar, text="🔍 Search Teacher:", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(0, 4))
            self.entry_teach_tab_search = ttk.Entry(teach_bar, width=20)
            self.entry_teach_tab_search.pack(side=tk.LEFT, padx=(0, 6))
            btn_teach_search = ttk.Button(teach_bar, text="Search", command=self.refresh_table)
            btn_teach_search.pack(side=tk.LEFT, padx=(0, 15))

            self.entry_teach_tab_search.bind("<Return>", lambda e: self.refresh_table())
            self.entry_teach_tab_search.bind("<KeyRelease>", lambda e: self.refresh_table())

            btn_view_teach = ttk.Button(teach_bar, text="📋 View Individual Monthly Attendance", style="Primary.TButton", command=self.open_selected_teacher_attendance)
            btn_view_teach.pack(side=tk.LEFT, padx=5)

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

            self.tree_teach.tag_configure("highlight", background="#fef08a", font=("Segoe UI", 9, "bold"))
            self.tree_teach.bind("<Double-1>", lambda e: self.open_selected_teacher_attendance())

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

        self.tree_stu.tag_configure("highlight", background="#fef08a", font=("Segoe UI", 9, "bold"))
        self.tree_stu.bind("<Double-1>", lambda e: self.open_selected_student_attendance())

        sb_s = ttk.Scrollbar(self.s_tbl_frame, orient="vertical", command=self.tree_stu.yview)
        self.tree_stu.configure(yscroll=sb_s.set)
        self.tree_stu.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_s.pack(side=tk.RIGHT, fill=tk.Y)

    def open_selected_student_attendance(self):
        if not hasattr(self, 'tree_stu') or self.tree_stu is None:
            return
        sel = self.tree_stu.selection()
        if not sel:
            messagebox.showwarning("Notice", "Please select a student from the table.")
            return
        vals = self.tree_stu.item(sel[0])['values']
        if not vals:
            return
        sid = str(vals[1]).strip()
        IndividualStudentAttendanceDialog(self, self.db, sid)

    def open_individual_monthly_view(self):
        if self.student_id:
            IndividualStudentAttendanceDialog(self, self.db, self.student_id)

    def open_selected_teacher_attendance(self):
        if not hasattr(self, 'tree_teach') or self.tree_teach is None:
            return
        sel = self.tree_teach.selection()
        if not sel:
            messagebox.showwarning("Notice", "Please select a teacher from the table.")
            return
        vals = self.tree_teach.item(sel[0])['values']
        if not vals:
            return
        tid = str(vals[1]).strip()
        IndividualTeacherAttendanceDialog(self, self.db, tid)

    def refresh_table(self):
        if self.student_id:
            for item in self.tree_single.get_children():
                self.tree_single.delete(item)
            
            selected_year = self.entry_year.get().strip()
            selected_month_name = self.entry_month.get().strip()
            search_query = self.entry_student_search.get().strip().lower() if hasattr(self, 'entry_student_search') else ""
            
            month_idx = parse_month_input(selected_month_name)
            if not selected_year.isdigit():
                selected_year = str(datetime.now().year)
            
            display_month_name = MONTH_NAMES[month_idx - 1]
            month_prefix = f"{selected_year}-{month_idx:02d}-"
            
            logs = self.db.get_student_attendance(self.student_id)
            student = self.db.get_student(self.student_id)
            sname = student['name'] if student else self.student_id
            is_college = student and student.get('education_type') == 'College'
            
            present_days = 0
            absent_days = 0
            leave_days = 0
            
            yearly_present = 0
            yearly_absent = 0
            yearly_leave = 0

            matched_records = 0

            # Sort logs chronologically in ascending order by actual date value
            def parse_log_date(l):
                d_str = str(l.get('date', '')).strip()
                try:
                    return datetime.strptime(d_str, "%Y-%m-%d")
                except Exception:
                    try:
                        clean_d = d_str.split(" ")[0].replace("/", "-")
                        parts = [int(p) for p in clean_d.split("-") if p.isdigit()]
                        if len(parts) == 3:
                            if parts[0] > 1000:
                                return datetime(parts[0], parts[1], parts[2])
                            else:
                                return datetime(parts[2], parts[1], parts[0])
                    except Exception:
                        pass
                return datetime.min

            sorted_logs = sorted(logs, key=parse_log_date)
            
            for l in sorted_logs:
                ldate = l['date']
                lstatus = l['status']
                
                # Yearly stats
                if ldate.startswith(f"{selected_year}-"):
                    if lstatus == 'Present':
                        yearly_present += 1
                    elif lstatus == 'Absent':
                        yearly_absent += 1
                    elif lstatus == 'Leave':
                        yearly_leave += 1
                
                # Monthly stats and filtered insertion
                if ldate.startswith(month_prefix):
                    if lstatus == 'Present':
                        present_days += 1
                    elif lstatus == 'Absent':
                        absent_days += 1
                    elif lstatus == 'Leave':
                        leave_days += 1
                    
                    if is_college:
                        enr_no = student.get('enrollment_number') or self.student_id
                        scourse = student.get('course') or student.get('current_class') or "N/A"
                        row_vals = (ldate, enr_no, sname, scourse, lstatus)
                    else:
                        sclass = student.get('current_class') or "N/A"
                        ssec = student.get('section') or "N/A"
                        row_vals = (ldate, self.student_id, sname, sclass, ssec, lstatus)

                    row_str = " ".join(str(v) for v in row_vals).lower()
                    tags = []
                    if search_query:
                        if search_query in row_str:
                            tags.append("highlight")
                            matched_records += 1
                        else:
                            continue
                    else:
                        matched_records += 1

                    self.tree_single.insert("", tk.END, values=row_vals, tags=tuple(tags))
            
            if search_query and matched_records == 0:
                if is_college:
                    self.tree_single.insert("", tk.END, values=("No record found", "-", "-", "-", "-"))
                else:
                    self.tree_single.insert("", tk.END, values=("No record found", "-", "-", "-", "-", "-"))

            # Monthly summary
            monthly_total = present_days + absent_days + leave_days
            monthly_pct = (present_days / monthly_total) * 100.0 if monthly_total > 0 else 0.0
            
            monthly_text = (
                f"📊 Monthly Summary ({display_month_name} {selected_year}): "
                f"Present: {present_days} | Absent: {absent_days} | Leave: {leave_days} | "
                f"Recorded Days: {monthly_total} | Attendance Score: {monthly_pct:.2f}%"
            )
            self.lbl_monthly_summary.config(text=monthly_text)
            
            # Yearly summary
            yearly_total = yearly_present + yearly_absent + yearly_leave
            yearly_pct = (yearly_present / yearly_total) * 100.0 if yearly_total > 0 else 0.0
            yearly_text = (
                f"📅 Yearly Summary ({selected_year}): "
                f"Present: {yearly_present} | Absent: {yearly_absent} | Leave: {yearly_leave} | "
                f"Recorded Days: {yearly_total} | Attendance Score: {yearly_pct:.2f}%"
            )
            self.lbl_yearly_summary.config(text=yearly_text)
        else:
            self._setup_student_tree()

            for item in self.tree_stu.get_children():
                self.tree_stu.delete(item)
            for item in self.tree_teach.get_children():
                self.tree_teach.delete(item)

            today = get_current_date()
            summary = self.db.get_attendance_dashboard_summary(today)
            mode = self.combo_category.get() if hasattr(self, 'combo_category') else "School"

            stu_search = self.entry_stu_tab_search.get().strip().lower() if hasattr(self, 'entry_stu_tab_search') else ""
            teach_search = self.entry_teach_tab_search.get().strip().lower() if hasattr(self, 'entry_teach_tab_search') else ""

            present_count = 0
            absent_count = 0

            # Filtered lists to populate treeview
            present_rows = []
            for row in summary['students_present']:
                stu = self.db.get_student(row['student_id']) or {}
                stu_edu_type = stu.get('education_type', 'School')
                if stu_edu_type == mode:
                    present_count += 1
                    present_rows.append((row, stu))

            absent_rows = []
            for row in summary['students_absent']:
                stu = self.db.get_student(row['student_id']) or {}
                stu_edu_type = stu.get('education_type', 'School')
                if stu_edu_type == mode:
                    absent_count += 1
                    absent_rows.append((row, stu))

            self.lbl_stu_present.config(text=f"Present Students ({today}): {present_count}")
            self.lbl_stu_absent.config(text=f"Absent Students ({today}): {absent_count}")
            self.lbl_teach_present.config(text=f"Present Teachers ({today}): {summary['teachers_present_count']}")
            self.lbl_teach_absent.config(text=f"Absent Teachers ({today}): {summary['teachers_absent_count']}")

            matched_stu = 0
            # Populate Students: Present first, then Absent
            for row, stu in present_rows:
                if mode == "School":
                    sclass = stu.get('current_class') or row.get('course') or "N/A"
                    ssec = stu.get('section') or "N/A"
                    row_vals = (row['date'], row['student_id'], row['name'], sclass, ssec, "Present")
                else:
                    enr_no = stu.get('enrollment_number') or row['student_id']
                    scourse = stu.get('course') or row.get('course') or "N/A"
                    row_vals = (row['date'], enr_no, row['name'], scourse, "Present")

                row_str = " ".join(str(v) for v in row_vals).lower()
                tags = []
                if stu_search:
                    if stu_search in row_str:
                        tags.append("highlight")
                        matched_stu += 1
                    else:
                        continue
                else:
                    matched_stu += 1

                self.tree_stu.insert("", tk.END, values=row_vals, tags=tuple(tags))

            for row, stu in absent_rows:
                if mode == "School":
                    sclass = stu.get('current_class') or row.get('course') or "N/A"
                    ssec = stu.get('section') or "N/A"
                    row_vals = (row['date'], row['student_id'], row['name'], sclass, ssec, "Absent")
                else:
                    enr_no = stu.get('enrollment_number') or row['student_id']
                    scourse = stu.get('course') or row.get('course') or "N/A"
                    row_vals = (row['date'], enr_no, row['name'], scourse, "Absent")

                row_str = " ".join(str(v) for v in row_vals).lower()
                tags = []
                if stu_search:
                    if stu_search in row_str:
                        tags.append("highlight")
                        matched_stu += 1
                    else:
                        continue
                else:
                    matched_stu += 1

                self.tree_stu.insert("", tk.END, values=row_vals, tags=tuple(tags))

            if stu_search and matched_stu == 0:
                if mode == "School":
                    self.tree_stu.insert("", tk.END, values=("No record found", "-", "-", "-", "-", "-"))
                else:
                    self.tree_stu.insert("", tk.END, values=("No record found", "-", "-", "-", "-"))

            # Populate Teachers: Present first, then Absent
            matched_teach = 0
            for row in summary['teachers_present']:
                row_vals = (row['date'], row['teacher_id'], row['name'], row['department'], "Present")
                row_str = " ".join(str(v) for v in row_vals).lower()
                tags = []
                if teach_search:
                    if teach_search in row_str:
                        tags.append("highlight")
                        matched_teach += 1
                    else:
                        continue
                else:
                    matched_teach += 1
                self.tree_teach.insert("", tk.END, values=row_vals, tags=tuple(tags))

            for row in summary['teachers_absent']:
                row_vals = (row['date'], row['teacher_id'], row['name'], row['department'], "Absent")
                row_str = " ".join(str(v) for v in row_vals).lower()
                tags = []
                if teach_search:
                    if teach_search in row_str:
                        tags.append("highlight")
                        matched_teach += 1
                    else:
                        continue
                else:
                    matched_teach += 1
                self.tree_teach.insert("", tk.END, values=row_vals, tags=tuple(tags))

            if teach_search and matched_teach == 0:
                self.tree_teach.insert("", tk.END, values=("No record found", "-", "-", "-", "-"))
                self.tree_teach.insert("", tk.END, values=row_vals, tags=tuple(tags))

            if teach_search and matched_teach == 0:
                self.tree_teach.insert("", tk.END, values=("No record found", "-", "-", "-", "-"))
