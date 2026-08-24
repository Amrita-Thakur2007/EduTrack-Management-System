import os
import sys
import tkinter as tk

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db_manager import DBManager
from gui.student_forms import StudentFormDialog

def test_edit_student_workflow():
    root = tk.Tk()
    root.withdraw()

    db_path = os.path.join(os.path.dirname(__file__), "test_edit_student.db")
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = DBManager(db_path=db_path)

    # 1. Insert initial student
    student_id = "STU1001"
    initial_data = {
        "student_id": student_id,
        "name": "Rahul Sharma",
        "father_name": "Amit Sharma",
        "mother_name": "Sunita Sharma",
        "dob": "2005-04-10",
        "gender": "Male",
        "phone": "9876543210",
        "email": "rahul.sharma@example.com",
        "address": "123 Main St, City",
        "course": "B.Tech Computer Science",
        "department": "Computer Science & Engineering",
        "admission_date": "2024-08-01",
        "previous_school": "ABC School",
        "previous_percentage": 85.0,
        "current_class": "10-A",
        "study_hours": 4.0
    }
    db.add_student(initial_data)

    parent_initial = {
        "student_id": student_id,
        "name": "Amit Sharma",
        "phone": "9876543210",
        "email": "amit.sharma@example.com",
        "occupation": "Engineer",
        "emergency_contact": "9876543210",
        "relationship": "Father",
        "address": "123 Main St, City"
    }
    db.add_parent(parent_initial)

    # 2. Open StudentFormDialog in edit mode
    saved_called = [False]
    def on_save_callback():
        saved_called[0] = True

    dialog = StudentFormDialog(root, db, student_id=student_id, on_save_callback=on_save_callback)

    print("Loaded dialog.entry_name:", dialog.entry_name.get())
    print("Loaded dialog.entry_father:", dialog.entry_father.get())

    # 3. Simulate teacher editing details
    dialog.entry_name.delete(0, tk.END)
    dialog.entry_name.insert(0, "Rahul Verma")

    dialog.entry_class.delete(0, tk.END)
    dialog.entry_class.insert(0, "11-B")

    dialog.entry_phone.delete(0, tk.END)
    dialog.entry_phone.insert(0, "9998887770")

    dialog.entry_father.delete(0, tk.END)
    dialog.entry_father.insert(0, "Suresh Verma")

    dialog.entry_parent_phone.delete(0, tk.END)
    dialog.entry_parent_phone.insert(0, "9998887771")

    # Override messagebox.showinfo to prevent blocking popup during headless test
    import tkinter.messagebox as mb
    mb.showinfo = lambda title, msg: print("Showinfo:", title, msg)
    mb.showerror = lambda title, msg: print("Showerror:", title, msg)

    # 4. Save student record
    dialog.save_student()

    # 5. Verify database update
    updated_student = db.get_student(student_id)
    print("Updated Student from DB:", updated_student)

    updated_parent = db.get_parent_by_student_id(student_id)
    print("Updated Parent from DB:", updated_parent)

    assert updated_student is not None, "Student record missing from DB!"
    assert updated_student["name"] == "Rahul Verma", f"DB student name not updated! Got '{updated_student['name']}'"
    assert updated_student["current_class"] == "11-B", f"DB class not updated! Got '{updated_student['current_class']}'"
    assert updated_student["phone"] == "9998887770", f"DB phone not updated! Got '{updated_student['phone']}'"
    assert updated_student["father_name"] == "Suresh Verma", f"DB father_name not updated! Got '{updated_student['father_name']}'"

    assert updated_parent is not None, "Parent record missing from DB!"
    assert updated_parent["name"] == "Suresh Verma", f"DB parent name not updated! Got '{updated_parent['name']}'"

    root.destroy()
    print("ALL EDIT STUDENT WORKFLOW TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_edit_student_workflow()
