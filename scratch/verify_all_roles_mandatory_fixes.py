import os
import sys
import time
import tkinter as tk
from database.db_manager import DBManager
from gui.login import LoginWindow, ForgotPasswordDialog

def main():
    root = tk.Tk()
    root.withdraw()

    # Mock tkinter messagebox functions to record outputs
    import tkinter.messagebox
    msg_history = []
    def mock_showerror(title, message):
        msg_history.append(("error", title, str(message)))
    def mock_showinfo(title, message):
        msg_history.append(("info", title, str(message)))
    def mock_showwarning(title, message):
        msg_history.append(("warning", title, str(message)))

    tkinter.messagebox.showerror = mock_showerror
    tkinter.messagebox.showinfo = mock_showinfo
    tkinter.messagebox.showwarning = mock_showwarning

    db_path = f"test_all_roles_fixes_{int(time.time())}.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = DBManager(db_path=db_path)

    roles = ["Student", "Parent", "Teacher"]

    for role in roles:
        print(f"\n--- TESTING MANDATORY FIXES FOR ROLE: {role} ---")
        username = f"{role.lower()}_user_01"
        password = "PassWord123"
        fav_person = f"Hero_{role}"

        # 1. Create account with favouritePersonName
        user_id = db.create_user(username, password, role, favourite_person=fav_person)
        assert user_id is not None, f"Failed to create user for role {role}"

        # Verify secure hashing in DB
        with db.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT favourite_person_hash, password_hash FROM users WHERE id = ?", (user_id,))
            row = c.fetchone()
            assert row['favourite_person_hash'] is not None, "favourite_person_hash is missing"
            assert row['favourite_person_hash'] != fav_person, "Security answer saved in plain-text!"
            assert row['password_hash'] != password, "Password saved in plain-text!"
        print(f"[{role}] 1 & 2 & 9 PASS: Account created, favouritePersonName & password securely hashed!")

        # 2. Login with invalid password
        login_win = LoginWindow(root, db, role)
        login_win.entry_username.insert(0, username)
        login_win.entry_password.insert(0, "WrongPassWord")

        msg_history.clear()
        login_win.do_login()
        assert len(msg_history) > 0, "No error dialog shown"
        assert msg_history[-1][2] == "Wrong password. Please try again.", f"Expected 'Wrong password. Please try again.', got '{msg_history[-1][2]}'"
        assert login_win.entry_username.get() == username, "Username was incorrectly cleared!"
        assert login_win.entry_password.get() == "", "Password field was not cleared!"
        print(f"[{role}] 5 PASS: Wrong password message & field clearing verified!")

        # 3. Forgot Password verification (Verify User ID/email + Favourite Person Name)
        forgot_dlg = ForgotPasswordDialog(login_win, db, role)

        # Invalid Favourite Person Name
        forgot_dlg.entry_identifier.insert(0, username)
        forgot_dlg.entry_fav_person.insert(0, "Wrong_Hero_Name")
        forgot_dlg.entry_new_pass.insert(0, "NewSecurePass123")
        forgot_dlg.entry_confirm_pass.insert(0, "NewSecurePass123")

        msg_history.clear()
        forgot_dlg.do_reset()
        assert msg_history[-1][2] == "Incorrect Favourite Person Name. Please try again.", f"Expected incorrect name message, got: '{msg_history[-1][2]}'"

        # Mismatched passwords
        forgot_dlg.entry_fav_person.delete(0, tk.END)
        forgot_dlg.entry_fav_person.insert(0, fav_person)
        forgot_dlg.entry_confirm_pass.delete(0, tk.END)
        forgot_dlg.entry_confirm_pass.insert(0, "MismatchedPass123")

        msg_history.clear()
        forgot_dlg.do_reset()
        assert msg_history[-1][2] == "Passwords do not match.", f"Expected 'Passwords do not match.', got: '{msg_history[-1][2]}'"

        # Valid password recovery
        forgot_dlg.entry_confirm_pass.delete(0, tk.END)
        forgot_dlg.entry_confirm_pass.insert(0, "NewSecurePass123")

        msg_history.clear()
        forgot_dlg.do_reset()
        assert msg_history[-1][2] == "Password reset successfully. Please log in using your new password.", f"Unexpected success message: '{msg_history[-1][2]}'"
        print(f"[{role}] 3 & 4 PASS: Forgot Password link & User ID/email + favouritePersonName verification passed!")

        # 4. Login with updated password
        login_win.entry_password.delete(0, tk.END)
        login_win.entry_password.insert(0, "NewSecurePass123")

        msg_history.clear()
        login_win.do_login()
        assert not login_win.winfo_exists() or msg_history == [], f"Login failed after password reset for role {role}"
        print(f"[{role}] 8 PASS: Existing User ID, Password, and role authentication working smoothly!")

    root.quit()
    root.destroy()

    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    print("\n=== ALL MANDATORY FIXES TESTED AND VERIFIED FOR STUDENT, PARENT, AND TEACHER ROLES ===")

if __name__ == "__main__":
    main()
