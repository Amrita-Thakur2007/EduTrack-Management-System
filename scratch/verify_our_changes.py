import unittest
import os
import sys
import tempfile
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

sys.path.insert(0, ".")
from database.db_manager import DBManager
from gui.teacher_dashboard import TeacherDashboard

class TestWorkTimeDashboardChanges(unittest.TestCase):
    def setUp(self):
        # Create a temporary database for testing
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_verify.db")
        self.db = DBManager(db_path=self.db_path)
        
        # Set up a test teacher
        self.teacher_id = "T_VERIFY"
        self.user_id = 999
        self.base_salary = 30000.0
        
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO users (id, username, password_hash, salt, role)
                VALUES (?, 'verify_teacher', 'hash', 'salt', 'Teacher')
            """, (self.user_id, ))
            conn.execute("""
                INSERT INTO teachers (teacher_id, user_id, name, department, email, phone, monthly_salary)
                VALUES (?, ?, 'Verify Sakshi', 'Science', 'verify@test.com', '1234567890', ?)
            """, (self.teacher_id, self.user_id, self.base_salary))
            conn.commit()

        # Initialize Tkinter root in background
        self.root = tk.Tk()
        self.root.withdraw()

        # Mock messagebox functions globally for tests to prevent hanging
        self.message_shown = []
        self.old_showinfo = messagebox.showinfo
        self.old_showerror = messagebox.showerror
        messagebox.showinfo = lambda title, message: self.message_shown.append(message)
        messagebox.showerror = lambda title, message: self.message_shown.append(message)

    def tearDown(self):
        messagebox.showinfo = self.old_showinfo
        messagebox.showerror = self.old_showerror
        self.root.destroy()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass

    def test_school_timing_status_calculations(self):
        user_data = {"id": self.user_id, "username": "verify_teacher", "role": "Teacher"}
        dashboard = TeacherDashboard(self.root, self.db, user_data)
        
        # 1. 07:30 AM -> Congratulations / On Time
        s1 = dashboard.calculate_status_string("07:30:00 AM", None, "2026-08-27")
        self.assertIn("Congratulations", s1)

        # 2. 07:25 AM -> Early
        s2 = dashboard.calculate_status_string("07:25:00 AM", None, "2026-08-27")
        self.assertEqual(s2, "🟢 You are early.")

        # 3. 07:31 AM -> Late by 1 minute
        s3 = dashboard.calculate_status_string("07:31:00 AM", None, "2026-08-27")
        self.assertEqual(s3, "⚠️ You are late by 1 minute.")

        # 4. 07:32 AM -> Late by 2 minutes
        s4 = dashboard.calculate_status_string("07:32:00 AM", None, "2026-08-27")
        self.assertEqual(s4, "⚠️ You are late by 2 minutes.")

        # 5. 07:35 AM -> Late by 5 minutes
        s5 = dashboard.calculate_status_string("07:35:00 AM", None, "2026-08-27")
        self.assertEqual(s5, "⚠️ You are late by 5 minutes.")

        # 6. 08:00 AM -> Late by 30 minutes
        s6 = dashboard.calculate_status_string("08:00:00 AM", None, "2026-08-27")
        self.assertEqual(s6, "⚠️ You are late by 30 minutes.")

        # 7. After 12:30 PM -> Time is over
        s7 = dashboard.calculate_status_string("03:07:00 PM", None, "2026-08-27")
        self.assertEqual(s7, "⏰ SCHOOL TIME IS OVER")

    def test_automatic_start_time_on_successful_login(self):
        user_data = {"id": self.user_id, "username": "verify_teacher", "role": "Teacher"}
        
        # Verify no log before login
        from utils.helpers import get_current_date
        today = get_current_date()
        db_log_before = self.db.get_teacher_work_log(self.teacher_id, today)
        self.assertIsNone(db_log_before)

        # Instantiate Dashboard (Simulates successful login)
        dashboard = TeacherDashboard(self.root, self.db, user_data)
        
        # Verify Start Time is automatically created in DB
        db_log_after = self.db.get_teacher_work_log(self.teacher_id, today)
        self.assertIsNotNone(db_log_after)
        self.assertIsNotNone(db_log_after.get('start_time'))

        dashboard.show_my_work_time()

        # START TIME button must still exist and be functional
        self.assertTrue(hasattr(dashboard, 'btn_start_time'))
        self.assertTrue(hasattr(dashboard, 'btn_end_time'))

        # Verify Live Time and Working Time labels exist
        self.assertTrue(hasattr(dashboard, 'lbl_live_time_val'))
        self.assertTrue(hasattr(dashboard, 'lbl_work_time_val'))

        # Verify Live Time is just time format HH:MM:SS without RUNNING text
        live_txt = dashboard.lbl_live_time_val.cget("text")
        self.assertNotIn("RUNNING", live_txt)
        self.assertNotIn("STOPPED", live_txt)

        # Clicking START TIME button when time is already running
        dashboard.click_start_time()
        
        self.assertTrue(any("already running" in msg for msg in self.message_shown))

        # Check duplicate logic: Start Time remains the same
        db_log_dup = self.db.get_teacher_work_log(self.teacher_id, today)
        self.assertEqual(db_log_dup.get('start_time'), db_log_after.get('start_time'))

        # Click END TIME
        dashboard.click_end_time()

        # Reopen Work Time Dashboard and verify values remain correct
        dashboard.show_my_work_time()
        live_txt_stopped = dashboard.lbl_live_time_val.cget("text")
        self.assertNotIn("RUNNING", live_txt_stopped)
        self.assertNotIn("STOPPED", live_txt_stopped)
        self.assertNotEqual(dashboard.lbl_work_time_val.cget("text"), "--")

    def test_salary_deductions_calculation(self):
        # We will manually calculate lateness deductions using the exact logic:
        # Per Minute Salary = (monthly_salary / N) / 300.0 (where N is actual days in month)
        # Deduction = Late Minutes * Per Minute Salary
        import calendar
        now = datetime.now()
        num_days = calendar.monthrange(now.year, now.month)[1]
        monthly_salary = 30000.0
        per_minute_salary = (monthly_salary / num_days) / 300.0

        # Test late by 5 mins
        late_mins = 5
        expected_deduction = round(late_mins * per_minute_salary, 2)
        
        # We verify that our DB salary calculations are filtered by Month and Year
        # Let's insert a simulated work log record for today
        from utils.helpers import get_current_date
        today = get_current_date()
        salary_month = datetime.now().month
        salary_year = datetime.now().year
        
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO teacher_work_logs (
                    teacher_id, teacher_name, date, work_date, official_start_time, official_end_time,
                    actual_start_time, start_time, status, session_status, attendance_status,
                    late_minutes, face_verified, salary_deduction, salary_eligible, salary_month, salary_year
                ) VALUES (?, 'Verify Sakshi', ?, ?, '07:30 AM', '12:30 PM', '07:35:00 AM', '07:35:00 AM',
                         'Late', 'Late', 'Late', ?, 1, ?, 'YES', ?, ?)
            """, (self.teacher_id, today, today, late_mins, expected_deduction, salary_month, salary_year))
            
            # Log attendance
            conn.execute("""
                INSERT INTO teacher_attendance (teacher_id, date, time, status)
                VALUES (?, ?, '07:35:00 AM', 'Present')
            """, (self.teacher_id, today))
            conn.commit()

        # Retrieve salary summary
        summary = self.db.get_teacher_salary_summary(self.teacher_id, monthly_salary)
        self.assertEqual(summary['late_summary_mins'], 5)
        self.assertEqual(summary['late_deduction'], expected_deduction)

    def test_login_after_school_ends(self):
        # If teacher logs in after 12:30 PM:
        # Salary Eligible = NO, status = SCHOOL TIME IS OVER
        user_data = {"id": self.user_id, "username": "verify_teacher", "role": "Teacher"}
        
        dashboard = TeacherDashboard(self.root, self.db, user_data)
        
        status_str = dashboard.calculate_status_string("03:07:00 PM", None, "2026-08-27")
        self.assertEqual(status_str, "⏰ SCHOOL TIME IS OVER")

if __name__ == '__main__':
    unittest.main()
