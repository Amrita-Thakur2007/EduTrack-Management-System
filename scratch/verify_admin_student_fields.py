import os
import sys
import tkinter as tk
import time

# Add root directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DBManager
from gui.student_forms import StudentFormDialog
from gui.admin_dashboard import AdminDashboard
from tkinter import messagebox

# Mock messagebox dialogs to run autonomously
messagebox.showinfo = lambda *a, **k: None
messagebox.showwarning = lambda *a, **k: None
messagebox.showerror = lambda *a, **k: None

def test_admin_student_fields():
    print("=== STARTING ADMIN STUDENT MANAGEMENT FIELDS TEST ===")
    
    # Use temporary test database
    db_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f"test_student_fields_{int(time.time())}.db")
    if os.path.exists(db_file):
        os.remove(db_file)
        
    db = DBManager(db_file)
    
    # Initialize Tk root
    root = tk.Tk()
    root.withdraw()
    
    # --- TEST 1: CREATE STUDENT ACCOUNT WITH SCHOOL NAME & DEPARTMENT ---
    print("\n--- TEST 1: CREATE STUDENT ---")
    student_id = "STU_TEST_01"
    user_id = db.create_user("student_user_01", "pass1234", "Student", "My Hero")
    assert user_id is not None, "Failed to create user account"
    
    student_data = {
        "student_id": student_id,
        "name": "Aarav Sharma",
        "father_name": "Rajesh Sharma",
        "mother_name": "Sunita Sharma",
        "dob": "2007-04-12",
        "gender": "Male",
        "phone": "9876543210",
        "email": "aarav@example.com",
        "address": "123 Delhi Road",
        "school_name": "SKV No. 1",
        "department": "Science",
        "current_class": "11",
        "section": "A",
        "roll_number": "15",
        "admission_date": "2024-07-01",
        "father_phone": "9876500001",
        "study_hours": 3.5,
        "education_type": "School"
    }
    
    ok = db.add_student(student_data, user_id)
    assert ok, "Failed to add student to DB"
    
    # Verify directly from DB
    saved_record = db.get_student(student_id)
    assert saved_record is not None, "Student record not found in DB"
    assert saved_record["school_name"] == "SKV No. 1", f"Expected 'SKV No. 1', got '{saved_record['school_name']}'"
    assert saved_record["department"] == "Science", f"Expected 'Science', got '{saved_record['department']}'"
    assert saved_record["student_id"] == student_id, f"Expected '{student_id}', got '{saved_record['student_id']}'"
    print("[PASS] TEST 1 PASS: Student created with School Name 'SKV No. 1' and Department 'Science' with same Student ID!")
    
    # --- TEST 2: ADMIN EDIT STUDENT AUTO-POPULATION ---
    print("\n--- TEST 2: ADMIN EDIT STUDENT AUTO-POPULATION ---")
    edit_dialog = StudentFormDialog(root, db, student_id=student_id)
    
    # Check fields in dialog
    loaded_sid = edit_dialog.entry_sid.get()
    loaded_name = edit_dialog.entry_name.get()
    loaded_school = edit_dialog.entry_school_name.get()
    loaded_dept = edit_dialog.entry_dept.get()
    loaded_class = edit_dialog.entry_class.get()
    loaded_section = edit_dialog.entry_section.get()
    
    assert loaded_sid == student_id, f"Expected sid '{student_id}', got '{loaded_sid}'"
    assert loaded_name == "Aarav Sharma", f"Expected 'Aarav Sharma', got '{loaded_name}'"
    assert loaded_school == "SKV No. 1", f"Expected 'SKV No. 1', got '{loaded_school}'"
    assert loaded_dept == "Science", f"Expected 'Science', got '{loaded_dept}'"
    assert loaded_class == "11", f"Expected '11', got '{loaded_class}'"
    assert loaded_section == "A", f"Expected 'A', got '{loaded_section}'"
    
    # Verify unwanted fields are removed from Edit Student form
    assert not hasattr(edit_dialog, "entry_course"), "Unwanted field 'entry_course' still exists on Edit Student dialog!"
    assert not hasattr(edit_dialog, "entry_prev_school"), "Unwanted field 'entry_prev_school' still exists on Edit Student dialog!"
    assert not hasattr(edit_dialog, "entry_prev_pct"), "Unwanted field 'entry_prev_pct' still exists on Edit Student dialog!"
    
    print("[PASS] TEST 2 PASS: Edit Student automatically loaded School Name ('SKV No. 1') and Department ('Science')!")
    print("[PASS] Unwanted fields (Course, Program, Previous School/College, Previous Percentage) successfully removed!")
    
    # --- TEST 3: EDIT VALUES AND SAVE ---
    print("\n--- TEST 3: EDIT VALUES & SAVE ---")
    # Change Department to "PCB"
    edit_dialog.entry_dept.delete(0, tk.END)
    edit_dialog.entry_dept.insert(0, "PCB")
    
    # Save the record
    edit_dialog.save_student()
    
    # Close dialog
    edit_dialog.destroy()
    
    # Reopen Edit Student Dialog
    edit_dialog_reopened = StudentFormDialog(root, db, student_id=student_id)
    reopened_school = edit_dialog_reopened.entry_school_name.get()
    reopened_dept = edit_dialog_reopened.entry_dept.get()
    
    assert reopened_school == "SKV No. 1", f"Expected 'SKV No. 1', got '{reopened_school}'"
    assert reopened_dept == "PCB", f"Expected 'PCB', got '{reopened_dept}'"
    
    # Verify in DB that no duplicate student was created and count is 1
    all_students = db.get_all_students()
    assert len(all_students) == 1, f"Expected 1 student record, found {len(all_students)}"
    assert all_students[0]["student_id"] == student_id
    assert all_students[0]["department"] == "PCB"
    assert all_students[0]["school_name"] == "SKV No. 1"
    
    edit_dialog_reopened.destroy()
    print("[PASS] TEST 3 PASS: Edited Department ('PCB') persisted to SQLite database and correctly re-loaded upon reopening without creating duplicate records!")
    
    # --- TEST 4: STUDENT LIST TABLE IN ADMIN DASHBOARD ---
    print("\n--- TEST 4: STUDENT LIST TABLE IN ADMIN DASHBOARD ---")
    admin_dash = AdminDashboard(root, db, {"username": "admin", "role": "Admin"})
    admin_dash.show_students()
    
    # Verify column headings in tree_students
    cols = admin_dash.tree_students["columns"]
    print("Treeview columns:", cols)
    assert "school_name" in cols, "Column 'school_name' missing from treeview columns!"
    assert "dept" in cols, "Column 'dept' missing from treeview columns!"
    assert "course" not in cols, "Unwanted column 'course' still in treeview columns!"
    
    heading_school = admin_dash.tree_students.heading("school_name")["text"]
    heading_dept = admin_dash.tree_students.heading("dept")["text"]
    assert "School Name" in heading_school, f"Expected 'School Name' in heading, got '{heading_school}'"
    assert "Department" in heading_dept, f"Expected 'Department' in heading, got '{heading_dept}'"
    
    # Check populated items in table
    items = admin_dash.tree_students.get_children()
    assert len(items) == 1, f"Expected 1 item in treeview, got {len(items)}"
    
    row_values = admin_dash.tree_students.item(items[0])["values"]
    print("Populated row values:", row_values)
    # values: (student_id, name, school_name, dept, class, phone, email)
    assert row_values[0] == student_id, f"Expected sid '{student_id}', got '{row_values[0]}'"
    assert row_values[1] == "Aarav Sharma", f"Expected name 'Aarav Sharma', got '{row_values[1]}'"
    assert row_values[2] == "SKV No. 1", f"Expected school 'SKV No. 1', got '{row_values[2]}'"
    assert row_values[3] == "PCB", f"Expected dept 'PCB', got '{row_values[3]}'"
    
    print("[PASS] TEST 4 PASS: Admin Student List / Added Students table displays School Name ('SKV No. 1') and Department ('PCB') accurately from DB!")
    
    # --- TEST 5: BACKWARD COMPATIBILITY TEST ---
    print("\n--- TEST 5: BACKWARD COMPATIBILITY TEST ---")
    # Add an old legacy student that only had previous_school and course stored
    legacy_sid = "STU_LEGACY_01"
    legacy_data = {
        "student_id": legacy_sid,
        "name": "Pooja Gupta",
        "father_name": "Ramesh Gupta",
        "dob": "2006-08-20",
        "gender": "Female",
        "phone": "9812345678",
        "email": "pooja@example.com",
        "previous_school": "Modern Public School",
        "course": "Commerce",
        "current_class": "12",
        "section": "C",
        "father_phone": "9812300000",
        "study_hours": 4.0,
        "education_type": "School"
    }
    db.add_student(legacy_data)
    
    legacy_record = db.get_student(legacy_sid)
    assert legacy_record["school_name"] == "Modern Public School", f"Expected fallback 'Modern Public School', got '{legacy_record['school_name']}'"
    assert legacy_record["department"] == "Commerce", f"Expected fallback 'Commerce', got '{legacy_record['department']}'"
    
    legacy_dialog = StudentFormDialog(root, db, student_id=legacy_sid)
    assert legacy_dialog.entry_school_name.get() == "Modern Public School"
    assert legacy_dialog.entry_dept.get() == "Commerce"
    legacy_dialog.destroy()
    
    print("[PASS] TEST 5 PASS: Backward compatibility correctly mapped legacy fields to School Name and Department without data loss!")
    
    # Cleanup
    try:
        admin_dash.destroy()
        root.destroy()
    except Exception:
        pass
        
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass
            
    print("\n==================================================")
    print("ALL TESTS COMPLETED SUCCESSFULLY AND PASSED 100%!")
    print("==================================================")

if __name__ == "__main__":
    test_admin_student_fields()
