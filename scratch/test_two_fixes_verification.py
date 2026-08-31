import os
import sys
import time
import pickle
import numpy as np
import tkinter as tk
from tkinter import ttk
from unittest.mock import patch, MagicMock

sys.path.insert(0, ".")
from database.db_manager import DBManager
from gui.register import AccountRegistrationWindow
from gui.admin_dashboard import IndividualStudentResultDialog

def run_tests():
    print("=== STARTING TESTS FOR THE 2 SPECIFIC FIXES ===")
    test_db_path = f"scratch/test_two_fixes_{int(time.time())}.db"
    db = DBManager(db_path=test_db_path)
    root = tk.Tk()
    root.withdraw()

    # -------------------------------------------------------------
    # FIX 1 & FIX 2 TEST: SCHOOL STUDENT REGISTRATION
    # -------------------------------------------------------------
    print("\n--- Testing School Student Registration (Roll Number & No Parent Account Creation) ---")
    reg_win = AccountRegistrationWindow(root, db, "Student")
    assert reg_win.combo_edu_type.get() == "School"

    # Verify Roll Number field exists in School registration
    assert "roll_number" in reg_win._entries, "Roll Number field MUST exist in School student registration!"

    # Fill School student registration fields with Roll Number = 25
    reg_win._entries["username"].insert(0, "aarav_school")
    reg_win._entries["password"].insert(0, "Password123")
    reg_win._entries["confirm_password"].insert(0, "Password123")
    reg_win._entries["favourite_person"].insert(0, "APJ Kalam")
    reg_win._entries["name"].insert(0, "Aarav Sharma")
    reg_win._entries["email"].insert(0, "aarav@school.edu")
    reg_win._entries["phone"].insert(0, "9876543210")
    reg_win._entries["dob"].delete(0, tk.END)
    reg_win._entries["dob"].insert(0, "2006-05-15")
    reg_win._entries["address"].insert(0, "123 School Lane")
    reg_win._entries["father_name"].insert(0, "Rajesh Sharma")
    reg_win._entries["parent_phone"].insert(0, "9876500001")
    reg_win._entries["study_hours"].delete(0, tk.END)
    reg_win._entries["study_hours"].insert(0, "4.0")

    reg_win._entries["school_name"].insert(0, "Greenwood High School")
    reg_win._entries["current_class"].insert(0, "10")
    reg_win._entries["section"].insert(0, "B")
    reg_win._entries["roll_number"].insert(0, "25")
    reg_win._entries["admission_date"].delete(0, tk.END)
    reg_win._entries["admission_date"].insert(0, "2024-04-01")
    reg_win._entries["student_id"].insert(0, "SCH_AARAV_25")

    # Register face encoding for student
    dummy_face = np.random.uniform(0, 1, (100, 100)).astype(np.float32)
    db.save_face_encoding("SCH_AARAV_25", pickle.dumps(dummy_face))
    reg_win.student_face_registered = True

    # Complete student registration
    with patch("tkinter.messagebox.showinfo"), \
         patch.object(reg_win, "_finish_registration") as mock_finish:
        reg_win.do_register()
        assert mock_finish.called, "Student registration should finish successfully!"

    reg_win.destroy()

    # 1. VERIFY STUDENT ACCOUNT IS CREATED
    stu_auth = db.authenticate_user("aarav_school", "Password123", expected_role="Student")
    assert stu_auth is not None and stu_auth.get("success") is not False, "Student account must be created and able to log in!"
    stu_rec = db.get_student("SCH_AARAV_25")
    assert stu_rec is not None, "Student record must exist in database!"
    assert stu_rec["name"] == "Aarav Sharma"
    assert stu_rec["father_name"] == "Rajesh Sharma"
    assert stu_rec["roll_number"] == "25", f"Roll number must be 25, got {stu_rec.get('roll_number')}"
    print("[PASS] Test 1: School Student account created with Roll Number = 25 and Parent details saved in Student record.")

    # 2. VERIFY NO PARENT ACCOUNT / PARENT LOGIN RECORD WAS CREATED
    with db.get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE role = 'Parent'")
        parent_users = c.fetchall()
        assert len(parent_users) == 0, f"No Parent user accounts should be created when student registers! Found: {parent_users}"

    # Verify parent phone or father name cannot log in as parent
    p_login_phone = db.authenticate_user("9876500001", "Password123", expected_role="Parent")
    assert p_login_phone.get("success") is False, "Parent should NOT be able to log in using phone before registering!"
    p_login_name = db.authenticate_user("Rajesh Sharma", "Password123", expected_role="Parent")
    assert p_login_name.get("success") is False, "Parent should NOT be able to log in using name before registering!"
    print("[PASS] Test 2: NO Parent user account, ID, or login credentials created from Student registration.")

    # 3. VERIFY ADMIN RESULT DASHBOARD DISPLAYS ROLL NUMBER: 25
    result_dialog = IndividualStudentResultDialog(root, db, "SCH_AARAV_25")
    assert result_dialog.student.get("roll_number") == "25"
    
    # Check widgets in result dialog
    labels_text = []
    def collect_labels(widget):
        if isinstance(widget, (ttk.Label, tk.Label)):
            labels_text.append(widget.cget("text"))
        for ch in widget.winfo_children():
            collect_labels(ch)

    collect_labels(result_dialog)
    assert "25" in labels_text, f"Result Dashboard MUST display Roll Number: 25! Found labels: {labels_text}"
    assert "Roll Number:" in labels_text
    result_dialog.destroy()
    print("[PASS] Test 3: Admin Result Dashboard correctly displays saved Roll Number: 25 (NOT N/A).")

    # -------------------------------------------------------------
    # FIX 1 TEST PART B: PARENT INDEPENDENTLY CREATES ACCOUNT
    # -------------------------------------------------------------
    print("\n--- Testing Parent Independent Registration Flow ---")
    parent_reg_win = AccountRegistrationWindow(root, db, "Parent")
    parent_reg_win._entries["username"].insert(0, "rajesh_parent")
    parent_reg_win._entries["password"].insert(0, "ParentSecret123")
    parent_reg_win._entries["confirm_password"].insert(0, "ParentSecret123")
    parent_reg_win._entries["favourite_person"].insert(0, "Gandhiji")
    parent_reg_win._entries["name"].insert(0, "Rajesh Sharma")
    parent_reg_win._entries["phone"].insert(0, "9876500001")
    parent_reg_win._entries["email"].insert(0, "rajesh@gmail.com")
    parent_reg_win._entries["address"].insert(0, "123 School Lane")

    # Link child slot
    assert len(parent_reg_win.child_entries) >= 1
    slot = parent_reg_win.child_entries[0]
    slot["entry_sid"].insert(0, "SCH_AARAV_25")
    parent_reg_win._verify_child_slot(0)
    assert slot["verified_student"] is not None

    with patch("tkinter.messagebox.showinfo"), \
         patch.object(parent_reg_win, "_finish_registration") as mock_p_finish:
        parent_reg_win.do_register()
        assert mock_p_finish.called

    parent_reg_win.destroy()

    # Now Parent CAN authenticate with their chosen credentials
    p_auth = db.authenticate_user("rajesh_parent", "ParentSecret123", expected_role="Parent")
    assert p_auth is not None and p_auth.get("success") is not False, "Parent must be able to log in after registering!"
    print("[PASS] Test 4: Parent independent registration works normally and Parent can now log in.")

    # -------------------------------------------------------------
    # FIX 2 TEST PART B: COLLEGE STUDENT (NO ROLL NUMBER)
    # -------------------------------------------------------------
    print("\n--- Testing College Student Registration (No Roll Number) ---")
    col_reg_win = AccountRegistrationWindow(root, db, "Student")
    col_reg_win.combo_edu_type.set("College")
    col_reg_win._on_edu_type_changed()

    # Verify Roll Number field does NOT exist in College registration
    assert "roll_number" not in col_reg_win._entries, "Roll Number MUST NOT exist for College students!"

    col_reg_win._entries["username"].insert(0, "priya_college")
    col_reg_win._entries["password"].insert(0, "CollegePass123")
    col_reg_win._entries["confirm_password"].insert(0, "CollegePass123")
    col_reg_win._entries["favourite_person"].insert(0, "Mother")
    col_reg_win._entries["name"].insert(0, "Priya Nair")
    col_reg_win._entries["email"].insert(0, "priya@college.edu")
    col_reg_win._entries["phone"].insert(0, "9112233445")
    col_reg_win._entries["dob"].delete(0, tk.END)
    col_reg_win._entries["dob"].insert(0, "2003-08-20")
    col_reg_win._entries["address"].insert(0, "456 College Road")
    col_reg_win._entries["father_name"].insert(0, "Suresh Nair")
    col_reg_win._entries["parent_phone"].insert(0, "9112200002")
    col_reg_win._entries["study_hours"].delete(0, tk.END)
    col_reg_win._entries["study_hours"].insert(0, "5.0")

    col_reg_win._entries["college_name"].insert(0, "National Engineering College")
    col_reg_win._entries["enrollment_number"].insert(0, "ENR_PRIYA_99")
    col_reg_win._entries["course"].insert(0, "B.Tech Computer Science")
    col_reg_win._entries["semester"].insert(0, "Semester 5")
    col_reg_win._entries["admission_date"].delete(0, tk.END)
    col_reg_win._entries["admission_date"].insert(0, "2022-08-01")

    # Register face encoding for college student
    dummy_face_col = np.random.uniform(0, 1, (100, 100)).astype(np.float32)
    db.save_face_encoding("ENR_PRIYA_99", pickle.dumps(dummy_face_col))
    col_reg_win.student_face_registered = True

    with patch("tkinter.messagebox.showinfo"), \
         patch.object(col_reg_win, "_finish_registration") as mock_col_finish:
        col_reg_win.do_register()
        assert mock_col_finish.called

    col_reg_win.destroy()

    col_rec = db.get_student("ENR_PRIYA_99")
    assert col_rec is not None
    assert col_rec["enrollment_number"] == "ENR_PRIYA_99"
    assert col_rec.get("roll_number") in ["", None]

    col_result_dialog = IndividualStudentResultDialog(root, db, "ENR_PRIYA_99")
    assert col_result_dialog.student.get("enrollment_number") == "ENR_PRIYA_99"
    col_result_dialog.destroy()
    print("[PASS] Test 5: College student registration and dashboard flow intact without Roll Number.")

    root.destroy()
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except Exception:
            pass

    print("\n=== ALL 2 FIXES VERIFIED AND PASSED 100%! ===")

if __name__ == "__main__":
    run_tests()
