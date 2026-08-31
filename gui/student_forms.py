import sys
import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DBManager
from gui.theme import COLORS, FONTS
from utils.validators import validate_email, validate_phone, validate_study_hours, validate_student_id

class StudentFormDialog(tk.Toplevel):
    """Full Student Registration & Edit Modal Form."""
    def __init__(self, parent, db_manager: DBManager, student_id: str = None, on_save_callback=None, default_edu_type: str = None, **kwargs):
        super().__init__(parent)
        self.db = db_manager
        self.student_id = student_id
        self.on_save = on_save_callback
        self.is_edit = student_id is not None

        title_text = f"Edit Student: {student_id}" if self.is_edit else "Register New Student"
        self.title(title_text)
        self.geometry("620x720")
        self.resizable(False, False)
        try:
            if parent and hasattr(parent, 'winfo_viewable') and parent.winfo_viewable():
                self.transient(parent)
                self.grab_set()
        except Exception:
            pass

        self._build_ui()
        if self.is_edit:
            self._load_student_data()

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        header_title = f"✏️ Edit Student Details" if self.is_edit else "📝 Student Registration Form"
        ttk.Label(main_frame, text=header_title, font=FONTS["h1"]).pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(main_frame, text="Complete Personal, Parent, and Academic Details.", style="Subtitle.TLabel").pack(anchor=tk.W, pady=(0, 10))

        # Notebook / Tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(5, 15))

        # Tab 1: Personal Details
        self.tab_personal = ttk.Frame(notebook, padding=15)
        notebook.add(self.tab_personal, text="Personal Details")
        self._build_personal_tab()

        # Tab 2: Parent/Guardian Details
        self.tab_parent = ttk.Frame(notebook, padding=15)
        notebook.add(self.tab_parent, text="Parent/Guardian Details")
        self._build_parent_tab()

        # Tab 3: Academic Details
        self.tab_academic = ttk.Frame(notebook, padding=15)
        notebook.add(self.tab_academic, text="Academic Details")
        self._build_academic_tab()

        # Bottom Actions
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        btn_save = ttk.Button(btn_frame, text="💾 Save Student Record", style="Primary.TButton", command=self.save_student)
        btn_save.pack(side=tk.RIGHT, padx=5)

        btn_cancel = ttk.Button(btn_frame, text="Cancel", command=self.destroy)
        btn_cancel.pack(side=tk.RIGHT, padx=5)

    def _build_personal_tab(self):
        f = self.tab_personal
        
        ttk.Label(f, text="Student ID (Unique):", font=FONTS["body_bold"]).grid(row=0, column=0, sticky="w", pady=4)
        self.entry_sid = ttk.Entry(f, width=25)
        self.entry_sid.grid(row=0, column=1, sticky="w", pady=4, padx=5)
        if self.is_edit:
            self.entry_sid.config(state="readonly")

        ttk.Label(f, text="Student Name:", font=FONTS["body_bold"]).grid(row=1, column=0, sticky="w", pady=4)
        self.entry_name = ttk.Entry(f, width=30)
        self.entry_name.grid(row=1, column=1, sticky="w", pady=4, padx=5)

        ttk.Label(f, text="Date of Birth (YYYY-MM-DD):", font=FONTS["body_bold"]).grid(row=2, column=0, sticky="w", pady=4)
        self.entry_dob = ttk.Entry(f, width=25)
        self.entry_dob.grid(row=2, column=1, sticky="w", pady=4, padx=5)

        ttk.Label(f, text="Gender:", font=FONTS["body_bold"]).grid(row=3, column=0, sticky="w", pady=4)
        self.combo_gender = ttk.Combobox(f, values=["Male", "Female", "Other"], state="readonly", width=23)
        self.combo_gender.set("Male")
        self.combo_gender.grid(row=3, column=1, sticky="w", pady=4, padx=5)

        ttk.Label(f, text="Phone Number:", font=FONTS["body_bold"]).grid(row=4, column=0, sticky="w", pady=4)
        self.entry_phone = ttk.Entry(f, width=25)
        self.entry_phone.grid(row=4, column=1, sticky="w", pady=4, padx=5)

        ttk.Label(f, text="Email Address:", font=FONTS["body_bold"]).grid(row=5, column=0, sticky="w", pady=4)
        self.entry_email = ttk.Entry(f, width=30)
        self.entry_email.grid(row=5, column=1, sticky="w", pady=4, padx=5)

        ttk.Label(f, text="Admission Date:", font=FONTS["body_bold"]).grid(row=6, column=0, sticky="w", pady=4)
        self.entry_adm_date = ttk.Entry(f, width=25)
        self.entry_adm_date.grid(row=6, column=1, sticky="w", pady=4, padx=5)

        ttk.Label(f, text="Address:", font=FONTS["body_bold"]).grid(row=7, column=0, sticky="nw", pady=4)
        self.text_address = tk.Text(f, width=30, height=3, font=FONTS["body"])
        self.text_address.grid(row=7, column=1, sticky="w", pady=4, padx=5)

        ttk.Label(f, text="Student Photo (Optional):", font=FONTS["body_bold"]).grid(row=8, column=0, sticky="w", pady=4)
        photo_frame = ttk.Frame(f)
        photo_frame.grid(row=8, column=1, sticky="w", pady=4, padx=5)
        self.lbl_photo = ttk.Label(photo_frame, text="No photo selected", font=FONTS["small"])
        self.lbl_photo.pack(side=tk.LEFT, padx=(0, 5))
        btn_photo = ttk.Button(photo_frame, text="📁 Browse Photo...", command=self._browse_photo)
        btn_photo.pack(side=tk.LEFT)
        self.photo_path = ""

    def _browse_photo(self):
        from tkinter import filedialog
        import os
        path = filedialog.askopenfilename(title="Select Student Photo", filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")])
        if path:
            self.photo_path = path
            self.lbl_photo.config(text=os.path.basename(path))

    def _build_parent_tab(self):
        f = self.tab_parent
        
        ttk.Label(f, text="Father / Guardian Name *:", font=FONTS["body_bold"]).grid(row=0, column=0, sticky="w", pady=4)
        self.entry_father = ttk.Entry(f, width=30)
        self.entry_father.grid(row=0, column=1, sticky="w", pady=4, padx=5)

        ttk.Label(f, text="Mother / Guardian Name:", font=FONTS["body_bold"]).grid(row=1, column=0, sticky="w", pady=4)
        self.entry_mother = ttk.Entry(f, width=30)
        self.entry_mother.grid(row=1, column=1, sticky="w", pady=4, padx=5)

        ttk.Label(f, text="Father / Guardian Phone *:", font=FONTS["body_bold"]).grid(row=2, column=0, sticky="w", pady=4)
        self.entry_parent_phone = ttk.Entry(f, width=25)
        self.entry_parent_phone.grid(row=2, column=1, sticky="w", pady=4, padx=5)

        ttk.Label(f, text="Mother Phone:", font=FONTS["body_bold"]).grid(row=3, column=0, sticky="w", pady=4)
        self.entry_mother_phone = ttk.Entry(f, width=25)
        self.entry_mother_phone.grid(row=3, column=1, sticky="w", pady=4, padx=5)

        ttk.Label(f, text="Father / Guardian Email:", font=FONTS["body_bold"]).grid(row=4, column=0, sticky="w", pady=4)
        self.entry_parent_email = ttk.Entry(f, width=30)
        self.entry_parent_email.grid(row=4, column=1, sticky="w", pady=4, padx=5)

        ttk.Label(f, text="Parent Occupation:", font=FONTS["body_bold"]).grid(row=5, column=0, sticky="w", pady=4)
        self.entry_parent_occ = ttk.Entry(f, width=25)
        self.entry_parent_occ.grid(row=5, column=1, sticky="w", pady=4, padx=5)

        ttk.Label(f, text="Emergency Contact:", font=FONTS["body_bold"]).grid(row=6, column=0, sticky="w", pady=4)
        self.entry_emergency = ttk.Entry(f, width=25)
        self.entry_emergency.grid(row=6, column=1, sticky="w", pady=4, padx=5)

        ttk.Label(f, text="Relationship with Student:", font=FONTS["body_bold"]).grid(row=7, column=0, sticky="w", pady=4)
        self.entry_relation = ttk.Entry(f, width=25)
        self.entry_relation.insert(0, "Father")
        self.entry_relation.grid(row=7, column=1, sticky="w", pady=4, padx=5)

    def _build_academic_tab(self):
        f = self.tab_academic

        ttk.Label(f, text="School Name:", font=FONTS["body_bold"]).grid(row=0, column=0, sticky="w", pady=4)
        self.entry_school_name = ttk.Entry(f, width=30)
        self.entry_school_name.grid(row=0, column=1, sticky="w", pady=4, padx=5)

        ttk.Label(f, text="Department:", font=FONTS["body_bold"]).grid(row=1, column=0, sticky="w", pady=4)
        self.entry_dept = ttk.Entry(f, width=30)
        self.entry_dept.grid(row=1, column=1, sticky="w", pady=4, padx=5)

        ttk.Label(f, text="Current Class / Year *:", font=FONTS["body_bold"]).grid(row=2, column=0, sticky="w", pady=4)
        self.entry_class = ttk.Entry(f, width=25)
        self.entry_class.insert(0, "10")
        self.entry_class.grid(row=2, column=1, sticky="w", pady=4, padx=5)

        ttk.Label(f, text="Section *:", font=FONTS["body_bold"]).grid(row=3, column=0, sticky="w", pady=4)
        self.entry_section = ttk.Entry(f, width=25)
        self.entry_section.insert(0, "A")
        self.entry_section.grid(row=3, column=1, sticky="w", pady=4, padx=5)

        ttk.Label(f, text="Study Hours Per Day (ML Feature):", font=FONTS["body_bold"]).grid(row=4, column=0, sticky="w", pady=4)
        self.entry_study_hours = ttk.Entry(f, width=25)
        self.entry_study_hours.insert(0, "3.5")
        self.entry_study_hours.grid(row=4, column=1, sticky="w", pady=4, padx=5)

    def _load_student_data(self):
        target_sid = str(self.student_id or '').strip()
        s = self.db.get_student(target_sid) if target_sid else None
        
        # Ensure Student ID field is ALWAYS populated and set to readonly
        final_sid = str(s.get('student_id', target_sid)) if s else target_sid
        if final_sid:
            self.student_id = final_sid
        
        self.entry_sid.config(state="normal")
        self.entry_sid.delete(0, tk.END)
        self.entry_sid.insert(0, final_sid)
        self.entry_sid.config(state="readonly")

        if not s:
            return

        # 1. Personal Details
        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, s.get('name') or '')

        self.entry_dob.delete(0, tk.END)
        self.entry_dob.insert(0, s.get('dob') or '')

        if s.get('gender'):
            self.combo_gender.set(s.get('gender'))
        else:
            self.combo_gender.set('')

        self.entry_phone.delete(0, tk.END)
        self.entry_phone.insert(0, s.get('phone') or '')

        self.entry_email.delete(0, tk.END)
        self.entry_email.insert(0, s.get('email') or '')

        self.entry_adm_date.delete(0, tk.END)
        self.entry_adm_date.insert(0, s.get('admission_date') or '')

        self.text_address.delete("1.0", tk.END)
        self.text_address.insert("1.0", s.get('address') or '')

        if s.get('photo_path'):
            self.photo_path = s.get('photo_path')
            import os
            self.lbl_photo.config(text=os.path.basename(self.photo_path))

        # 2. Academic Details
        self.entry_school_name.delete(0, tk.END)
        self.entry_school_name.insert(0, s.get('school_name') or s.get('previous_school') or s.get('college_name') or '')

        self.entry_dept.delete(0, tk.END)
        self.entry_dept.insert(0, s.get('department') or '')

        self.entry_class.delete(0, tk.END)
        self.entry_class.insert(0, s.get('current_class') or s.get('semester') or '')

        self.entry_section.delete(0, tk.END)
        self.entry_section.insert(0, s.get('section') or '')

        self.entry_study_hours.delete(0, tk.END)
        hrs_val = s.get('study_hours')
        if hrs_val is not None and str(hrs_val).strip() != '':
            self.entry_study_hours.insert(0, str(hrs_val))

        # 3. Parent/Guardian Details from database (checking both parents and students tables)
        p = self.db.get_parent_by_student_id(self.student_id) or {}

        father_name = s.get('father_name') or p.get('name') or s.get('parent_guardian_name') or ''
        mother_name = s.get('mother_name') or p.get('mother_name') or ''
        father_phone = s.get('father_phone') or p.get('phone') or s.get('parent_phone') or s.get('guardian_phone') or ''
        mother_phone = s.get('mother_phone') or p.get('mother_phone') or ''
        parent_email = s.get('parent_email') or p.get('email') or s.get('guardian_email') or ''
        parent_occ = s.get('parent_occupation') or p.get('occupation') or ''
        emergency = s.get('emergency_contact') or p.get('emergency_contact') or ''
        relation = s.get('relationship') or p.get('relationship') or ''

        self.entry_father.delete(0, tk.END)
        self.entry_father.insert(0, father_name)

        self.entry_mother.delete(0, tk.END)
        self.entry_mother.insert(0, mother_name)

        self.entry_parent_phone.delete(0, tk.END)
        self.entry_parent_phone.insert(0, father_phone)

        self.entry_mother_phone.delete(0, tk.END)
        self.entry_mother_phone.insert(0, mother_phone)

        self.entry_parent_email.delete(0, tk.END)
        self.entry_parent_email.insert(0, parent_email)

        self.entry_parent_occ.delete(0, tk.END)
        self.entry_parent_occ.insert(0, parent_occ)

        self.entry_emergency.delete(0, tk.END)
        self.entry_emergency.insert(0, emergency)

        self.entry_relation.delete(0, tk.END)
        self.entry_relation.insert(0, relation)

    def save_student(self):
        sid = str(self.student_id or self.entry_sid.get() or '').strip()
        name = self.entry_name.get().strip()
        dob = self.entry_dob.get().strip()
        gender = self.combo_gender.get().strip()
        school_name = self.entry_school_name.get().strip()
        department = self.entry_dept.get().strip()
        current_class = self.entry_class.get().strip()
        section = self.entry_section.get().strip()
        father_name = self.entry_father.get().strip()
        mother_name = self.entry_mother.get().strip()
        parent_phone = self.entry_parent_phone.get().strip()
        mother_phone = self.entry_mother_phone.get().strip()
        parent_email = self.entry_parent_email.get().strip()
        parent_occ = self.entry_parent_occ.get().strip()
        emergency = self.entry_emergency.get().strip()
        relation = self.entry_relation.get().strip()

        # Validation: Required fields
        if not sid or not name or not dob or not current_class or not section or not (father_name or mother_name) or not parent_phone:
            messagebox.showwarning("Validation Error", "Please fill all essential required fields:\n- Student ID & Student Name\n- Date of Birth & Gender\n- Class & Section\n- Parent/Guardian Name\n- Parent/Guardian Phone Number")
            return

        if not self.is_edit and self.db.get_student(sid):
            messagebox.showerror("Error", f"Student ID '{sid}' already exists.")
            return

        # Phone Number Format Validation
        phone = self.entry_phone.get().strip()
        if phone and not validate_phone(phone):
            messagebox.showwarning("Validation Error", "Student phone number must contain exactly 10 digits.")
            return

        if parent_phone and not validate_phone(parent_phone):
            messagebox.showwarning("Validation Error", "Parent phone number must contain exactly 10 digits.")
            return

        if mother_phone and not validate_phone(mother_phone):
            messagebox.showwarning("Validation Error", "Mother phone number must contain exactly 10 digits.")
            return

        if emergency and not validate_phone(emergency):
            messagebox.showwarning("Validation Error", "Emergency contact phone number must contain exactly 10 digits.")
            return

        # Email Format Validation
        email = self.entry_email.get().strip()
        if email and not validate_email(email):
            messagebox.showwarning("Validation Error", "Invalid student email format.")
            return

        if parent_email and not validate_email(parent_email):
            messagebox.showwarning("Validation Error", "Invalid parent email format.")
            return

        # Prevent Accidental Duplicate Records
        dup = self.db.check_duplicate_student(
            name=name,
            dob=dob,
            current_class=current_class,
            section=section,
            parent_phone=parent_phone,
            exclude_sid=sid if self.is_edit else None
        )
        if dup and not self.is_edit:
            messagebox.showerror(
                "Duplicate Student Record",
                f"A student record for '{name}' in Class {dup.get('current_class')}-{dup.get('section')} with matching DOB/Parent Phone already exists in the database (Student ID: {dup.get('student_id')})."
            )
            return

        study_hrs_str = self.entry_study_hours.get().strip()
        if not study_hrs_str:
            study_hrs_val = 0.0
        else:
            valid_hrs, hrs_msg = validate_study_hours(study_hrs_str)
            if not valid_hrs:
                messagebox.showwarning("Validation Error", hrs_msg)
                return
            try:
                study_hrs_val = float(study_hrs_str)
            except ValueError:
                study_hrs_val = 0.0

        existing_s = (self.db.get_student(sid) or {}) if self.is_edit else {}

        student_data = {
            "student_id": sid,
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
            "address": self.text_address.get("1.0", tk.END).strip(),
            "school_name": school_name,
            "department": department,
            "previous_school": school_name if school_name else existing_s.get("previous_school", ""),
            "course": existing_s.get("course", ""),
            "education_type": existing_s.get("education_type", "School"),
            "roll_number": existing_s.get("roll_number", ""),
            "academic_year": existing_s.get("academic_year", ""),
            "enrollment_number": existing_s.get("enrollment_number", ""),
            "college_name": existing_s.get("college_name", ""),
            "semester": existing_s.get("semester", ""),
            "admission_date": self.entry_adm_date.get().strip() or existing_s.get("admission_date", ""),
            "current_class": current_class,
            "section": section,
            "study_hours": study_hrs_val,
            "photo_path": self.photo_path or existing_s.get("photo_path", "")
        }

        try:
            if self.is_edit:
                ok = self.db.update_student(sid, student_data)
            else:
                ok = self.db.add_student(student_data)
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Database error occurred: {e}")
            return

        if ok:
            # If a parent record already exists for this student, update its contact details
            existing_p = self.db.get_parent_by_student_id(sid)
            if existing_p and (father_name or mother_name or parent_phone or mother_phone or parent_email):
                parent_data = {
                    "student_id": sid,
                    "name": father_name or mother_name or existing_p.get("name", "Parent/Guardian"),
                    "mother_name": mother_name or existing_p.get("mother_name", ""),
                    "phone": parent_phone or existing_p.get("phone", ""),
                    "mother_phone": mother_phone or existing_p.get("mother_phone", ""),
                    "email": parent_email or existing_p.get("email", ""),
                    "occupation": parent_occ or existing_p.get("occupation", ""),
                    "emergency_contact": emergency or existing_p.get("emergency_contact", ""),
                    "relationship": relation or existing_p.get("relationship", "Parent"),
                    "address": self.text_address.get("1.0", tk.END).strip() or existing_p.get("address", "")
                }
                self.db.update_parent(sid, parent_data)

            messagebox.showinfo("Success", f"Student record for '{name}' ({sid}) saved successfully in a single submission!")
            if self.on_save:
                self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Error", "Failed to save student record to database.")
