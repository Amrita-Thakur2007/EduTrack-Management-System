import time
from datetime import datetime
from database.db_manager import DBManager
from utils.helpers import get_current_date

def test_work_time_workflow():
    db = DBManager()
    today = get_current_date()
    teacher_id = "Sakshi2007"
    
    # 1. Clean test record for today
    with db.get_connection() as conn:
        conn.execute("DELETE FROM teacher_work_logs WHERE teacher_id = ? AND date = ?", (teacher_id, today))
        conn.execute("DELETE FROM teacher_attendance WHERE teacher_id = ? AND date = ?", (teacher_id, today))
        conn.commit()

    # Step 1: Open page -> verify no record yet (BEFORE START)
    log1 = db.get_teacher_work_log(teacher_id, today)
    print("1. BEFORE START check:", log1)
    assert log1 is None, "Expected no log before start"

    # Step 2: Click START
    start_time_str = "07:42:18 AM"
    db.mark_teacher_attendance(teacher_id, today, start_time_str, "Present")
    log2 = db.record_teacher_login(teacher_id, start_time_override=start_time_str)
    print("2. AFTER START check:", log2)
    assert log2['actual_start_time'] == start_time_str, "Start time mismatch"
    assert log2.get('actual_end_time') is None, "End time should be None after START"

    # Step 3: Click END
    end_time_str = "12:30:10 PM"
    ok = db.record_teacher_logout(teacher_id, end_time_override=end_time_str)
    assert ok, "Logout record failed"
    log3 = db.get_teacher_work_log(teacher_id, today)
    print("3. AFTER END check:", log3)
    assert log3['actual_start_time'] == start_time_str, "Start time changed after END"
    assert log3['actual_end_time'] == end_time_str, "End time mismatch"
    assert log3['total_work_time'] == "04:47:52", f"Total work time expected '04:47:52', got '{log3['total_work_time']}'"

    print("ALL VERIFICATIONS PASSED SUCCESSFULLY! ✓")

if __name__ == "__main__":
    test_work_time_workflow()
