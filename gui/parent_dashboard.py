import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DBManager
from gui.theme import COLORS, FONTS, StatCard
from gui.attendance_view import AttendanceViewFrame
from gui.charts_view import AnalyticsChartsFrame
from ml.prediction import PerformancePredictor

class ParentDashboard(tk.Toplevel):
    """Parent Portal supporting multiple linked children per Parent account."""
    def __init__(self, welcome_win: tk.Tk, db_manager: DBManager, user_data: dict):
        super().__init__(welcome_win)
        self.welcome_win = welcome_win
        self.db = db_manager
        self.user_data = user_data
        self.predictor = PerformancePredictor()

        # Retrieve all linked children for this Parent
        self.linked_children = self.db.get_parent_students(self.user_data['id'])
        self.parent_record = self.db.get_parent_by_user_id(self.user_data['id'])

        if not self.linked_children and self.parent_record:
            # Fallback single student lookup
            s = self.db.get_student(self.parent_record.get('student_id', ''))
            if s:
                self.linked_children = [s]

        if not self.linked_children:
            messagebox.showerror("Access Error", "Parent account is not linked to any valid student ID.")
            self.destroy()
            self.welcome_win.deiconify()
            return

        # Default active child
        self.current_child_idx = 0
        self.child_student = self.linked_children[0]
        self.child_student_id = self.child_student['student_id']

        self.title(f"Parent Portal - Child: {self.child_student['name']} ({self.child_student_id})")
        self.geometry("1050x700")
        self.minsize(950, 600)
        self.protocol("WM_DELETE_WINDOW", self.on_logout)

        self.current_view_cmd = self.show_child_profile
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Top Header Bar
        top_bar = tk.Frame(self, bg="#059669", height=60)
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        top_bar.pack_propagate(False)

        self.lbl_title = tk.Label(top_bar, text=f"👨‍👩‍👧 Parent Portal | Child: {self.child_student['name']}", font=("Segoe UI", 13, "bold"), bg="#059669", fg="#ffffff")
        self.lbl_title.pack(side=tk.LEFT, padx=15)

        btn_logout = tk.Button(top_bar, text="🚪 Logout", font=("Segoe UI", 9, "bold"), bg="#dc2626", fg="#ffffff", activebackground="#b91c1c", activeforeground="#ffffff", bd=0, cursor="hand2", command=self.on_logout)
        btn_logout.pack(side=tk.RIGHT, padx=15, ipadx=10, ipady=4)

        pname = self.parent_record['name'] if self.parent_record else self.user_data['username']
        lbl_parent = tk.Label(top_bar, text=f"Parent: {pname}", font=("Segoe UI", 9), bg="#059669", fg="#ecfdf5")
        lbl_parent.pack(side=tk.RIGHT, padx=10)

        # Child Selector Dropdown (if multiple children)
        if len(self.linked_children) > 1:
            child_frame = tk.Frame(top_bar, bg="#059669")
            child_frame.pack(side=tk.LEFT, padx=15)

            tk.Label(child_frame, text="Select Child: ", font=("Segoe UI", 9, "bold"), bg="#059669", fg="#ffffff").pack(side=tk.LEFT)

            child_options = [f"{s['name']} ({s['student_id']})" for s in self.linked_children]
            self.combo_child_select = ttk.Combobox(child_frame, values=child_options, state="readonly", width=26)
            self.combo_child_select.current(0)
            self.combo_child_select.pack(side=tk.LEFT)
            self.combo_child_select.bind("<<ComboboxSelected>>", self._on_child_selected)

        # Sidebar
        sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=220)
        sidebar.grid(row=1, column=0, sticky="nsew")

        nav_buttons = [
            ("👤 My Profile", lambda: self._switch_view(lambda: self.show_parent_profile(edit_mode=False))),
            ("👶 Child Profile", lambda: self._switch_view(self.show_child_profile)),
            ("📅 Attendance History", lambda: self._switch_view(self.show_attendance)),
            ("📑 Academic Marks", lambda: self._switch_view(self.show_marks)),
            ("🤖 AI Prediction & Risk", lambda: self._switch_view(self.show_prediction)),
            ("📊 Performance Charts", lambda: self._switch_view(self.show_charts)),
            ("⚙️ Settings", lambda: self._switch_view(self.show_settings)),
            ("📅 Holiday", lambda: self._switch_view(self.show_holidays)),
            ("🚪 Logout", self.on_logout)
        ]

        for text, cmd in nav_buttons:
            btn = ttk.Button(sidebar, text=text, style="Sidebar.TButton", command=cmd)
            btn.pack(fill=tk.X, pady=2)

        # Content Frame
        self.content_frame = ttk.Frame(self, padding=15)
        self.content_frame.grid(row=1, column=1, sticky="nsew")

        self.show_parent_profile(edit_mode=False)

    def _switch_view(self, view_func):
        self.current_view_cmd = view_func
        view_func()

    def _on_child_selected(self, event=None):
        idx = self.combo_child_select.current()
        if 0 <= idx < len(self.linked_children):
            self.current_child_idx = idx
            self.child_student = self.linked_children[idx]
            self.child_student_id = self.child_student['student_id']

            self.lbl_title.config(text=f"👨‍👩‍👧 Parent Portal | Child: {self.child_student['name']}")
            self.title(f"Parent Portal - Child: {self.child_student['name']} ({self.child_student_id})")

            # Refresh active view for selected child
            if self.current_view_cmd:
                self.current_view_cmd()

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_parent_profile(self, edit_mode: bool = False):
        self.clear_content()

        self.parent_record = self.db.get_parent_by_user_id(self.user_data['id']) or self.parent_record or {}

        hdr = ttk.Frame(self.content_frame)
        hdr.pack(fill=tk.X, pady=(0, 15))

        pname = self.parent_record.get('name', self.user_data['username'])
        ttk.Label(hdr, text=f"👤 Parent Profile - {pname}", font=FONTS["h1"]).pack(side=tk.LEFT)
        if not edit_mode:
            ttk.Button(hdr, text="✏️ Edit Profile", style="Primary.TButton", command=lambda: self.show_parent_profile(edit_mode=True)).pack(side=tk.RIGHT)

        children = self.db.get_parent_students(self.user_data['id'])
        child_str = ", ".join([f"{c['name']} ({c['student_id']})" for c in children]) if children else "N/A"

        if not edit_mode:
            pbox = ttk.LabelFrame(self.content_frame, text=" Authorized Parent Profile Details ", padding=20)
            pbox.pack(fill=tk.BOTH, expand=True)

            info = f"""
            • Parent ID Code: {self.parent_record.get('parent_id_code', 'N/A')}
            • Full Name: {self.parent_record.get('name', 'N/A')}
            • Phone Number: {self.parent_record.get('phone', 'N/A')}
            • Email Address: {self.parent_record.get('email', 'N/A')}
            • Address: {self.parent_record.get('address', 'N/A')}
            • Occupation: {self.parent_record.get('occupation', 'N/A')}
            • Emergency Contact: {self.parent_record.get('emergency_contact', 'N/A')}
            • Linked Children: {child_str}
            """
            ttk.Label(pbox, text=info, font=("Consolas", 11), justify="left").pack(anchor=tk.W, pady=10)
        else:
            form_card = ttk.LabelFrame(self.content_frame, text=" Edit Parent Profile Information ", padding=20)
            form_card.pack(fill=tk.BOTH, expand=True)

            ttk.Label(form_card, text="Parent ID Code:", font=FONTS["body_bold"]).grid(row=0, column=0, sticky="w", pady=8)
            ttk.Label(form_card, text=f"{self.parent_record.get('parent_id_code', 'N/A')} (Protected)", font=FONTS["body_bold"], foreground=COLORS["text_muted"]).grid(row=0, column=1, sticky="w", pady=8, padx=10)

            ttk.Label(form_card, text="Full Name *:", font=FONTS["body_bold"]).grid(row=1, column=0, sticky="w", pady=8)
            entry_name = ttk.Entry(form_card, width=35)
            entry_name.insert(0, self.parent_record.get('name', ''))
            entry_name.grid(row=1, column=1, sticky="w", pady=8, padx=10)

            ttk.Label(form_card, text="Phone Number *:", font=FONTS["body_bold"]).grid(row=2, column=0, sticky="w", pady=8)
            entry_phone = ttk.Entry(form_card, width=35)
            entry_phone.insert(0, self.parent_record.get('phone', ''))
            entry_phone.grid(row=2, column=1, sticky="w", pady=8, padx=10)

            ttk.Label(form_card, text="Email Address:", font=FONTS["body_bold"]).grid(row=3, column=0, sticky="w", pady=8)
            entry_email = ttk.Entry(form_card, width=35)
            entry_email.insert(0, self.parent_record.get('email', ''))
            entry_email.grid(row=3, column=1, sticky="w", pady=8, padx=10)

            ttk.Label(form_card, text="Address:", font=FONTS["body_bold"]).grid(row=4, column=0, sticky="w", pady=8)
            entry_address = ttk.Entry(form_card, width=40)
            entry_address.insert(0, self.parent_record.get('address', ''))
            entry_address.grid(row=4, column=1, sticky="w", pady=8, padx=10)

            ttk.Label(form_card, text="Occupation:", font=FONTS["body_bold"]).grid(row=5, column=0, sticky="w", pady=8)
            entry_occupation = ttk.Entry(form_card, width=35)
            entry_occupation.insert(0, self.parent_record.get('occupation', ''))
            entry_occupation.grid(row=5, column=1, sticky="w", pady=8, padx=10)

            ttk.Label(form_card, text="Emergency Contact:", font=FONTS["body_bold"]).grid(row=6, column=0, sticky="w", pady=8)
            entry_emergency = ttk.Entry(form_card, width=35)
            entry_emergency.insert(0, self.parent_record.get('emergency_contact', ''))
            entry_emergency.grid(row=6, column=1, sticky="w", pady=8, padx=10)

            def save_parent_profile_callback():
                from utils.validators import validate_email, validate_phone
                name = entry_name.get().strip()
                phone = entry_phone.get().strip()
                email = entry_email.get().strip()
                address = entry_address.get().strip()
                occupation = entry_occupation.get().strip()
                emergency = entry_emergency.get().strip()

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
                    "address": address,
                    "occupation": occupation,
                    "emergency_contact": emergency
                }
                p_code = self.parent_record.get('parent_id_code', '')
                self.db.update_parent_profile(self.user_data['id'], parent_data, p_code)
                self.parent_record = self.db.get_parent_by_user_id(self.user_data['id'])
                messagebox.showinfo("Success", "Parent profile updated successfully!")
                self.show_parent_profile(edit_mode=False)

            btn_bar = ttk.Frame(form_card)
            btn_bar.grid(row=7, column=0, columnspan=2, sticky="w", pady=(15, 0))

            ttk.Button(btn_bar, text="💾 Save Profile", style="Primary.TButton", command=save_parent_profile_callback).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(btn_bar, text="Cancel", command=lambda: self.show_parent_profile(edit_mode=False)).pack(side=tk.LEFT)

    def show_child_profile(self):
        self.clear_content()

        ttk.Label(self.content_frame, text=f"👶 Child Profile: {self.child_student['name']}", font=FONTS["h1"]).pack(anchor=tk.W, pady=(0, 15))

        cards_frame = ttk.Frame(self.content_frame)
        cards_frame.pack(fill=tk.X, pady=(0, 15))
        cards_frame.columnconfigure((0,1,2,3), weight=1)

        att_stats = self.db.get_student_attendance_stats(self.child_student_id)
        overall_m = self.db.get_student_overall_marks(self.child_student_id)

        StatCard(cards_frame, "Attendance %", f"{att_stats['percentage']}%", "📅", "#16a34a").grid(row=0, column=0, padx=5, sticky="ew")
        StatCard(cards_frame, "Total Marks", f"{overall_m['total_marks']}/{overall_m['max_marks'] or 180.0}", "⭐", "#2563eb").grid(row=0, column=1, padx=5, sticky="ew")
        StatCard(cards_frame, "Grade", f"{overall_m['grade']}", "🏆", "#7c3aed").grid(row=0, column=2, padx=5, sticky="ew")
        StatCard(cards_frame, "Daily Study Hrs", f"{self.child_student.get('study_hours', 2.0)} hrs", "⏰", "#d97706").grid(row=0, column=3, padx=5, sticky="ew")

        box = ttk.LabelFrame(self.content_frame, text="Academic Summary", padding=15)
        box.pack(fill=tk.BOTH, expand=True)

        info = f"""
        • Student ID: {self.child_student_id}
        • Student Name: {self.child_student['name']}
        • Course: {self.child_student.get('course', 'N/A')}
        • Department: {self.child_student.get('department', 'N/A')}
        • Current Class: {self.child_student.get('current_class', 'N/A')}
        • Section: {self.child_student.get('section', 'N/A')}
        • Daily Study Hours: {self.child_student.get('study_hours', 'N/A')} hrs/day
        • Total Working Days Tracked: {att_stats['total_days']} days
        • Present Days: {att_stats['present_days']} days
        • Absent Days: {att_stats['absent_days']} days
        """
        ttk.Label(box, text=info, font=("Consolas", 10), justify="left").pack(anchor=tk.W)

    def show_attendance(self):
        self.clear_content()
        AttendanceViewFrame(self.content_frame, self.db, student_id=self.child_student_id, is_admin_or_teacher=False).pack(fill=tk.BOTH, expand=True)

    def show_marks(self):
        self.clear_content()
        # Automatically mark as viewed and remove active marks notification when Parent views marks
        self.db.clear_parent_marks_notifications(self.child_student_id)

        hdr = ttk.Frame(self.content_frame)
        hdr.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(hdr, text=f"📑 Academic Marks Breakdown - {self.child_student['name']}", font=FONTS["h1"]).pack(side=tk.LEFT)
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

        all_m = self.db.get_all_student_marks(self.child_student_id)
        for m in all_m:
            tree.insert("", tk.END, values=(
                m['subject'], m['internal_marks'], m['mid_term_marks'], m['project_marks'],
                m['viva_marks'], m['final_exam_marks'], m['total_marks'], f"{m['percentage']:.1f}%",
                m['grade'], m['status']
            ))
        tree.pack(fill=tk.BOTH, expand=True)

    def show_prediction(self):
        self.clear_content()

        ttk.Label(self.content_frame, text=f"🤖 AI Performance Prediction - {self.child_student['name']}", font=FONTS["h1"]).pack(anchor=tk.W, pady=(0, 10))

        att = self.db.get_student_attendance_stats(self.child_student_id)['percentage']
        marks = self.db.get_student_marks(self.child_student_id) or {}

        pred = self.predictor.predict_performance(
            attendance_pct=att,
            study_hours=self.child_student.get('study_hours', 2.0),
            previous_pct=self.child_student.get('previous_percentage', 75.0),
            internal_marks=marks.get('internal_marks', 0),
            mid_term_marks=marks.get('mid_term_marks', 0),
            project_marks=marks.get('project_marks', 0),
            viva_marks=marks.get('viva_marks', 0)
        )

        card = ttk.LabelFrame(self.content_frame, text=f"Parent AI Report for {self.child_student['name']}", padding=20)
        card.pack(fill=tk.BOTH, expand=True)

        res_text = f"""
        PREDICTED PERFORMANCE CATEGORY: {pred['category'].upper()}
        ESTIMATED SCORE: {pred['predicted_score']}%
        ACADEMIC RISK ASSESSMENT: {pred['risk_level'].upper()}
        
        PARENT ADVISORY / RECOMMENDATIONS:
        {pred['recommendations']}
        """
        color = COLORS["success"] if pred['risk_level'] == "Low Risk" else COLORS["danger"]
        lbl = tk.Label(card, text=res_text, font=("Segoe UI", 11, "bold"), fg=color, bg=COLORS["bg_card"], justify="left")
        lbl.pack(anchor=tk.W)

    def show_charts(self):
        self.clear_content()
        AnalyticsChartsFrame(self.content_frame, self.db, student_id=self.child_student_id).pack(fill=tk.BOTH, expand=True)

    def show_notifications(self):
        self.clear_content()
        ttk.Label(self.content_frame, text="🔔 Parent Notifications", font=FONTS["h1"]).pack(anchor=tk.W, pady=(0, 10))
        notifs = self.db.get_notifications("Parent", self.child_student_id)
        if not notifs:
            ttk.Label(self.content_frame, text="No new active notifications.", font=FONTS["body"], foreground=COLORS["text_muted"]).pack(anchor=tk.W, pady=10)
            return

        for n in notifs:
            card = ttk.Frame(self.content_frame, style="Card.TFrame", padding=12)
            card.pack(fill=tk.X, pady=5)

            top_row = ttk.Frame(card)
            top_row.pack(fill=tk.X)

            ttk.Label(top_row, text=f"[{n['date']}] {n['title']}", font=FONTS["body_bold"], style="Card.TLabel").pack(side=tk.LEFT, anchor=tk.W)

            is_marks_notif = (n['title'] == 'Marks Updated' or n['message'] == 'See your marks, marks updated.')

            def _view_notif(nid=n['id'], is_marks=is_marks_notif):
                self.db.mark_notification_as_read(nid)
                if is_marks:
                    self._switch_view(self.show_marks)
                else:
                    self.show_notifications()

            btn_view = ttk.Button(top_row, text="👁️ View", command=_view_notif)
            btn_view.pack(side=tk.RIGHT)

            ttk.Label(card, text=n['message'], font=FONTS["body"], style="Card.TLabel").pack(anchor=tk.W, pady=(4, 0))

    def show_settings(self):
        self.clear_content()
        from gui.settings_view import SettingsViewFrame
        SettingsViewFrame(self.content_frame, self.db, self.user_data, "Parent", on_cancel=self.show_child_profile).pack(fill=tk.BOTH, expand=True)

    def show_holidays(self):
        self.clear_content()
        from gui.holiday_view import HolidayViewFrame
        HolidayViewFrame(self.content_frame, self.db).pack(fill=tk.BOTH, expand=True)

    def on_logout(self):
        if messagebox.askyesno("Confirm Logout", "Are you sure you want to log out of your session?"):
            self.destroy()
            self.welcome_win.deiconify()
