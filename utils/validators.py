import re

def validate_email(email: str) -> bool:
    """Validate email address format."""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email.strip()) is not None

def validate_phone(phone: str) -> bool:
    """Validate phone number (must contain exactly 10 numeric digits)."""
    if not phone:
        return False
    digits = phone.strip()
    return digits.isdigit() and len(digits) == 10

def validate_student_id(student_id: str) -> bool:
    """Validate student ID format (non-empty alphanumeric)."""
    if not student_id:
        return False
    return len(student_id.strip()) >= 3 and bool(re.match(r'^[a-zA-Z0-9_\-]+$', student_id.strip()))

def validate_marks(internal, mid_term, project, viva, final_exam=100) -> tuple[bool, str]:
    """
    Validate marks against allowed maximums:
    - Internal: max 20
    - Mid-Term: max 30
    - Project: max 20
    - Viva: max 10
    - Final Exam: max 100
    """
    try:
        val_int = float(internal) if internal is not None and str(internal).strip() != "" else 0.0
        val_mid = float(mid_term) if mid_term is not None and str(mid_term).strip() != "" else 0.0
        val_proj = float(project) if project is not None and str(project).strip() != "" else 0.0
        val_viva = float(viva) if viva is not None and str(viva).strip() != "" else 0.0
        val_final = float(final_exam) if final_exam is not None and str(final_exam).strip() != "" else 0.0

        if val_int < 0 or val_int > 20:
            return False, "Internal Marks must be between 0 and 20."
        if val_mid < 0 or val_mid > 30:
            return False, "Mid-Term Marks must be between 0 and 30."
        if val_proj < 0 or val_proj > 20:
            return False, "Project Marks must be between 0 and 20."
        if val_viva < 0 or val_viva > 10:
            return False, "Viva Marks must be between 0 and 10."
        if val_final < 0 or val_final > 100:
            return False, "Final Exam Marks must be between 0 and 100."

        return True, ""
    except ValueError:
        return False, "Marks must be valid numeric values."

def validate_study_hours(hours) -> tuple[bool, str]:
    """Validate daily study hours (0 to 24)."""
    try:
        val = float(hours)
        if 0.0 <= val <= 24.0:
            return True, ""
        return False, "Study Hours must be between 0 and 24."
    except ValueError:
        return False, "Study Hours must be a valid number."
