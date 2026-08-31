import os
import sys
import tkinter as tk
import time
from tkinter import messagebox
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DBManager
from gui.register import AccountRegistrationWindow
from gui.student_forms import StudentFormDialog

messagebox.showinfo = lambda *a, **k: None
messagebox.showwarning = lambda *a, **k: None
messagebox.showerror = lambda *a, **k: None

def test_no_parent_account_created():
    print("=== TESTING: NO PARENT ACCOUNT CREATION ON STUDENT REGISTRATION/CREATE ===")
    
    db_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f"test_no_parent_{int(time.time())}.db")
    if os.path.exists(db_file):
        os.remove(db_file)
    db = DBManager(db_file)
    
    root = tk.Tk()
    root.withdraw()
    
    # 1. Register a student via AccountRegistrationWindow
    reg_win = AccountRegistrationWindow(root, db, role="Student")
    
    reg_win._entries["username"].insert(0, "student_neha")
    reg_win._entries["password"].insert(0, "Pass1234")
    reg_win._entries["confirm_password"].insert(0, "Pass1234")
    reg_win._entries["favourite_person"].insert(0, "Mother")
    reg_win._entries["name"].insert(0, "Neha Singh")
    reg_win._entries["email"].insert(0, "neha@example.com")
    reg_win._entries["phone"].insert(0, "9876543210")
    reg_win._entries["dob"].delete(0, tk.END)
    reg_win._entries["dob"].insert(0, "2006-03-15")
    reg_win._entries["address"].insert(0, "Delhi, India")
    
    # Dynamic School fields
    reg_win._entries["school_name"].insert(0, "SKV No. 1")
    reg_win._entries["department"].insert(0, "Science")
    reg_win._entries["current_class"].delete(0, tk.END)
    reg_win._entries["current_class"].insert(0, "11")
    reg_win._entries["section"].delete(0, tk.END)
    reg_win._entries["section"].insert(0, "A")
    reg_win._entries["roll_number"].insert(0, "33")
    reg_win._entries["admission_date"].delete(0, tk.END)
    reg_win._entries["admission_date"].insert(0, "2024-07-01")
    reg_win._entries["student_id"].insert(0, "STU_NEHA_01")
    
    # Parent details filled by student
    reg_win._entries["father_name"].insert(0, "Vikram Singh")
    reg_win._entries["parent_phone"].insert(0, "9876500111")
    reg_win._entries["mother_name"].insert(0, "Anita Singh")
    reg_win._entries["mother_phone"].insert(0, "9876500222")
    reg_win._entries["study_hours"].delete(0, tk.END)
    reg_win._entries["study_hours"].insert(0, "3.5")
    
    # Register dummy face encoding for verification
    db.save_face_encoding("STU_NEHA_01", np.zeros(128))
    reg_win.student_face_registered = True
    
    # Complete student registration
    reg_win.do_register()
    reg_win.destroy()
    
    # Verify in DB: ONLY Student user exists, NO Parent user account exists!
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        print(f"Users in DB after Student Registration: {[dict(u) for u in users]}")
        
        # Check roles in users table
        roles = [u["role"] for u in users]
        assert "Student" in roles, "Student user account was not created!"
        assert "Parent" not in roles, "ERROR: A Parent user account was created when student registered!"
        assert len(users) == 1, f"Expected exactly 1 user account (Student), found {len(users)}!"
        
    print("[PASS] TEST 1: Creating student account in registration form created ONLY 1 Student user and ZERO Parent accounts!")
    
    # 2. Add another student via StudentFormDialog
    dialog = StudentFormDialog(root, db)
    dialog.entry_sid.insert(0, "STU_RAHUL_02")
    dialog.entry_name.insert(0, "Rahul Kumar")
    dialog.entry_dob.insert(0, "2005-01-01")
    dialog.entry_phone.insert(0, "9876511111")
    dialog.entry_email.insert(0, "rahul2@example.com")
    dialog.entry_school_name.insert(0, "SKV No. 1")
    dialog.entry_dept.insert(0, "PCB")
    dialog.entry_class.insert(0, "12")
    dialog.entry_section.insert(0, "B")
    dialog.entry_father.insert(0, "Suresh Kumar")
    dialog.entry_parent_phone.insert(0, "9876599888")
    dialog.save_student()
    dialog.destroy()
    
    # Verify in DB again
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE role = 'Parent'")
        parent_users = cursor.fetchall()
        assert len(parent_users) == 0, f"ERROR: Found {len(parent_users)} Parent users after StudentFormDialog save!"
        
    print("[PASS] TEST 2: StudentFormDialog created/saved student without creating any Parent user accounts!")
    
    try:
        root.destroy()
    except Exception:
        pass
        
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass
            
    print("\nALL NO-PARENT-ACCOUNT TESTS PASSED 100%!")

if __name__ == "__main__":
    test_no_parent_account_created()
