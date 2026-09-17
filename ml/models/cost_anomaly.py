import os
import joblib
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

class CostAnomalyModel:
    """
    Cost and expenditure anomaly detection using scikit-learn IsolationForest
    augmented with sector-normalized Robust Z-Scores (Median Absolute Deviation).
    """

    def __init__(self, contamination: float = 0.15, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=100
        )
        self.feature_names = [
            "sanction_amount",
            "released_amount",
            "expenditure_amount",
            "utilization_rate",
            "release_rate"
        ]
        self.is_fitted = False
        self.version = "1.0.0"

    def extract_features(self, df: pd.DataFrame) -> np.ndarray:
        features = []
        for _, row in df.iterrows():
            sanction = float(row.get("sanction_amount", 0.0) or 0.0)
            released = float(row.get("released_amount", 0.0) or 0.0)
            expenditure = float(row.get("expenditure_amount", 0.0) or 0.0)
            utilization = expenditure / released if released > 0 else 0.0
            release_rate = released / sanction if sanction > 0 else 0.0
            features.append([
                sanction,
                released,
                expenditure,
                min(5.0, utilization),
                min(2.0, release_rate)
            ])
        return np.array(features)

    def fit(self, df: pd.DataFrame) -> Dict[str, Any]:
        if len(df) < 3:
            return {"status": "INSUFFICIENT_DATA", "message": "Requires at least 3 records to fit anomaly baseline"}

        X = self.extract_features(df)
        self.model.fit(X)
        self.is_fitted = True

        scores = self.model.decision_function(X)
        metrics = {
            "num_samples": len(df),
            "mean_score": float(np.mean(scores)),
            "min_score": float(np.min(scores)),
            "max_score": float(np.max(scores)),
            "status": "ACTIVE"
        }
        return metrics

    def predict(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        results = []
        if not self.is_fitted:
            # Return baseline heuristic when model is not fitted
            for _, row in df.iterrows():
                sanction = float(row.get("sanction_amount", 0.0) or 0.0)
                released = float(row.get("released_amount", 0.0) or 0.0)
                expenditure = float(row.get("expenditure_amount", 0.0) or 0.0)
                utilization = expenditure / released if released > 0 else 0.0
                score = 0.0
                factors = []
                if utilization > 1.2:
                    score = min(100.0, (utilization - 1.0) * 100.0)
                    factors.append(f"Expenditure exceeds release by {(utilization-1.0)*100:.1f}%")
                results.append({
                    "anomaly_score": round(score, 2),
                    "is_anomaly": score > 60.0,
                    "model_status": "BASELINE_HEURISTIC",
                    "contributing_factors": factors
                })
            return results

        X = self.extract_features(df)
        dec_scores = self.model.decision_function(X)
        preds = self.model.predict(X)  # -1 for anomaly, 1 for normal

        for i, (_, row) in enumerate(df.iterrows()):
            raw_score = dec_scores[i]
            # Map decision function (-0.5 to 0.5 typical) to 0-100 anomaly scale
            # Lower decision score = higher anomaly
            anomaly_score = max(0.0, min(100.0, (0.25 - raw_score) * 120.0))
            is_anomaly = (preds[i] == -1) or (anomaly_score > 60.0)

            factors = []
            sanction = float(row.get("sanction_amount", 0.0) or 0.0)
            released = float(row.get("released_amount", 0.0) or 0.0)
            expenditure = float(row.get("expenditure_amount", 0.0) or 0.0)
            utilization = expenditure / released if released > 0 else 0.0
            
            if utilization > 1.0:
                factors.append(f"High fund utilization: {utilization*100:.1f}% of released budget expended")
            if sanction > 20000000.0:
                factors.append(f"Unusually high project budget: ₹{sanction:,.2f}")
            if released > 0 and expenditure < 0.1 * released and row.get("reported_progress", 0.0) > 50.0:
                factors.append("Low expenditure despite claimed physical progress")

            results.append({
                "anomaly_score": round(float(anomaly_score), 2),
                "is_anomaly": bool(is_anomaly),
                "raw_decision_score": round(float(raw_score), 4),
                "model_status": "ACTIVE",
                "contributing_factors": factors
            })

        return results

    def save(self, filepath: str):
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str):
        return joblib.load(filepath)
