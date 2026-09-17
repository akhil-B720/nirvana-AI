import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

from backend.core.database import SessionLocal
from backend.models.macro_models import (
    StateYearlyPerformance,
    StateSectoralAllocation,
    StateUnspentLiquidity,
    StateMacroMetrics,
    DataQualityAuditLog
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("nirvana.pipeline.macro")

STATE_CANONICAL_MAP = {
    "A & N Islands": "Andaman and Nicobar Islands",
    "A & N Island": "Andaman and Nicobar Islands",
    "Andaman & Nicobar Islands": "Andaman and Nicobar Islands",
    "Andaman and Nicobar Islands": "Andaman and Nicobar Islands",
    "Andhra Pradesh": "Andhra Pradesh",
    "Andhra Pradesh (Old)": "Andhra Pradesh",
    "Arunachal Pradesh": "Arunachal Pradesh",
    "Assam": "Assam",
    "Bihar": "Bihar",
    "Chandigarh": "Chandigarh",
    "Chhattisgarh": "Chhattisgarh",
    "D & N Haveli": "Dadra and Nagar Haveli",
    "Dadra & Nagar Haveli": "Dadra and Nagar Haveli",
    "Dadra and Nagar Haveli": "Dadra and Nagar Haveli",
    "Daman & Diu": "Daman and Diu",
    "Daman and Diu": "Daman and Diu",
    "Delhi": "Delhi",
    "Goa": "Goa",
    "Gujarat": "Gujarat",
    "Haryana": "Haryana",
    "Himachal Pradesh": "Himachal Pradesh",
    "Jammu & Kashmir": "Jammu and Kashmir",
    "Jammu and Kashmir": "Jammu and Kashmir",
    "Jharkhand": "Jharkhand",
    "Karnataka": "Karnataka",
    "Kerala": "Kerala",
    "Lakshadweep": "Lakshadweep",
    "Madhya Pradesh": "Madhya Pradesh",
    "Maharashtra": "Maharashtra",
    "Manipur": "Manipur",
    "Meghalaya": "Meghalaya",
    "Mizoram": "Mizoram",
    "Nagaland": "Nagaland",
    "Nominated": "Nominated MPs",
    "Odisha": "Odisha",
    "Puducherry": "Puducherry",
    "Punjab": "Punjab",
    "Rajasthan": "Rajasthan",
    "Sikkim": "Sikkim",
    "Tamil Nadu": "Tamil Nadu",
    "Telangana": "Telangana",
    "Tripura": "Tripura",
    "Uttar Pradesh": "Uttar Pradesh",
    "Uttarakhand": "Uttarakhand",
    "West Bengal": "West Bengal"
}

class MacroDataPipeline:
    """
    End-to-end reproducible pipeline for macro State/UT MPLADS data:
    raw -> validation -> cleaning -> normalization -> feature engineering -> database -> ML
    """

    def __init__(self, raw_dir: str = "dataset/raw"):
        self.raw_dir = Path(raw_dir)
        self.audit_logs: List[Dict[str, Any]] = []

    def log_transformation(self, file_name: str, row_id: str, field: str, original: Any, cleaned: Any, rule: str, rationale: str):
        self.audit_logs.append({
            "source_file": file_name,
            "row_identifier": str(row_id),
            "field_name": field,
            "original_value": str(original) if original is not None else None,
            "cleaned_value": str(cleaned) if cleaned is not None else None,
            "transformation_rule": rule,
            "rationale": rationale
        })

    def process_yearly_data(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        fname = "mplads_state_yearly_expenditure_and_works.csv"
        fpath = self.raw_dir / fname
        if not fpath.exists():
            raise FileNotFoundError(f"Missing {fpath}")

        df_raw = pd.read_csv(fpath)
        logger.info(f"Processing {fname}: raw shape {df_raw.shape}")

        # Fix duplicate year header in raw CSV (2016-17 was repeated for 2017-18)
        cols = list(df_raw.columns)
        # Rename col 4 and 5 (index 4 and 5)
        self.log_transformation(
            fname, "HEADER", cols[4], cols[4], "2017-18 - Expenditure - Incurred With (Rs. Crore)",
            "DISAMBIGUATE_DUPLICATE_YEAR_HEADER",
            "Second 2016-17 column in raw file corresponds chronologically to FY 2017-18 based on MoSPI Parliamentary reports"
        )
        self.log_transformation(
            fname, "HEADER", cols[5], cols[5], "2017-18 - Completed - Works",
            "DISAMBIGUATE_DUPLICATE_YEAR_HEADER",
            "Second 2016-17 completed works column corresponds to FY 2017-18"
        )
        df_raw.columns = [
            "s_no", "state_raw",
            "exp_16_17", "works_16_17",
            "exp_17_18", "works_17_18",
            "exp_18_19", "works_18_19",
            "exp_19_20", "works_19_20"
        ]

        # Filter out summary total row
        total_row = df_raw[df_raw["state_raw"].astype(str).str.lower().isin(["total", "sub total"])].copy()
        df_states = df_raw[~df_raw["state_raw"].astype(str).str.lower().isin(["total", "sub total"])].copy()

        # Canonicalize state names
        df_states["state"] = df_states["state_raw"].apply(lambda s: STATE_CANONICAL_MAP.get(str(s).strip(), str(s).strip()))
        for idx, r in df_states.iterrows():
            if r["state_raw"] != r["state"]:
                self.log_transformation(
                    fname, r["s_no"], "State", r["state_raw"], r["state"],
                    "CANONICALIZE_STATE_NAME", "Standardize Indian state/UT naming across administrative divisions"
                )

        # Reshape into tidy state-year panel format
        yearly_records = []
        years = [
            ("2016-17", "exp_16_17", "works_16_17"),
            ("2017-18", "exp_17_18", "works_17_18"),
            ("2018-19", "exp_18_19", "works_18_19"),
            ("2019-20", "exp_19_20", "works_19_20"),
        ]

        for _, r in df_states.iterrows():
            st = r["state"]
            for yr, exp_col, wrk_col in years:
                exp_cr = float(r[exp_col])
                wrk_cnt = int(r[wrk_col])
                cost_per_wrk = (exp_cr * 100.0) / wrk_cnt if wrk_cnt > 0 else None
                yearly_records.append({
                    "state": st,
                    "financial_year": yr,
                    "expenditure_crore": exp_cr,
                    "completed_works": wrk_cnt,
                    "avg_cost_per_work_lakhs": round(cost_per_wrk, 2) if cost_per_wrk is not None else None,
                    "raw_record_id": f"YR_{r['s_no']}_{yr}"
                })

        df_yearly = pd.DataFrame(yearly_records)
        return df_yearly, df_states

    def process_sector_data(self) -> pd.DataFrame:
        fname = "mplads_state_sector_distribution.csv"
        fpath = self.raw_dir / fname
        if not fpath.exists():
            raise FileNotFoundError(f"Missing {fpath}")

        df_raw = pd.read_csv(fpath)
        logger.info(f"Processing {fname}: raw shape {df_raw.shape}")

        df_clean = df_raw.copy()
        df_clean.columns = [
            "sr_no", "state_raw",
            "railways_roads_bridges_pct",
            "education_pct",
            "drinking_water_pct",
            "sanitation_health_pct",
            "other_public_facilities_pct",
            "others_pct"
        ]

        df_clean["state"] = df_clean["state_raw"].apply(lambda s: STATE_CANONICAL_MAP.get(str(s).strip(), str(s).strip()))
        for idx, r in df_clean.iterrows():
            if r["state_raw"] != r["state"]:
                self.log_transformation(
                    fname, r["sr_no"], "State/ UT Name", r["state_raw"], r["state"],
                    "CANONICALIZE_STATE_NAME", "Standardize Indian state/UT naming"
                )

        # Check for NA entries and document
        sector_cols = [
            "railways_roads_bridges_pct", "education_pct", "drinking_water_pct",
            "sanitation_health_pct", "other_public_facilities_pct", "others_pct"
        ]
        for col in sector_cols:
            df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce")
            
        for _, r in df_clean[df_clean[sector_cols].isnull().any(axis=1)].iterrows():
            self.log_transformation(
                fname, r["sr_no"], "all_sectors", "NA", None,
                "PRESERVE_MISSING_SECTOR_DATA", f"State {r['state']} had NA for sector percentages in original MoSPI table"
            )

        return df_clean

    def process_unspent_data(self) -> pd.DataFrame:
        fname = "mplads_state_unspent_balance.csv"
        fpath = self.raw_dir / fname
        if not fpath.exists():
            raise FileNotFoundError(f"Missing {fpath}")

        df_raw = pd.read_csv(fpath)
        logger.info(f"Processing {fname}: raw shape {df_raw.shape}")

        df_clean = df_raw.copy()
        df_clean.columns = ["s_no", "state_raw", "unspent_balance_crore"]

        # Filter out sub-total and grand-total summary rows
        is_summary = df_clean["state_raw"].astype(str).str.lower().str.contains("total")
        df_states = df_clean[~is_summary].copy()

        df_states["state"] = df_states["state_raw"].apply(lambda s: STATE_CANONICAL_MAP.get(str(s).strip(), str(s).strip()))
        df_states["unspent_balance_crore"] = pd.to_numeric(df_states["unspent_balance_crore"], errors="coerce")

        for idx, r in df_states.iterrows():
            if r["state_raw"] != r["state"]:
                self.log_transformation(
                    fname, r["s_no"], "States/UTs", r["state_raw"], r["state"],
                    "CANONICALIZE_STATE_NAME", "Standardize Indian state/UT naming"
                )

        return df_states

    def build_feature_master(self, df_states_yearly: pd.DataFrame, df_sectors: pd.DataFrame, df_unspent: pd.DataFrame) -> pd.DataFrame:
        """
        Synthesizes multi-year time-series, liquidity balances, and sectoral distributions
        into a unified State/UT feature matrix.
        """
        logger.info("Synthesizing multi-dimensional state feature matrix...")

        # 1. Yearly Aggregations
        states = []
        for _, r in df_states_yearly.iterrows():
            st = r["state"]
            exp_16 = float(r["exp_16_17"])
            exp_17 = float(r["exp_17_18"])
            exp_18 = float(r["exp_18_19"])
            exp_19 = float(r["exp_19_20"])

            w_16 = int(r["works_16_17"])
            w_17 = int(r["works_17_18"])
            w_18 = int(r["works_18_19"])
            w_19 = int(r["works_19_20"])

            tot_exp = exp_16 + exp_17 + exp_18 + exp_19
            tot_w = w_16 + w_17 + w_18 + w_19
            avg_exp = tot_exp / 4.0
            avg_w = tot_w / 4.0

            cost_per_w_lakhs = (tot_exp * 100.0) / tot_w if tot_w > 0 else 0.0

            # Dynamic YoY growth rates
            yoy_17 = ((exp_17 - exp_16) / exp_16 * 100.0) if exp_16 > 0 else 0.0
            yoy_18 = ((exp_18 - exp_17) / exp_17 * 100.0) if exp_17 > 0 else 0.0
            yoy_19 = ((exp_19 - exp_18) / exp_18 * 100.0) if exp_18 > 0 else 0.0

            # Volatility (Coefficient of Variation)
            exp_vals = np.array([exp_16, exp_17, exp_18, exp_19])
            std_exp = float(np.std(exp_vals))
            vol_cv = (std_exp / avg_exp) if avg_exp > 0 else 0.0

            # COVID deceleration drop: drop from 18-19 to 19-20
            covid_drop = ((exp_18 - exp_19) / exp_18 * 100.0) if exp_18 > 0 else 0.0

            states.append({
                "state": st,
                "total_expenditure_4yr_crore": round(tot_exp, 2),
                "total_works_completed_4yr": tot_w,
                "avg_annual_expenditure_crore": round(avg_exp, 2),
                "avg_annual_works": round(avg_w, 1),
                "cost_per_work_lakhs": round(cost_per_w_lakhs, 2),
                "yoy_growth_17_18_pct": round(yoy_17, 2),
                "yoy_growth_18_19_pct": round(yoy_18, 2),
                "yoy_growth_19_20_pct": round(yoy_19, 2),
                "expenditure_volatility_cv": round(vol_cv, 3),
                "covid_drop_19_20_pct": round(covid_drop, 2)
            })

        df_master = pd.DataFrame(states)

        # 2. Merge Unspent Liquidity
        unspent_map = df_unspent.set_index("state")["unspent_balance_crore"].to_dict()
        df_master["unspent_balance_crore"] = df_master["state"].map(unspent_map)

        # Backlog Absorption Years = unspent / avg_annual_expenditure
        df_master["backlog_absorption_years"] = df_master.apply(
            lambda r: round(r["unspent_balance_crore"] / r["avg_annual_expenditure_crore"], 2)
            if pd.notna(r["unspent_balance_crore"]) and r["avg_annual_expenditure_crore"] > 0 else 0.0,
            axis=1
        )

        # 3. Merge Sector Allocations
        sec_clean = df_sectors.drop_duplicates(subset=["state"]).set_index("state")
        
        def compute_sector_metrics(row):
            st = row["state"]
            if st in sec_clean.index:
                s_row = sec_clean.loc[st]
                infra = s_row["railways_roads_bridges_pct"]
                edu = s_row["education_pct"]
                water = s_row["drinking_water_pct"]
                san = s_row["sanitation_health_pct"]
                pub = s_row["other_public_facilities_pct"]
                oth = s_row["others_pct"]

                if pd.notna(infra):
                    social = (edu or 0) + (water or 0) + (san or 0)
                    # Herfindahl-Hirschman Index for concentration
                    vals = [v for v in [infra, edu, water, san, pub, oth] if pd.notna(v)]
                    hhi = sum((v / 100.0) ** 2 for v in vals)
                    return pd.Series([infra, social, round(hhi, 3)])
            return pd.Series([None, None, None])

        df_master[["infrastructure_dominance_pct", "social_infrastructure_pct", "sector_hhi"]] = df_master.apply(
            compute_sector_metrics, axis=1
        )

        return df_master

    def persist_to_database(self, df_yearly: pd.DataFrame, df_sectors: pd.DataFrame, df_unspent: pd.DataFrame, df_master: pd.DataFrame) -> int:
        db = SessionLocal()
        try:
            logger.info("Persisting macro datasets to database...")
            
            # Clear old macro entries if re-running
            db.query(StateYearlyPerformance).delete()
            db.query(StateSectoralAllocation).delete()
            db.query(StateUnspentLiquidity).delete()
            db.query(StateMacroMetrics).delete()
            db.query(DataQualityAuditLog).delete()
            db.commit()

            # 1. Yearly
            for _, r in df_yearly.iterrows():
                rec = StateYearlyPerformance(
                    state=r["state"],
                    financial_year=r["financial_year"],
                    expenditure_crore=r["expenditure_crore"],
                    completed_works=r["completed_works"],
                    avg_cost_per_work_lakhs=r["avg_cost_per_work_lakhs"],
                    raw_record_id=r["raw_record_id"]
                )
                db.add(rec)

            # 2. Sectors
            for _, r in df_sectors.drop_duplicates(subset=["state"]).iterrows():
                rec = StateSectoralAllocation(
                    state=r["state"],
                    railways_roads_bridges_pct=r["railways_roads_bridges_pct"] if pd.notna(r["railways_roads_bridges_pct"]) else None,
                    education_pct=r["education_pct"] if pd.notna(r["education_pct"]) else None,
                    drinking_water_pct=r["drinking_water_pct"] if pd.notna(r["drinking_water_pct"]) else None,
                    sanitation_health_pct=r["sanitation_health_pct"] if pd.notna(r["sanitation_health_pct"]) else None,
                    other_public_facilities_pct=r["other_public_facilities_pct"] if pd.notna(r["other_public_facilities_pct"]) else None,
                    others_pct=r["others_pct"] if pd.notna(r["others_pct"]) else None,
                    raw_record_id=f"SEC_{r['sr_no']}"
                )
                db.add(rec)

            # 3. Unspent
            for _, r in df_unspent.drop_duplicates(subset=["state"]).iterrows():
                rec = StateUnspentLiquidity(
                    state=r["state"],
                    unspent_balance_crore=float(r["unspent_balance_crore"]),
                    raw_record_id=f"UNSP_{r['s_no']}"
                )
                db.add(rec)

            # 4. Master Metrics
            for _, r in df_master.iterrows():
                rec = StateMacroMetrics(
                    state=r["state"],
                    total_expenditure_4yr_crore=r["total_expenditure_4yr_crore"],
                    total_works_completed_4yr=r["total_works_completed_4yr"],
                    avg_annual_expenditure_crore=r["avg_annual_expenditure_crore"],
                    avg_annual_works=r["avg_annual_works"],
                    cost_per_work_lakhs=r["cost_per_work_lakhs"],
                    unspent_balance_crore=r["unspent_balance_crore"] if pd.notna(r["unspent_balance_crore"]) else None,
                    backlog_absorption_years=r["backlog_absorption_years"] if pd.notna(r["backlog_absorption_years"]) else None,
                    yoy_growth_17_18_pct=r["yoy_growth_17_18_pct"] if pd.notna(r["yoy_growth_17_18_pct"]) else None,
                    yoy_growth_18_19_pct=r["yoy_growth_18_19_pct"] if pd.notna(r["yoy_growth_18_19_pct"]) else None,
                    yoy_growth_19_20_pct=r["yoy_growth_19_20_pct"] if pd.notna(r["yoy_growth_19_20_pct"]) else None,
                    expenditure_volatility_cv=r["expenditure_volatility_cv"] if pd.notna(r["expenditure_volatility_cv"]) else None,
                    covid_drop_19_20_pct=r["covid_drop_19_20_pct"] if pd.notna(r["covid_drop_19_20_pct"]) else None,
                    infrastructure_dominance_pct=r["infrastructure_dominance_pct"] if pd.notna(r["infrastructure_dominance_pct"]) else None,
                    social_infrastructure_pct=r["social_infrastructure_pct"] if pd.notna(r["social_infrastructure_pct"]) else None,
                    sector_hhi=r["sector_hhi"] if pd.notna(r["sector_hhi"]) else None,
                    is_anomaly=bool(r.get("is_anomaly", False)),
                    anomaly_score=float(r.get("anomaly_score", 0.0)) if pd.notna(r.get("anomaly_score")) else None,
                    risk_cluster=int(r.get("risk_cluster", 0)) if pd.notna(r.get("risk_cluster")) else None,
                    risk_tier=str(r.get("risk_tier", "NORMAL"))
                )
                db.add(rec)

            # 5. Audit Logs
            for a in self.audit_logs:
                log_entry = DataQualityAuditLog(
                    source_file=a["source_file"],
                    row_identifier=a["row_identifier"],
                    field_name=a["field_name"],
                    original_value=a["original_value"],
                    cleaned_value=a["cleaned_value"],
                    transformation_rule=a["transformation_rule"],
                    rationale=a["rationale"]
                )
                db.add(log_entry)

            db.commit()
            total_records = len(df_yearly) + len(df_sectors) + len(df_unspent) + len(df_master)
            logger.info(f"Database persistence complete. Inserted {total_records} macro records + {len(self.audit_logs)} audit logs.")
            return total_records
        finally:
            db.close()

    def run(self) -> pd.DataFrame:
        df_yearly, df_states = self.process_yearly_data()
        df_sectors = self.process_sector_data()
        df_unspent = self.process_unspent_data()
        df_master = self.build_feature_master(df_states, df_sectors, df_unspent)
        return df_yearly, df_sectors, df_unspent, df_master
