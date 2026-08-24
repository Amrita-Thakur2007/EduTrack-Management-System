import os
import sys
import unittest

# Ensure workspace root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DBManager

class TestProfileAndMarksSync(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_sync_and_profile.db")
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
        cls.db = DBManager(cls.db_path)

        # 1. Setup test user accounts and records
        with cls.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password_hash, salt, role) VALUES ('t_user', 'hash', 'salt', 'Teacher')")
            cls.t_user_id = cursor.lastrowid
            cursor.execute("INSERT INTO users (username, password_hash, salt, role) VALUES ('s_user', 'hash', 'salt', 'Student')")
            cls.s_user_id = cursor.lastrowid
            cursor.execute("INSERT INTO users (username, password_hash, salt, role) VALUES ('p_user', 'hash', 'salt', 'Parent')")
            cls.p_user_id = cursor.lastrowid
            conn.commit()

        # Teacher record
        cls.db.add_teacher({
            'teacher_id': 'T1001',
            'name': 'Original Teacher',
            'phone': '9876543210',
            'email': 'teacher@school.com',
            'address': 'Original Address',
            'department': 'Science',
            'designation': 'Senior Teacher',
            'joining_date': '2025-01-01'
        }, user_id=cls.t_user_id)

        # Student record
        cls.db.add_student({
            'student_id': 'S1001',
            'name': 'John Doe',
            'father_name': 'Parent Doe',
            'mother_name': 'Jane Doe',
            'dob': '2008-05-15',
            'gender': 'Male',
            'phone': '9123456789',
            'email': 'john@student.com',
            'address': 'Student Home Address',
            'course': 'Computer Science',
            'department': 'CS Dept',
            'current_class': 'Class 10',
            'section': 'A',
            'roll_number': '101',
            'parent_id_code': 'PAR1001'
        }, user_id=cls.s_user_id)

        # Parent record
        cls.db.add_parent({
            'parent_id_code': 'PAR1001',
            'student_id': 'S1001',
            'name': 'Parent Doe',
            'relationship': 'Father',
            'phone': '9988776655',
            'email': 'parent@home.com',
            'occupation': 'Engineer',
            'emergency_contact': '9988776655',
            'address': 'Parent House Address'
        }, user_id=cls.p_user_id)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.db_path):
            try:
                os.remove(cls.db_path)
            except Exception:
                pass

    def test_01_teacher_profile_update(self):
        t = self.db.get_teacher_by_user_id(self.t_user_id)
        self.assertIsNotNone(t)
        self.assertEqual(t['name'], 'Original Teacher')

        # Perform UPDATE
        update_data = {
            'name': 'Updated Dr. Teacher',
            'phone': '9876543211',
            'email': 'updated_teacher@school.com',
            'address': 'Updated Workstation Address',
            'department': t.get('department', ''),
            'designation': t.get('designation', ''),
            'joining_date': t.get('joining_date', '')
        }
        res = self.db.update_teacher('T1001', update_data)
        self.assertTrue(res)

        # Verify record updated and persisted in DB
        t_reloaded = self.db.get_teacher('T1001')
        self.assertEqual(t_reloaded['name'], 'Updated Dr. Teacher')
        self.assertEqual(t_reloaded['phone'], '9876543211')
        self.assertEqual(t_reloaded['email'], 'updated_teacher@school.com')
        self.assertEqual(t_reloaded['address'], 'Updated Workstation Address')
        print("[OK] Teacher Profile UPDATE and COMMIT verified successfully.")

    def test_02_student_profile_update(self):
        s = self.db.get_student_by_user_id(self.s_user_id)
        self.assertIsNotNone(s)
        self.assertEqual(s['name'], 'John Doe')

        # Perform UPDATE on editable student fields
        s_data = dict(s)
        s_data['phone'] = '9123456700'
        s_data['email'] = 'john.updated@student.com'
        s_data['address'] = 'New Apartment 4B'

        res = self.db.update_student('S1001', s_data)
        self.assertTrue(res)

        # Verify persistence
        s_reloaded = self.db.get_student('S1001')
        self.assertEqual(s_reloaded['phone'], '9123456700')
        self.assertEqual(s_reloaded['email'], 'john.updated@student.com')
        self.assertEqual(s_reloaded['address'], 'New Apartment 4B')
        # Protected fields remain unchanged
        self.assertEqual(s_reloaded['student_id'], 'S1001')
        self.assertEqual(s_reloaded['name'], 'John Doe')
        print("[OK] Student Profile UPDATE and COMMIT verified successfully.")

    def test_03_parent_profile_update(self):
        p = self.db.get_parent_by_user_id(self.p_user_id)
        self.assertIsNotNone(p)
        self.assertEqual(p['name'], 'Parent Doe')

        # Perform UPDATE
        p_data = {
            'name': 'Updated Parent Doe',
            'phone': '9988776600',
            'email': 'parent.updated@home.com',
            'address': 'New Parent Villa 12',
            'occupation': 'Senior Architect',
            'emergency_contact': '9988776600'
        }
        res = self.db.update_parent_profile(self.p_user_id, p_data, 'PAR1001')
        self.assertTrue(res)

        # Verify persistence
        p_reloaded = self.db.get_parent_by_user_id(self.p_user_id)
        self.assertEqual(p_reloaded['name'], 'Updated Parent Doe')
        self.assertEqual(p_reloaded['phone'], '9988776600')
        self.assertEqual(p_reloaded['email'], 'parent.updated@home.com')
        self.assertEqual(p_reloaded['address'], 'New Parent Villa 12')
        self.assertEqual(p_reloaded['occupation'], 'Senior Architect')
        print("[OK] Parent Profile UPDATE and COMMIT verified successfully.")

    def test_04_teacher_marks_entry_all_subjects_sync(self):
        # Teacher enters marks for 4 subjects for student S1001
        subjects_data = {
            'Mathematics': {'internal_marks': 20.0, 'mid_term_marks': 25.0, 'project_marks': 15.0, 'viva_marks': 10.0, 'final_exam_marks': 80.0},
            'English':     {'internal_marks': 18.0, 'mid_term_marks': 22.0, 'project_marks': 18.0, 'viva_marks': 8.0,  'final_exam_marks': 75.0},
            'Science':     {'internal_marks': 19.0, 'mid_term_marks': 28.0, 'project_marks': 19.0, 'viva_marks': 9.0,  'final_exam_marks': 89.0},
            'Computer':    {'internal_marks': 20.0, 'mid_term_marks': 27.0, 'project_marks': 20.0, 'viva_marks': 10.0, 'final_exam_marks': 82.0}
        }

        for subj, m_dict in subjects_data.items():
            ok = self.db.save_or_update_marks('S1001', m_dict, subj)
            self.assertTrue(ok)

        # 1. Read from Student Portal perspective
        all_student_marks = self.db.get_all_student_marks('S1001')
        self.assertEqual(len(all_student_marks), 4)

        retrieved_subjects = {m['subject']: m for m in all_student_marks}
        self.assertIn('Mathematics', retrieved_subjects)
        self.assertIn('English', retrieved_subjects)
        self.assertIn('Science', retrieved_subjects)
        self.assertIn('Computer', retrieved_subjects)

        # 2. Read overall aggregate marks for student profile stat cards
        overall = self.db.get_student_overall_marks('S1001')
        self.assertEqual(overall['subject_count'], 4)
        self.assertGreater(overall['percentage'], 70.0)
        self.assertNotEqual(overall['grade'], 'N/A')

        # 3. Read from Parent Portal perspective (linked child)
        linked_students = self.db.get_parent_students(self.p_user_id)
        self.assertTrue(any(s['student_id'] == 'S1001' for s in linked_students))

        parent_read_marks = self.db.get_all_student_marks('S1001')
        self.assertEqual(len(parent_read_marks), 4)
        print("[OK] All 4 Subject Marks Sync (Teacher -> DB -> Student & Parent Portals) verified successfully.")

if __name__ == '__main__':
    unittest.main()
