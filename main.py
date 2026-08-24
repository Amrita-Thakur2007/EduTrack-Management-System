import os
import sys
from database.db_manager import DBManager
from gui.welcome import WelcomeWindow

def seed_sample_data(db: DBManager):
    """Seed initial sample records (Students, Teachers, Parents) if database is completely empty."""
    students = db.get_all_students()
    if len(students) == 0:
        print("Seeding initial sample data for demonstration...")

        # Students & Users
        sid1 = "STU101"
        uid1 = db.create_user("student1", "stu123", "Student")
        db.add_student({
            "student_id": sid1,
            "name": "Alex Johnson",
            "father_name": "Michael Johnson",
            "mother_name": "Laura Johnson",
            "dob": "2003-05-14",
            "gender": "Male",
            "phone": "9876543210",
            "email": "alex.j@university.edu",
            "address": "123 Campus Avenue",
            "course": "B.Tech Computer Science",
            "department": "Computer Science & Engineering",
            "current_class": "CS-Year2",
            "section": "A",
            "roll_number": "101",
            "admission_date": "2024-08-01",
            "academic_year": "2024-2025",
            "previous_school": "Central High",
            "previous_percentage": 88.5,
            "study_hours": 4.5
        }, uid1)

        sid2 = "STU102"
        uid2 = db.create_user("student2", "stu123", "Student")
        db.add_student({
            "student_id": sid2,
            "name": "Sophia Martinez",
            "father_name": "Carlos Martinez",
            "mother_name": "Elena Martinez",
            "dob": "2004-01-22",
            "gender": "Female",
            "phone": "9876543211",
            "email": "sophia.m@university.edu",
            "address": "456 College Road",
            "course": "B.Tech Information Technology",
            "department": "Information Technology",
            "current_class": "IT-Year2",
            "section": "B",
            "roll_number": "102",
            "admission_date": "2024-08-01",
            "academic_year": "2024-2025",
            "previous_school": "St. Jude Academy",
            "previous_percentage": 74.0,
            "study_hours": 2.5
        }, uid2)

        # Teacher
        t_user_id = db.create_user("teacher1", "tch123", "Teacher")
        db.add_teacher({
            "teacher_id": "TCH501",
            "name": "Dr. Robert Smith",
            "email": "robert.smith@university.edu",
            "phone": "9988776655",
            "address": "789 Faculty Row",
            "department": "Computer Science & Engineering",
            "designation": "Associate Professor",
            "joining_date": "2022-08-15"
        }, t_user_id)

        # Parent linked to STU101
        p_user_id = db.create_user("parent1", "par123", "Parent")
        db.add_parent({
            "parent_id_code": "PAR101",
            "student_id": sid1,
            "name": "Michael Johnson",
            "phone": "9876500000",
            "email": "michael.j@gmail.com",
            "occupation": "Senior Engineer",
            "emergency_contact": "9876500000",
            "relationship": "Father",
            "address": "123 Campus Avenue"
        }, p_user_id)

        # Seed Marks & Attendance
        from utils.helpers import get_current_date, get_current_time
        today = get_current_date()
        now_t = get_current_time()

        db.mark_attendance(sid1, today, now_t, "Present")
        db.mark_attendance(sid2, today, now_t, "Present")

        db.save_or_update_marks(sid1, {
            "internal_marks": 18.0,
            "mid_term_marks": 26.0,
            "project_marks": 18.5,
            "viva_marks": 9.0,
            "final_exam_marks": 85.0
        }, "General Performance")

        db.save_or_update_marks(sid2, {
            "internal_marks": 12.0,
            "mid_term_marks": 18.0,
            "project_marks": 14.0,
            "viva_marks": 6.0,
            "final_exam_marks": 62.0
        }, "General Performance")

        db.add_notification("System Ready", "Sample dataset initialized successfully.", "ALL")

def main():
    """Main application launcher."""
    print("Starting Student Management & Performance Prediction System...")
    
    # Initialize DB
    db_manager = DBManager()
    
    # Seed sample student/teacher/parent data if empty (NO HARDCODED ADMIN)
    seed_sample_data(db_manager)

    # Launch GUI (WelcomeWindow will handle first-time Admin setup check via DB)
    app = WelcomeWindow(db_manager)
    app.mainloop()

if __name__ == "__main__":
    main()
