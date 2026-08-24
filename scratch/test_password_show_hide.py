import os
import sys
import time
import tkinter as tk
from tkinter import ttk
from database.db_manager import DBManager
from gui.register import AccountRegistrationWindow
from gui.login import LoginWindow

def run_tests():
    print("=== STARTING PASSWORD SHOW/HIDE TOGGLE VERIFICATION ===")

    db_path = f"scratch/test_sh_{int(time.time())}.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = DBManager(db_path=db_path)

    root = tk.Tk()
    root.withdraw()

    # 1. Test Registration Window Password & Confirm Password Show/Hide
    reg_window = AccountRegistrationWindow(root, db, role="Student")

    pass_entry = reg_window._entries["password"]
    confirm_entry = reg_window._entries["confirm_password"]

    assert pass_entry.cget("show") == "*", "Password field must be hidden/masked with '*' by default!"
    assert confirm_entry.cget("show") == "*", "Confirm Password field must be hidden/masked with '*' by default!"

    # Locate toggle buttons in password entry containers
    pass_container = pass_entry.master
    pass_toggle_btn = None
    for child in pass_container.winfo_children():
        if isinstance(child, ttk.Button):
            pass_toggle_btn = child
            break
    assert pass_toggle_btn is not None, "Password field must have a Show/Hide toggle button!"

    confirm_container = confirm_entry.master
    confirm_toggle_btn = None
    for child in confirm_container.winfo_children():
        if isinstance(child, ttk.Button):
            confirm_toggle_btn = child
            break
    assert confirm_toggle_btn is not None, "Confirm Password field must have a Show/Hide toggle button!"

    # --- TEST PASSWORD FIELD TOGGLE ---
    pass_entry.insert(0, "MySecret123")
    assert pass_entry.cget("show") == "*"
    
    # Click 👁️ Show
    pass_toggle_btn.invoke()
    assert pass_entry.cget("show") == "", "Password field must become visible (show='') when Show is clicked!"
    assert pass_toggle_btn.cget("text") == "🙈 Hide", "Toggle button text must update to '🙈 Hide'!"
    assert pass_entry.get() == "MySecret123", "Typed password content must remain intact!"

    # Click 🙈 Hide
    pass_toggle_btn.invoke()
    assert pass_entry.cget("show") == "*", "Password field must become masked (show='*') when Hide is clicked!"
    assert pass_toggle_btn.cget("text") == "👁️ Show", "Toggle button text must update to '👁️ Show'!"

    print("TEST 1 PASS: Registration Password field Show/Hide toggle verified.")

    # --- TEST CONFIRM PASSWORD FIELD TOGGLE ---
    confirm_entry.insert(0, "MySecret123")
    assert confirm_entry.cget("show") == "*"
    
    # Click 👁️ Show
    confirm_toggle_btn.invoke()
    assert confirm_entry.cget("show") == "", "Confirm Password field must become visible (show='') when Show is clicked!"
    assert confirm_toggle_btn.cget("text") == "🙈 Hide"

    # Click 🙈 Hide
    confirm_toggle_btn.invoke()
    assert confirm_entry.cget("show") == "*", "Confirm Password field must become masked (show='*') when Hide is clicked!"
    assert confirm_toggle_btn.cget("text") == "👁️ Show"

    print("TEST 2 PASS: Registration Confirm Password field Show/Hide toggle verified.")

    reg_window.destroy()

    # --- TEST LOGIN WINDOW PASSWORD SHOW/HIDE TOGGLE ---
    login_win = LoginWindow(root, db, initial_role="Student")
    login_pass_entry = login_win.entry_password

    assert login_pass_entry.cget("show") == "*", "Login Password field must be masked by default!"

    login_pass_container = login_pass_entry.master
    login_toggle_btn = None
    for child in login_pass_container.winfo_children():
        if isinstance(child, ttk.Button):
            login_toggle_btn = child
            break
    assert login_toggle_btn is not None, "Login Password field must have a Show/Hide toggle button!"

    login_pass_entry.insert(0, "LoginPass456")
    
    # Click 👁️ Show
    login_toggle_btn.invoke()
    assert login_pass_entry.cget("show") == "", "Login Password field must become visible when Show is clicked!"
    assert login_toggle_btn.cget("text") == "🙈 Hide"

    # Click 🙈 Hide
    login_toggle_btn.invoke()
    assert login_pass_entry.cget("show") == "*", "Login Password field must become masked when Hide is clicked!"
    assert login_toggle_btn.cget("text") == "👁️ Show"

    print("TEST 3 PASS: Login window Password field Show/Hide toggle verified.")

    login_win.destroy()
    root.quit()
    root.destroy()

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

    print("\n=== ALL PASSWORD SHOW/HIDE TOGGLE VERIFICATIONS PASSED 100% ===")

if __name__ == "__main__":
    run_tests()
