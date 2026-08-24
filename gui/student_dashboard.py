import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DBManager
from gui.theme import COLORS, FONTS, StatCard
from gui.attendance_view import AttendanceViewFrame
from gui.charts_view import AnalyticsChartsFrame
from ml.prediction import PerformancePredictor

class StudentDashboard(tk.Toplevel):
    """Personal Student Portal for student user role."""
    def __init__(self, welcome_win: tk.Tk, db_manager: DBManager, user_data: dict):
        super().__init__(welcome_win)
        self.welcome_win = welcome_win
        self.db = db_manager
        self.user_data = user_data
        self.predictor = PerformancePredictor()

        # Find linked student record
        self.student = self.db.get_student_by_user_id(self.user_data['id'])
        if not self.student:
            # Fallback if student account was registered directly with username matching student_id
            self.student = self.db.get_student(self.user_data['username'])

        if not self.student:
            messagebox.showerror("Error", "No linked student profile found for this account.")
            self.destroy()
            self.welcome_win.deiconify()
            return

        self.student_id = self.student['student_id']

        self.title(f"Student Portal - {self.student['name']} ({self.student_id})")
        self.geometry("1050x700")
        self.minsize(950, 600)
        self.protocol("WM_DELETE_WINDOW", self.on_logout)

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Top Bar
        top_bar = tk.Frame(self, bg="#7c3aed", height=60)
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        top_bar.pack_propagate(False)

        lbl_title = tk.Label(top_bar, text=f"🎓 Student Portal | {self.student['name']}", font=("Segoe UI", 14, "bold"), bg="#7c3aed", fg="#ffffff")
        lbl_title.pack(side=tk.LEFT, padx=20)

        btn_logout = tk.Button(top_bar, text="🚪 Logout", font=("Segoe UI", 9, "bold"), bg="#dc2626", fg="#ffffff", activebackground="#b91c1c", activeforeground="#ffffff", bd=0, cursor="hand2", command=self.on_logout)
        btn_logout.pack(side=tk.RIGHT, padx=20, ipadx=10, ipady=4)

        lbl_info = tk.Label(top_bar, text=f"ID: {self.student_id} | {self.student.get('course', '')}", font=("Segoe UI", 9), bg="#7c3aed", fg="#f3e8ff")
        lbl_info.pack(side=tk.RIGHT, padx=10)

        # Sidebar
        sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=220)
        sidebar.grid(row=1, column=0, sticky="nsew")

        nav_buttons = [
            ("👤 My Profile", self.show_profile),
            ("📅 Attendance History", self.show_attendance),
            ("📑 Marks & Grade", self.show_marks),
            ("🤖 ML Performance Prediction", self.show_ml_prediction),
            ("📊 Performance Charts", self.show_charts),
            ("⚙️ Settings", self.show_settings),
            ("📅 Holiday", self.show_holidays),
            ("🚪 Logout", self.on_logout)
        ]

        for text, cmd in nav_buttons:
            btn = ttk.Button(sidebar, text=text, style="Sidebar.TButton", command=cmd)
            btn.pack(fill=tk.X, pady=2)

        # Content Frame
        self.content_frame = ttk.Frame(self, padding=15)
        self.content_frame.grid(row=1, column=1, sticky="nsew")

        self.show_profile()

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_profile(self, edit_mode: bool = False):
        self.clear_content()

        self.student = self.db.get_student(self.student_id) or self.student

        hdr = ttk.Frame(self.content_frame)
        hdr.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(hdr, text="👤 Student Profile & Academic Details", font=FONTS["h1"]).pack(side=tk.LEFT)
        if not edit_mode:
            ttk.Button(hdr, text="✏️ Edit Profile", style="Primary.TButton", command=lambda: self.show_profile(edit_mode=True)).pack(side=tk.RIGHT)

        # Metrics Cards
        cards_frame = ttk.Frame(self.content_frame)
        cards_frame.pack(fill=tk.X, pady=(0, 15))
        cards_frame.columnconfigure((0,1,2,3), weight=1)

        att_stats = self.db.get_student_attendance_stats(self.student_id)
        overall_m = self.db.get_student_overall_marks(self.student_id)

        StatCard(cards_frame, "Attendance %", f"{att_stats['percentage']}%", "📅", "#16a34a").grid(row=0, column=0, padx=5, sticky="ew")
        StatCard(cards_frame, "Total Marks", f"{overall_m['total_marks']}/{overall_m['max_marks'] or 180.0}", "⭐", "#2563eb").grid(row=0, column=1, padx=5, sticky="ew")
        StatCard(cards_frame, "Overall Grade", f"{overall_m['grade']}", "🏆", "#7c3aed").grid(row=0, column=2, padx=5, sticky="ew")
        StatCard(cards_frame, "Study Hours/Day", f"{self.student.get('study_hours', 2.0)} hrs", "⏰", "#d97706").grid(row=0, column=3, padx=5, sticky="ew")

        p = self.db.get_parent_by_student_id(self.student_id) or {}

        if not edit_mode:
            # Profile Box - View Mode
            pbox = ttk.LabelFrame(self.content_frame, text="Personal & Academic Details", padding=15)
            pbox.pack(fill=tk.BOTH, expand=True)

            edu_type = self.student.get('education_type', 'School')
            if edu_type == "College":
                id_line = f"• Enrollment Number: {self.student.get('enrollment_number') or self.student_id}"
                edu_lines = f"""• Education Type: College
            • College Name: {self.student.get('college_name') or 'N/A'}
            • Course / Program: {self.student.get('course') or 'N/A'}
            • Semester / Year: {self.student.get('semester') or 'N/A'}"""
            else:
                id_line = f"• Student ID: {self.student_id}"
                edu_lines = f"""• Education Type: School
            • School Name: {self.student.get('school_name') or 'N/A'}
            • Current Class: {self.student.get('current_class') or 'N/A'}
            • Section: {self.student.get('section') or 'N/A'}"""

            profile_info = f"""
            PERSONAL & ACADEMIC DETAILS:
            {id_line}
            • Name: {self.student['name']}
            • Gender: {self.student.get('gender', 'N/A')}
            • Date of Birth: {self.student.get('dob', 'N/A')}
            {edu_lines}
            • Admission Date: {self.student.get('admission_date', 'N/A')}
            • Email: {self.student.get('email', 'N/A')}
            • Phone: {self.student.get('phone', 'N/A')}
            • Address: {self.student.get('address', 'N/A')}
            • Daily Study Hours: {self.student.get('study_hours', 2.0)} hrs
            
            PARENT / GUARDIAN DETAILS:
            • Guardian Name: {self.student.get('guardian_name') or p.get('name') or 'N/A'}
            • Father Name: {self.student.get('father_name') or 'N/A'}
            • Father Phone: {self.student.get('father_phone') or p.get('phone') or 'N/A'}
            • Mother Name: {self.student.get('mother_name') or 'N/A'}
            • Mother Phone: {self.student.get('mother_phone') or 'N/A'}
            • Parent Occupation: {p.get('occupation') or 'N/A'}
            • Relationship: {p.get('relationship') or 'N/A'}
            • Emergency Contact: {p.get('emergency_contact') or 'N/A'}
            """
            ttk.Label(pbox, text=profile_info, font=("Consolas", 10), justify="left").pack(anchor=tk.W)
        else:
            # Profile Box - Edit Mode
            form_card = ttk.LabelFrame(self.content_frame, text=" Edit Personal Information ", padding=20)
            form_card.pack(fill=tk.BOTH, expand=True)

            ttk.Label(form_card, text="Student ID:", font=FONTS["body_bold"]).grid(row=0, column=0, sticky="w", pady=8)
            ttk.Label(form_card, text=f"{self.student_id} (Protected)", font=FONTS["body_bold"], foreground=COLORS["text_muted"]).grid(row=0, column=1, sticky="w", pady=8, padx=10)

            ttk.Label(form_card, text="Full Name:", font=FONTS["body_bold"]).grid(row=1, column=0, sticky="w", pady=8)
            ttk.Label(form_card, text=f"{self.student['name']} (Protected)", font=FONTS["body"]).grid(row=1, column=1, sticky="w", pady=8, padx=10)

            ttk.Label(form_card, text="Phone Number:", font=FONTS["body_bold"]).grid(row=2, column=0, sticky="w", pady=8)
            entry_phone = ttk.Entry(form_card, width=35)
            entry_phone.insert(0, self.student.get('phone', ''))
            entry_phone.grid(row=2, column=1, sticky="w", pady=8, padx=10)

            ttk.Label(form_card, text="Email Address:", font=FONTS["body_bold"]).grid(row=3, column=0, sticky="w", pady=8)
            entry_email = ttk.Entry(form_card, width=35)
            entry_email.insert(0, self.student.get('email', ''))
            entry_email.grid(row=3, column=1, sticky="w", pady=8, padx=10)

            ttk.Label(form_card, text="Address:", font=FONTS["body_bold"]).grid(row=4, column=0, sticky="w", pady=8)
            entry_address = ttk.Entry(form_card, width=40)
            entry_address.insert(0, self.student.get('address', ''))
            entry_address.grid(row=4, column=1, sticky="w", pady=8, padx=10)

            def save_student_profile_callback():
                from utils.validators import validate_email, validate_phone
                phone = entry_phone.get().strip()
                email = entry_email.get().strip()
                address = entry_address.get().strip()

                if phone and not validate_phone(phone):
                    messagebox.showwarning("Validation Error", "Phone number must contain exactly 10 digits.")
                    return
                if email and not validate_email(email):
                    messagebox.showwarning("Validation Error", "Please enter a valid Email Address.")
                    return

                student_data = dict(self.student)
                student_data['phone'] = phone
                student_data['email'] = email
                student_data['address'] = address

                self.db.update_student(self.student_id, student_data)
                self.student = self.db.get_student(self.student_id)
                messagebox.showinfo("Success", "Profile information updated successfully!")
                self.show_profile(edit_mode=False)

            btn_bar = ttk.Frame(form_card)
            btn_bar.grid(row=5, column=0, columnspan=2, sticky="w", pady=(15, 0))

            ttk.Button(btn_bar, text="💾 Save Profile", style="Primary.TButton", command=save_student_profile_callback).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(btn_bar, text="Cancel", command=lambda: self.show_profile(edit_mode=False)).pack(side=tk.LEFT)

    def show_attendance(self):
        self.clear_content()
        view_frame = AttendanceViewFrame(self.content_frame, self.db, student_id=self.student_id, is_admin_or_teacher=False)
        view_frame.pack(fill=tk.BOTH, expand=True)

        from face_attendance.face_recognition import FaceAttendanceScannerWindow
        FaceAttendanceScannerWindow(self, self.db, target_role="Student", on_attendance_marked=view_frame.refresh_table)

    def show_marks(self):
        self.clear_content()

        hdr = ttk.Frame(self.content_frame)
        hdr.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(hdr, text="📑 Subject Marks & Grade Evaluation", font=FONTS["h1"]).pack(side=tk.LEFT)
        ttk.Button(hdr, text="🔄 Refresh Marks", command=self.show_marks).pack(side=tk.RIGHT)

        tbl_frame = ttk.Frame(self.content_frame)
        tbl_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("subject", "internal", "mid", "proj", "viva", "final", "total", "pct", "grade", "status")
        tree = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=12)

        tree.heading("subject", text="Subject")
        tree.heading("internal", text="Internal (20)")
        tree.heading("mid", text="Mid-Term (30)")
        tree.heading("proj", text="Project (20)")
        tree.heading("viva", text="Viva (10)")
        tree.heading("final", text="Final (100)")
        tree.heading("total", text="Total (180)")
        tree.heading("pct", text="Pct %")
        tree.heading("grade", text="Grade")
        tree.heading("status", text="Status")

        for c in cols:
            tree.column(c, width=90, anchor="center")
        tree.column("subject", width=180, anchor="w")

        all_m = self.db.get_all_student_marks(self.student_id)
        for m in all_m:
            tree.insert("", tk.END, values=(
                m['subject'], m['internal_marks'], m['mid_term_marks'], m['project_marks'],
                m['viva_marks'], m['final_exam_marks'], m['total_marks'], f"{m['percentage']:.1f}%",
                m['grade'], m['status']
            ))
        tree.pack(fill=tk.BOTH, expand=True)

    def show_ml_prediction(self):
        self.clear_content()

        ttk.Label(self.content_frame, text="🤖 Machine Learning Academic Risk Prediction", font=FONTS["h1"]).pack(anchor=tk.W, pady=(0, 10))

        att = self.db.get_student_attendance_stats(self.student_id)['percentage']
        marks = self.db.get_student_marks(self.student_id) or {}

        pred = self.predictor.predict_performance(
            attendance_pct=att,
            study_hours=self.student.get('study_hours', 2.0),
            previous_pct=self.student.get('previous_percentage', 75.0),
            internal_marks=marks.get('internal_marks', 0),
            mid_term_marks=marks.get('mid_term_marks', 0),
            project_marks=marks.get('project_marks', 0),
            viva_marks=marks.get('viva_marks', 0)
        )

        card = ttk.LabelFrame(self.content_frame, text="AI Analysis Result", padding=20)
        card.pack(fill=tk.BOTH, expand=True)

        res_text = f"""
        PREDICTED PERFORMANCE CATEGORY: {pred['category'].upper()}
        ESTIMATED FINAL SCORE: {pred['predicted_score']}%
        RISK LEVEL: {pred['risk_level'].upper()}
        
        ACADEMIC RECOMMENDATION:
        {pred['recommendations']}
        """
        color = COLORS["success"] if pred['risk_level'] == "Low Risk" else COLORS["danger"]
        lbl = tk.Label(card, text=res_text, font=("Segoe UI", 11, "bold"), fg=color, bg=COLORS["bg_card"], justify="left")
        lbl.pack(anchor=tk.W)

    def show_charts(self):
        self.clear_content()
        AnalyticsChartsFrame(self.content_frame, self.db, student_id=self.student_id).pack(fill=tk.BOTH, expand=True)

    def show_notifications(self):
        self.clear_content()
        ttk.Label(self.content_frame, text="🔔 My Notifications", font=FONTS["h1"]).pack(anchor=tk.W, pady=(0, 10))
        notifs = self.db.get_notifications("Student", self.student_id)
        for n in notifs:
            card = ttk.Frame(self.content_frame, style="Card.TFrame", padding=10)
            card.pack(fill=tk.X, pady=5)
            ttk.Label(card, text=f"[{n['date']}] {n['title']}", font=FONTS["body_bold"], style="Card.TLabel").pack(anchor=tk.W)
            ttk.Label(card, text=n['message'], font=FONTS["body"], style="Card.TLabel").pack(anchor=tk.W)

    def show_settings(self):
        self.clear_content()
        from gui.settings_view import SettingsViewFrame
        SettingsViewFrame(self.content_frame, self.db, self.user_data, "Student", on_cancel=self.show_profile).pack(fill=tk.BOTH, expand=True)

    def show_holidays(self):
        self.clear_content()
        from gui.holiday_view import HolidayViewFrame
        HolidayViewFrame(self.content_frame, self.db).pack(fill=tk.BOTH, expand=True)

    def on_logout(self):
        if messagebox.askyesno("Confirm Logout", "Are you sure you want to log out of your session?"):
            self.destroy()
            self.welcome_win.deiconify()
