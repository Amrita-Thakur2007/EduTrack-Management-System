import os
import time
import pickle
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DBManager

# Mock messagebox popups
messagebox.showinfo = lambda title, msg: None
messagebox.showwarning = lambda title, msg: None
messagebox.showerror = lambda title, msg: None

from face_attendance.face_recognition import FaceAttendanceScannerWindow
from gui.attendance_view import AttendanceViewFrame

def run_tests():
    print("=== STARTING FACE VERIFICATION SCHOOL / COLLEGE MODE & REMOVE TIME TEST ===")

    db_path = f"scratch/test_face_mode_{int(time.time())}.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = DBManager(db_path=db_path)

    # 1. Register School Student (Rahul)
    u1 = db.create_user("RahulUser", "Pass1234", "Student")
    db.add_student({
        "student_id": "ST101",
        "name": "Rahul",
        "email": "rahul@school.edu",
        "education_type": "School",
        "school_name": "Delhi Public School",
        "current_class": "10",
        "section": "A"
    }, u1)

    # 2. Register College Student (Priya)
    u2 = db.create_user("PriyaUser", "Pass1234", "Student")
    db.add_student({
        "student_id": "ST202",
        "name": "Priya",
        "email": "priya@college.edu",
        "education_type": "College",
        "college_name": "Delhi University",
        "course": "B.Com",
        "enrollment_number": "EN202",
        "semester": "4th Semester",
        "academic_year": "2nd Year"
    }, u2)

    root = tk.Tk()
    root.withdraw()

    # 3. Test FaceAttendanceScannerWindow
    scanner = FaceAttendanceScannerWindow(root, db, target_role="Student")

    # Mode 1: SCHOOL
    scanner.combo_category.set("School")
    scanner._update_details("ST101")

    lbl_1_text = scanner.lbl_det_1.cget("text")
    lbl_2_text = scanner.lbl_det_2.cget("text")
    lbl_3_text = scanner.lbl_det_3.cget("text")
    lbl_4_text = scanner.lbl_det_4.cget("text")
    lbl_5_text = scanner.lbl_det_5.cget("text")

    assert "Rahul" in lbl_1_text, f"Expected Rahul in lbl_1, got {lbl_1_text}"
    assert "ST101" in lbl_2_text, f"Expected ST101 in lbl_2, got {lbl_2_text}"
    assert "10" in lbl_3_text, f"Expected Class 10 in lbl_3, got {lbl_3_text}"
    assert "A" in lbl_4_text, f"Expected Section A in lbl_4, got {lbl_4_text}"
    assert "Present" in lbl_5_text, f"Expected Present in lbl_5, got {lbl_5_text}"

    # Ensure Time is NOT in any display label
    all_text = f"{lbl_1_text} {lbl_2_text} {lbl_3_text} {lbl_4_text} {lbl_5_text}"
    assert "Time" not in all_text, "Time must NOT appear in Face Verification section!"
    assert "Course" not in all_text, "Course must NOT appear in School mode!"
    print("TEST 1 PASS: School mode verified -> Student Name (Rahul), ID (ST101), Class (10), Section (A), Status (Present). Time & Course NOT displayed.")

    # Mode 2: COLLEGE
    scanner.combo_category.set("College")
    scanner._update_details("ST202")

    lbl_1_text = scanner.lbl_det_1.cget("text")
    lbl_2_text = scanner.lbl_det_2.cget("text")
    lbl_3_text = scanner.lbl_det_3.cget("text")
    lbl_4_text = scanner.lbl_det_4.cget("text")
    lbl_5_text = scanner.lbl_det_5.cget("text")

    assert "Priya" in lbl_1_text, f"Expected Priya in lbl_1, got {lbl_1_text}"
    assert "EN202" in lbl_2_text, f"Expected EN202 in lbl_2, got {lbl_2_text}"
    assert "B.Com" in lbl_3_text, f"Expected B.Com in lbl_3, got {lbl_3_text}"
    assert "Present" in lbl_5_text, f"Expected Present in lbl_5, got {lbl_5_text}"

    all_text_col = f"{lbl_1_text} {lbl_2_text} {lbl_3_text} {lbl_4_text} {lbl_5_text}"
    assert "Time" not in all_text_col, "Time must NOT appear in Face Verification section!"
    assert "Section" not in all_text_col, "Section must NOT appear in College mode!"
    print("TEST 2 PASS: College mode verified -> Student Name (Priya), Enrollment No (EN202), Course (B.Com), Status (Present). Time & Section NOT displayed.")

    scanner.on_close()

    # 4. Test AttendanceViewFrame (Removing Time column)
    view_frame = AttendanceViewFrame(root, db, is_admin_or_teacher=True)
    
    # Check tree_stu columns
    cols = view_frame.tree_stu.cget("columns")
    assert "time" not in cols, f"Time column must NOT exist in AttendanceViewFrame, got {cols}"
    print("TEST 3 PASS: AttendanceViewFrame verified -> Time column successfully removed from table.")

    root.quit()
    root.destroy()

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

    print("\n=== ALL FACE VERIFICATION SCHOOL / COLLEGE MODE & REMOVE TIME TESTS PASSED 100% ===")

if __name__ == "__main__":
    run_tests()
