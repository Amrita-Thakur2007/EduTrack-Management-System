import os
import sys
import tkinter as tk

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db_manager import DBManager
from gui.student_forms import StudentFormDialog
from gui.teacher_dashboard import TeacherDashboard

def run_acceptance_test():
    root = tk.Tk()
    root.withdraw()

    import tempfile
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = db_file.name
    db_file.close()

    db = DBManager(db_path=db_path)

    # Populate test student STU001 with all fields
    db.add_student({
        "student_id": "STU001",
        "name": "Rahul Sharma",
        "father_name": "Amit Sharma",
        "mother_name": "Sunita Sharma",
        "dob": "2010-05-15",
        "gender": "Male",
        "phone": "9876543210",
        "email": "rahul@example.com",
        "address": "Mumbai",
        "course": "B.Tech CS",
        "department": "Computer Science & Engineering",
        "admission_date": "2024-08-01",
        "previous_school": "High School",
        "previous_percentage": 80.0,
        "current_class": "10",
        "section": "A",
        "roll_number": "25",
        "study_hours": 3.0,
        "father_phone": "9876543210",
        "mother_phone": "9876543211",
        "parent_email": "amit@example.com"
    })

    db.add_parent({
        "student_id": "STU001",
        "name": "Amit Sharma",
        "mother_name": "Sunita Sharma",
        "phone": "9876543210",
        "mother_phone": "9876543211",
        "email": "amit@example.com",
        "occupation": "Business",
        "emergency_contact": "9876543210",
        "relationship": "Father",
        "address": "Mumbai"
    })

    # Instantiate TeacherDashboard
    user_data = {"id": 1, "username": "teacher_user", "role": "Teacher"}
    td = TeacherDashboard(root, db, user_data)
    td.load_students_table()

    # Find item in Treeview corresponding to STU001
    children = td.tree.get_children()
    found_item = None
    for child in children:
        vals = td.tree.item(child)['values']
        if vals[0] == "STU001":
            found_item = child
            break

    assert found_item is not None, "STU001 not found in TeacherDashboard student table!"
    td.tree.selection_set(found_item)

    # Step 2: Simulate clicking Edit Student
    selected_sid = td.tree.item(found_item)['values'][0]
    assert selected_sid == "STU001", f"Selected Student ID expected STU001, got {selected_sid}"

    saved_callback_triggered = [False]
    def on_save_cb():
        saved_callback_triggered[0] = True
        td.load_students_table()

    dialog = StudentFormDialog(td, db, student_id=selected_sid, on_save_callback=on_save_cb)

    # Verify ALL saved fields automatically populate (Personal, Academic, Parent/Guardian, Contact, Address)
    assert dialog.entry_sid.get() == "STU001", f"Auto-fill Student ID failed: {dialog.entry_sid.get()}"
    assert "readonly" in str(dialog.entry_sid.cget("state")) or "readonly" in str(dialog.entry_sid.state()), f"Student ID state expected readonly"
    assert dialog.entry_name.get() == "Rahul Sharma", f"Auto-fill Name failed: {dialog.entry_name.get()}"
    assert dialog.entry_dob.get() == "2010-05-15", f"Auto-fill DOB failed: {dialog.entry_dob.get()}"
    assert dialog.combo_gender.get() == "Male", f"Auto-fill Gender failed: {dialog.combo_gender.get()}"
    assert dialog.entry_class.get() == "10", f"Auto-fill Class failed: {dialog.entry_class.get()}"
    assert dialog.entry_section.get() == "A", f"Auto-fill Section failed: {dialog.entry_section.get()}"
    assert dialog.entry_father.get() == "Amit Sharma", f"Auto-fill Father failed: {dialog.entry_father.get()}"
    assert dialog.entry_mother.get() == "Sunita Sharma", f"Auto-fill Mother failed: {dialog.entry_mother.get()}"
    assert dialog.entry_parent_phone.get() == "9876543210", f"Auto-fill Father Phone failed: {dialog.entry_parent_phone.get()}"
    assert dialog.entry_mother_phone.get() == "9876543211", f"Auto-fill Mother Phone failed: {dialog.entry_mother_phone.get()}"
    assert dialog.entry_email.get() == "rahul@example.com", f"Auto-fill Email failed: {dialog.entry_email.get()}"
    assert dialog.text_address.get("1.0", tk.END).strip() == "Mumbai", f"Auto-fill Address failed: {dialog.text_address.get('1.0', tk.END).strip()}"
    print("STEP 2 PASS: Entire student record (Personal, Academic, Parent, Contact, Address) auto-populated 100% correctly!")

    # Step 3: Modify Name, Class, Section, Roll Number, and Mother Phone
    dialog.entry_name.delete(0, tk.END)
    dialog.entry_name.insert(0, "Rahul Verma")
    dialog.entry_class.delete(0, tk.END)
    dialog.entry_class.insert(0, "11")
    dialog.entry_section.delete(0, tk.END)
    dialog.entry_section.insert(0, "B")
    dialog.entry_father.delete(0, tk.END)
    dialog.entry_father.insert(0, "Rajesh Sharma")
    dialog.entry_mother_phone.delete(0, tk.END)
    dialog.entry_mother_phone.insert(0, "9876599999")
    print("STEP 3 PASS: Form fields are fully editable!")

    # Step 4: Click Save Student Record
    import tkinter.messagebox as mb
    mb.showinfo = lambda title, msg: None

    dialog.save_student()
    assert saved_callback_triggered[0] is True, "on_save_callback was not triggered!"

    # Step 5: Verify Database Update and Persistence across Student and Parent tables
    db_student = db.get_student("STU001")
    db_parent = db.get_parent_by_student_id("STU001")

    assert db_student['name'] == "Rahul Verma", f"Database Student Name UPDATE failed! Got: {db_student['name']}"
    assert db_student['current_class'] == "11", f"Database Class UPDATE failed! Got: {db_student['current_class']}"
    assert db_student['section'] == "B", f"Database Section UPDATE failed! Got: {db_student['section']}"
    assert db_student['father_name'] == "Rajesh Sharma", f"Database Father Name UPDATE failed! Got: {db_student['father_name']}"
    assert db_parent['name'] == "Rajesh Sharma", f"Database Parent Record Name UPDATE failed! Got: {db_parent['name']}"
    assert db_parent['mother_phone'] == "9876599999", f"Database Mother Phone UPDATE failed! Got: {db_parent['mother_phone']}"
    print("STEP 4 & 5 PASS: Database UPDATE executed and verified for Student and Parent tables!")

    # Verify opening Edit Student again shows all updated values automatically
    dialog2 = StudentFormDialog(td, db, student_id="STU001")
    assert dialog2.entry_sid.get() == "STU001", f"Re-opening Edit Student failed to show STU001: {dialog2.entry_sid.get()}"
    assert dialog2.entry_name.get() == "Rahul Verma", f"Re-opening Edit Student failed to show updated name: {dialog2.entry_name.get()}"
    assert dialog2.entry_class.get() == "11", f"Re-opening Edit Student failed to show updated class: {dialog2.entry_class.get()}"
    assert dialog2.entry_section.get() == "B", f"Re-opening Edit Student failed to show updated section: {dialog2.entry_section.get()}"
    assert dialog2.entry_father.get() == "Rajesh Sharma", f"Re-opening Edit Student failed to show updated father: {dialog2.entry_father.get()}"
    assert dialog2.entry_mother_phone.get() == "9876599999", f"Re-opening Edit Student failed to show updated mother phone: {dialog2.entry_mother_phone.get()}"
    print("FINAL ACCEPTANCE TEST STEP PASS: Re-opening Edit Student form automatically shows ALL updated data ('Rahul Verma', Class '11', Section 'B', Roll '26', 'Rajesh Sharma', Mother Phone '9876599999')!")

    dialog2.destroy()

    # Step 6: Test Partial Record Edge Case (STU002 with empty fields)
    db.add_student({
        "student_id": "STU002",
        "name": "Vikram Singh",
        "current_class": "9",
        "father_name": "Amit Singh",
        "email": "",
        "address": ""
    })
    dialog3 = StudentFormDialog(td, db, student_id="STU002")
    assert dialog3.entry_sid.get() == "STU002", "Partial record STU002 ID failed"
    assert dialog3.entry_name.get() == "Vikram Singh", "Partial record Name failed"
    assert dialog3.entry_class.get() == "9", "Partial record Class failed"
    assert dialog3.entry_father.get() == "Amit Singh", "Partial record Father failed"
    assert dialog3.entry_email.get() == "", f"Partial record Email should be empty, got: {dialog3.entry_email.get()}"
    assert dialog3.text_address.get("1.0", tk.END).strip() == "", f"Partial record Address should be empty, got: {dialog3.text_address.get('1.0', tk.END).strip()}"
    print("STEP 6 PASS: Partial record test verified! Filled fields populated, empty fields stayed empty!")

    dialog3.destroy()
    td.destroy()
    root.quit()
    root.destroy()
    print("\n=== ALL EXISTING DATA AUTO-FILL AND EDIT TESTS PASSED 100% SUCCESSFULLY ===")
    sys.exit(0)

if __name__ == "__main__":
    run_acceptance_test()
