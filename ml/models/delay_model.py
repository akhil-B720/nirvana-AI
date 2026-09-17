from datetime import date
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import joblib

class DelayRiskModel:
    """
    Evaluates project timeline slippage probability and estimated delay days
    using mathematical S-curve tracking and statistical regression baseline.
    """

    def __init__(self):
        self.model_name = "DelayRiskModel"
        self.version = "1.0.0"
        self.status = "ACTIVE"
        self.is_supervised = False

    def predict_project(self, project) -> Dict[str, Any]:
        start_d = project.start_date
        exp_d = project.expected_completion_date
        act_d = project.actual_completion_date
        reported_prog = float(project.reported_progress or 0.0)
        
        sanction = float(project.sanction_amount or 0.0)
        expenditure = float(project.expenditure_amount or 0.0)
        utilization = (expenditure / sanction) if sanction > 0 else 0.0

        today = date.today()
        ref_end_date = act_d if act_d else today

        if not start_d or not exp_d:
            return {
                "delay_probability": None,
                "predicted_delay_days": None,
                "confidence": 0.0,
                "model_status": "INSUFFICIENT_DATA",
                "explanation": "Start date or scheduled completion date is missing from project records."
            }

        planned_days = max(1, (exp_d - start_d).days)
        elapsed_days = max(0, (ref_end_date - start_d).days)
        time_ratio = elapsed_days / planned_days

        # S-Curve expected progress at current time ratio
        # Standard logistical curve
        midpoint = 0.5
        k = 6.0
        expected_prog = 100.0 / (1.0 + np.exp(-k * (min(1.5, time_ratio) - midpoint)))
        expected_prog = float(np.clip(expected_prog, 0.0, 100.0))

        # Slippage calculation
        progress_deficit = max(0.0, expected_prog - reported_prog)
        
        # Delay probability mapping
        if act_d:
            # Completed project: deterministic outcome
            actual_days = (act_d - start_d).days
            delayed_days = max(0, actual_days - planned_days)
            delay_prob = 1.0 if delayed_days > 0 else 0.0
            return {
                "delay_probability": float(delay_prob),
                "predicted_delay_days": int(delayed_days),
                "confidence": 95.0,
                "model_status": "HISTORICAL_GROUND_TRUTH",
                "explanation": f"Project completed with actual duration of {actual_days} days vs planned {planned_days} days."
            }

        # Project in progress
        if time_ratio >= 1.0 and reported_prog < 95.0:
            # Overdue
            overdue_days = elapsed_days - planned_days
            delay_prob = min(0.99, 0.75 + (overdue_days / 180.0) * 0.24)
            remaining_work = max(5.0, 100.0 - reported_prog)
            daily_burn_rate = max(0.05, reported_prog / max(1, elapsed_days))
            estimated_delay = int(overdue_days + (remaining_work / daily_burn_rate))
        else:
            # Before target date
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

        # Confidence is higher when more time has elapsed and progress measurements exist
        confidence = round(min(90.0, 50.0 + (time_ratio * 30.0)), 1)

        return {
            "delay_probability": round(float(delay_prob), 2),
            "predicted_delay_days": int(estimated_delay),
            "confidence": float(confidence),
            "model_status": "BASELINE_SCURVE",
            "explanation": f"Elapsed time is {time_ratio*100:.1f}% of planned duration, with {progress_deficit:.1f}% progress deficit against expected construction curve."
        }

    def save(self, filepath: str):
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str):
        return joblib.load(filepath)
