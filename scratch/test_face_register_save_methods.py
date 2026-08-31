import os
import sys
import time
import pickle
import numpy as np
import cv2
import tkinter as tk
from unittest.mock import patch, MagicMock

sys.path.insert(0, ".")
from database.db_manager import DBManager
from face_attendance.face_registration import FaceRegisterWindow

def test_face_save_flows():
    print("=== TESTING FACE REGISTRATION SAVE FLOWS ===")
    test_db = f"scratch/test_face_save_{int(time.time())}.db"
    db = DBManager(db_path=test_db)
    root = tk.Tk()
    root.withdraw()

    # 1. Test direct save_face from a synthetic camera frame
    on_complete_called = []
    def on_comp(res):
        on_complete_called.append(res)

    with patch("face_attendance.face_registration.FaceRegisterWindow._start_camera"):
        win = FaceRegisterWindow(root, "STU_1001", "Aarav Sharma", db, on_complete=on_comp)
        
        # Create a frame with a face
        fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.circle(fake_frame, (320, 240), 80, (200, 200, 200), -1)
        win.current_frame = fake_frame

        with patch("tkinter.messagebox.showinfo") as mock_info:
            win.save_face()
            assert len(on_complete_called) == 1 and on_complete_called[0] is True, "Callback should be called with True!"
            assert mock_info.called, "Should show success message!"
            
            # Verify in DB
            enc = db.get_face_encoding("STU_1001")
            assert enc is not None, "Face encoding should be saved in DB!"
            mat = pickle.loads(enc)
            assert mat.shape == (100, 100), f"Saved face shape should be (100, 100), got {mat.shape}"
            print("[PASS] Test 1: Direct Save Face saved successfully to database!")

    # 2. Test snap_face then save_face
    on_complete_called.clear()
    with patch("face_attendance.face_registration.FaceRegisterWindow._start_camera"):
        win2 = FaceRegisterWindow(root, "STU_1002", "Pooja Verma", db, on_complete=on_comp)
        fake_frame2 = np.ones((480, 640, 3), dtype=np.uint8) * 128
        win2.current_frame = fake_frame2

        win2.snap_face()
        assert win2.is_paused_preview is True, "Preview should be paused after snap_face"

        with patch("tkinter.messagebox.showinfo") as mock_info2:
            win2.save_face()
            assert len(on_complete_called) == 1
            enc2 = db.get_face_encoding("STU_1002")
            assert enc2 is not None
            print("[PASS] Test 2: Snap Face -> Save Face flow successfully verified!")

    # 3. Test Photo Upload flow
    test_img_path = "scratch/temp_test_face.jpg"
    cv2.imwrite(test_img_path, np.ones((300, 300, 3), dtype=np.uint8) * 180)

    on_complete_called.clear()
    with patch("face_attendance.face_registration.FaceRegisterWindow._start_camera"):
        win3 = FaceRegisterWindow(root, "STU_1003", "Karan Johar", db, on_complete=on_comp)
        with patch("tkinter.filedialog.askopenfilename", return_value=test_img_path):
            win3.upload_photo()
            assert win3.captured_encoding is not None

        with patch("tkinter.messagebox.showinfo"):
            win3.save_face()
            assert len(on_complete_called) == 1
            enc3 = db.get_face_encoding("STU_1003")
            assert enc3 is not None
            print("[PASS] Test 3: Upload Photo -> Save Face flow successfully verified!")

    if os.path.exists(test_img_path):
        try:
            os.remove(test_img_path)
        except Exception:
            pass
    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except Exception:
            pass

    root.destroy()
    print("=== ALL FACE SAVE FLOWS PASSED 100%! ===")

if __name__ == "__main__":
    test_face_save_flows()
