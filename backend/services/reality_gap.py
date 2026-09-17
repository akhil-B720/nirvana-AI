from datetime import date
from typing import Dict, Any, Optional, List
import numpy as np

class RealityGapEngine:
    """
    Core Reality Gap computation engine comparing:
    - EXPECTED REALITY (Engineering S-Curve from timeline)
    - REPORTED REALITY (Contractor administrative claim)
    - OBSERVED REALITY (Physical ground sensors / geotagged photo evidence)
    """

    NOTICE = "This is a prototype/system-defined analytical score and is not an official government metric."
    LEGAL_DISCLAIMER = "AI-generated risk indicators are decision-support signals and do not constitute proof of fraud, corruption, or wrongdoing."

    @classmethod
    def evaluate(cls, project) -> Dict[str, Any]:
        start_d = project.start_date
        exp_d = project.expected_completion_date
        act_d = project.actual_completion_date
        today = date.today()
        ref_end = act_d if act_d else today

        # 1. Temporal metrics
        time_elapsed_ratio: Optional[float] = None
        expected_progress: Optional[float] = None
        expected_lower: Optional[float] = None
        expected_upper: Optional[float] = None

        if start_d and exp_d:
            planned_days = max(1, (exp_d - start_d).days)
            elapsed_days = max(0, (ref_end - start_d).days)
            time_elapsed_ratio = round(min(5.0, elapsed_days / planned_days), 4)

            # Logistical S-Curve for engineering milestones
            if time_elapsed_ratio <= 0.0:
                expected_progress = 0.0
            elif act_d and time_elapsed_ratio >= 1.0:
                expected_progress = 100.0
            else:
                k = 6.0
                midpoint = 0.5
                raw_s = 100.0 / (1.0 + np.exp(-k * (min(1.25, time_elapsed_ratio) - midpoint)))
                expected_progress = round(float(np.clip(raw_s, 0.0, 100.0)), 2)

            expected_lower = round(max(0.0, expected_progress - 15.0), 2)
            expected_upper = round(min(100.0, expected_progress + 15.0), 2)

        # 2. Financial Metrics
        sanction = float(project.sanction_amount or 0.0)
        released = float(project.released_amount or 0.0)
        expenditure = float(project.expenditure_amount or 0.0)
        fin_utilization = round(expenditure / released, 4) if released > 0 else 0.0

        # 3. Reported & Observed Progress
        reported_prog = float(project.reported_progress or 0.0)
        observed_prog: Optional[float] = float(project.observed_progress) if project.observed_progress is not None else None
        obs_status = project.observed_progress_status or ("AI_ESTIMATE" if observed_prog is not None else "NOT_AVAILABLE")

        # 4. Component Gaps
        contributing_factors: List[str] = []
        
        # Financial Progress Gap
        fin_progress_gap = round(abs((fin_utilization * 100.0) - reported_prog), 2)
        if fin_progress_gap > 30.0:
            contributing_factors.append(f"Financial expenditure ({fin_utilization*100:.1f}%) diverges from reported physical progress ({reported_prog:.1f}%)")

        # Time Progress Gap (Schedule slippage)
        time_progress_gap = None
        if expected_progress is not None:
            time_progress_gap = round(max(0.0, expected_progress - reported_prog), 2)
            if time_progress_gap > 20.0:
                contributing_factors.append(f"Physical work lags behind expected schedule milestone by {time_progress_gap:.1f}%")

        # Observed vs Reported Gap
        reported_observed_gap = None
        expected_observed_gap = None
        if observed_prog is not None:
            reported_observed_gap = round(abs(reported_prog - observed_prog), 2)
            if reported_observed_gap > 20.0:
                contributing_factors.append(f"Reality Gap: Reported progress ({reported_prog:.1f}%) significantly exceeds ground-observed progress ({observed_prog:.1f}%)")
            if expected_progress is not None:
                expected_observed_gap = round(abs(expected_progress - observed_prog), 2)
        else:
            contributing_factors.append("Observed physical ground evidence unavailable. Status: NOT_AVAILABLE")

        # 5. Composite Reality Gap Score (0-100)
        # 0-30 NORMAL, 31-60 WATCH, 61-80 HIGH, 81-100 CRITICAL
        active_components = []
        if reported_observed_gap is not None:
            active_components.append((reported_observed_gap, 0.60))
        if time_progress_gap is not None:
            active_components.append((time_progress_gap, 0.20))
        active_components.append((min(100.0, fin_progress_gap), 0.20))

        total_weight = sum(w for _, w in active_components)
        weighted_score = sum(val * (w / total_weight) for val, w in active_components) if total_weight > 0 else 0.0
        
        # If there is a direct ground-truth reality gap, the score must be at least that divergence
        if reported_observed_gap is not None:
            weighted_score = max(weighted_score, reported_observed_gap)

        reality_gap_score = round(float(np.clip(weighted_score, 0.0, 100.0)), 2)

        if reality_gap_score <= 30.0:
            tier = "NORMAL"
        elif reality_gap_score <= 60.0:
            tier = "WATCH"
        elif reality_gap_score <= 80.0:
            tier = "HIGH"
        else:
            tier = "CRITICAL"

        confidence = 90.0 if observed_prog is not None else 60.0

        return {
            "project_id": project.project_id,
            "project_name": project.project_name,
            "expected_progress": expected_progress,
            "expected_lower_bound": expected_lower,
            "expected_upper_bound": expected_upper,
            "reported_progress": reported_prog,
            "observed_progress": observed_prog,
            "observed_progress_status": obs_status,
            "financial_utilization": fin_utilization,
            "time_elapsed_ratio": time_elapsed_ratio,
            "reality_gap_score": reality_gap_score,
            "reality_gap_tier": tier,
            "confidence": confidence,
            "components": {
                "financial_progress_gap": fin_progress_gap,
                "time_progress_gap": time_progress_gap,
                "reported_observed_gap": reported_observed_gap,
                "expected_observed_gap": expected_observed_gap,
                "document_consistency_gap": 0.0
            },
            "contributing_factors": contributing_factors,
            "notice": cls.NOTICE,
            "disclaimer": cls.LEGAL_DISCLAIMER
        }
