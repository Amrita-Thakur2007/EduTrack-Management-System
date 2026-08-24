# Student Management & Performance Prediction System

A complete desktop application built in Python using **Tkinter (ttk)**, **OpenCV**, **SQLite**, **Scikit-Learn**, **Pandas**, **NumPy**, and **Matplotlib**.

---

## 🌟 Overview & Key Features

1. **Role-Based Portals**:
   - **Admin**: Full system management (Student & Teacher CRUD, system analytics, notifications, CSV exports).
   - **Teacher**: Marks entry & updates, attendance scanner, student directory, class ML predictions.
   - **Student**: Personal profile, attendance %, subject marks, grade calculation, ML performance prediction, visual charts.
   - **Parent**: Strictly restricted to viewing linked child's profile, attendance logs, marks evaluation, ML prediction, and notifications.

2. **Facial Recognition Attendance Engine**:
   - Automated attendance logging using OpenCV Haar Cascades and normalized ROI feature matching.
   - Duplicate attendance prevention for the same date.
   - Handles missing camera hardware gracefully with fallback mock testing.

3. **Machine Learning Performance Predictor**:
   - Real Scikit-Learn `RandomForestClassifier` trained on academic features (Attendance %, Study Hours, Previous %, Internal Marks, Mid-Term Marks, Project Marks, Viva Marks).
   - Excludes Final Exam Marks to prevent data leakage.
   - Predicts performance category ('Excellent', 'Good', 'Average', 'Needs Improvement') and academic risk assessment ('Low Risk', 'Medium Risk', 'High Risk').

4. **Security & Data Integrity**:
   - Passwords stored securely using PBKDF2 SHA256 hashing with individual 16-byte random salts.
   - Manual password entry required during registration (No auto-generated passwords).
   - Parameterized SQLite queries preventing SQL injection.

---

## 🛠️ System Requirements & Installation

- **Python**: 3.10+
- **Libraries**: `opencv-python`, `pillow`, `pandas`, `numpy`, `matplotlib`, `scikit-learn`, `joblib`

### Installation Steps

1. Clone or navigate to project directory:
   ```bash
   cd NSMS
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Launch Application:
   ```bash
   python main.py
   ```

---

## 🔑 Initial Demo Credentials (Pre-seeded)

- **Admin Portal**:
  - Username: `admin`
  - Password: `admin123`
- **Teacher Portal**:
  - Username: `teacher1`
  - Password: `tch123`
- **Student Portal**:
  - Username: `student1`
  - Password: `stu123`
- **Parent Portal**:
  - Username: `parent1`
  - Password: `par123`

*Note: You can also create new Teacher, Student, or Parent accounts directly from the Account Registration forms.*

---

## 📷 How Face Attendance Works

1. **Registration**: Open Student Management -> Select Student -> Click **Register Face**. Position face in green frame -> Click **Capture & Save**.
2. **Attendance Scanner**: Click **Open Face Scanner**. When a registered student faces the camera, the system matches their ROI encoding, logs attendance as 'Present' with current timestamp, and enforces once-per-day logging.

---

## 🤖 How ML Prediction Works

The ML model reads student attendance %, daily study hours, previous academic percentage, and term marks (Internal, Mid-Term, Project, Viva) to compute a predicted final performance percentage and assign a risk classification with actionable study recommendations.
