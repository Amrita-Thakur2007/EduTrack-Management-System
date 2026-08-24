import sqlite3
import os
from typing import List, Dict, Any, Optional
from utils.security import hash_password, verify_password

class DBManager:
    """Thread-safe SQLite database manager for Student Management System with safe migration."""
    def __init__(self, db_path: str = None):
        if db_path is None:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "database.db")
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=20.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self):
        """Creates tables and performs safe column migrations if necessary."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Students table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                user_id INTEGER,
                name TEXT NOT NULL,
                father_name TEXT,
                mother_name TEXT,
                dob TEXT,
                gender TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                course TEXT,
                department TEXT,
                current_class TEXT,
                section TEXT,
                roll_number TEXT,
                admission_date TEXT,
                academic_year TEXT,
                parent_id_code TEXT,
                previous_school TEXT,
                previous_percentage REAL DEFAULT 0.0,
                study_hours REAL DEFAULT 2.0,
                photo_path TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
            """)

            # Parents table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS parents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id_code TEXT,
                user_id INTEGER,
                student_id TEXT,
                name TEXT NOT NULL,
                relationship TEXT,
                phone TEXT,
                email TEXT,
                occupation TEXT,
                emergency_contact TEXT,
                address TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
            """)

            # Teachers table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS teachers (
                teacher_id TEXT PRIMARY KEY,
                user_id INTEGER,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                address TEXT,
                department TEXT,
                designation TEXT,
                joining_date TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
            """)

            # Attendance table (Students)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
                UNIQUE(student_id, date)
            );
            """)

            # Teacher Attendance table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS teacher_attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id) ON DELETE CASCADE,
                UNIQUE(teacher_id, date)
            );
            """)

            # Teacher Work Logs table (Check-in, Check-out, On-Time/Late status, Working Hours)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS teacher_work_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id TEXT NOT NULL,
                date TEXT NOT NULL,
                check_in_time TEXT,
                check_out_time TEXT,
                status TEXT DEFAULT 'On-Time',
                late_minutes INTEGER DEFAULT 0,
                working_hours REAL DEFAULT 0.0,
                base_salary REAL DEFAULT 3500.0,
                FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id) ON DELETE CASCADE,
                UNIQUE(teacher_id, date)
            );
            """)

            # Marks table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS marks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                subject TEXT NOT NULL DEFAULT 'General Performance',
                internal_marks REAL DEFAULT 0.0,
                mid_term_marks REAL DEFAULT 0.0,
                project_marks REAL DEFAULT 0.0,
                viva_marks REAL DEFAULT 0.0,
                final_exam_marks REAL DEFAULT 0.0,
                total_marks REAL DEFAULT 0.0,
                percentage REAL DEFAULT 0.0,
                grade TEXT DEFAULT 'F',
                status TEXT DEFAULT 'Fail',
                max_marks REAL DEFAULT 180.0,
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
                UNIQUE(student_id, subject)
            );
            """)

            # Notifications table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient_role TEXT DEFAULT 'ALL',
                recipient_id TEXT DEFAULT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                date TEXT NOT NULL,
                is_read INTEGER DEFAULT 0
            );
            """)

            # Parent Marks Notification Tracker Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS parent_marks_notif_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                month_key TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(student_id, month_key)
            );
            """)

            # Face data table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS face_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT UNIQUE NOT NULL,
                encoding_blob BLOB NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
            );
            """)

            # Settings table for school configuration
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """)
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('school_start_time', '07:30 AM');")
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('school_end_time', '12:30 PM');")

            # Holidays table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS holidays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'School Holiday',
                description TEXT,
                created_at TEXT NOT NULL
            );
            """)

            # Activities table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL
            );
            """)

            conn.commit()

            # Safe column migration for existing databases
            self._migrate_table_columns(conn, "users", [
                ("favourite_person_hash", "TEXT"),
                ("failed_login_attempts", "INTEGER DEFAULT 0")
            ])
            self._migrate_table_columns(conn, "students", [
                ("father_name", "TEXT"), ("mother_name", "TEXT"), ("section", "TEXT"),
                ("roll_number", "TEXT"), ("academic_year", "TEXT"), ("parent_id_code", "TEXT"),
                ("father_phone", "TEXT"), ("mother_phone", "TEXT"), ("parent_phone", "TEXT"),
                ("parent_email", "TEXT"), ("guardian_phone", "TEXT"), ("guardian_email", "TEXT"),
                ("photo_path", "TEXT"), ("education_type", "TEXT"), ("school_name", "TEXT"),
                ("college_name", "TEXT"), ("enrollment_number", "TEXT"), ("semester", "TEXT"),
                ("guardian_name", "TEXT")
            ])
            self._migrate_table_columns(conn, "teachers", [
                ("address", "TEXT"), ("joining_date", "TEXT"), ("monthly_salary", "REAL DEFAULT 35000.0")
            ])
            self._migrate_table_columns(conn, "parents", [
                ("parent_id_code", "TEXT"), ("mother_name", "TEXT"), ("mother_phone", "TEXT")
            ])
            self._migrate_table_columns(conn, "marks", [
                ("max_marks", "REAL DEFAULT 180.0")
            ])
            self._migrate_table_columns(conn, "teacher_work_logs", [
                ("teacher_name", "TEXT"),
                ("official_start_time", "TEXT DEFAULT '07:30 AM'"),
                ("official_end_time", "TEXT DEFAULT '12:30 PM'"),
                ("actual_start_time", "TEXT"),
                ("actual_end_time", "TEXT"),
                ("late_minutes", "INTEGER DEFAULT 0"),
                ("total_work_time", "TEXT DEFAULT '00:00:00'"),
                ("attendance_status", "TEXT DEFAULT 'On Time'"),
                ("face_verified", "INTEGER DEFAULT 1"),
                ("salary_deduction", "REAL DEFAULT 0.0"),
                ("work_date", "TEXT"),
                ("start_time", "TEXT"),
                ("end_time", "TEXT"),
                ("total_work_seconds", "INTEGER DEFAULT 0"),
                ("session_status", "TEXT DEFAULT 'NOT_STARTED'")
            ])
            try:
                cursor.execute("UPDATE teacher_work_logs SET work_date = date WHERE work_date IS NULL AND date IS NOT NULL;")
                cursor.execute("UPDATE teacher_work_logs SET start_time = COALESCE(actual_start_time, check_in_time) WHERE start_time IS NULL;")
                cursor.execute("UPDATE teacher_work_logs SET end_time = COALESCE(actual_end_time, check_out_time) WHERE end_time IS NULL;")
                cursor.execute("UPDATE teacher_work_logs SET session_status = status WHERE session_status IS NULL AND status IS NOT NULL;")
                cursor.execute("UPDATE students SET school_name = previous_school WHERE (school_name IS NULL OR school_name = '') AND (previous_school IS NOT NULL AND previous_school != '');")
                cursor.execute("UPDATE students SET college_name = school_name WHERE (education_type IS NOT NULL AND LOWER(education_type) = 'college') AND (college_name IS NULL OR college_name = '') AND (school_name IS NOT NULL AND school_name != '');")
                conn.commit()
            except Exception:
                pass

    def _migrate_table_columns(self, conn: sqlite3.Connection, table_name: str, required_cols: List[tuple]):
        """Safely adds missing columns to an existing SQLite table without altering data."""
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        existing_cols = {row['name'] for row in cursor.fetchall()}

        for col_name, col_type in required_cols:
            if col_name not in existing_cols:
                try:
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type};")
                    print(f"Migrated DB: Added column '{col_name}' to table '{table_name}'.")
                except Exception as e:
                    print(f"Migration notice for {table_name}.{col_name}:", e)
        conn.commit()

    # --- UNIQUNESS CHECK METHODS ---
    def is_username_exists(self, username: str) -> bool:
        if not username or not str(username).strip():
            return False
        u_clean = str(username).strip()
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id, role FROM users WHERE LOWER(username) = LOWER(?)", (u_clean,))
            row = c.fetchone()
            if not row:
                return False

            user_id = row['id']
            role = row['role']

            # Check if user account is attached to an active profile
            if role == 'Student':
                c.execute("""
                    SELECT 1 FROM students 
                    WHERE user_id = ? 
                       OR LOWER(student_id) = LOWER(?) 
                       OR (enrollment_number IS NOT NULL AND LOWER(enrollment_number) = LOWER(?))
                """, (user_id, u_clean, u_clean))
                if not c.fetchone():
                    # Orphaned user record from deleted student profile
                    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
                    conn.commit()
                    return False
            elif role == 'Teacher':
                c.execute("SELECT 1 FROM teachers WHERE user_id = ? OR LOWER(teacher_id) = LOWER(?)", (user_id, u_clean))
                if not c.fetchone():
                    # Orphaned user record from deleted teacher profile
                    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
                    conn.commit()
                    return False
            elif role == 'Parent':
                c.execute("SELECT 1 FROM parents WHERE user_id = ? OR LOWER(parent_id_code) = LOWER(?)", (user_id, u_clean))
                if not c.fetchone():
                    # Orphaned user record from deleted parent profile
                    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
                    conn.commit()
                    return False

            return True

    def is_student_id_exists(self, student_id: str) -> bool:
        if not student_id or not str(student_id).strip():
            return False
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT 1 FROM students WHERE LOWER(student_id) = LOWER(?)", (str(student_id).strip(),))
            return c.fetchone() is not None

    def is_enrollment_number_exists(self, enrollment_number: str) -> bool:
        if not enrollment_number or not str(enrollment_number).strip():
            return False
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT 1 FROM students WHERE LOWER(enrollment_number) = LOWER(?)", (str(enrollment_number).strip(),))
            return c.fetchone() is not None

    def is_teacher_id_exists(self, teacher_id: str) -> bool:
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT 1 FROM teachers WHERE LOWER(teacher_id) = LOWER(?)", (teacher_id.strip(),))
            return c.fetchone() is not None

    def is_parent_id_exists(self, parent_id_code: str) -> bool:
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT 1 FROM parents WHERE LOWER(parent_id_code) = LOWER(?)", (parent_id_code.strip(),))
            return c.fetchone() is not None

    def has_admin(self) -> bool:
        """Check if at least one Admin account exists."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'Admin'")
            row = cursor.fetchone()
            return row['count'] > 0

    def create_user(self, username: str, password: str, role: str, favourite_person: str = None) -> Optional[int]:
        """Create a user account with PBKDF2 salt hashing and security question hash. Returns new user ID or None."""
        pwd_hash, salt = hash_password(password)
        fav_hash = None
        if favourite_person and favourite_person.strip():
            fav_hash, _ = hash_password(favourite_person.strip().lower(), salt)

        u_clean = username.strip()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            # If username belongs only to a deleted profile, clean it up first
            if not self.is_username_exists(u_clean):
                cursor.execute("DELETE FROM users WHERE LOWER(username) = LOWER(?)", (u_clean,))
                conn.commit()

            try:
                cursor.execute(
                    "INSERT INTO users (username, password_hash, salt, role, favourite_person_hash) VALUES (?, ?, ?, ?, ?)",
                    (u_clean, pwd_hash, salt, role, fav_hash)
                )
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                cursor.execute("DELETE FROM users WHERE LOWER(username) = LOWER(?)", (u_clean,))
                conn.commit()
                try:
                    cursor.execute(
                        "INSERT INTO users (username, password_hash, salt, role, favourite_person_hash) VALUES (?, ?, ?, ?, ?)",
                        (u_clean, pwd_hash, salt, role, fav_hash)
                    )
                    conn.commit()
                    return cursor.lastrowid
                except sqlite3.IntegrityError:
                    return None

    def authenticate_user(self, username: str, password: str, expected_role: str = None) -> Dict[str, Any]:
        """Authenticate user credentials with failed attempt rate limiting. Returns dict with status or user_data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),))
            user = cursor.fetchone()
            if not user:
                cursor.execute("""
                    SELECT u.* FROM users u
                    JOIN students s ON u.id = s.user_id
                    WHERE (s.student_id IS NOT NULL AND LOWER(s.student_id) = LOWER(?))
                       OR (s.enrollment_number IS NOT NULL AND LOWER(s.enrollment_number) = LOWER(?))
                """, (username.strip(), username.strip()))
                user = cursor.fetchone()

            if not user:
                return {"success": False, "error_type": "invalid_user", "message": f"Account with User ID / Enrollment Number '{username.strip()}' does not exist."}
            
            if expected_role and user['role'] != expected_role:
                return {"success": False, "error_type": "invalid_role", "message": f"Account is registered under '{user['role']}' role, not '{expected_role}'."}

            failed_attempts = user['failed_login_attempts'] if dict(user).get('failed_login_attempts') is not None else 0
            if failed_attempts >= 5:
                return {
                    "success": False,
                    "error_type": "locked",
                    "message": "Account locked due to 5 consecutive failed login attempts. Please click 'Forgot Password?' to reset your password."
                }

            if verify_password(password, user['password_hash'], user['salt']):
                cursor.execute("UPDATE users SET failed_login_attempts = 0 WHERE id = ?", (user['id'],))
                conn.commit()
                res = dict(user)
                res["success"] = True
                return res

            new_failed = failed_attempts + 1
            cursor.execute("UPDATE users SET failed_login_attempts = ? WHERE id = ?", (new_failed, user['id']))
            conn.commit()

            if new_failed >= 5:
                return {
                    "success": False,
                    "error_type": "locked",
                    "message": "Account locked due to 5 consecutive failed login attempts. Please click 'Forgot Password?' to reset your password."
                }
            return {
                "success": False,
                "error_type": "wrong_password",
                "message": "Wrong password. Please try again."
            }

    def reset_password_with_favourite_person(self, identifier: str, favourite_person_answer: str, new_password: str, role: str = None) -> Tuple[bool, str]:
        """Reset password after verifying User ID/Email and Favourite Person Name."""
        ident_clean = str(identifier or '').strip()
        ans_clean = str(favourite_person_answer or '').strip().lower()
        if not ident_clean or not ans_clean or not new_password:
            return False, "Please fill all required recovery fields."

        with self.get_connection() as conn:
            cursor = conn.cursor()
            user = None
            # 1. Direct username or student/enrollment ID lookup
            query = "SELECT * FROM users WHERE TRIM(LOWER(username)) = TRIM(LOWER(?))"
            params = [ident_clean]
            if role:
                query += " AND role = ?"
                params.append(role)
            cursor.execute(query, params)
            user = cursor.fetchone()

            if not user:
                query = """
                    SELECT u.* FROM users u
                    JOIN students s ON u.id = s.user_id
                    WHERE (
                        (s.student_id IS NOT NULL AND TRIM(LOWER(s.student_id)) = TRIM(LOWER(?)))
                        OR (s.enrollment_number IS NOT NULL AND TRIM(LOWER(s.enrollment_number)) = TRIM(LOWER(?)))
                    )
                """
                params = [ident_clean, ident_clean]
                if role:
                    query += " AND u.role = ?"
                    params.append(role)
                cursor.execute(query, params)
                user = cursor.fetchone()

            # 2. Registered email lookup from students/teachers/parents tables if not matched by username
            if not user:
                cursor.execute("""
                    SELECT u.* FROM users u
                    LEFT JOIN students s ON u.id = s.user_id
                    LEFT JOIN teachers t ON u.id = t.user_id
                    LEFT JOIN parents p ON u.id = p.user_id
                    WHERE (
                        (s.email IS NOT NULL AND s.email != '' AND TRIM(LOWER(s.email)) = TRIM(LOWER(?)))
                        OR (t.email IS NOT NULL AND t.email != '' AND TRIM(LOWER(t.email)) = TRIM(LOWER(?)))
                        OR (p.email IS NOT NULL AND p.email != '' AND TRIM(LOWER(p.email)) = TRIM(LOWER(?)))
                    )
                """, (ident_clean, ident_clean, ident_clean))
                user = cursor.fetchone()

            if not user:
                return False, "User ID or registered email not found."

            user_dict = dict(user)
            stored_fav_hash = user_dict.get('favourite_person_hash')

            if stored_fav_hash:
                ans_hash, _ = hash_password(ans_clean, user_dict['salt'])
                if ans_hash != stored_fav_hash:
                    return False, "Incorrect Favourite Person Name. Please try again."

            new_hash, new_salt = hash_password(new_password)
            new_fav_hash, _ = hash_password(ans_clean, new_salt)

            cursor.execute("""
                UPDATE users SET
                    password_hash = ?,
                    salt = ?,
                    favourite_person_hash = ?,
                    failed_login_attempts = 0
                WHERE id = ?
            """, (new_hash, new_salt, new_fav_hash, user_dict['id']))
            conn.commit()
            return True, "Password reset successfully. Please log in using your new password."

    def change_user_password(self, user_id: int, current_pwd: str, new_pwd: str) -> tuple[bool, str]:
        """Verifies current password and updates to new PBKDF2 hashed password."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            if not user:
                return False, "User account not found."

            if not verify_password(current_pwd, user['password_hash'], user['salt']):
                return False, "Current Password is incorrect."

            new_hash, new_salt = hash_password(new_pwd)
            cursor.execute(
                "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
                (new_hash, new_salt, user_id)
            )
            conn.commit()
            return True, "Password changed successfully."

    def update_user_username(self, user_id: int, new_username: str) -> tuple[bool, str]:
        """Update username for user_id after verifying uniqueness."""
        new_u = new_username.strip()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (new_u,))
            existing = cursor.fetchone()
            if existing and existing['id'] != user_id:
                return False, f"Username '{new_u}' is already taken."

            cursor.execute("UPDATE users SET username = ? WHERE id = ?", (new_u, user_id))
            conn.commit()
            return True, "Username updated successfully."

    def add_notification(self, title: str, message: str, recipient_role: str = 'ALL', recipient_id: str = None):
        """Add a new notification entry."""
        from utils.helpers import get_current_date
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO notifications (recipient_role, recipient_id, title, message, date) VALUES (?, ?, ?, ?, ?)",
                (recipient_role, recipient_id, title, message, get_current_date())
            )
            conn.commit()

    def add_parent_marks_notification(self, student_id: str, date_override: str = None) -> bool:
        """
        Creates a Parent marks notification ("See your marks, marks updated.")
        allowing only ONE marks notification per parent/student relationship per month.
        """
        from utils.helpers import get_current_date
        today_str = str(date_override).strip() if date_override else get_current_date()
        month_key = today_str[:7]  # e.g. "2026-08"
        sid_clean = str(student_id).strip()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parent_marks_notif_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    month_key TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(student_id, month_key)
                );
            """)

            # Check if notification was already generated for this student in this month
            cursor.execute("""
                SELECT id FROM parent_marks_notif_log
                WHERE TRIM(LOWER(student_id)) = TRIM(LOWER(?)) AND month_key = ?
            """, (sid_clean, month_key))
            if cursor.fetchone():
                return False

            # Record that monthly notification was triggered for this month
            cursor.execute("""
                INSERT OR IGNORE INTO parent_marks_notif_log (student_id, month_key, created_at)
                VALUES (?, ?, ?)
            """, (sid_clean, month_key, today_str))

            # Add notification entry for Parent
            cursor.execute("""
                INSERT INTO notifications (recipient_role, recipient_id, title, message, date, is_read)
                VALUES (?, ?, ?, ?, ?, 0)
            """, ('Parent', sid_clean, 'Marks Updated', 'See your marks, marks updated.', today_str))

            conn.commit()
            return True

    def mark_notification_as_read(self, notification_id: int) -> bool:
        """Mark notification as read and remove/delete it from active list."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM notifications WHERE id = ?", (notification_id,))
            conn.commit()
            return True

    def clear_parent_marks_notifications(self, student_id: str) -> bool:
        """Delete/clear all active parent marks notifications for a student when viewed by parent."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM notifications 
                WHERE recipient_role = 'Parent' 
                  AND TRIM(LOWER(recipient_id)) = TRIM(LOWER(?))
                  AND (title = 'Marks Updated' OR message = 'See your marks, marks updated.')
            """, (str(student_id).strip(),))
            conn.commit()
            return cursor.rowcount > 0

    def get_notifications(self, role: str, user_target_id: str = None) -> List[Dict[str, Any]]:
        """Fetch notifications matching role or target ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT * FROM notifications 
                WHERE recipient_role = 'ALL' 
                   OR recipient_role = ? 
                   OR (recipient_id IS NOT NULL AND recipient_id = ?)
                ORDER BY id DESC LIMIT 50
            """
            cursor.execute(query, (role, user_target_id))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    # --- STUDENT METHODS ---
    def add_student(self, student_data: Dict[str, Any], user_id: int = None) -> bool:
        """Insert a new student record with complete fields."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO students (
                        student_id, user_id, name, father_name, mother_name, dob, gender, phone, email, address,
                        course, department, current_class, section, roll_number, admission_date, academic_year,
                        parent_id_code, previous_school, previous_percentage, study_hours,
                        father_phone, mother_phone, parent_phone, parent_email, guardian_phone, guardian_email, photo_path,
                        education_type, school_name, college_name, enrollment_number, semester, guardian_name
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    student_data['student_id'].strip(),
                    user_id,
                    student_data['name'].strip(),
                    student_data.get('father_name', '').strip(),
                    student_data.get('mother_name', '').strip(),
                    student_data.get('dob', '').strip(),
                    student_data.get('gender', 'Male'),
                    student_data.get('phone', '').strip(),
                    student_data.get('email', '').strip(),
                    student_data.get('address', '').strip(),
                    student_data.get('course', '').strip(),
                    student_data.get('department', '').strip(),
                    student_data.get('current_class', '').strip(),
                    student_data.get('section', '').strip(),
                    student_data.get('roll_number', '').strip(),
                    student_data.get('admission_date', '').strip(),
                    student_data.get('academic_year', '').strip(),
                    student_data.get('parent_id_code', '').strip(),
                    student_data.get('previous_school', '').strip(),
                    float(student_data.get('previous_percentage', 0.0)),
                    float(student_data.get('study_hours', 2.0)),
                    student_data.get('father_phone', student_data.get('parent_phone', '')).strip(),
                    student_data.get('mother_phone', '').strip(),
                    student_data.get('parent_phone', '').strip(),
                    student_data.get('parent_email', '').strip(),
                    student_data.get('guardian_phone', student_data.get('parent_phone', '')).strip(),
                    student_data.get('guardian_email', student_data.get('parent_email', '')).strip(),
                    student_data.get('photo_path', '').strip(),
                    student_data.get('education_type', 'School').strip(),
                    student_data.get('school_name', '').strip(),
                    student_data.get('college_name', '').strip(),
                    student_data.get('enrollment_number', '').strip(),
                    student_data.get('semester', '').strip(),
                    student_data.get('guardian_name', '').strip()
                ))
                conn.commit()
                return True
            except sqlite3.Error as e:
                print("Error adding student:", e)
                return False

    def update_student(self, student_id: str, student_data: Dict[str, Any]) -> bool:
        """Update existing student details."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sid_clean = str(student_id).strip()
            cursor.execute("""
                UPDATE students SET
                    name = ?, father_name = ?, mother_name = ?, dob = ?, gender = ?, phone = ?, email = ?, address = ?,
                    course = ?, department = ?, current_class = ?, section = ?, roll_number = ?, admission_date = ?,
                    academic_year = ?, parent_id_code = ?, previous_school = ?, previous_percentage = ?, study_hours = ?,
                    father_phone = ?, mother_phone = ?, parent_phone = ?, parent_email = ?, guardian_phone = ?, guardian_email = ?,
                    photo_path = ?, education_type = ?, school_name = ?, college_name = ?, enrollment_number = ?, semester = ?, guardian_name = ?
                WHERE TRIM(LOWER(student_id)) = TRIM(LOWER(?))
            """, (
                student_data['name'].strip(),
                student_data.get('father_name', '').strip(),
                student_data.get('mother_name', '').strip(),
                student_data.get('dob', '').strip(),
                student_data.get('gender', 'Male'),
                student_data.get('phone', '').strip(),
                student_data.get('email', '').strip(),
                student_data.get('address', '').strip(),
                student_data.get('course', '').strip(),
                student_data.get('department', '').strip(),
                student_data.get('current_class', '').strip(),
                student_data.get('section', '').strip(),
                student_data.get('roll_number', '').strip(),
                student_data.get('admission_date', '').strip(),
                student_data.get('academic_year', '').strip(),
                student_data.get('parent_id_code', '').strip(),
                student_data.get('previous_school', '').strip(),
                float(student_data.get('previous_percentage', 0.0)),
                float(student_data.get('study_hours', 2.0)),
                student_data.get('father_phone', student_data.get('parent_phone', '')).strip(),
                student_data.get('mother_phone', '').strip(),
                student_data.get('parent_phone', '').strip(),
                student_data.get('parent_email', '').strip(),
                student_data.get('guardian_phone', student_data.get('parent_phone', '')).strip(),
                student_data.get('guardian_email', student_data.get('parent_email', '')).strip(),
                student_data.get('photo_path', '').strip(),
                student_data.get('education_type', 'School').strip(),
                student_data.get('school_name', '').strip(),
                student_data.get('college_name', '').strip(),
                student_data.get('enrollment_number', '').strip(),
                student_data.get('semester', '').strip(),
                student_data.get('guardian_name', '').strip(),
                sid_clean
            ))
            conn.commit()
            return cursor.rowcount > 0 or self.is_student_id_exists(sid_clean)

    def check_duplicate_student(self, name: str, dob: str, current_class: str, section: str, parent_phone: str, exclude_sid: str = None) -> Optional[Dict[str, Any]]:
        """Check if a student with matching Name + Class/Section + (DOB or Parent Phone) already exists."""
        if not name or not current_class:
            return None
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT * FROM students
                WHERE TRIM(LOWER(name)) = TRIM(LOWER(?))
                  AND TRIM(LOWER(current_class)) = TRIM(LOWER(?))
                  AND TRIM(LOWER(section)) = TRIM(LOWER(?))
                  AND (
                      (dob IS NOT NULL AND dob != '' AND dob = ?)
                      OR (father_phone IS NOT NULL AND father_phone != '' AND father_phone = ?)
                      OR (parent_phone IS NOT NULL AND parent_phone != '' AND parent_phone = ?)
                  )
            """
            params = [name.strip(), current_class.strip(), section.strip(), dob.strip(), parent_phone.strip(), parent_phone.strip()]
            if exclude_sid:
                query += " AND TRIM(LOWER(student_id)) != TRIM(LOWER(?))"
                params.append(exclude_sid.strip())
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_student(self, student_id: str) -> bool:
        """Delete student and linked records, including user account."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sid_clean = str(student_id).strip()

            cursor.execute("SELECT user_id, student_id, enrollment_number FROM students WHERE TRIM(LOWER(student_id)) = TRIM(LOWER(?))", (sid_clean,))
            row = cursor.fetchone()
            user_id = row['user_id'] if row else None
            enr_no = row['enrollment_number'] if row else None

            cursor.execute("DELETE FROM students WHERE TRIM(LOWER(student_id)) = TRIM(LOWER(?))", (sid_clean,))
            deleted = cursor.rowcount > 0

            if user_id:
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            cursor.execute("DELETE FROM users WHERE LOWER(username) = LOWER(?)", (sid_clean,))
            if enr_no:
                cursor.execute("DELETE FROM users WHERE LOWER(username) = LOWER(?)", (enr_no.strip(),))

            conn.commit()
            return deleted

    def _format_student_dict(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """Helper to format student dictionary and ensure school_name and college_name fallbacks."""
        if not d:
            return d
        res = dict(d)
        sch_name = res.get('school_name') or res.get('previous_school') or ''
        col_name = res.get('college_name') or res.get('school_name') or res.get('previous_school') or ''
        res['school_name'] = sch_name
        res['college_name'] = col_name
        return res

    def get_student(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Get single student by student_id or enrollment_number."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sid_clean = str(student_id).strip()
            cursor.execute("""
                SELECT * FROM students 
                WHERE TRIM(LOWER(student_id)) = TRIM(LOWER(?))
                   OR (enrollment_number IS NOT NULL AND TRIM(LOWER(enrollment_number)) = TRIM(LOWER(?)))
            """, (sid_clean, sid_clean))
            row = cursor.fetchone()
            return self._format_student_dict(dict(row)) if row else None

    def get_student_by_user_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get single student by user_id."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return self._format_student_dict(dict(row)) if row else None

    def get_all_students(self, search_term: str = None, filter_dept: str = None, filter_course: str = None, filter_edu_type: str = None) -> List[Dict[str, Any]]:
        """Fetch all students with optional search/filter."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM students WHERE 1=1"
            params = []
            if search_term:
                query += " AND (student_id LIKE ? OR name LIKE ? OR email LIKE ? OR roll_number LIKE ? OR course LIKE ? OR enrollment_number LIKE ? OR school_name LIKE ? OR college_name LIKE ? OR previous_school LIKE ?)"
                t = f"%{search_term.strip()}%"
                params.extend([t, t, t, t, t, t, t, t, t])
            if filter_dept and filter_dept != "All":
                query += " AND department = ?"
                params.append(filter_dept)
            if filter_course and filter_course != "All":
                query += " AND course = ?"
                params.append(filter_course)
            if filter_edu_type and filter_edu_type != "All":
                if filter_edu_type == "School":
                    query += " AND (LOWER(education_type) = 'school' OR (education_type IS NULL AND (course IS NULL OR course = '')))"
                elif filter_edu_type == "College":
                    query += " AND (LOWER(education_type) = 'college' OR (course IS NOT NULL AND course != '') OR (enrollment_number IS NOT NULL AND enrollment_number != ''))"
            
            query += " ORDER BY name ASC"
            cursor.execute(query, params)
            return [self._format_student_dict(dict(r)) for r in cursor.fetchall()]

    # --- TEACHER METHODS ---
    def add_teacher(self, teacher_data: Dict[str, Any], user_id: int = None) -> bool:
        """Insert a teacher record with full fields."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO teachers (teacher_id, user_id, name, phone, email, address, department, designation, joining_date, monthly_salary)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    teacher_data['teacher_id'].strip(),
                    user_id,
                    teacher_data['name'].strip(),
                    teacher_data.get('phone', '').strip(),
                    teacher_data.get('email', '').strip(),
                    teacher_data.get('address', '').strip(),
                    teacher_data.get('department', '').strip(),
                    teacher_data.get('designation', '').strip(),
                    teacher_data.get('joining_date', '').strip(),
                    float(teacher_data.get('monthly_salary', 35000.0))
                ))
                conn.commit()
                return True
            except sqlite3.Error as e:
                print("Error adding teacher:", e)
                return False

    def update_teacher_salary(self, teacher_id: str, monthly_salary: float) -> bool:
        """Update individual teacher's monthly salary in database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE teachers SET monthly_salary = ? WHERE TRIM(LOWER(teacher_id)) = TRIM(LOWER(?))
            """, (float(monthly_salary), str(teacher_id).strip()))
            conn.commit()
            return cursor.rowcount > 0

    def update_teacher(self, teacher_id: str, teacher_data: Dict[str, Any]) -> bool:
        """Update teacher details."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE teachers SET name = ?, phone = ?, email = ?, address = ?, department = ?, designation = ?, joining_date = ?
                WHERE teacher_id = ?
            """, (
                teacher_data['name'].strip(),
                teacher_data.get('phone', '').strip(),
                teacher_data.get('email', '').strip(),
                teacher_data.get('address', '').strip(),
                teacher_data.get('department', '').strip(),
                teacher_data.get('designation', '').strip(),
                teacher_data.get('joining_date', '').strip(),
                teacher_id
            ))
            conn.commit()
            return cursor.rowcount > 0

    def delete_teacher(self, teacher_id: str) -> bool:
        """Delete teacher record and linked user account."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            tid_clean = str(teacher_id).strip()

            cursor.execute("SELECT user_id FROM teachers WHERE TRIM(LOWER(teacher_id)) = TRIM(LOWER(?))", (tid_clean,))
            row = cursor.fetchone()
            user_id = row['user_id'] if row else None

            cursor.execute("DELETE FROM teachers WHERE TRIM(LOWER(teacher_id)) = TRIM(LOWER(?))", (tid_clean,))
            deleted = cursor.rowcount > 0

            if user_id:
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            cursor.execute("DELETE FROM users WHERE LOWER(username) = LOWER(?)", (tid_clean,))

            conn.commit()
            return deleted

    def get_all_teachers(self, search_term: str = None) -> List[Dict[str, Any]]:
        """Fetch all teachers with optional search filtering by ID, name, or email."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM teachers WHERE 1=1"
            params = []
            if search_term:
                query += " AND (teacher_id LIKE ? OR name LIKE ? OR email LIKE ?)"
                t = f"%{search_term.strip()}%"
                params.extend([t, t, t])
            query += " ORDER BY name ASC"
            cursor.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]

    def get_teacher(self, teacher_id: str) -> Optional[Dict[str, Any]]:
        """Fetch single teacher record by teacher_id."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM teachers WHERE teacher_id = ?", (teacher_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_teacher_by_user_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Fetch single teacher record by user_id, with fallback auto-linking and creation."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM teachers WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)

            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user_row = cursor.fetchone()
            if user_row and user_row['role'] == 'Teacher':
                username = user_row['username']
                cursor.execute("SELECT * FROM teachers WHERE teacher_id = ? OR LOWER(name) = LOWER(?)", (username, username))
                t_match = cursor.fetchone()
                if t_match:
                    cursor.execute("UPDATE teachers SET user_id = ? WHERE teacher_id = ?", (user_id, t_match['teacher_id']))
                    conn.commit()
                    return self.get_teacher(t_match['teacher_id'])
                else:
                    tid = f"T{user_id:03d}"
                    cursor.execute("""
                        INSERT OR IGNORE INTO teachers (teacher_id, user_id, name, email, department, designation, joining_date)
                        VALUES (?, ?, ?, ?, 'Science', 'Teacher', CURRENT_DATE)
                    """, (tid, user_id, username, f"{username}@school.com"))
                    conn.commit()
                    return self.get_teacher(tid)
            return None

    # --- PARENT METHODS ---
    def add_parent(self, parent_data: Dict[str, Any], user_id: int = None) -> bool:
        """Insert parent record with parent_id_code."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO parents (
                        parent_id_code, user_id, student_id, name, mother_name, relationship, phone, mother_phone, email, occupation, emergency_contact, address
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    parent_data.get('parent_id_code', '').strip(),
                    user_id,
                    parent_data.get('student_id', '').strip(),
                    parent_data['name'].strip(),
                    parent_data.get('mother_name', '').strip(),
                    parent_data.get('relationship', 'Parent').strip(),
                    parent_data.get('phone', '').strip(),
                    parent_data.get('mother_phone', '').strip(),
                    parent_data.get('email', '').strip(),
                    parent_data.get('occupation', '').strip(),
                    parent_data.get('emergency_contact', '').strip(),
                    parent_data.get('address', '').strip()
                ))
                conn.commit()
                return True
            except sqlite3.Error as e:
                print("Error adding parent:", e)
                return False

    def update_parent(self, student_id: str, parent_data: Dict[str, Any]) -> bool:
        """Update existing parent record by student_id."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                sid_clean = str(student_id).strip()
                p_name = parent_data.get('name', '').strip()
                m_name = parent_data.get('mother_name', '').strip()
                rel = parent_data.get('relationship', 'Parent').strip()
                f_phone = parent_data.get('phone', parent_data.get('father_phone', '')).strip()
                m_phone = parent_data.get('mother_phone', '').strip()
                p_email = parent_data.get('email', parent_data.get('parent_email', '')).strip()
                p_occ = parent_data.get('occupation', '').strip()
                em_contact = parent_data.get('emergency_contact', '').strip()
                addr = parent_data.get('address', '').strip()

                cursor.execute("""
                    UPDATE parents SET
                        name = ?, mother_name = ?, relationship = ?, phone = ?, mother_phone = ?, email = ?, occupation = ?, emergency_contact = ?, address = ?
                    WHERE TRIM(LOWER(student_id)) = TRIM(LOWER(?))
                """, (
                    p_name, m_name, rel, f_phone, m_phone, p_email, p_occ, em_contact, addr, sid_clean
                ))
                conn.commit()
                return cursor.rowcount > 0 or self.get_parent_by_student_id(sid_clean) is not None
            except Exception as e:
                import traceback
                print("Error updating parent:", e)
                traceback.print_exc()
                return False

    def update_parent_profile(self, user_id: int, parent_data: Dict[str, Any], parent_id_code: str = None) -> bool:
        """Update parent profile record in database by user_id or parent_id_code."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                name = parent_data.get('name', '').strip()
                phone = parent_data.get('phone', '').strip()
                email = parent_data.get('email', '').strip()
                address = parent_data.get('address', '').strip()
                occupation = parent_data.get('occupation', '').strip()
                emergency_contact = parent_data.get('emergency_contact', '').strip()

                cursor.execute("""
                    UPDATE parents SET
                        name = ?, phone = ?, email = ?, address = ?, occupation = ?, emergency_contact = ?
                    WHERE user_id = ? OR (parent_id_code IS NOT NULL AND parent_id_code != '' AND LOWER(parent_id_code) = LOWER(?))
                """, (name, phone, email, address, occupation, emergency_contact, user_id, (parent_id_code or '').strip()))
                conn.commit()
                return cursor.rowcount > 0 or self.get_parent_by_user_id(user_id) is not None
            except Exception as e:
                print("Error in update_parent_profile:", e)
                return False

    def get_parent_by_user_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get parent details by user_id."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM parents WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_parent_by_student_id(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Get parent record by linked student_id."""
        if not student_id:
            return None
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM parents WHERE TRIM(LOWER(student_id)) = TRIM(LOWER(?))", (str(student_id).strip(),))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_parent_by_id_code(self, parent_id_code: str) -> Optional[Dict[str, Any]]:
        """Get parent record by parent_id_code."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM parents WHERE LOWER(parent_id_code) = LOWER(?)", (parent_id_code.strip(),))
            row = cursor.fetchone()
            return dict(row) if row else None

    def auto_link_parent_account(self, student_id: str, phone: str = None, email: str = None, mother_phone: str = None) -> bool:
        """Find parent user account by phone/email and associate user_id with parent record."""
        if not student_id:
            return False
        with self.get_connection() as conn:
            cursor = conn.cursor()
            p_user_id = None
            # 1. Find user_id from parents table matching phone/email
            query = """
                SELECT user_id FROM parents
                WHERE user_id IS NOT NULL AND (
                    (phone IS NOT NULL AND phone != '' AND phone = ?)
                    OR (mother_phone IS NOT NULL AND mother_phone != '' AND mother_phone = ?)
                    OR (email IS NOT NULL AND email != '' AND email = ?)
                ) LIMIT 1
            """
            params = [phone or '', mother_phone or phone or '', email or '']
            cursor.execute(query, params)
            row = cursor.fetchone()
            if row and row['user_id']:
                p_user_id = row['user_id']
            else:
                # 2. Find user_id from users table where role = 'Parent' matching username
                cursor.execute("""
                    SELECT id FROM users
                    WHERE role = 'Parent' AND (
                        username = ? OR username = ?
                    ) LIMIT 1
                """, (phone or '', email or ''))
                urow = cursor.fetchone()
                if urow and urow['id']:
                    p_user_id = urow['id']

            if p_user_id:
                cursor.execute("""
                    UPDATE parents SET user_id = ?
                    WHERE TRIM(LOWER(student_id)) = TRIM(LOWER(?))
                """, (p_user_id, student_id.strip()))
                conn.commit()
                return True
            return False

    def get_parent_students(self, user_id: int) -> List[Dict[str, Any]]:
        """Fetch all student records linked to a parent user_id or parent's phone/email."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Get parent phone & email details
            cursor.execute("SELECT phone, mother_phone, email FROM parents WHERE user_id = ?", (user_id,))
            p_rec = cursor.fetchone()
            p_phone = p_rec['phone'] if p_rec and p_rec['phone'] else ''
            m_phone = p_rec['mother_phone'] if p_rec and p_rec['mother_phone'] else ''
            p_email = p_rec['email'] if p_rec and p_rec['email'] else ''

            cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            u_rec = cursor.fetchone()
            u_phone = u_rec['username'] if u_rec and u_rec['username'] else ''

            phones = list(filter(None, set([p_phone, m_phone, u_phone])))
            emails = list(filter(None, set([p_email])))

            query = """
                SELECT DISTINCT s.*
                FROM students s
                LEFT JOIN parents p ON TRIM(LOWER(s.student_id)) = TRIM(LOWER(p.student_id))
                WHERE p.user_id = ?
            """
            params = [user_id]

            if phones:
                ph_placeholders = ",".join(["?"] * len(phones))
                query += f"""
                    OR s.father_phone IN ({ph_placeholders})
                    OR s.mother_phone IN ({ph_placeholders})
                    OR s.parent_phone IN ({ph_placeholders})
                    OR p.phone IN ({ph_placeholders})
                    OR p.mother_phone IN ({ph_placeholders})
                """
                params.extend(phones * 5)

            if emails:
                em_placeholders = ",".join(["?"] * len(emails))
                query += f"""
                    OR s.parent_email IN ({em_placeholders})
                    OR p.email IN ({em_placeholders})
                """
                params.extend(emails * 2)

            query += " ORDER BY s.name ASC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_all_parents(self, search_term: str = None) -> List[Dict[str, Any]]:
        """Fetch all parents with optional search filtering by name, email, phone, or student_id."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM parents WHERE 1=1"
            params = []
            if search_term:
                query += " AND (name LIKE ? OR email LIKE ? OR phone LIKE ? OR student_id LIKE ? OR parent_id_code LIKE ?)"
                t = f"%{search_term.strip()}%"
                params.extend([t, t, t, t, t])
            query += " ORDER BY name ASC"
            cursor.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]

    def update_parent_by_id_code(self, parent_id_code: str, parent_data: Dict[str, Any]) -> bool:
        """Update parent record by parent_id_code in SQLite."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE parents SET name = ?, student_id = ?, relationship = ?, phone = ?, email = ?, address = ?
                WHERE TRIM(LOWER(parent_id_code)) = TRIM(LOWER(?))
            """, (
                parent_data['name'].strip(),
                parent_data.get('student_id', '').strip(),
                parent_data.get('relationship', 'Parent').strip(),
                parent_data.get('phone', '').strip(),
                parent_data.get('email', '').strip(),
                parent_data.get('address', '').strip(),
                parent_id_code.strip()
            ))
            conn.commit()
            return cursor.rowcount > 0

    def delete_parent(self, parent_id_code: str) -> bool:
        """Delete parent record and linked user account."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            pid_clean = str(parent_id_code).strip()

            cursor.execute("SELECT user_id FROM parents WHERE TRIM(LOWER(parent_id_code)) = TRIM(LOWER(?))", (pid_clean,))
            row = cursor.fetchone()
            user_id = row['user_id'] if row else None

            cursor.execute("DELETE FROM parents WHERE TRIM(LOWER(parent_id_code)) = TRIM(LOWER(?))", (pid_clean,))
            deleted = cursor.rowcount > 0

            if user_id:
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            cursor.execute("DELETE FROM users WHERE LOWER(username) = LOWER(?)", (pid_clean,))

            conn.commit()
            return deleted


    # --- ATTENDANCE METHODS ---
    def mark_attendance(self, student_id: str, date_str: str, time_str: str, status: str = 'Present') -> tuple[bool, str]:
        """Mark or update student attendance for date. Returns (success, message)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sid_clean = str(student_id).strip()
            try:
                cursor.execute(
                    "SELECT id FROM attendance WHERE TRIM(LOWER(student_id)) = TRIM(LOWER(?)) AND date = ?",
                    (sid_clean, date_str)
                )
                row = cursor.fetchone()
                if row:
                    cursor.execute(
                        "UPDATE attendance SET status = ?, time = ? WHERE id = ?",
                        (status, time_str, row['id'])
                    )
                    conn.commit()
                    return True, f"Attendance updated to '{status}' for {sid_clean}."
                else:
                    cursor.execute(
                        "INSERT INTO attendance (student_id, date, time, status) VALUES (?, ?, ?, ?)",
                        (sid_clean, date_str, time_str, status)
                    )
                    conn.commit()
                    
                    # Auto-generate notifications for Student and Parent
                    self.add_notification(
                        title="Attendance Logged",
                        message=f"Attendance marked as '{status}' on {date_str} at {time_str}.",
                        recipient_role="Student",
                        recipient_id=sid_clean
                    )
                    self.add_notification(
                        title="Child Attendance Update",
                        message=f"Attendance for student {sid_clean} marked as '{status}' on {date_str}.",
                        recipient_role="Parent",
                        recipient_id=sid_clean
                    )
                    return True, f"Attendance marked as '{status}' for {sid_clean}."
            except sqlite3.Error as e:
                return False, f"Failed to mark attendance: {e}"

    def get_student_attendance_for_date(self, student_id: str, date_str: str) -> Optional[Dict[str, Any]]:
        """Get student attendance record for a specific date."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sid_clean = str(student_id).strip()
            cursor.execute(
                "SELECT * FROM attendance WHERE TRIM(LOWER(student_id)) = TRIM(LOWER(?)) AND date = ?",
                (sid_clean, date_str)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_student_attendance(self, student_id: str) -> List[Dict[str, Any]]:
        """Get attendance log for student."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM attendance WHERE student_id = ? ORDER BY date DESC, time DESC", (student_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_student_attendance_stats(self, student_id: str) -> Dict[str, Any]:
        """Calculate attendance stats for a student."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM attendance WHERE student_id = ?", (student_id,))
            total = cursor.fetchone()['total']
            cursor.execute("SELECT COUNT(*) as present FROM attendance WHERE student_id = ? AND status = 'Present'", (student_id,))
            present = cursor.fetchone()['present']
            absent = total - present
            pct = round((present / total * 100.0), 2) if total > 0 else 0.0
            return {
                "total_days": total,
                "present_days": present,
                "absent_days": absent,
                "percentage": pct
            }

    def mark_teacher_attendance(self, teacher_id: str, date_str: str, time_str: str, status: str = 'Present') -> tuple[bool, str]:
        """Mark teacher attendance for date. Returns (success, message)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO teacher_attendance (teacher_id, date, time, status) VALUES (?, ?, ?, ?)",
                    (teacher_id, date_str, time_str, status)
                )
                conn.commit()
                self.add_notification(
                    title="Teacher Attendance Logged",
                    message=f"Attendance marked as '{status}' for teacher {teacher_id} on {date_str} at {time_str}.",
                    recipient_role="Teacher",
                    recipient_id=teacher_id
                )
                return True, f"Attendance marked as '{status}' for Teacher {teacher_id}."
            except sqlite3.IntegrityError:
                return False, "Teacher attendance already marked for today."

    def get_teacher_attendance(self, teacher_id: str) -> List[Dict[str, Any]]:
        """Get attendance log for a teacher."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM teacher_attendance WHERE teacher_id = ? ORDER BY date DESC, time DESC", (teacher_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_all_teacher_attendance(self, date_str: str = None) -> List[Dict[str, Any]]:
        """Get all teacher attendance logs, optionally filtered by date."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if date_str:
                cursor.execute("""
                    SELECT ta.date, ta.time, ta.teacher_id, t.name as teacher_name, t.department, ta.status
                    FROM teacher_attendance ta
                    JOIN teachers t ON ta.teacher_id = t.teacher_id
                    WHERE ta.date = ?
                    ORDER BY ta.time DESC
                """, (date_str,))
            else:
                cursor.execute("""
                    SELECT ta.date, ta.time, ta.teacher_id, t.name as teacher_name, t.department, ta.status
                    FROM teacher_attendance ta
                    JOIN teachers t ON ta.teacher_id = t.teacher_id
                    ORDER BY ta.date DESC, ta.time DESC LIMIT 200
                """)
            return [dict(r) for r in cursor.fetchall()]

    def get_attendance_dashboard_summary(self, date_str: str = None) -> Dict[str, Any]:
        """Calculate Present/Absent records & counts for both Students and Teachers for a given date."""
        if not date_str:
            from utils.helpers import get_current_date
            date_str = get_current_date()

        all_students = self.get_all_students()
        all_teachers = self.get_all_teachers()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Student Present Today
            cursor.execute("""
                SELECT a.date, a.time, a.student_id, s.name as name, s.course, a.status
                FROM attendance a
                JOIN students s ON a.student_id = s.student_id
                WHERE a.date = ? AND a.status = 'Present'
            """, (date_str,))
            stu_present_rows = [dict(r) for r in cursor.fetchall()]
            present_stu_ids = {r['student_id'] for r in stu_present_rows}

            # Student Absent Today (all registered students not present today)
            stu_absent_rows = []
            for s in all_students:
                if s['student_id'] not in present_stu_ids:
                    stu_absent_rows.append({
                        "student_id": s['student_id'],
                        "name": s['name'],
                        "course": s.get('course', 'N/A'),
                        "date": date_str,
                        "time": "--:--:--",
                        "status": "Absent"
                    })

            # Teacher Present Today
            cursor.execute("""
                SELECT ta.date, ta.time, ta.teacher_id, t.name as name, t.department, ta.status
                FROM teacher_attendance ta
                JOIN teachers t ON ta.teacher_id = t.teacher_id
                WHERE ta.date = ? AND ta.status = 'Present'
            """, (date_str,))
            teach_present_rows = [dict(r) for r in cursor.fetchall()]
            present_teach_ids = {r['teacher_id'] for r in teach_present_rows}

            # Teacher Absent Today (all registered teachers not present today)
            teach_absent_rows = []
            for t in all_teachers:
                if t['teacher_id'] not in present_teach_ids:
                    teach_absent_rows.append({
                        "teacher_id": t['teacher_id'],
                        "name": t['name'],
                        "department": t.get('department', 'General'),
                        "date": date_str,
                        "time": "--:--:--",
                        "status": "Absent"
                    })

            return {
                "date": date_str,
                "students_present": stu_present_rows,
                "students_absent": stu_absent_rows,
                "students_present_count": len(stu_present_rows),
                "students_absent_count": len(stu_absent_rows),
                "teachers_present": teach_present_rows,
                "teachers_absent": teach_absent_rows,
                "teachers_present_count": len(teach_present_rows),
                "teachers_absent_count": len(teach_absent_rows)
            }

    def get_teacher_today_attendance(self, teacher_id: str, date_str: str = None) -> Optional[Dict[str, Any]]:
        """Fetch teacher attendance record for a specific date."""
        if not date_str:
            from utils.helpers import get_current_date
            date_str = get_current_date()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM teacher_attendance WHERE teacher_id = ? AND date = ?", (teacher_id, date_str))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_today_attendance_summary(self, date_str: str) -> Dict[str, int]:
        """Summary of present/absent for specified date."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as present FROM attendance WHERE date = ? AND status = 'Present'", (date_str,))
            present = cursor.fetchone()['present']
            cursor.execute("SELECT COUNT(*) as absent FROM attendance WHERE date = ? AND status = 'Absent'", (date_str,))
            absent = cursor.fetchone()['absent']
            return {"present": present, "absent": absent}

    # --- SCHOOL TIMINGS SETTINGS METHODS ---
    def get_school_timings(self) -> Dict[str, str]:
        """Fetch central official school start and end times."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings WHERE key IN ('school_start_time', 'school_end_time')")
            rows = cursor.fetchall()
            d = {r['key']: r['value'] for r in rows}
            return {
                "start_time": d.get("school_start_time", "07:30 AM"),
                "end_time": d.get("school_end_time", "12:30 PM")
            }

    def update_school_timings(self, start_time: str, end_time: str) -> bool:
        """Update central official school start and end times."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('school_start_time', ?)", (start_time,))
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('school_end_time', ?)", (end_time,))
            conn.commit()
            return True

    # --- TEACHER WORK TIME & SALARY METHODS ---
    def record_teacher_login(self, teacher_id: str, start_time_override: str = None) -> Dict[str, Any]:
        """Record teacher check-in time on manual START click."""
        from datetime import datetime
        from utils.helpers import get_current_date, parse_datetime_helper

        today = get_current_date()
        now_time_str = start_time_override if start_time_override else datetime.now().strftime("%I:%M:%S %p")
        timings = self.get_school_timings()
        off_start = timings['start_time']
        off_end = timings['end_time']

        teacher = self.get_teacher(teacher_id)
        tname = teacher['name'] if teacher else teacher_id

        try:
            start_dt = parse_datetime_helper(off_start, today) or datetime.now()
            curr_dt = parse_datetime_helper(now_time_str, today) or datetime.now()
            diff_mins = int((curr_dt - start_dt).total_seconds() // 60)

            if diff_mins > 0:
                att_status = "Late"
                late_mins = diff_mins
                deduction = round(late_mins * 1.0, 2)
            else:
                att_status = "On Time"
                late_mins = 0
                deduction = 0.0
        except Exception as e:
            print("Time parse error in record_teacher_login:", e)
            att_status = "On Time"
            late_mins = 0
            deduction = 0.0

        sess_status = "ACTIVE"
        db_status = "RUNNING"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            existing = self.get_teacher_work_log(teacher_id, today)

            def clean_val(v):
                if not v or str(v).strip() in ("", "--", "None", "NULL"):
                    return None
                return str(v).strip()

            if not existing:
                cursor.execute("""
                    INSERT INTO teacher_work_logs (
                        teacher_id, teacher_name, date, work_date, official_start_time, official_end_time,
                        actual_start_time, check_in_time, start_time, status, session_status, attendance_status,
                        late_minutes, face_verified, salary_deduction
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """, (teacher_id, tname, today, today, off_start, off_end, now_time_str, now_time_str, now_time_str, db_status, sess_status, att_status, late_mins, deduction))
                conn.commit()
                return self.get_teacher_work_log(teacher_id, today) or {
                    "teacher_id": teacher_id,
                    "work_date": today,
                    "date": today,
                    "official_start_time": off_start,
                    "official_end_time": off_end,
                    "actual_start_time": now_time_str,
                    "check_in_time": now_time_str,
                    "start_time": now_time_str,
                    "status": db_status,
                    "session_status": sess_status,
                    "attendance_status": att_status,
                    "late_minutes": late_mins,
                    "salary_deduction": deduction,
                    "face_verified": 1
                }
            else:
                cursor.execute("""
                    UPDATE teacher_work_logs SET
                        work_date = ?,
                        actual_start_time = ?,
                        check_in_time = ?,
                        start_time = ?,
                        status = ?,
                        session_status = ?,
                        attendance_status = ?,
                        late_minutes = ?,
                        salary_deduction = ?
                    WHERE id = ?
                """, (today, now_time_str, now_time_str, now_time_str, db_status, sess_status, att_status, late_mins, deduction, existing['id']))
                conn.commit()
                return self.get_teacher_work_log(teacher_id, today) or existing

    def record_teacher_logout(self, teacher_id: str, end_time_override: str = None) -> bool:
        """Record teacher check-out time on manual END click or logout."""
        from datetime import datetime
        from utils.helpers import get_current_date, parse_datetime_helper

        today = get_current_date()
        now_time_str = end_time_override if end_time_override else datetime.now().strftime("%I:%M:%S %p")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            log_rec = self.get_teacher_work_log(teacher_id, today)

            def clean_val(v):
                if not v or str(v).strip() in ("", "--", "None", "NULL"):
                    return None
                return str(v).strip()

            if log_rec:
                log_id = log_rec['id']
                check_in_str = clean_val(log_rec.get('start_time')) or clean_val(log_rec.get('actual_start_time')) or clean_val(log_rec.get('check_in_time'))
                diff_secs = 0
                if check_in_str:
                    try:
                        t_in = parse_datetime_helper(check_in_str, log_rec.get('date', today))
                        t_out = parse_datetime_helper(now_time_str, today)

                        if t_in and t_out:
                            diff_secs = int((t_out - t_in).total_seconds())
                            if diff_secs < 0:
                                diff_secs += 86400  # Cross-midnight session support

                            dur_hours = round(diff_secs / 3600.0, 2)

                            hrs = diff_secs // 3600
                            mins = (diff_secs % 3600) // 60
                            secs = diff_secs % 60
                            total_work_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"
                        else:
                            dur_hours = 0.0
                            total_work_str = "00:00:00"
                    except Exception as e:
                        print("Logout calc error:", e)
                        dur_hours = 0.0
                        total_work_str = "00:00:00"
                else:
                    dur_hours = 0.0
                    total_work_str = "00:00:00"

                cursor.execute("""
                    UPDATE teacher_work_logs SET
                        actual_end_time = ?, check_out_time = ?, end_time = ?, working_hours = ?, total_work_time = ?, total_work_seconds = ?, status = 'ENDED', session_status = 'ENDED'
                    WHERE id = ?
                """, (now_time_str, now_time_str, now_time_str, dur_hours, total_work_str, diff_secs, log_id))
                conn.commit()
                return True
            return False

    def get_teacher_work_log(self, teacher_id: str, date_str: str = None) -> Optional[Dict[str, Any]]:
        """Fetch teacher work log for specific date."""
        if not date_str:
            from utils.helpers import get_current_date
            date_str = get_current_date()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM teacher_work_logs WHERE teacher_id = ? AND date = ?", (teacher_id, date_str))
            row = cursor.fetchone()
            if row:
                return dict(row)

            # Fallback matching alternative date formats (e.g. YYYY-MM-DD vs DD-MM-YYYY)
            cursor.execute("SELECT * FROM teacher_work_logs WHERE teacher_id = ?", (teacher_id,))
            rows = cursor.fetchall()
            for r in rows:
                d = dict(r)
                if d['date'].strip() == date_str.strip():
                    return d
                try:
                    from datetime import datetime
                    d1, d2 = None, None
                    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"):
                        try:
                            d1 = datetime.strptime(date_str.strip(), fmt).date()
                            break
                        except ValueError:
                            pass
                    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"):
                        try:
                            d2 = datetime.strptime(d['date'].strip(), fmt).date()
                            break
                        except ValueError:
                            pass
                    if d1 and d2 and d1 == d2:
                        return d
                except Exception:
                    pass
            return None

    def get_teacher_salary_summary(self, teacher_id: str, base_salary: float = None) -> Dict[str, Any]:
        """Calculate complete monthly salary summary based on actual attendance & work hours."""
        teacher = self.get_teacher(teacher_id)
        tname = teacher['name'] if teacher else teacher_id
        tdept = teacher.get('department', 'General') if teacher else 'General'

        if base_salary is None:
            base_salary = float(teacher.get('monthly_salary', 35000.0)) if teacher else 35000.0

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Present Days
            cursor.execute("SELECT COUNT(*) as present_days FROM teacher_attendance WHERE teacher_id = ? AND status = 'Present'", (teacher_id,))
            present_days = cursor.fetchone()['present_days']

            # Total Working Hours, Late Summary & Deductions
            cursor.execute("""
                SELECT SUM(working_hours) as total_hrs, SUM(late_minutes) as total_late, SUM(salary_deduction) as total_ded
                FROM teacher_work_logs WHERE teacher_id = ?
            """, (teacher_id,))
            row_hrs = cursor.fetchone()
            total_hours = float(row_hrs['total_hrs'] or 0.0)
            total_late = int(row_hrs['total_late'] or 0)
            late_deduction = float(row_hrs['total_ded'] or 0.0)

            working_days = 26
            daily_rate = round(base_salary / working_days, 2)
            earned_base = round(daily_rate * present_days, 2)

            expected_hours = present_days * 5.0
            overtime_hours = round(max(0.0, total_hours - expected_hours), 2)
            hourly_rate = round(daily_rate / 5.0, 2)
            overtime_amount = round(overtime_hours * hourly_rate * 1.5, 2)
            total_salary = round(earned_base + overtime_amount - late_deduction, 2)

            return {
                "teacher_id": teacher_id,
                "teacher_name": tname,
                "department": tdept,
                "present_days": present_days,
                "working_days": working_days,
                "total_working_hours": total_hours,
                "late_summary_mins": total_late,
                "late_deduction": late_deduction,
                "overtime_hours": overtime_hours,
                "base_salary": base_salary,
                "earned_base_salary": earned_base,
                "overtime_amount": overtime_amount,
                "total_salary": total_salary
            }

    def get_all_teachers_salary_summary(self) -> List[Dict[str, Any]]:
        """Calculate salary summary for all registered teachers."""
        teachers = self.get_all_teachers()
        results = []
        for t in teachers:
            results.append(self.get_teacher_salary_summary(t['teacher_id']))
        return results

    # --- MARKS METHODS ---
    def _resolve_student_identifiers(self, student_id: str):
        """Helper to resolve primary student_id and all lookup identifiers (ID, Enrollment Number)."""
        sid_raw = str(student_id).strip()
        s = self.get_student(sid_raw)
        primary_sid = s.get('student_id') if s and s.get('student_id') else sid_raw
        sids = list(filter(None, set([
            sid_raw,
            primary_sid,
            str(s.get('enrollment_number')).strip() if s and s.get('enrollment_number') else None
        ])))
        return primary_sid, sids

    def save_or_update_marks(self, student_id: str, marks_data: Dict[str, Any], subject: str = "General Performance") -> bool:
        """Insert or update student marks breakdown."""
        from utils.helpers import calculate_grade_and_status
        internal = float(marks_data.get('internal_marks', 0.0))
        mid = float(marks_data.get('mid_term_marks', 0.0))
        proj = float(marks_data.get('project_marks', 0.0))
        viva = float(marks_data.get('viva_marks', 0.0))
        final_exam = float(marks_data.get('final_exam_marks', 0.0))

        total = internal + mid + proj + viva + final_exam
        pct, grade, status = calculate_grade_and_status(total)

        primary_sid, sids = self._resolve_student_identifiers(student_id)
        subj_clean = str(subject).strip()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join(["LOWER(?)"] * len(sids))
            query_check = f"SELECT id FROM marks WHERE LOWER(student_id) IN ({placeholders}) AND TRIM(LOWER(subject)) = TRIM(LOWER(?))"
            params_check = [s_id.lower() for s_id in sids] + [subj_clean.lower()]
            cursor.execute(query_check, params_check)
            existing_row = cursor.fetchone()

            if existing_row:
                record_id = existing_row['id']
                cursor.execute("""
                    UPDATE marks SET
                        student_id = ?,
                        subject = ?,
                        internal_marks = ?,
                        mid_term_marks = ?,
                        project_marks = ?,
                        viva_marks = ?,
                        final_exam_marks = ?,
                        total_marks = ?,
                        percentage = ?,
                        grade = ?,
                        status = ?
                    WHERE id = ?
                """, (primary_sid, subj_clean, internal, mid, proj, viva, final_exam, total, pct, grade, status, record_id))
            else:
                cursor.execute("""
                    INSERT INTO marks (
                        student_id, subject, internal_marks, mid_term_marks, project_marks, viva_marks,
                        final_exam_marks, total_marks, percentage, grade, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (primary_sid, subj_clean, internal, mid, proj, viva, final_exam, total, pct, grade, status))
            conn.commit()

            # Auto-generate notifications for Student and Parent
            self.add_notification(
                title="Marks Updated",
                message=f"Your marks for '{subj_clean}' have been updated (Total: {total}/180, Grade: {grade}).",
                recipient_role="Student",
                recipient_id=primary_sid
            )
            # Monthly rule Parent Marks Notification: "See your marks, marks updated."
            self.add_parent_marks_notification(primary_sid)
            return True

    def get_student_marks(self, student_id: str, subject: str = "General Performance") -> Optional[Dict[str, Any]]:
        """Fetch student marks for a subject."""
        _, sids = self._resolve_student_identifiers(student_id)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join(["LOWER(?)"] * len(sids))
            query = f"SELECT * FROM marks WHERE LOWER(student_id) IN ({placeholders}) AND TRIM(LOWER(subject)) = TRIM(LOWER(?))"
            params = [s_id.lower() for s_id in sids] + [str(subject).strip().lower()]
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_student_marks(self, student_id: str) -> List[Dict[str, Any]]:
        """Fetch all subject marks for a student."""
        _, sids = self._resolve_student_identifiers(student_id)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join(["LOWER(?)"] * len(sids))
            query = f"SELECT * FROM marks WHERE LOWER(student_id) IN ({placeholders}) ORDER BY subject ASC"
            params = [s_id.lower() for s_id in sids]
            cursor.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]

    def delete_student_marks(self, student_id: str, subject: str) -> bool:
        """Delete specific subject marks record for a student."""
        _, sids = self._resolve_student_identifiers(student_id)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join(["LOWER(?)"] * len(sids))
            query = f"DELETE FROM marks WHERE LOWER(student_id) IN ({placeholders}) AND TRIM(LOWER(subject)) = TRIM(LOWER(?))"
            params = [s_id.lower() for s_id in sids] + [str(subject).strip().lower()]
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0

    def get_student_overall_marks(self, student_id: str) -> Dict[str, Any]:
        """Fetch and aggregate overall academic performance marks for a student across all subjects."""
        all_m = self.get_all_student_marks(student_id)
        if not all_m:
            return {
                'total_marks': 0.0,
                'max_marks': 0.0,
                'percentage': 0.0,
                'grade': 'N/A',
                'status': 'No Records',
                'subject_count': 0
            }

        total_obtained_100 = 0.0
        total_max_100 = len(all_m) * 100.0
        any_failed = False

        for m in all_m:
            val_int = float(m.get('internal_marks', 0.0))
            val_mid = float(m.get('mid_term_marks', 0.0))
            val_proj = float(m.get('project_marks', 0.0))
            val_viva = float(m.get('viva_marks', 0.0))
            val_final = float(m.get('final_exam_marks', 0.0))
            stotal = float(m.get('total_marks', val_int + val_mid + val_proj + val_viva + val_final))

            if 'percentage' in m and m['percentage'] is not None and m['percentage'] > 0:
                subj_score = float(m['percentage'])
            else:
                subj_score = round((stotal / 180.0 * 100.0), 2) if stotal <= 180.0 else min(100.0, stotal)

            status = str(m.get('status', 'Fail')).lower()
            if status == 'fail':
                any_failed = True
            total_obtained_100 += subj_score

        overall_pct = round((total_obtained_100 / total_max_100 * 100.0), 2) if total_max_100 > 0 else 0.0
        
        from utils.helpers import calculate_grade_and_status
        _, grade, _ = calculate_grade_and_status(overall_pct * 1.8) if overall_pct > 0 else (0.0, 'F', 'Fail')
        overall_status = "Fail" if (any_failed or overall_pct < 40.0) else "Pass"

        return {
            'total_marks': round(total_obtained_100, 1),
            'max_marks': round(total_max_100, 1),
            'percentage': overall_pct,
            'grade': grade,
            'status': overall_status,
            'subject_count': len(all_m)
        }

    def delete_student_marks(self, student_id: str, subject: str) -> bool:
        """Delete specific subject marks record for a student."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM marks WHERE student_id = ? AND LOWER(subject) = LOWER(?)", (student_id, subject.strip()))
            conn.commit()
            return True

    # --- FACE DATA METHODS ---
    def save_face_encoding(self, student_id: str, encoding_bytes: bytes) -> bool:
        """Store face encoding vector bytes for a student or teacher ID."""
        from utils.helpers import get_current_date, get_current_time
        now_str = f"{get_current_date()} {get_current_time()}"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = OFF;")
            cursor.execute("""
                INSERT INTO face_data (student_id, encoding_blob, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(student_id) DO UPDATE SET
                    encoding_blob = excluded.encoding_blob,
                    updated_at = excluded.updated_at
            """, (student_id, encoding_bytes, now_str))
            conn.commit()
            return True

    def get_all_face_encodings(self) -> List[Dict[str, Any]]:
        """Retrieve all stored face encodings."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT student_id, encoding_blob FROM face_data")
            return [dict(r) for r in cursor.fetchall()]

    # --- SYSTEM METRICS FOR DASHBOARDS ---
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Calculate high-level dashboard metrics."""
        from utils.helpers import get_current_date
        today = get_current_date()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM students")
            total_students = cursor.fetchone()['cnt']
            
            cursor.execute("SELECT COUNT(*) as cnt FROM teachers")
            total_teachers = cursor.fetchone()['cnt']

            cursor.execute("SELECT COUNT(DISTINCT parent_id_code) as cnt FROM parents")
            total_parents = cursor.fetchone()['cnt']
            if total_parents == 0:
                cursor.execute("SELECT COUNT(*) as cnt FROM parents")
                total_parents = cursor.fetchone()['cnt']

            cursor.execute("SELECT COUNT(*) as cnt FROM attendance WHERE date = ? AND status = 'Present'", (today,))
            today_present = cursor.fetchone()['cnt']

            cursor.execute("SELECT COUNT(*) as cnt FROM attendance WHERE date = ? AND status = 'Absent'", (today,))
            today_absent = cursor.fetchone()['cnt']

            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN status = 'Present' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as avg_att
                FROM attendance
            """)
            row_att = cursor.fetchone()
            avg_att = round(row_att['avg_att'], 1) if row_att and row_att['avg_att'] is not None else 0.0

            cursor.execute("SELECT AVG(percentage) as avg_pct FROM marks")
            row_marks = cursor.fetchone()
            avg_perf = round(row_marks['avg_pct'], 1) if row_marks and row_marks['avg_pct'] is not None else 0.0

            return {
                "total_students": total_students,
                "total_teachers": total_teachers,
                "total_parents": total_parents,
                "today_present": today_present,
                "today_absent": today_absent,
                "avg_attendance": avg_att,
                "avg_performance": avg_perf
            }

    # --- HOLIDAY MANAGEMENT METHODS ---
    def add_holiday(self, title: str, date_str: str, description: str = "", type_str: str = "School Holiday") -> bool:
        """Add new holiday record (title, date, description) and broadcast notification to ALL users."""
        from utils.helpers import get_current_date
        created_at = get_current_date()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO holidays (title, date, type, description, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (title.strip(), date_str.strip(), type_str.strip(), description.strip(), created_at))
            conn.commit()

            # Automatic Notification Announcement to ALL users
            desc_msg = f" Announcement: {description.strip()}" if description.strip() else ""
            msg = f"🎉 Holiday Announcement: {title} on {date_str}.{desc_msg}"
            self.add_notification(
                title=f"🔔 Holiday Announcement: {title}",
                message=msg,
                recipient_role="ALL"
            )
            return True

    def update_holiday(self, holiday_id: int, title: str, date_str: str, description: str = "", type_str: str = "School Holiday") -> bool:
        """Update existing holiday record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE holidays SET title = ?, date = ?, type = ?, description = ?
                WHERE id = ?
            """, (title.strip(), date_str.strip(), type_str.strip(), description.strip(), holiday_id))
            conn.commit()
            return cursor.rowcount > 0

    def delete_holiday(self, holiday_id: int) -> bool:
        """Delete holiday record by id."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM holidays WHERE id = ?", (holiday_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_all_holidays(self) -> List[Dict[str, Any]]:
        """Fetch all holidays ordered by id ASC."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM holidays ORDER BY id ASC")
            return [dict(r) for r in cursor.fetchall()]

    def get_today_holiday(self, date_str: str = None) -> Optional[Dict[str, Any]]:
        """Fetch holiday for specified or current date."""
        if not date_str:
            from utils.helpers import get_current_date
            date_str = get_current_date()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM holidays WHERE date = ?", (date_str.strip(),))
            row = cursor.fetchone()
            if row:
                return dict(row)

            # Robust fallback for flexible date formats (e.g., DD-MM-YYYY vs YYYY-MM-DD)
            cursor.execute("SELECT * FROM holidays")
            rows = cursor.fetchall()
            for r in rows:
                d = dict(r)
                if d['date'].strip() == date_str.strip():
                    return d
                try:
                    from datetime import datetime
                    d1, d2 = None, None
                    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"):
                        try:
                            d1 = datetime.strptime(date_str.strip(), fmt).date()
                            break
                        except ValueError:
                            pass
                    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"):
                        try:
                            d2 = datetime.strptime(d['date'].strip(), fmt).date()
                            break
                        except ValueError:
                            pass
                    if d1 and d2 and d1 == d2:
                        return d
                except Exception:
                    pass
            return None

    def get_upcoming_holidays(self, date_str: str = None) -> List[Dict[str, Any]]:
        """Fetch upcoming holidays (returns all holidays ordered by id ASC)."""
        return self.get_all_holidays()

    def is_today_holiday(self, date_str: str = None) -> bool:
        """Check if specified/current date is an official holiday."""
        return self.get_today_holiday(date_str) is not None

    # --- ACTIVITY MANAGEMENT METHODS ---
    def add_activity(self, title: str, date_str: str, description: str = "") -> bool:
        """Add new activity record (title, date, description)."""
        from utils.helpers import get_current_date
        created_at = get_current_date()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO activities (title, date, description, created_at)
                VALUES (?, ?, ?, ?)
            """, (title.strip(), date_str.strip(), description.strip(), created_at))
            conn.commit()
            return True

    def update_activity(self, activity_id: int, title: str, date_str: str, description: str = "") -> bool:
        """Update existing activity record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE activities SET title = ?, date = ?, description = ?
                WHERE id = ?
            """, (title.strip(), date_str.strip(), description.strip(), activity_id))
            conn.commit()
            return cursor.rowcount > 0

    def delete_activity(self, activity_id: int) -> bool:
        """Delete activity record by id."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_all_activities(self) -> List[Dict[str, Any]]:
        """Fetch all activities ordered by date ASC."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM activities ORDER BY date ASC")
            return [dict(r) for r in cursor.fetchall()]

