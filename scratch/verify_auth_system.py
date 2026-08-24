import os
import sys
import time
import tkinter as tk
from database.db_manager import DBManager
from gui.login import LoginWindow, ForgotPasswordDialog

def main():
    root = tk.Tk()
    root.withdraw()

    # Mock tkinter messagebox functions for automated testing
    import tkinter.messagebox
    msg_box_history = []
    def mock_showerror(title, message):
        msg_box_history.append(("error", title, message))
    def mock_showinfo(title, message):
        msg_box_history.append(("info", title, message))
    def mock_showwarning(title, message):
        msg_box_history.append(("warning", title, message))

    tkinter.messagebox.showerror = mock_showerror
    tkinter.messagebox.showinfo = mock_showinfo
    tkinter.messagebox.showwarning = mock_showwarning

    db_path = f"test_auth_system_{int(time.time())}.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = DBManager(db_path=db_path)

    # --- STEP 1: Create Student Account with Security Question ---
    user_id = db.create_user("student_test", "oldpass123", "Student", favourite_person="Dr. APJ Abdul Kalam")
    assert user_id is not None, "Failed to create Student user account"

    # Verify security answer is securely hashed in database
    with db.get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT favourite_person_hash FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
        assert row['favourite_person_hash'] is not None, "favourite_person_hash is missing"
        assert row['favourite_person_hash'] != "Dr. APJ Abdul Kalam", "Security answer stored in plain text!"
    print("STEP 1 PASS: Account created with securely hashed Favourite Person Name!")

    # --- STEP 2: Wrong Password & Field Clearing Test ---
    login_win = LoginWindow(root, db, "Student")
    login_win.entry_username.insert(0, "student_test")
    login_win.entry_password.insert(0, "wrongpass")

    msg_box_history.clear()
    login_win.do_login()
    assert len(msg_box_history) > 0, "No message box triggered on wrong password"
    assert msg_box_history[-1][2] == "Wrong password. Please try again.", f"Unexpected msg: {msg_box_history[-1][2]}"
    assert login_win.entry_username.get() == "student_test", "Username field was cleared on failed login!"
    assert login_win.entry_password.get() == "", "Password field was not cleared on failed login!"
    print("STEP 2 PASS: Wrong password error message & password field clearing verified!")

    # --- STEP 3: Repeated Failed Attempt Account Lockout ---
    for i in range(4): # 1 attempt already done, 4 more makes 5 total failed attempts
        login_win.entry_password.insert(0, f"wrong{i}")
        login_win.do_login()

    msg_box_history.clear()
    login_win.entry_password.insert(0, "wrongpass6")
    login_win.do_login()
    assert "Account locked due to 5 consecutive failed login attempts" in msg_box_history[-1][2], f"Expected lockout message, got: {msg_box_history[-1][2]}"
    print("STEP 3 PASS: Account lockout after 5 failed login attempts verified!")

    # --- STEP 4: Forgot Password Dialog Verification ---
    forgot_dlg = ForgotPasswordDialog(login_win, db, "Student")

    # Mismatched passwords check
    forgot_dlg.entry_identifier.insert(0, "student_test")
    forgot_dlg.entry_fav_person.insert(0, "Dr. APJ Abdul Kalam")
    forgot_dlg.entry_new_pass.insert(0, "newpass123")
    forgot_dlg.entry_confirm_pass.insert(0, "differentpass")

    msg_box_history.clear()
    forgot_dlg.do_reset()
    assert msg_box_history[-1][2] == "Passwords do not match.", f"Expected 'Passwords do not match.', got: {msg_box_history[-1][2]}"

    # Incorrect Favourite Person Name check
    forgot_dlg.entry_confirm_pass.delete(0, tk.END)
    forgot_dlg.entry_confirm_pass.insert(0, "newpass123")
    forgot_dlg.entry_fav_person.delete(0, tk.END)
    forgot_dlg.entry_fav_person.insert(0, "Wrong Person Name")

    msg_box_history.clear()
    forgot_dlg.do_reset()
    assert msg_box_history[-1][2] == "Incorrect Favourite Person Name. Please try again.", f"Expected incorrect name message, got: {msg_box_history[-1][2]}"

    # Correct recovery details check
    forgot_dlg.entry_fav_person.delete(0, tk.END)
    forgot_dlg.entry_fav_person.insert(0, "Dr. APJ Abdul Kalam")

    msg_box_history.clear()
    forgot_dlg.do_reset()
    assert msg_box_history[-1][2] == "Password reset successfully. Please log in using your new password.", f"Unexpected success msg: {msg_box_history[-1][2]}"
    print("STEP 4 PASS: Forgot Password recovery flow verified (mismatched password, wrong security answer, and successful reset)!")

    # --- STEP 5: Successful Login with New Password ---
    login_win.entry_password.delete(0, tk.END)
    login_win.entry_password.insert(0, "newpass123")

    msg_box_history.clear()
    login_win.do_login()
    # If login succeeds, win is destroyed
    assert not login_win.winfo_exists() or msg_box_history == [], "Login with new password failed"

    # Verify failed attempts counter was reset in DB
    with db.get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT failed_login_attempts FROM users WHERE id = ?", (user_id,))
        r = c.fetchone()
        assert r['failed_login_attempts'] == 0, f"Expected failed_login_attempts=0, got {r['failed_login_attempts']}"
    print("STEP 5 PASS: Login with new password succeeded and reset failed attempt counter to 0!")

    root.quit()
    root.destroy()

    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    print("\n=== ALL AUTHENTICATION, RECOVERY & SECURITY TESTS PASSED 100% ===")

if __name__ == "__main__":
    main()
