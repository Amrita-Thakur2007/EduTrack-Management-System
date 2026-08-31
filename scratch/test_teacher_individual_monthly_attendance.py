import os
import sys
import tkinter as tk
from tkinter import messagebox
import sqlite3

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Mock messagebox
messagebox.showinfo = lambda title, message: print(f"[INFOBOX] {title}: {message}")
messagebox.showwarning = lambda title, message: print(f"[WARNBOX] {title}: {message}")
messagebox.showerror = lambda title, message: print(f"[ERRBOX] {title}: {message}")

from database.db_manager import DBManager
from gui.teacher_dashboard import TeacherDashboard
from gui.attendance_view import IndividualStudentAttendanceDialog

def test_teacher_portal_individual_monthly_attendance():
    db_path = os.path.join(PROJECT_ROOT, "scratch", "test_teacher_monthly_att.db")
    if os.path.exists(db_path):
        os.remove(db_path)

    db = DBManager(db_path=db_path)

    # Setup sample students: School & College
    # School Student 1: Amrita (Admission Date: 2026-08-28)
    db.add_student({
        "student_id": "STU_AMRITA",
        "name": "Amrita Thakur",
        "school_name": "Delhi Public School",
        "current_class": "10",
        "section": "A",
        "roll_number": "101",
        "admission_date": "2026-08-28",
        "dob": "2010-05-15",
        "gender": "Female",
        "education_type": "School",
        "phone": "9876543210",
        "email": "amrita@example.com"
    })

    # School Student 2: Rahul (Admission Date: 2026-04-01)
    db.add_student({
        "student_id": "STU_RAHUL",
        "name": "Rahul Kumar",
        "school_name": "Delhi Public School",
        "current_class": "10",
        "section": "A",
        "roll_number": "102",
        "admission_date": "2026-04-01",
        "dob": "2010-06-20",
        "gender": "Male",
        "education_type": "School",
        "phone": "9876543211",
        "email": "rahul@example.com"
    })

    # College Student 1: Ananya (Admission Date: 2026-08-01)
    db.add_student({
        "student_id": "STU_COL_ANANYA",
        "name": "Ananya Sharma",
        "college_name": "IIT Bombay",
        "enrollment_number": "ENR2026001",
        "course": "B.Tech Computer Science",
        "semester": "Semester 1",
        "academic_year": "1st Year",
        "admission_date": "2026-08-01",
        "dob": "2006-01-10",
        "gender": "Female",
        "education_type": "College",
        "phone": "9876543212",
        "email": "ananya@example.com"
    })

    # Add Attendance Records for Amrita
    # August 2026
    db.mark_attendance("STU_AMRITA", "2026-08-28", "09:00:00", "Present", source="Teacher")
    db.mark_attendance("STU_AMRITA", "2026-08-29", "09:00:00", "Absent", source="Teacher")
    db.mark_attendance("STU_AMRITA", "2026-08-30", "09:00:00", "Leave", source="Teacher")
    db.mark_attendance("STU_AMRITA", "2026-08-31", "09:00:00", "Present", source="Teacher")

    # September 2026
    db.mark_attendance("STU_AMRITA", "2026-09-01", "09:00:00", "Present", source="Teacher")
    db.mark_attendance("STU_AMRITA", "2026-09-02", "09:00:00", "Absent", source="Teacher")
    db.mark_attendance("STU_AMRITA", "2026-09-03", "09:00:00", "Leave", source="Teacher")
    db.mark_attendance("STU_AMRITA", "2026-09-04", "09:00:00", "Present", source="Teacher")
    db.mark_attendance("STU_AMRITA", "2026-09-30", "09:00:00", "Present", source="Teacher")

    # October 2026
    db.mark_attendance("STU_AMRITA", "2026-10-01", "09:00:00", "Present", source="Teacher")
    db.mark_attendance("STU_AMRITA", "2026-10-15", "09:00:00", "Leave", source="Teacher")
    db.mark_attendance("STU_AMRITA", "2026-10-31", "09:00:00", "Present", source="Teacher")

    # Add Attendance Records for College Student Ananya
    db.mark_attendance("STU_COL_ANANYA", "2026-09-01", "09:00:00", "Present", source="Teacher")
    db.mark_attendance("STU_COL_ANANYA", "2026-09-05", "09:00:00", "Absent", source="Teacher")

    root = tk.Tk()
    root.withdraw()

    user_data = {'id': 1, 'username': 'teacher1', 'role': 'Teacher'}
    dashboard = TeacherDashboard(root, db, user_data)
    dashboard.show_students()

    print("--- TEST 1: SCHOOL STUDENT (AMRITA) MONTHLY ATTENDANCE ---")
    # Search and select Amrita
    dashboard.combo_category.set("School")
    dashboard.entry_search.delete(0, tk.END)
    dashboard.entry_search.insert(0, "Amrita")
    dashboard.load_students_table()

    stu_items = dashboard.tree.get_children()
    assert len(stu_items) > 0, "Amrita row not found in Teacher Dashboard!"
    dashboard.tree.selection_set(stu_items[0])

    # Open Individual Monthly Attendance Dialog
    dialog = IndividualStudentAttendanceDialog(dashboard, db, "STU_AMRITA")

    # Select Month: September, Year: 2026
    dialog.entry_month.set("September")
    dialog.entry_year.delete(0, tk.END)
    dialog.entry_year.insert(0, "2026")
    dialog.load_attendance()

    items_sep = dialog.tree.get_children()
    print(f"Total September rows displayed: {len(items_sep)}")
    assert len(items_sep) == 30, f"Expected 30 dates for September 2026, got {len(items_sep)}"

    # Verify chronological order 1 -> 2 -> ... -> 30
    for idx, item in enumerate(items_sep, start=1):
        vals = dialog.tree.item(item)['values']
        date_str = vals[0]
        status = vals[1]
        assert str(idx) in date_str and "September" in date_str, f"Row {idx} date mismatch: {date_str}"

    # Verify specific statuses
    vals_1 = dialog.tree.item(items_sep[0])['values'] # 1 September
    assert vals_1[1] == "Present", f"Expected Present on 1 Sep, got {vals_1[1]}"
    vals_2 = dialog.tree.item(items_sep[1])['values'] # 2 September
    assert vals_2[1] == "Absent", f"Expected Absent on 2 Sep, got {vals_2[1]}"
    vals_3 = dialog.tree.item(items_sep[2])['values'] # 3 September
    assert vals_3[1] == "Leave", f"Expected Leave on 3 Sep, got {vals_3[1]}"
    vals_4 = dialog.tree.item(items_sep[3])['values'] # 4 September
    assert vals_4[1] == "Present", f"Expected Present on 4 Sep, got {vals_4[1]}"
    vals_30 = dialog.tree.item(items_sep[29])['values'] # 30 September
    assert vals_30[1] == "Present", f"Expected Present on 30 Sep, got {vals_30[1]}"

    # Unmarked days (e.g. 5 Sep)
    vals_5 = dialog.tree.item(items_sep[4])['values']
    assert vals_5[1] == "-", f"Expected '-' for unmarked day, got {vals_5[1]}"

    print("Test 1 Passed: School Student September date-wise attendance verified (1..30 in chronological order).")

    print("--- TEST 2: MONTH CHANGE (OCTOBER 2026) ---")
    dialog.entry_month.set("October")
    dialog.entry_year.delete(0, tk.END)
    dialog.entry_year.insert(0, "2026")
    dialog.load_attendance()

    items_oct = dialog.tree.get_children()
    print(f"Total October rows displayed: {len(items_oct)}")
    assert len(items_oct) == 31, f"Expected 31 dates for October 2026, got {len(items_oct)}"

    # Check 1 Oct, 15 Oct, 31 Oct
    vals_oct_1 = dialog.tree.item(items_oct[0])['values']
    assert vals_oct_1[1] == "Present", f"Expected Present on 1 Oct, got {vals_oct_1[1]}"
    vals_oct_15 = dialog.tree.item(items_oct[14])['values']
    assert vals_oct_15[1] == "Leave", f"Expected Leave on 15 Oct, got {vals_oct_15[1]}"
    vals_oct_31 = dialog.tree.item(items_oct[30])['values']
    assert vals_oct_31[1] == "Present", f"Expected Present on 31 Oct, got {vals_oct_31[1]}"

    print("Test 2 Passed: Month change to October (31 dates) verified.")

    print("--- TEST 3: ADMISSION DATE RULE (AUGUST 2026) ---")
    # Amrita was admitted on 28 August 2026.
    # August should start from 28 August up to 31 August (4 days: 28, 29, 30, 31).
    dialog.entry_month.set("August")
    dialog.entry_year.delete(0, tk.END)
    dialog.entry_year.insert(0, "2026")
    dialog.load_attendance()

    items_aug = dialog.tree.get_children()
    print(f"Total August rows displayed: {len(items_aug)}")
    assert len(items_aug) == 4, f"Expected 4 dates (28..31 August) for Amrita, got {len(items_aug)}"
    assert "28 August" in dialog.tree.item(items_aug[0])['values'][0]
    assert "31 August" in dialog.tree.item(items_aug[3])['values'][0]

    # Pre-admission month (July 2026)
    dialog.entry_month.set("July")
    dialog.entry_year.delete(0, tk.END)
    dialog.entry_year.insert(0, "2026")
    dialog.load_attendance()
    items_jul = dialog.tree.get_children()
    assert len(items_jul) == 1, "Expected 1 informational row for month prior to admission"
    assert "Before Admission Date" in dialog.tree.item(items_jul[0])['values'][0]

    print("Test 3 Passed: Admission date boundary rule strictly verified.")

    print("--- TEST 4: COLLEGE STUDENT MONTHLY ATTENDANCE ---")
    # College student Ananya
    col_dialog = IndividualStudentAttendanceDialog(dashboard, db, "STU_COL_ANANYA")
    col_dialog.entry_month.set("September")
    col_dialog.entry_year.delete(0, tk.END)
    col_dialog.entry_year.insert(0, "2026")
    col_dialog.load_attendance()

    items_col_sep = col_dialog.tree.get_children()
    assert len(items_col_sep) == 30, f"Expected 30 dates for College student September, got {len(items_col_sep)}"
    val_col_1 = col_dialog.tree.item(items_col_sep[0])['values']
    assert val_col_1[1] == "Present", f"Expected Present on 1 Sep for College student, got {val_col_1[1]}"
    assert val_col_1[2] == "Marked By: Teacher", f"Expected Marked By: Teacher, got {val_col_1[2]}"
    assert val_col_1[3] == "ENR2026001", f"Expected Enrollment No in table, got {val_col_1[3]}"

    print("Test 4 Passed: College student monthly attendance verified.")

    print("--- TEST 5: DIFFERENT STUDENT ISOLATION ---")
    # Rahul has NO records in September
    rahul_dialog = IndividualStudentAttendanceDialog(dashboard, db, "STU_RAHUL")
    rahul_dialog.entry_month.set("September")
    rahul_dialog.entry_year.delete(0, tk.END)
    rahul_dialog.entry_year.insert(0, "2026")
    rahul_dialog.load_attendance()

    items_rahul = rahul_dialog.tree.get_children()
    assert len(items_rahul) == 30
    for itm in items_rahul:
        v = rahul_dialog.tree.item(itm)['values']
        assert v[1] == "-", f"Rahul should have no attendance marks in Sep, got {v[1]}"
        assert v[2] == "-", f"Expected '-' for unmarked marked_by, got {v[2]}"
        assert v[3] == "STU_RAHUL", f"Expected STU_RAHUL, got {v[3]}"
        assert v[4] == "Rahul Kumar", f"Expected Rahul Kumar, got {v[4]}"

    print("Test 5 Passed: Student data isolation verified.")

    # Cleanup
    dialog.destroy()
    col_dialog.destroy()
    rahul_dialog.destroy()
    root.destroy()

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

    print("\nALL 5 TEST CASES PASSED PERFECTLY!")

if __name__ == '__main__':
    test_teacher_portal_individual_monthly_attendance()
