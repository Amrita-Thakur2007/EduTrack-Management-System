import unittest
import os
import sys
import tempfile
import time
import tkinter as tk
from datetime import datetime

sys.path.insert(0, ".")
from database.db_manager import DBManager
from gui.teacher_dashboard import TeacherDashboard

class TestMouseClickVerification(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_mouse_click.db")
        self.db = DBManager(db_path=self.db_path)
        
        # Setup teacher user & teacher record
        self.teacher_id = "T_CLICK_001"
        self.db.add_teacher({
            "teacher_id": self.teacher_id,
            "name": "Click Test Teacher",
            "department": "Physics",
            "email": "click@test.com",
            "phone": "9998887771",
            "qualification": "Ph.D",
            "joining_date": "2024-01-01",
            "base_salary": 5500.0
        })

        # Add user account linked to teacher
        from utils.security import hash_password
        pwd_hash, salt = hash_password("pass123")
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password_hash, salt, role) VALUES ('clickteacher', ?, ?, 'Teacher')", (pwd_hash, salt))
            user_id = cursor.lastrowid
            cursor.execute("UPDATE teachers SET user_id = ? WHERE teacher_id = ?", (user_id, self.teacher_id))
            conn.commit()

        self.user_data = {"id": user_id, "username": "clickteacher", "role": "Teacher"}

        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_real_mouse_click_events(self):
        dashboard = TeacherDashboard(self.root, self.db, self.user_data)
        dashboard.show_my_work_time()
        self.root.update()

        # Step 1: Verify START button is enabled and clickable
        self.assertEqual(str(dashboard.btn_start.cget("state")), str(tk.NORMAL))
        self.assertEqual(str(dashboard.btn_end.cget("state")), str(tk.DISABLED))

        # Step 2: Generate REAL Mouse Click Event <Button-1> on START button
        print("\n--- GENERATING MOUSE CLICK ON START BUTTON ---")
        dashboard.btn_start.event_generate("<Button-1>")
        self.root.update()

        start_val = dashboard.lbl_start_val.cget("text")
        self.assertNotEqual(start_val, "--", "Start time must be populated after clicking START!")
        self.assertEqual(str(dashboard.btn_start.cget("state")), str(tk.DISABLED))
        self.assertEqual(str(dashboard.btn_end.cget("state")), str(tk.NORMAL))

        # Step 3: Wait 3 seconds to let live timer update
        for _ in range(30):
            time.sleep(0.1)
            self.root.update()

        wt = dashboard.lbl_total_wt_val.cget("text")
        self.assertNotEqual(wt, "00:00:00", "Live timer must be running!")
        print(f"Elapsed Work Time after 3 seconds: '{wt}'")

        # Step 4: Generate REAL Mouse Click Event <Button-1> on END button
        print("\n--- GENERATING MOUSE CLICK ON END BUTTON ---")
        dashboard.btn_end.event_generate("<Button-1>")
        self.root.update()

        end_val = dashboard.lbl_end_val.cget("text")
        total_wt = dashboard.lbl_total_wt_val.cget("text")
        self.assertNotEqual(end_val, "--", "End time must be populated after clicking END!")
        self.assertEqual(str(dashboard.btn_start.cget("state")), str(tk.DISABLED))
        self.assertEqual(str(dashboard.btn_end.cget("state")), str(tk.DISABLED))

        # Step 5: Verify Session Saved in Database
        from utils.helpers import get_current_date
        today = get_current_date()
        w_log = self.db.get_teacher_work_log(self.teacher_id, today)
        self.assertIsNotNone(w_log, "Session record must be saved in database!")
        self.assertIsNotNone(w_log.get('actual_start_time'), "Start time must be saved in database!")
        self.assertIsNotNone(w_log.get('actual_end_time'), "End time must be saved in database!")
        self.assertEqual(w_log.get('status'), "ENDED", "Session status must be ENDED in database!")

        print(f"Database Record Verified: Start='{w_log.get('actual_start_time')}', End='{w_log.get('actual_end_time')}', Total='{w_log.get('total_work_time')}'")
        print("\nSUCCESS: REAL MOUSE CLICK VERIFICATION COMPLETE!")

if __name__ == '__main__':
    unittest.main()
