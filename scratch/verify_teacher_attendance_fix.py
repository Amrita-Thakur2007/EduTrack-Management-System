import os
import sys
import sqlite3
import datetime

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from database.db_manager import DBManager

def test_school_college_and_attendance_workflow():
    db_path = os.path.join(PROJECT_ROOT, "data", "database.db")
    print(f"Testing DB at: {db_path}")
    db = DBManager(db_path=db_path)

    # 1. Fetch all school students
    school_students = db.get_all_students(filter_edu_type="School")
    amrita = None
    for s in school_students:
        if s['name'].strip().lower() == 'amrita':
            amrita = s
            break
    
    assert amrita is not None, "Amrita not found in database!"
    print(f"Found Amrita: ID={amrita['student_id']}, Name={amrita['name']}, School Name='{amrita['school_name']}'")
    assert amrita['school_name'] != "", "Amrita's School Name MUST NOT be blank!"
    print("Step 1 Passed: Amrita's School Name is displayed correctly (not blank).")

    # 2. Mark Amrita as Present
    today = datetime.date.today().strftime('%Y-%m-%d')
    now_t = datetime.datetime.now().strftime('%H:%M:%S')

    ok_pres, msg_pres = db.mark_attendance(amrita['student_id'], today, now_t, "Present")
    assert ok_pres, f"Failed to mark Amrita as Present: {msg_pres}"
    
    att_rec = db.get_student_attendance_for_date(amrita['student_id'], today)
    assert att_rec is not None and att_rec['status'] == "Present", f"Expected status Present, got {att_rec}"
    print("Step 2 Passed: Marked Amrita as Present & verified DB record.")

    # 3. Change Amrita's attendance to Absent & Save again (Verify UPSERT, no duplicate)
    ok_abs, msg_abs = db.mark_attendance(amrita['student_id'], today, now_t, "Absent")
    assert ok_abs, f"Failed to update Amrita to Absent: {msg_abs}"

    att_rec_abs = db.get_student_attendance_for_date(amrita['student_id'], today)
    assert att_rec_abs is not None and att_rec_abs['status'] == "Absent", f"Expected status Absent, got {att_rec_abs}"

    # Check total count of attendance rows for Amrita on today
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM attendance WHERE student_id = ? AND date = ?", (amrita['student_id'], today))
        cnt = cursor.fetchone()['cnt']
        assert cnt == 1, f"Expected exactly 1 attendance record for Amrita on {today}, but found {cnt}!"
    print("Step 3 Passed: Updated Amrita's attendance to Absent (UPSERT verified, 0 duplicates).")

    # 4. Fetch College student (e.g. Grisha)
    college_students = db.get_all_students(filter_edu_type="College")
    assert len(college_students) > 0, "No College students found in database!"
    college_student = college_students[0]
    cid = college_student['student_id']
    cname = college_student['name']
    col_school_name = college_student['college_name']
    
    print(f"Found College Student: ID={cid}, Name={cname}, College Name='{col_school_name}'")
    assert col_school_name != "", f"College student {cname}'s College Name MUST NOT be blank!"

    # Mark College student Present then Absent
    ok_c1, _ = db.mark_attendance(cid, today, now_t, "Present")
    assert ok_c1
    att_c1 = db.get_student_attendance_for_date(cid, today)
    assert att_c1['status'] == "Present"

    ok_c2, _ = db.mark_attendance(cid, today, now_t, "Absent")
    assert ok_c2
    att_c2 = db.get_student_attendance_for_date(cid, today)
    assert att_c2['status'] == "Absent"

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM attendance WHERE student_id = ? AND date = ?", (cid, today))
        cnt_c = cursor.fetchone()['cnt']
        assert cnt_c == 1, f"Expected 1 record for College student on {today}, found {cnt_c}"

    print("Step 4 Passed: College student attendance workflow verified (UPSERT, correct college name, 0 duplicates).")
    print("\nALL DATABASE AND BACKEND WORKFLOW TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_school_college_and_attendance_workflow()
