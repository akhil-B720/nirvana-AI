from datetime import datetime, date
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

class FeatureExtractor:
    """
    Derives engineering and analytical metrics from project financial,
    temporal, and physical attributes.
    """

    @staticmethod
    def calculate_project_features(p) -> Dict[str, Any]:
        features = {}

        # 1. Financial Ratios
        sanction = float(p.sanction_amount or 0.0)
        released = float(p.released_amount or 0.0)
        expenditure = float(p.expenditure_amount or 0.0)

        features["sanction_amount"] = sanction
        features["released_amount"] = released
        features["expenditure_amount"] = expenditure

        features["utilization_rate"] = round(expenditure / released, 4) if released > 0 else 0.0
        features["release_rate"] = round(released / sanction, 4) if sanction > 0 else 0.0
        features["expenditure_rate"] = round(expenditure / sanction, 4) if sanction > 0 else 0.0

        # 2. Temporal Ratios
        start_d = p.start_date
        exp_d = p.expected_completion_date
        act_d = p.actual_completion_date

        today = date.today()
        ref_end_date = act_d if act_d else today

        if start_d and exp_d:
            planned_days = max(1, (exp_d - start_d).days)
            elapsed_days = max(0, (ref_end_date - start_d).days)
            features["planned_duration_days"] = planned_days
            features["elapsed_days"] = elapsed_days
            features["time_elapsed_ratio"] = round(min(5.0, elapsed_days / planned_days), 4)
        else:
            features["planned_duration_days"] = None
            features["elapsed_days"] = None
            features["time_elapsed_ratio"] = None

        # 3. Expected Progress via Standard Construction S-Curve Model
        # S-Curve: P_E = 100 / (1 + exp(-10 * (t - 0.5)))
        t_ratio = features["time_elapsed_ratio"]
        if t_ratio is not None:
            if t_ratio <= 0.0:
                exp_prog = 0.0
            elif t_ratio >= 1.0 and act_d:
                exp_prog = 100.0
            else:
                # S-curve approximation
                k = 6.0
                midpoint = 0.5
                exp_prog = 100.0 / (1.0 + np.exp(-k * (min(1.2, t_ratio) - midpoint)))
                exp_prog = round(float(np.clip(exp_prog, 0.0, 100.0)), 2)
            features["expected_progress"] = exp_prog
            features["expected_lower_bound"] = round(max(0.0, exp_prog - 15.0), 2)
            features["expected_upper_bound"] = round(min(100.0, exp_prog + 15.0), 2)
        else:
            features["expected_progress"] = None
            features["expected_lower_bound"] = None
            features["expected_upper_bound"] = None

        # 4. Progress Alignment
        rep_prog = float(p.reported_progress or 0.0)
        features["reported_progress"] = rep_prog
        features["observed_progress"] = float(p.observed_progress) if p.observed_progress is not None else None

        # Gaps
        # Financial Progress Gap: Expenditure ratio vs physical completion ratio
        features["financial_progress_gap"] = round(abs(features["utilization_rate"] * 100.0 - rep_prog), 2)

        # Time Progress Gap (Slippage)
        if features["expected_progress"] is not None:
            features["time_progress_gap"] = round(max(0.0, features["expected_progress"] - rep_prog), 2)
        else:
            features["time_progress_gap"] = None

        # Observed Reality Gap
        if features["observed_progress"] is not None:
            features["reported_observed_gap"] = round(abs(rep_prog - features["observed_progress"]), 2)
            if features["expected_progress"] is not None:
                features["expected_observed_gap"] = round(abs(features["expected_progress"] - features["observed_progress"]), 2)
            else:
                features["expected_observed_gap"] = None
        else:
            features["reported_observed_gap"] = None
            features["expected_observed_gap"] = None

        return features
