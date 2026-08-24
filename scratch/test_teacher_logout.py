import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from database.db_manager import DBManager
from gui.teacher_dashboard import TeacherDashboard

class TestTeacherLogout(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.db = MagicMock(spec=DBManager)
        self.user_data = {'id': 1, 'username': 'teacher1', 'role': 'Teacher'}
        self.db.get_teacher_by_user_id.return_value = {
            'teacher_id': 'TCH501',
            'name': 'Dr. Robert Smith',
            'department': 'Computer Science & Engineering'
        }
        self.db.get_teacher_work_log.return_value = {}

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    @patch('gui.teacher_dashboard.messagebox.askyesno')
    @patch('gui.login.LoginWindow')
    def test_on_logout_cancel(self, mock_login_window, mock_askyesno):
        mock_askyesno.return_value = False
        dashboard = TeacherDashboard(self.root, self.db, self.user_data)
        
        # Call logout (user clicks Cancel)
        dashboard.on_logout()
        
        # Verify dashboard is NOT destroyed and LoginWindow is NOT opened
        self.assertTrue(dashboard.winfo_exists())
        self.assertIsNotNone(dashboard.user_data)
        mock_login_window.assert_not_called()
        dashboard.destroy()

    @patch('gui.teacher_dashboard.messagebox.askyesno')
    @patch('gui.login.LoginWindow')
    def test_on_logout_confirm(self, mock_login_window, mock_askyesno):
        mock_askyesno.return_value = True
        dashboard = TeacherDashboard(self.root, self.db, self.user_data)
        
        # Call logout (user clicks Yes)
        dashboard.on_logout()
        
        # Verify session cleared, dashboard destroyed, and LoginWindow launched
        self.assertEqual(dashboard.user_data, None)
        self.assertEqual(dashboard.teacher_id, None)
        mock_login_window.assert_called_once_with(self.root, self.db, "Teacher")

if __name__ == '__main__':
    unittest.main()
