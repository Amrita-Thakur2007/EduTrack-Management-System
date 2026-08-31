import os
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DBManager

# Mock messagebox for non-interactive test run
last_error = []
last_warning = []
last_info = []

def mock_showerror(title, message):
    last_error.append((title, message))

def mock_showwarning(title, message):
    last_warning.append((title, message))

def mock_showinfo(title, message):
    last_info.append((title, message))

messagebox.showerror = mock_showerror
messagebox.showwarning = mock_showwarning
messagebox.showinfo = mock_showinfo

from gui.register import AccountRegistrationWindow
from gui.login import LoginWindow

def run_tests():
    print("=== STARTING REGISTRATION USERNAME FIELD VERIFICATION ===")

    db_path = f"scratch/test_reg_usr_{int(time.time())}.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = DBManager(db_path=db_path)

    root = tk.Tk()
    root.withdraw()

    # 1. Verify Username field presence & order in Student registration
    reg_window = AccountRegistrationWindow(root, db, role="Student")
    assert "username" in reg_window._entries, "Username field MUST exist in Student registration form entries!"
    assert "password" in reg_window._entries, "Password field MUST exist in Student registration form entries!"
    assert "confirm_password" in reg_window._entries, "Confirm Password field MUST exist in Student registration form entries!"
    
    usr_widget = reg_window._entries["username"]
    assert isinstance(usr_widget, ttk.Entry), "Username field MUST be a ttk.Entry widget!"
    print("TEST 1 PASS: Username input field added to Account Credentials section of Registration form.")

    # 2. Test empty username registration validation
    last_warning.clear()
    reg_window._entries["username"].delete(0, tk.END)
    reg_window._entries["password"].insert(0, "Password123")
    reg_window._entries["confirm_password"].insert(0, "Password123")
    reg_window._entries["favourite_person"].insert(0, "Hero")
    reg_window.do_register()
    assert len(last_warning) > 0, "Registration with empty username must trigger a validation warning!"
    print("TEST 2 PASS: Empty username registration correctly blocked.")

    # 3. Test successful registration with custom Username: StudentUser1
    last_warning.clear()
    last_info.clear()
    
    reg_window._entries["username"].insert(0, "StudentUser1")
    reg_window._entries["name"].insert(0, "Amit Kumar")
    reg_window._entries["email"].insert(0, "amit@example.com")
    reg_window._entries["phone"].insert(0, "9876543210")
    reg_window._entries["dob"].delete(0, tk.END)
    reg_window._entries["dob"].insert(0, "2005-05-15")
    reg_window._entries["address"].insert(0, "123 Main St")
    reg_window._entries["father_name"].insert(0, "Father Kumar")
    reg_window._entries["parent_phone"].insert(0, "9876543211")
    reg_window._entries["study_hours"].delete(0, tk.END)
    reg_window._entries["study_hours"].insert(0, "4.0")
    
    # Fill School specific fields
    reg_window._entries["school_name"].insert(0, "Delhi Public School")
    reg_window._entries["current_class"].insert(0, "10")
    reg_window._entries["section"].insert(0, "A")
    reg_window._entries["admission_date"].delete(0, tk.END)
    reg_window._entries["admission_date"].insert(0, "2024-04-01")
    reg_window._entries["student_id"].insert(0, "STU_SCH_101")

    # Register face
    import pickle, numpy as np
    dummy_face = np.random.uniform(0, 1, (100, 100)).astype(np.float32)
    db.save_face_encoding("STU_SCH_101", pickle.dumps(dummy_face))
    reg_window.student_face_registered = True

    reg_window.do_register()

    assert len(last_info) > 0, f"Registration failed! Warnings/Errors: {last_warning} {last_error}"
    
    # Verify DB user record
    auth_res = db.authenticate_user("StudentUser1", "Password123", expected_role="Student")
    assert auth_res is not None, f"Failed to authenticate newly registered Username StudentUser1: {auth_res}"
    assert auth_res["username"].lower() == "studentuser1", f"Username mismatch in auth_res: {auth_res}"
    print("TEST 3 PASS: Student registered successfully with Username StudentUser1 & saved in database.")

    reg_window.destroy()

    # 4. Test duplicate username validation on another registration window
    reg_window2 = AccountRegistrationWindow(root, db, role="Student")
    reg_window2._entries["username"].insert(0, "StudentUser1") # Duplicate username
    reg_window2._entries["password"].insert(0, "Password123")
    reg_window2._entries["confirm_password"].insert(0, "Password123")
    reg_window2._entries["favourite_person"].insert(0, "Hero")
    
    reg_window2._entries["name"].insert(0, "Second Student")
    reg_window2._entries["email"].insert(0, "second@example.com")
    reg_window2._entries["phone"].insert(0, "9876543222")
    reg_window2._entries["dob"].delete(0, tk.END)
    reg_window2._entries["dob"].insert(0, "2005-05-15")
    reg_window2._entries["address"].insert(0, "456 Side St")
    reg_window2._entries["father_name"].insert(0, "Father Second")
    reg_window2._entries["parent_phone"].insert(0, "9876543223")
    reg_window2._entries["study_hours"].delete(0, tk.END)
    reg_window2._entries["study_hours"].insert(0, "4.0")
    
    reg_window2._entries["school_name"].insert(0, "Delhi Public School")
    reg_window2._entries["current_class"].insert(0, "10")
    reg_window2._entries["section"].insert(0, "A")
    reg_window2._entries["admission_date"].delete(0, tk.END)
    reg_window2._entries["admission_date"].insert(0, "2024-04-01")
    reg_window2._entries["student_id"].insert(0, "STU_SCH_102")

    last_error.clear()
    reg_window2.do_register()

    assert len(last_error) > 0, "Duplicate username attempt MUST be blocked with an error dialog!"
    assert "already exists" in last_error[0][1], f"Unexpected error message: {last_error[0][1]}"
    print("TEST 4 PASS: Duplicate username registration blocked with clear error message.")

    reg_window2.destroy()

    # 5. Test Login with newly created Username + Password
    login_win = LoginWindow(root, db, initial_role="Student")
    login_win.entry_username.insert(0, "StudentUser1")
    login_win.entry_password.insert(0, "Password123")
    
    auth_login = db.authenticate_user("StudentUser1", "Password123", expected_role="Student")
    assert auth_login is not None, "Login failed for registered Username StudentUser1!"
    assert auth_login["role"] == "Student", "Incorrect user session role after login!"
    print("TEST 5 PASS: Newly registered Username + Password successfully logs in to Student Portal.")

    login_win.destroy()
    root.quit()
    root.destroy()

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

    print("\n=== ALL REGISTRATION USERNAME FIELD VERIFICATIONS PASSED 100% ===")

if __name__ == "__main__":
    run_tests()
