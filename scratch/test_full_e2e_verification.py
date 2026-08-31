import os
import sys
import tkinter as tk
import time
import pickle
import numpy as np
from tkinter import messagebox

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DBManager
from gui.teacher_dashboard import TeacherDashboard
from face_attendance.face_registration import FaceRegisterWindow
from face_attendance.face_recognition import FaceAttendanceScannerWindow

messages_info = []
messages_warning = []
messages_error = []

messagebox.showinfo = lambda title, msg: messages_info.append((title, str(msg)))
messagebox.showwarning = lambda title, msg: messages_warning.append((title, str(msg)))
messagebox.showerror = lambda title, msg: messages_error.append((title, str(msg)))

def test_full_flow():
    print("=================================================================")
    print("=== RUNNING FULL END-TO-END VERIFICATION OF TEACHER & STUDENT FACE FLOWS ===")
    print("=================================================================")

    db_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f"test_e2e_verify_{int(time.time())}.db")
    if os.path.exists(db_file):
        os.remove(db_file)
    db = DBManager(db_file)

    root = tk.Tk()
    root.withdraw()

    FaceRegisterWindow._start_camera = lambda self: None
    FaceAttendanceScannerWindow._start_camera = lambda self: None

    # Step 1: Create teacher account and login
    u_teacher = db.create_user("teacher1", "Pass1234", "Teacher")
    db.add_teacher({
        "teacher_id": "TCH_101",
        "name": "Prof. Sharma",
        "department": "Science",
        "email": "sharma@school.edu"
    }, u_teacher)

    # Step 2: Create Student 1 (Amrita) and register initial face
    u_amrita = db.create_user("amrita", "Pass1234", "Student")
    db.add_student({
        "student_id": "STU_AMRITA",
        "name": "Amrita",
        "education_type": "School",
        "school_name": "SKV Delhi",
        "current_class": "10",
        "section": "A"
    }, u_amrita)

    # Step 3: Create Student 2 (Anandi) and register initial face
    u_anandi = db.create_user("anandi", "Pass1234", "Student")
    db.add_student({
        "student_id": "STU_ANANDI",
        "name": "Anandi",
        "education_type": "School",
        "school_name": "SKV Delhi",
        "current_class": "10",
        "section": "B"
    }, u_anandi)

    # Synthetic realistic face matrices
    np.random.seed(42)
    amrita_face_orig = (np.random.rand(100, 100) * 255).astype(np.uint8)
    np.random.seed(99)
    anandi_face_orig = (np.random.rand(100, 100) * 255).astype(np.uint8)

    # Student initial face registration (Step 1 of Prompt)
    db.save_face_encoding("STU_AMRITA", pickle.dumps(amrita_face_orig))
    db.save_face_encoding("STU_ANANDI", pickle.dumps(anandi_face_orig))
    print("[STEP 1 CHECK] Initial faces saved for Amrita and Anandi.")

    # Step 4: Open Teacher Dashboard -> My Class Students
    teacher_user_data = {"id": u_teacher, "username": "teacher1", "role": "Teacher"}
    t_dash = TeacherDashboard(root, db, teacher_user_data)
    t_dash.show_students()

    # Step 5: Teacher selects Amrita from table and clicks 'Register Face'
    # Find Amrita's item in treeview
    amrita_item = None
    anandi_item = None
    for child in t_dash.tree.get_children():
        vals = t_dash.tree.item(child)['values']
        if vals and vals[0] == "STU_AMRITA":
            amrita_item = child
        elif vals and vals[0] == "STU_ANANDI":
            anandi_item = child

    assert amrita_item is not None, "Amrita must appear in teacher students list"
    assert anandi_item is not None, "Anandi must appear in teacher students list"

    # --- SUB-TEST A: Teacher selects Amrita, but Anandi's face is presented ---
    t_dash.tree.selection_set(amrita_item)
    messages_error.clear()
    messages_info.clear()

    # Trigger Register Face from Teacher Dashboard
    item_vals = t_dash.tree.item(amrita_item)['values']
    sid = item_vals[0]
    sname = item_vals[1]
    reg_win_wrong = FaceRegisterWindow(t_dash, sid, sname, db, require_identity_match=True)
    reg_win_wrong.captured_encoding = anandi_face_orig  # Wrong face!
    reg_win_wrong.save_face()
    reg_win_wrong.destroy()

    assert len(messages_error) == 1, f"Expected 1 error message, got {len(messages_error)}"
    assert "You are not Amrita. This face does not match the registered face." in messages_error[0][1]
    assert len(messages_info) == 0, "No success message should be shown on mismatch"

    # Verify DB still has Amrita's original face
    db_amrita_face = pickle.loads(db.get_face_encoding("STU_AMRITA"))
    assert np.array_equal(db_amrita_face, amrita_face_orig), "DB face must NOT be modified when wrong person face is presented"
    print("[SUB-TEST A PASS] Teacher selected Amrita + Anandi face -> Rejected with 'You are not Amrita. This face does not match the registered face.' & DB unchanged.")

    # --- SUB-TEST B: Teacher selects Amrita, and Amrita's face is presented ---
    messages_error.clear()
    messages_info.clear()

    amrita_new_face = np.clip(amrita_face_orig.astype(int) + np.random.randint(-4, 4, (100, 100)), 0, 255).astype(np.uint8)
    reg_win_correct = FaceRegisterWindow(t_dash, sid, sname, db, require_identity_match=True)
    reg_win_correct.captured_encoding = amrita_new_face  # Correct face!
    reg_win_correct.save_face()
    reg_win_correct.destroy()

    assert len(messages_error) == 0, f"Expected no error, got {messages_error}"
    assert len(messages_info) == 1, "Success message must be shown"
    assert "Face Registered Successfully" in messages_info[0][1] or "success" in messages_info[0][1].lower()

    # Verify DB now has updated face
    db_amrita_face_updated = pickle.loads(db.get_face_encoding("STU_AMRITA"))
    assert np.array_equal(db_amrita_face_updated, amrita_new_face), "DB face must be updated when Amrita's face matches"
    print("[SUB-TEST B PASS] Teacher selected Amrita + Amrita face -> Verified, saved & success dialog shown.")

    # --- SUB-TEST C: Teacher selects Anandi, but Amrita's face is presented ---
    t_dash.tree.selection_set(anandi_item)
    messages_error.clear()
    messages_info.clear()

    item_vals_anandi = t_dash.tree.item(anandi_item)['values']
    sid_anandi = item_vals_anandi[0]
    sname_anandi = item_vals_anandi[1]
    reg_win_anandi_wrong = FaceRegisterWindow(t_dash, sid_anandi, sname_anandi, db, require_identity_match=True)
    reg_win_anandi_wrong.captured_encoding = amrita_new_face  # Wrong face for Anandi!
    reg_win_anandi_wrong.save_face()
    reg_win_anandi_wrong.destroy()

    assert len(messages_error) == 1, f"Expected 1 error message, got {len(messages_error)}"
    assert "You are not Anandi. This face does not match the registered face." in messages_error[0][1]
    print("[SUB-TEST C PASS] Teacher selected Anandi + Amrita face -> Rejected with 'You are not Anandi. This face does not match the registered face.'")

    # --- SUB-TEST D: Attendance scanner verification for Anandi ---
    messages_error.clear()
    messages_info.clear()
    scanner_anandi = FaceAttendanceScannerWindow(root, db, target_role="Student", student_id="STU_ANANDI")
    scanner_anandi.captured_frame_gray = amrita_new_face # Amrita face on Anandi account
    scanner_anandi.attempt_capture()
    scanner_anandi.destroy()

    assert len(messages_error) > 0, "Attendance must reject Amrita face on Anandi account"
    assert "You are not Anandi" in messages_error[0][1]
    print("[SUB-TEST D PASS] Attendance marking: Anandi account + Amrita face -> Rejected with 'You are not Anandi! Attendance cannot be marked.'")

    try:
        t_dash.destroy()
        root.destroy()
    except Exception:
        pass

    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass

    print("\n=================================================================")
    print("=== 100% PROPER WORKING VERIFIED: ALL END-TO-END TESTS PASSED! ===")
    print("=================================================================")

if __name__ == "__main__":
    test_full_flow()
