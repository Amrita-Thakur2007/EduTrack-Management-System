import os
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DBManager

# Mock messagebox popups
last_info = []
last_warning = []
last_error = []

messagebox.showinfo = lambda title, msg: last_info.append((title, msg))
messagebox.showwarning = lambda title, msg: last_warning.append((title, msg))
messagebox.showerror = lambda title, msg: last_error.append((title, msg))

from gui.register import AccountRegistrationWindow

def run_tests():
    print("=== STARTING PARENT REGISTRATION EDUCATION TYPE LINKING VERIFICATION ===")

    db_path = f"scratch/test_par_edu_{int(time.time())}.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = DBManager(db_path=db_path)

    # 1. Create a School student in DB
    uid_school = db.create_user("SchoolChild01", "pass123", "Student")
    db.add_student({
        "student_id": "STU_SCHOOL_01",
        "name": "Aarav Sharma",
        "email": "aarav@school.edu",
        "phone": "9876543111",
        "father_name": "Rajesh Sharma",
        "parent_phone": "9876543000",
        "current_class": "10",
        "section": "A",
        "dob": "2006-01-01",
        "education_type": "School",
        "school_name": "St. Xavier School",
        "admission_date": "2024-04-01"
    }, uid_school)

    # 2. Create a College student in DB
    uid_college = db.create_user("CollegeChild02", "pass123", "Student")
    db.add_student({
        "student_id": "COL_ENR_02", # Primary key set to Enrollment Number
        "enrollment_number": "COL_ENR_02",
        "name": "Ananya Sharma",
        "email": "ananya@college.edu",
        "phone": "9876543222",
        "father_name": "Rajesh Sharma",
        "parent_phone": "9876543000",
        "course": "B.Tech Computer Science",
        "semester": "3rd Semester",
        "academic_year": "2nd Year",
        "dob": "2004-05-15",
        "education_type": "College",
        "college_name": "IIT Delhi",
        "admission_date": "2024-08-01"
    }, uid_college)

    root = tk.Tk()
    root.withdraw()

    # 3. Open Parent Registration Window
    reg_window = AccountRegistrationWindow(root, db, role="Parent")

    # Select 2 children
    reg_window.combo_num_children.set("2")
    reg_window._on_num_children_changed()

    assert len(reg_window.child_entries) == 2, f"Expected 2 child slots, got {len(reg_window.child_entries)}"

    slot1 = reg_window.child_entries[0]
    slot2 = reg_window.child_entries[1]

    # --- TEST CHILD 1 (School) ---
    slot1["combo_edu"].set("School")
    slot1["combo_edu"].event_generate("<<ComboboxSelected>>")
    assert slot1.get("entry_sid") is not None, "Child 1 must have Student ID entry for School choice!"
    assert slot1.get("entry_enr") is None, "Child 1 must NOT have Enrollment Number entry for School choice!"

    slot1["entry_sid"].insert(0, "STU_SCHOOL_01")
    reg_window._verify_child_slot(0)
    assert slot1["verified_student"] is not None, "Failed to verify Child 1 (School student)!"
    print("TEST 1 PASS: Child 1 (School -> Student ID) verified successfully.")

    # --- TEST CHILD 2 (College) ---
    slot2["combo_edu"].set("College")
    slot2["combo_edu"].event_generate("<<ComboboxSelected>>")
    assert slot2.get("entry_sid") is None, "Child 2 must NOT have Student ID entry for College choice!"
    assert slot2.get("entry_enr") is not None, "Child 2 must have Enrollment Number entry for College choice!"

    slot2["entry_enr"].insert(0, "COL_ENR_02")
    reg_window._verify_child_slot(1)
    assert slot2["verified_student"] is not None, "Failed to verify Child 2 (College student)!"
    print("TEST 2 PASS: Child 2 (College -> Enrollment Number) verified successfully.")

    # --- TEST BOTH CHOICE ---
    slot1["combo_edu"].set("Both")
    slot1["combo_edu"].event_generate("<<ComboboxSelected>>")
    assert slot1.get("entry_sid") is not None, "Both choice must render Student ID entry!"
    assert slot1.get("entry_enr") is not None, "Both choice must render Enrollment Number entry!"
    print("TEST 3 PASS: Education Type 'Both' renders both Student ID and Enrollment Number fields.")

    # Reset Child 1 to School & verify for submission
    slot1["combo_edu"].set("School")
    slot1["combo_edu"].event_generate("<<ComboboxSelected>>")
    slot1["entry_sid"].insert(0, "STU_SCHOOL_01")
    reg_window._verify_child_slot(0)

    # 4. Fill Parent Credentials & Submit Registration
    reg_window._entries["username"].insert(0, "ParentRajesh")
    reg_window._entries["password"].insert(0, "ParentPass123")
    reg_window._entries["confirm_password"].insert(0, "ParentPass123")
    reg_window._entries["favourite_person"].insert(0, "MyWife")

    reg_window._entries["name"].insert(0, "Rajesh Sharma")
    reg_window._entries["phone"].insert(0, "9876543000")

    reg_window.do_register()

    assert len(last_info) > 0, f"Parent registration failed! Errors: {last_error} Warnings: {last_warning}"
    
    # 5. Verify Parent in DB linked to BOTH children
    linked_parents = db.get_all_parents()
    parent_records = [p for p in linked_parents if p["phone"] == "9876543000"]
    assert len(parent_records) >= 2, f"Parent must be linked to at least 2 children, found {len(parent_records)}"

    print("TEST 4 PASS: Parent account successfully created and linked to both School and College children.")

    reg_window.destroy()
    root.quit()
    root.destroy()

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

    print("\n=== ALL PARENT EDUCATION TYPE LINKING VERIFICATIONS PASSED 100% ===")

if __name__ == "__main__":
    run_tests()
