from datetime import datetime
from typing import Optional, Any

def calculate_grade_and_status(total_marks: float, max_total: float = 180.0) -> tuple[float, str, str]:
    """
    Calculate overall percentage, grade letter, and Pass/Fail status.
    Default max marks breakdown:
    - Internal: 20
    - Mid-Term: 30
    - Project: 20
    - Viva: 10
    - Final Exam: 100
    Total max = 180
    """
    if max_total <= 0:
        percentage = 0.0
    else:
        percentage = round((total_marks / max_total) * 100.0, 2)
    
    if percentage >= 90.0:
        grade = "A+"
    elif percentage >= 80.0:
        grade = "A"
    elif percentage >= 70.0:
        grade = "B+"
    elif percentage >= 60.0:
        grade = "B"
    elif percentage >= 50.0:
        grade = "C"
    elif percentage >= 40.0:
        grade = "D"
    else:
        grade = "F"
    
    status = "Pass" if percentage >= 40.0 else "Fail"
    return percentage, grade, status

def get_current_date() -> str:
    """Return current date as YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")

def get_current_time() -> str:
    """Return current time as HH:MM:SS."""
    return datetime.now().strftime("%H:%M:%S")

def format_date(date_str: str) -> str:
    """Format date string cleanly."""
    if not date_str:
        return "N/A"
    return str(date_str).strip()

def parse_datetime_helper(t_str: Any, date_str: Any = None) -> Optional[datetime]:
    """Robustly parse time or datetime string given optional date_str."""
    if not t_str or str(t_str).strip() in ("", "--", "None", "NULL"):
        return None
    
    if isinstance(t_str, datetime):
        return t_str

    t_clean = str(t_str).strip()
    now_dt = datetime.now()
    b_date = now_dt.date()

    if date_str and str(date_str).strip() not in ("", "--", "None", "NULL"):
        d_clean = str(date_str).strip()
        for dfmt in ("%Y-%m-%d", "%d-%m-%Y", "%d-%b-%Y", "%Y/%m/%d", "%d/%m/%Y"):
            try:
                b_date = datetime.strptime(d_clean, dfmt).date()
                break
            except ValueError:
                pass

    t_upper = t_clean.upper()
    for tfmt in (
        "%I:%M:%S %p", "%I:%M:%S%p", "%I:%M %p", "%I:%M%p",
        "%H:%M:%S", "%H:%M"
    ):
        try:
            t = datetime.strptime(t_upper, tfmt).time()
            return datetime.combine(b_date, t)
        except ValueError:
            pass

    for dt_fmt in (
        "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %I:%M:%S %p",
        "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %I:%M:%S %p"
    ):
        try:
            return datetime.strptime(t_upper, dt_fmt)
        except ValueError:
            pass

    return None

