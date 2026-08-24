import os
import sys
import tkinter as tk
from database.db_manager import DBManager
from gui.teacher_dashboard import TeacherDashboard
from gui.student_forms import StudentFormDialog

def main():
    root = tk.Tk()
    root.withdraw()

    import time
    db_path = f"test_enrollment_flow_{int(time.time())}.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = DBManager(db_path=db_path)

    # 1. Verify roll_number widget is not on StudentFormDialog
    dialog_check = StudentFormDialog(root, db)
    assert not hasattr(dialog_check, 'entry_roll'), "FAIL: entry_roll still exists on StudentFormDialog!"
    print("TEST 1 PASS: Roll Number / Enrollment Number field completely removed from StudentFormDialog.")
    dialog_check.destroy()

    # 2. Test Single-Submission Add Student with photo and parent details
    dialog = StudentFormDialog(root, db)

    # Fill mandatory student details
    dialog.entry_sid.config(state="normal")
    dialog.entry_sid.delete(0, tk.END)
    dialog.entry_sid.insert(0, "STU100")

    dialog.entry_name.delete(0, tk.END)
    dialog.entry_name.insert(0, "Aarav Sharma")

    dialog.entry_dob.delete(0, tk.END)
    dialog.entry_dob.insert(0, "2012-04-10")

    dialog.combo_gender.set("Male")

    dialog.entry_class.delete(0, tk.END)
    dialog.entry_class.insert(0, "10")

    dialog.entry_section.delete(0, tk.END)
    dialog.entry_section.insert(0, "A")

    dialog.text_address.delete("1.0", tk.END)
    dialog.text_address.insert("1.0", "New Delhi, India")

    dialog.photo_path = "/path/to/student_photo.png"

    # Fill parent details on same form
    dialog.entry_father.delete(0, tk.END)
    dialog.entry_father.insert(0, "Vikram Sharma")

    dialog.entry_parent_phone.delete(0, tk.END)
    dialog.entry_parent_phone.insert(0, "9876543210")

    dialog.entry_parent_email.delete(0, tk.END)
    dialog.entry_parent_email.insert(0, "vikram@example.com")

    import tkinter.messagebox
    tkinter.messagebox.showinfo = lambda *a, **k: None
    tkinter.messagebox.showwarning = lambda *a, **k: None
    
    error_shown = [False]
    def mock_err(title, msg):
        error_shown[0] = True
    tkinter.messagebox.showerror = mock_err

    dialog.save_student()

    # Verify student & parent records created in database in single submission
    stu_db = db.get_student("STU100")
    parent_db = db.get_parent_by_student_id("STU100")

    assert stu_db is not None, "FAIL: Student STU100 record not created in DB!"
    assert stu_db['name'] == "Aarav Sharma", f"Expected Aarav Sharma, got {stu_db['name']}"
    assert stu_db['photo_path'] == "/path/to/student_photo.png", f"Expected photo_path saved, got {stu_db['photo_path']}"
    assert parent_db is not None, "FAIL: Parent record not created in DB in single submission!"
    assert parent_db['name'] == "Vikram Sharma", f"Expected Vikram Sharma, got {parent_db['name']}"
    assert parent_db['phone'] == "9876543210", f"Expected 9876543210, got {parent_db['phone']}"
    print("TEST 2 PASS: Add Student saved both Student and Parent records in a single submission!")

    # 4. Test Duplicate Record Prevention
    dialog_dup = StudentFormDialog(root, db)
    dialog_dup.entry_sid.config(state="normal")
    dialog_dup.entry_sid.delete(0, tk.END)
    dialog_dup.entry_sid.insert(0, "STU101")  # Different SID but same details

    dialog_dup.entry_name.delete(0, tk.END)
    dialog_dup.entry_name.insert(0, "Aarav Sharma")

    dialog_dup.entry_dob.delete(0, tk.END)
    dialog_dup.entry_dob.insert(0, "2012-04-10")

    dialog_dup.combo_gender.set("Male")

    dialog_dup.entry_class.delete(0, tk.END)
    dialog_dup.entry_class.insert(0, "10")

    dialog_dup.entry_section.delete(0, tk.END)
    dialog_dup.entry_section.insert(0, "A")

    dialog_dup.entry_father.delete(0, tk.END)
    dialog_dup.entry_father.insert(0, "Vikram Sharma")

    dialog_dup.entry_parent_phone.delete(0, tk.END)
    dialog_dup.entry_parent_phone.insert(0, "9876543210")

    dialog_dup.save_student()
    assert error_shown[0] is True, "FAIL: Duplicate student was not blocked!"
    assert db.get_student("STU101") is None, "FAIL: Duplicate student STU101 was saved in DB!"
    print("TEST 3 PASS: Duplicate student record prevention verified!")

    dialog_dup.destroy()

    # 5. Test Edit Form populates and saves both Student and Parent sections cleanly
    dialog_edit = StudentFormDialog(root, db, student_id="STU100")
    assert dialog_edit.entry_name.get() == "Aarav Sharma", f"Edit form name failed: {dialog_edit.entry_name.get()}"
    assert dialog_edit.entry_father.get() == "Vikram Sharma", f"Edit form father name failed: {dialog_edit.entry_father.get()}"

    # Update both sections
    dialog_edit.entry_name.delete(0, tk.END)
    dialog_edit.entry_name.insert(0, "Aarav Verma")

    dialog_edit.entry_father.delete(0, tk.END)
    dialog_edit.entry_father.insert(0, "Vikram Verma")

    dialog_edit.save_student()

    stu_updated = db.get_student("STU100")
    parent_updated = db.get_parent_by_student_id("STU100")

    assert stu_updated['name'] == "Aarav Verma", f"Updated student name failed: {stu_updated['name']}"
    assert parent_updated['name'] == "Vikram Verma", f"Updated parent name failed: {parent_updated['name']}"
    print("TEST 4 PASS: Student Profile/Edit form successfully updated both Student and Parent sections in single submission!")

    root.quit()
    root.destroy()

    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    print("\n=== ALL ENROLLMENT FLOW & DUPLICATE PREVENTION TESTS PASSED 100% ===")

if __name__ == "__main__":
    main()
