import os
import sys
import tkinter as tk
from database.db_manager import DBManager
from gui.student_forms import StudentFormDialog

def main():
    root = tk.Tk()
    root.withdraw()

    # Mock tkinter.messagebox functions to avoid GUI blocking during test run
    import tkinter.messagebox
    tkinter.messagebox.showinfo = lambda *a, **k: None
    tkinter.messagebox.showwarning = lambda *a, **k: None
    tkinter.messagebox.showerror = lambda *a, **k: None

    db_path = "test_end_to_end_sync.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = DBManager(db_path=db_path)

    # --- STEP 1: Student Account Creation with Complete Parent Details ---
    stu_user_id = db.create_user("rahul_stu", "password123", "Student")
    assert stu_user_id is not None, "Failed to create Student user"

    student_data = {
        "student_id": "STU001",
        "name": "Rahul Sharma",
        "father_name": "Amit Sharma",
        "mother_name": "Sunita Sharma",
        "father_phone": "9876543210",
        "mother_phone": "9876543211",
        "parent_phone": "9876543210",
        "parent_email": "amit@example.com",
        "guardian_phone": "9876543210",
        "guardian_email": "amit@example.com",
        "dob": "2004-05-15",
        "gender": "Male",
        "phone": "9998887770",
        "email": "rahul@example.com",
        "address": "Delhi, India",
        "course": "BCA",
        "current_class": "10",
        "section": "A",
        "admission_date": "2024-08-01",
        "academic_year": "2024-2025"
    }
    assert db.add_student(student_data, stu_user_id) is True, "add_student failed"

    parent_data = {
        "student_id": "STU001",
        "name": "Amit Sharma",
        "mother_name": "Sunita Sharma",
        "phone": "9876543210",
        "mother_phone": "9876543211",
        "email": "amit@example.com",
        "occupation": "Business",
        "emergency_contact": "9876543210",
        "relationship": "Father",
        "address": "Delhi, India"
    }
    assert db.add_parent(parent_data) is True, "add_parent failed"
    print("STEP 1 PASS: Student STU001 created with complete personal, academic, and parent details in database!")

    # --- STEP 2: Database Verification ---
    db_stu = db.get_student("STU001")
    db_par = db.get_parent_by_student_id("STU001")
    assert db_stu['name'] == "Rahul Sharma", "DB Student Name mismatch"
    assert db_stu['course'] == "BCA", "DB Course mismatch"
    assert db_stu['father_name'] == "Amit Sharma", "DB Father Name mismatch"
    assert db_par['name'] == "Amit Sharma", "DB Parent Name mismatch"
    assert db_par['phone'] == "9876543210", "DB Parent Phone mismatch"
    print("STEP 2 PASS: All fields verified in SQLite database as single source of truth!")

    # --- STEP 3: Teacher Portal & Edit Student Auto-Fill ---
    dialog = StudentFormDialog(root, db, student_id="STU001")
    assert dialog.entry_sid.get() == "STU001", "Edit form Student ID mismatch"
    assert dialog.entry_name.get() == "Rahul Sharma", "Edit form Name mismatch"
    assert dialog.entry_father.get() == "Amit Sharma", "Edit form Father Name mismatch"
    assert dialog.entry_parent_phone.get() == "9876543210", "Edit form Parent Phone mismatch"
    assert dialog.entry_course.get() == "BCA", "Edit form Course mismatch"
    assert not hasattr(dialog, 'entry_roll'), "Roll Number widget still present!"
    assert not hasattr(dialog, 'combo_dept'), "Department widget still present!"
    print("STEP 3 PASS: Teacher Portal Edit Student form auto-populated ALL saved fields correctly!")
    dialog.destroy()

    # --- STEP 4: Parent Portal Linkage ---
    parent_user_id = db.create_user("9876543210", "pass123", "Parent")
    assert parent_user_id is not None, "Failed to create Parent user"
    db.auto_link_parent_account("STU001", "9876543210", "amit@example.com")

    linked_children = db.get_parent_students(parent_user_id)
    assert len(linked_children) >= 1, "Parent Portal failed to retrieve linked child student!"
    assert linked_children[0]['name'] == "Rahul Sharma", f"Expected Rahul Sharma, got {linked_children[0]['name']}"
    print("STEP 4 PASS: Parent Portal automatically retrieved Rahul Sharma as linked child!")

    # --- STEP 5: Edit Sync Test ---
    dialog_edit = StudentFormDialog(root, db, student_id="STU001")
    dialog_edit.entry_parent_phone.delete(0, tk.END)
    dialog_edit.entry_parent_phone.insert(0, "9876500000")
    dialog_edit.save_student()

    db_stu_updated = db.get_student("STU001")
    db_par_updated = db.get_parent_by_student_id("STU001")
    assert db_stu_updated['father_phone'] == "9876500000", f"DB father_phone update failed: {db_stu_updated['father_phone']}"
    assert db_par_updated['phone'] == "9876500000", f"DB parent phone update failed: {db_par_updated['phone']}"

    # Re-open Edit Student to verify sync
    dialog_reopen = StudentFormDialog(root, db, student_id="STU001")
    assert dialog_reopen.entry_parent_phone.get() == "9876500000", "Re-opened edit dialog failed to show updated phone!"
    dialog_reopen.destroy()

    # Parent Portal verification with updated phone
    parent_user_id2 = db.create_user("9876500000", "pass123", "Parent")
    db.auto_link_parent_account("STU001", "9876500000", "amit@example.com")
    linked_children_updated = db.get_parent_students(parent_user_id2)
    assert len(linked_children_updated) >= 1, "Parent Portal failed to retrieve child after phone update!"
    assert linked_children_updated[0]['name'] == "Rahul Sharma", "Parent Portal child name mismatch after update"
    print("STEP 5 PASS: Edit Sync Test passed! Phone updated to 9876500000 across Database, Teacher Portal, Edit Student, and Parent Portal!")

    root.quit()
    root.destroy()

    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    print("\n=== END-TO-END DATA SYNCHRONIZATION TEST PASSED 100% SUCCESSFULLY ===")

if __name__ == "__main__":
    main()
