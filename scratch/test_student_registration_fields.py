import os
import sys
import tkinter as tk
import time
from tkinter import messagebox

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DBManager
from gui.register import AccountRegistrationWindow
from gui.student_forms import StudentFormDialog

messagebox.showinfo = lambda *a, **k: None
messagebox.showwarning = lambda *a, **k: None
messagebox.showerror = lambda *a, **k: None

def test_registration_window():
    print("=== TESTING REGISTRATION WINDOW STUDENT FIELDS ===")
    db_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f"test_reg_fields_{int(time.time())}.db")
    if os.path.exists(db_file):
        os.remove(db_file)
    db = DBManager(db_file)
    
    root = tk.Tk()
    root.withdraw()
    
    # 1. Open Student Registration Form
    reg_win = AccountRegistrationWindow(root, db, role="Student")
    
    # Verify School Name & Department fields are in _entries
    assert "school_name" in reg_win._entries, "Field 'school_name' missing in Student Registration entries!"
    assert "department" in reg_win._entries, "Field 'department' missing in Student Registration entries!"
    
    # Fill in registration data
    reg_win._entries["username"].insert(0, "student_skv_01")
    reg_win._entries["password"].insert(0, "pass1234")
    reg_win._entries["confirm_password"].insert(0, "pass1234")
    reg_win._entries["favourite_person"].insert(0, "Teacher")
    reg_win._entries["name"].insert(0, "Rohan Verma")
    reg_win._entries["email"].insert(0, "rohan@example.com")
    reg_win._entries["phone"].insert(0, "9876543210")
    reg_win._entries["dob"].delete(0, tk.END)
    reg_win._entries["dob"].insert(0, "2006-05-10")
    reg_win._entries["address"].insert(0, "Delhi, India")
    
    # Dynamic School fields
    reg_win._entries["school_name"].insert(0, "SKV No. 1")
    reg_win._entries["department"].insert(0, "Science")
    reg_win._entries["current_class"].delete(0, tk.END)
    reg_win._entries["current_class"].insert(0, "11")
    reg_win._entries["section"].delete(0, tk.END)
    reg_win._entries["section"].insert(0, "A")
    reg_win._entries["roll_number"].insert(0, "22")
    reg_win._entries["admission_date"].delete(0, tk.END)
    reg_win._entries["admission_date"].insert(0, "2024-07-01")
    reg_win._entries["student_id"].insert(0, "STU_SKV_01")
    
    # Parent details
    reg_win._entries["father_name"].insert(0, "Mahesh Verma")
    reg_win._entries["parent_phone"].insert(0, "9876599999")
    reg_win._entries["study_hours"].delete(0, tk.END)
    reg_win._entries["study_hours"].insert(0, "3.0")
    
    # Register face in DB mock
    import numpy as np
    dummy_encoding = np.zeros(128)
    db.save_face_encoding("STU_SKV_01", dummy_encoding)
    reg_win.student_face_registered = True
    
    # Submit registration
    reg_win.do_register()
    
    # Verify student saved in DB
    student = db.get_student("STU_SKV_01")
    assert student is not None, "Student record was not saved to DB"
    assert student["school_name"] == "SKV No. 1", f"Expected 'SKV No. 1', got '{student['school_name']}'"
    assert student["department"] == "Science", f"Expected 'Science', got '{student['department']}'"
    print("[PASS] Registration window created account with School Name 'SKV No. 1' and Department 'Science'!")
    
    # Verify opening Edit Student loads both
    edit_dialog = StudentFormDialog(root, db, student_id="STU_SKV_01")
    assert edit_dialog.entry_school_name.get() == "SKV No. 1", f"Edit dialog failed to load School Name: {edit_dialog.entry_school_name.get()}"
    assert edit_dialog.entry_dept.get() == "Science", f"Edit dialog failed to load Department: {edit_dialog.entry_dept.get()}"
    print("[PASS] Edit Student dialog correctly loaded School Name and Department from the registered account!")
    
    # Edit Department to PCB and save
    edit_dialog.entry_dept.delete(0, tk.END)
    edit_dialog.entry_dept.insert(0, "PCB")
    edit_dialog.save_student()
    edit_dialog.destroy()
    
    # Reopen Edit Student to verify persistence
    reopen_dialog = StudentFormDialog(root, db, student_id="STU_SKV_01")
    assert reopen_dialog.entry_school_name.get() == "SKV No. 1"
    assert reopen_dialog.entry_dept.get() == "PCB"
    reopen_dialog.destroy()
    print("[PASS] Edit Department to 'PCB' persisted and correctly reloaded!")
    
    try:
        reg_win.destroy()
        root.destroy()
    except Exception:
        pass
        
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass
            
    print("ALL REGISTRATION FLOW TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_registration_window()
