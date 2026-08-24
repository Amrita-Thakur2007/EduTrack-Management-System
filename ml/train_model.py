import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model")
MODEL_PATH = os.path.join(MODEL_DIR, "student_model.joblib")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CSV_PATH = os.path.join(DATA_DIR, "ml_training_data.csv")

def generate_sample_dataset(num_samples: int = 500) -> pd.DataFrame:
    """
    Generate synthetic dataset for training model if DB records are sparse.
    Features:
    - attendance_pct (0.0 - 100.0)
    - study_hours (0.5 - 12.0)
    - previous_pct (35.0 - 98.0)
    - internal_marks (0.0 - 20.0)
    - mid_term_marks (0.0 - 30.0)
    - project_marks (0.0 - 20.0)
    - viva_marks (0.0 - 10.0)
    
    Target:
    - performance_category: 'Excellent', 'Good', 'Average', 'Needs Improvement'
    """
    np.random.seed(42)
    
    att = np.random.uniform(40, 100, num_samples)
    study = np.random.uniform(1, 10, num_samples)
    prev = np.random.uniform(40, 95, num_samples)
    
    internal = np.clip(att * 0.15 + np.random.normal(3, 2, num_samples), 0, 20)
    mid_term = np.clip(prev * 0.25 + study * 0.8 + np.random.normal(3, 3, num_samples), 0, 30)
    project = np.clip(internal * 0.7 + study * 0.6 + np.random.normal(2, 2, num_samples), 0, 20)
    viva = np.clip(mid_term * 0.25 + np.random.normal(1, 1, num_samples), 0, 10)

    # Weighted score before final exam
    # Normalized score out of 80 (Internal 20 + Mid 30 + Proj 20 + Viva 10)
    term_score = (internal + mid_term + project + viva) / 80.0 * 100.0
    overall_potential = term_score * 0.5 + att * 0.25 + prev * 0.15 + (study / 10.0 * 100) * 0.10

    categories = []
    for score in overall_potential:
        if score >= 82.0:
            categories.append('Excellent')
        elif score >= 68.0:
            categories.append('Good')
        elif score >= 52.0:
            categories.append('Average')
        else:
            categories.append('Needs Improvement')

    df = pd.DataFrame({
        'attendance_pct': np.round(att, 1),
        'study_hours': np.round(study, 1),
        'previous_pct': np.round(prev, 1),
        'internal_marks': np.round(internal, 1),
        'mid_term_marks': np.round(mid_term, 1),
        'project_marks': np.round(project, 1),
        'viva_marks': np.round(viva, 1),
        'performance_category': categories
    })

    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(CSV_PATH, index=False)
    return df

def train_and_save_model(df: pd.DataFrame = None) -> tuple[float, str]:
    """Train RandomForest model and save to disk."""
    if df is None:
        if not os.path.exists(CSV_PATH):
            df = generate_sample_dataset()
        else:
            df = pd.read_csv(CSV_PATH)

    feature_cols = [
        'attendance_pct', 'study_hours', 'previous_pct',
        'internal_marks', 'mid_term_marks', 'project_marks', 'viva_marks'
    ]
    
    X = df[feature_cols]
    y = df['performance_category']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred)

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    print(f"ML Model Trained Successfully! Accuracy: {acc * 100:.2f}%")
    return acc, report

if __name__ == "__main__":
    train_and_save_model()
