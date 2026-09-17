from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np
from datetime import datetime

class DataQualityEngine:
    """
    Evaluates input infrastructure project datasets for consistency,
    domain boundaries, coordinate validity, and temporal coherence.
    Computes deterministic data_quality_score (0-100).
    """

    @staticmethod
    def validate_dataset(df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], float]:
        issues: List[Dict[str, Any]] = []
        total_rows = len(df)
        if total_rows == 0:
            return [{"issue_type": "EMPTY_DATASET", "severity": "CRITICAL", "details": "Dataset contains 0 rows"}], 0.0

        penalty_points = 0.0
        seen_ids = set()

        for idx, row in df.iterrows():
            p_id = str(row.get("project_id", "")).strip()
            
            # 1. Project ID validation
            if not p_id or p_id.lower() in ("nan", "none", "null"):
                issues.append({
                    "project_id": None,
                    "row_index": idx,
                    "issue_type": "INVALID_PROJECT_ID",
                    "severity": "CRITICAL",
                    "details": f"Row {idx} is missing a unique project_id",
                    "original_value": str(row.get("project_id"))
                })
                penalty_points += 5.0
            elif p_id in seen_ids:
                issues.append({
                    "project_id": p_id,
                    "row_index": idx,
                    "issue_type": "DUPLICATE_ID",
                    "severity": "CRITICAL",
                    "details": f"Duplicate project_id '{p_id}' detected at row {idx}",
                    "original_value": p_id
                })
                penalty_points += 4.0
            else:
                seen_ids.add(p_id)

            # 2. Coordinates validation
            lat = row.get("latitude")
            lon = row.get("longitude")
            if pd.notna(lat):
                try:
                    lat_f = float(lat)
                    if lat_f < -90.0 or lat_f > 90.0 or (lat_f == 0.0 and (lon is None or float(lon) == 0.0)):
                        issues.append({
                            "project_id": p_id,
                            "row_index": idx,
                            "issue_type": "INVALID_COORDINATES",
                            "severity": "ERROR",
                            "details": f"Latitude {lat_f} is out of valid bounds [-90, 90]",
                            "original_value": str(lat)
                        })
                        penalty_points += 2.0
                except (ValueError, TypeError):
                    issues.append({
                        "project_id": p_id,
                        "row_index": idx,
                        "issue_type": "INVALID_COORDINATES",
                        "severity": "ERROR",
                        "details": f"Unparseable latitude '{lat}'",
                        "original_value": str(lat)
                    })
                    penalty_points += 2.0

            if pd.notna(lon):
                try:
                    lon_f = float(lon)
                    if lon_f < -180.0 or lon_f > 180.0:
                        issues.append({
                            "project_id": p_id,
                            "row_index": idx,
                            "issue_type": "INVALID_COORDINATES",
                            "severity": "ERROR",
                            "details": f"Longitude {lon_f} is out of valid bounds [-180, 180]",
                            "original_value": str(lon)
                        })
                        penalty_points += 2.0
                except (ValueError, TypeError):
                    issues.append({
                        "project_id": p_id,
                        "row_index": idx,
                        "issue_type": "INVALID_COORDINATES",
                        "severity": "ERROR",
                        "details": f"Unparseable longitude '{lon}'",
                        "original_value": str(lon)
                    })
                    penalty_points += 2.0

            # 3. Financial Non-negativity & Inconsistencies
            sanction = float(row.get("sanction_amount", 0.0) or 0.0)
            released = float(row.get("released_amount", 0.0) or 0.0)
            expenditure = float(row.get("expenditure_amount", 0.0) or 0.0)

            if sanction < 0:
                issues.append({
                    "project_id": p_id,
                    "row_index": idx,
                    "issue_type": "NEGATIVE_FINANCIAL_VALUE",
                    "severity": "ERROR",
                    "details": f"Sanction amount {sanction} cannot be negative",
                    "original_value": str(sanction)
                })
                penalty_points += 3.0

            if released < 0:
                issues.append({
                    "project_id": p_id,
                    "row_index": idx,
                    "issue_type": "NEGATIVE_FINANCIAL_VALUE",
                    "severity": "ERROR",
                    "details": f"Released amount {released} cannot be negative",
                    "original_value": str(released)
                })
                penalty_points += 3.0

            if expenditure < 0:
                issues.append({
                    "project_id": p_id,
                    "row_index": idx,
                    "issue_type": "NEGATIVE_FINANCIAL_VALUE",
                    "severity": "ERROR",
                    "details": f"Expenditure amount {expenditure} cannot be negative",
                    "original_value": str(expenditure)
                })
                penalty_points += 3.0

            # Inconsistency: Expenditure substantially exceeds released funds
            if released > 0 and expenditure > released * 1.5:
                issues.append({
                    "project_id": p_id,
                    "row_index": idx,
                    "issue_type": "EXPENDITURE_INCONSISTENCY",
                    "severity": "WARNING",
                    "details": f"Expenditure (₹{expenditure:,.2f}) exceeds released amount (₹{released:,.2f}) by >50%",
                    "original_value": f"exp={expenditure}, rel={released}"
                })
                penalty_points += 1.5

            # 4. Progress bounds [0, 100]
            rep_prog = row.get("reported_progress")
            if pd.notna(rep_prog):
                try:
                    prog_f = float(rep_prog)
                    if prog_f < 0.0 or prog_f > 100.0:
                        issues.append({
                            "project_id": p_id,
                            "row_index": idx,
                            "issue_type": "PROGRESS_OUT_OF_BOUNDS",
                            "severity": "ERROR",
                            "details": f"Reported progress {prog_f}% outside valid range [0, 100]",
                            "original_value": str(rep_prog)
                        })
                        penalty_points += 2.5
                except (ValueError, TypeError):
                    issues.append({
                        "project_id": p_id,
                        "row_index": idx,
                        "issue_type": "PROGRESS_OUT_OF_BOUNDS",
                        "severity": "ERROR",
                        "details": f"Unparseable reported progress '{rep_prog}'",
                        "original_value": str(rep_prog)
                    })
                    penalty_points += 2.0

            # 5. Date Coherence: Start, Expected, Actual
            start_d = row.get("start_date")
            act_comp_d = row.get("actual_completion_date")
            if pd.notna(start_d) and pd.notna(act_comp_d):
                try:
                    s_dt = pd.to_datetime(start_d)
                    c_dt = pd.to_datetime(act_comp_d)
                    if c_dt < s_dt:
                        issues.append({
                            "project_id": p_id,
                            "row_index": idx,
                            "issue_type": "COMPLETION_BEFORE_START",
                            "severity": "ERROR",
                            "details": f"Actual completion date ({c_dt.strftime('%Y-%m-%d')}) precedes start date ({s_dt.strftime('%Y-%m-%d')})",
                            "original_value": f"start={start_d}, comp={act_comp_d}"
                        })
                        penalty_points += 3.0
                except Exception:
                    pass

        # Calculate score: baseline 100, normalized by row count
        max_possible_penalty = total_rows * 10.0
        normalized_loss = (penalty_points / max_possible_penalty) * 100.0 if max_possible_penalty > 0 else 0.0
        score = max(0.0, round(100.0 - normalized_loss, 2))

        return issues, score
