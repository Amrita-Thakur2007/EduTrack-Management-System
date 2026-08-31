import os
import sys
import time
import tkinter as tk
from tkinter import messagebox
from database.db_manager import DBManager

sys.path.insert(0, ".")
# Mock messagebox popups
messagebox.showinfo = lambda title, msg: None
messagebox.showwarning = lambda title, msg: None
messagebox.showerror = lambda title, msg: None

from gui.admin_dashboard import AdminDashboard
from gui.parent_forms import ParentFormDialog

def run_tests():
    print("=== STARTING PARENT MANAGEMENT TESTS ===")

    db_path = f"scratch/test_parent_mgmt_{int(time.time())}.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = DBManager(db_path=db_path)

    # 1. Register students
    # Child A (School)
    u1 = db.create_user("ChildAUser", "Pass1234", "Student")
    db.add_student({
        "student_id": "ST_SCH_A",
        "name": "Child A",
        "email": "childa@school.edu",
        "education_type": "School",
        "school_name": "Delhi Public School",
        "current_class": "10",
        "section": "A"
    }, u1)

    # Child B (College)
    u2 = db.create_user("ChildBUser", "Pass1234", "Student")
    db.add_student({
        "student_id": "ST_COL_B",
        "name": "Child B",
        "email": "childb@college.edu",
        "education_type": "College",
        "college_name": "Delhi University",
        "course": "B.Com",
        "enrollment_number": "EN_B",
        "semester": "Semester 2",
        "academic_year": "1st Year"
    }, u2)

    # 2. Add Parent for Child A
    db.add_parent({
        "parent_id_code": "PAR001",
        "student_id": "ST_SCH_A",
        "name": "Parent Father",
        "relationship": "Father",
        "phone": "9876543210",
        "email": "father@test.com",
        "address": "Delhi"
    })

    # Add Parent for Child B (Multiple children scenario, same parent_id_code but linked to Child B)
    db.add_parent({
        "parent_id_code": "PAR001",
        "student_id": "ST_COL_B",
        "name": "Parent Father",
        "relationship": "Father",
        "phone": "9876543210",
        "email": "father@test.com",
        "address": "Delhi"
    })

    root = tk.Tk()
    root.withdraw()

    # 3. Test GUI filtering
    admin_user = {"id": 1, "username": "admin", "role": "Admin"}
    admin_dash = AdminDashboard(root, db, admin_user)
    admin_dash.show_parents()

    # TEST 1: SCHOOL category selected
    admin_dash.combo_parent_category.set("School")
    admin_dash.combo_parent_category.event_generate("<<ComboboxSelected>>")

    items_school = admin_dash.tree_parents.get_children()
    linked_children_school = [admin_dash.tree_parents.item(item)["values"][5] for item in items_school]
    assert len(items_school) == 1, f"Expected 1 parent entry in School, got {len(items_school)}"
    assert "ST_SCH_A" in linked_children_school, f"Expected Child A in School mode, got {linked_children_school}"
    assert "ST_COL_B" not in linked_children_school, "Child B should not appear in School mode!"
    print("TEST 1 PASS: School mode parent filtering verified (multiple children handled correctly).")

    # TEST 2: COLLEGE category selected
    admin_dash.combo_parent_category.set("College")
    admin_dash.combo_parent_category.event_generate("<<ComboboxSelected>>")

    items_college = admin_dash.tree_parents.get_children()
    linked_children_college = [admin_dash.tree_parents.item(item)["values"][5] for item in items_college]
    assert len(items_college) == 1, f"Expected 1 parent entry in College, got {len(items_college)}"
    assert "ST_COL_B" in linked_children_college, f"Expected Child B in College mode, got {linked_children_college}"
    assert "ST_SCH_A" not in linked_children_college, "Child A should not appear in College mode!"
    print("TEST 2 PASS: College mode parent filtering verified (multiple children handled correctly).")

    # TEST 3: Parent Edit and Save functionality
    # Open dialog for editing PAR001
    # Note: Dialog is transient and grabs focus, we just mock save_parent calls
    dialog = ParentFormDialog(admin_dash, db, parent_id_code="PAR001")
    assert dialog.is_edit is True
    
    # Change phone and save
    dialog.entry_phone.delete(0, tk.END)
    dialog.entry_phone.insert(0, "9999999999")
    
    # Trigger save
    dialog.save_parent()
    
    # Check database: both records for PAR001 should have updated phone number
    all_p = db.get_all_parents()
    for p in all_p:
        if p["parent_id_code"] == "PAR001":
            assert p["phone"] == "9999999999", f"Expected updated phone to be 9999999999, got {p['phone']}"
            
    print("TEST 3 PASS: Parent Edit & Save functionality works correctly. Phone number successfully updated.")

    admin_dash.destroy()
    root.quit()
    root.destroy()

    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    print("\n=== ALL PARENT MANAGEMENT TESTS PASSED 100% ===")

if __name__ == "__main__":
    run_tests()
