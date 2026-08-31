import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
import numpy as np
import pickle
import os
from PIL import Image, ImageTk
from database.db_manager import DBManager

class FaceRegisterWindow(tk.Toplevel):
    """GUI window for registering student or teacher face encoding via camera feed or photo upload."""
    def __init__(self, parent, student_id: str, student_name: str, db_manager: DBManager, on_complete=None, success_message="Face Registered Successfully", require_identity_match: bool = False):
        super().__init__(parent)
        self.title(f"Face Registration - {student_name} ({student_id})")
        self.geometry("740x660")
        self.minsize(680, 600)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.student_id = str(student_id).strip()
        self.student_name = str(student_name).strip()
        self.db = db_manager
        self.on_complete = on_complete
        self.success_message = success_message
        self.require_identity_match = require_identity_match

        # Retrieve existing registered face for this student ID if available
        self.existing_face_mat = None
        existing_blob = self.db.get_face_encoding(self.student_id)
        if not existing_blob:
            st = self.db.get_student(self.student_id)
            if st:
                if not self.student_name:
                    self.student_name = st.get('name', self.student_name)
                if st.get('student_id') and st.get('student_id') != self.student_id:
                    existing_blob = self.db.get_face_encoding(st['student_id'])
                if not existing_blob and st.get('enrollment_number'):
                    existing_blob = self.db.get_face_encoding(st['enrollment_number'])
        if existing_blob:
            try:
                mat = pickle.loads(existing_blob)
                if isinstance(mat, np.ndarray):
                    self.existing_face_mat = mat
            except Exception as e:
                print("Error loading existing face encoding:", e)

        self.cap = None
        self.is_running = False
        self.is_paused_preview = False
        self.current_frame = None
        self.captured_encoding = None
        self.last_detected_roi = None

        if hasattr(cv2, 'CascadeClassifier') and hasattr(cv2, 'data') and hasattr(cv2.data, 'haarcascades'):
            try:
                self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            except Exception:
                self.face_cascade = None
        else:
            self.face_cascade = None

        self._build_ui()
        self._start_camera()

    def _build_ui(self):
        # Header
        header = ttk.Frame(self, padding=12)
        header.pack(fill=tk.X)
        ttk.Label(header, text=f"📷 Register Face: {self.student_name}", font=("Segoe UI", 14, "bold")).pack(anchor=tk.W)
        ttk.Label(header, text=f"User ID / Enrollment No: {self.student_id} | Look directly into camera or upload a photo.", font=("Segoe UI", 9)).pack(anchor=tk.W)

        # Video Canvas Frame
        video_frame = ttk.Frame(self, padding=4, relief="solid")
        video_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=4)

        self.canvas_label = ttk.Label(video_frame, text="Initializing Camera Stream...", anchor=tk.CENTER)
        self.canvas_label.pack(fill=tk.BOTH, expand=True)

        # Status Bar
        self.status_label = tk.Label(self, text="Status: Starting camera...", font=("Segoe UI", 10, "bold"), bg="#1a202c", fg="#63b3ed", pady=6)
        self.status_label.pack(fill=tk.X, padx=15, pady=(4, 0))

        # Controls & Action Buttons Frame
        ctrl_frame = ttk.Frame(self, padding=10)
        ctrl_frame.pack(fill=tk.X)

        self.btn_capture = ttk.Button(ctrl_frame, text="📸 Capture Photo", command=self.snap_face)
        self.btn_capture.pack(side=tk.LEFT, padx=4)

        self.btn_save = ttk.Button(ctrl_frame, text="💾 Save Face", style="Primary.TButton", command=self.save_face)
        self.btn_save.pack(side=tk.LEFT, padx=4)

        self.btn_retake = ttk.Button(ctrl_frame, text="🔄 Retake", command=self.retake_face, state=tk.DISABLED)
        self.btn_retake.pack(side=tk.LEFT, padx=4)

        self.btn_upload = ttk.Button(ctrl_frame, text="📁 Upload Photo", command=self.upload_photo)
        self.btn_upload.pack(side=tk.LEFT, padx=4)

        self.btn_cancel = ttk.Button(ctrl_frame, text="✖ Cancel", command=self.on_close)
        self.btn_cancel.pack(side=tk.RIGHT, padx=4)

    def _start_camera(self):
        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)

            if not self.cap.isOpened():
                self.status_label.config(text="Status: Camera unavailable. You can click 'Upload Photo' to register.", bg="#742a2a", fg="#fff")
                self._offer_mock_registration()
                return

            self.is_running = True
            self.is_paused_preview = False
            self._update_frame()
        except Exception as e:
            self.status_label.config(text=f"Status: Camera error ({str(e)}). You can click 'Upload Photo'.", bg="#742a2a", fg="#fff")
            self._offer_mock_registration()

    def _offer_mock_registration(self):
        """Offers fallback mock registration when camera hardware is absent during automated tests or if device has no camera."""
        if messagebox.askyesno("Mock Face Registration", "Camera unavailable. Register synthetic face encoding for testing / offline mode?"):
            mock_vec = np.random.uniform(0, 1, (100, 100)).astype(np.float32)
            blob = pickle.dumps(mock_vec)
            self.db.save_face_encoding(self.student_id, blob)
            messagebox.showinfo("Success", f"Face registered successfully for {self.student_name}!")
            if self.on_complete:
                try:
                    self.on_complete(True)
                except Exception as e:
                    print("Error executing on_complete:", e)
            self.destroy()

    def _extract_face_roi(self, frame_img: np.ndarray) -> np.ndarray:
        """Extract a 100x100 grayscale face matrix from given image frame."""
        if frame_img is None:
            return None

        if len(frame_img.shape) == 3:
            gray = cv2.cvtColor(frame_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame_img.copy()

        if self.face_cascade is not None:
            # Try detection with sensitive parameters
            for s_factor in [1.1, 1.15, 1.2]:
                faces = self.face_cascade.detectMultiScale(gray, scaleFactor=s_factor, minNeighbors=3, minSize=(30, 30))
                if len(faces) > 0:
                    # Select largest face (closest to camera)
                    largest_face = max(faces, key=lambda f: f[2] * f[3])
                    x, y, w, h = largest_face
                    roi = gray[y:y+h, x:x+w]
                    return cv2.resize(roi, (100, 100))

        # Fallback: center square crop if face detector misses edge cases
        h, w = gray.shape[:2]
        size = min(h, w)
        y1 = (h - size) // 2
        x1 = (w - size) // 2
        center_crop = gray[y1:y1+size, x1:x1+size]
        return cv2.resize(center_crop, (100, 100))

    def _update_frame(self):
        if not self.is_running or self.is_paused_preview or self.cap is None or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret or frame is None:
            self.after(30, self._update_frame)
            return

        frame = cv2.flip(frame, 1)
        self.current_frame = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = []
        if self.face_cascade is not None:
            try:
                faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
            except Exception:
                faces = []

        if len(faces) == 0:
            self.status_label.config(
                text="Status: Looking for face... Please look directly at the camera.",
                bg="#1a202c",
                fg="#63b3ed"
            )
        elif len(faces) > 1:
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            self.status_label.config(
                text="Status: ❌ Multiple faces detected. Please make sure only one face is visible.",
                bg="#742a2a",
                fg="#fff"
            )
        else:
            (x, y, w, h) = faces[0]
            roi_gray = gray[y:y+h, x:x+w]
            self.last_detected_roi = cv2.resize(roi_gray, (100, 100))
            self.captured_encoding = self.last_detected_roi

            from face_attendance.face_recognition import compare_face_matrices

            if self.existing_face_mat is not None:
                score = compare_face_matrices(self.last_detected_roi, self.existing_face_mat)
                if score >= 0.45:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, f"Verified: {self.student_name}", (x, max(20, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    self.status_label.config(
                        text=f"Status: ✓ Face matched for {self.student_name}! Click 'Save Face' to update.",
                        bg="#22543d",
                        fg="#9ae6b4"
                    )
                else:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    cv2.putText(frame, f"Not {self.student_name}!", (x, max(20, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    self.status_label.config(
                        text=f"Status: ❌ You are not {self.student_name}. This face does not match the registered face.",
                        bg="#742a2a",
                        fg="#fff"
                    )
            else:
                # First-time registration flow: No existing face to compare against
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, "Face Detected - Ready to Save", (x, max(20, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                self.status_label.config(
                    text="Status: ✓ Face detected! Click 'Save Face' or 'Capture Photo'.",
                    bg="#22543d",
                    fg="#9ae6b4"
                )

        # Convert to Image for Tkinter
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame)
        img = img.resize((680, 440), Image.Resampling.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=img)

        self.canvas_label.imgtk = imgtk
        self.canvas_label.configure(image=imgtk)

        self.after(30, self._update_frame)

    def snap_face(self):
        """Freeze preview on captured face and prepare for saving."""
        if self.current_frame is None:
            messagebox.showwarning("Warning", "No camera frame available. Please wait for camera stream.")
            return

        if self.face_cascade is not None:
            gray = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2GRAY)
            try:
                faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
                if len(faces) > 1:
                    self.status_label.config(
                        text="Status: ❌ Multiple faces detected. Please make sure only one face is visible.",
                        bg="#742a2a",
                        fg="#fff"
                    )
                    messagebox.showwarning("Notice", "Multiple faces detected. Please make sure only one face is visible.")
                    return
            except Exception:
                pass

        # Extract face from current frame
        roi = self._extract_face_roi(self.current_frame)
        if roi is not None:
            self.captured_encoding = roi
            self.last_detected_roi = roi

        self.is_paused_preview = True
        self.btn_capture.config(state=tk.DISABLED)
        self.btn_save.config(state=tk.NORMAL)
        self.btn_retake.config(state=tk.NORMAL)
        self.status_label.config(
            text="Status: Photo captured! Click 'Save Face' to save, or 'Retake' to recapture.",
            bg="#1e3a8a",
            fg="#93c5fd"
        )

    def retake_face(self):
        """Resume live camera stream for new capture."""
        self.is_paused_preview = False
        self.btn_capture.config(state=tk.NORMAL)
        self.btn_save.config(state=tk.NORMAL)
        self.btn_retake.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Scanning for face...", bg="#1a202c", fg="#63b3ed")
        self._update_frame()

    def upload_photo(self):
        """Allow user to select an existing photo file to extract and register face."""
        file_path = filedialog.askopenfilename(
            parent=self,
            title="Select Face Photo",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.webp"), ("All files", "*.*")]
        )
        if not file_path or not os.path.exists(file_path):
            return

        img = cv2.imread(file_path)
        if img is None:
            messagebox.showerror("Error", "Could not load selected image file.")
            return

        roi = self._extract_face_roi(img)
        if roi is None:
            messagebox.showerror("Error", "Could not detect a clear face in the uploaded photo.")
            return

        self.captured_encoding = roi
        self.last_detected_roi = roi
        self.is_paused_preview = True

        # Display uploaded photo on canvas
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_img)
        pil_img = pil_img.resize((680, 440), Image.Resampling.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=pil_img)
        self.canvas_label.imgtk = imgtk
        self.canvas_label.configure(image=imgtk)

        self.btn_retake.config(state=tk.NORMAL)
        self.status_label.config(
            text=f"Status: Photo '{os.path.basename(file_path)}' loaded. Click 'Save Face' to complete registration.",
            bg="#1e3a8a",
            fg="#93c5fd"
        )

    def save_face(self):
        """Save captured face encoding to database after verifying identity if an existing face is registered."""
        if self.current_frame is not None and self.face_cascade is not None:
            try:
                gray = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
                if len(faces) > 1:
                    self.status_label.config(
                        text="Status: ❌ Multiple faces detected. Please make sure only one face is visible.",
                        bg="#742a2a",
                        fg="#fff"
                    )
                    messagebox.showwarning("Notice", "Multiple faces detected. Please make sure only one face is visible.")
                    return
            except Exception:
                pass

        target_roi = self.captured_encoding if self.captured_encoding is not None else self.last_detected_roi

        if target_roi is None and self.current_frame is not None:
            target_roi = self._extract_face_roi(self.current_frame)

        if target_roi is None:
            messagebox.showwarning("Warning", "No valid face detected. Please look at the camera or click 'Upload Photo'.")
            return

        from face_attendance.face_recognition import compare_face_matrices

        # Identity Verification: If this student already has a registered face, verify identity before replacing
        if self.existing_face_mat is not None:
            score = compare_face_matrices(target_roi, self.existing_face_mat)
            if score < 0.45:
                err_msg = f"You are not {self.student_name}. This face does not match the registered face."
                self.status_label.config(text=f"Status: ❌ {err_msg}", bg="#742a2a", fg="#fff")
                messagebox.showerror("Identity Verification Failed", err_msg)
                return

        blob = pickle.dumps(target_roi)
        success = self.db.save_face_encoding(self.student_id, blob)

        if success:
            messagebox.showinfo("Success", f"{self.success_message}\n\nUser ID: {self.student_id}\nName: {self.student_name}")
            if self.on_complete:
                try:
                    self.on_complete(True)
                except Exception as e:
                    print("Error executing on_complete callback:", e)
            self.on_close()
        else:
            messagebox.showerror("Error", "Failed to save face encoding to database.")

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
