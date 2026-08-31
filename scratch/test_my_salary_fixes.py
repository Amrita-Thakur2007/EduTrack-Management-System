import unittest
import datetime
import os
import sqlite3
from database.db_manager import DatabaseManager
from utils.helpers import parse_datetime_helper, get_current_date

class TestMySalaryFixes(unittest.TestCase):
    def setUp(self):
        self.db_file = "test_salary_fixes.db"
        if os.path.exists(self.db_file):
            try:
                os.remove(self.db_file)
            except PermissionError:
                pass
        self.db = DatabaseManager(self.db_file)
        
        # Insert a test teacher record with joining date August 5, 2026 and monthly salary 30,000
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO teachers (teacher_id, name, department, designation, joining_date, monthly_salary)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("TCH_TEST_01", "Test Teacher", "Science", "Teacher", "2026-08-05", 30000.0))
            
            # Setup a government holiday on August 15, 2026
            cursor.execute("""
                INSERT INTO holidays (title, date, created_at)
                VALUES (?, ?, ?)
            """, ("Independence Day", "2026-08-15", get_current_date()))
            
            conn.commit()

    def tearDown(self):
        # Close any lingering connections
        if hasattr(self, 'db'):
            self.db = None
        # Clean up database file
        if os.path.exists(self.db_file):
            try:
                os.remove(self.db_file)
            except PermissionError:
                pass

    def test_joining_date_and_holidays_and_sundays(self):
        # Simulate date being 2026-08-27
        # We query the salary summary for August 2026
        # Under our rules:
        # Aug 1, 2, 3, 4 (before joining date Aug 5) must be "Not Joined"
        # Aug 15 is a government holiday, must be "Government Holiday - Paid"
        # Sundays after Aug 5 (e.g. Aug 9, 16, 23) must be "Sunday - Paid"
        # Future dates (Aug 28-31) must NOT be generated or present in day_wise_records
        
        # Let's mock datetime.date.today in our test context or use parameter checks.
        # Since our code uses datetime.date.today() to identify the current month/day,
        # we can patch datetime.date.today. But since it's a built-in type, patching is easiest
        # by stubbing datetime.date inside db_manager or modifying the local time context.
        # Alternatively, we can let our code check August 2026 and mock the date today.
        
        # Let's inspect the results returned
        # We will query salary summary. If today is indeed 2026-08-27 (the system local time is set to this in metadata):
        summary = self.db.get_teacher_salary_summary("TCH_TEST_01", month=8, year=2026)
        
        # Day-wise records should only go up to today's day (27th)
        day_wise = summary["day_wise_records"]
        self.assertEqual(len(day_wise), 27)
        
        # Days 1 to 4 should be "Not Joined"
        for i in range(4):
            self.assertEqual(day_wise[i]["attendance"], "Not Joined")
            self.assertEqual(day_wise[i]["start_time"], "--")
            self.assertEqual(day_wise[i]["end_time"], "--")
            self.assertEqual(day_wise[i]["working_time"], "--")
            self.assertEqual(day_wise[i]["late_minutes"], 0)
            
        # Day 15 (Aug 15) must be Government Holiday - Paid
        self.assertEqual(day_wise[14]["attendance"], "Government Holiday - Paid")
        
        # Day 9 (Aug 9) must be Sunday - Paid
        self.assertEqual(day_wise[8]["attendance"], "Sunday - Paid")
        
        # Net salary should have deductions for 4 Not Joined days
        # base_salary = 30000. Daily rate = 30000 / 31 = 967.74
        # not_joined_deduction = 4 * 967.74 = 3870.97
        self.assertAlmostEqual(summary["not_joined_deduction"], 4 * (30000.0 / 31.0), places=2)

    def test_future_month_september(self):
        # September 2026 is in the future.
        # Data must remain empty / return 0 values.
        summary = self.db.get_teacher_salary_summary("TCH_TEST_01", month=9, year=2026)
        self.assertTrue(summary["is_future_month"])
        self.assertEqual(len(summary["day_wise_records"]), 0)
        self.assertEqual(summary["present_days"], 0)
        self.assertEqual(summary["absent_days"], 0)
        self.assertEqual(summary["late_summary_mins"], 0)
        self.assertEqual(summary["total_salary"], 0.0)

    def test_logins_during_and_outside_school_hours(self):
        # TEST 1: On-time login at 07:30 AM on Aug 5
        # TEST 2: 5 minutes late login at 07:35 AM on Aug 6
        # TEST 3: 30 minutes late login at 08:00 AM on Aug 7
        # TEST 4: School time over login at 04:25 PM on Aug 8
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # Aug 5 check-in (On Time)
            cursor.execute("""
                INSERT INTO teacher_work_logs (teacher_id, date, start_time, end_time, working_hours, total_work_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("TCH_TEST_01", "2026-08-05", "07:30:00 AM", "12:30:00 PM", 5.0, "05:00:00"))
            cursor.execute("INSERT INTO teacher_attendance (teacher_id, date, time, status) VALUES (?, ?, ?, ?)",
                           ("TCH_TEST_01", "2026-08-05", "07:30:00 AM", "Present"))
            
            # Aug 6 check-in (5 mins late)
            cursor.execute("""
                INSERT INTO teacher_work_logs (teacher_id, date, start_time, end_time, working_hours, total_work_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("TCH_TEST_01", "2026-08-06", "07:35:00 AM", "12:30:00 PM", 4.92, "04:55:00"))
            cursor.execute("INSERT INTO teacher_attendance (teacher_id, date, time, status) VALUES (?, ?, ?, ?)",
                           ("TCH_TEST_01", "2026-08-06", "07:35:00 AM", "Present"))
            
            # Aug 7 check-in (30 mins late)
            cursor.execute("""
                INSERT INTO teacher_work_logs (teacher_id, date, start_time, end_time, working_hours, total_work_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("TCH_TEST_01", "2026-08-07", "08:00:00 AM", "12:30:00 PM", 4.5, "04:30:00"))
            cursor.execute("INSERT INTO teacher_attendance (teacher_id, date, time, status) VALUES (?, ?, ?, ?)",
                           ("TCH_TEST_01", "2026-08-07", "08:00:00 AM", "Present"))
            
            # Aug 8 check-in (04:25 PM - School Time Over)
            cursor.execute("""
                INSERT INTO teacher_work_logs (teacher_id, date, start_time, end_time, working_hours, total_work_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("TCH_TEST_01", "2026-08-08", "04:25:00 PM", "05:00:00 PM", 0.58, "00:35:00"))
            cursor.execute("INSERT INTO teacher_attendance (teacher_id, date, time, status) VALUES (?, ?, ?, ?)",
                           ("TCH_TEST_01", "2026-08-08", "04:25:00 PM", "Present"))
                           
            conn.commit()
            
        summary = self.db.get_teacher_salary_summary("TCH_TEST_01", month=8, year=2026)
        day_wise = summary["day_wise_records"]
        
        # Verify Day 5 (Aug 5) is Present, 0 late minutes
        self.assertEqual(day_wise[4]["attendance"], "Present")
        self.assertEqual(day_wise[4]["late_minutes"], 0)
        self.assertEqual(day_wise[4]["working_time"], "05:00:00")
        
        # Verify Day 6 (Aug 6) is Present, 5 late minutes
        self.assertEqual(day_wise[5]["attendance"], "Present")
        self.assertEqual(day_wise[5]["late_minutes"], 5)
        self.assertEqual(day_wise[5]["working_time"], "04:55:00")
        
        # Verify Day 7 (Aug 7) is Present, 30 late minutes
        self.assertEqual(day_wise[6]["attendance"], "Present")
        self.assertEqual(day_wise[6]["late_minutes"], 30)
        self.assertEqual(day_wise[6]["working_time"], "04:30:00")
        
        # Verify Day 8 (Aug 8) is School Time Over - Not Included, 0 late minutes, working time "--"
        self.assertEqual(day_wise[7]["attendance"], "School Time Over - Not Included")
        self.assertEqual(day_wise[7]["late_minutes"], 0)
        self.assertEqual(day_wise[7]["working_time"], "--")
        
        # Verify total late minutes accumulated = 35 minutes
        self.assertEqual(summary["late_summary_mins"], 35)
        
        # Verify working minutes/hours total:
        # Aug 5 = 5 hours (18000s)
        # Aug 6 = 4h 55m (17700s)
        # Aug 7 = 4h 30m (16200s)
        # Total = 14h 25m = 865 minutes
        # Overtime must be 0.0
        self.assertEqual(summary["total_working_minutes"], 865)
        self.assertEqual(summary["overtime_hours"], 0.0)
        self.assertEqual(summary["overtime_amount"], 0.0)

if __name__ == '__main__':
    unittest.main()
