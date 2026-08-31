import os
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DBManager

sys.path.insert(0, ".")
from gui.admin_dashboard import AdminDashboard

def run_tests():
    print("=== STARTING STUDENT MANAGEMENT FILTERING TEST ===")

    db_path = f"scratch/test_student_mgmt_{int(time.time())}.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = DBManager(db_path=db_path)

    # 1. Register School Student (Amrita)
    u1 = db.create_user("AmritaUser", "Pass1234", "Student")
    db.add_student({
        "student_id": "ST_SCH_01",
        "name": "Amrita",
        "email": "amrita@school.edu",
        "education_type": "School",
        "school_name": "SKV NO-1",
        "current_class": "12",
        "section": "B"
    }, u1)

    # 2. Register College Student (Grisha)
    u2 = db.create_user("GrishaUser", "Pass1234", "Student")
    db.add_student({
        "student_id": "ST_COL_02",
        "name": "Grisha",
        "email": "grisha@college.edu",
        "education_type": "College",
        "college_name": "Rajdhani College",
        "course": "BCA",
        "enrollment_number": "ST_COL_02",
        "semester": "Semester 2",
        "academic_year": "2024-2025"
    }, u2)

    root = tk.Tk()
    root.withdraw()

    # 3. Instantiate AdminDashboard
    admin_user = {"id": 1, "username": "admin", "role": "Admin"}
    admin_dash = AdminDashboard(root, db, admin_user)
    
    # 4. Open Student Management
    admin_dash.show_students()

    # --- TEST 1: Default Mode (School) ---
    assert admin_dash.combo_category.get() == "School", "Expected default category to be School"
    
    # Get all items in the treeview
    items_school = admin_dash.tree_students.get_children()
    student_names_school = [admin_dash.tree_students.item(item)["values"][1] for item in items_school]
    student_ids_school = [admin_dash.tree_students.item(item)["values"][0] for item in items_school]
    
    assert len(items_school) == 1, f"Expected 1 student in School mode, got {len(items_school)}"
    assert "Amrita" in student_names_school, f"Expected Amrita to be shown, got {student_names_school}"
    assert "ST_SCH_01" in student_ids_school
    print("TEST 1 PASS: Default Mode (School) displays ONLY the School student.")

    # --- TEST 2: Switch to College ---
    admin_dash.combo_category.set("College")
    admin_dash.combo_category.event_generate("<<ComboboxSelected>>")
    
    items_college = admin_dash.tree_students.get_children()
    student_names_college = [admin_dash.tree_students.item(item)["values"][1] for item in items_college]
    student_ids_college = [admin_dash.tree_students.item(item)["values"][0] for item in items_college]
    
    assert len(items_college) == 1, f"Expected 1 student in College mode, got {len(items_college)}"
    assert "Grisha" in student_names_college, f"Expected Grisha to be shown, got {student_names_college}"
    assert "ST_COL_02" in student_ids_college
    print("TEST 2 PASS: Switching to College displays ONLY the College student.")

    # --- TEST 3: Switch back to School ---
    admin_dash.combo_category.set("School")
    admin_dash.combo_category.event_generate("<<ComboboxSelected>>")
    
    items_school_2 = admin_dash.tree_students.get_children()
    student_names_school_2 = [admin_dash.tree_students.item(item)["values"][1] for item in items_school_2]
    
    assert len(items_school_2) == 1, f"Expected 1 student, got {len(items_school_2)}"
    assert "Amrita" in student_names_school_2
    print("TEST 3 PASS: Switching back to School works correctly.")

    # --- TEST 4: Verify student records were not deleted or modified in DB ---
    all_db_students = db.get_all_students(filter_edu_type="All")
    assert len(all_db_students) == 2, f"Expected 2 students in database, got {len(all_db_students)}"
    
    amrita_db = [s for s in all_db_students if s["name"] == "Amrita"][0]
    grisha_db = [s for s in all_db_students if s["name"] == "Grisha"][0]
    
    assert amrita_db["student_id"] == "ST_SCH_01"
    assert amrita_db["school_name"] == "SKV NO-1"
    assert grisha_db["student_id"] == "ST_COL_02"
    assert grisha_db["course"] == "BCA"
    print("TEST 4 PASS: Student records were not modified or deleted in the database.")

    # Clean up
    admin_dash.destroy()
    root.quit()
    root.destroy()
    
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    print("\n=== ALL STUDENT MANAGEMENT FILTERING TESTS PASSED 100% ===")

if __name__ == "__main__":
    run_tests()
