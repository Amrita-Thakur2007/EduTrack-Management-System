import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
import pickle
from PIL import Image, ImageTk
from database.db_manager import DBManager

class FaceRegisterWindow(tk.Toplevel):
    """GUI window for registering student face encoding via camera feed."""
    def __init__(self, parent, student_id: str, student_name: str, db_manager: DBManager, on_complete=None):
        super().__init__(parent)
        self.title(f"Face Registration - {student_name} ({student_id})")
        self.geometry("680x580")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.student_id = student_id
        self.student_name = student_name
        self.db = db_manager
        self.on_complete = on_complete

        self.cap = None
        self.is_running = False
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.captured_encoding = None

        self._build_ui()
        self._start_camera()

    def _build_ui(self):
        # Header
        header = ttk.Frame(self, padding=10)
        header.pack(fill=tk.X)
        ttk.Label(header, text=f"Register Face: {self.student_name}", font=("Segoe UI", 14, "bold")).pack(anchor=tk.W)
        ttk.Label(header, text=f"ID: {self.student_id} | Position face inside the green box and click Capture.", font=("Segoe UI", 9)).pack(anchor=tk.W)

        # Video Canvas Frame
        video_frame = ttk.Frame(self, padding=5, relief="solid")
        video_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        self.canvas_label = ttk.Label(video_frame, text="Initializing Camera...", anchor=tk.CENTER)
        self.canvas_label.pack(fill=tk.BOTH, expand=True)

        # Controls & Status
        ctrl_frame = ttk.Frame(self, padding=10)
        ctrl_frame.pack(fill=tk.X)

        self.status_label = ttk.Label(ctrl_frame, text="Status: Waiting for camera feed...", font=("Segoe UI", 10, "italic"))
        self.status_label.pack(side=tk.LEFT, padx=10)

        self.btn_capture = ttk.Button(ctrl_frame, text="📸 Capture & Save", command=self.capture_face, state=tk.DISABLED)
        self.btn_capture.pack(side=tk.RIGHT, padx=5)

        self.btn_cancel = ttk.Button(ctrl_frame, text="Cancel", command=self.on_close)
        self.btn_cancel.pack(side=tk.RIGHT, padx=5)

    def _start_camera(self):
        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)
            
            if not self.cap.isOpened():
                self.status_label.config(text="Status: Camera unavailable (Device 0 disconnected).")
                messagebox.showwarning(
                    "Camera Error", 
                    "Unable to access camera.\nIf testing on a system without a camera, mock face data can be generated for testing."
                )
                self._offer_mock_registration()
                return
            
            self.is_running = True
            self._update_frame()
        except Exception as e:
            self.status_label.config(text=f"Status: Camera error ({str(e)})")
            messagebox.showerror("Camera Error", f"Failed to initialize camera: {e}")
            self._offer_mock_registration()

    def _offer_mock_registration(self):
        """Offers fallback mock registration when camera hardware is absent during automated tests."""
        if messagebox.askyesno("Mock Face Registration", "Camera unavailable. Register synthetic face encoding for testing?"):
            mock_vec = np.random.uniform(0, 1, (100, 100)).astype(np.float32)
            blob = pickle.dumps(mock_vec)
            self.db.save_face_encoding(self.student_id, blob)
            messagebox.showinfo("Success", f"Mock face registered successfully for {self.student_name}!")
            if self.on_complete:
                self.on_complete(True)
            self.destroy()

    def _update_frame(self):
        if not self.is_running or self.cap is None or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret or frame is None:
            self.after(30, self._update_frame)
            return

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80))

        if len(faces) == 0:
            self.status_label.config(text="Status: No face detected. Adjust lighting and face camera.")
            self.btn_capture.config(state=tk.DISABLED)
            self.captured_encoding = None
        elif len(faces) > 1:
            self.status_label.config(text="Status: Multiple faces detected! Ensure only one person is in view.")
            self.btn_capture.config(state=tk.DISABLED)
            self.captured_encoding = None
        else:
            (x, y, w, h) = faces[0]
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, "Ready to Capture", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            roi_gray = gray[y:y+h, x:x+w]
            roi_resized = cv2.resize(roi_gray, (100, 100))
            self.captured_encoding = roi_resized
            
            self.status_label.config(text="Status: Valid face detected. Click 'Capture & Save'.")
            self.btn_capture.config(state=tk.NORMAL)

        # Convert to Image for Tkinter
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame)
        img = img.resize((640, 420), Image.Resampling.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=img)
        
        self.canvas_label.imgtk = imgtk
        self.canvas_label.configure(image=imgtk)

        self.after(30, self._update_frame)

    def capture_face(self):
        if self.captured_encoding is None:
            messagebox.showwarning("Warning", "No valid face encoding ready for capture.")
            return

        blob = pickle.dumps(self.captured_encoding)
        success = self.db.save_face_encoding(self.student_id, blob)
        if success:
            messagebox.showinfo("Success", f"Face registered successfully for Student ID {self.student_id} ({self.student_name})!")
            if self.on_complete:
                self.on_complete(True)
            self.on_close()
        else:
            messagebox.showerror("Error", "Failed to save face encoding to database.")

    def on_close(self):
        self.is_running = False
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
        self.destroy()
