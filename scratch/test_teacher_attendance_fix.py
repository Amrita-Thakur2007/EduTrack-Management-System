import unittest
import os
import sys
import tempfile
from datetime import datetime, timedelta

sys.path.insert(0, ".")
from database.db_manager import DBManager

class TestTeacherAttendanceFix(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_attendance.db")
        self.db = DBManager(db_path=self.db_path)
        # Seed a test teacher
        self.teacher_id = "T999"
        self.db.add_teacher({
            "teacher_id": self.teacher_id,
            "name": "Test Teacher",
            "department": "Mathematics",
            "email": "teacher@test.com",
            "phone": "9999999999",
            "qualification": "M.Sc",
            "joining_date": "2025-01-01",
            "base_salary": 4000.0
        })

    def test_real_login_time_capture(self):
        """TEST 1: Login captures current system time and starts session."""
        log = self.db.record_teacher_login(self.teacher_id)
        self.assertIsNotNone(log)
        self.assertEqual(log['teacher_id'], self.teacher_id)
        self.assertIn('actual_start_time', log)
        print(f"Recorded login start time: {log['actual_start_time']}")

    def test_prevent_multiple_active_sessions(self):
        """TEST 7: Prevent creating multiple active sessions for same teacher on same day."""
        start_1 = "01:00:00 AM"
        log1 = self.db.record_teacher_login(self.teacher_id, start_time_override=start_1)
        self.assertEqual(log1['actual_start_time'], start_1)

        # Attempt second login on same date
        start_2 = "02:00:00 AM"
        log2 = self.db.record_teacher_login(self.teacher_id, start_time_override=start_2)
        # Should keep original start time
        self.assertEqual(log2['actual_start_time'], start_1)

    def test_night_time_worked_time_calculation(self):
        """TEST 5 & 12: Test night-time login (01:00:00 AM) and END (01:25:30 AM)."""
        start_time = "01:00:00 AM"
        end_time = "01:25:30 AM"

        # Record login at 01:00:00 AM
        self.db.record_teacher_login(self.teacher_id, start_time_override=start_time)

        # Record logout at 01:25:30 AM
        res = self.db.record_teacher_logout(self.teacher_id, end_time_override=end_time)
        self.assertTrue(res)

        from utils.helpers import get_current_date
        today = get_current_date()
        final_log = self.db.get_teacher_work_log(self.teacher_id, today)

        self.assertEqual(final_log['actual_start_time'], start_time)
        self.assertEqual(final_log['actual_end_time'], end_time)
        self.assertEqual(final_log['total_work_time'], "00:25:30")
        self.assertNotEqual(final_log['total_work_time'], "07:42:18")
        self.assertEqual(final_log['status'], "Work Session Completed")
        print(f"Night-time test passed: Start={start_time}, End={end_time}, Total={final_log['total_work_time']}")

    def test_restart_safety(self):
        """TEST 10: Application restart safety — completed record remains unchanged."""
        start_time = "09:00:00 AM"
        end_time = "10:30:15 AM"
        self.db.record_teacher_login(self.teacher_id, start_time_override=start_time)
        self.db.record_teacher_logout(self.teacher_id, end_time_override=end_time)

        # Simulate app restart by re-instantiating DBManager
        db2 = DBManager(db_path=self.db_path)
        from utils.helpers import get_current_date
        today = get_current_date()

        log = db2.get_teacher_work_log(self.teacher_id, today)
        self.assertEqual(log['actual_start_time'], start_time)
        self.assertEqual(log['actual_end_time'], end_time)
        self.assertEqual(log['total_work_time'], "01:30:15")
        self.assertEqual(log['status'], "Work Session Completed")

        # Attempting login again after completion should not reset completed log
        new_log = db2.record_teacher_login(self.teacher_id)
        self.assertEqual(new_log['actual_start_time'], start_time)
        self.assertEqual(new_log['actual_end_time'], end_time)

if __name__ == '__main__':
    unittest.main()
