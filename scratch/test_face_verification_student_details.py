import os
import sys
import time
import pickle
import numpy as np
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

from face_attendance.face_recognition import FaceAttendanceScannerWindow

def run_tests():
    print("=== STARTING FACE VERIFICATION STUDENT DETAILS DISPLAY TEST ===")

    db_path = f"scratch/test_face_det_{int(time.time())}.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = DBManager(db_path=db_path)

    # 1. Register 2 Students with complete details
    u1 = db.create_user("RohanUser", "Pass1234", "Student")
    db.add_student({
        "student_id": "STU_FACE_1",
        "name": "Rohan Verma",
        "email": "rohan@school.edu",
        "phone": "9811223344",
        "education_type": "School",
        "school_name": "Delhi Public School",
        "current_class": "10",
        "section": "A",
        "roll_number": "101",
        "admission_date": "2024-04-01"
    }, u1)

    u2 = db.create_user("AnanyaUser", "Pass1234", "Student")
    db.add_student({
        "student_id": "STU_FACE_2",
        "name": "Ananya Roy",
        "email": "ananya@college.edu",
        "phone": "9822334455",
        "education_type": "College",
        "college_name": "IIT Delhi",
        "course": "Computer Science",
        "enrollment_number": "ENR_9900",
        "semester": "3rd Semester",
        "academic_year": "2nd Year"
    }, u2)

    # Save mock face encodings
    dummy_enc = pickle.dumps(np.zeros((100, 100), dtype=np.uint8))
    db.save_face_encoding("STU_FACE_1", dummy_enc)
    db.save_face_encoding("STU_FACE_2", dummy_enc)

    root = tk.Tk()
    root.withdraw()

    # 2. Open Face Attendance Scanner Window
    scanner = FaceAttendanceScannerWindow(root, db, target_role="Student")

    # TEST 1: Initial state before verification -> details must be empty (--)
    assert "--" in scanner.lbl_det_1.cget("text"), "Initial details should be empty (--)"
    assert "--" in scanner.lbl_det_2.cget("text"), "Initial details should be empty (--)"
    print("TEST 1 PASS: Scanner initialized -> Student Details section initially empty (--).")

    # TEST 2: Verify Student 1 (Rohan Verma) - School Mode
    scanner.combo_category.set("School")
    scanner._update_details("STU_FACE_1")

    assert "Rohan Verma" in scanner.lbl_det_1.cget("text"), f"Expected Rohan Verma, got {scanner.lbl_det_1.cget('text')}"
    assert "STU_FACE_1" in scanner.lbl_det_2.cget("text"), f"Expected STU_FACE_1, got {scanner.lbl_det_2.cget('text')}"
    assert "10" in scanner.lbl_det_3.cget("text"), f"Expected Class 10, got {scanner.lbl_det_3.cget('text')}"
    assert "A" in scanner.lbl_det_4.cget("text"), f"Expected Section A, got {scanner.lbl_det_4.cget('text')}"
    assert "Present" in scanner.lbl_det_5.cget("text"), f"Expected Status Present, got {scanner.lbl_det_5.cget('text')}"
    print("TEST 2 PASS: Verified Student 1 (Rohan Verma) -> Stored database details (Name, ID, Class, Section, Status) automatically displayed.")

    # TEST 3: Verify Student 2 (Ananya Roy) - College Mode
    scanner.combo_category.set("College")
    scanner._update_details("STU_FACE_2")

    assert "Ananya Roy" in scanner.lbl_det_1.cget("text"), f"Expected Ananya Roy, got {scanner.lbl_det_1.cget('text')}"
    assert "ENR_9900" in scanner.lbl_det_2.cget("text"), f"Expected Enrollment ENR_9900, got {scanner.lbl_det_2.cget('text')}"
    assert "Computer Science" in scanner.lbl_det_3.cget("text"), f"Expected Computer Science, got {scanner.lbl_det_3.cget('text')}"
    assert "3rd Semester" in scanner.lbl_det_4.cget("text"), f"Expected 3rd Semester, got {scanner.lbl_det_4.cget('text')}"
    assert "Present" in scanner.lbl_det_5.cget("text"), f"Expected Status Present, got {scanner.lbl_det_5.cget('text')}"
    print("TEST 3 PASS: Verified Student 2 (Ananya Roy) -> Stored database details (Name, ID/Enrollment, Course, Semester/Year, Status) automatically displayed.")

    # TEST 4: Unverified / Unknown Face -> Details cleared back to (--)
    scanner._update_details(None)
    assert "--" in scanner.lbl_det_1.cget("text"), "Unverified face should reset details to (--)"
    assert "--" in scanner.lbl_det_2.cget("text"), "Unverified face should reset details to (--)"
    print("TEST 4 PASS: Unverified / unknown face -> Student details cleared to (--), ensuring no wrong student details appear.")

    scanner.on_close()
    root.quit()
    root.destroy()

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

    print("\n=== ALL FACE VERIFICATION STUDENT DETAILS DISPLAY TESTS PASSED 100% ===")

if __name__ == "__main__":
    run_tests()
