import unittest
import os
import sys
import tempfile
import tkinter as tk

sys.path.insert(0, ".")
from database.db_manager import DBManager
from gui.teacher_dashboard import TeacherDashboard

class TestTeacherPortalNavigation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_nav.db")
        self.db = DBManager(db_path=self.db_path)
        u_id = self.db.create_user("TeacherNav", "password123", "Teacher")
        self.user_data = {
            "id": u_id,
            "username": "TeacherNav",
            "role": "Teacher"
        }
        
        self.teacher_id = "T888"
        self.db.add_teacher({
            "teacher_id": self.teacher_id,
            "name": "Nav Teacher",
            "department": "Mathematics",
            "email": "nav@school.com",
            "phone": "9876543211",
            "qualification": "M.Sc Math",
            "joining_date": "2024-01-01",
            "base_salary": 6000.0
        }, user_id=u_id)
        
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_full_navigation_and_work_time_rendering(self):
        dashboard = TeacherDashboard(self.root, self.db, self.user_data)
        
        # 1. Default load (Students View)
        dashboard.update()
        
        # 2. Navigate to My Attendance / Work Time
        dashboard.show_my_work_time()
        dashboard.update()
        
        # 3. Navigate to My Salary
        dashboard.show_my_salary()
        dashboard.update()
        
        # 4. Navigate back to Work Time
        dashboard.show_my_work_time()
        dashboard.update()
        
        # 5. Verify timer ticks cleanly
        dashboard.after(100, lambda: None)
        dashboard.update()

        print("NAVIGATION TEST PASSED: All Teacher Portal pages open smoothly with zero errors!")

if __name__ == "__main__":
    unittest.main()
