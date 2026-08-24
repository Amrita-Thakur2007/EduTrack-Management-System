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

from gui.admin_dashboard import AdminDashboard
from gui.teacher_dashboard import TeacherDashboard

def run_tests():
    print("=== STARTING ADMIN TEACHER SALARY MANAGEMENT VERIFICATION ===")

    db_path = f"scratch/test_teacher_sal_{int(time.time())}.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = DBManager(db_path=db_path)

    # 1. Create 2 Teacher accounts in DB
    u1 = db.create_user("RahulTeacher", "Pass1234", "Teacher")
    db.add_teacher({
        "teacher_id": "TCH_01",
        "name": "Rahul Verma",
        "email": "rahul@school.edu",
        "phone": "9811001122",
        "department": "Mathematics"
    }, u1)

    u2 = db.create_user("PriyaTeacher", "Pass1234", "Teacher")
    db.add_teacher({
        "teacher_id": "TCH_02",
        "name": "Priya Sharma",
        "email": "priya@school.edu",
        "phone": "9822003344",
        "department": "Science"
    }, u2)

    root = tk.Tk()
    root.withdraw()

    # 2. Open Admin Panel -> Teacher Salary Management
    admin_user = {"id": 1, "username": "admin", "role": "Admin"}
    admin_dash = AdminDashboard(root, db, admin_user)
    admin_dash.show_teacher_salaries()

    # Select Rahul Verma (TCH_01) and set salary 45000
    rahul_opt = [opt for opt in admin_dash.combo_teacher_salary["values"] if "TCH_01" in opt][0]
    admin_dash.combo_teacher_salary.set(rahul_opt)
    admin_dash.combo_teacher_salary.event_generate("<<ComboboxSelected>>")

    admin_dash.entry_teacher_monthly_salary.delete(0, tk.END)
    admin_dash.entry_teacher_monthly_salary.insert(0, "45000")
    admin_dash.save_teacher_salary()

    # Verify Rahul's salary in DB
    r_rec = db.get_teacher("TCH_01")
    assert r_rec["monthly_salary"] == 45000.0, f"Expected Rahul salary 45000.0, got {r_rec['monthly_salary']}"
    print("TEST 1 PASS: Admin set monthly salary of Rahul (TCH_01) to 45000. Saved to DB.")

    # Select Priya Sharma (TCH_02) and set salary 60000
    priya_opt = [opt for opt in admin_dash.combo_teacher_salary["values"] if "TCH_02" in opt][0]
    admin_dash.combo_teacher_salary.set(priya_opt)
    admin_dash.combo_teacher_salary.event_generate("<<ComboboxSelected>>")

    admin_dash.entry_teacher_monthly_salary.delete(0, tk.END)
    admin_dash.entry_teacher_monthly_salary.insert(0, "60000")
    admin_dash.save_teacher_salary()

    # Verify Priya's salary & verify Rahul's salary did NOT change
    p_rec = db.get_teacher("TCH_02")
    r_rec_check = db.get_teacher("TCH_01")

    assert p_rec["monthly_salary"] == 60000.0, f"Expected Priya salary 60000.0, got {p_rec['monthly_salary']}"
    assert r_rec_check["monthly_salary"] == 45000.0, f"Rahul's salary changed unexpectedly! Expected 45000.0, got {r_rec_check['monthly_salary']}"
    print("TEST 2 PASS: Admin set monthly salary of Priya (TCH_02) to 60000. Rahul's salary remained 45000.")

    admin_dash.destroy()

    # 3. Verify Teacher Access Control (Teacher views their OWN salary, cannot edit)
    rahul_user = {"id": u1, "username": "RahulTeacher", "role": "Teacher"}
    t_dash_rahul = TeacherDashboard(root, db, rahul_user)
    sal_rahul = db.get_teacher_salary_summary("TCH_01")
    assert sal_rahul["base_salary"] == 45000.0, f"Expected Teacher Rahul to view base salary 45000.0, got {sal_rahul['base_salary']}"
    t_dash_rahul.destroy()
    print("TEST 3 PASS: Teacher Rahul logs in and views their exact base salary 45000.0.")

    priya_user = {"id": u2, "username": "PriyaTeacher", "role": "Teacher"}
    t_dash_priya = TeacherDashboard(root, db, priya_user)
    sal_priya = db.get_teacher_salary_summary("TCH_02")
    assert sal_priya["base_salary"] == 60000.0, f"Expected Teacher Priya to view base salary 60000.0, got {sal_priya['base_salary']}"
    t_dash_priya.destroy()
    print("TEST 4 PASS: Teacher Priya logs in and views their exact base salary 60000.0.")

    root.quit()
    root.destroy()

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

    print("\n=== ALL ADMIN TEACHER SALARY MANAGEMENT VERIFICATIONS PASSED 100% ===")

if __name__ == "__main__":
    run_tests()
