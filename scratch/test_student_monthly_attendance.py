import os
import sys
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Mock messagebox
messagebox.showinfo = lambda title, message: print(f"[INFOBOX] {title}: {message}")
messagebox.showwarning = lambda title, message: print(f"[WARNBOX] {title}: {message}")
messagebox.showerror = lambda title, message: print(f"[ERRBOX] {title}: {message}")
messagebox.askyesno = lambda title, message: True

from database.db_manager import DBManager
from gui.student_dashboard import StudentDashboard
from gui.attendance_view import AttendanceViewFrame, IndividualStudentAttendanceDialog

def run_tests():
    db_path = os.path.join(PROJECT_ROOT, "scratch", "test_student_monthly_att.db")
    if os.path.exists(db_path):
        os.remove(db_path)

    db = DBManager(db_path=db_path)

    # 1. Setup Student 1 (School Mode): Amrita (Admission Date: 2026-08-28)
    uid_amrita = db.create_user("amrita", "pass123", "Student")
    user_amrita = {"id": uid_amrita, "username": "amrita", "role": "Student"}
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
    }, user_id=uid_amrita)

    # 2. Setup Student 2 (College Mode): Ananya (Admission Date: 2026-08-01)
    uid_ananya = db.create_user("ananya", "pass123", "Student")
    user_ananya = {"id": uid_ananya, "username": "ananya", "role": "Student"}
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
    }, user_id=uid_ananya)

    # Add Attendance Records for Amrita
    # August 2026 (Inserted out of order in database to test date sorting)
    db.mark_attendance("STU_AMRITA", "2026-08-31", "09:00:00", "Present", source="Teacher")
    db.mark_attendance("STU_AMRITA", "2026-08-30", "09:00:00", "Leave", source="Teacher")
    db.mark_attendance("STU_AMRITA", "2026-08-28", "09:00:00", "Present", source="Teacher")
    # Note: 2026-08-29 has NO record -> should be Absent on past date check

    # September 2026
    db.mark_attendance("STU_AMRITA", "2026-09-03", "09:00:00", "Leave", source="Teacher")
    db.mark_attendance("STU_AMRITA", "2026-09-01", "09:00:00", "Present", source="Teacher")
    db.mark_attendance("STU_AMRITA", "2026-09-02", "09:00:00", "Absent", source="Teacher")

    # Add Attendance Records for College Student Ananya
    db.mark_attendance("STU_COL_ANANYA", "2026-08-30", "09:00:00", "Present", source="Teacher")
    db.mark_attendance("STU_COL_ANANYA", "2026-08-31", "09:00:00", "Present", source="Teacher")

    root = tk.Tk()
    root.withdraw()

    # Launch Student Portal for Amrita
    student_portal = StudentDashboard(root, db, user_amrita)
    student_portal.show_attendance()

    print("=== TEST 1: BUTTON IN STUDENT PORTAL -> ATTENDANCE HISTORY ===")
    # Verify that Attendance History UI has "View Individual Monthly Attendance" buttons
    content_widgets = student_portal.content_frame.winfo_children()
    found_button = False
    for w in content_widgets:
        for child in w.winfo_children():
            if isinstance(child, tk.ttk.Button) and "View Individual Monthly Attendance" in child.cget("text"):
                found_button = True
    assert found_button, "Button 'View Individual Monthly Attendance' not found in Student Attendance History!"
    print("PASS: Button 'View Individual Monthly Attendance' exists in Student Portal Attendance History.")

    print("=== TEST 2: EMBEDDED ATTENDANCE VIEW DATE ORDER ===")
    # Find AttendanceViewFrame in student_portal
    att_view_frame = None
    for w in content_widgets:
        if isinstance(w, AttendanceViewFrame):
            att_view_frame = w
            break
    assert att_view_frame is not None, "AttendanceViewFrame not found in Student Dashboard"
    att_view_frame.entry_year.delete(0, tk.END)
    att_view_frame.entry_year.insert(0, "2026")
    if hasattr(att_view_frame.entry_month, 'set'):
        att_view_frame.entry_month.set("August")
    else:
        att_view_frame.entry_month.delete(0, tk.END)
        att_view_frame.entry_month.insert(0, "August")
    att_view_frame.refresh_table()

    single_items = att_view_frame.tree_single.get_children()
    single_dates = [att_view_frame.tree_single.item(item)['values'][0] for item in single_items]
    print("Embedded single table dates in August 2026:", single_dates)
    # Check that 2026-08-28 comes before 2026-08-30, and 2026-08-30 comes before 2026-08-31
    assert single_dates == sorted(single_dates), f"Dates not in ascending chronological order: {single_dates}"
    print("PASS: Embedded AttendanceViewFrame date order is properly sorted chronologically.")

    print("=== TEST 3: MONTHLY ATTENDANCE DIALOG (AUGUST 2026) ===")
    dialog = IndividualStudentAttendanceDialog(student_portal, db, "STU_AMRITA")
    dialog.entry_month.set("August")
    dialog.entry_year.delete(0, tk.END)
    dialog.entry_year.insert(0, "2026")
    dialog.load_attendance()

    items_aug = dialog.tree.get_children()
    aug_dates = [dialog.tree.item(item)['values'][0] for item in items_aug]
    aug_statuses = [dialog.tree.item(item)['values'][1] for item in items_aug]
    print("August dates:", aug_dates)
    print("August statuses:", aug_statuses)

    # Amrita Admission Date is 2026-08-28 -> August should display 28 August, 29 August, 30 August, 31 August
    assert len(items_aug) == 4, f"Expected 4 dates (28..31 August), got {len(items_aug)}"
    assert aug_dates == ["28 August", "29 August", "30 August", "31 August"], f"Incorrect August date sequence: {aug_dates}"
    
    # 28 August was Present
    assert aug_statuses[0] == "Present", f"Expected Present on 28 Aug, got {aug_statuses[0]}"
    # 29 August had no record (and is past date <= 2026-08-31) -> Absent
    assert aug_statuses[1] == "Absent", f"Expected Absent on 29 Aug (no record rule), got {aug_statuses[1]}"
    # 30 August was Leave
    assert aug_statuses[2] == "Leave", f"Expected Leave on 30 Aug, got {aug_statuses[2]}"
    # 31 August was Present
    assert aug_statuses[3] == "Present", f"Expected Present on 31 Aug, got {aug_statuses[3]}"
    print("PASS: August 2026 date sequence and status rules strictly verified.")

    print("=== TEST 4: NEW MONTH NAVIGATION (SEPTEMBER 2026) ===")
    dialog.entry_month.set("September")
    dialog.entry_year.delete(0, tk.END)
    dialog.entry_year.insert(0, "2026")
    dialog.load_attendance()

    items_sep = dialog.tree.get_children()
    sep_dates = [dialog.tree.item(item)['values'][0] for item in items_sep]
    sep_statuses = [dialog.tree.item(item)['values'][1] for item in items_sep]
    print(f"September total days: {len(sep_dates)}, First 5: {sep_dates[:5]}")

    assert len(items_sep) == 30, f"Expected 30 dates for September, got {len(items_sep)}"
    assert sep_dates[0] == "1 September"
    assert sep_dates[1] == "2 September"
    assert sep_dates[2] == "3 September"
    assert sep_dates[3] == "4 September"
    assert sep_dates[29] == "30 September"

    # Status check
    assert sep_statuses[0] == "Present", f"Expected Present on 1 Sep, got {sep_statuses[0]}"
    assert sep_statuses[1] == "Absent", f"Expected Absent on 2 Sep, got {sep_statuses[1]}"
    assert sep_statuses[2] == "Leave", f"Expected Leave on 3 Sep, got {sep_statuses[2]}"
    print("PASS: September 2026 starts 1 September -> 2 September -> 3 September ... in chronological order.")

    print("=== TEST 5: RETURN TO AUGUST (PREVIOUS DATA PERSISTENCE) ===")
    dialog.entry_month.set("August")
    dialog.entry_year.delete(0, tk.END)
    dialog.entry_year.insert(0, "2026")
    dialog.load_attendance()

    items_aug_again = dialog.tree.get_children()
    assert len(items_aug_again) == 4, f"August data lost after switching months! Got {len(items_aug_again)}"
    assert dialog.tree.item(items_aug_again[0])['values'][0] == "28 August"
    assert dialog.tree.item(items_aug_again[3])['values'][0] == "31 August"
    print("PASS: Previous month data remains viewable and persisted.")

    print("=== TEST 6: COLLEGE STUDENT MONTHLY VIEW ===")
    col_dialog = IndividualStudentAttendanceDialog(student_portal, db, "STU_COL_ANANYA")
    col_dialog.entry_month.set("August")
    col_dialog.entry_year.delete(0, tk.END)
    col_dialog.entry_year.insert(0, "2026")
    col_dialog.load_attendance()

    items_col_aug = col_dialog.tree.get_children()
    assert len(items_col_aug) == 31, f"Ananya admitted 1 Aug, expected 31 days in Aug, got {len(items_col_aug)}"
    # 30 August & 31 August Present
    val_30 = col_dialog.tree.item(items_col_aug[29])['values']
    val_31 = col_dialog.tree.item(items_col_aug[30])['values']
    assert val_30[0] == "30 August" and val_30[1] == "Present", f"30 Aug College test failed: {val_30}"
    assert val_31[0] == "31 August" and val_31[1] == "Present", f"31 Aug College test failed: {val_31}"
    assert val_30[3] == "ENR2026001", f"Expected Enrollment No in college row, got {val_30[3]}"
    print("PASS: College mode monthly attendance view verified.")

    print("=== TEST 7: STUDENT DATA ISOLATION ===")
    # Amrita only sees Amrita data, Ananya only sees Ananya data
    for itm in dialog.tree.get_children():
        v = dialog.tree.item(itm)['values']
        assert v[3] == "STU_AMRITA", f"Wrong student ID in Amrita dialog: {v[3]}"
        assert v[4] == "Amrita Thakur", f"Wrong student name in Amrita dialog: {v[4]}"

    for itm in col_dialog.tree.get_children():
        v = col_dialog.tree.item(itm)['values']
        assert v[3] == "ENR2026001", f"Wrong enrollment/ID in Ananya dialog: {v[3]}"
        assert v[4] == "Ananya Sharma", f"Wrong student name in Ananya dialog: {v[4]}"
    print("PASS: Data strictly isolated to logged-in student.")

    # Cleanup
    dialog.destroy()
    col_dialog.destroy()
    student_portal.destroy()
    root.destroy()

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

    print("\n=======================================================")
    print(">>> ALL FINAL TESTS PASSED WITH ZERO ERRORS! <<<")
    print("=======================================================")

if __name__ == '__main__':
    run_tests()
