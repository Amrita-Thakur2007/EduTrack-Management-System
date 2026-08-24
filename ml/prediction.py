import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any
from ml.train_model import MODEL_PATH, train_and_save_model

class PerformancePredictor:
    """Predicts student performance category & risk using trained Scikit-Learn model."""
    def __init__(self):
        self.model = None
        self._load_or_train_model()

    def _load_or_train_model(self):
        if not os.path.exists(MODEL_PATH):
            train_and_save_model()
        try:
            self.model = joblib.load(MODEL_PATH)
        except Exception as e:
            print("Error loading ML model:", e)
            train_and_save_model()
            self.model = joblib.load(MODEL_PATH)

    def predict_performance(self, 
                            attendance_pct: float, 
                            study_hours: float, 
                            previous_pct: float,
                            internal_marks: float, 
                            mid_term_marks: float, 
                            project_marks: float, 
                            viva_marks: float) -> Dict[str, Any]:
        """
        Predict performance category, estimated percentage, and risk level.
        Excludes Final Exam Marks to prevent data leakage!
        """
        if self.model is None:
            self._load_or_train_model()

        features = pd.DataFrame([{
            'attendance_pct': float(attendance_pct),
            'study_hours': float(study_hours),
            'previous_pct': float(previous_pct),
            'internal_marks': float(internal_marks),
            'mid_term_marks': float(mid_term_marks),
            'project_marks': float(project_marks),
            'viva_marks': float(viva_marks)
        }])

        category = self.model.predict(features)[0]
        
        # Calculate predicted score % based on feature weights
        # Internal(20) + Mid(30) + Project(20) + Viva(10) = 80 max
        subtotal = internal_marks + mid_term_marks + project_marks + viva_marks
        subtotal_pct = (subtotal / 80.0) * 100.0 if subtotal > 0 else 0.0
        
        predicted_score = round(
            subtotal_pct * 0.50 + attendance_pct * 0.25 + previous_pct * 0.15 + (min(study_hours, 10.0) / 10.0 * 100.0) * 0.10,
            1
        )

        # Risk indicator
        if category == 'Needs Improvement' or attendance_pct < 60.0 or subtotal_pct < 45.0:
            risk_level = "High Risk"
            recommendations = "Requires immediate academic counseling, attendance monitoring, and extra tutoring."
        elif category == 'Average' or attendance_pct < 75.0 or subtotal_pct < 60.0:
            risk_level = "Medium Risk"
            recommendations = "Recommended to increase study hours to at least 4 hrs/day and participate in revision classes."
        elif category == 'Good':
            risk_level = "Low Risk"
            recommendations = "Good steady progress. Maintain attendance and focus on weak subjects before final exams."
        else: # Excellent
            risk_level = "Low Risk"
            recommendations = "Outstanding performance. Recommended for advanced projects and peer mentoring."

        return {
            "category": category,
            "predicted_score": min(predicted_score, 99.9),
            "risk_level": risk_level,
            "recommendations": recommendations,
            "feature_breakdown": {
                "attendance": attendance_pct,
                "study_hours": study_hours,
                "previous_pct": previous_pct,
                "mid_term_score": round((mid_term_marks / 30.0) * 100.0 if mid_term_marks else 0.0, 1)
            }
        }
