import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
import pickle
from PIL import Image, ImageTk
from database.db_manager import DBManager
from utils.helpers import get_current_date, get_current_time

def preprocess_face_roi(img: np.ndarray) -> np.ndarray:
    """Standardize face ROI with histogram equalization and Gaussian smoothing."""
    if img is None:
        return None
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if img.shape != (100, 100):
        img = cv2.resize(img, (100, 100))
    eq = cv2.equalizeHist(img)
    return cv2.GaussianBlur(eq, (5, 5), 0)

def compare_face_matrices(mat1: np.ndarray, mat2: np.ndarray) -> float:
    """Calculates robust normalized cross-correlation and facial feature region matching score between two face matrices."""
    p1 = preprocess_face_roi(mat1)
    p2 = preprocess_face_roi(mat2)
    if p1 is None or p2 is None:
        return 0.0
    if np.std(p1) < 1e-5 or np.std(p2) < 1e-5:
        mse = np.mean((p1.astype(float) - p2.astype(float)) ** 2)
        return 1.0 if mse < 10.0 else 0.0

    # 1. Full 1-to-1 template correlation
    res_full = float(cv2.matchTemplate(p1, p2, cv2.TM_CCOEFF_NORMED)[0][0])

    # 2. Key Facial Regions (Left Eye, Right Eye, Nose Bridge, Mouth)
    regions = [
        (15, 48, 15, 48), # Left Eye & Brow
        (15, 48, 52, 85), # Right Eye & Brow
        (38, 70, 32, 68), # Nose Bridge & Nostrils
        (65, 95, 22, 78), # Mouth & Lip Line
    ]
    reg_scores = []
    for y1, y2, x1, x2 in regions:
        r1 = p1[y1:y2, x1:x2]
        r2 = p2[y1:y2, x1:x2]
        if np.std(r1) > 1e-4 and np.std(r2) > 1e-4:
            s = float(cv2.matchTemplate(r1, r2, cv2.TM_CCOEFF_NORMED)[0][0])
            reg_scores.append(max(0.0, s))

    avg_reg = float(np.mean(reg_scores)) if reg_scores else max(0.0, res_full)
    final_score = 0.5 * max(0.0, res_full) + 0.5 * avg_reg
    return final_score

