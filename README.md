# 🎓 EduTrack Management System

A Python-based **School & College Management System** designed to manage students, teachers, parents, attendance, academic records, face recognition, and administrative activities through separate role-based portals.

The project is built with a focus on **easy management, automation, data persistence, and a simple desktop GUI**.

---

## 📌 About the Project

**EduTrack Management System** provides separate portals for:

- 👨‍💼 Admin
- 👩‍🏫 Teacher
- 👨‍🎓 Student
- 👨‍👩‍👧 Parent

Each portal provides features according to the user's role.

The system supports both **School Mode** and **College Mode**, allowing the same application to manage different types of educational institutions.

---

## ✨ Key Features

### 👨‍💼 Admin Portal

The Admin can manage the complete system.

Features include:

- Admin Dashboard
- Student Management
- Teacher Management
- Parent Management
- Attendance Management
- Individual Monthly Attendance
- Academic Marks & Evaluation
- Student Result Dashboard
- School/College information
- User management
- Data monitoring
- Attendance history
- Monthly attendance reports

---

### 👩‍🏫 Teacher Portal

Teachers can manage their students and academic activities.

Features include:

- Teacher Dashboard
- My Class Students
- Student details
- Add Student
- Edit Student
- Delete Student
- Student management
- Attendance management
- Face-based attendance
- Individual monthly attendance
- Date-wise attendance records
- Present / Absent / Leave status
- Student academic records
- Marks entry
- Student result information
- Face registration/update where applicable

Teachers can also view a student's attendance month-by-month.

Example:

```text
August 2026

28 August  → Present
29 August  → Absent
30 August  → Present
31 August  → Leave
```

---

### 👨‍🎓 Student Portal

Students can manage their own information and academic activities.

Features include:

- Student Login
- Student Dashboard
- My Profile
- Edit Profile
- Attendance
- Attendance History
- Individual Monthly Attendance
- Year & Month selection
- Date-wise attendance
- Present / Absent / Leave status
- Face registration
- Face-based attendance
- Academic marks
- Result information

Students can view previous months' attendance without losing historical records.

---

### 👨‍👩‍👧 Parent Portal

Parents can access information related to their children.

Features include:

- Parent Registration
- Parent Login
- Parent Dashboard
- Child information
- Attendance information
- Monthly attendance
- Academic information
- Student performance information

Student-entered parent details do **not automatically create a Parent account**.

A Parent account is created when the Parent completes the Parent registration process.

---

# 📅 Attendance Management

The system supports date-wise attendance.

Attendance can contain:

- **Present**
- **Absent**
- **Leave**

### Attendance Rules

If a valid attendance record exists:

```text
Present → Present
Leave   → Leave
```

If an applicable past/current date has no attendance record:

```text
No Record → Absent
```

Future dates are not automatically marked as Absent.

---

## 📆 Monthly Attendance

Users can select:

```text
Year → Month
```

and view the complete attendance for that month.

Example:

```text
Year: 2026
Month: September
```

The system displays the applicable dates in proper chronological order:

```text
1 September
2 September
3 September
4 September
...
30 September
```

Previous months remain available for viewing.

---

# 🤳 Face Recognition Attendance

The system supports face-based attendance.

The important distinction is:

```text
Face Detection ≠ Face Recognition
```

A detected face should not automatically be accepted as the selected student's identity.

For an existing registered student:

```text
Selected Student
       ↓
Existing Registered Face
       ↓
Camera
       ↓
Face Detection
       ↓
Face Recognition / Matching
       ↓
Identity Verified?
       ↓
YES → Continue
NO  → Reject
```

This helps prevent one person's face from being registered or used as another student's identity.

---

## 👩‍🏫 Teacher Face Attendance

A teacher can select a student and use the Face Attendance feature.

Example:

```text
Teacher Portal
   ↓
My Class Students
   ↓
Select Student
   ↓
Face Attendance
   ↓
Camera
   ↓
Verify Selected Student
   ↓
Present
```

If successful, the attendance source can indicate:

```text
Marked By: Teacher
```

If the student marks their own attendance:

```text
Marked By: Student
```

Duplicate attendance records should not be created for the same student and date.

---

# 🎓 School & College Mode

EduTrack supports both:

### 🏫 School Mode

Suitable for school student management and attendance.

### 🎓 College Mode

Suitable for college student management and academic records.

The same core system can handle both modes while maintaining student-specific information.

---

# 🗂️ Attendance History

Attendance history provides a record of student attendance over time.

Users can view:

- Date
- Attendance status
- Monthly records
- Previous attendance
- Student-specific attendance

The date order is chronological and based on actual calendar dates rather than alphabetical text sorting.

---

# 📊 Academic Management

The system provides academic record management including:

- Subject information
- Marks
- Internal assessment
- Mid-term marks
- Project marks
- Grades
- Percentage
- Result information
- Student result dashboard

Teachers can enter academic information and students can view their results through the Student Portal.

---

# 🧑‍🎓 Student Management

Student records can contain information such as:

