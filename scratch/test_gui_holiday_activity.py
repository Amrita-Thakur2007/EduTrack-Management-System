import os
import sys
import tempfile
import tkinter as tk
from tkinter import ttk
from unittest.mock import patch

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.db_manager import DBManager
from gui.admin_dashboard import AdminDashboard

def test_gui_holiday_activity_flow():
    print("=== TESTING GUI HOLIDAY & ACTIVITY WORKFLOW ===")
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
        
    root = tk.Tk()
    root.withdraw()
    
    try:
        db = DBManager(db_path)
        user_data = {"id": 1, "username": "admin", "role": "Admin"}
        
        dashboard = AdminDashboard(root, db, user_data)
        dashboard.show_holidays()
        
        # Mock messagebox to avoid modal blocking in headless test
        with patch('tkinter.messagebox.showinfo') as mock_info, \
             patch('tkinter.messagebox.showerror') as mock_err, \
             patch('tkinter.messagebox.showwarning') as mock_warn:
            
            # Test 1: Add Holiday Dialog
            dashboard.add_holiday_dialog()
            
            # Find Add Holiday Toplevel window
            all_toplevels = [w for w in dashboard.winfo_children() + root.winfo_children() if isinstance(w, tk.Toplevel) and w != dashboard]
            assert len(all_toplevels) >= 1, f"Add Holiday dialog window not opened, found {len(all_toplevels)}"
            win = all_toplevels[-1]
            
            # Find entries and text widget inside dialog
            entries = []
            text_widget = None
            
            def find_widgets(parent):
                nonlocal text_widget
                for child in parent.winfo_children():
                    if isinstance(child, ttk.Entry):
                        entries.append(child)
                    elif isinstance(child, tk.Text):
                        text_widget = child
                    find_widgets(child)
                    
            find_widgets(win)
            
            assert len(entries) >= 2, f"Expected at least 2 entries (Name, Date), found {len(entries)}"
            assert text_widget is not None, "Description Text widget not found"
            
            entry_name = entries[0]
            entry_date = entries[1]
            
            # Type into fields as requested in prompt example
            entry_name.delete(0, tk.END)
            entry_name.insert(0, "Independence Day")
            
            entry_date.delete(0, tk.END)
            entry_date.insert(0, "15-08-2026")
            
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", "School will remain closed for Independence Day.")
            
            # Find and click Save Holiday button
            save_btn = None
            for child in win.winfo_children():
                if isinstance(child, ttk.Button) and "Save" in child.cget("text"):
                    save_btn = child
                    break
                    
            assert save_btn is not None, "Save Holiday button not found"
            save_btn.invoke()
            
            # Verify saved holiday in treeview
            holidays_tree_items = dashboard.tree_holidays.get_children()
            assert len(holidays_tree_items) == 1, f"Expected 1 item in treeview, got {len(holidays_tree_items)}"
            vals = dashboard.tree_holidays.item(holidays_tree_items[0])['values']
            print(f"[OK] GUI Saved Holiday Treeview Row: {vals}")
            assert vals[1] == "Independence Day"
            assert vals[2] == "15-08-2026"
            assert vals[3] == "School will remain closed for Independence Day."
            
            # Test 2: Add Activity Dialog
            dashboard.add_activity_dialog()
            all_toplevels_act = [w for w in dashboard.winfo_children() + root.winfo_children() if isinstance(w, tk.Toplevel) and w not in (dashboard, win)]
            assert len(all_toplevels_act) >= 1, "Add Activity dialog window not opened"
            win_act = all_toplevels_act[-1]
            
            entries_act = []
            text_widget_act = None
            
            def find_widgets_act(parent):
                nonlocal text_widget_act
                for child in parent.winfo_children():
                    if isinstance(child, ttk.Entry):
                        entries_act.append(child)
                    elif isinstance(child, tk.Text):
                        text_widget_act = child
                    find_widgets_act(child)
                    
            find_widgets_act(win_act)
            
            assert len(entries_act) >= 2, f"Expected at least 2 entries for activity, found {len(entries_act)}"
            assert text_widget_act is not None, "Activity Description Text widget not found"
            
            entries_act[0].delete(0, tk.END)
            entries_act[0].insert(0, "Independence Day Celebration")
            
            entries_act[1].delete(0, tk.END)
            entries_act[1].insert(0, "15-08-2026")
            
            text_widget_act.delete("1.0", tk.END)
            text_widget_act.insert("1.0", "Students will participate in the Independence Day celebration.")
            
            save_act_btn = None
            for child in win_act.winfo_children():
                if isinstance(child, ttk.Button) and "Save" in child.cget("text"):
                    save_act_btn = child
                    break
                    
            assert save_act_btn is not None, "Save Activity button not found"
            save_act_btn.invoke()
            
            activities_tree_items = dashboard.tree_activities.get_children()
            assert len(activities_tree_items) == 1, f"Expected 1 activity in treeview, got {len(activities_tree_items)}"
            vals_act = dashboard.tree_activities.item(activities_tree_items[0])['values']
            print(f"[OK] GUI Saved Activity Treeview Row: {vals_act}")
            assert vals_act[1] == "Independence Day Celebration"
            assert vals_act[2] == "15-08-2026"
            assert vals_act[3] == "Students will participate in the Independence Day celebration."
            
            print("\n=== ALL GUI HOLIDAY & ACTIVITY WORKFLOW TESTS PASSED PERFECTLY! ===")
        
    finally:
        root.destroy()
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass

if __name__ == "__main__":
    test_gui_holiday_activity_flow()
