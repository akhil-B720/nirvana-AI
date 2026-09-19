from datetime import date, datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier


class DelayRiskModel:
    """
    Evaluates project timeline slippage probability and estimated delay days.
    Supports both supervised machine-learning regression on multi-month project
    trajectories and calibrated mathematical construction S-curve baseline fallback.
    """

    FEATURE_NAMES = [
        "planned_days",
        "elapsed_days",
        "time_ratio",
        "reported_progress",
        "utilization_ratio",
        "progress_velocity",
        "progress_deficit"
    ]

    def __init__(self):
        self.model_name = "DelayRiskModel"
        self.version = "2.0.0"
        self.status = "ACTIVE"
        self.is_supervised = False
        self.regressor: Optional[GradientBoostingRegressor] = None
        self.classifier: Optional[GradientBoostingClassifier] = None
        self.metrics: Dict[str, Any] = {}

    @staticmethod
    def _parse_date(d: Any) -> Optional[date]:
        if d is None:
            return None
        if isinstance(d, datetime):
            return d.date()
        if isinstance(d, date):
            return d
        if isinstance(d, str):
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"):
                try:
                    return datetime.strptime(d.strip()[:10], fmt).date()
                except Exception:
                    continue
        return None

    def extract_features(self, project: Any) -> Optional[np.ndarray]:
        """
        Extracts 7-dimensional trajectory and pacing feature vector for a project.
        """
        start_d = self._parse_date(getattr(project, "start_date", None))
        exp_d = self._parse_date(getattr(project, "expected_completion_date", None))
        act_d = self._parse_date(getattr(project, "actual_completion_date", None))

        if not start_d or not exp_d:
            return None

        today = date.today()
        ref_end_date = act_d if act_d else today

        planned_days = max(1, (exp_d - start_d).days)
        elapsed_days = max(0, (ref_end_date - start_d).days)
        time_ratio = float(elapsed_days / planned_days)

        reported_prog = float(getattr(project, "reported_progress", 0.0) or 0.0)
        sanction = float(getattr(project, "sanction_amount", 0.0) or 0.0)
        expenditure = float(getattr(project, "expenditure_amount", 0.0) or 0.0)
        utilization = float(expenditure / sanction) if sanction > 0 else 0.0

        # Logistical expected S-curve
        midpoint = 0.5
        k = 6.0
        expected_prog = 100.0 / (1.0 + np.exp(-k * (min(1.5, time_ratio) - midpoint)))
        expected_prog = float(np.clip(expected_prog, 0.0, 100.0))
        progress_deficit = float(max(0.0, expected_prog - reported_prog))

        progress_velocity = float(reported_prog / max(1, elapsed_days))

        return np.array([
            planned_days,
            elapsed_days,
            time_ratio,
            reported_prog,
            utilization,
            progress_velocity,
            progress_deficit
        ], dtype=float)

    def fit(self, X: np.ndarray, y_days: np.ndarray, y_delayed: np.ndarray) -> Dict[str, Any]:
        """
        Trains supervised Gradient Boosting Regressor (for delay days)
        and Classifier (for delay probability).
        """
        self.regressor = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.08,
            random_state=42
        )
        self.regressor.fit(X, y_days)

        self.classifier = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.08,
            random_state=42
        )
        self.classifier.fit(X, y_delayed)
        self.is_supervised = True
        return {"status": "FITTED", "samples": len(X)}

    def predict_project(self, project) -> Dict[str, Any]:
        start_d = self._parse_date(getattr(project, "start_date", None))
        exp_d = self._parse_date(getattr(project, "expected_completion_date", None))
        act_d = self._parse_date(getattr(project, "actual_completion_date", None))
        reported_prog = float(getattr(project, "reported_progress", 0.0) or 0.0)

        is_synthetic = getattr(project, "data_status", "PUBLIC_VERIFIED") == "SYNTHETIC"
        data_status = getattr(project, "data_status", "PUBLIC_VERIFIED")

        if not start_d or not exp_d:
            return {
                "delay_probability": None,
                "predicted_delay_days": None,
                "confidence": 0.0,
                "model_status": "INSUFFICIENT_DATA",
                "data_status": data_status,
                "is_synthetic": is_synthetic,
                "explanation": "Start date or scheduled completion date is missing from project records."
            }

        planned_days = max(1, (exp_d - start_d).days)
        today = date.today()
        ref_end_date = act_d if act_d else today
        elapsed_days = max(0, (ref_end_date - start_d).days)
        time_ratio = elapsed_days / planned_days

        # Deterministic outcome if project is completed
        if act_d:
            actual_days = (act_d - start_d).days
            delayed_days = max(0, actual_days - planned_days)
            delay_prob = 1.0 if delayed_days > 0 else 0.0
            return {
                "delay_probability": float(delay_prob),
                "predicted_delay_days": int(delayed_days),
                "confidence": 95.0,
                "model_status": "HISTORICAL_GROUND_TRUTH",
                "data_status": data_status,
                "is_synthetic": is_synthetic,
                "explanation": f"Project completed with actual duration of {actual_days} days vs planned {planned_days} days."
            }

        # If supervised model is available and project is ongoing
        feat = self.extract_features(project)
        if self.is_supervised and self.regressor is not None and self.classifier is not None and feat is not None:
            x_vec = feat.reshape(1, -1)
            pred_days = max(0, int(round(self.regressor.predict(x_vec)[0])))
            pred_prob = float(np.clip(self.classifier.predict_proba(x_vec)[0][1], 0.02, 0.98))
            confidence = round(min(92.0, 55.0 + (min(1.0, time_ratio) * 35.0)), 1)
            progress_deficit = feat[6]

            return {
                "delay_probability": round(pred_prob, 2),
                "predicted_delay_days": int(pred_days),
                "confidence": float(confidence),
                "model_status": "SUPERVISED_REGRESSION",
                "data_status": data_status,
                "is_synthetic": is_synthetic,
                "explanation": f"Supervised ML projection: elapsed time {time_ratio*100:.1f}% of planned duration with {progress_deficit:.1f}% progress deficit."
            }

        # Fallback: S-Curve heuristic calculation
        midpoint = 0.5
        k = 6.0
        expected_prog = 100.0 / (1.0 + np.exp(-k * (min(1.5, time_ratio) - midpoint)))
        expected_prog = float(np.clip(expected_prog, 0.0, 100.0))
        progress_deficit = max(0.0, expected_prog - reported_prog)

        if time_ratio >= 1.0 and reported_prog < 95.0:
            overdue_days = elapsed_days - planned_days
            delay_prob = min(0.99, 0.75 + (overdue_days / 180.0) * 0.24)
            remaining_work = max(5.0, 100.0 - reported_prog)
            daily_burn_rate = max(0.05, reported_prog / max(1, elapsed_days))
            estimated_delay = int(overdue_days + (remaining_work / daily_burn_rate))
        else:
            delay_prob = min(0.95, (progress_deficit / 100.0) * 0.85 + (max(0.0, time_ratio - 0.7) * 0.3))
            remaining_days = max(1, planned_days - elapsed_days)
            remaining_prog = max(0.0, 100.0 - reported_prog)
            current_speed = (reported_prog / elapsed_days) if elapsed_days > 0 else 0.0
            needed_speed = (remaining_prog / remaining_days)

            if current_speed > 0 and needed_speed > current_speed:
                projected_total_days = elapsed_days + (remaining_prog / current_speed)
                estimated_delay = max(0, int(projected_total_days - planned_days))
            else:
                estimated_delay = 0

        confidence = round(min(90.0, 50.0 + (time_ratio * 30.0)), 1)

        return {
            "delay_probability": round(float(delay_prob), 2),
            "predicted_delay_days": int(estimated_delay),
            "confidence": float(confidence),
            "model_status": "BASELINE_SCURVE",
            "data_status": data_status,
            "is_synthetic": is_synthetic,
            "explanation": f"Elapsed time is {time_ratio*100:.1f}% of planned duration, with {progress_deficit:.1f}% progress deficit against expected construction curve."
        }

    def save(self, filepath: str):
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str):
        return joblib.load(filepath)