- Student ID
- Student Name
- Personal details
- Contact information
- School Name
- Department
- Course/Program information where applicable
- Admission Date
- Academic information
- Face registration information

The system uses the existing Student ID to associate student-related records.

---

# 🛠️ Technologies Used

The project is developed using Python.

Main technologies/libraries include:

- **Python**
- **Tkinter** — Graphical User Interface
- **SQLite** — Database management
- **OpenCV** — Computer vision and face-related functionality
- **NumPy** — Numerical operations
- **Pandas** — Data handling
- **Matplotlib** — Data visualization

Additional Python libraries may be used depending on the enabled features in the project.

---

# 💾 Database

The application uses a persistent database to store system information.

The database can contain records related to:

- Students
- Teachers
- Parents
- Attendance
- Academic records
- Face registration
- User accounts

Existing records should be preserved when modifying or updating the application.

---

# 🔐 Data & Validation

The system uses role-based access so users can access features according to their portal.

Important validation areas include:

- Unique Student IDs
- User authentication
- Required fields
- Attendance duplication prevention
- Student-specific data
- Face identity verification
- Database consistency

---

# 🚀 Installation

## 1. Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
```

Then move into the project folder:

```bash
cd EduTrack-Management-System
```

---

## 2. Install Python

Make sure Python is installed on your computer.

Check:

```bash
python --version
```

or:

```bash
python3 --version
```

---

## 3. Install Required Libraries

Install the required packages:

```bash
pip install numpy pandas matplotlib opencv-python pillow
```

If the project contains a `requirements.txt` file, preferably use:

```bash
pip install -r requirements.txt
```

---

# ▶️ Running the Project

Open the project in **VS Code**.

Run the main Python file:

```bash
python main.py
```

If your project uses a different entry file, run the project's main Python file instead.

---

# 🔑 User Flow

The general system flow is:

```text
Application
    ↓
Role Selection
    ↓
Admin / Teacher / Student / Parent
    ↓
Login / Registration
    ↓
Role Dashboard
    ↓
Role-specific Features
```

---

# 👨‍💼 Admin Flow

```text
Admin Login
     ↓
Admin Dashboard
     ↓
Manage Students / Teachers / Parents
     ↓
Attendance
     ↓
Academic Evaluation
     ↓
Reports / Individual Records
```

---

# 👩‍🏫 Teacher Flow

```text
Teacher Login
     ↓
Teacher Dashboard
     ↓
My Class Students
     ↓
Select Student
     ↓
Student Details / Attendance / Academic Records
```

---

# 👨‍🎓 Student Flow

```text
Student Registration
     ↓
Student Login
     ↓
Student Dashboard
     ↓
Profile / Attendance / Results
```

---

# 👨‍👩‍👧 Parent Flow

```text
Parent Registration
     ↓
Parent Login
     ↓
Parent Dashboard
     ↓
Child Information / Attendance / Academic Records
```

---

# 📁 Suggested Project Structure

A typical structure can look like:

```text
EduTrack-Management-System/
│
├── main.py
├── database/
│   └── database files
│
├── assets/
│   ├── images/
│   └── icons/
│
├── modules/
│   ├── admin/
│   ├── teacher/
│   ├── student/
│   └── parent/
│
├── face_recognition/
│
├── requirements.txt
└── README.md
```

> The actual project structure may be different depending on the current implementation.

---

# 🐛 Troubleshooting

### Camera is not opening

Check that:

- Camera permissions are enabled.
- No other application is using the camera.
- OpenCV is installed correctly.

Try:

```bash
pip install --upgrade opencv-python
```

---

### Module Not Found Error

Example:

```text
ModuleNotFoundError
```

Install the missing package using:

```bash
pip install package-name
```

---

### Database Problems

Before modifying the database:

- Keep a backup.
- Do not delete existing records.
- Check that the correct database file is being used.

---

# 🔮 Future Improvements

Possible future improvements include:

- Advanced attendance analytics
- Better reporting
- PDF report generation
- Automated notifications
- Performance dashboards
- Improved face-recognition accuracy
- Backup and restore
- More detailed analytics
- Cloud synchronization

---

# 🤝 Contributing

Contributions and suggestions are welcome.

If you want to improve the project:

1. Fork the repository.
2. Create a new branch.
3. Make your changes.
4. Test the changes.
5. Create a Pull Request.

---

# 📜 License

This project can be used for educational and learning purposes.

Add an appropriate open-source license to the repository if you plan to distribute the project publicly.

---

# 👩‍💻 Project Purpose

EduTrack Management System is designed as an educational software project demonstrating how Python can be used to build a complete role-based management application with:

- GUI development
- Database management
- Attendance management
- Face recognition
- Academic management
- Student management
- Role-based access

The goal is to provide a practical example that students and beginners can study, understand, modify, and extend.

---

## ⭐ If You Find This Project Helpful

If this project helps you learn Python, Tkinter, SQLite, OpenCV, or management-system development, consider giving the repository a ⭐ star and sharing your suggestions.
