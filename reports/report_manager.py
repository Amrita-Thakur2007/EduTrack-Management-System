import os
import pandas as pd
from typing import List, Dict, Any
from database.db_manager import DBManager

class ReportManager:
    """Generates structured data reports and handles CSV exports using Pandas."""
    def __init__(self, db_manager: DBManager):
        self.db = db_manager

    def generate_student_list_dataframe(self, search_term: str = None, filter_dept: str = None, filter_course: str = None) -> pd.DataFrame:
        """Fetch students list into a Pandas DataFrame."""
        students = self.db.get_all_students(search_term, filter_dept, filter_course)
        if not students:
            return pd.DataFrame()
        df = pd.DataFrame(students)
        cols_order = ['student_id', 'name', 'course', 'department', 'current_class', 'phone', 'email', 'study_hours', 'previous_percentage']
        existing_cols = [c for c in cols_order if c in df.columns]
        return df[existing_cols]

    def generate_attendance_report_dataframe(self, student_id: str = None) -> pd.DataFrame:
        """Fetch attendance records into a DataFrame."""
        with self.db.get_connection() as conn:
            query = """
                SELECT a.student_id, s.name as student_name, s.course, s.department, a.date, a.time, a.status
                FROM attendance a
                JOIN students s ON a.student_id = s.student_id
            """
            params = []
            if student_id:
                query += " WHERE a.student_id = ?"
                params.append(student_id)
            query += " ORDER BY a.date DESC, a.time DESC"
            df = pd.read_sql_query(query, conn, params=params)
            return df

    def generate_marks_report_dataframe(self, student_id: str = None) -> pd.DataFrame:
        """Fetch subject marks & evaluation records into a DataFrame."""
        with self.db.get_connection() as conn:
            query = """
                SELECT m.student_id, s.name as student_name, s.course, m.subject,
                       m.internal_marks, m.mid_term_marks, m.project_marks, m.viva_marks,
                       m.final_exam_marks, m.total_marks, m.percentage, m.grade, m.status
                FROM marks m
                JOIN students s ON m.student_id = s.student_id
            """
            params = []
            if student_id:
                query += " WHERE m.student_id = ?"
                params.append(student_id)
            query += " ORDER BY m.student_id ASC, m.subject ASC"
            df = pd.read_sql_query(query, conn, params=params)
            return df

    def export_dataframe_to_csv(self, df: pd.DataFrame, filepath: str) -> tuple[bool, str]:
        """Export a pandas DataFrame to CSV file."""
        if df.empty:
            return False, "Data is empty. Nothing to export."
        try:
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            df.to_csv(filepath, index=False)
            return True, f"Successfully exported {len(df)} records to {filepath}."
        except Exception as e:
            return False, f"Failed to export CSV: {str(e)}"
