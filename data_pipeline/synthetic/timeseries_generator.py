# -*- coding: utf-8 -*-
"""
Synthetic Time-Series Progress History Generator.
Creates chronological multi-month progress and expenditure records
for testing timeline progression, delay curves, and historical time machine.
"""

from datetime import date, timedelta
from typing import List, Dict, Any

def generate_progress_history(
    project_id: str,
    start_d: date,
    end_d: date,
    final_progress: float,
    final_expenditure: float,
    status: str,
    anomaly_category: str = "NORMAL"
) -> List[Dict[str, Any]]:
    """
    Generates chronological checkpoint snapshots between start date and completion/today.
    """
    history = []
    total_days = max(30, (end_d - start_d).days)
    num_checkpoints = min(10, max(3, total_days // 60))

    step_days = total_days / num_checkpoints

    for step in range(1, num_checkpoints + 1):
        snap_date = start_d + timedelta(days=int(step * step_days))
        ratio = step / num_checkpoints

        if anomaly_category == "PAYMENT_PROGRESS_MISMATCH":
            # Expenditure jumps early, progress stays low
            step_progress = round(final_progress * (ratio ** 1.8), 1)
            step_exp = round(final_expenditure * (ratio ** 0.5), 1)
        elif anomaly_category == "DELAY_PATTERN":
            # Progress stalls midway
            effective_ratio = min(0.4, ratio)
            step_progress = round(final_progress * (effective_ratio / 0.4), 1)
            step_exp = round(final_expenditure * ratio, 1)
        else:
            # Normal S-curve progression
            s_curve_factor = 1.0 / (1.0 + ( (1.0 - ratio) / max(0.01, ratio) )**1.5)
            step_progress = round(final_progress * s_curve_factor, 1)
            step_exp = round(final_expenditure * s_curve_factor, 1)

        step_status = "COMPLETED" if (step == num_checkpoints and final_progress >= 100.0) else "IN_PROGRESS"

        history.append({
            "project_id": project_id,
            "record_date": snap_date,
            "reported_progress": min(100.0, max(0.0, step_progress)),
            "financial_expenditure": round(min(final_expenditure, max(0.0, step_exp)), 2),
            "status": step_status,
            "data_status": "SYNTHETIC"
        })

    return history
