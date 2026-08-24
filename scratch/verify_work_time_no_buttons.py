import unittest
import os
import sys
import tempfile
import tkinter as tk

sys.path.insert(0, ".")
from database.db_manager import DBManager
from gui.teacher_dashboard import TeacherDashboard

class TestWorkTimeNoButtons(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_no_buttons.db")
        self.db = DBManager(db_path=self.db_path)
        u_id = self.db.create_user("TeacherUser", "password123", "Teacher")
        self.user_data = {
            "id": u_id,
            "username": "TeacherUser",
            "role": "Teacher"
        }
        
        self.teacher_id = "T999"
        self.db.add_teacher({
            "teacher_id": self.teacher_id,
            "name": "Test Teacher",
            "department": "Science",
            "email": "teacher@school.com",
            "phone": "9876543210",
            "qualification": "M.Sc",
            "joining_date": "2024-01-01",
            "base_salary": 5000.0
        }, user_id=u_id)
        
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_work_time_page_opens_without_start_end_buttons(self):
        dashboard = TeacherDashboard(self.root, self.db, self.user_data)
        
        # 1. Open Work Time page
        dashboard.show_my_work_time()
        dashboard.update()

        # 2. Verify btn_start and btn_end attributes NO LONGER exist on dashboard
        self.assertFalse(hasattr(dashboard, 'btn_start'), "btn_start should not exist")
        self.assertFalse(hasattr(dashboard, 'btn_end'), "btn_end should not exist")

        # 3. Verify handlers NO LONGER exist
        self.assertFalse(hasattr(dashboard, 'start_work'), "start_work should not exist")
        self.assertFalse(hasattr(dashboard, 'start_my_work_session'), "start_my_work_session should not exist")
        self.assertFalse(hasattr(dashboard, 'end_work'), "end_work should not exist")
        self.assertFalse(hasattr(dashboard, 'end_my_work_session'), "end_my_work_session should not exist")

        # 4. Verify Work Time labels still render normally
        self.assertTrue(hasattr(dashboard, 'lbl_current_time'), "Digital clock should exist")
        self.assertTrue(hasattr(dashboard, 'lbl_start_val'), "Start value label should exist")
        self.assertTrue(hasattr(dashboard, 'lbl_end_val'), "End value label should exist")
        self.assertTrue(hasattr(dashboard, 'lbl_total_wt_val'), "Total work time label should exist")
        self.assertTrue(hasattr(dashboard, 'lbl_status_val'), "Status label should exist")

        # 5. Verify label contents render without errors
        self.assertNotEqual(dashboard.lbl_current_time.cget("text"), "")
        self.assertEqual(dashboard.lbl_start_val.cget("text"), "--")
        self.assertEqual(dashboard.lbl_end_val.cget("text"), "--")
        self.assertEqual(dashboard.lbl_total_wt_val.cget("text"), "00:00:00")
        
        print("ALL CHECKS PASSED: Work Time page opens normally without Start or End buttons!")

if __name__ == "__main__":
    unittest.main()
