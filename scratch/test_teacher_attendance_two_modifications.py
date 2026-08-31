import os
import sys
import tkinter as tk
import time
import pickle
import numpy as np
from tkinter import messagebox

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

messages_info = []
messages_warning = []
messages_error = []

messagebox.showinfo = lambda title, msg: messages_info.append((title, str(msg)))
messagebox.showwarning = lambda title, msg: messages_warning.append((title, str(msg)))
messagebox.showerror = lambda title, msg: messages_error.append((title, str(msg)))

from database.db_manager import DBManager
from gui.attendance_view import IndividualStudentAttendanceDialog
from gui.teacher_dashboard import TeacherDashboard
from face_attendance.face_recognition import FaceAttendanceScannerWindow
from utils.helpers import get_current_date, get_current_time

def test_two_modifications():
    print("=== STARTING TEST SUITE FOR TWO TEACHER PORTAL ATTENDANCE MODIFICATIONS ===")
    
    db_file = os.path.join(PROJECT_ROOT, "scratch", f"test_two_mods_{int(time.time())}.db")
    if os.path.exists(db_file):
        os.remove(db_file)
    db = DBManager(db_file)
    
    root = tk.Tk()
    root.withdraw()
    
    FaceAttendanceScannerWindow._start_camera = lambda self: None
    
    # 1. Setup Student Amrita (School) and Anandi (School) and College Student Rahul
    u_amrita = db.create_user("amrita", "Pass1234", "Student")
    db.add_student({
        "student_id": "STU_AMRITA",
        "name": "Amrita",
        "education_type": "School",
        "school_name": "SKV Delhi",
        "current_class": "10",
        "section": "A",
        "admission_date": "2026-08-28"
    }, u_amrita)
    
    u_anandi = db.create_user("anandi", "Pass1234", "Student")
    db.add_student({
        "student_id": "STU_ANANDI",
        "name": "Anandi",
        "education_type": "School",
        "school_name": "SKV Delhi",
        "current_class": "10",
        "section": "B",
        "admission_date": "2026-08-28"
    }, u_anandi)
    
    u_rahul = db.create_user("rahul", "Pass1234", "Student")
    db.add_student({
        "student_id": "STU_RAHUL",
        "name": "Rahul",
        "education_type": "College",
        "college_name": "IIT Bombay",
        "enrollment_number": "ENR_RAHUL_99",
        "course": "B.Tech",
        "semester": "Semester 3",
        "admission_date": "2026-08-01"
    }, u_rahul)
    
    # Face matrices
    np.random.seed(444)
    face_amrita = (np.random.rand(100, 100) * 255).astype(np.uint8)
    np.random.seed(555)
    face_anandi = (np.random.rand(100, 100) * 255).astype(np.uint8)
    
    db.save_face_encoding("STU_AMRITA", pickle.dumps(face_amrita))
    db.save_face_encoding("STU_ANANDI", pickle.dumps(face_anandi))
    
    today = get_current_date()
    now_time = get_current_time()
    
    # ----------------------------------------------------
    # PART 1: TEST MODIFICATION 1 — VIEW INDIVIDUAL MONTHLY ATTENDANCE
    # ----------------------------------------------------
    print("\n--- PART 1: VIEW INDIVIDUAL MONTHLY ATTENDANCE TESTS ---")
    
    # Setup test attendance data for August 2026 for Amrita:
    # 28 Aug: Present (Student)
    # 29 Aug: No record (Should show Absent in past)
    # 30 Aug: Present (Teacher)
    # 31 Aug: (Future or marked)
    db.mark_attendance("STU_AMRITA", "2026-08-28", "08:30:00 AM", "Present", source="Student")
    # 2026-08-29 has NO RECORD
    db.mark_attendance("STU_AMRITA", "2026-08-30", "09:15:00 AM", "Present", source="Teacher")
    
    dlg = IndividualStudentAttendanceDialog(root, db, "STU_AMRITA")
    dlg.entry_month.set("August")
    dlg.entry_year.delete(0, tk.END)
    dlg.entry_year.insert(0, "2026")
    dlg.load_attendance()
    
    # Check rows in tree
    rows = [dlg.tree.item(item)['values'] for item in dlg.tree.get_children()]
    # rows format: (display_date, status, marked_by, sid_display, sname, info_str)
    
    print(f"Loaded {len(rows)} days for August (Starting from Admission Date: 28 August).")
    assert len(rows) == 4, f"August has 31 days, starting from 28th should be 4 days (28, 29, 30, 31), got {len(rows)}"
    
    # Check 28 Aug -> Present, Marked By: Student
    r28 = rows[0]
    assert "28 August" in str(r28[0])
    assert r28[1] == "Present", f"Expected Present for 28 Aug, got {r28[1]}"
    assert "Student" in str(r28[2]), f"Expected Marked By: Student for 28 Aug, got {r28[2]}"
    print("[PASS] 28 Aug Verified: Present | Marked By: Student")
    
    # Check 29 Aug -> Absent (past date with no record)
    r29 = rows[1]
    assert "29 August" in str(r29[0])
    assert r29[1] == "Absent", f"Expected Absent for 29 Aug (no record), got {r29[1]}"
    print("[PASS] 29 Aug Verified: Absent (No Record on Past Date)")
    
    # Check 30 Aug -> Present, Marked By: Teacher
    r30 = rows[2]
    assert "30 August" in str(r30[0])
    assert r30[1] == "Present", f"Expected Present for 30 Aug, got {r30[1]}"
    assert "Teacher" in str(r30[2]), f"Expected Marked By: Teacher for 30 Aug, got {r30[2]}"
    print("[PASS] 30 Aug Verified: Present | Marked By: Teacher")
    
    # Test Leave case on 29 Aug
    db.mark_attendance("STU_AMRITA", "2026-08-29", "09:00:00 AM", "Leave", source="Teacher")
    dlg.load_attendance()
    rows_leave = [dlg.tree.item(item)['values'] for item in dlg.tree.get_children()]
    r29_leave = rows_leave[1]
    assert r29_leave[1] == "Leave", f"Expected Leave for 29 Aug, got {r29_leave[1]}"
    print("[PASS] 29 Aug Verified after Leave entry: Leave (NOT Absent)")
    
    # Check chronological order
    day_numbers = [int(str(r[0]).split()[0]) for r in rows_leave]
    assert day_numbers == [28, 29, 30, 31], f"Expected chronological order [28, 29, 30, 31], got {day_numbers}"
    print("[PASS] Chronological order verified: 28 -> 29 -> 30 -> 31")
    
    dlg.destroy()

    # ----------------------------------------------------
    # PART 2: TEST MODIFICATION 2 — TEACHER FACE ATTENDANCE
    # ----------------------------------------------------
    print("\n--- PART 2: TEACHER FACE ATTENDANCE TESTS ---")
    
    t_user = {'id': 1, 'username': 'teacher1', 'role': 'Teacher'}
    t_dash = TeacherDashboard(root, db, t_user)
    t_dash.show_students()
    
    # 1. Successful Teacher Face Attendance:
    # Student = STU_ANANDI. Today has no attendance yet. Camera shows Anandi's face.
    messages_error.clear()
    messages_warning.clear()
    messages_info.clear()
    
    scanner_anandi = FaceAttendanceScannerWindow(
        t_dash,
        db,
        target_role="Student",
        student_id="STU_ANANDI",
        source="Teacher"
    )
    scanner_anandi.captured_frame_gray = face_anandi
    scanner_anandi.attempt_capture()
    scanner_anandi.destroy()
    
    assert len(messages_info) > 0, f"Expected success dialog for Anandi, got: info={messages_info}, err={messages_error}, warn={messages_warning}"
    
    # Check DB record for Anandi today
    anandi_att = db.get_student_attendance_for_date("STU_ANANDI", today)
    assert anandi_att is not None, "Anandi attendance must be recorded in DB"
    assert anandi_att['status'] == 'Present', f"Expected Present, got {anandi_att['status']}"
    assert anandi_att.get('source') == 'Teacher', f"Expected source='Teacher', got {anandi_att.get('source')}"
    print(f"[PASS] Teacher Face Attendance Success Verified: STU_ANANDI marked Present with source='{anandi_att.get('source')}'")
    
    # 2. Duplicate Attendance Protection:
    # Teacher tries to mark face attendance again for STU_ANANDI today
    messages_error.clear()
    messages_warning.clear()
    messages_info.clear()
    
    scanner_dup = FaceAttendanceScannerWindow(
        t_dash,
        db,
        target_role="Student",
        student_id="STU_ANANDI",
        source="Teacher"
    )
    scanner_dup.captured_frame_gray = face_anandi
    scanner_dup.attempt_capture()
    scanner_dup.destroy()
    
    assert len(messages_warning) > 0, "Expected warning for duplicate attendance!"
    assert "already marked" in messages_warning[0][1].lower(), f"Expected already marked warning, got {messages_warning[0][1]}"
    print(f"[PASS] Duplicate Attendance Protection Verified: Warning shown: '{messages_warning[0][1]}'")
    
    # 3. Wrong Person Protection:
    # Teacher selects STU_AMRITA (or STU_ANANDI) -> Anandi's face presented for Amrita
    messages_error.clear()
    messages_warning.clear()
    messages_info.clear()
    
    scanner_wrong = FaceAttendanceScannerWindow(
        t_dash,
        db,
        target_role="Student",
        student_id="STU_AMRITA",
        source="Teacher"
    )
    scanner_wrong.captured_frame_gray = face_anandi # Anandi face presented for Amrita
    scanner_wrong.attempt_capture()
    scanner_wrong.destroy()
    
    assert len(messages_error) > 0, "Expected error when wrong face is presented for Amrita"
    assert "You are not Amrita" in messages_error[0][1] or "does not match" in messages_error[0][1]
    print(f"[PASS] Wrong Person Protection Verified: Rejected with message: '{messages_error[0][1]}'")
    
    # Verify registered face in DB was NOT modified during attendance
    stored_amrita_face = pickle.loads(db.get_face_encoding("STU_AMRITA"))
    assert np.array_equal(stored_amrita_face, face_amrita), "Amrita's registered face must remain unchanged!"
    print("[PASS] Registered Face Preserved: Face was not overwritten or replaced during attendance.")

    try:
        root.destroy()
    except Exception:
        pass

    try:
        if os.path.exists(db_file):
            os.remove(db_file)
    except Exception:
        pass

    print("\n=========================================================================")
    print("ALL TESTS FOR MODIFICATION 1 & MODIFICATION 2 PASSED 100% SUCCESSFULLY!")
    print("=========================================================================")

if __name__ == '__main__':
    test_two_modifications()
