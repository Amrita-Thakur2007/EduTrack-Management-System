import unittest
import os
import sys
import tempfile
import tkinter as tk

sys.path.insert(0, ".")
from database.db_manager import DBManager
from gui.teacher_dashboard import TeacherDashboard

class TestManualWorkTimeFields(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_manual_fields.db")
        self.db = DBManager(db_path=self.db_path)
        u_id = self.db.create_user("ManualTeacher", "password123", "Teacher")
        self.user_data = {
            "id": u_id,
            "username": "ManualTeacher",
            "role": "Teacher"
        }
        
        self.teacher_id = "T555"
        self.db.add_teacher({
            "teacher_id": self.teacher_id,
            "name": "Manual Input Teacher",
            "department": "Chemistry",
            "email": "manual@school.com",
            "phone": "9876543219",
            "qualification": "M.Sc",
            "joining_date": "2024-01-01",
            "base_salary": 4800.0
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

    def test_manual_input_fields_and_persistence(self):
        self.dashboard = TeacherDashboard(self.root, self.db, self.user_data)
        self.dashboard.show_my_work_time()
        self.dashboard.update()

        # 1. Verify Entry fields exist
        self.assertTrue(hasattr(self.dashboard, 'ent_start_time'), "ent_start_time Entry field must exist.")
        self.assertTrue(hasattr(self.dashboard, 'ent_end_time'), "ent_end_time Entry field must exist.")

        # 2. Verify automatic timer/buttons/status/clock elements are ABSENT
        self.assertFalse(hasattr(self.dashboard, 'btn_start'), "START button must NOT exist.")
        self.assertFalse(hasattr(self.dashboard, 'btn_end'), "END button must NOT exist.")
        self.assertFalse(hasattr(self.dashboard, 'lbl_current_time'), "Current Time field must NOT exist.")
        self.assertFalse(hasattr(self.dashboard, 'lbl_total_wt_val'), "Total Working Time field must NOT exist.")
        self.assertFalse(hasattr(self.dashboard, 'lbl_status_val'), "Status field must NOT exist.")

        # 3. Enter manual Start Time and End Time
        self.dashboard.ent_start_time.delete(0, tk.END)
        self.dashboard.ent_start_time.insert(0, "07:30 AM")

        self.dashboard.ent_end_time.delete(0, tk.END)
        self.dashboard.ent_end_time.insert(0, "12:30 PM")

        # Mock messagebox
        from unittest.mock import patch
        with patch('tkinter.messagebox.showinfo'):
            self.dashboard.save_manual_work_time()
            self.dashboard.update()

        # 4. Verify persisted values in database
        today = self.db.get_teacher_work_log(self.teacher_id, "2026-08-24")
        from utils.helpers import get_current_date
        today_str = get_current_date()
        w_log = self.db.get_teacher_work_log(self.teacher_id, today_str)
        self.assertIsNotNone(w_log)
        self.assertEqual(w_log.get('start_time'), "07:30 AM")
        self.assertEqual(w_log.get('end_time'), "12:30 PM")

        print("MANUAL WORK TIME FIELDS VERIFICATION PASSED PERFECTLY!")

if __name__ == "__main__":
    unittest.main()
