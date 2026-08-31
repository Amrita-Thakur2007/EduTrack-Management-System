import unittest
import os
import sys
import tempfile
import time
import tkinter as tk
from unittest.mock import patch
from datetime import datetime

sys.path.insert(0, ".")
from database.db_manager import DBManager
from gui.teacher_dashboard import TeacherDashboard

class TestActualTeacherDashboard(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_actual_dashboard.db")
        self.db = DBManager(db_path=self.db_path)
        
        # Setup teacher
        self.teacher_id = "T_TEST_001"
        self.db.add_teacher({
            "teacher_id": self.teacher_id,
            "name": "Test Teacher",
            "department": "CSE",
            "email": "test@school.com",
            "phone": "9998887776",
            "qualification": "ME",
            "joining_date": "2024-01-01",
            "base_salary": 6000.0
        })

        from utils.security import hash_password
        pwd_hash, salt = hash_password("pass123")
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password_hash, salt, role) VALUES ('testteacher', ?, ?, 'Teacher')", (pwd_hash, salt))
            user_id = cursor.lastrowid
            cursor.execute("UPDATE teachers SET user_id = ? WHERE teacher_id = ?", (user_id, self.teacher_id))
            conn.commit()

        self.user_data = {"id": user_id, "username": "testteacher", "role": "Teacher"}
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    @patch('tkinter.messagebox.showinfo')
    @patch('tkinter.messagebox.showerror')
    def test_dashboard_flow(self, mock_error, mock_info):
        # 1. Initialize dashboard -> Simulates Login
        dashboard = TeacherDashboard(self.root, self.db, self.user_data)
        
        # Capture times
        sess_start = dashboard.session_start_time
        sess_date = dashboard.session_date
        
        self.assertIsNotNone(sess_start)
        self.assertIsNotNone(sess_date)
        
        # Verify a record was automatically created in database for today
        log = self.db.get_teacher_work_log(self.teacher_id, sess_date)
        self.assertIsNotNone(log)
        self.assertEqual(log['start_time'], sess_start)
        expected_status = dashboard.calculate_status_string(sess_start, None, sess_date)
        self.assertEqual(log['status'], expected_status)
        
        # 2. Render Work Time View
        dashboard.show_my_work_time()
        self.root.update()
        
        # Verify UI Labels are set
        self.assertEqual(dashboard.lbl_start_time.cget("text"), sess_start)
        self.assertEqual(dashboard.lbl_end_time.cget("text"), "--")
        self.assertEqual(dashboard.lbl_work_time_val.cget("text"), "--")
        
        # Live Time label exists
        live_init = dashboard.lbl_live_time_val.cget("text")
        self.assertIsNotNone(live_init)
        
        # Buttons must be enabled (state is normal/active)
        self.assertNotIn("disabled", dashboard.btn_start_time.state())
        self.assertNotIn("disabled", dashboard.btn_end_time.state())
        
        # 3. Clicking START TIME button again must show "already running"
        # We can trigger click_start_time
        dashboard.click_start_time()
        # Verify start time is unchanged in database
        log_after_start_click = self.db.get_teacher_work_log(self.teacher_id, sess_date)
        self.assertEqual(log_after_start_click['start_time'], sess_start)
        
        # 4. Click END TIME
        dashboard.click_end_time()
        
        # Verify database record updated
        log_ended = self.db.get_teacher_work_log(self.teacher_id, sess_date)
        self.assertIsNotNone(log_ended['end_time'])
        self.assertNotEqual(log_ended['total_work_time'], "00:00:00")
        
        # Verify UI updated after end time
        self.assertEqual(dashboard.lbl_start_time.cget("text"), sess_start)
        self.assertEqual(dashboard.lbl_end_time.cget("text"), log_ended['end_time'])
        self.assertEqual(dashboard.lbl_work_time_val.cget("text"), log_ended['total_work_time'])
        
        # Clicking END TIME again shows message and doesn't crash or update
        dashboard.click_end_time()
        
        print("\nALL MAIN TEACHER DASHBOARD TESTS PASSED PERFECTLY!")

if __name__ == '__main__':
    unittest.main()
