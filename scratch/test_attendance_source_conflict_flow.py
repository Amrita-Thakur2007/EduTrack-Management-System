import os
import sys
import time
import tkinter as tk
from unittest.mock import patch

sys.path.insert(0, ".")
from database.db_manager import DBManager
from gui.teacher_dashboard import TeacherDashboard

def run_tests():
    print("=== STARTING ATTENDANCE SOURCE CONFLICT FLOW TEST ===")
    test_db_path = f"scratch/test_att_conflict_{int(time.time())}.db"
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except Exception:
            pass

    db = DBManager(db_path=test_db_path)

    # 1. Create a student
    u_stu = db.create_user("student_test", "Pass123", "Student")
    db.add_student({
        "student_id": "STU_999",
        "name": "Aryan Kumar",
        "email": "aryan@school.edu",
        "education_type": "School",
        "school_name": "Delhi Public School",
        "current_class": "10",
        "section": "A"
    }, u_stu)

    # 2. Student marks attendance for today
    today = "2026-08-30"
    now_time = "09:00:00 AM"

    ok_stu, msg_stu = db.mark_attendance("STU_999", today, now_time, "Present", source="Student")
    assert ok_stu is True, f"Student attendance should succeed: {msg_stu}"
    print("[PASS] Step 1: Student successfully marked attendance.")

    # 3. Teacher attempts to mark attendance for that student
    ok_teach, msg_teach = db.mark_attendance("STU_999", today, "10:00:00 AM", "Present", source="Teacher")
    assert ok_teach is False, "Teacher attendance should fail when student has already marked."
    assert msg_teach == "Attendance is already marked by student.", f"Expected 'Attendance is already marked by student.', got '{msg_teach}'"
    print(f"[PASS] Step 2: Database returned exact message: '{msg_teach}'")

    # 4. Test Teacher Dashboard GUI interaction
    root = tk.Tk()
    root.withdraw()

    teacher_user = {"id": 2, "username": "teacher1", "role": "Teacher"}
    t_dash = TeacherDashboard(root, db, teacher_user)
    t_dash.load_students_table()

    # Find the treeview item for STU_999
    found_item = None
    for item in t_dash.tree.get_children():
        vals = t_dash.tree.item(item)["values"]
        if vals and str(vals[0]) == "STU_999":
            found_item = item
            break

    assert found_item is not None, "STU_999 must exist in teacher dashboard table"
    t_dash.tree.selection_set(found_item)

    # Trigger Save Attendance / Mark Present in teacher dashboard
    with patch("tkinter.messagebox.showwarning") as mock_warn:
        t_dash.save_selected_attendance(status_override="Present")
        assert mock_warn.called, "Teacher dashboard must show a warning popup!"
        args, kwargs = mock_warn.call_args
        assert args[0] == "Notice"
        assert args[1] == "Attendance is already marked by student.", f"Expected notice 'Attendance is already marked by student.', got '{args[1]}'"
        print(f"[PASS] Step 3: Teacher Dashboard GUI displayed warning popup: '{args[1]}'")

    # 5. Reverse Case: Teacher marks attendance first for another student
    u_stu2 = db.create_user("student_test2", "Pass123", "Student")
    db.add_student({
        "student_id": "STU_888",
        "name": "Pooja Sharma",
        "email": "pooja@school.edu",
        "education_type": "School",
        "school_name": "Delhi Public School",
        "current_class": "10",
        "section": "A"
    }, u_stu2)

    ok_t2, msg_t2 = db.mark_attendance("STU_888", today, now_time, "Present", source="Teacher")
    assert ok_t2 is True

    ok_s2, msg_s2 = db.mark_attendance("STU_888", today, now_time, "Present", source="Student")
    assert ok_s2 is False
    assert msg_s2 == "Attendance is already marked by teacher."
    print(f"[PASS] Step 4: Reverse check: student cannot overwrite teacher attendance: '{msg_s2}'")

    try:
        t_dash.destroy()
        root.destroy()
    except Exception:
        pass

    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except Exception:
            pass

    print("=== ALL ATTENDANCE CONFLICT TESTS PASSED (100%) ===")

if __name__ == "__main__":
    run_tests()
