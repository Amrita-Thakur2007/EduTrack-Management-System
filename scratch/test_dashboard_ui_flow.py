import unittest
import os
import sys
import tempfile
from datetime import datetime, timedelta

sys.path.insert(0, ".")
from database.db_manager import DBManager
from utils.helpers import get_current_date

class TestDashboardUIFlow(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_ui.db")
        self.db = DBManager(db_path=self.db_path)
        self.teacher_id = "T_TEST_1"
        self.db.add_teacher({
            "teacher_id": self.teacher_id,
            "name": "Sakshi Teacher",
            "department": "Science",
            "email": "sakshi@test.com",
            "phone": "9876543210",
            "qualification": "M.Sc",
            "joining_date": "2025-01-01",
            "base_salary": 4000.0
        })

    def test_full_work_time_dashboard_lifecycle(self):
        today = get_current_date()

        # TEST 1: Before Start
        log_before = self.db.get_teacher_work_log(self.teacher_id, today)
        self.assertIsNone(log_before, "Work log should not exist before START")

        # TEST 2: Start session (real current system time captured)
        t_start_sys = datetime.now().strftime("%I:%M:%S %p")
        self.db.mark_teacher_attendance(self.teacher_id, today, t_start_sys, "Present")
        log_started = self.db.record_teacher_login(self.teacher_id, start_time_override=t_start_sys)

        self.assertIsNotNone(log_started)
        self.assertEqual(log_started['actual_start_time'], t_start_sys)
        self.assertIsNone(log_started.get('actual_end_time'))

        # TEST 3: Multiple clicks on START should not overwrite active session
        t_start_fake = "11:59:59 PM"
        log_retry = self.db.record_teacher_login(self.teacher_id, start_time_override=t_start_fake)
        self.assertEqual(log_retry['actual_start_time'], t_start_sys, "START must not reset active start time")

        # TEST 4: End session (real current system time captured)
        t_end_sys = (datetime.now() + timedelta(minutes=45, seconds=12)).strftime("%I:%M:%S %p")
        ok_end = self.db.record_teacher_logout(self.teacher_id, end_time_override=t_end_sys)
        self.assertTrue(ok_end)

        log_ended = self.db.get_teacher_work_log(self.teacher_id, today)
        self.assertEqual(log_ended['actual_start_time'], t_start_sys)
        self.assertEqual(log_ended['actual_end_time'], t_end_sys)
        self.assertEqual(log_ended['total_work_time'], "00:45:12")

        # TEST 6: Application restart persistence
        db_restarted = DBManager(db_path=self.db_path)
        log_persisted = db_restarted.get_teacher_work_log(self.teacher_id, today)
        self.assertIsNotNone(log_persisted)
        self.assertEqual(log_persisted['actual_start_time'], t_start_sys)
        self.assertEqual(log_persisted['actual_end_time'], t_end_sys)
        self.assertEqual(log_persisted['total_work_time'], "00:45:12")
        print("ALL 6 TEST CASES PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    unittest.main()
