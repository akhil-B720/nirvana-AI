import re
from typing import Optional
import pandas as pd
import numpy as np

class DataNormalizer:
    """
    Standardizes schema, types, sectors, project categories, and monetary values.
    """

    PROJECT_TYPE_MAPPINGS = {
        r"bridge|flyover|overbridge|subway": "BRIDGE",
        r"build|school|hospital|hall|shed|anganwadi|shelter|center|centre|room|toilet|complex": "BUILDING",
        r"road|pathway|cc road|bt road|street|lane|culvert": "ROAD",
        r"water|tank|borewell|piped|tubewell|filtration|handpump|reservoir": "WATER_TANK",
        r"drain|drainage|sewer|gutter|nullah": "DRAINAGE",
        r"community|samudayik|panchayat|kalyan": "COMMUNITY_HALL",
    }

    @classmethod
    def normalize_project_type(cls, raw_type: Optional[str], project_name: Optional[str] = "") -> str:
        text = f"{raw_type or ''} {project_name or ''}".lower()
        for pattern, standard_type in cls.PROJECT_TYPE_MAPPINGS.items():
            if re.search(pattern, text):
                return standard_type
        return "OTHER"

    @staticmethod
    def clean_currency(val) -> float:
        if pd.isna(val):
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).replace("₹", "").replace(",", "").replace("Rs.", "").strip()
        try:
            return max(0.0, float(val_str))
        except ValueError:
            return 0.0

    @staticmethod
    def clean_date(val) -> Optional[str]:
        if pd.isna(val) or not str(val).strip():
            return None
        try:
            dt = pd.to_datetime(val, errors="coerce")
            if pd.isna(dt):
                return None
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return None

    @classmethod
    def normalize_dataframe(cls, df: pd.DataFrame) -> pd.DataFrame:
        norm_df = df.copy()

        # Ensure core columns exist
        for col in ["project_id", "project_name", "project_type", "state", "district"]:
            if col not in norm_df.columns:
                norm_df[col] = ""

        # Normalize project_type
        norm_df["project_type"] = norm_df.apply(
            lambda r: cls.normalize_project_type(r.get("project_type"), r.get("project_name")),
            axis=1
        )

        # Monetary fields
        for f_col in ["sanction_amount", "released_amount", "expenditure_amount"]:
            if f_col in norm_df.columns:
                norm_df[f_col] = norm_df[f_col].apply(cls.clean_currency)
            else:
                norm_df[f_col] = 0.0

        # Dates
        for d_col in ["start_date", "expected_completion_date", "actual_completion_date"]:
            if d_col in norm_df.columns:
                norm_df[d_col] = norm_df[d_col].apply(cls.clean_date)
            else:
                norm_df[d_col] = None

        # Coordinates
        for c_col in ["latitude", "longitude"]:
            if c_col in norm_df.columns:
                norm_df[c_col] = pd.to_numeric(norm_df[c_col], errors="coerce")
            else:
                norm_df[c_col] = None

        # Progress
        if "reported_progress" in norm_df.columns:
            norm_df["reported_progress"] = pd.to_numeric(norm_df["reported_progress"], errors="coerce").fillna(0.0)
            norm_df["reported_progress"] = norm_df["reported_progress"].clip(0.0, 100.0)
        else:
            norm_df["reported_progress"] = 0.0

        if "observed_progress" in norm_df.columns:
            norm_df["observed_progress"] = pd.to_numeric(norm_df["observed_progress"], errors="coerce")
        else:
            norm_df["observed_progress"] = None

        return norm_df
