import os
import sys
import time
import pickle
import numpy as np
import tkinter as tk
from unittest.mock import MagicMock, patch

sys.path.insert(0, ".")
from database.db_manager import DBManager
from gui.register import AccountRegistrationWindow

def run_tests():
    print("=== STARTING STUDENT FACE REGISTRATION MANDATORY TESTS ===")
    test_db_path = f"scratch/test_stu_face_reg_{int(time.time())}.db"
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except Exception:
            pass

    db = DBManager(db_path=test_db_path)
    root = tk.Tk()
    root.withdraw()

    # TEST CASE 1: Attempt registration without face registered
    reg_win = AccountRegistrationWindow(root, db, "Student")
    
    # Fill in entries for school student
    reg_win._entries["username"].insert(0, "rohit_sharma")
    reg_win._entries["password"].insert(0, "Secret123")
    reg_win._entries["confirm_password"].insert(0, "Secret123")
    reg_win._entries["favourite_person"].insert(0, "Sachin")
    reg_win._entries["name"].insert(0, "Rohit Sharma")
    reg_win._entries["email"].insert(0, "rohit@school.edu")
    reg_win._entries["phone"].insert(0, "9876543210")
    reg_win._entries["dob"].delete(0, tk.END)
    reg_win._entries["dob"].insert(0, "2005-04-30")
    reg_win._entries["address"].insert(0, "Mumbai, India")
    reg_win._entries["father_name"].insert(0, "Gurunath Sharma")
    reg_win._entries["parent_phone"].insert(0, "9876543211")
    reg_win._entries["study_hours"].delete(0, tk.END)
    reg_win._entries["study_hours"].insert(0, "4.0")
    reg_win._entries["school_name"].insert(0, "Swami Vivekanand High School")
    reg_win._entries["student_id"].insert(0, "SCH_ROHIT_45")
    reg_win._entries["current_class"].insert(0, "11")
    reg_win._entries["section"].insert(0, "A")
    reg_win._entries["roll_number"].insert(0, "45")
    reg_win._entries["admission_date"].insert(0, "2024-04-01")

    # Mock messagebox
    with patch("tkinter.messagebox.showerror") as mock_err:
        reg_win.do_register()
        assert mock_err.called, "Must show error when face is not registered!"
        err_title, err_msg = mock_err.call_args[0]
        assert "Face Registration Required" in err_title
        assert "First you doing face register" in err_msg
        
        # Check that user and student were NOT created
        assert not db.is_username_exists("rohit_sharma"), "User should NOT be created without face registration!"
        assert db.get_student("SCH_ROHIT_45") is None, "Student profile should NOT be created without face registration!"
        print(f"[PASS] Test 1: Error shown when submitting without face: '{err_msg.splitlines()[0]}'")

    # Case 1b: Student clicks 'REGISTER YOUR FACE' and saves face
    with patch("face_attendance.face_registration.FaceRegisterWindow") as mock_face_win:
        def complete_face_reg(parent, sid, name, db_m, on_complete, **kwargs):
            dummy_face = np.random.uniform(0, 1, (100, 100)).astype(np.float32)
            db.save_face_encoding(sid, pickle.dumps(dummy_face))
            on_complete(True)

        mock_face_win.side_effect = complete_face_reg
        reg_win.register_student_face()
        assert reg_win.student_face_registered is True
        print("[PASS] Test 2: Face registered successfully via 'REGISTER YOUR FACE'.")

    # Case 1c: Now student submits registration
    with patch("tkinter.messagebox.showinfo"), \
         patch.object(reg_win, "_finish_registration") as mock_finish:
        reg_win.do_register()
        assert mock_finish.called, "Should finish registration after face is registered!"

    # Verify in DB
    u = db.authenticate_user("rohit_sharma", "Secret123")
    assert u is not None, "User should be created after face is registered!"
    s = db.get_student("SCH_ROHIT_45")
    assert s is not None, "Student profile should be created after face is registered!"
    assert db.get_face_encoding("SCH_ROHIT_45") is not None, "Face encoding must exist in database!"
    print("[PASS] Test 3: Account created successfully after face is registered!")

    try:
        reg_win.destroy()
    except Exception:
        pass

    # TEST CASE 2: College Student
    reg_win2 = AccountRegistrationWindow(root, db, "Student")
    reg_win2.combo_edu_type.set("College")
    reg_win2._on_edu_type_changed()

    reg_win2._entries["username"].insert(0, "virat_kohli")
    reg_win2._entries["password"].insert(0, "King1818")
    reg_win2._entries["confirm_password"].insert(0, "King1818")
    reg_win2._entries["favourite_person"].insert(0, "Anushka")
    reg_win2._entries["name"].insert(0, "Virat Kohli")
    reg_win2._entries["email"].insert(0, "virat@college.edu")
    reg_win2._entries["phone"].insert(0, "9123456789")
    reg_win2._entries["dob"].delete(0, tk.END)
    reg_win2._entries["dob"].insert(0, "2002-11-05")
    reg_win2._entries["address"].insert(0, "Delhi, India")
    reg_win2._entries["father_name"].insert(0, "Prem Kohli")
    reg_win2._entries["parent_phone"].insert(0, "9123456780")
    reg_win2._entries["study_hours"].delete(0, tk.END)
    reg_win2._entries["study_hours"].insert(0, "5.0")
    reg_win2._entries["college_name"].insert(0, "Delhi University")
    reg_win2._entries["enrollment_number"].insert(0, "COL_VIRAT_18")
    reg_win2._entries["course"].insert(0, "B.Com")
    reg_win2._entries["semester"].insert(0, "Semester 4")
    reg_win2._entries["admission_date"].insert(0, "2023-08-01")

    with patch("tkinter.messagebox.showerror") as mock_err2:
        reg_win2.do_register()
        assert mock_err2.called
        assert not db.is_username_exists("virat_kohli")
        print("[PASS] Test 4: College student prevented from creating account before face registration.")

    with patch("face_attendance.face_registration.FaceRegisterWindow") as mock_face_win2:
        def complete_face_reg2(parent, sid, name, db_m, on_complete, **kwargs):
            dummy_face = np.random.uniform(0, 1, (100, 100)).astype(np.float32)
            db.save_face_encoding(sid, pickle.dumps(dummy_face))
            on_complete(True)

        mock_face_win2.side_effect = complete_face_reg2
        reg_win2.register_student_face()

    with patch("tkinter.messagebox.showinfo"), \
         patch.object(reg_win2, "_finish_registration") as mock_finish2:
        reg_win2.do_register()
        assert mock_finish2.called

        u2 = db.authenticate_user("virat_kohli", "King1818")
        assert u2 is not None
        s2 = db.get_student("COL_VIRAT_18")
        assert s2 is not None
        assert db.get_face_encoding("COL_VIRAT_18") is not None
        print("[PASS] Test 5: College student account created successfully after face is registered.")

    try:
        reg_win2.destroy()
        root.destroy()
    except Exception:
        pass

    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except Exception:
            pass

    print("=== ALL TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()
