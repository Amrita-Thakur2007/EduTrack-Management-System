import os
import sys
import tkinter as tk

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db_manager import DBManager
from gui.student_forms import StudentFormDialog
from gui.teacher_dashboard import TeacherDashboard

def run_verification():
    root = tk.Tk()
    root.withdraw()

    db_path = os.path.join(os.path.dirname(__file__), "test_roll_removal.db")
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = DBManager(db_path=db_path)
    
    # Test 1: Check StudentFormDialog attributes for entry_roll_number
    dialog = StudentFormDialog(root, db)
    assert not hasattr(dialog, 'entry_roll_number'), "FAIL: entry_roll_number still exists on StudentFormDialog!"
    print("PASS: entry_roll_number field completely removed from StudentFormDialog.")
    dialog.destroy()

    # Test 2: Check TeacherDashboard columns
    user_data = {"id": 1, "username": "teacher1", "role": "teacher"}
    td = TeacherDashboard(root, db, user_data)
    cols = td.tree["columns"]
    print(f"TeacherDashboard Student Tree columns: {cols}")
    assert "roll" not in cols, "FAIL: 'roll' column still in TeacherDashboard student table!"
    print("PASS: 'roll' column completely removed from TeacherDashboard student table.")

    td.destroy()
    root.destroy()
    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_verification()
