import os
import sys
import time
import tkinter as tk

sys.path.insert(0, ".")
from database.db_manager import DBManager
from gui.admin_dashboard import AdminDashboard

def run_tests():
    print("=== STARTING PARENT GROUPING & SEARCH HIGHLIGHT TESTS ===")

    db_path = f"scratch/test_fixes_{int(time.time())}.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = DBManager(db_path=db_path)

    # 1. Add students: Amrita (School), Rahul (School), Grisha (College)
    u1 = db.create_user("AmritaUser", "Pass123", "Student")
    db.add_student({
        "student_id": "ST_SCH_1",
        "name": "Amrita",
        "email": "amrita@school.edu",
        "education_type": "School",
        "school_name": "SKV NO-1",
        "current_class": "12",
        "section": "B"
    }, u1)

    u2 = db.create_user("RahulUser", "Pass123", "Student")
    db.add_student({
        "student_id": "ST_SCH_2",
        "name": "Rahul",
        "email": "rahul@school.edu",
        "education_type": "School",
        "school_name": "SKV NO-1",
        "current_class": "10",
        "section": "A"
    }, u2)

    u3 = db.create_user("GrishaUser", "Pass123", "Student")
    db.add_student({
        "student_id": "ST_COL_1",
        "name": "Grisha",
        "email": "grisha@college.edu",
        "education_type": "College",
        "college_name": "Rajdhani College",
        "course": "BCA",
        "enrollment_number": "ST_COL_1",
        "semester": "Semester 2",
        "academic_year": "2024-2025"
    }, u3)

    # 2. Add Parent "Kamotha" connected to BOTH Child 1 (Amrita) and Child 2 (Rahul)
    p1 = db.create_user("KamothaUser", "Pass123", "Parent")
    db.add_parent({
        "parent_id_code": "PAR_KAMOTHA",
        "student_id": "ST_SCH_1",
        "name": "Kamotha",
        "phone": "9876543210",
        "email": "kamotha@example.com",
        "relationship": "Mother"
    }, p1)

    db.add_parent({
        "parent_id_code": "PAR_KAMOTHA",
        "student_id": "ST_SCH_2",
        "name": "Kamotha",
        "phone": "9876543210",
        "email": "kamotha@example.com",
        "relationship": "Mother"
    }, p1)

    root = tk.Tk()
    root.withdraw()

    admin_user = {"id": 1, "username": "admin", "role": "Admin"}
    admin_dash = AdminDashboard(root, db, admin_user)

    # --- TEST FIX 1: Parent Management Grouping ---
    admin_dash.show_parents()
    admin_dash.combo_parent_category.set("School")
    admin_dash.load_parents_table()

    parent_items = admin_dash.tree_parents.get_children()
    # Should only be 1 parent row for Kamotha, not 2!
    assert len(parent_items) == 1, f"Expected exactly 1 parent row, got {len(parent_items)}"
    p_values = admin_dash.tree_parents.item(parent_items[0])["values"]
    assert p_values[1] == "Kamotha"
    assert "ST_SCH_1" in p_values[5] and "ST_SCH_2" in p_values[5], f"Expected both student IDs in linked column, got {p_values[5]}"
    print("TEST 1 PASS: Kamotha appears ONLY ONCE in Parent Management with all linked children.")

    # --- TEST FIX 2: Student Management Search Highlighting ---
    admin_dash.show_students()
    admin_dash.combo_category.set("School")
    admin_dash.load_students_table()

    # Baseline school: 2 students (Amrita, Rahul)
    all_school_items = admin_dash.tree_students.get_children()
    assert len(all_school_items) == 2, f"Expected 2 school students, got {len(all_school_items)}"

    # Search for "Rahul" and simulate Enter
    admin_dash.entry_search.delete(0, tk.END)
    admin_dash.entry_search.insert(0, "Rahul")
    admin_dash.entry_search.event_generate("<Return>")
    admin_dash.load_students_table()

    # Check that ALL students remain in table (not deleted)
    search_school_items = admin_dash.tree_students.get_children()
    assert len(search_school_items) == 2, f"Expected all 2 students to remain visible in list, got {len(search_school_items)}"

    # Check tags
    rahul_item = [i for i in search_school_items if admin_dash.tree_students.item(i)["values"][1] == "Rahul"][0]
    amrita_item = [i for i in search_school_items if admin_dash.tree_students.item(i)["values"][1] == "Amrita"][0]

    assert "highlighted" in admin_dash.tree_students.item(rahul_item)["tags"], "Rahul should have 'highlighted' tag"
    assert "normal" in admin_dash.tree_students.item(amrita_item)["tags"], "Amrita should have 'normal' tag"
    print("TEST 2 PASS: Searching for 'Rahul' highlights Rahul in bold while preserving Amrita in the list.")

    # Switch to College and search for "Grisha"
    admin_dash.combo_category.set("College")
    admin_dash.entry_search.delete(0, tk.END)
    admin_dash.entry_search.insert(0, "Grisha")
    admin_dash.load_students_table()

    college_items = admin_dash.tree_students.get_children()
    assert len(college_items) == 1
    grisha_item = college_items[0]
    assert admin_dash.tree_students.item(grisha_item)["values"][1] == "Grisha"
    assert "highlighted" in admin_dash.tree_students.item(grisha_item)["tags"]
    print("TEST 3 PASS: College search for 'Grisha' works and highlights Grisha.")

    admin_dash.destroy()
    root.quit()
    root.destroy()

    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    print("\n=== ALL PARENT GROUPING & SEARCH HIGHLIGHT TESTS PASSED (100%) ===")

if __name__ == "__main__":
    run_tests()
