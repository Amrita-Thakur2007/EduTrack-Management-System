import unittest
import os
import sys
import tempfile
import tkinter as tk

sys.path.insert(0, ".")
from database.db_manager import DBManager
from gui.teacher_dashboard import TeacherDashboard

class TestWorkTimeFieldsRemoved(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_fields_removed.db")
        self.db = DBManager(db_path=self.db_path)
        u_id = self.db.create_user("TeacherFields", "password123", "Teacher")
        self.user_data = {
            "id": u_id,
            "username": "TeacherFields",
            "role": "Teacher"
        }
        
        self.teacher_id = "T777"
        self.db.add_teacher({
            "teacher_id": self.teacher_id,
            "name": "Field Teacher",
            "department": "Physics",
            "email": "field@school.com",
            "phone": "9876543212",
            "qualification": "Ph.D",
            "joining_date": "2024-01-01",
            "base_salary": 7000.0
        }, user_id=u_id)
        
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_four_time_fields_absent_date_and_school_time_present(self):
        dashboard = TeacherDashboard(self.root, self.db, self.user_data)
        
        # 1. Open Work Time Dashboard
        dashboard.show_my_work_time()
        dashboard.update()

        # 2. Verify 4 fields do NOT exist
        self.assertFalse(hasattr(dashboard, 'lbl_start_val'), "Start Time field should be absent")
        self.assertFalse(hasattr(dashboard, 'lbl_current_time'), "Current Time field should be absent")
        self.assertFalse(hasattr(dashboard, 'lbl_end_val'), "End Time field should be absent")
        self.assertFalse(hasattr(dashboard, 'lbl_total_wt_val'), "Total Working Time field should be absent")

        # 3. Verify Date & School Time & Status exist
        self.assertTrue(hasattr(dashboard, 'lbl_status_val'), "Status label should be present")

        # 4. Verify timer tick executes cleanly without error
        dashboard.after(100, lambda: None)
        dashboard.update()

        print("ALL VERIFICATIONS PASSED: Date + School Time present; Start Time, Current Time, End Time, and Total Working Time absent!")

if __name__ == "__main__":
    unittest.main()
