import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
import pickle
from PIL import Image, ImageTk
from database.db_manager import DBManager
from utils.helpers import get_current_date, get_current_time

class FaceAttendanceScannerWindow(tk.Toplevel):
    """GUI Window for live facial recognition attendance scanner for Students."""
    def __init__(self, parent, db_manager: DBManager, target_role: str = "Student", on_attendance_marked=None):
        super().__init__(parent)
        self.db = db_manager
        self.target_role = target_role  # "Student" or "Teacher"
        self.on_attendance_marked = on_attendance_marked
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
        for r in records:
            user_id = r['student_id']
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

        if self.target_role == "Student":
            mode_frame = ttk.Frame(header)
            mode_frame.pack(side=tk.RIGHT, padx=5)
            ttk.Label(mode_frame, text="Mode:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
            self.combo_category = ttk.Combobox(mode_frame, values=["School", "College"], state="readonly", width=10)
            self.combo_category.set("School")
            self.combo_category.pack(side=tk.LEFT)
            self.combo_category.bind("<<ComboboxSelected>>", lambda e: self._update_details(getattr(self, 'current_verified_uid', None)))

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

        self.current_verified_uid = None
        self._update_details(None)

        self.status_bar = tk.Label(self, text="System Ready - Scanning...", font=("Segoe UI", 11, "bold"), bg="#1a202c", fg="#63b3ed")
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, ipady=4)

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
        category = self.combo_category.get() if hasattr(self, 'combo_category') else "School"

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
            self._update_frame()
        except Exception as e:
            err_msg = "Camera could not be opened. Please check camera permission or availability."
            self.canvas_label.config(text=err_msg)
            self.status_bar.config(text=err_msg, bg="#742a2a", fg="#fff")
            messagebox.showerror("Camera Error", err_msg)

    def _match_face(self, roi_resized: np.ndarray) -> tuple[str, str, float]:
        """Matches input face ROI matrix against registered face templates."""
        if not self.registered_faces:
            return None, None, 999999.0

        best_uid = None
        best_name = None
        min_mse = 999999.0

        for uid, name, stored_mat in self.registered_faces:
            if stored_mat.shape != roi_resized.shape:
                stored_mat = cv2.resize(stored_mat, roi_resized.shape[::-1])
            
            mse = np.mean((roi_resized.astype("float") - stored_mat.astype("float")) ** 2)
            if mse < min_mse:
                min_mse = mse
                best_uid = uid
                best_name = name

        if min_mse < 4500.0:
            return best_uid, best_name, min_mse
        return None, None, min_mse

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
            self.status_bar.config(text="Status: Position face in front of camera...", bg="#1a202c", fg="#63b3ed")
            self._update_details(None)
        elif len(faces) > 1:
            self.status_bar.config(text="Warning: Only one person should be in front of the camera.", bg="#742a2a", fg="#fff")
            self._update_details(None)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
        else:
            (x, y, w, h) = faces[0]
            roi_gray = gray[y:y+h, x:x+w]
            roi_resized = cv2.resize(roi_gray, (100, 100))

            uid, name, score = self._match_face(roi_resized)

            if uid is not None:
                self.is_verified = True
                self._update_details(uid)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, f"Face Recognized: {name} ({uid})", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                today = get_current_date()
                now_t = get_current_time()

                if self.target_role == "Teacher":
                    ok, msg = self.db.mark_teacher_attendance(uid, today, now_t, "Present")
                    self.db.record_teacher_login(uid, start_time_override=now_t)
                else:
                    ok, msg = self.db.mark_attendance(uid, today, now_t, "Present")
                
                self.status_bar.config(text=f"Face Recognized ✓ Attendance Marked Successfully for {name} ({uid})", bg="#22543d", fg="#9ae6b4")
                if self.on_attendance_marked:
                    self.on_attendance_marked()

                # Automatically release camera and close scanner after 1.2 seconds
                self.after(1200, self.on_close)
            else:
                self._update_details(None)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 165, 255), 2)
                cv2.putText(frame, "Face not recognized", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
                self.status_bar.config(text="Face not recognized. Please try again.", bg="#744210", fg="#fefcbf")

        # Convert to Image for Tkinter
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame)
        img = img.resize((680, 440), Image.Resampling.LANCZOS)
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


class TeacherFaceAttendanceWindow(tk.Toplevel):
    """Dedicated Teacher Face Attendance Scanner Window with automatic camera face verification."""
    def __init__(self, parent, db_manager: DBManager, teacher_id: str = None, on_attendance_marked=None):
        super().__init__(parent)
        self.db = db_manager
        self.teacher_id = teacher_id
        self.on_attendance_marked = on_attendance_marked
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
            padding=10
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
        """Matches face ROI matrix against registered teacher templates."""
        if not self.registered_faces:
            return None, None, 999999.0

        best_uid = None
        best_name = None
        min_mse = 999999.0

        for uid, name, stored_mat in self.registered_faces:
            if stored_mat.shape != roi_resized.shape:
                stored_mat = cv2.resize(stored_mat, roi_resized.shape[::-1])

            mse = np.mean((roi_resized.astype("float") - stored_mat.astype("float")) ** 2)
            if mse < min_mse:
                min_mse = mse
                best_uid = uid
                best_name = name

        if min_mse < 4500.0:
            return best_uid, best_name, min_mse
        return None, None, min_mse

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
            self.status_bar.config(text="Status: Please position face in front of camera...", bg="#1a202c", fg="#63b3ed")
            self._update_details(None)
        elif len(faces) > 1:
            self.status_bar.config(text="Warning: Only one person should be in front of camera.", bg="#742a2a", fg="#fff")
            self._update_details(None)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
        else:
            (x, y, w, h) = faces[0]
            roi_gray = gray[y:y+h, x:x+w]
            roi_resized = cv2.resize(roi_gray, (100, 100))

            matched_uid, matched_name, score = self._match_face(roi_resized)

            if matched_uid is None:
                # Face NOT recognized
                self._update_details(None)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 165, 255), 2)
                cv2.putText(frame, "Face not recognized", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
                self.status_bar.config(text="Face not recognized. Please try again.", bg="#744210", fg="#fefcbf")
            elif self.teacher_id and matched_uid != self.teacher_id:
                # Face mismatch for logged-in teacher context
                self._update_details(None)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(frame, "Face not recognized", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                self.status_bar.config(text=f"Face not recognized: Recognized as {matched_name} ({matched_uid}), not logged-in teacher.", bg="#742a2a", fg="#fff")
            else:
                # Face successfully verified & matched!
                target_id = matched_uid
                target_name = matched_name
                self.is_verified = True
                self._update_details(target_id)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, f"Face Recognized: {target_name} ({target_id})", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                today = get_current_date()
                now_t = get_current_time()

                ok, msg = self.db.mark_teacher_attendance(target_id, today, now_t, "Present")
                self.db.record_teacher_login(target_id, start_time_override=now_t)

                self.status_bar.config(text=f"Face Recognized ✓ Attendance Marked & Work Session Started ({target_name})", bg="#22543d", fg="#9ae6b4")
                if self.on_attendance_marked:
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
