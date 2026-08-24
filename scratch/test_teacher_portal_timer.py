import unittest
import os
import sys
import tempfile
import time
import tkinter as tk

sys.path.insert(0, ".")
from database.db_manager import DBManager
from utils.helpers import get_current_date, parse_datetime_helper
from gui.teacher_dashboard import TeacherDashboard

class TestTeacherPortalTimerGUI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_gui_timer.db")
        self.db = DBManager(db_path=self.db_path)
        u_id = self.db.create_user("Sakshi", "password123", "Teacher")
        self.user_data = {
            "id": u_id,
            "username": "Sakshi",
            "role": "Teacher"
        }
        
        self.teacher_id = "T101"
        self.db.add_teacher({
            "teacher_id": self.teacher_id,
            "name": "Sakshi Sharma",
            "department": "Science",
            "email": "sakshi@school.com",
            "phone": "9876543210",
            "qualification": "M.Sc Physics",
            "joining_date": "2024-01-01",
            "base_salary": 4500.0
        }, user_id=u_id)
        
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        try:
            if hasattr(self, 'dashboard') and self.dashboard:
                self.dashboard.destroy()
            self.root.destroy()
        except Exception:
            pass

    def test_full_gui_timer_workflow(self):
        today = get_current_date()

        # Step 1: Open Teacher Dashboard and view Work Time
        self.dashboard = TeacherDashboard(self.root, self.db, self.user_data)
        dashboard = self.dashboard
        dashboard.show_my_work_time()
        dashboard.update()

        from unittest.mock import patch
        patcher = patch('tkinter.messagebox.showwarning')
        patcher_err = patch('tkinter.messagebox.showerror')
        mock_warn = patcher.start()
        mock_err = patcher_err.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(patcher_err.stop)

        # Step 2: Verify Initial Button States and Values
        self.assertEqual(str(dashboard.btn_start.cget("state")), str(tk.NORMAL), "START button must be ENABLED initially.")
        self.assertEqual(str(dashboard.btn_end.cget("state")), str(tk.DISABLED), "END button must be DISABLED initially.")
        self.assertEqual(dashboard.lbl_status_val.cget("text"), "NOT STARTED")
        self.assertEqual(dashboard.lbl_total_wt_val.cget("text"), "00:00:00")

        # Step 3: Attempt END before START
        dashboard.end_my_work_session()
        log_before_start = self.db.get_teacher_work_log(self.teacher_id, today)
        self.assertIsNone(log_before_start, "No work log should be created on END before START.")

        # Step 4: Click START
        dashboard.start_my_work_session()
        dashboard.update()

        # Step 5: Verify Active Button States and Values
        self.assertEqual(str(dashboard.btn_start.cget("state")), str(tk.DISABLED), "START button must be DISABLED after START.")
        self.assertEqual(str(dashboard.btn_end.cget("state")), str(tk.NORMAL), "END button must be ENABLED after START.")
        self.assertEqual(dashboard.lbl_status_val.cget("text"), "WORKING")
        
        log_after_start = self.db.get_teacher_work_log(self.teacher_id, today)
        self.assertIsNotNone(log_after_start)
        self.assertIsNotNone(log_after_start.get('start_time'))

        # Step 6: Attempt duplicate START click
        dashboard.start_my_work_session()
        log_retry = self.db.get_teacher_work_log(self.teacher_id, today)
        self.assertEqual(log_retry['start_time'], log_after_start['start_time'], "Start Time must not change on duplicate START.")

        # Step 7: Wait 2 seconds and verify live working time accumulation
        time.sleep(2)
        dashboard.update()
        wt_str = dashboard.lbl_total_wt_val.cget("text")
        self.assertNotEqual(wt_str, "00:00:00", "Working Time must accumulate continuously.")

        # Step 8: Click END
        dashboard.end_my_work_session()
        dashboard.update()

        # Step 9: Verify Completed Button States and Values
        self.assertEqual(str(dashboard.btn_start.cget("state")), str(tk.DISABLED), "START button must be DISABLED after END.")
        self.assertEqual(str(dashboard.btn_end.cget("state")), str(tk.DISABLED), "END button must be DISABLED after END.")
        self.assertEqual(dashboard.lbl_status_val.cget("text"), "WORK COMPLETED")
        
        log_after_end = self.db.get_teacher_work_log(self.teacher_id, today)
        self.assertIsNotNone(log_after_end.get('end_time'))

        # Step 10: Page Navigation and Persistence
        # Switch to Salary view and return to Work Time view
        dashboard.show_my_salary()
        dashboard.update()
        dashboard.show_my_work_time()
        dashboard.update()

        self.assertEqual(str(dashboard.btn_start.cget("state")), str(tk.DISABLED))
        self.assertEqual(str(dashboard.btn_end.cget("state")), str(tk.DISABLED))
        self.assertEqual(dashboard.lbl_status_val.cget("text"), "WORK COMPLETED")

        print("\nALL 10 FULL GUI TIMER WORKFLOW CHECKS PASSED PERFECTLY!")

if __name__ == '__main__':
    unittest.main()