class FaceAttendanceScannerWindow(tk.Toplevel):
    """GUI Window for live facial recognition attendance scanner for Students."""
    def __init__(self, parent, db_manager: DBManager, target_role: str = "Student", student_id: str = None, on_attendance_marked=None, source: str = "Student"):
        super().__init__(parent)
        self.db = db_manager
        self.target_role = target_role  # "Student" or "Teacher"
        self.student_id = student_id
        self.on_attendance_marked = on_attendance_marked
        self.source = source or "Student"
        self.cap = None
        self.is_running = False
        self.is_verified = False

        self.title(f"Face Recognition Attendance Scanner ({self.target_role})")
        self.geometry("760x720")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        if hasattr(cv2, 'CascadeClassifier') and hasattr(cv2, 'data') and hasattr(cv2.data, 'haarcascades'):
            try:
                self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            except Exception:
                self.face_cascade = None
        else:
            self.face_cascade = None
        self.registered_faces = [] # list of (user_id, user_name, roi_matrix)
        self._load_registered_faces()

        self._build_ui()
        self._start_camera()

    def _load_registered_faces(self):
        """Load and deserialize face encodings from DB according to target_role."""
        records = self.db.get_all_face_encodings()
        self.registered_faces = []
        
        target_ids = set()
        if self.student_id:
            target_ids.add(str(self.student_id).strip().lower())
            st = self.db.get_student(self.student_id)
            if st:
                if st.get('student_id'):
                    target_ids.add(str(st.get('student_id')).strip().lower())
                if st.get('enrollment_number'):
                    target_ids.add(str(st.get('enrollment_number')).strip().lower())

        for r in records:
            user_id = r['student_id']
            if target_ids and str(user_id).strip().lower() not in target_ids:
                continue
            try:
                roi_mat = pickle.loads(r['encoding_blob'])
                if not isinstance(roi_mat, np.ndarray):
                    continue

                if self.target_role == "Teacher":
                    teacher = self.db.get_teacher(user_id)
                    if teacher:
                        name = teacher['name']
                        self.registered_faces.append((user_id, name, roi_mat))
                else:
                    student = self.db.get_student(user_id)
                    if student:
                        name = student['name']
                        self.registered_faces.append((user_id, name, roi_mat))
            except Exception as e:
                print(f"Error loading face encoding for {user_id}:", e)

    def _build_ui(self):
        header = ttk.Frame(self, padding=10)
        header.pack(fill=tk.X)
        
        lbl_info_frame = ttk.Frame(header)
        lbl_info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(lbl_info_frame, text=f"📷 Live Face Verification ({self.target_role})", font=("Segoe UI", 14, "bold")).pack(anchor=tk.W)
        reg_count = len(self.registered_faces)
        ttk.Label(lbl_info_frame, text=f"Registered {self.target_role}s in DB: {reg_count} | Automatic verification active.", font=("Segoe UI", 9)).pack(anchor=tk.W)

        video_frame = ttk.Frame(self, padding=5, relief="solid")
        video_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        self.canvas_label = ttk.Label(video_frame, text="Initializing Camera Stream...", anchor=tk.CENTER)
        self.canvas_label.pack(fill=tk.BOTH, expand=True)

        # Verified Details Box (Below Camera Stream)
        det_title = " 👤 Verified Student Details " if self.target_role == "Student" else " 👤 Verified Teacher Details "
        self.details_box = ttk.LabelFrame(self, text=det_title, padding=10)
        self.details_box.pack(fill=tk.X, padx=15, pady=5)

        self.lbl_det_1 = ttk.Label(self.details_box, text="Student Name: --", font=("Segoe UI", 10, "bold"))
        self.lbl_det_1.grid(row=0, column=0, sticky=tk.W, padx=12, pady=3)

        self.lbl_det_2 = ttk.Label(self.details_box, text="Student ID: --", font=("Segoe UI", 10))
        self.lbl_det_2.grid(row=0, column=1, sticky=tk.W, padx=12, pady=3)

        self.lbl_det_3 = ttk.Label(self.details_box, text="Class: --", font=("Segoe UI", 10))
        self.lbl_det_3.grid(row=1, column=0, sticky=tk.W, padx=12, pady=3)

        self.lbl_det_4 = ttk.Label(self.details_box, text="Section: --", font=("Segoe UI", 10))
        self.lbl_det_4.grid(row=1, column=1, sticky=tk.W, padx=12, pady=3)

        self.lbl_det_5 = ttk.Label(self.details_box, text="Status: --", font=("Segoe UI", 10, "bold"))
        self.lbl_det_5.grid(row=2, column=0, sticky=tk.W, padx=12, pady=3)

        self.is_paused_preview = False
        self.captured_frame_gray = None
        self.current_verified_uid = None
        self._update_details(None)

        # Controls Frame for attendance capture & save
        ctrl_frame = ttk.Frame(self, padding=10)
        ctrl_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.btn_capture = ttk.Button(ctrl_frame, text="📸 Capture Face", command=self.snap_face)
        self.btn_capture.pack(side=tk.LEFT, padx=5)

        self.btn_save_attendance = ttk.Button(ctrl_frame, text="💾 Save Face & Mark Attendance", style="Primary.TButton", command=self.attempt_capture)
        self.btn_save_attendance.pack(side=tk.LEFT, padx=5)

        self.btn_save_face = ttk.Button(ctrl_frame, text="💾 Save Face", command=self.attempt_capture)
        self.btn_save_face.pack(side=tk.LEFT, padx=5)

        self.btn_retake = ttk.Button(ctrl_frame, text="🔄 Retake", command=self.retake_face, state=tk.DISABLED)
        self.btn_retake.pack(side=tk.LEFT, padx=5)

        self.btn_cancel = ttk.Button(ctrl_frame, text="✖ Cancel", command=self.on_close)
        self.btn_cancel.pack(side=tk.RIGHT, padx=5)

        self.status_bar = tk.Label(self, text="System Ready - Scanning for face...", font=("Segoe UI", 11, "bold"), bg="#1a202c", fg="#63b3ed")
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, ipady=5)

    def _update_details(self, uid: str = None):
        """Fetch and display stored database details for the verified student or teacher without Time."""
        self.current_verified_uid = uid

        if self.target_role == "Teacher":
            if not uid:
                self.lbl_det_1.config(text="Teacher Name: --")
                self.lbl_det_2.config(text="Teacher ID: --")
                self.lbl_det_3.config(text="Department: --")
                self.lbl_det_4.config(text="Designation: --")
                self.lbl_det_5.config(text="Status: Absent")
                return

            teacher = self.db.get_teacher(uid)
            if teacher:
                self.lbl_det_1.config(text=f"Teacher Name: {teacher.get('name', 'N/A')}")
                self.lbl_det_2.config(text=f"Teacher ID: {teacher.get('teacher_id', uid)}")
                self.lbl_det_3.config(text=f"Department: {teacher.get('department', 'N/A')}")
                self.lbl_det_4.config(text=f"Designation: {teacher.get('designation', 'N/A')}")
                self.lbl_det_5.config(text="Status: Present")
            else:
                self._update_details(None)
            return

        # STUDENT ROLE
        category = "School"
        if uid:
            student = self.db.get_student(uid)
            if student:
                category = student.get('education_type', 'School')

        if not uid:
            if category == "School":
                self.lbl_det_1.config(text="Student Name: --")
                self.lbl_det_2.config(text="Student ID: --")
                self.lbl_det_3.config(text="Class: --")
                self.lbl_det_4.config(text="Section: --")
                self.lbl_det_5.config(text="Status: Absent")
            else:
                self.lbl_det_1.config(text="Student Name: --")
                self.lbl_det_2.config(text="Student ID / Enrollment Number: --")
                self.lbl_det_3.config(text="Course: --")
                self.lbl_det_4.config(text="Semester / Year: --")
                self.lbl_det_5.config(text="Status: Absent")
            return

        student = self.db.get_student(uid)
        if student:
            s_name = student.get('name', 'N/A')
            s_id = student.get('student_id', uid)
            enr_no = student.get('enrollment_number') or s_id
            s_class = student.get('current_class') or 'N/A'
            s_sec = student.get('section') or 'N/A'
            s_course = student.get('course') or student.get('current_class') or 'N/A'
            
            sem = student.get('semester') or ''
            yr = student.get('academic_year') or student.get('year') or ''
            sem_yr_str = f"{sem} {yr}".strip() if (sem or yr) else "N/A"

            if category == "School":
                self.lbl_det_1.config(text=f"Student Name: {s_name}")
                self.lbl_det_2.config(text=f"Student ID: {s_id}")
                self.lbl_det_3.config(text=f"Class: {s_class}")
                self.lbl_det_4.config(text=f"Section: {s_sec}")
                self.lbl_det_5.config(text="Status: Present")
            else:
                self.lbl_det_1.config(text=f"Student Name: {s_name}")
                self.lbl_det_2.config(text=f"Student ID / Enrollment Number: {enr_no}")
                self.lbl_det_3.config(text=f"Course: {s_course}")
                self.lbl_det_4.config(text=f"Semester / Year: {sem_yr_str}")
                self.lbl_det_5.config(text="Status: Present")
        else:
            self._update_details(None)

    def _start_camera(self):
        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)

            if not self.cap.isOpened():
                err_msg = "Camera could not be opened. Please check camera permission or availability."
                self.canvas_label.config(text=err_msg)
                self.status_bar.config(text=err_msg, bg="#742a2a", fg="#fff")
                messagebox.showerror("Camera Error", err_msg)
                return

            self.is_running = True
            self.is_paused_preview = False
            self._update_frame()
        except Exception as e:
            err_msg = "Camera could not be opened. Please check camera permission or availability."
            self.canvas_label.config(text=err_msg)
            self.status_bar.config(text=err_msg, bg="#742a2a", fg="#fff")
            messagebox.showerror("Camera Error", err_msg)

    def _get_mismatch_message(self) -> str:
        """Returns dynamic mismatch error message with the currently logged-in student's or teacher's name."""
        if self.target_role == "Student" and self.student_id:
            st = self.db.get_student(self.student_id)
            sname = st.get('name') if st else "the student"
            return f"You are not {sname}! This face does not match {sname}'s registered face. Attendance cannot be marked."
        elif self.target_role == "Teacher" and hasattr(self, 'teacher_id') and self.teacher_id:
            tch = self.db.get_teacher(self.teacher_id)
            tname = tch.get('name') if tch else "the teacher"
            return f"You are not {tname}! This face does not match {tname}'s registered face. Attendance cannot be marked."
        return "Face verification failed! This face does not match the registered face. Attendance cannot be marked."

    def _match_face(self, roi_resized: np.ndarray) -> tuple[str, str, float]:
        """Matches input face ROI matrix against registered face templates using normalized template cross-correlation."""
        if not self.registered_faces:
            return None, None, 0.0

        best_uid = None
        best_name = None
        max_score = -1.0

        for uid, name, stored_mat in self.registered_faces:
            try:
                score = compare_face_matrices(roi_resized, stored_mat)
                if score > max_score:
                    max_score = score
                    best_uid = uid
                    best_name = name
            except Exception as e:
                print("Error matching face:", e)

        # If student_id is set (Logged in student), we strictly require that the best match is that student
        if self.student_id:
            target_ids = {str(self.student_id).strip().lower()}
            st = self.db.get_student(self.student_id)
            if st:
                if st.get('student_id'):
                    target_ids.add(str(st.get('student_id')).strip().lower())
                if st.get('enrollment_number'):
                    target_ids.add(str(st.get('enrollment_number')).strip().lower())
            if best_uid is None or str(best_uid).strip().lower() not in target_ids:
                return None, None, max_score

        # Verified authentic match threshold (> 0.45 correlation)
        if max_score >= 0.45:
            return best_uid, best_name, max_score
        return None, None, max_score

    def _process_successful_verification(self, uid: str, name: str):
        """Mark attendance in database, update UI, and notify callback."""
        if self.is_verified:
            return
        self.is_verified = True
        self._update_details(uid)

        from utils.helpers import get_current_date, get_current_time
        today = get_current_date()
        now_t = get_current_time()

        if self.target_role == "Teacher":
            ok, msg = self.db.mark_teacher_attendance(uid, today, now_t, "Present")
            self.db.record_teacher_login(uid, start_time_override=now_t)
        else:
            source_val = self.source or ('Student' if self.student_id else 'Teacher')
            ok, msg = self.db.mark_attendance(uid, today, now_t, "Present", source=source_val)

        if ok:
            success_msg = f"Your attendance is marked successfully for {today}."
            self.status_bar.config(text=success_msg, bg="#22543d", fg="#9ae6b4")
            if self.on_attendance_marked:
                try:
                    self.on_attendance_marked()
                except Exception as e:
                    print("Error calling on_attendance_marked:", e)
            messagebox.showinfo("Success", "Your attendance is marked successfully.")
            self.on_close()
        else:
            self.is_verified = False
            if "marked by student" in msg.lower():
                display_msg = "Attendance is already marked by student."
            elif "marked by teacher" in msg.lower():
                display_msg = "Attendance is already marked by teacher."
            elif "already marked" in msg.lower():
                display_msg = "Your attendance is already marked."
            else:
                display_msg = msg
            self.status_bar.config(text=display_msg, bg="#742a2a", fg="#fff")
            messagebox.showwarning("Notice", display_msg)
            self.on_close()

    def snap_face(self):
        """Freeze current frame on camera and verify face."""
        if self.cap is None or not self.cap.isOpened():
            messagebox.showerror("Error", "Camera is not available.")
            return

        ret, frame = self.cap.read()
        if not ret or frame is None:
            messagebox.showerror("Error", "Failed to capture frame from camera.")
            return

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.face_cascade is not None:
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80))
        else:
            faces = []

        if len(faces) == 0:
            self.status_bar.config(text="No face detected. Please look at the camera.", bg="#742a2a", fg="#fff")
            messagebox.showwarning("Notice", "No face detected. Please look at the camera.")
            return
        elif len(faces) > 1:
            self.status_bar.config(text="Multiple faces detected. Please make sure only one face is visible.", bg="#742a2a", fg="#fff")
            messagebox.showwarning("Notice", "Multiple faces detected. Please make sure only one face is visible.")
            return

        (x, y, w, h) = faces[0]
        roi_gray = gray[y:y+h, x:x+w]
        roi_resized = cv2.resize(roi_gray, (100, 100))
        matched_uid, matched_name, score = self._match_face(roi_resized)

        self.is_paused_preview = True
        self.btn_capture.config(state=tk.DISABLED)
        self.btn_retake.config(state=tk.NORMAL)
        self.captured_frame_gray = roi_resized

        if matched_uid is not None:
            self._update_details(matched_uid)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, f"Verified: {matched_name}", (x, max(20, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            self.status_bar.config(text=f"Face Verified ({matched_name})! Click '💾 Save Face' to mark attendance.", bg="#1e3a8a", fg="#93c5fd")
        else:
            self._update_details(None)
            target_name = "the student"
            if self.target_role == "Student" and self.student_id:
                st = self.db.get_student(self.student_id)
                if st:
                    target_name = st.get('name', 'the student')
            elif self.target_role == "Teacher" and hasattr(self, 'teacher_id') and self.teacher_id:
                tch = self.db.get_teacher(self.teacher_id)
                if tch:
                    target_name = tch.get('name', 'the teacher')

            # Check if this face matches another registered user
            other_name = None
            try:
                all_encs = self.db.get_all_face_encodings()
                for r in all_encs:
                    uid_other = r.get('student_id')
                    if uid_other and str(uid_other).strip().lower() != str(self.student_id or '').strip().lower():
                        stored_m = pickle.loads(r['encoding_blob'])
                        if isinstance(stored_m, np.ndarray):
                            s = compare_face_matrices(roi_resized, stored_m)
                            if s >= 0.50:
                                ost = self.db.get_student(uid_other)
                                other_name = ost.get('name') if ost else uid_other
                                break
            except Exception:
                pass

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            if other_name:
                banner_txt = f"You are not {target_name}! ({other_name})"
                cv2.putText(frame, banner_txt, (x, max(20, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
                self.status_bar.config(text=f"❌ You are not {target_name}! (Detected {other_name})", bg="#742a2a", fg="#fff")
            else:
                banner_txt = f"You are not {target_name}!"
                cv2.putText(frame, banner_txt, (x, max(20, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                mismatch_msg = self._get_mismatch_message()
                self.status_bar.config(text=f"❌ {mismatch_msg}", bg="#742a2a", fg="#fff")

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame)
        img = img.resize((680, 440), Image.Resampling.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=img)
        self.canvas_label.imgtk = imgtk
        self.canvas_label.configure(image=imgtk)

    def retake_face(self):
        """Resume live camera feed."""
        self.is_paused_preview = False
        self.captured_frame_gray = None
        self.btn_capture.config(state=tk.NORMAL)
        self.btn_retake.config(state=tk.DISABLED)
        self.status_bar.config(text="System Ready - Scanning for face...", bg="#1a202c", fg="#63b3ed")
        self._update_details(None)
        self._update_frame()

    def _update_frame(self):
        if not self.is_running or self.is_paused_preview or self.cap is None or not self.cap.isOpened() or self.is_verified:
            return

        ret, frame = self.cap.read()
        if not ret or frame is None:
            self.after(30, self._update_frame)
            return

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.face_cascade is not None:
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80))
        else:
            faces = []

        if len(faces) == 0:
            self.status_bar.config(text="No face detected. Please look at the camera.", bg="#1a202c", fg="#63b3ed")
            self._update_details(None)
        elif len(faces) > 1:
            self.status_bar.config(text="Multiple faces detected. Please make sure only one face is visible.", bg="#742a2a", fg="#fff")
            self._update_details(None)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
        else:
            (x, y, w, h) = faces[0]
            roi_gray = gray[y:y+h, x:x+w]
            roi_resized = cv2.resize(roi_gray, (100, 100))
            matched_uid, matched_name, score = self._match_face(roi_resized)

            if matched_uid is not None:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, f"Face Recognized: {matched_name}", (x, max(20, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                self.status_bar.config(text=f"Face matched: {matched_name}. Click '💾 Save Face' to mark attendance.", bg="#22543d", fg="#9ae6b4")
                self._update_details(matched_uid)
            else:
                self._update_details(None)
                target_name = "the student"
                if self.target_role == "Student" and self.student_id:
                    st = self.db.get_student(self.student_id)
                    if st:
                        target_name = st.get('name', 'the student')
                elif self.target_role == "Teacher" and hasattr(self, 'teacher_id') and self.teacher_id:
                    tch = self.db.get_teacher(self.teacher_id)
                    if tch:
                        target_name = tch.get('name', 'the teacher')

                # Check if this face matches another registered user
                other_name = None
                try:
                    all_encs = self.db.get_all_face_encodings()
                    for r in all_encs:
                        uid_other = r.get('student_id')
                        if uid_other and str(uid_other).strip().lower() != str(self.student_id or '').strip().lower():
                            stored_m = pickle.loads(r['encoding_blob'])
                            if isinstance(stored_m, np.ndarray):
                                s = compare_face_matrices(roi_resized, stored_m)
                                if s >= 0.50:
                                    ost = self.db.get_student(uid_other)
                                    other_name = ost.get('name') if ost else uid_other
                                    break
                except Exception:
                    pass

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                if other_name:
                    banner_txt = f"You are not {target_name} ({other_name})"
                    cv2.putText(frame, banner_txt, (x, max(20, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
                    self.status_bar.config(text=f"❌ You are not {target_name}! (Detected {other_name})", bg="#742a2a", fg="#fff")
                else:
                    banner_txt = f"You are not {target_name}!"
                    cv2.putText(frame, banner_txt, (x, max(20, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    self.status_bar.config(text=f"❌ You are not {target_name}! This face does not match {target_name}.", bg="#742a2a", fg="#fff")

        # Convert to Image for Tkinter
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame)
        img = img.resize((680, 440), Image.Resampling.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=img)
        self.canvas_label.imgtk = imgtk
        self.canvas_label.configure(image=imgtk)

        if not self.is_verified:
            self.after(30, self._update_frame)

    def attempt_capture(self):
        """Verify face and save attendance to database."""
        mismatch_msg = self._get_mismatch_message()

        if self.captured_frame_gray is not None:
            roi_resized = self.captured_frame_gray
            uid, name, score = self._match_face(roi_resized)
            if uid is not None:
                self._process_successful_verification(uid, name)
                return
            else:
                self._update_details(None)
                self.status_bar.config(text=mismatch_msg, bg="#742a2a", fg="#fff")
                messagebox.showerror("Verification Error", mismatch_msg)
                return

        if self.cap is None or not self.cap.isOpened():
            messagebox.showerror("Error", "Camera is not available.")
            return

        ret, frame = self.cap.read()
        if not ret or frame is None:
            messagebox.showerror("Error", "Failed to capture frame from camera.")
            return

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.face_cascade is not None:
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80))
        else:
            faces = []

        if len(faces) == 0:
            self.status_bar.config(text="No face detected. Please look at the camera.", bg="#742a2a", fg="#fff")
            messagebox.showwarning("Notice", "No face detected. Please look at the camera.")
            return
        elif len(faces) > 1:
            self.status_bar.config(text="Multiple faces detected. Please make sure only one face is visible.", bg="#742a2a", fg="#fff")
            messagebox.showwarning("Notice", "Multiple faces detected. Please make sure only one face is visible.")
            return

        # Exactly one face
        (x, y, w, h) = faces[0]
        roi_gray = gray[y:y+h, x:x+w]
        roi_resized = cv2.resize(roi_gray, (100, 100))

        uid, name, score = self._match_face(roi_resized)

        if uid is not None:
            self._process_successful_verification(uid, name)
        else:
            self._update_details(None)
            self.status_bar.config(text=mismatch_msg, bg="#742a2a", fg="#fff")
            messagebox.showerror("Verification Error", mismatch_msg)

    def on_close(self):
        self.is_running = False
        self.is_paused_preview = False
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        cv2.destroyAllWindows()
        try:
            self.destroy()
        except Exception:
            pass


class TeacherFaceAttendanceWindow(tk.Toplevel):
    """Dedicated Teacher Face Attendance Scanner Window with automatic camera face verification."""
    def __init__(self, parent, db_manager: DBManager, teacher_id: str = None, on_attendance_marked=None, custom_db_handling=False):
        super().__init__(parent)
        self.db = db_manager
        self.teacher_id = teacher_id
        self.on_attendance_marked = on_attendance_marked
        self.custom_db_handling = custom_db_handling
        self.cap = None
        self.is_running = False
        self.is_verified = False

        self.title("TEACHER FACE ATTENDANCE SCANNER")
        self.geometry("760x720")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        if hasattr(cv2, 'CascadeClassifier') and hasattr(cv2, 'data') and hasattr(cv2.data, 'haarcascades'):
            try:
                self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            except Exception:
                self.face_cascade = None
        else:
            self.face_cascade = None
        self.registered_faces = []
        self._load_registered_faces()

        self._build_ui()
        self._start_camera()

    def _load_registered_faces(self):
        """Load registered teacher face encodings."""
        records = self.db.get_all_face_encodings()
        self.registered_faces = []
        for r in records:
            user_id = r['student_id']
            teacher = self.db.get_teacher(user_id)
            if teacher:
                try:
                    roi_mat = pickle.loads(r['encoding_blob'])
                    if isinstance(roi_mat, np.ndarray):
                        self.registered_faces.append((user_id, teacher['name'], roi_mat))
                except Exception as e:
                    print("Error loading teacher face:", e)

    def _build_ui(self):
        # Header Section
        hdr = ttk.Frame(self, padding=12)
        hdr.pack(fill=tk.X)
        ttk.Label(hdr, text="📷 TEACHER FACE ATTENDANCE SCANNER", font=("Segoe UI", 14, "bold")).pack(anchor=tk.W)
        ttk.Label(hdr, text="Position your face in front of the camera. System will verify identity automatically.", font=("Segoe UI", 9)).pack(anchor=tk.W)

        # Video Preview Canvas Container
        video_box = ttk.LabelFrame(self, text=" LIVE CAMERA PREVIEW ", padding=8)
        video_box.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        self.canvas_label = ttk.Label(video_box, text="Initializing Camera Stream...", anchor=tk.CENTER, font=("Segoe UI", 11))
        self.canvas_label.pack(fill=tk.BOTH, expand=True)

        # Verified Teacher Details Box (Below Camera Stream)
        self.details_box = ttk.LabelFrame(self, text=" 👤 Verified Teacher Details ", padding=10)
        self.details_box.pack(fill=tk.X, padx=15, pady=5)

        self.lbl_det_name = ttk.Label(self.details_box, text="Teacher Name: --", font=("Segoe UI", 10, "bold"))
        self.lbl_det_name.grid(row=0, column=0, sticky=tk.W, padx=12, pady=3)

        self.lbl_det_id = ttk.Label(self.details_box, text="Teacher ID: --", font=("Segoe UI", 10))
        self.lbl_det_id.grid(row=0, column=1, sticky=tk.W, padx=12, pady=3)

        self.lbl_det_number = ttk.Label(self.details_box, text="Department: --", font=("Segoe UI", 10))
        self.lbl_det_number.grid(row=1, column=0, sticky=tk.W, padx=12, pady=3)

        self.lbl_det_type = ttk.Label(self.details_box, text="Designation: --", font=("Segoe UI", 10))
        self.lbl_det_type.grid(row=1, column=1, sticky=tk.W, padx=12, pady=3)

        self.lbl_det_class = ttk.Label(self.details_box, text="Phone: --", font=("Segoe UI", 10))
        self.lbl_det_class.grid(row=2, column=0, sticky=tk.W, padx=12, pady=3)

        self.lbl_det_sem_year = ttk.Label(self.details_box, text="Email: --", font=("Segoe UI", 10))
        self.lbl_det_sem_year.grid(row=2, column=1, sticky=tk.W, padx=12, pady=3)

        self._update_details(None)

        # Status Display Label
        self.status_bar = tk.Label(
            self,
            text="Status: Position face in front of camera...",
            font=("Segoe UI", 11, "bold"),
            bg="#1a202c",
            fg="#63b3ed",
            pady=10
        )
        self.status_bar.pack(fill=tk.X)

        # Action Buttons Frame
        btn_frame = ttk.Frame(self, padding=10)
        btn_frame.pack(fill=tk.X)

        btn_cancel = ttk.Button(btn_frame, text="✖ Cancel / Close Scanner", command=self.on_close)
        btn_cancel.pack(side=tk.RIGHT, padx=10, ipady=4)

    def _update_details(self, uid: str = None):
        """Fetch and display stored database details for verified teacher."""
        if not uid:
            self.lbl_det_name.config(text="Teacher Name: --")
            self.lbl_det_id.config(text="Teacher ID: --")
            self.lbl_det_number.config(text="Department: --")
            self.lbl_det_type.config(text="Designation: --")
            self.lbl_det_class.config(text="Phone: --")
            self.lbl_det_sem_year.config(text="Email: --")
            return

        teacher = self.db.get_teacher(uid)
        if teacher:
            t_name = teacher.get('name', 'N/A')
            t_id = teacher.get('teacher_id', uid)
            t_dept = teacher.get('department', 'N/A')
            t_desig = teacher.get('designation', 'N/A')
            t_phone = teacher.get('phone', 'N/A')
            t_email = teacher.get('email', 'N/A')

            self.lbl_det_name.config(text=f"Teacher Name: {t_name}")
            self.lbl_det_id.config(text=f"Teacher ID: {t_id}")
            self.lbl_det_number.config(text=f"Department: {t_dept}")
            self.lbl_det_type.config(text=f"Designation: {t_desig}")
            self.lbl_det_class.config(text=f"Phone: {t_phone}")
            self.lbl_det_sem_year.config(text=f"Email: {t_email}")
        else:
            self._update_details(None)

    def _start_camera(self):
        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)

            if not self.cap.isOpened():
                err_msg = "Camera could not be opened. Please check camera permission or availability."
                self.canvas_label.config(text=err_msg)
                self.status_bar.config(text=err_msg, bg="#742a2a", fg="#fff")
                messagebox.showerror("Camera Error", err_msg)
                return

            self.is_running = True
            self._update_frame()
        except Exception as e:
            err_msg = "Camera could not be opened. Please check camera permission or availability."
            self.canvas_label.config(text=err_msg)
            self.status_bar.config(text=err_msg, bg="#742a2a", fg="#fff")
            messagebox.showerror("Camera Error", err_msg)

    def _match_face(self, roi_resized: np.ndarray) -> tuple[str, str, float]:
        """Matches face ROI matrix against registered teacher templates using normalized correlation."""
        if not self.registered_faces:
            return None, None, 0.0

        best_uid = None
        best_name = None
        max_score = -1.0

        for uid, name, stored_mat in self.registered_faces:
            try:
                score = compare_face_matrices(roi_resized, stored_mat)
                if score > max_score:
                    max_score = score
                    best_uid = uid
                    best_name = name
            except Exception as e:
                print("Error matching teacher face:", e)

        if max_score >= 0.60:
            return best_uid, best_name, max_score
        return None, None, max_score

    def _update_frame(self):
        if not self.is_running or self.cap is None or not self.cap.isOpened() or self.is_verified:
            return

        ret, frame = self.cap.read()
        if not ret or frame is None:
            self.after(30, self._update_frame)
            return

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.face_cascade is not None:
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80))
        else:
            faces = []

        if len(faces) == 0:
            self.status_bar.config(text="No face detected. Please look at the camera.", bg="#1a202c", fg="#63b3ed")
            self._update_details(None)
        elif len(faces) > 1:
            self.status_bar.config(text="Multiple faces detected. Please make sure only one face is visible.", bg="#742a2a", fg="#fff")
            self._update_details(None)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
        else:
            (x, y, w, h) = faces[0]
            roi_gray = gray[y:y+h, x:x+w]
            roi_resized = cv2.resize(roi_gray, (100, 100))

            matched_uid, matched_name, score = self._match_face(roi_resized)

            if matched_uid is None or (self.teacher_id and matched_uid != self.teacher_id):
                # Face NOT recognized or mismatched teacher
                self._update_details(None)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(frame, "Verification Failed", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                self.status_bar.config(text="Face verification failed.", bg="#742a2a", fg="#fff")
            else:
                # Face successfully verified & matched!
                target_id = matched_uid
                target_name = matched_name
                self.is_verified = True
                self._update_details(target_id)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, f"Face Recognized: {target_name} ({target_id})", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                today = get_current_date()
                from datetime import datetime
                now_t = datetime.now().strftime("%I:%M:%S %p")

                if not self.custom_db_handling:
                    ok, msg = self.db.mark_teacher_attendance(target_id, today, now_t, "Present")
                    self.db.record_teacher_login(target_id, start_time_override=now_t)

                self.status_bar.config(text=f"Face Recognized ✓ Attendance Marked & Work Session Started ({target_name})", bg="#22543d", fg="#9ae6b4")
                if self.on_attendance_marked:
                    try:
                        self.on_attendance_marked(now_t)
                    except TypeError:
                        self.on_attendance_marked()

                # Automatically release camera and close scanner after 1.2 seconds
                self.after(1200, self.on_close)

        # Convert to Image for Tkinter
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame)
        img = img.resize((680, 420), Image.Resampling.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=img)

        self.canvas_label.imgtk = imgtk
        self.canvas_label.configure(image=imgtk)

        if not self.is_verified:
            self.after(30, self._update_frame)

    def on_close(self):
        self.is_running = False
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        cv2.destroyAllWindows()
        try:
            self.destroy()
        except Exception:
            pass
        cv2.destroyAllWindows()
        try:
            self.destroy()
        except Exception:
            pass
