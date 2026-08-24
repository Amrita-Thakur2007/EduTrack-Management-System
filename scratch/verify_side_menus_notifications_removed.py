import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Mock messagebox popups for non-blocking execution
messagebox.showinfo = lambda title, message: print(f"[INFOBOX] {title}: {message}")
messagebox.showwarning = lambda title, message: print(f"[WARNBOX] {title}: {message}")
messagebox.showerror = lambda title, message: print(f"[ERRBOX] {title}: {message}")

from database.db_manager import DBManager
from gui.admin_dashboard import AdminDashboard
from gui.student_dashboard import StudentDashboard
from gui.parent_dashboard import ParentDashboard

def test_side_menu_notifications_removal():
    db_path = os.path.join(PROJECT_ROOT, "data", "database.db")
    db = DBManager(db_path=db_path)

    root = tk.Tk()
    root.withdraw()

    # 1. Test Admin Dashboard Side Menu
    admin_user = {'id': 1, 'username': 'admin', 'role': 'Admin'}
    admin_dash = AdminDashboard(root, db, admin_user)
    
    admin_sidebar = None
    for child in admin_dash.winfo_children():
        if isinstance(child, ttk.Frame) and "Sidebar.TFrame" in str(child.cget("style")):
            admin_sidebar = child
            break

    assert admin_sidebar is not None, "Admin sidebar not found!"
    admin_menu_texts = [btn.cget("text") for btn in admin_sidebar.winfo_children() if isinstance(btn, ttk.Button)]
    clean_admin_texts = [text.encode('ascii', 'ignore').decode('ascii').strip() for text in admin_menu_texts]
    print(f"Admin Side Menu Items: {clean_admin_texts}")

    for text in admin_menu_texts:
        assert "notification" not in text.lower(), f"Notifications item '{text}' still present in Admin Side Menu!"

    expected_admin = ["Dashboard Overview", "Student Management", "Teacher Management", "Attendance Records", "Marks & Evaluation", "Settings", "Logout"]
    for exp in expected_admin:
        assert any(exp in text for text in admin_menu_texts), f"Expected menu item '{exp}' missing from Admin Side Menu!"

    print("Step 1 Passed: Admin Side Menu verified - Notifications removed completely, all other menu items intact.")

    # 2. Test Student Dashboard Side Menu
    student_user = {'id': 20, 'username': 'Amrita', 'role': 'Student'}
    student_dash = StudentDashboard(root, db, student_user)
    
    student_sidebar = None
    for child in student_dash.winfo_children():
        if isinstance(child, ttk.Frame) and "Sidebar.TFrame" in str(child.cget("style")):
            student_sidebar = child
            break

    assert student_sidebar is not None, "Student sidebar not found!"
    student_menu_texts = [btn.cget("text") for btn in student_sidebar.winfo_children() if isinstance(btn, ttk.Button)]
    clean_student_texts = [text.encode('ascii', 'ignore').decode('ascii').strip() for text in student_menu_texts]
    print(f"Student Side Menu Items: {clean_student_texts}")

    for text in student_menu_texts:
        assert "notification" not in text.lower(), f"Notifications item '{text}' still present in Student Side Menu!"

    expected_student = ["My Profile", "Attendance History", "Marks & Grade", "Settings", "Logout"]
    for exp in expected_student:
        assert any(exp in text for text in student_menu_texts), f"Expected menu item '{exp}' missing from Student Side Menu!"

    print("Step 2 Passed: Student Side Menu verified - Notifications removed completely, all other menu items intact.")

    # 3. Test Parent Dashboard Side Menu
    parent_user = {'id': 22, 'username': 'Kamodthakur', 'role': 'Parent'}
    parent_dash = ParentDashboard(root, db, parent_user)

    parent_sidebar = None
    for child in parent_dash.winfo_children():
        if isinstance(child, ttk.Frame) and "Sidebar.TFrame" in str(child.cget("style")):
            parent_sidebar = child
            break

    assert parent_sidebar is not None, "Parent sidebar not found!"
    parent_menu_texts = [btn.cget("text") for btn in parent_sidebar.winfo_children() if isinstance(btn, ttk.Button)]
    clean_parent_texts = [text.encode('ascii', 'ignore').decode('ascii').strip() for text in parent_menu_texts]
    print(f"Parent Side Menu Items: {clean_parent_texts}")

    for text in parent_menu_texts:
        assert "notification" not in text.lower(), f"Notifications item '{text}' still present in Parent Side Menu!"

    expected_parent = ["My Profile", "Child Profile", "Attendance History", "Academic Marks", "Settings", "Logout"]
    for exp in expected_parent:
        assert any(exp in text for text in parent_menu_texts), f"Expected menu item '{exp}' missing from Parent Side Menu!"

    print("Step 3 Passed: Parent Side Menu verified - Notifications removed completely, all other menu items intact.")

    root.destroy()
    print("\nALL THREE PORTAL SIDE MENU VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_side_menu_notifications_removal()
