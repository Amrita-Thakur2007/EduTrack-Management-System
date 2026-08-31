import os
import sys
import tkinter as tk
import time
import pickle
import numpy as np
from tkinter import messagebox

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DBManager
from face_attendance.face_registration import FaceRegisterWindow
from face_attendance.face_recognition import FaceAttendanceScannerWindow

messages_info = []
messages_warning = []
messages_error = []

messagebox.showinfo = lambda title, msg: messages_info.append((title, str(msg)))
messagebox.showwarning = lambda title, msg: messages_warning.append((title, str(msg)))
messagebox.showerror = lambda title, msg: messages_error.append((title, str(msg)))

def test_face_update_and_attendance():
    print("=== TESTING STUDENT FACE UPDATE & ATTENDANCE MISMATCH CHECK ===")
    
    db_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f"test_face_upd_{int(time.time())}.db")
    if os.path.exists(db_file):
        os.remove(db_file)
    db = DBManager(db_file)
    
    root = tk.Tk()
    root.withdraw()
    
    # 1. Create two students: Amrita and Anandi
    u_amrita = db.create_user("amrita", "Pass1234", "Student")
    db.add_student({
        "student_id": "STU_AMRITA",
        "name": "Amrita",
        "education_type": "School",
        "school_name": "SKV Delhi",
        "current_class": "10",
        "section": "A"
    }, u_amrita)
    
    u_anandi = db.create_user("anandi", "Pass1234", "Student")
    db.add_student({
        "student_id": "STU_ANANDI",
        "name": "Anandi",
        "education_type": "School",
        "school_name": "SKV Delhi",
        "current_class": "10",
        "section": "B"
    }, u_anandi)
    
    # Distinct face images
    np.random.seed(101)
    amrita_face_v1 = (np.random.rand(100, 100) * 255).astype(np.uint8)
    amrita_face_v2 = np.clip(amrita_face_v1.astype(int) + np.random.randint(-5, 5, (100, 100)), 0, 255).astype(np.uint8)
    np.random.seed(201)
    anandi_face = (np.random.rand(100, 100) * 255).astype(np.uint8)
    
    # Save initial face for Anandi
    db.save_face_encoding("STU_ANANDI", pickle.dumps(anandi_face))
    
    FaceRegisterWindow._start_camera = lambda self: None
    FaceAttendanceScannerWindow._start_camera = lambda self: None
    
    # TEST 1: Amrita registers her face initially
    messages_error.clear()
    messages_info.clear()
    reg_win1 = FaceRegisterWindow(root, "STU_AMRITA", "Amrita", db)
    reg_win1.captured_encoding = amrita_face_v1
    reg_win1.save_face()
    reg_win1.destroy()
    
    assert len(messages_error) == 0, f"No error expected on registering face: {messages_error}"
    assert len(messages_info) > 0, "Success info expected"
    print("[PASS] Test 1: Amrita registered her face successfully with NO errors.")
    
    # TEST 2: Amrita UPDATES her face (e.g. from My Profile -> Update / Save Face)
    messages_error.clear()
    messages_info.clear()
    reg_win2 = FaceRegisterWindow(root, "STU_AMRITA", "Amrita", db, success_message="Face Updated Successfully")
    reg_win2.captured_encoding = amrita_face_v2
    reg_win2.save_face()
    reg_win2.destroy()
    
    assert len(messages_error) == 0, f"No error should occur when Amrita updates her own face: {messages_error}"
    assert len(messages_info) > 0, "Success info expected on update"
    assert "Face Updated Successfully" in messages_info[0][1]
    
    # Verify in DB that Amrita's face is updated to amrita_face_v2
    stored_blob = db.get_face_encoding("STU_AMRITA")
    stored_mat = pickle.loads(stored_blob)
    assert np.array_equal(stored_mat, amrita_face_v2), "Amrita's face matrix in DB should be updated"
    print("[PASS] Test 2: Amrita updated her face successfully with NO errors.")
    
    # TEST 3: Marking Attendance for Anandi using Amrita's face -> MUST FAIL WITH ERROR!
    messages_error.clear()
    messages_info.clear()
    scanner_anandi = FaceAttendanceScannerWindow(root, db, target_role="Student", student_id="STU_ANANDI")
    scanner_anandi.captured_frame_gray = amrita_face_v2
    scanner_anandi.attempt_capture()
    scanner_anandi.destroy()
    
    assert len(messages_error) > 0, "Error must be shown when Amrita tries to mark attendance for Anandi!"
    assert "You are not Anandi" in messages_error[0][1] or "verification failed" in messages_error[0][1].lower()
    print("[PASS] Test 3: Attendance for Anandi rejected when Amrita's face is used. Error shown:", messages_error[0][1])
    
    # TEST 4: Marking Attendance for Anandi using Anandi's registered face -> MUST SUCCEED!
    messages_error.clear()
    messages_info.clear()
    scanner_anandi2 = FaceAttendanceScannerWindow(root, db, target_role="Student", student_id="STU_ANANDI")
    scanner_anandi2.captured_frame_gray = anandi_face
    scanner_anandi2.attempt_capture()
    scanner_anandi2.destroy()
    
    assert len(messages_error) == 0, f"No error expected for Anandi's own face: {messages_error}"
    assert len(messages_info) > 0, "Success message expected for Anandi"
    print("[PASS] Test 4: Anandi's attendance marked successfully with Anandi's registered face.")
    
    # TEST 5: Marking Attendance for Amrita using Amrita's updated face -> MUST SUCCEED!
    messages_error.clear()
    messages_info.clear()
    scanner_amrita = FaceAttendanceScannerWindow(root, db, target_role="Student", student_id="STU_AMRITA")
    scanner_amrita.captured_frame_gray = amrita_face_v2
    scanner_amrita.attempt_capture()
    scanner_amrita.destroy()
    
    assert len(messages_error) == 0, f"No error expected for Amrita's own face: {messages_error}"
    assert len(messages_info) > 0, "Success message expected for Amrita"
    print("[PASS] Test 5: Amrita's attendance marked successfully with Amrita's updated face.")
    
    try:
        root.destroy()
    except Exception:
        pass
    
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass
            
    print("\n=== ALL FACE UPDATE & ATTENDANCE VERIFICATION TESTS PASSED 100% ===")

if __name__ == "__main__":
    test_face_update_and_attendance()
