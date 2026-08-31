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

messages_info = []
messages_warning = []
messages_error = []

messagebox.showinfo = lambda title, msg: messages_info.append((title, str(msg)))
messagebox.showwarning = lambda title, msg: messages_warning.append((title, str(msg)))
messagebox.showerror = lambda title, msg: messages_error.append((title, str(msg)))

def test_teacher_face_identity_matching():
    print("=== STARTING TEACHER PORTAL REGISTER FACE IDENTITY MATCHING TESTS ===")
    
    db_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f"test_tch_reg_{int(time.time())}.db")
    if os.path.exists(db_file):
        os.remove(db_file)
    db = DBManager(db_file)
    
    root = tk.Tk()
    root.withdraw()
    
    FaceRegisterWindow._start_camera = lambda self: None
    
    # 1. Setup multiple students: Amrita, Anandi, and Rohan
    u_amrita = db.create_user("amrita", "Pass1234", "Student")
    db.add_student({
        "student_id": "STU_AMRITA",
        "name": "Amrita",
        "education_type": "School",
        "school_name": "Delhi Public School",
        "current_class": "10",
        "section": "A"
    }, u_amrita)
    
    u_anandi = db.create_user("anandi", "Pass1234", "Student")
    db.add_student({
        "student_id": "STU_ANANDI",
        "name": "Anandi",
        "education_type": "School",
        "school_name": "Delhi Public School",
        "current_class": "10",
        "section": "B"
    }, u_anandi)
    
    u_rohan = db.create_user("rohan", "Pass1234", "Student")
    db.add_student({
        "student_id": "STU_ROHAN",
        "name": "Rohan",
        "education_type": "College",
        "college_name": "IIT Delhi",
        "course": "B.Tech",
        "semester": "Semester 4"
    }, u_rohan)
    
    # Unique face matrices for each student
    np.random.seed(111)
    face_amrita = (np.random.rand(100, 100) * 255).astype(np.uint8)
    np.random.seed(222)
    face_anandi = (np.random.rand(100, 100) * 255).astype(np.uint8)
    np.random.seed(333)
    face_rohan = (np.random.rand(100, 100) * 255).astype(np.uint8)
    
    # Initial Face Registration for each student
    db.save_face_encoding("STU_AMRITA", pickle.dumps(face_amrita))
    db.save_face_encoding("STU_ANANDI", pickle.dumps(face_anandi))
    db.save_face_encoding("STU_ROHAN", pickle.dumps(face_rohan))
    
    print("[SETUP] 3 students with registered faces created in database.")
    
    # ----------------------------------------------------
    # TEST 1: Teacher Portal -> Select Amrita -> Show Amrita's face
    # ----------------------------------------------------
    messages_error.clear()
    messages_info.clear()
    
    win_amrita_own = FaceRegisterWindow(root, "STU_AMRITA", "Amrita", db)
    win_amrita_own.captured_encoding = face_amrita
    win_amrita_own.save_face()
    win_amrita_own.destroy()
    
    assert len(messages_error) == 0, f"Expected no error for Amrita's own face, got {messages_error}"
    assert len(messages_info) > 0, "Expected success dialog for Amrita"
    print("[PASS] TEST 1: Teacher Portal -> Selected Amrita + Amrita Face -> Allowed & Saved Successfully!")
    
    # ----------------------------------------------------
    # TEST 2: Teacher Portal -> Select Amrita -> Show Anandi's face (Different Person)
    # ----------------------------------------------------
    messages_error.clear()
    messages_info.clear()
    
    win_amrita_diff = FaceRegisterWindow(root, "STU_AMRITA", "Amrita", db)
    win_amrita_diff.captured_encoding = face_anandi
    win_amrita_diff.save_face()
    win_amrita_diff.destroy()
    
    assert len(messages_error) > 0, "Expected error when different person face presented!"
    expected_msg = "You are not Amrita. This face does not match the registered face."
    assert expected_msg in messages_error[0][1], f"Expected '{expected_msg}', got '{messages_error[0][1]}'"
    
    # Confirm DB face for Amrita was NOT changed
    stored_amrita = pickle.loads(db.get_face_encoding("STU_AMRITA"))
    assert np.array_equal(stored_amrita, face_amrita), "Amrita's original face must remain unchanged in DB!"
    print(f"[PASS] TEST 2: Teacher Portal -> Selected Amrita + Anandi Face -> Rejected with exact message: '{messages_error[0][1]}'")
    
    # ----------------------------------------------------
    # TEST 3: Teacher Portal -> Select Anandi -> Show Rohan's face (Different Person)
    # ----------------------------------------------------
    messages_error.clear()
    messages_info.clear()
    
    win_anandi_diff = FaceRegisterWindow(root, "STU_ANANDI", "Anandi", db)
    win_anandi_diff.captured_encoding = face_rohan
    win_anandi_diff.save_face()
    win_anandi_diff.destroy()
    
    assert len(messages_error) > 0, "Expected error when Rohan face presented for Anandi!"
    expected_msg_anandi = "You are not Anandi. This face does not match the registered face."
    assert expected_msg_anandi in messages_error[0][1], f"Expected '{expected_msg_anandi}', got '{messages_error[0][1]}'"
    print(f"[PASS] TEST 3: Teacher Portal -> Selected Anandi + Rohan Face -> Rejected with exact message: '{messages_error[0][1]}'")
    
    # ----------------------------------------------------
    # TEST 4: Teacher Portal -> Select Anandi -> Show Anandi's Own Face
    # ----------------------------------------------------
    messages_error.clear()
    messages_info.clear()
    
    win_anandi_own = FaceRegisterWindow(root, "STU_ANANDI", "Anandi", db)
    win_anandi_own.captured_encoding = face_anandi
    win_anandi_own.save_face()
    win_anandi_own.destroy()
    
    assert len(messages_error) == 0, f"Expected no error for Anandi's own face, got {messages_error}"
    assert len(messages_info) > 0, "Expected success dialog for Anandi"
    print("[PASS] TEST 4: Teacher Portal -> Selected Anandi + Anandi Face -> Allowed & Saved Successfully!")
    
    # ----------------------------------------------------
    # TEST 5: Teacher Portal -> Select Rohan -> Show Rohan's Own Face
    # ----------------------------------------------------
    messages_error.clear()
    messages_info.clear()
    
    win_rohan_own = FaceRegisterWindow(root, "STU_ROHAN", "Rohan", db)
    win_rohan_own.captured_encoding = face_rohan
    win_rohan_own.save_face()
    win_rohan_own.destroy()
    
    assert len(messages_error) == 0, f"Expected no error for Rohan's own face, got {messages_error}"
    assert len(messages_info) > 0, "Expected success dialog for Rohan"
    print("[PASS] TEST 5: Teacher Portal -> Selected Rohan + Rohan Face -> Allowed & Saved Successfully!")

    try:
        root.destroy()
    except Exception:
        pass
    
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass
            
    print("\n=== ALL TEACHER PORTAL REGISTER FACE IDENTITY MATCHING TESTS PASSED 100% ===")

if __name__ == "__main__":
    test_teacher_face_identity_matching()
