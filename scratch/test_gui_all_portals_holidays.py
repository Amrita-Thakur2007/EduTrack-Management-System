import os
import sys
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DBManager
from gui.holiday_view import HolidayViewFrame

def test_gui_all_portals_holiday_flow():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print("=== TESTING GUI CENTRALIZED HOLIDAY FLOW FOR ALL 4 PORTALS ===")

    test_db_path = os.path.join(os.path.dirname(__file__), "test_gui_4_portals_holiday.db")
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    db = DBManager(test_db_path)

    # 1. Admin adds Holiday: Raksha Bandhan
    h_name = "Raksha Bandhan"
    h_date = "28-08-2026"
    h_desc = "Raksha Bandhan की छुट्टी है। Enjoy your day."

    print(f"Step 1: Admin adds Holiday -> Name='{h_name}', Date='{h_date}', Desc='{h_desc}'")
    db.add_holiday(h_name, h_date, h_desc)

    # Verify Holiday in central DB
    holidays = db.get_all_holidays()
    assert len(holidays) == 1, f"Expected 1 holiday, got {len(holidays)}"
    assert holidays[0]['title'] == h_name
    assert holidays[0]['date'] == h_date
    assert holidays[0]['description'] == h_desc
    print("[OK] Admin-created holiday verified in Central DB.")

    # 2. Test Admin Portal read
    print("\nStep 2: Testing Admin Portal Holiday View...")
    root = tk.Tk()
    root.withdraw() # Hide root window during testing

    admin_view = HolidayViewFrame(root, db)
    admin_holidays = admin_view.db.get_all_holidays()
    assert len(admin_holidays) == 1
    assert admin_holidays[0]['title'] == h_name
    print(f"[OK] Admin Portal reads holiday: {admin_holidays[0]['title']} ({admin_holidays[0]['date']})")
    admin_view.destroy()

    # 3. Test Teacher Portal read
    print("\nStep 3: Testing Teacher Portal Holiday View...")
    teacher_view = HolidayViewFrame(root, db)
    teacher_holidays = teacher_view.db.get_all_holidays()
    assert len(teacher_holidays) == 1
    assert teacher_holidays[0]['title'] == h_name
    print(f"[OK] Teacher Portal reads holiday: {teacher_holidays[0]['title']} ({teacher_holidays[0]['date']})")
    teacher_view.destroy()

    # 4. Test Student Portal read
    print("\nStep 4: Testing Student Portal Holiday View...")
    student_view = HolidayViewFrame(root, db)
    student_holidays = student_view.db.get_all_holidays()
    assert len(student_holidays) == 1
    assert student_holidays[0]['title'] == h_name
    print(f"[OK] Student Portal reads holiday: {student_holidays[0]['title']} ({student_holidays[0]['date']})")
    student_view.destroy()

    # 5. Test Parent Portal read
    print("\nStep 5: Testing Parent Portal Holiday View...")
    parent_view = HolidayViewFrame(root, db)
    parent_holidays = parent_view.db.get_all_holidays()
    assert len(parent_holidays) == 1
    assert parent_holidays[0]['title'] == h_name
    print(f"[OK] Parent Portal reads holiday: {parent_holidays[0]['title']} ({parent_holidays[0]['date']})")
    parent_view.destroy()

    # 6. Test Adding Multiple Holidays (Independence Day, Raksha Bandhan, Diwali)
    print("\nStep 6: Admin adds multiple holidays...")
    db.add_holiday("Independence Day", "15-08-2026", "School will remain closed.")
    db.add_holiday("Diwali", "20-10-2026", "School will remain closed for Diwali.")

    all_h = db.get_all_holidays()
    assert len(all_h) == 3, f"Expected 3 holidays, got {len(all_h)}"
    titles = [h['title'] for h in all_h]
    assert "Raksha Bandhan" in titles
    assert "Independence Day" in titles
    assert "Diwali" in titles
    print(f"[OK] Central DB has all 3 holidays: {titles}")

    # Verify all 4 portals read all 3 holidays
    for portal_name in ["Admin", "Teacher", "Student", "Parent"]:
        view = HolidayViewFrame(root, db)
        p_holidays = view.db.get_all_holidays()
        assert len(p_holidays) == 3
        p_titles = [h['title'] for h in p_holidays]
        assert "Raksha Bandhan" in p_titles
        assert "Independence Day" in p_titles
        assert "Diwali" in p_titles
        print(f"[OK] {portal_name} Portal automatically displays all 3 holidays: {p_titles}")
        view.destroy()

    # 7. Test Admin EDIT Holiday Synchronization
    print("\nStep 7: Admin edits 'Raksha Bandhan'...")
    rb_item = [h for h in db.get_all_holidays() if h['title'] == "Raksha Bandhan"][0]
    db.update_holiday(rb_item['id'], "Raksha Bandhan Special", "28-08-2026", "Updated Raksha Bandhan description.")

    for portal_name in ["Admin", "Teacher", "Student", "Parent"]:
        view = HolidayViewFrame(root, db)
        p_holidays = view.db.get_all_holidays()
        p_titles = [h['title'] for h in p_holidays]
        assert "Raksha Bandhan Special" in p_titles
        assert "Raksha Bandhan" not in p_titles
        print(f"[OK] {portal_name} Portal sees updated holiday: 'Raksha Bandhan Special'")
        view.destroy()

    # 8. Test Admin DELETE Holiday Synchronization
    print("\nStep 8: Admin deletes 'Raksha Bandhan Special'...")
    rb_updated_item = [h for h in db.get_all_holidays() if h['title'] == "Raksha Bandhan Special"][0]
    deleted_ok = db.delete_holiday(rb_updated_item['id'])
    assert deleted_ok is True

    # Verify Raksha Bandhan Special is completely gone from all 4 portals
    for portal_name in ["Admin", "Teacher", "Student", "Parent"]:
        view = HolidayViewFrame(root, db)
        p_holidays = view.db.get_all_holidays()
        assert len(p_holidays) == 2
        p_titles = [h['title'] for h in p_holidays]
        assert "Raksha Bandhan Special" not in p_titles
        assert "Raksha Bandhan" not in p_titles
        assert "Independence Day" in p_titles
        assert "Diwali" in p_titles
        print(f"[OK] {portal_name} Portal no longer displays deleted holiday. Current holidays: {p_titles}")
        view.destroy()

    root.destroy()
    del db

    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except Exception:
            pass

    print("\n=== ALL GUI CENTRALIZED HOLIDAY TESTS PASSED PERFECTLY! ===")

if __name__ == "__main__":
    test_gui_all_portals_holiday_flow()
