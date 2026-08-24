import os
import sys
import pickle
import numpy as np
from datetime import datetime

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.db_manager import DBManager
from utils.helpers import get_current_date, get_current_time

def test_face_attendance_and_time_tracking():
    print("=== STARTING FACE ATTENDANCE & TIME TRACKING TEST ===")
    
    # Use test database in scratch
    test_db_path = os.path.join(PROJECT_ROOT, "scratch", "test_attendance.db")
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    db = DBManager(test_db_path)

    # 1. Setup Test Data (Teacher and Student)
    with db.get_connection() as conn:
        cursor = conn.cursor()
        # Insert User & Teacher
        cursor.execute("INSERT INTO users (username, password_hash, salt, role) VALUES ('teacher1', 'hash', 'salt', 'Teacher')")
        t_user_id = cursor.lastrowid
        cursor.execute("INSERT INTO teachers (teacher_id, user_id, name, department) VALUES ('T101', ?, 'Prof. John Doe', 'Computer Science')", (t_user_id,))
        
        # Insert User & Student
        cursor.execute("INSERT INTO users (username, password_hash, salt, role) VALUES ('student1', 'hash', 'salt', 'Student')")
        s_user_id = cursor.lastrowid
        cursor.execute("INSERT INTO students (student_id, user_id, name, course) VALUES ('S101', ?, 'Alice Smith', 'B.Tech CS')", (s_user_id,))
        
        # Register fake face encodings for testing
        fake_face_t = np.ones((100, 100), dtype=np.uint8) * 128
        fake_face_s = np.ones((100, 100), dtype=np.uint8) * 200
        
        blob_t = pickle.dumps(fake_face_t)
        blob_s = pickle.dumps(fake_face_s)

        cursor.execute("CREATE TABLE IF NOT EXISTS face_encodings (student_id TEXT PRIMARY KEY, encoding_blob BLOB, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        cursor.execute("INSERT INTO face_encodings (student_id, encoding_blob) VALUES ('T101', ?)", (blob_t,))
        cursor.execute("INSERT INTO face_encodings (student_id, encoding_blob) VALUES ('S101', ?)", (blob_s,))
        conn.commit()

    print("[SUCCESS] Test teachers, students, and face encodings initialized.")

    # 2. TEST TEACHER FACE ATTENDANCE & TIME TRACKING
    print("\n--- Testing Teacher Flow ---")
    today = get_current_date()
    start_time = "07:30:00"
    
    # Simulate face recognition match -> Mark attendance & Record Start Time
    ok, msg = db.mark_teacher_attendance("T101", today, start_time, "Present")
    assert ok, f"Failed to mark teacher attendance: {msg}"
    print(f"[OK] Teacher Attendance Marked: {msg}")

    wlog = db.record_teacher_login("T101", start_time_override=start_time)
    assert wlog is not None, "Teacher work log missing"
    assert wlog['actual_start_time'] == start_time, f"Expected start time {start_time}, got {wlog['actual_start_time']}"
    print(f"[OK] Teacher Start Time Recorded Automatically: {wlog['actual_start_time']}")

    # Verify session active (no check-out time yet)
    active_log = db.get_teacher_work_log("T101", today)
    assert active_log['actual_end_time'] is None, "End time should be None while working"
    print("[OK] Teacher Working Time Tracking Active (Timer Running).")

    # Simulate Teacher Exit / Logout at 12:30 PM (5 hours later)
    end_time = "12:30:00"
    ok_out = db.record_teacher_logout("T101", end_time_override=end_time)
    assert ok_out, "Teacher logout recording failed"

    final_log = db.get_teacher_work_log("T101", today)
    assert final_log['actual_end_time'] == end_time, f"Expected end time {end_time}, got {final_log['actual_end_time']}"
    assert final_log['total_work_time'] == "05:00:00", f"Expected '05:00:00', got {final_log['total_work_time']}"
    print(f"[OK] Teacher Logout / Exit Completed:")
    print(f"  - Start Time: {final_log['actual_start_time']}")
    print(f"  - End Time:   {final_log['actual_end_time']}")
    print(f"  - Working Hours: {final_log['working_hours']} hrs ({final_log['total_work_time']})")

    # 3. TEST STUDENT FACE ATTENDANCE (NO TIME TRACKING)
    print("\n--- Testing Student Flow ---")
    s_time = "08:15:00"
    
    # Simulate Student Face Recognition Match
    ok_s, msg_s = db.mark_attendance("S101", today, s_time, "Present")
    assert ok_s, f"Failed to mark student attendance: {msg_s}"
    print(f"[OK] Student Attendance Marked: {msg_s}")

    # Verify NO work log or time tracking exists for Student
    s_log = db.get_teacher_work_log("S101", today)
    assert s_log is None, "ERROR: Work log created for Student! Students MUST NOT have time tracking."
    print("[OK] Confirmed: NO Start Time, End Time, or Timer created for Student (DONE).")

    # 4. CLEANUP
    del db
    import gc
    gc.collect()
    try:
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
    except Exception:
        pass
        
    print("\n=== ALL TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    test_face_attendance_and_time_tracking()
