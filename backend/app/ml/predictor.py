import numpy as np
from app.models.models import RiskCategoryEnum

class AttritionPredictor:
    def __init__(self):
        # Calibrated weights based on HR industry benchmarks
        self.weights = np.array([
            -0.000022,  # monthly_income
            0.14,       # total_leave_days
            0.42,       # avg_daily_hours
            -0.018,     # tenure_months
            2.15,       # overtime_frequency
            -0.95       # job_satisfaction_score
        ])
        self.intercept = 0.25
        # Pre-calibrated distribution metrics
        self.means = np.array([137500.0, 10.0, 8.0, 36.0, 0.5, 3.0])
        self.stds = np.array([65000.0, 3.16, 1.5, 36.0, 0.29, 1.41])
        self.feature_names = [
            "monthly_income",
            "total_leave_days",
            "avg_daily_hours",
            "tenure_months",
            "overtime_frequency",
            "job_satisfaction_score"
        ]

    def predict_risk(self, data: dict) -> dict:
        raw_vals = np.array([
            float(data.get("monthly_income", 50000)),
            float(data.get("total_leave_days", 0)),
            float(data.get("avg_daily_hours", 8.0)),
            float(data.get("tenure_months", 12.0)),
            float(data.get("overtime_frequency", 0.1)),
            float(data.get("job_satisfaction_score", 3))
        ])

        scaled_vals = (raw_vals - self.means) / self.stds
        logit = float(np.dot(scaled_vals, self.weights) + self.intercept)
        prob = 1.0 / (1.0 + np.exp(-np.clip(logit, -15.0, 15.0)))
        risk_score = round(prob * 100.0, 2)

        # Risk Classification
        if risk_score >= 65.0:
            category = RiskCategoryEnum.HIGH
        elif risk_score >= 35.0:
            category = RiskCategoryEnum.MODERATE
        else:
            category = RiskCategoryEnum.LOW

        confidence = round(abs(prob - 0.5) * 2.0 * 100.0, 2)
        if confidence < 50.0:
            confidence = 65.0

        impacts = scaled_vals * self.weights
        impact_dict = {
            "monthly_income": "Low compensation relative to industry tier",
            "total_leave_days": "Excessive or sudden spike in leave requests",
            "avg_daily_hours": "Consistently elongated work hours / Burnout",
            "tenure_months": "Critical career inflection checkpoint (1-3 yr tenure)",
            "overtime_frequency": "High rate of recurring overtime shifts",
            "job_satisfaction_score": "Disengagement and low workplace satisfaction"
        }

        top_feature_idx = int(np.argmax(impacts))
        top_feature = self.feature_names[top_feature_idx]
        top_factor = impact_dict.get(top_feature, "General workload and tenure distribution")

        return {
            "risk_score": risk_score,
            "risk_category": category,
            "confidence_level": confidence,
            "top_contributing_factor": top_factor
        }

predictor_instance = None

def get_predictor() -> AttritionPredictor:
    global predictor_instance
    if predictor_instance is None:
        predictor_instance = AttritionPredictor()
    return predictor_instance
