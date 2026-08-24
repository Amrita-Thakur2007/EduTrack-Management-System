import os
import sys
import time
import tkinter as tk
from database.db_manager import DBManager
from gui.teacher_dashboard import TeacherDashboard

def run_tests():
    print("=== STARTING TEACHER WORKSTATION SCHOOL & COLLEGE DISPLAY VERIFICATION ===")

    db_path = f"scratch/test_teacher_disp_{int(time.time())}.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = DBManager(db_path=db_path)

    # 1. Create a Teacher User & Record
    uid_teacher = db.create_user("TeacherJohn", "Pass1234", "Teacher")
    db.add_teacher({
        "teacher_id": "TCH_101",
        "name": "John Doe",
        "phone": "9988776655",
        "email": "john@school.edu",
        "department": "Science",
        "designation": "Senior Teacher",
        "joining_date": "2020-01-01"
    }, uid_teacher)

    user_data = {
        "id": uid_teacher,
        "username": "TeacherJohn",
        "role": "Teacher"
    }

    # 2. Register School Student
    uid_school = db.create_user("SchoolStudent99", "Pass1234", "Student")
    db.add_student({
        "student_id": "SCH_ID_99",
        "name": "Rahul Verma",
        "email": "rahul@school.edu",
        "phone": "9123456789",
        "dob": "2008-04-10",
        "gender": "Male",
        "address": "House 12, Park Street, New Delhi",
        "father_name": "Suresh Verma",
        "parent_phone": "9123456780",
        "education_type": "School",
        "school_name": "Greenwood High School",
        "current_class": "10",
        "section": "B",
        "admission_date": "2022-04-01"
    }, uid_school)

    # 3. Register College Student
    uid_college = db.create_user("CollegeStudent88", "Pass1234", "Student")
    db.add_student({
        "student_id": "COL_ENR_88",
        "enrollment_number": "COL_ENR_88",
        "name": "Priya Sharma",
        "email": "priya@college.edu",
        "phone": "9876543210",
        "dob": "2003-11-25",
        "gender": "Female",
        "address": "Flat 4B, Metro Towers, Mumbai",
        "father_name": "Ramesh Sharma",
        "parent_phone": "9876543200",
        "education_type": "College",
        "college_name": "St. Xavier College",
        "course": "B.Sc Computer Science",
        "semester": "4th Semester",
        "academic_year": "2nd Year",
        "admission_date": "2023-08-01"
    }, uid_college)

    root = tk.Tk()
    root.withdraw()

    dashboard = TeacherDashboard(root, db, user_data)
    dashboard.show_students()

    # --- VERIFY SCHOOL DISPLAY ---
    dashboard.combo_category.set("School")
    dashboard.load_students_table()

    school_items = dashboard.tree.get_children()
    assert len(school_items) == 1, f"Expected 1 School student, found {len(school_items)}"
    sch_vals = dashboard.tree.item(school_items[0])["values"]

    assert sch_vals[0] == "SCH_ID_99", f"Expected Student ID SCH_ID_99, got {sch_vals[0]}"
    assert sch_vals[1] == "Rahul Verma", f"Expected Name Rahul Verma, got {sch_vals[1]}"
    assert sch_vals[2] == "Greenwood High School", f"Expected School Greenwood High School, got {sch_vals[2]}"
    assert str(sch_vals[3]) == "10", f"Expected Class 10, got {sch_vals[3]}"
    assert sch_vals[4] == "B", f"Expected Section B, got {sch_vals[4]}"
    assert sch_vals[5] == "2022-04-01", f"Expected Admission Date 2022-04-01, got {sch_vals[5]}"
    assert sch_vals[6] == "2008-04-10", f"Expected DOB 2008-04-10, got {sch_vals[6]}"
    assert sch_vals[7] == "Male", f"Expected Gender Male, got {sch_vals[7]}"
    assert str(sch_vals[8]) == "9123456789", f"Expected Phone 9123456789, got {sch_vals[8]}"
    assert sch_vals[9] == "rahul@school.edu", f"Expected Email rahul@school.edu, got {sch_vals[9]}"
    assert sch_vals[10] == "Suresh Verma", f"Expected Parent Name Suresh Verma, got {sch_vals[10]}"
    assert str(sch_vals[11]) == "9123456780", f"Expected Parent Phone 9123456780, got {sch_vals[11]}"
    assert "Park Street" in sch_vals[12], f"Expected Address containing Park Street, got {sch_vals[12]}"

    print("TEST 1 PASS: Teacher Workstation -> School selected: ONLY School students and ALL stored details (ID, Name, School, Class, Section, Admission Date, DOB, Gender, Phone, Email, Parent Name, Parent Phone, Address) displayed.")

    # --- VERIFY COLLEGE DISPLAY ---
    dashboard.combo_category.set("College")
    dashboard.load_students_table()

    college_items = dashboard.tree.get_children()
    assert len(college_items) == 1, f"Expected 1 College student, found {len(college_items)}"
    col_vals = dashboard.tree.item(college_items[0])["values"]

    assert col_vals[0] == "COL_ENR_88", f"Expected Student ID COL_ENR_88, got {col_vals[0]}"
    assert col_vals[1] == "COL_ENR_88", f"Expected Enrollment Number COL_ENR_88, got {col_vals[1]}"
    assert col_vals[2] == "Priya Sharma", f"Expected Name Priya Sharma, got {col_vals[2]}"
    assert col_vals[3] == "St. Xavier College", f"Expected College St. Xavier College, got {col_vals[3]}"
    assert col_vals[4] == "B.Sc Computer Science", f"Expected Course B.Sc Computer Science, got {col_vals[4]}"
    assert col_vals[5] == "4th Semester", f"Expected Semester 4th Semester, got {col_vals[5]}"
    assert col_vals[6] == "2nd Year", f"Expected Academic Year 2nd Year, got {col_vals[6]}"
    assert col_vals[7] == "2023-08-01", f"Expected Admission Date 2023-08-01, got {col_vals[7]}"
    assert col_vals[8] == "2003-11-25", f"Expected DOB 2003-11-25, got {col_vals[8]}"
    assert col_vals[9] == "Female", f"Expected Gender Female, got {col_vals[9]}"
    assert str(col_vals[10]) == "9876543210", f"Expected Phone 9876543210, got {col_vals[10]}"
    assert col_vals[11] == "priya@college.edu", f"Expected Email priya@college.edu, got {col_vals[11]}"
    assert col_vals[12] == "Ramesh Sharma", f"Expected Parent Name Ramesh Sharma, got {col_vals[12]}"
    assert str(col_vals[13]) == "9876543200", f"Expected Parent Phone 9876543200, got {col_vals[13]}"
    assert "Metro Towers" in col_vals[14], f"Expected Address containing Metro Towers, got {col_vals[14]}"

    print("TEST 2 PASS: Teacher Workstation -> College selected: ONLY College students and ALL stored details (ID, Enrollment No, Name, College, Course, Semester, Year, Admission Date, DOB, Gender, Phone, Email, Parent Name, Parent Phone, Address) displayed.")

    dashboard.destroy()
    root.quit()
    root.destroy()

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

    print("\n=== ALL TEACHER WORKSTATION SCHOOL & COLLEGE DISPLAY TESTS PASSED 100% ===")

if __name__ == "__main__":
    run_tests()
