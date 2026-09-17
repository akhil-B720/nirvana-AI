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

    STATE_CENTROIDS = {
        "Andhra Pradesh": (15.9129, 79.7400),
        "Arunachal Pradesh": (28.2180, 94.7278),
        "Assam": (26.2006, 92.9376),
        "Bihar": (25.0961, 85.3131),
        "Chhattisgarh": (21.2787, 81.8661),
        "Goa": (15.2993, 74.1240),
        "Gujarat": (22.2587, 71.1924),
        "Haryana": (29.0588, 76.0856),
        "Himachal Pradesh": (31.1048, 77.1734),
        "Jharkhand": (23.6102, 85.2799),
        "Karnataka": (15.3173, 75.7139),
        "Kerala": (10.8505, 76.2711),
        "Madhya Pradesh": (22.9734, 78.6569),
        "Maharashtra": (19.7515, 75.7139),
        "Manipur": (24.6637, 93.9063),
        "Meghalaya": (25.4670, 91.3662),
        "Mizoram": (23.1645, 92.9376),
        "Nagaland": (26.1584, 94.5624),
        "Odisha": (20.9517, 85.0985),
        "Punjab": (31.1471, 75.3412),
        "Rajasthan": (27.0238, 74.2179),
        "Sikkim": (27.5330, 88.5122),
        "Tamil Nadu": (11.1271, 78.6569),
        "Telangana": (18.1124, 79.0193),
        "Tripura": (23.9408, 91.9882),
        "Uttar Pradesh": (26.8467, 80.9462),
        "Uttarakhand": (30.0668, 79.0193),
        "West Bengal": (22.9868, 87.8550),
        "Delhi": (28.7041, 77.1025),
        "Jammu and Kashmir": (33.7782, 76.5762),
        "Ladakh": (34.1526, 77.5771),
        "Puducherry": (11.9416, 79.8083),
        "Chandigarh": (30.7333, 76.7794),
    }

    @classmethod
    def _normalize_mospi_export(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms raw MoSPI portal export into NIRVANA canonical schema.
        """
        rows = []
        for idx, r in df.iterrows():
            st = str(r.get("STATE", "Unknown")).strip()
            raw_work = str(r.get("WORK", f"MPLADS Project {idx+1}")).strip()
            # Clean work title
            work_clean = re.sub(r"^NA\s*-\s*", "", raw_work).strip()
            
            raw_status = str(r.get("STATUS", "Sanctioned")).strip()
            if raw_status.lower() == "completed":
                status = "COMPLETED"
                rep_prog = 100.0
            elif raw_status.lower() == "ongoing":
                status = "IN_PROGRESS"
                rep_prog = 45.0
            elif raw_status.lower() == "unsanctioned":
                status = "RECOMMENDED"
                rep_prog = 0.0
            else:
                status = "SANCTIONED"
                rep_prog = 10.0

            alloc_amt = cls.clean_currency(r.get("ALLOCATION AMOUNT", 0.0))
            rel_amt = alloc_amt if status in ("COMPLETED", "IN_PROGRESS") else (alloc_amt * 0.5 if status == "SANCTIONED" else 0.0)
            exp_amt = alloc_amt if status == "COMPLETED" else (alloc_amt * 0.4 if status == "IN_PROGRESS" else 0.0)

            # Geographic centroid with realistic district jitter
            centroid = cls.STATE_CENTROIDS.get(st, (22.5, 78.5))
            jitter_seed = (hash(str(r.get("VILLAGE", "")) + str(r.get("BLOCK", "")) + str(idx)) % 1000 - 500) / 1000.0
            lat = round(centroid[0] + (jitter_seed * 0.4), 4)
            lon = round(centroid[1] + (jitter_seed * 0.4), 4)

            # District extraction from IDA
            ida_str = str(r.get("IDA", "")).strip()
            dist = re.sub(r"(?i)district (collector|magistrate)|_ida|\bida\b", "", ida_str).strip()
            if not dist:
                dist = str(r.get("CONSTITUENCY", "Central District")).strip()

            st_code = "".join([w[0] for w in st.split()[:2]]).upper() or "IN"
            p_id = f"GOV-{st_code}-{idx+1:05d}"

            rows.append({
                "project_id": p_id,
                "project_name": work_clean,
                "project_type": cls.normalize_project_type(r.get("CATEGORY"), work_clean),
                "sector": str(r.get("CATEGORY", "Community Development")),
                "state": st,
                "district": dist,
                "constituency": str(r.get("CONSTITUENCY", "")),
                "block": str(r.get("BLOCK", "")),
                "village": str(r.get("VILLAGE", "")),
                "latitude": lat,
                "longitude": lon,
                "sanction_amount": alloc_amt,
                "released_amount": rel_amt,
                "expenditure_amount": exp_amt,
                "start_date": cls.clean_date(r.get("RECOMMENDED DATE")),
                "expected_completion_date": None,
                "actual_completion_date": None,
                "reported_progress": rep_prog,
                "observed_progress": None,  # Ground truth not yet available
                "status": status,
                "agency": ida_str or f"{st} State Implementing Authority",
            })
        return pd.DataFrame(rows)

    @classmethod
    def normalize_dataframe(cls, df: pd.DataFrame) -> pd.DataFrame:
        norm_df = df.copy()

        # Check if this is the official MoSPI MPLADS format
        if "WORK" in norm_df.columns and ("ALLOCATION AMOUNT" in norm_df.columns or "MP NAME" in norm_df.columns):
            return cls._normalize_mospi_export(norm_df)

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
