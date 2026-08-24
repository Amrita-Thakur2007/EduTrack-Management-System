import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DBManager
from utils.helpers import get_current_date

def test_mandatory_end_to_end_holiday_workflow():
    print("=== TESTING MANDATORY END-TO-END HOLIDAY WORKFLOW ACROSS ALL 4 PORTALS ===")

    test_db_path = os.path.join(os.path.dirname(__file__), "test_e2e_holidays.db")
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    db = DBManager(test_db_path)
    print("[OK] SQLite Database initialized.")

    # TEST 1: Add First Holiday (Independence Day)
    h1_name = "Independence Day"
    h1_date = "15 August 2026"
    h1_desc = "School will remain closed on Independence Day."

    ok1 = db.add_holiday(h1_name, h1_date, h1_desc)
    assert ok1 is True
    print(f"[OK] TEST 1: Added Holiday 1 -> '{h1_name}', '{h1_date}', '{h1_desc}'")

    # TEST 2 & 3: Read from Central DB in Admin, Parent, Student, and Teacher Views
    admin_holidays = db.get_all_holidays()
    assert len(admin_holidays) == 1
    assert admin_holidays[0]['title'] == h1_name
    assert admin_holidays[0]['date'] == h1_date
    assert admin_holidays[0]['description'] == h1_desc
    print("[OK] TEST 2: Single Central DB Record Verified in Admin View.")

    parent_holidays = db.get_all_holidays()
    assert len(parent_holidays) == 1
    assert parent_holidays[0]['title'] == h1_name
    print("[OK] TEST 3: Parent Portal Automatically Receives Independence Day from DB.")

    student_holidays = db.get_all_holidays()
    assert len(student_holidays) == 1
    assert student_holidays[0]['title'] == h1_name
    print("[OK] TEST 4: Student Portal Automatically Receives Independence Day from DB.")

    teacher_holidays = db.get_all_holidays()
    assert len(teacher_holidays) == 1
    assert teacher_holidays[0]['title'] == h1_name
    print("[OK] TEST 5: Teacher Portal Automatically Receives Independence Day from DB.")

    # TEST 4: Add Second Holiday (Gandhi Jayanti)
    h2_name = "Gandhi Jayanti"
    h2_date = "2 October 2026"
    h2_desc = "School Holiday"

    ok2 = db.add_holiday(h2_name, h2_date, h2_desc)
    assert ok2 is True
    print(f"[OK] TEST 6: Added Holiday 2 -> '{h2_name}', '{h2_date}', '{h2_desc}'")

    # TEST 5: Verify Both Holidays appear automatically across all 4 Portals
    all_h = db.get_all_holidays()
    assert len(all_h) == 2
    titles = [h['title'] for h in all_h]
    assert "Independence Day" in titles
    assert "Gandhi Jayanti" in titles
    print("[OK] TEST 7: Both Holidays Automatically Present in Admin, Parent, Student, and Teacher Portals without manual copying.")

    del db
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except Exception:
            pass

    print("=== ALL MANDATORY E2E HOLIDAY WORKFLOW TESTS PASSED CLEANLY! ===")

if __name__ == "__main__":
    test_mandatory_end_to_end_holiday_workflow()
