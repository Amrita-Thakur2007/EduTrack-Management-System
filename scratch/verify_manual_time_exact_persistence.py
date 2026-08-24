import unittest
import os
import sys
import tempfile
import tkinter as tk

sys.path.insert(0, ".")
from database.db_manager import DBManager
from gui.teacher_dashboard import TeacherDashboard
from utils.helpers import get_current_date

class TestManualTimeExactPersistence(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_exact_persistence.db")
        self.db = DBManager(db_path=self.db_path)
        u_id = self.db.create_user("ExactTeacher", "password123", "Teacher")
        self.user_data = {
            "id": u_id,
            "username": "ExactTeacher",
            "role": "Teacher"
        }
        
        self.teacher_id = "T_EXACT_001"
        self.db.add_teacher({
            "teacher_id": self.teacher_id,
            "name": "Exact Time Teacher",
            "department": "Mathematics",
            "email": "exact@school.com",
            "phone": "9876543299",
            "qualification": "M.Sc Math",
            "joining_date": "2024-01-01",
            "base_salary": 5200.0
        }, user_id=u_id)

        # Pre-seed database with a record that has an old system timestamp (simulating the bug case)
        today = get_current_date()
        self.db.mark_teacher_attendance(self.teacher_id, today, "07:42:18", "Present")
        self.db.record_teacher_login(self.teacher_id, start_time_override="07:42:18")

        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        try:
            if hasattr(self, 'dashboard') and self.dashboard:
                self.dashboard.destroy()
            self.root.destroy()
        except Exception:
            pass

    def test_exact_manual_time_saved_and_never_overwritten_by_system_clock(self):
        self.dashboard = TeacherDashboard(self.root, self.db, self.user_data)
        self.dashboard.show_my_work_time()
        self.dashboard.update()

        # Step 1: Verify current entry has old timestamp "07:42:18" before editing
        self.assertEqual(self.dashboard.ent_start_time.get(), "07:42:18")

        # Step 2: Teacher manually types "07:30 AM" for Start Time and "12:30 PM" for End Time
        self.dashboard.ent_start_time.delete(0, tk.END)
        self.dashboard.ent_start_time.insert(0, "07:30 AM")

        self.dashboard.ent_end_time.delete(0, tk.END)
        self.dashboard.ent_end_time.insert(0, "12:30 PM")

        # Step 3: Click Save Work Time
        from unittest.mock import patch
        with patch('tkinter.messagebox.showinfo'):
            self.dashboard.save_manual_work_time()
            self.dashboard.update()

        # Step 4: Verify SQLite DB log record contains exact strings "07:30 AM" and "12:30 PM"
        today = get_current_date()
        w_log = self.db.get_teacher_work_log(self.teacher_id, today)
        self.assertIsNotNone(w_log)
        self.assertEqual(w_log.get('start_time'), "07:30 AM", "Start Time in DB must be exactly '07:30 AM'")
        self.assertEqual(w_log.get('end_time'), "12:30 PM", "End Time in DB must be exactly '12:30 PM'")

        # Step 5: Reload / Reopen Work Time Dashboard
        self.dashboard.show_my_work_time()
        self.dashboard.update()

        # Step 6: Verify entry fields present exact values "07:30 AM" and "12:30 PM" without auto-converting
        self.assertEqual(self.dashboard.ent_start_time.get(), "07:30 AM", "Start Time Entry must show '07:30 AM'")
        self.assertEqual(self.dashboard.ent_end_time.get(), "12:30 PM", "End Time Entry must show '12:30 PM'")

        print("\nEXACT MANUAL TIME PERSISTENCE TEST PASSED PERFECTLY!")

if __name__ == "__main__":
    unittest.main()
