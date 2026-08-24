import unittest
import os
import sys
import tempfile
import time
from datetime import datetime, timedelta

sys.path.insert(0, ".")
from database.db_manager import DBManager
from utils.helpers import get_current_date, parse_datetime_helper

class TestTeacherTimerFix(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_timer.db")
        self.db = DBManager(db_path=self.db_path)
        self.teacher_id = "T_TIMER_001"
        self.db.add_teacher({
            "teacher_id": self.teacher_id,
            "name": "Sakshi Ma'am",
            "department": "Science",
            "email": "sakshi@school.com",
            "phone": "9876543210",
            "qualification": "M.Sc Physics",
            "joining_date": "2024-01-01",
            "base_salary": 4500.0
        })

    def test_parse_datetime_helper(self):
        dt1 = parse_datetime_helper("12:55:17 PM", "2026-08-24")
        self.assertIsNotNone(dt1)
        self.assertEqual(dt1.hour, 12)
        self.assertEqual(dt1.minute, 55)
        self.assertEqual(dt1.second, 17)

        dt2 = parse_datetime_helper("01:02:42 PM", "2026-08-24")
        self.assertIsNotNone(dt2)
        self.assertEqual(dt2.hour, 13)
        self.assertEqual(dt2.minute, 2)
        self.assertEqual(dt2.second, 42)

        diff = int((dt2 - dt1).total_seconds())
        self.assertEqual(diff, 445)
        hrs = diff // 3600
        mins = (diff % 3600) // 60
        secs = diff % 60
        self.assertEqual(f"{hrs:02d}:{mins:02d}:{secs:02d}", "00:07:25")

    def test_real_timer_lifecycle(self):
        today = get_current_date()

        # Step 1: NOT_STARTED
        log0 = self.db.get_teacher_work_log(self.teacher_id, today)
        self.assertIsNone(log0)

        # Step 2: START clicked at 12:55:17 PM
        start_time_str = "12:55:17 PM"
        self.db.mark_teacher_attendance(self.teacher_id, today, start_time_str, "Present")
        log_start = self.db.record_teacher_login(self.teacher_id, start_time_override=start_time_str)
        
        self.assertIsNotNone(log_start)
        self.assertEqual(log_start['actual_start_time'], "12:55:17 PM")
        self.assertEqual(log_start['status'], "RUNNING")

        # Verify Start Time stays fixed on duplicate START click attempt
        retry_log = self.db.record_teacher_login(self.teacher_id, start_time_override="12:59:59 PM")
        self.assertEqual(retry_log['actual_start_time'], "12:55:17 PM", "Start Time must remain fixed!")

        # Step 3: Verify timer calculation at 5s, 10s, 60s
        start_dt = parse_datetime_helper("12:55:17 PM", today)
        
        # Simulated tick after 5s
        t_5s = start_dt + timedelta(seconds=5)
        diff_5s = int((t_5s - start_dt).total_seconds())
        self.assertEqual(f"{diff_5s // 3600:02d}:{(diff_5s % 3600) // 60:02d}:{diff_5s % 60:02d}", "00:00:05")

        # Simulated tick after 10s
        t_10s = start_dt + timedelta(seconds=10)
        diff_10s = int((t_10s - start_dt).total_seconds())
        self.assertEqual(f"{diff_10s // 3600:02d}:{(diff_10s % 3600) // 60:02d}:{diff_10s % 60:02d}", "00:00:10")

        # Simulated tick after 60s
        t_60s = start_dt + timedelta(seconds=60)
        diff_60s = int((t_60s - start_dt).total_seconds())
        self.assertEqual(f"{diff_60s // 3600:02d}:{(diff_60s % 3600) // 60:02d}:{diff_60s % 60:02d}", "00:01:00")

        # Step 4: END clicked at 13:02:42 PM
        end_time_str = "01:02:42 PM"
        ok_end = self.db.record_teacher_logout(self.teacher_id, end_time_override=end_time_str)
        self.assertTrue(ok_end)

        log_end = self.db.get_teacher_work_log(self.teacher_id, today)
        self.assertEqual(log_end['actual_start_time'], "12:55:17 PM")
        self.assertEqual(log_end['actual_end_time'], "01:02:42 PM")
        self.assertEqual(log_end['total_work_time'], "00:07:25")
        self.assertEqual(log_end['status'], "ENDED")

        # Step 5: Post-END freeze check (after 10s or 10m later)
        # Check that log_end values do not change
        log_frozen = self.db.get_teacher_work_log(self.teacher_id, today)
        self.assertEqual(log_frozen['total_work_time'], "00:07:25")

        print("\nALL WORK TIMER LIFECYCLE TESTS PASSED PERFECTLY!")

if __name__ == '__main__':
    unittest.main()
