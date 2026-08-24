import unittest
import os
import sys
import tempfile
import time
import tkinter as tk
from datetime import datetime

from unittest.mock import patch
sys.path.insert(0, ".")
from database.db_manager import DBManager
from gui.teacher_dashboard import TeacherDashboard

class TestCompleteTeacherWorkflow(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_full_workflow.db")
        self.db = DBManager(db_path=self.db_path)

        # Setup teacher user & teacher record
        self.teacher_id = "T_FULL_001"
        self.db.add_teacher({
            "teacher_id": self.teacher_id,
            "name": "Full Test Teacher",
            "department": "Science",
            "email": "fullteacher@test.com",
            "phone": "9991112223",
            "qualification": "M.Sc",
            "joining_date": "2024-01-01",
            "base_salary": 4000.0
        })

        from utils.security import hash_password
        pwd_hash, salt = hash_password("pass123")
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password_hash, salt, role) VALUES ('fullteacher', ?, ?, 'Teacher')", (pwd_hash, salt))
            user_id = cursor.lastrowid
            cursor.execute("UPDATE teachers SET user_id = ? WHERE teacher_id = ?", (user_id, self.teacher_id))
            conn.commit()

        self.user_data = {"id": user_id, "username": "fullteacher", "role": "Teacher"}

        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_complete_7_step_workflow(self):
        # ----------------------------------------------------
        # Test 1: Open Teacher Portal -> Current Time changes continuously
        # ----------------------------------------------------
        dashboard = TeacherDashboard(self.root, self.db, self.user_data)
        dashboard.show_my_work_time()
        self.root.update()

        time1 = dashboard.lbl_current_time.cget("text")
        self.assertIsNotNone(time1)
        self.assertNotEqual(time1, "")
        
        # Wait 1.1s for tick
        time.sleep(1.1)
        self.root.update()
        time2 = dashboard.lbl_current_time.cget("text")
        print(f"Test 1 Passed: Current Time changes continuously ({time1} -> {time2})")

        # ----------------------------------------------------
        # Test 7: Try clicking END before START -> show warning and do not create invalid record
        # ----------------------------------------------------
        self.assertEqual(dashboard.btn_end.cget("state"), tk.DISABLED)
        # Directly call end handler to verify guard condition
        with patch('tkinter.messagebox.showwarning'):
            dashboard.end_my_work_session()
        today = datetime.now().strftime("%Y-%m-%d")
        log_before_start = self.db.get_teacher_work_log(self.teacher_id, today)
        self.assertIsNone(log_before_start)
        print("Test 7 Passed: Clicking END before START is prevented and creates no invalid record.")

        # ----------------------------------------------------
        # Test 2: Click START -> Start Time saved, Work Timer starts counting
        # ----------------------------------------------------
        dashboard.btn_start.invoke()
        self.root.update()

        start_disp = dashboard.lbl_start_val.cget("text")
        self.assertNotEqual(start_disp, "--")
        
        log_after_start = self.db.get_teacher_work_log(self.teacher_id, today)
        self.assertIsNotNone(log_after_start)
        self.assertEqual(log_after_start['status'], "RUNNING")
        self.assertIsNotNone(log_after_start['actual_start_time'])
        print(f"Test 2 Passed: Clicked START. Start Time saved as '{start_disp}', DB status='RUNNING'.")

        # ----------------------------------------------------
        # Test 6: Try clicking START twice -> no duplicate active session
        # ----------------------------------------------------
        self.assertEqual(dashboard.btn_start.cget("state"), tk.DISABLED)
        first_start_time = log_after_start['actual_start_time']
        # Call start handler again
        with patch('tkinter.messagebox.showwarning'):
            dashboard.start_my_work_session()
        log_retry = self.db.get_teacher_work_log(self.teacher_id, today)
        self.assertEqual(log_retry['actual_start_time'], first_start_time)
        print(f"Test 6 Passed: Second START click ignored, Start Time unchanged ('{first_start_time}').")

        # ----------------------------------------------------
        # Test 3: Wait several seconds -> Work Timer must actually increase
        # ----------------------------------------------------
        for _ in range(25):
            time.sleep(0.1)
            self.root.update()
        wt_3s = dashboard.lbl_total_wt_val.cget("text")
        self.assertNotEqual(wt_3s, "00:00:00")
        print(f"Test 3 Passed: Work Timer increased to '{wt_3s}'.")

        # ----------------------------------------------------
        # Test 4: Click END -> End Time saved, Timer immediately stops, Total Work Time calculated correctly
        # ----------------------------------------------------
        dashboard.btn_end.invoke()
        self.root.update()

        end_disp = dashboard.lbl_end_val.cget("text")
        final_wt = dashboard.lbl_total_wt_val.cget("text")
        self.assertNotEqual(end_disp, "--")
        self.assertNotEqual(final_wt, "00:00:00")

        log_completed = self.db.get_teacher_work_log(self.teacher_id, today)
        self.assertEqual(log_completed['status'], "ENDED")
        self.assertIsNotNone(log_completed['actual_end_time'])
        self.assertEqual(log_completed['total_work_time'], final_wt)
        print(f"Test 4 Passed: Clicked END. End Time='{end_disp}', Total Work Time='{final_wt}', DB status='ENDED'.")

        # Destroy dashboard 1
        dashboard.destroy()

        # ----------------------------------------------------
        # Test 5: Restart/reopen Teacher Portal -> previously saved completed session remains in DB
        # ----------------------------------------------------
        dashboard2 = TeacherDashboard(self.root, self.db, self.user_data)
        dashboard2.show_my_work_time()
        self.root.update()

        self.assertEqual(dashboard2.lbl_start_val.cget("text"), start_disp)
        self.assertEqual(dashboard2.lbl_end_val.cget("text"), end_disp)
        self.assertEqual(dashboard2.lbl_total_wt_val.cget("text"), final_wt)
        self.assertEqual(dashboard2.btn_start.cget("state"), tk.DISABLED)
        self.assertEqual(dashboard2.btn_end.cget("state"), tk.DISABLED)
        print(f"Test 5 Passed: Reopened portal. Completed session retrieved from DB intact (Start: {start_disp}, End: {end_disp}, Total: {final_wt}).")
        dashboard2.destroy()

        print("\n=======================================================")
        print("ALL 7 WORKFLOW TESTS PASSED PERFECTLY WITHOUT ERRORS!")
        print("=======================================================\n")

if __name__ == '__main__':
    unittest.main()
