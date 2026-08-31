import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import pickle
import numpy as np
import tkinter as tk
from tkinter import messagebox, ttk
from database.db_manager import DBManager

# Mock messagebox popups to prevent blocking test runs
messagebox.showinfo = lambda title, msg: print(f"Mock showinfo: {title} | {msg}")
messagebox.showwarning = lambda title, msg: print(f"Mock showwarning: {title} | {msg}")
messagebox.showerror = lambda title, msg: print(f"Mock showerror: {title} | {msg}")

from gui.admin_dashboard import AdminDashboard
from gui.teacher_dashboard import TeacherDashboard
from gui.register import AccountRegistrationWindow, RoleSelectModal

def test_everything():
    print("=== STARTING MODIFICATIONS VERIFICATION TEST ===")

    db_path = f"scratch/test_mods_flow_{int(time.time())}.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = DBManager(db_path=db_path)
    print("[OK] Test Database created.")

    # Create users, students, parent for testing
    u_school = db.create_user("school_stu", "pass", "Student")
    db.add_student({
        "student_id": "SCH_101",
        "name": "School Student A",
        "email": "schoola@school.edu",
        "phone": "1234567890",
        "education_type": "School",
        "school_name": "Delhi Public School",
        "current_class": "10",
        "section": "A",
        "admission_date": "2024-08-01",
        "study_hours": "3.0"
    }, u_school)

    u_college = db.create_user("college_stu", "pass", "Student")
    db.add_student({
        "student_id": "COL_101",
        "name": "College Student B",
        "email": "collegeb@college.edu",
        "phone": "0987654321",
        "education_type": "College",
        "college_name": "Delhi University",
        "course": "BCA",
        "enrollment_number": "COL_101",
        "semester": "1st Semester",
        "admission_date": "2024-08-01",
        "study_hours": "4.0"
    }, u_college)

    # Parent with BOTH children
    db.add_parent({
        "parent_id_code": "PID_PARENT",
        "student_id": "SCH_101",
        "name": "Parent P",
        "relationship": "Father",
        "phone": "5555555555",
        "email": "parent@gmail.com",
        "address": "Delhi"
    })
    db.add_parent({
        "parent_id_code": "PID_PARENT",
        "student_id": "COL_101",
        "name": "Parent P",
        "relationship": "Father",
        "phone": "5555555555",
        "email": "parent@gmail.com",
        "address": "Delhi"
    })

    # Leave requests
    db.add_leave_request("SCH_101", "2026-09-01", "Sick Leave")
    db.add_leave_request("COL_101", "2026-09-02", "College Event")

    # Create teacher in DB
    u_teacher = db.create_user("teacher_user", "password", "Teacher")
    db.add_teacher({
        "teacher_id": "T100",
        "name": "Teacher T",
        "phone": "1234567890",
        "email": "teacher@school.edu",
        "department": "Computer Science",
        "designation": "Professor",
        "joining_date": "2024-01-01"
    }, u_teacher)

    root = tk.Tk()
    root.withdraw()

    # 1. Verify Admin Dashboard Student Management Filter
    admin_dash = AdminDashboard(root, db, {"username": "admin_user", "name": "Admin"})
    admin_dash.show_students()
    
    # Check that Mode combo is present
    assert hasattr(admin_dash, "combo_category"), "Student Management Mode filter combo is missing!"
    
    # Test School Selection
    admin_dash.combo_category.set("School")
    admin_dash.load_students_table()
    rows = admin_dash.tree_students.get_children()
    assert len(rows) == 1, f"Expected 1 student for School, got {len(rows)}"
    vals = admin_dash.tree_students.item(rows[0])["values"]
    assert vals[0] == "SCH_101", f"Expected student SCH_101, got {vals[0]}"
    print("[OK] Admin Dashboard Student Management filter shows ONLY School student.")

    # Test College Selection
    admin_dash.combo_category.set("College")
    admin_dash.load_students_table()
    rows = admin_dash.tree_students.get_children()
    assert len(rows) == 1, f"Expected 1 student for College, got {len(rows)}"
    vals = admin_dash.tree_students.item(rows[0])["values"]
    assert vals[0] == "COL_101", f"Expected student COL_101, got {vals[0]}"
    print("[OK] Admin Dashboard Student Management filter shows ONLY College student.")

    # 2. Verify Teacher Management does NOT have Mode filter and shows all teachers
    admin_dash.show_teachers()
    assert not hasattr(admin_dash, "combo_teacher_category"), "Teacher Management must NOT have a Mode filter!"
    print("[OK] Teacher Management has no Mode filter.")

    # 3. Verify Admin Dashboard Parents Management Filter
    admin_dash.show_parents()
    assert hasattr(admin_dash, "combo_parent_category"), "Parents Management Mode filter combo is missing!"
    
    # Test School Selection
    admin_dash.combo_parent_category.set("School")
    admin_dash.load_parents_table()
    rows = admin_dash.tree_parents.get_children()
    assert len(rows) == 1, f"Expected 1 parent row for School child, got {len(rows)}"
    vals = admin_dash.tree_parents.item(rows[0])["values"]
    assert vals[0] == "PID_PARENT", f"Expected PID_PARENT, got {vals[0]}"
    assert vals[5] == "SCH_101", f"Expected linked child SCH_101, got {vals[5]}"
    
    # Test College Selection
    admin_dash.combo_parent_category.set("College")
    admin_dash.load_parents_table()
    rows = admin_dash.tree_parents.get_children()
    assert len(rows) == 1, f"Expected 1 parent row for College child, got {len(rows)}"
    vals = admin_dash.tree_parents.item(rows[0])["values"]
    assert vals[0] == "PID_PARENT", f"Expected PID_PARENT, got {vals[0]}"
    assert vals[5] == "COL_101", f"Expected linked child COL_101, got {vals[5]}"
    print("[OK] Parents Management Mode filter works. Parent appears under both modes based on linked child.")

    # 4. Verify Admin Dashboard Marks & Evaluation -> MLP Edition Center Filter
    admin_dash.show_ml_center()
    
    # Check that Mode category combo is present in ml center
    combos = []
    for child in admin_dash.content_frame.winfo_children():
        if isinstance(child, ttk.Frame):
            for gc in child.winfo_children():
                if isinstance(gc, ttk.Combobox):
                    combos.append(gc)
    assert len(combos) > 0, "ML Prediction Center Mode filter is missing!"
    ml_combo = combos[0]
    
    # Set School mode
    ml_combo.set("School")
    ml_combo.event_generate("<<ComboboxSelected>>")
    
    # Retrieve the treeview in ml center
    trees = []
    for child in admin_dash.content_frame.winfo_children():
        if isinstance(child, ttk.Frame):
            for gc in child.winfo_children():
                if isinstance(gc, ttk.Treeview):
                    trees.append(gc)
    assert len(trees) > 0, "ML Prediction Center tree is missing!"
    ml_tree = trees[0]
    rows = ml_tree.get_children()
    assert len(rows) == 1, f"Expected 1 ML row for School, got {len(rows)}"
    assert ml_tree.item(rows[0])["values"][0] == "SCH_101"
    
    # Set College mode
    ml_combo.set("College")
    ml_combo.event_generate("<<ComboboxSelected>>")
    rows = ml_tree.get_children()
    assert len(rows) == 1, f"Expected 1 ML row for College, got {len(rows)}"
    assert ml_tree.item(rows[0])["values"][0] == "COL_101"
    print("[OK] MLP Performance Predictions (MLP Edition Center) School/College filter verified successfully.")

    admin_dash.destroy()

    # 5. Verify Student Leave Requests filter in Teacher Dashboard
    teacher_dash = TeacherDashboard(root, db, {"id": u_teacher, "username": "teacher_user", "role": "Teacher"})
    teacher_dash.show_leave_requests()
    
    # Get combos in teacher content_frame
    t_combos = []
    for child in teacher_dash.content_frame.winfo_children():
        if isinstance(child, ttk.Frame):
            for gc in child.winfo_children():
                if isinstance(gc, ttk.Combobox):
                    t_combos.append(gc)
    assert len(t_combos) > 0, "Student Leave Requests Mode filter is missing!"
    leave_combo = t_combos[0]
    
    # Get tree
    t_trees = []
    for child in teacher_dash.content_frame.winfo_children():
        if isinstance(child, ttk.Frame):
            for gc in child.winfo_children():
                if isinstance(gc, ttk.Treeview):
                    t_trees.append(gc)
    assert len(t_trees) > 0, "Leave requests tree is missing!"
    leave_tree = t_trees[0]
    
    # School selected
    leave_combo.set("School")
    leave_combo.event_generate("<<ComboboxSelected>>")
    rows = leave_tree.get_children()
    assert len(rows) == 1, f"Expected 1 leave request for School, got {len(rows)}"
    assert leave_tree.item(rows[0])["values"][1] == "SCH_101"
    
    # College selected
    leave_combo.set("College")
    leave_combo.event_generate("<<ComboboxSelected>>")
    rows = leave_tree.get_children()
    assert len(rows) == 1, f"Expected 1 leave request for College, got {len(rows)}"
    assert leave_tree.item(rows[0])["values"][1] == "COL_101"
    print("[OK] Student Leave Requests filter verified in Teacher portal.")

    teacher_dash.destroy()

    # 6. Verify Teacher Registration Form
    reg_window = AccountRegistrationWindow(root, db, "Teacher")
    
    # Check that Teaching Mode combobox is removed
    assert "teaching_mode" not in reg_window._entries, "Teaching Mode field must be removed from Teacher Registration!"
    print("[OK] Teaching Mode field successfully removed.")

    # Check Face Registration Requirement
    reg_window._entries["username"].insert(0, "new_teacher")
    reg_window._entries["password"].insert(0, "password")
    reg_window._entries["confirm_password"].insert(0, "password")
    reg_window._entries["favourite_person"].insert(0, "Friend")
    reg_window._entries["teacher_id"].insert(0, "T101")
    reg_window._entries["name"].insert(0, "New Teacher")
    reg_window._entries["phone"].insert(0, "9999999999")
    
    # Attempt submit without face registration
    reg_window.do_register()
    assert not db.is_teacher_id_exists("T101"), "Teacher registration should NOT succeed without face registration!"
    print("[OK] Teacher registration blocked when face is not registered.")
    
    # Simulate face registration success
    reg_window.teacher_face_registered = True
    reg_window.do_register()
    assert db.is_teacher_id_exists("T101"), "Teacher registration should succeed with face registration!"
    print("[OK] Teacher registration successfully completed with face registration.")
    
    reg_window.destroy()

    # 7. Student Registration Course normal combobox & Relationship normal combobox
    reg_student = AccountRegistrationWindow(root, db, "Student")
    
    # Change edu type to College to build College fields
    reg_student.combo_edu_type.set("College")
    reg_student._on_edu_type_changed()
    
    # Check course combobox state
    course_combo = reg_student._entries["course"]
    assert str(course_combo.cget("state")) == "normal", f"Course combobox state must be 'normal' to allow custom program typing, got {course_combo.cget('state')}"
    print("[OK] Student College registration Course combobox allows text typing.")
    
    # Check relationship combobox state
    relation_combo = reg_student._entries["relationship"]
    assert str(relation_combo.cget("state")) == "normal", f"Relationship combobox state must be 'normal' to allow typing relationship, got {relation_combo.cget('state')}"
    print("[OK] Student registration Relationship combobox allows text typing.")

    reg_student.destroy()

    root.quit()
    root.destroy()

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

    print("=== ALL MODIFICATIONS VERIFICATION TESTS PASSED 100% ===")

if __name__ == "__main__":
    test_everything()
