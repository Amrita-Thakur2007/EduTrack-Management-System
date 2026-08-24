import os
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DBManager

# Mock messagebox for non-interactive test run
last_info = []
last_warning = []
last_error = []

messagebox.showinfo = lambda title, msg: last_info.append((title, msg))
messagebox.showwarning = lambda title, msg: last_warning.append((title, msg))
messagebox.showerror = lambda title, msg: last_error.append((title, msg))

from gui.register import AccountRegistrationWindow

def run_tests():
    print("=== STARTING SEMESTER AND YEAR EDITABLE FIELDS VERIFICATION ===")

    db_path = f"scratch/test_sem_year_{int(time.time())}.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = DBManager(db_path=db_path)

    root = tk.Tk()
    root.withdraw()

    # 1. Open Student Registration Window
    reg_window = AccountRegistrationWindow(root, db, role="Student")

    # Select College education type
    reg_window.combo_edu_type.set("College")
    reg_window._on_edu_type_changed()

    # 2. Verify Semester field is an editable Entry widget (NOT Combobox)
    assert "semester" in reg_window._entries, "Semester field MUST exist in College entries!"
    sem_widget = reg_window._entries["semester"]
    assert isinstance(sem_widget, ttk.Entry), f"Semester widget MUST be ttk.Entry, got {type(sem_widget)}"
    assert not isinstance(sem_widget, ttk.Combobox), "Semester widget MUST NOT be a Combobox dropdown!"

    # 3. Verify Year field is an editable Entry widget (NOT Combobox)
    assert "year" in reg_window._entries, "Year field MUST exist in College entries!"
    year_widget = reg_window._entries["year"]
    assert isinstance(year_widget, ttk.Entry), f"Year widget MUST be ttk.Entry, got {type(year_widget)}"
    assert not isinstance(year_widget, ttk.Combobox), "Year widget MUST NOT be a Combobox dropdown!"

    print("TEST 1 PASS: Both Semester and Year fields are normal editable text input fields with NO dropdown options.")

    # 4. Fill form with custom manual text for Semester ("3rd Semester") and Year ("2nd Year")
    reg_window._entries["username"].insert(0, "CollegeUser88")
    reg_window._entries["password"].insert(0, "Pass1234")
    reg_window._entries["confirm_password"].insert(0, "Pass1234")
    reg_window._entries["favourite_person"].insert(0, "TeacherHero")

    reg_window._entries["name"].insert(0, "Vikram Malhotra")
    reg_window._entries["email"].insert(0, "vikram@college.edu")
    reg_window._entries["phone"].insert(0, "9876543210")
    reg_window._entries["dob"].delete(0, tk.END)
    reg_window._entries["dob"].insert(0, "2003-08-20")
    reg_window._entries["address"].insert(0, "College Campus Hostel 4")
    reg_window._entries["father_name"].insert(0, "Ramesh Malhotra")
    reg_window._entries["parent_phone"].insert(0, "9876543211")
    reg_window._entries["study_hours"].delete(0, tk.END)
    reg_window._entries["study_hours"].insert(0, "5.0")

    # College specific fields
    reg_window._entries["college_name"].insert(0, "Delhi Technological University")
    reg_window._entries["enrollment_number"].insert(0, "DTU_ENR_8899")
    reg_window._entries["course"].delete(0, tk.END)
    reg_window._entries["course"].insert(0, "B.Tech Software Engineering")

    # Type manual custom values in Semester and Year
    sem_widget.delete(0, tk.END)
    sem_widget.insert(0, "3rd Semester")
    assert sem_widget.get() == "3rd Semester", "Manual typing in Semester failed!"

    year_widget.delete(0, tk.END)
    year_widget.insert(0, "2nd Year")
    assert year_widget.get() == "2nd Year", "Manual typing in Year failed!"

    reg_window._entries["admission_date"].delete(0, tk.END)
    reg_window._entries["admission_date"].insert(0, "2024-08-01")

    # Submit registration
    reg_window.do_register()

    assert len(last_info) > 0, f"Registration failed! Warnings/Errors: {last_warning} {last_error}"
    print("TEST 2 PASS: Student Registration submitted successfully with typed Semester and Year.")

    # 5. Verify saved record in database contains exact typed values
    student_rec = db.get_student("DTU_ENR_8899")
    assert student_rec is not None, "Student record was not found in DB!"
    assert "3rd Semester" in student_rec["semester"], f"Semester mismatch in saved DB record: {student_rec['semester']}"
    assert student_rec["academic_year"] == "2nd Year", f"Academic Year mismatch in saved DB record: {student_rec['academic_year']}"

    print("TEST 3 PASS: Exact typed Semester ('3rd Semester') and Year ('2nd Year') verified in SQLite database.")

    reg_window.destroy()
    root.quit()
    root.destroy()

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

    print("\n=== ALL SEMESTER AND YEAR EDITABLE FIELDS VERIFICATIONS PASSED 100% ===")

if __name__ == "__main__":
    run_tests()
