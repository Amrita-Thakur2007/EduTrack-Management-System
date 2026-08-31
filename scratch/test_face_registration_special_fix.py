import os
import sys
import tkinter as tk
import time
import pickle
import numpy as np
from tkinter import messagebox

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

messages_info = []
messages_warning = []
messages_error = []

messagebox.showinfo = lambda title, msg: messages_info.append((title, str(msg)))
messagebox.showwarning = lambda title, msg: messages_warning.append((title, str(msg)))
messagebox.showerror = lambda title, msg: messages_error.append((title, str(msg)))

from database.db_manager import DBManager
from face_attendance.face_registration import FaceRegisterWindow
from gui.teacher_dashboard import TeacherDashboard

def test_face_registration_and_verification_rules():
    print("=== STARTING FACE REGISTRATION & IDENTITY VERIFICATION ACCEPTANCE TESTS ===")
    
    db_file = os.path.join(PROJECT_ROOT, "scratch", f"test_face_spec_{int(time.time())}.db")
    if os.path.exists(db_file):
        os.remove(db_file)
    db = DBManager(db_file)
    
    root = tk.Tk()
    root.withdraw()
    
    FaceRegisterWindow._start_camera = lambda self: None
    
    # 1. Setup Student Amrita (School) and Student Anandi (School) and Student Rohan (College)
    db.add_student({
        "student_id": "STU_AMRITA",
        "name": "Amrita",
        "education_type": "School",
        "school_name": "Delhi Public School",
        "current_class": "10",
        "section": "A",
        "admission_date": "2026-08-28"
    })
    
    db.add_student({
        "student_id": "STU_ANANDI",
        "name": "Anandi",
        "education_type": "School",
        "school_name": "Delhi Public School",
        "current_class": "10",
        "section": "B",
        "admission_date": "2026-08-28"
    })
    
    db.add_student({
        "student_id": "STU_ROHAN",
        "name": "Rohan",
        "education_type": "College",
        "college_name": "IIT Bombay",
        "enrollment_number": "ENR_ROHAN_01",
        "course": "B.Tech",
        "semester": "Semester 1",
        "admission_date": "2026-08-01"
    })

    # Prepare face matrices
    np.random.seed(1111)
    face_amrita_v1 = (np.random.rand(100, 100) * 255).astype(np.uint8)
    face_amrita_v2 = np.clip(face_amrita_v1.astype(int) + np.random.randint(-4, 4, (100, 100)), 0, 255).astype(np.uint8)
    
    np.random.seed(2222)
    face_anandi = (np.random.rand(100, 100) * 255).astype(np.uint8)
    
    np.random.seed(3333)
    face_rohan = (np.random.rand(100, 100) * 255).astype(np.uint8)

    # ----------------------------------------------------
    # TEST A: FIRST-TIME STUDENT FACE REGISTRATION
    # Amrita has NO registered face yet.
    # Expected: Face captured, saved to STU_AMRITA, success message, NOT "You are not Amrita"
    # ----------------------------------------------------
    print("\n--- TEST A: FIRST-TIME STUDENT FACE REGISTRATION ---")
    messages_error.clear()
    messages_info.clear()
    
    assert db.get_face_encoding("STU_AMRITA") is None, "Amrita must have no face initially"
    
    win_reg = FaceRegisterWindow(root, "STU_AMRITA", "Amrita", db)
    assert win_reg.existing_face_mat is None, "Existing face matrix must be None for first-time registration"
    win_reg.captured_encoding = face_amrita_v1
    win_reg.save_face()
    win_reg.destroy()
    
    assert len(messages_error) == 0, f"Expected 0 errors on first-time registration, got: {messages_error}"
    assert len(messages_info) > 0, "Expected success dialog on first-time registration"
    
    stored_amrita_blob = db.get_face_encoding("STU_AMRITA")
    assert stored_amrita_blob is not None, "Amrita's face must be saved in DB"
    stored_amrita_mat = pickle.loads(stored_amrita_blob)
    assert np.array_equal(stored_amrita_mat, face_amrita_v1), "Saved face must match Amrita's face"
    print("Test A Passed: First-time face registration succeeded without any false 'You are not Amrita' rejection!")

    # ----------------------------------------------------
    # TEST B: STUDENT UPDATE (AMRITA SHOWS AMRITA'S FACE)
    # Existing face = Amrita.
    # Expected: Match, update allowed, new face saved under STU_AMRITA
    # ----------------------------------------------------
    print("\n--- TEST B: STUDENT UPDATE FACE (SAME PERSON) ---")
    messages_error.clear()
    messages_info.clear()
    
    win_upd = FaceRegisterWindow(root, "STU_AMRITA", "Amrita", db, success_message="Face Updated Successfully")
    assert win_upd.existing_face_mat is not None, "Existing face matrix must be loaded"
    win_upd.captured_encoding = face_amrita_v2
    win_upd.save_face()
    win_upd.destroy()
    
    assert len(messages_error) == 0, f"Expected 0 errors when Amrita updates her own face, got: {messages_error}"
    assert len(messages_info) > 0, "Expected success info on update"
    
    updated_amrita_blob = db.get_face_encoding("STU_AMRITA")
    updated_amrita_mat = pickle.loads(updated_amrita_blob)
    assert np.array_equal(updated_amrita_mat, face_amrita_v2), "Amrita's face must be updated to v2"
    print("Test B Passed: Student face update with matching identity succeeded and updated DB!")

    # ----------------------------------------------------
    # TEST C: WRONG PERSON IN STUDENT UPDATE
    # Student = Amrita. Another person (e.g. Anandi) shows face.
    # Expected: Match failed, update rejected, Amrita's DB face unchanged, no success message
    # ----------------------------------------------------
    print("\n--- TEST C: WRONG PERSON IN STUDENT UPDATE ---")
    messages_error.clear()
    messages_info.clear()
    
    win_wrong = FaceRegisterWindow(root, "STU_AMRITA", "Amrita", db, success_message="Face Updated Successfully")
    win_wrong.captured_encoding = face_anandi
    win_wrong.save_face()
    win_wrong.destroy()
    
    assert len(messages_error) > 0, "Expected error when different person attempts to update Amrita's face!"
    assert "You are not Amrita" in messages_error[0][1] or "does not match" in messages_error[0][1]
    assert len(messages_info) == 0, "No success message should be shown on mismatch!"
    
    # Verify Amrita's DB face is still v2
    stored_check = pickle.loads(db.get_face_encoding("STU_AMRITA"))
    assert np.array_equal(stored_check, face_amrita_v2), "Amrita's face in DB must NOT be modified when wrong face is presented!"
    print(f"Test C Passed: Wrong person update correctly rejected with message: '{messages_error[0][1]}'")

    # ----------------------------------------------------
    # TEST D: TEACHER PORTAL REGISTER/UPDATE FACE
    # Teacher selects Amrita -> Register Face
    # - If Amrita appears -> Allowed
    # - If another person appears -> Rejected
    # ----------------------------------------------------
    print("\n--- TEST D: TEACHER PORTAL REGISTER/UPDATE FACE ---")
    t_user = {'id': 1, 'username': 'teacher1', 'role': 'Teacher'}
    t_dash = TeacherDashboard(root, db, t_user)
    t_dash.show_students()
    
    # Case D1: Another person appears (Rohan)
    messages_error.clear()
    messages_info.clear()
    win_tch_wrong = FaceRegisterWindow(t_dash, "STU_AMRITA", "Amrita", db)
    win_tch_wrong.captured_encoding = face_rohan
    win_tch_wrong.save_face()
    win_tch_wrong.destroy()
    
    assert len(messages_error) > 0, "Teacher portal must reject wrong person for Amrita"
    assert "You are not Amrita" in messages_error[0][1]
    assert len(messages_info) == 0
    print("Test D1 Passed: Teacher Portal rejected wrong person.")
    
    # Case D2: Amrita appears
    messages_error.clear()
    messages_info.clear()
    win_tch_correct = FaceRegisterWindow(t_dash, "STU_AMRITA", "Amrita", db)
    win_tch_correct.captured_encoding = face_amrita_v2
    win_tch_correct.save_face()
    win_tch_correct.destroy()
    
    assert len(messages_error) == 0, f"Teacher portal must accept Amrita: {messages_error}"
    assert len(messages_info) > 0
    print("Test D2 Passed: Teacher Portal accepted correct student.")

    # ----------------------------------------------------
    # TEST E: DIFFERENT STUDENTS (ANANDI & ROHAN)
    # First-time registration for Anandi and Rohan
    # ----------------------------------------------------
    print("\n--- TEST E: DIFFERENT STUDENTS (FIRST-TIME & UPDATE) ---")
    # First-time Anandi
    messages_error.clear()
    messages_info.clear()
    win_anandi_first = FaceRegisterWindow(root, "STU_ANANDI", "Anandi", db)
    win_anandi_first.captured_encoding = face_anandi
    win_anandi_first.save_face()
    win_anandi_first.destroy()
    assert len(messages_error) == 0
    assert len(messages_info) > 0
    print("Test E1 Passed: Anandi first-time registration succeeded.")
    
    # First-time College Student Rohan
    messages_error.clear()
    messages_info.clear()
    win_rohan_first = FaceRegisterWindow(root, "STU_ROHAN", "Rohan", db)
    win_rohan_first.captured_encoding = face_rohan
    win_rohan_first.save_face()
    win_rohan_first.destroy()
    assert len(messages_error) == 0
    assert len(messages_info) > 0
    print("Test E2 Passed: Rohan (College) first-time registration succeeded.")
    
    # Cross-verify: Rohan presents face for Anandi -> Must reject
    messages_error.clear()
    messages_info.clear()
    win_anandi_mismatch = FaceRegisterWindow(root, "STU_ANANDI", "Anandi", db)
    win_anandi_mismatch.captured_encoding = face_rohan
    win_anandi_mismatch.save_face()
    win_anandi_mismatch.destroy()
    assert len(messages_error) > 0
    assert "You are not Anandi" in messages_error[0][1]
    print("Test E3 Passed: Rohan's face presented for Anandi correctly rejected.")

    try:
        root.destroy()
    except Exception:
        pass

    try:
        if os.path.exists(db_file):
            os.remove(db_file)
    except Exception:
        pass

    print("\n=========================================================")
    print("ALL TESTS (A, B, C, D, E) PASSED WITH 100% SUCCESS!")
    print("=========================================================")

if __name__ == '__main__':
    test_face_registration_and_verification_rules()
