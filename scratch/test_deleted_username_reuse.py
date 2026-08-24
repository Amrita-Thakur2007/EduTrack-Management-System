import os
import sys
import time
import tkinter as tk
from database.db_manager import DBManager

def run_tests():
    print("=== STARTING DELETED USERNAME RE-USE VERIFICATION ===")

    db_path = f"scratch/test_reuse_{int(time.time())}.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = DBManager(db_path=db_path)

    # 1. Register active Student: Rahul123
    u1 = "Rahul123"
    uid1 = db.create_user(u1, "Password123", "Student", "FavPerson")
    assert uid1 is not None, "Failed to create user Rahul123"
    
    db.add_student({
        "student_id": u1,
        "name": "Rahul Sharma",
        "email": "rahul@example.com",
        "phone": "9876543210",
        "father_name": "Father Sharma",
        "father_phone": "9876543211",
        "current_class": "10",
        "section": "A",
        "dob": "2005-01-01",
        "education_type": "School",
        "school_name": "Delhi Public School",
        "admission_date": "2024-04-01",
        "study_hours": 3.0
    }, uid1)

    # 2. Verify Rahul123 is reported as active username existing
    assert db.is_username_exists(u1) is True, "Active user Rahul123 must report username exists!"

    # 3. Register active Teacher: Priya456
    u2 = "Priya456"
    uid2 = db.create_user(u2, "Password123", "Teacher", "FavPerson")
    assert uid2 is not None, "Failed to create user Priya456"

    db.add_teacher({
        "teacher_id": u2,
        "name": "Priya Singh",
        "phone": "9876543212",
        "email": "priya@example.com",
        "department": "Computer Science"
    }, uid2)

    assert db.is_username_exists(u2) is True, "Active teacher Priya456 must report username exists!"
    print("TEST 1 PASS: Active accounts (Rahul123, Priya456) properly detected as duplicate/existing usernames.")

    # 4. Admin Deletes Student Rahul123
    del_ok = db.delete_student(u1)
    assert del_ok is True, "Failed to delete student Rahul123"

    # 5. Verify username Rahul123 is now AVAILABLE for new registration
    assert db.is_username_exists(u1) is False, "Deleted username Rahul123 MUST be available for new registration!"
    print("TEST 2 PASS: Deleted username Rahul123 is now available for new registration.")

    # 6. Register NEW Student with the SAME username Rahul123
    uid1_new = db.create_user(u1, "NewPassword456", "Student", "NewFavPerson")
    assert uid1_new is not None, "Registration MUST succeed for previously deleted username Rahul123!"

    ok_new = db.add_student({
        "student_id": u1,
        "name": "Rahul Verma",
        "email": "rahulverma@example.com",
        "phone": "9876543299",
        "father_name": "Father Verma",
        "father_phone": "9876543298",
        "current_class": "12",
        "section": "B",
        "dob": "2004-06-10",
        "education_type": "School",
        "school_name": "Modern School",
        "admission_date": "2024-04-01",
        "study_hours": 4.0
    }, uid1_new)
    assert ok_new is True, "Failed to save new student with reused username Rahul123"
    print("TEST 3 PASS: New user successfully registered using previously deleted username Rahul123.")

    # 7. Verify active user Priya456 is STILL protected against duplicate registration
    assert db.is_username_exists(u2) is True, "Active user Priya456 must STILL be protected against duplicate registration!"
    print("TEST 4 PASS: Active accounts continue to be strictly protected against duplicate registration.")

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

    print("\n=== ALL DELETED USERNAME RE-USE VERIFICATIONS PASSED 100% ===")

if __name__ == "__main__":
    run_tests()
