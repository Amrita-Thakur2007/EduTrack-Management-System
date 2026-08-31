import os
import sys
import time
import tkinter as tk
from tkinter import messagebox

sys.path.insert(0, ".")
from database.db_manager import DBManager
from gui.admin_dashboard import AdminDashboard

def run_tests():
    print("=== STARTING STUDENT REGISTRATION TO ADMIN SYNC TEST ===")

    db_path = f"scratch/test_reg_admin_sync_{int(time.time())}.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = DBManager(db_path=db_path)

    # 1. Existing baseline students: Amrita (School), Grisha (College)
    u_amrita = db.create_user("AmritaUser", "Pass123", "Student")
    db.add_student({
        "student_id": "20180065157",
        "name": "Amrita",
        "email": "amrita@school.edu",
        "education_type": "School",
        "school_name": "SKV NO-1",
        "current_class": "12",
        "section": "B"
    }, u_amrita)

    u_grisha = db.create_user("GrishaUser", "Pass123", "Student")
    db.add_student({
        "student_id": "2601651466",
        "name": "Grisha",
        "email": "grisha@college.edu",
        "education_type": "College",
        "college_name": "Rajdhani College",
        "course": "BCA",
        "enrollment_number": "2601651466",
        "semester": "Semester 2",
        "academic_year": "2024-2025"
    }, u_grisha)

    root = tk.Tk()
    root.withdraw()

    admin_user = {"id": 1, "username": "admin", "role": "Admin"}
    admin_dash = AdminDashboard(root, db, admin_user)
    admin_dash.show_students()

    # Verify baseline
    # Mode: School -> Amrita
    admin_dash.combo_category.set("School")
    admin_dash.combo_category.event_generate("<<ComboboxSelected>>")
    school_items = [admin_dash.tree_students.item(i)["values"][1] for i in admin_dash.tree_students.get_children()]
    assert "Amrita" in school_items and "Grisha" not in school_items

    # Mode: College -> Grisha
    admin_dash.combo_category.set("College")
    admin_dash.combo_category.event_generate("<<ComboboxSelected>>")
    college_items = [admin_dash.tree_students.item(i)["values"][1] for i in admin_dash.tree_students.get_children()]
    assert "Grisha" in college_items and "Amrita" not in college_items
    print("TEST 1 PASS: Baseline existing students (Amrita & Grisha) visible under respective modes.")

    # 2. Simulate Student Registration: New School Student (Rohan)
    u_rohan = db.create_user("RohanUser", "Pass123", "Student")
    db.add_student({
        "student_id": "ST_SCH_NEW",
        "name": "Rohan School",
        "email": "rohan@school.edu",
        "education_type": "School",
        "school_name": "DPS Delhi",
        "current_class": "10",
        "section": "A"
    }, u_rohan)

    # 3. Simulate Student Registration: New College Student (Priya)
    u_priya = db.create_user("PriyaUser", "Pass123", "Student")
    db.add_student({
        "student_id": "ST_COL_NEW",
        "name": "Priya College",
        "email": "priya@college.edu",
        "education_type": "College",
        "college_name": "Delhi Technical University",
        "course": "B.Tech CSE",
        "enrollment_number": "ST_COL_NEW",
        "semester": "Semester 4",
        "academic_year": "2024-2025"
    }, u_priya)

    # 4. Refresh Admin UI
    # In School Mode -> should show Amrita + Rohan School, NOT Grisha or Priya College
    admin_dash.combo_category.set("School")
    admin_dash.load_students_table()
    updated_school_items = [admin_dash.tree_students.item(i)["values"][1] for i in admin_dash.tree_students.get_children()]
    assert len(updated_school_items) == 2, f"Expected 2 school students, got {len(updated_school_items)}"
    assert "Amrita" in updated_school_items
    assert "Rohan School" in updated_school_items
    assert "Grisha" not in updated_school_items
    assert "Priya College" not in updated_school_items
    print("TEST 2 PASS: Newly registered School student immediately appears in Admin Student Management under School mode.")

    # In College Mode -> should show Grisha + Priya College, NOT Amrita or Rohan School
    admin_dash.combo_category.set("College")
    admin_dash.load_students_table()
    updated_college_items = [admin_dash.tree_students.item(i)["values"][1] for i in admin_dash.tree_students.get_children()]
    assert len(updated_college_items) == 2, f"Expected 2 college students, got {len(updated_college_items)}"
    assert "Grisha" in updated_college_items
    assert "Priya College" in updated_college_items
    assert "Amrita" not in updated_college_items
    assert "Rohan School" not in updated_college_items
    print("TEST 3 PASS: Newly registered College student immediately appears in Admin Student Management under College mode.")

    # 5. Database safety checks
    all_students = db.get_all_students(filter_edu_type="All")
    assert len(all_students) == 4, f"Expected total 4 students in database, found {len(all_students)}"
    print("TEST 4 PASS: All 4 student records exist cleanly in the same database without duplicates.")

    admin_dash.destroy()
    root.quit()
    root.destroy()

    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    print("\n=== ALL REGISTRATION TO ADMIN SYNC TESTS PASSED (100%) ===")

if __name__ == "__main__":
    run_tests()
