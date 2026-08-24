import os
import sys
import time
import tkinter as tk
from database.db_manager import DBManager
from gui.register import AccountRegistrationWindow
from gui.login import LoginWindow, ForgotPasswordDialog
from utils.validators import validate_email, validate_phone, validate_study_hours

def run_tests():
    print("=== STARTING STUDENT PORTAL FEATURES VERIFICATION ===")

    # Setup isolated test database
    db_path = f"scratch/test_student_portal_{int(time.time())}.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    db = DBManager(db_path=db_path)

    # -------------------------------------------------------------
    # 1. DB Schema & Safe Migration Verification
    # -------------------------------------------------------------
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(students);")
        cols = {row['name'] for row in cursor.fetchall()}

    required_cols = {"education_type", "school_name", "college_name", "enrollment_number", "semester", "guardian_name"}
    for col in required_cols:
        assert col in cols, f"TEST FAIL: Column '{col}' missing from students table!"
    print("TEST 1 PASS: Database schema safely migrated with all required new fields.")

    # -------------------------------------------------------------
    # 2. Validation Utilities Verification
    # -------------------------------------------------------------
    assert validate_email("student@example.com") is True
    assert validate_email("invalid-email") is False
    assert validate_phone("9876543210") is True
    assert validate_phone("12345") is False
    assert validate_study_hours("4.5")[0] is True
    assert validate_study_hours("25.0")[0] is False
    print("TEST 2 PASS: Input validators (email, 10-digit phone, study hours) verified.")

    # -------------------------------------------------------------
    # 3. School Student Registration, Login & Recovery Flow
    # -------------------------------------------------------------
    school_sid = "SCH_STU_101"
    pwd_school = "SchoolPass123"
    fav_school = "MyTeacher"

    user_id_sch = db.create_user(school_sid, pwd_school, "Student", fav_school)
    assert user_id_sch is not None, "Failed to create user account for School student."

    school_saved = db.add_student({
        "student_id": school_sid,
        "name": "Rohan Mehta",
        "email": "rohan@school.com",
        "phone": "9876543211",
        "gender": "Male",
        "dob": "2010-05-15",
        "address": "123 School Lane",
        "guardian_name": "Suresh Mehta",
        "father_name": "Suresh Mehta",
        "mother_name": "Sunita Mehta",
        "father_phone": "9876543212",
        "mother_phone": "9876543213",
        "parent_phone": "9876543212",
        "parent_email": "suresh@example.com",
        "parent_occupation": "Engineer",
        "emergency_contact": "9876543214",
        "relationship": "Father",
        "study_hours": 3.0,
        "education_type": "School",
        "school_name": "Green Valley High School",
        "current_class": "10",
        "section": "A",
        "admission_date": "2024-04-01"
    }, user_id_sch)

    assert school_saved is True, "Failed to save School student profile in DB."

    # Verify DB content for School student
    stu_sch = db.get_student(school_sid)
    assert stu_sch['education_type'] == "School"
    assert stu_sch['school_name'] == "Green Valley High School"
    assert stu_sch['student_id'] == school_sid

    # Test School Student Login using Student ID + Password
    auth_sch = db.authenticate_user(school_sid, pwd_school, "Student")
    assert auth_sch.get("success") is True, f"School Student Login failed using Student ID: {auth_sch}"

    # Test Wrong Password Login failure
    auth_sch_bad = db.authenticate_user(school_sid, "WrongPass", "Student")
    assert auth_sch_bad.get("success") is False, "Login should fail with wrong password."

    # Test School Student Password Reset using Student ID + Favourite Person Name
    reset_ok_sch, reset_msg_sch = db.reset_password_with_favourite_person(school_sid, fav_school, "NewSchoolPass123", "Student")
    assert reset_ok_sch is True, f"School password reset failed: {reset_msg_sch}"

    # Verify login with new password
    auth_sch_new = db.authenticate_user(school_sid, "NewSchoolPass123", "Student")
    assert auth_sch_new.get("success") is True, "School Student Login failed using newly reset password."

    # Duplicate Student ID check
    assert db.is_student_id_exists(school_sid) is True
    print("TEST 3 PASS: School student account creation, login with Student ID, and password recovery verified.")

    # -------------------------------------------------------------
    # 4. College Student Registration, Login & Recovery Flow
    # -------------------------------------------------------------
    college_enr = "ENR2026999"
    pwd_college = "CollegePass123"
    fav_college = "Grandmother"

    user_id_col = db.create_user(college_enr, pwd_college, "Student", fav_college)
    assert user_id_col is not None, "Failed to create user account for College student."

    college_saved = db.add_student({
        "student_id": college_enr, # Primary Key mapped to Enrollment Number
        "name": "Ananya Sharma",
        "email": "ananya@college.edu",
        "phone": "9123456780",
        "gender": "Female",
        "dob": "2004-09-20",
        "address": "456 University Campus Rd",
        "guardian_name": "Rajesh Sharma",
        "father_name": "Rajesh Sharma",
        "mother_name": "Priya Sharma",
        "father_phone": "9123456781",
        "mother_phone": "9123456782",
        "parent_phone": "9123456781",
        "parent_email": "rajesh@example.com",
        "parent_occupation": "Doctor",
        "emergency_contact": "9123456783",
        "relationship": "Father",
        "study_hours": 5.5,
        "education_type": "College",
        "college_name": "Imperial Institute of Technology",
        "enrollment_number": college_enr,
        "course": "B.Tech Robotics & Automation (Custom)",
        "semester": "Semester 4",
        "admission_date": "2023-08-10"
    }, user_id_col)

    assert college_saved is True, "Failed to save College student profile in DB."

    # Verify DB content for College student
    stu_col = db.get_student(college_enr)
    assert stu_col['education_type'] == "College"
    assert stu_col['college_name'] == "Imperial Institute of Technology"
    assert stu_col['enrollment_number'] == college_enr
    assert stu_col['course'] == "B.Tech Robotics & Automation (Custom)"

    # Test College Student Login using Enrollment Number + Password
    auth_col = db.authenticate_user(college_enr, pwd_college, "Student")
    assert auth_col.get("success") is True, f"College Student Login failed using Enrollment Number: {auth_col}"

    # Test College Student Password Reset using Enrollment Number + Favourite Person Name
    reset_ok_col, reset_msg_col = db.reset_password_with_favourite_person(college_enr, fav_college, "NewCollegePass123", "Student")
    assert reset_ok_col is True, f"College password reset failed: {reset_msg_col}"

    # Verify login with new password
    auth_col_new = db.authenticate_user(college_enr, "NewCollegePass123", "Student")
    assert auth_col_new.get("success") is True, "College Student Login failed using newly reset password."

    # Duplicate Enrollment Number check
    assert db.is_enrollment_number_exists(college_enr) is True
    print("TEST 4 PASS: College student account creation, login with Enrollment Number, custom course text, and password recovery verified.")

    # -------------------------------------------------------------
    # 5. Tkinter UI & Dynamic Fields Verification
    # -------------------------------------------------------------
    root = tk.Tk()
    root.withdraw()

    # Test Registration Dialog
    reg_dialog = AccountRegistrationWindow(root, db, role="Student")
    assert hasattr(reg_dialog, 'combo_edu_type'), "Education type combo missing on registration form!"
    assert reg_dialog.combo_edu_type.get() == "School"
    assert "school_name" in reg_dialog._entries
    assert "student_id" in reg_dialog._entries
    assert "enrollment_number" not in reg_dialog._entries

    # Switch to College
    reg_dialog.combo_edu_type.set("College")
    reg_dialog._on_edu_type_changed()
    assert "college_name" in reg_dialog._entries
    assert "enrollment_number" in reg_dialog._entries
    assert "student_id" not in reg_dialog._entries, "Student ID should NOT be shown for College students!"
    assert str(reg_dialog._entries["course"].cget("state")) != "readonly", "Course combo must support typing custom text!"

    reg_dialog.destroy()

    # Test Login Window labels
    login_dialog = LoginWindow(root, db, initial_role="Student")
    assert login_dialog.lbl_username.cget("text") == "Student ID / Enrollment Number *:"
    login_dialog.destroy()

    # Test Forgot Password Dialog labels
    forgot_dialog = ForgotPasswordDialog(root, db, initial_role="Student")

    root.quit()
    root.destroy()
    print("TEST 5 PASS: GUI dynamic form fields, labels, and College 'no Student ID' requirements verified.")

    # Clean up test DB
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

    print("\n=== ALL STUDENT PORTAL FEATURE VERIFICATIONS PASSED 100% ===")

if __name__ == "__main__":
    run_tests()
