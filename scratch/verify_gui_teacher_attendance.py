import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Mock messagebox popups for automated non-blocking execution
messagebox.showinfo = lambda title, message: print(f"[INFOBOX] {title}: {message}")
messagebox.showwarning = lambda title, message: print(f"[WARNBOX] {title}: {message}")
messagebox.showerror = lambda title, message: print(f"[ERRBOX] {title}: {message}")

from database.db_manager import DBManager
from gui.teacher_dashboard import TeacherDashboard

def test_gui_teacher_dashboard_attendance():
    db_path = os.path.join(PROJECT_ROOT, "data", "database.db")
    db = DBManager(db_path=db_path)

    root = tk.Tk()
    root.withdraw() # Keep root window hidden for automated testing

    user_data = {
        'id': 1,
        'username': 'teacher1',
        'role': 'Teacher'
    }

    dashboard = TeacherDashboard(root, db, user_data)
    dashboard.show_students() # Navigate to My Class Students

    # Verify Treeview columns and headings
    cols = dashboard.tree['columns']
    print(f"School columns in Treeview: {cols}")
    assert "school_name" in cols, "school_name column missing!"
    assert "attendance" in cols, "attendance column missing!"

    # Search for Amrita
    dashboard.entry_search.delete(0, tk.END)
    dashboard.entry_search.insert(0, "Amrita")
    dashboard.load_students_table()

    items = dashboard.tree.get_children()
    assert len(items) > 0, "Amrita row not rendered in Treeview!"
    
    amrita_vals = dashboard.tree.item(items[0])['values']
    print(f"Amrita Treeview values: {amrita_vals}")
    sid = str(amrita_vals[0]).strip()
    sname = str(amrita_vals[1]).strip()
    sch_name = str(amrita_vals[2]).strip()
    att_val = str(amrita_vals[5]).strip()

    assert sname.lower() == 'amrita', f"Expected Amrita, got {sname}"
    assert sch_name != "", "School Name in Treeview must NOT be blank!"
    print(f"Amrita in GUI: ID={sid}, Name={sname}, School Name={sch_name}, Attendance={att_val}")

    # Select Amrita in Treeview
    dashboard.tree.selection_set(items[0])
    dashboard._on_student_select()

    # Mark Present via quick button
    dashboard.mark_quick_attendance("Present")
    amrita_vals_after_pres = dashboard.tree.item(dashboard.tree.get_children()[0])['values']
    assert str(amrita_vals_after_pres[5]).strip() == "Present", f"Expected Present after click, got {amrita_vals_after_pres[5]}"
    print("GUI Step 1 Passed: Marked Amrita Present via GUI control.")

    # Mark Absent via quick button (verifying UPSERT UI refresh)
    dashboard.tree.selection_set(dashboard.tree.get_children()[0])
    dashboard.mark_quick_attendance("Absent")
    amrita_vals_after_abs = dashboard.tree.item(dashboard.tree.get_children()[0])['values']
    assert str(amrita_vals_after_abs[5]).strip() == "Absent", f"Expected Absent after click, got {amrita_vals_after_abs[5]}"
    print("GUI Step 2 Passed: Updated Amrita to Absent via GUI control.")

    # Switch category to College
    dashboard.combo_category.set("College")
    dashboard.entry_search.delete(0, tk.END)
    dashboard.load_students_table()

    college_items = dashboard.tree.get_children()
    assert len(college_items) > 0, "No College student rows rendered!"
    c_vals = dashboard.tree.item(college_items[0])['values']
    print(f"College student Treeview values: {c_vals}")
    c_school_name = str(c_vals[3]).strip()
    c_att_val = str(c_vals[6]).strip()
    assert c_school_name != "", "College Name in Treeview must NOT be blank!"
    print(f"College student in GUI: Name={c_vals[2]}, College Name={c_school_name}, Attendance={c_att_val}")

    # Select College student and mark Present
    dashboard.tree.selection_set(college_items[0])
    dashboard.mark_quick_attendance("Present")

    root.destroy()
    print("\nALL GUI TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_gui_teacher_dashboard_attendance()
