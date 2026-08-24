import os
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DBManager

# Mock messagebox popups for non-interactive execution
messagebox.showinfo = lambda *a, **k: None
messagebox.showwarning = lambda *a, **k: None
messagebox.showerror = lambda *a, **k: None

from gui.register import AccountRegistrationWindow
from gui.teacher_forms import TeacherFormDialog

def run_tests():
    print("=== STARTING DEPARTMENT EDITABLE FIELD VERIFICATION ===")

    db_path = f"scratch/test_dept_{int(time.time())}.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = DBManager(db_path=db_path)

    root = tk.Tk()
    root.withdraw()

    # 1. Test Registration Window Teacher Department Field
    reg_window = AccountRegistrationWindow(root, db, role="Teacher")
    dept_widget_reg = reg_window._entries["department"]
    assert isinstance(dept_widget_reg, ttk.Entry), f"Registration Department widget must be ttk.Entry, got {type(dept_widget_reg)}"
    assert not isinstance(dept_widget_reg, ttk.Combobox), "Registration Department widget must NOT be a Combobox!"
    
    # Simulate user typing a custom Department
    dept_widget_reg.delete(0, tk.END)
    dept_widget_reg.insert(0, "Cyber Security & Quantum Computing")
    assert dept_widget_reg.get() == "Cyber Security & Quantum Computing"
    print("TEST 1 PASS: AccountRegistrationWindow Department field is a normal editable text input.")
    reg_window.destroy()

    # 2. Test TeacherFormDialog Department Field
    form_dialog = TeacherFormDialog(root, db)
    assert hasattr(form_dialog, 'entry_dept'), "TeacherFormDialog must have entry_dept widget!"
    assert isinstance(form_dialog.entry_dept, ttk.Entry), f"TeacherFormDialog Department widget must be ttk.Entry, got {type(form_dialog.entry_dept)}"
    assert not isinstance(form_dialog.entry_dept, ttk.Combobox), "TeacherFormDialog Department widget must NOT be a Combobox!"

    # Simulate user typing custom Department & saving
    form_dialog.entry_tid.insert(0, "TCH_CUSTOM_01")
    form_dialog.entry_name.insert(0, "Dr. Alan Turing")
    form_dialog.entry_phone.insert(0, "9876543210")
    form_dialog.entry_email.insert(0, "turing@university.edu")
    form_dialog.entry_dept.delete(0, tk.END)
    form_dialog.entry_dept.insert(0, "Theoretical Computer Science & Cryptography")

    form_dialog.save_teacher()

    # Verify custom department saved in database
    t_rec = db.get_teacher("TCH_CUSTOM_01")
    assert t_rec is not None, "Teacher record was not saved!"
    assert t_rec['department'] == "Theoretical Computer Science & Cryptography", f"Saved department mismatch: {t_rec['department']}"
    print("TEST 2 PASS: TeacherFormDialog Department field is a normal editable text input and saves typed values normally.")

    # 3. Test Loading Saved Custom Department in Edit Mode
    edit_dialog = TeacherFormDialog(root, db, teacher_id="TCH_CUSTOM_01")
    assert edit_dialog.entry_dept.get() == "Theoretical Computer Science & Cryptography", f"Loaded department mismatch: {edit_dialog.entry_dept.get()}"
    print("TEST 3 PASS: Existing and custom typed Department values load normally into the editable text field.")
    edit_dialog.destroy()

    root.quit()
    root.destroy()

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

    print("\n=== ALL DEPARTMENT EDITABLE TEXT FIELD VERIFICATIONS PASSED 100% ===")

if __name__ == "__main__":
    run_tests()
