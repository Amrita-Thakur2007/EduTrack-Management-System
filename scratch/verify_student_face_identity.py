import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
import pickle
import numpy as np
import tkinter as tk
from tkinter import messagebox

messages_info = []
messages_warning = []
messages_error = []
messagebox.showinfo = lambda title, msg: messages_info.append((title, str(msg)))
messagebox.showwarning = lambda title, msg: messages_warning.append((title, str(msg)))
messagebox.showerror = lambda title, msg: messages_error.append((title, str(msg)))
messagebox.askyesno = lambda title, msg: True

from database.db_manager import DBManager
from face_attendance.face_recognition import FaceAttendanceScannerWindow, preprocess_face_roi, compare_face_matrices

FaceAttendanceScannerWindow._start_camera = lambda self: None

def run_tests():
    print("=== STARTING VERIFICATION: STUDENT FACE IDENTITY VERIFICATION ===")
    
    db_path = f"scratch/test_face_id_{int(time.time())}.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass
            
    db = DBManager(db_path=db_path)
    root = tk.Tk()
    root.withdraw()

    np.random.seed(42)
    face_anandi = (np.random.rand(100, 100) * 255).astype(np.uint8)
    face_amrita = (np.random.rand(100, 100) * 255).astype(np.uint8)
    face_unknown = (np.random.rand(100, 100) * 255).astype(np.uint8)

    # 1. Register Student 1: Anandi
    u_anandi = db.create_user("anandi", "Pass1234", "Student")
    db.add_student({
        "student_id": "STU_ANANDI",
        "name": "Anandi",
        "education_type": "School",
        "school_name": "Delhi Public School",
        "current_class": "10",
        "section": "A",
        "admission_date": "2026-08-28"
    }, u_anandi)
    db.save_face_encoding("STU_ANANDI", pickle.dumps(face_anandi))

    # 2. Register Student 2: Amrita
    u_amrita = db.create_user("amrita", "Pass1234", "Student")
    db.add_student({
        "student_id": "STU_AMRITA",
        "name": "Amrita",
        "education_type": "School",
        "school_name": "Delhi Public School",
        "current_class": "10",
        "section": "B",
        "admission_date": "2026-08-28"
    }, u_amrita)
    db.save_face_encoding("STU_AMRITA", pickle.dumps(face_amrita))

    from utils.helpers import get_current_date
    today = get_current_date()

    # TEST 1: Anandi account + Anandi Face
    messages_info.clear()
    messages_warning.clear()
    messages_error.clear()

    scanner_anandi = FaceAttendanceScannerWindow(root, db, target_role="Student", student_id="STU_ANANDI")
    scanner_anandi.captured_frame_gray = face_anandi
    scanner_anandi.attempt_capture()

    att_anandi = db.get_student_attendance_for_date("STU_ANANDI", today)
    assert att_anandi is not None, "Attendance for Anandi must be marked"
    assert att_anandi['status'] == "Present", "Attendance status must be Present"
    assert any("attendance is marked" in m[1].lower() for m in messages_info), "Success message must be shown"
    print("TEST 1 PASS: Anandi account + Anandi face -> Face verified and attendance successfully marked.")

    # TEST 2: Anandi account + Unknown Face
    with db.get_connection() as conn:
        conn.cursor().execute("DELETE FROM attendance WHERE student_id = 'STU_ANANDI'")
        conn.commit()

    messages_info.clear()
    messages_warning.clear()
    messages_error.clear()

    scanner_wrong = FaceAttendanceScannerWindow(root, db, target_role="Student", student_id="STU_ANANDI")
    scanner_wrong.captured_frame_gray = face_unknown
    scanner_wrong.attempt_capture()

    att_anandi_after_wrong = db.get_student_attendance_for_date("STU_ANANDI", today)
    assert att_anandi_after_wrong is None, "Attendance must NOT be marked for wrong face"
    assert len(messages_info) == 0, "No success message should appear"
    assert len(messages_error) > 0, "Error message must appear"
    expected_msg_anandi = "You are not Anandi! This face does not match Anandi's registered face. Attendance cannot be marked."
    assert messages_error[0][1] == expected_msg_anandi, f"Expected '{expected_msg_anandi}', got '{messages_error[0][1]}'"
    print("TEST 2 PASS: Anandi account + Unknown face -> Rejected with dynamic message:", messages_error[0][1])

    # TEST 3: Amrita account + Amrita Face
    messages_info.clear()
    messages_warning.clear()
    messages_error.clear()

    scanner_amrita = FaceAttendanceScannerWindow(root, db, target_role="Student", student_id="STU_AMRITA")
    scanner_amrita.captured_frame_gray = face_amrita
    scanner_amrita.attempt_capture()

    att_amrita = db.get_student_attendance_for_date("STU_AMRITA", today)
    assert att_amrita is not None, "Attendance for Amrita must be marked"
    assert att_amrita['status'] == "Present", "Attendance status must be Present"
    assert any("attendance is marked" in m[1].lower() for m in messages_info), "Success message must be shown"
    print("TEST 3 PASS: Amrita account + Amrita face -> Face verified and attendance successfully marked.")

    # TEST 4: Anandi account + Amrita Face
    with db.get_connection() as conn:
        conn.cursor().execute("DELETE FROM attendance WHERE student_id = 'STU_ANANDI'")
        conn.commit()

    messages_info.clear()
    messages_warning.clear()
    messages_error.clear()

    scanner_anandi_amrita = FaceAttendanceScannerWindow(root, db, target_role="Student", student_id="STU_ANANDI")
    scanner_anandi_amrita.captured_frame_gray = face_amrita
    scanner_anandi_amrita.attempt_capture()

    att_anandi_cross = db.get_student_attendance_for_date("STU_ANANDI", today)
    assert att_anandi_cross is None, "Anandi attendance must NOT be marked when Amrita's face is shown"
    assert len(messages_info) == 0, "No success message should appear"
    assert len(messages_error) > 0, "Error message must appear"
    assert messages_error[0][1] == expected_msg_anandi, f"Expected '{expected_msg_anandi}', got '{messages_error[0][1]}'"
    print("TEST 4 PASS: Anandi account + Amrita face -> Rejected with dynamic message:", messages_error[0][1])

    # TEST 5: Multiple Faces Detected
    messages_info.clear()
    messages_warning.clear()
    messages_error.clear()

    scanner_multi = FaceAttendanceScannerWindow(root, db, target_role="Student", student_id="STU_ANANDI")
    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    class MockCascade:
        def detectMultiScale(self, *args, **kwargs):
            return [(50, 50, 80, 80), (200, 200, 80, 80)]
    scanner_multi.face_cascade = MockCascade()
    class MockCap:
        def isOpened(self): return True
        def read(self): return True, fake_frame
    scanner_multi.cap = MockCap()
    scanner_multi.captured_frame_gray = None

    scanner_multi.attempt_capture()

    att_anandi_multi = db.get_student_attendance_for_date("STU_ANANDI", today)
    assert att_anandi_multi is None, "Attendance must NOT be marked when multiple faces are detected"
    assert any("multiple faces" in m[1].lower() for m in messages_warning), "Multiple faces warning must appear"
    print("TEST 5 PASS: Multiple faces detected -> Rejected with multiple faces warning.")

    scanner_anandi.destroy()
    scanner_wrong.destroy()
    scanner_amrita.destroy()
    scanner_anandi_amrita.destroy()
    scanner_multi.destroy()
    root.quit()
    root.destroy()

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

    print("\n=======================================================")
    print("ALL 5 STUDENT FACE IDENTITY VERIFICATION TESTS PASSED 100%!")
    print("=======================================================")

if __name__ == "__main__":
    run_tests()
