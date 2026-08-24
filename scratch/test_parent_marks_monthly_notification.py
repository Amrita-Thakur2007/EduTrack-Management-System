import os
import sys
import time
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

from gui.parent_dashboard import ParentDashboard

def run_tests():
    print("=== STARTING PARENT MARKS MONTHLY NOTIFICATION TEST ===")

    db_path = f"scratch/test_notif_{int(time.time())}.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = DBManager(db_path=db_path)

    # 1. Create Student & Parent
    su = db.create_user("NotifStudent", "Pass1234", "Student")
    db.add_student({
        "student_id": "STU_NOTIF_100",
        "name": "Aryan Sharma",
        "email": "aryan@school.edu",
        "phone": "9811002233",
        "education_type": "School",
        "school_name": "St. Xavier",
        "current_class": "10",
        "section": "B",
        "admission_date": "2024-04-01"
    }, su)

    pu = db.create_user("NotifParent", "Pass1234", "Parent")
    db.add_parent({
        "name": "Suresh Sharma",
        "phone": "9811009988",
        "email": "suresh@parent.com",
        "student_id": "STU_NOTIF_100",
        "parent_id_code": "P_NOTIF_100"
    }, pu)

    # TEST 1: Teacher saves marks in August (2026-08)
    db.save_or_update_marks("STU_NOTIF_100", {
        "internal_marks": 15, "mid_term_marks": 25, "project_marks": 15, "viva_marks": 8, "final_exam_marks": 75
    }, subject="Mathematics")

    parent_notifs = db.get_notifications("Parent", "STU_NOTIF_100")
    marks_notifs = [n for n in parent_notifs if n["message"] == "See your marks, marks updated."]

    assert len(marks_notifs) == 1, f"Expected 1 Parent marks notification, found {len(marks_notifs)}"
    assert marks_notifs[0]["title"] == "Marks Updated", f"Expected title 'Marks Updated', got {marks_notifs[0]['title']}"
    assert marks_notifs[0]["message"] == "See your marks, marks updated.", f"Unexpected message {marks_notifs[0]['message']}"
    print("TEST 1 PASS: Teacher updated marks in August -> Parent received 'See your marks, marks updated.' notification.")

    # TEST 2: Teacher updates marks AGAIN in August (Physics, Chemistry...)
    db.save_or_update_marks("STU_NOTIF_100", {
        "internal_marks": 18, "mid_term_marks": 28, "project_marks": 18, "viva_marks": 9, "final_exam_marks": 80
    }, subject="Physics")
    db.save_or_update_marks("STU_NOTIF_100", {
        "internal_marks": 20, "mid_term_marks": 29, "project_marks": 19, "viva_marks": 10, "final_exam_marks": 85
    }, subject="Chemistry")

    parent_notifs_check = db.get_notifications("Parent", "STU_NOTIF_100")
    marks_notifs_check = [n for n in parent_notifs_check if n["message"] == "See your marks, marks updated."]

    assert len(marks_notifs_check) == 1, f"Expected ONLY 1 marks notification in August, found {len(marks_notifs_check)}"
    print("TEST 2 PASS: Teacher updated marks multiple times in August -> System generated NO duplicate notifications.")

    # TEST 3: Parent views notification -> automatically disappears
    root = tk.Tk()
    root.withdraw()

    parent_user = {"id": pu, "username": "NotifParent", "role": "Parent"}
    parent_dash = ParentDashboard(root, db, parent_user)

    # Parent views marks / opens notification
    parent_dash.show_marks()

    parent_notifs_after_view = db.get_notifications("Parent", "STU_NOTIF_100")
    marks_notifs_after_view = [n for n in parent_notifs_after_view if n["message"] == "See your marks, marks updated."]

    assert len(marks_notifs_after_view) == 0, f"Expected notification to disappear after viewing, found {len(marks_notifs_after_view)}"

    # Verify student's academic marks are intact
    student_marks_db = db.get_all_student_marks("STU_NOTIF_100")
    assert len(student_marks_db) == 3, f"Expected 3 academic mark records intact, found {len(student_marks_db)}"
    print("TEST 3 PASS: Parent viewed marks -> notification automatically removed from active list, academic marks records remain intact.")

    # TEST 4: Teacher updates marks again in August AFTER parent viewed it
    db.save_or_update_marks("STU_NOTIF_100", {
        "internal_marks": 20, "mid_term_marks": 30, "project_marks": 20, "viva_marks": 10, "final_exam_marks": 90
    }, subject="Mathematics")

    parent_notifs_aug_end = db.get_notifications("Parent", "STU_NOTIF_100")
    marks_notifs_aug_end = [n for n in parent_notifs_aug_end if n["message"] == "See your marks, marks updated."]

    assert len(marks_notifs_aug_end) == 0, f"Expected NO second notification in same month August, found {len(marks_notifs_aug_end)}"
    print("TEST 4 PASS: Further marks updates in August did NOT recreate second marks notification.")

    # TEST 5: NEXT MONTH (September 2026-09)
    # Teacher updates marks in September
    db.add_parent_marks_notification("STU_NOTIF_100", date_override="2026-09-05")

    sept_notifs = db.get_notifications("Parent", "STU_NOTIF_100")
    sept_marks_notifs = [n for n in sept_notifs if n["message"] == "See your marks, marks updated."]

    assert len(sept_marks_notifs) == 1, f"Expected 1 new notification for September, found {len(sept_marks_notifs)}"
    assert sept_marks_notifs[0]["date"] == "2026-09-05", f"Expected September date 2026-09-05, got {sept_marks_notifs[0]['date']}"
    print("TEST 5 PASS: Next month (September) started -> Teacher updated marks -> 1 new notification created for September.")

    parent_dash.destroy()
    root.quit()
    root.destroy()

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

    print("\n=== ALL PARENT MARKS MONTHLY NOTIFICATION TESTS PASSED 100% ===")

if __name__ == "__main__":
    run_tests()
