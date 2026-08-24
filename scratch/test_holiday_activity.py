import os
import sys
import tempfile

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.db_manager import DBManager

def test_holiday_and_activity_management():
    print("=== TESTING HOLIDAY & ACTIVITY MANAGEMENT ===")
    
    # Use temporary DB file for isolation
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
        
    try:
        db = DBManager(db_path)
        
        # 1. Test Add Holiday (as requested in prompt example)
        h_name = "Independence Day"
        h_date = "15-08-2026"
        h_desc = "School will remain closed for Independence Day."
        
        ok_h = db.add_holiday(h_name, h_date, h_desc)
        assert ok_h == True, "add_holiday failed"
        print(f"[OK] Added Holiday: Name='{h_name}', Date='{h_date}', Desc='{h_desc}'")
        
        # 2. Verify Saved Holiday
        holidays = db.get_all_holidays()
        assert len(holidays) == 1, f"Expected 1 holiday, got {len(holidays)}"
        saved_h = holidays[0]
        assert saved_h['title'] == h_name, f"Expected title '{h_name}', got '{saved_h['title']}'"
        assert saved_h['date'] == h_date, f"Expected date '{h_date}', got '{saved_h['date']}'"
        assert saved_h['description'] == h_desc, f"Expected desc '{h_desc}', got '{saved_h['description']}'"
        print(f"[OK] Verified Saved Holiday in DB: {saved_h['title']} | {saved_h['date']} | {saved_h['description']}")
        
        # 3. Test Add Activity (as requested in prompt example)
        a_name = "Independence Day Celebration"
        a_date = "15-08-2026"
        a_desc = "Students will participate in the Independence Day celebration."
        
        ok_a = db.add_activity(a_name, a_date, a_desc)
        assert ok_a == True, "add_activity failed"
        print(f"[OK] Added Activity: Name='{a_name}', Date='{a_date}', Desc='{a_desc}'")
        
        # 4. Verify Saved Activity
        activities = db.get_all_activities()
        assert len(activities) == 1, f"Expected 1 activity, got {len(activities)}"
        saved_a = activities[0]
        assert saved_a['title'] == a_name, f"Expected title '{a_name}', got '{saved_a['title']}'"
        assert saved_a['date'] == a_date, f"Expected date '{a_date}', got '{saved_a['date']}'"
        assert saved_a['description'] == a_desc, f"Expected desc '{a_desc}', got '{saved_a['description']}'"
        print(f"[OK] Verified Saved Activity in DB: {saved_a['title']} | {saved_a['date']} | {saved_a['description']}")
        
        # 5. Test Update Holiday & Activity
        db.update_holiday(saved_h['id'], "Independence Day 2026", "15-08-2026", "Updated holiday desc")
        updated_h = db.get_all_holidays()[0]
        assert updated_h['title'] == "Independence Day 2026"
        assert updated_h['description'] == "Updated holiday desc"
        print(f"[OK] Verified Holiday Update")
        
        db.update_activity(saved_a['id'], "Independence Day Celebration 2026", "15-08-2026", "Updated activity desc")
        updated_a = db.get_all_activities()[0]
        assert updated_a['title'] == "Independence Day Celebration 2026"
        assert updated_a['description'] == "Updated activity desc"
        print(f"[OK] Verified Activity Update")
        
        print("\n=== ALL HOLIDAY & ACTIVITY DB TESTS PASSED CLEANLY! ===")
        
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)

if __name__ == "__main__":
    test_holiday_and_activity_management()
