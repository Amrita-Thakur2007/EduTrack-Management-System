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

class TestLiveGuiTimer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_gui_live.db")
        self.db = DBManager(db_path=self.db_path)
        
        # Setup teacher user & teacher record
        self.teacher_id = "T_LIVE_001"
        self.db.add_teacher({
            "teacher_id": self.teacher_id,
            "name": "Live Test Teacher",
            "department": "Mathematics",
            "email": "teacher@test.com",
            "phone": "9998887770",
            "qualification": "Ph.D",
            "joining_date": "2024-01-01",
            "base_salary": 5000.0
        })

        # Add user account linked to teacher
        from utils.security import hash_password
        pwd_hash, salt = hash_password("pass123")
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password_hash, salt, role) VALUES ('liveteacher', ?, ?, 'Teacher')", (pwd_hash, salt))
            user_id = cursor.lastrowid
            cursor.execute("UPDATE teachers SET user_id = ? WHERE teacher_id = ?", (user_id, self.teacher_id))
            conn.commit()

        self.user_data = {"id": user_id, "username": "liveteacher", "role": "Teacher"}

        # Create hidden root tk window
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_live_tkinter_start_end_timer_flow(self):
        # Instantiate real TeacherDashboard window
        dashboard = TeacherDashboard(self.root, self.db, self.user_data)
        
        # Navigate to Work Time Dashboard
        dashboard.show_my_work_time()
        self.root.update()

        # Step 1: NOT_STARTED Check
        self.assertEqual(dashboard.lbl_start_val.cget("text"), "--")
        self.assertEqual(dashboard.lbl_end_val.cget("text"), "--")
        self.assertEqual(dashboard.lbl_total_wt_val.cget("text"), "00:00:00")
        self.assertEqual(dashboard.btn_start.cget("state"), tk.NORMAL)
        self.assertEqual(dashboard.btn_end.cget("state"), tk.DISABLED)
        print("STAGE 1 PASSED: NOT_STARTED state verified.")

        # Step 2: Click START button
        start_click_time = datetime.now().strftime("%I:%M:%S %p")
        dashboard.btn_start.invoke()
        self.root.update()

        start_val_after = dashboard.lbl_start_val.cget("text")
        self.assertNotEqual(start_val_after, "--")
        self.assertEqual(dashboard.lbl_end_val.cget("text"), "--")
        self.assertEqual(dashboard.btn_start.cget("state"), tk.DISABLED)
        self.assertEqual(dashboard.btn_end.cget("state"), tk.NORMAL)
        print(f"STAGE 2 PASSED: START clicked. Captured Start Time: '{start_val_after}'")

        # Step 3: Wait 3 seconds in Tkinter loop and verify Total Working Time increases
        for _ in range(30):
            time.sleep(0.1)
            self.root.update()

        wt_3s = dashboard.lbl_total_wt_val.cget("text")
        print(f"Working Time after 3 seconds: '{wt_3s}'")
        self.assertNotEqual(wt_3s, "00:00:00", "Total Working Time MUST increase while session is RUNNING!")

        # Wait another 2 seconds
        for _ in range(20):
            time.sleep(0.1)
            self.root.update()

        wt_5s = dashboard.lbl_total_wt_val.cget("text")
        print(f"Working Time after 5 seconds: '{wt_5s}'")
        self.assertNotEqual(wt_5s, wt_3s, "Total Working Time MUST continuously increase!")

        # Step 4: Click END button
        dashboard.btn_end.invoke()
        self.root.update()

        end_val_after = dashboard.lbl_end_val.cget("text")
        final_wt = dashboard.lbl_total_wt_val.cget("text")
        self.assertNotEqual(end_val_after, "--")
        self.assertEqual(dashboard.btn_start.cget("state"), tk.DISABLED)
        self.assertEqual(dashboard.btn_end.cget("state"), tk.DISABLED)
        print(f"STAGE 3 PASSED: END clicked. Captured End Time: '{end_val_after}', Final Total Working Time: '{final_wt}'")

        # Step 5: Wait 3 seconds post-END and verify Total Working Time is PERMANENTLY FROZEN
        for _ in range(30):
            time.sleep(0.1)
            self.root.update()

        wt_post_end = dashboard.lbl_total_wt_val.cget("text")
        print(f"Working Time post-END after 3 seconds: '{wt_post_end}'")
        self.assertEqual(wt_post_end, final_wt, "Total Working Time MUST remain frozen after END!")

        print("\nALL LIVE TKINTER TIMER FLOW TESTS PASSED PERFECTLY!")

if __name__ == '__main__':
    unittest.main()
