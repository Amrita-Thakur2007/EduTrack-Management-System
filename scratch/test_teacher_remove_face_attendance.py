import os
import sys
import tkinter as tk
import time
from tkinter import ttk, messagebox

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DBManager
from gui.teacher_dashboard import TeacherDashboard

messagebox.showinfo = lambda *a, **k: None
messagebox.showwarning = lambda *a, **k: None
messagebox.showerror = lambda *a, **k: None

def test_teacher_attendance_view():
    print("=== TESTING TEACHER ATTENDANCE BOOK TIME VIEW ===")
    db_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f"test_tch_face_{int(time.time())}.db")
    if os.path.exists(db_file):
        os.remove(db_file)
    db = DBManager(db_file)
    
    # Create a teacher account
    uid = db.create_user("teacher_test_01", "pass1234", "Teacher", "Person")
    db.add_teacher({
        "teacher_id": "TCH001",
        "name": "Prof. Sharma",
        "phone": "9876543210",
        "email": "teacher@example.com",
        "department": "Computer Science"
    }, uid)
    
    root = tk.Tk()
    root.withdraw()
    
    td = TeacherDashboard(root, db, {"id": uid, "username": "teacher_test_01", "role": "Teacher"})
    
    # Open My Attendance / Work Time
    td.show_my_work_time()
    
    # Verify START TIME button exists and is active
    assert hasattr(td, "btn_start_time"), "Start time button missing on Teacher Dashboard!"
    assert td.btn_start_time.cget("text") == "START TIME", f"Expected 'START TIME', got '{td.btn_start_time.cget('text')}'"
    print("[PASS] START TIME button exists and is active.")
    
    # Verify END TIME button exists
    assert hasattr(td, "btn_end_time"), "End time button missing on Teacher Dashboard!"
    assert td.btn_end_time.cget("text") == "END TIME", f"Expected 'END TIME', got '{td.btn_end_time.cget('text')}'"
    print("[PASS] END TIME button exists and is active.")
    
    # Verify FACE ATTENDANCE button is removed from work time card
    assert not hasattr(td, "btn_face_attendance") or not td.btn_face_attendance.winfo_exists() if hasattr(td, "btn_face_attendance") else True, "Face Attendance button still exists!"
    # Check widgets in content frame to be 100% sure no button with text 'FACE ATTENDANCE' is packed
    all_buttons = []
    def find_buttons(widget):
        for child in widget.winfo_children():
            if isinstance(child, (ttk.Button, tk.Button)):
                try:
                    all_buttons.append(child.cget("text"))
                except Exception:
                    pass
            find_buttons(child)
            
    find_buttons(td.content_frame)
    print("Buttons found in My Attendance / Work Time section:", all_buttons)
    assert "FACE ATTENDANCE" not in all_buttons, "FACE ATTENDANCE button found in My Attendance / Work Time section!"
    assert "START TIME" in all_buttons, "START TIME button not found in My Attendance / Work Time section!"
    assert "END TIME" in all_buttons, "END TIME button not found in My Attendance / Work Time section!"
    
    print("[PASS] FACE ATTENDANCE button is completely removed from Teacher Portal -> My Attendance Book Time!")
    
    # Test Start Time functionality
    td.click_start_time()
    work_log = db.get_teacher_work_log("TCH001")
    assert work_log is not None, "Work log not created on Start Time click"
    start_time = work_log.get("start_time") or work_log.get("actual_start_time")
    assert start_time is not None and str(start_time).strip() != "", "Start time was not recorded in DB"
    print(f"[PASS] Start Time clicked successfully and recorded start time in DB: {start_time}")
    
    try:
        td.destroy()
        root.destroy()
    except Exception:
        pass
        
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass
            
    print("ALL TEACHER ATTENDANCE BOOK TIME TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_teacher_attendance_view()
