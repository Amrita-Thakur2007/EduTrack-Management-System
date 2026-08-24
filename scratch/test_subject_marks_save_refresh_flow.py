import os
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DBManager

# Mock messagebox popups
last_info = []
last_warning = []
last_error = []

messagebox.showinfo = lambda title, msg: last_info.append((title, msg))
messagebox.showwarning = lambda title, msg: last_warning.append((title, msg))
messagebox.showerror = lambda title, msg: last_error.append((title, msg))

from gui.marks_view import MarksEntryDialog

def run_tests():
    print("=== STARTING SUBJECT MARKS SAVE & REFRESH WORKFLOW VERIFICATION ===")

    db_path = f"scratch/test_marks_flow_{int(time.time())}.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = DBManager(db_path=db_path)

    # 1. Register a test student
    uid = db.create_user("StudentMarksUser", "Pass1234", "Student")
    db.add_student({
        "student_id": "STU_MARKS_100",
        "name": "Karan Kapoor",
        "email": "karan@school.edu",
        "phone": "9811223344",
        "education_type": "School",
        "school_name": "Delhi Public School",
        "current_class": "12",
        "section": "A",
        "admission_date": "2023-04-01"
    }, uid)

    root = tk.Tk()
    root.withdraw()

    # 2. Open MarksEntryDialog
    dlg = MarksEntryDialog(root, db, student_id="STU_MARKS_100", student_name="Karan Kapoor", subject="Physics")

    # Fill marks for Physics
    dlg.entry_subject.delete(0, tk.END)
    dlg.entry_subject.insert(0, "Physics")

    dlg.entry_internal.delete(0, tk.END)
    dlg.entry_internal.insert(0, "15.0")

    dlg.entry_mid.delete(0, tk.END)
    dlg.entry_mid.insert(0, "25.0")

    dlg.entry_proj.delete(0, tk.END)
    dlg.entry_proj.insert(0, "15.0")

    dlg.entry_viva.delete(0, tk.END)
    dlg.entry_viva.insert(0, "8.0")

    dlg.entry_final.delete(0, tk.END)
    dlg.entry_final.insert(0, "75.0")  # Total = 138.0

    # Save Subject Marks
    dlg.save_marks()

    # Verify table reloaded with latest values
    tree_items = dlg.tree_marks.get_children()
    assert len(tree_items) == 1, f"Expected 1 record in tree table, found {len(tree_items)}"
    row1 = dlg.tree_marks.item(tree_items[0])["values"]
    assert str(row1[0]) == "Physics", f"Expected subject Physics, got {row1[0]}"
    assert str(row1[6]) == "138", f"Expected total 138, got {row1[6]}"

    # Verify directly in SQLite DB
    db_marks_1 = db.get_student_marks("STU_MARKS_100", "Physics")
    assert db_marks_1 is not None, "Physics marks not found in DB!"
    assert db_marks_1["total_marks"] == 138.0, f"Expected DB total 138.0, got {db_marks_1['total_marks']}"

    print("TEST 1 PASS: Marks saved to database and Subject-Wise Mark Records table immediately refreshed with 138 total.")

    # 3. EDIT EXISTING MARKS (Change 75 -> 85)
    dlg.edit_selected_subject()  # Selects Physics for editing
    dlg.entry_final.delete(0, tk.END)
    dlg.entry_final.insert(0, "85.0")  # Total becomes 148.0

    dlg.save_marks()

    # Verify table reloaded with NEW values (148)
    tree_items = dlg.tree_marks.get_children()
    assert len(tree_items) == 1, f"Expected exactly 1 updated record (NO duplicate), found {len(tree_items)}"
    row_updated = dlg.tree_marks.item(tree_items[0])["values"]
    assert str(row_updated[0]) == "Physics", f"Expected subject Physics, got {row_updated[0]}"
    assert str(row_updated[6]) == "148", f"Expected updated total 148, got {row_updated[6]}"

    # Verify in DB: updated value 148 and exactly 1 record
    all_db_marks = db.get_all_student_marks("STU_MARKS_100")
    assert len(all_db_marks) == 1, f"Expected exactly 1 record in DB (no duplicates), found {len(all_db_marks)}"
    assert all_db_marks[0]["total_marks"] == 148.0, f"Expected updated DB total 148.0, got {all_db_marks[0]['total_marks']}"

    print("TEST 2 PASS: Editing marks (75 -> 85) updated existing record to 148 without creating duplicate records.")

    # 4. ADD SECOND SUBJECT (Chemistry)
    dlg._add_new_subject_form()
    dlg.entry_subject.delete(0, tk.END)
    dlg.entry_subject.insert(0, "Chemistry")

    dlg.entry_internal.delete(0, tk.END)
    dlg.entry_internal.insert(0, "18.0")

    dlg.entry_mid.delete(0, tk.END)
    dlg.entry_mid.insert(0, "28.0")

    dlg.entry_proj.delete(0, tk.END)
    dlg.entry_proj.insert(0, "18.0")

    dlg.entry_viva.delete(0, tk.END)
    dlg.entry_viva.insert(0, "9.0")

    dlg.entry_final.delete(0, tk.END)
    dlg.entry_final.insert(0, "80.0")

    dlg.save_marks()

    tree_items_2 = dlg.tree_marks.get_children()
    assert len(tree_items_2) == 2, f"Expected 2 subject records in tree table, found {len(tree_items_2)}"

    print("TEST 3 PASS: Second subject 'Chemistry' added successfully alongside 'Physics'.")

    dlg.destroy()
    root.quit()
    root.destroy()

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

    print("\n=== ALL SUBJECT MARKS SAVE & REFRESH WORKFLOW TESTS PASSED 100% ===")

if __name__ == "__main__":
    run_tests()
