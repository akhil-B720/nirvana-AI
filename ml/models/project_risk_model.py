import math
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class ProjectRiskModel:
    """
    Project-Level MPLADS Risk Intelligence Engine.
    Combines unsupervised Isolation Forest anomaly detection with sector-normalized
    Median Absolute Deviation (MAD), schedule stall tracking, and textual duplicate similarity.
    All outputs strictly adhere to analytical decision-support semantics without synthetic fraud labels.
    """

    FEATURE_NAMES = [
        "cost_log_ratio_sector",
        "cost_log_ratio_state",
        "utilization_ratio",
        "release_ratio",
        "stalled_days_scaled",
        "fin_phys_gap",
        "text_similarity_max",
        "data_completeness_ratio",
    ]

    def __init__(self, contamination: float = 0.10, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=150,
        )
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=1000)
        self.version = "1.0.0"
        self.is_fitted = False

        # Empirical baseline statistics computed during fit
        self.sector_medians: Dict[str, float] = {}
        self.sector_mads: Dict[str, float] = {}
        self.state_medians: Dict[str, float] = {}
        self.state_mads: Dict[str, float] = {}
        self.global_median_cost: float = 500000.0
        self.global_mad_cost: float = 300000.0
        self.metrics: Dict[str, Any] = {}

    @staticmethod
    def _compute_mad(arr: np.ndarray, median_val: float) -> float:
        if len(arr) == 0:
            return 1.0
        mad = float(np.median(np.abs(arr - median_val)))
        return mad if mad > 1.0 else 1.0

    def compute_data_completeness(self, project: Any) -> Tuple[float, List[str]]:
        """
        Evaluates the completeness of administrative and milestone records.
        Returns completeness ratio [0.0, 1.0] and list of missing fields.
        """
        critical_fields = [
            ("project_name", getattr(project, "project_name", None)),
            ("project_type", getattr(project, "project_type", None)),
            ("state", getattr(project, "state", None)),
            ("district", getattr(project, "district", None)),
            ("constituency", getattr(project, "constituency", None)),
            ("block", getattr(project, "block", None)),
            ("village", getattr(project, "village", None)),
            ("sanction_amount", getattr(project, "sanction_amount", None)),
            ("start_date", getattr(project, "start_date", None)),
            ("status", getattr(project, "status", None)),
        ]

        missing = []
        present_count = 0
        for name, val in critical_fields:
            if val is not None and str(val).strip() not in ("", "None", "nan", "UNKNOWN"):
                present_count += 1
            else:
                missing.append(name)

        ratio = round(present_count / len(critical_fields), 3)
        return ratio, missing

    def extract_single_feature_vector(self, project: Any, text_sim_max: float = 0.0) -> Dict[str, float]:
        """
        Extracts raw and normalized feature values for a single project.
        """
        sanction = float(getattr(project, "sanction_amount", 0.0) or 0.0)
        released = float(getattr(project, "released_amount", 0.0) or 0.0)
        expenditure = float(getattr(project, "expenditure_amount", 0.0) or 0.0)
        rep_prog = float(getattr(project, "reported_progress", 0.0) or 0.0)
        status = str(getattr(project, "status", "SANCTIONED") or "SANCTIONED").upper()
        sector = str(getattr(project, "sector", "OTHER") or "OTHER")
        state = str(getattr(project, "state", "UNKNOWN") or "UNKNOWN")

        # 1. Cost Deviation vs Sector Baseline
        sec_med = self.sector_medians.get(sector, self.global_median_cost)
        sec_mad = self.sector_mads.get(sector, self.global_mad_cost)
        log_cost = np.log10(max(1.0, sanction))
        log_sec_med = np.log10(max(1.0, sec_med))
        sec_mad_log = max(0.1, np.log10(max(1.0, sec_med + sec_mad)) - log_sec_med)
        cost_log_ratio_sector = float((log_cost - log_sec_med) / sec_mad_log)

        # 2. Cost Deviation vs State Baseline
        st_med = self.state_medians.get(state, self.global_median_cost)
        st_mad = self.state_mads.get(state, self.global_mad_cost)
        log_st_med = np.log10(max(1.0, st_med))
        st_mad_log = max(0.1, np.log10(max(1.0, st_med + st_mad)) - log_st_med)
        cost_log_ratio_state = float((log_cost - log_st_med) / st_mad_log)

        # 3. Utilization & Release Rates
        utilization_ratio = float(min(3.0, expenditure / released)) if released > 0 else 0.0
        release_ratio = float(min(2.0, released / sanction)) if sanction > 0 else 0.0

        # 4. Schedule Momentum & Stalled Days
        start_d = getattr(project, "start_date", None)
        act_d = getattr(project, "actual_completion_date", None)
        ref_date = act_d if act_d else date.today()

        elapsed_days = 0
        if start_d:
            try:
                if isinstance(start_d, str):
                    start_d = datetime.strptime(start_d, "%Y-%m-%d").date()
                elapsed_days = max(0, (ref_date - start_d).days)
            except Exception:
                elapsed_days = 0

        # High stall flag: project sanctioned long ago with low progress
        if status in ("SANCTIONED", "IN_PROGRESS", "RECOMMENDED") and elapsed_days > 365 and rep_prog < 30.0:
            stalled_days_scaled = float(min(5.0, elapsed_days / 365.0))
        elif status == "COMPLETED":
            stalled_days_scaled = 0.0
        else:
            stalled_days_scaled = float(min(3.0, elapsed_days / 730.0))

        # 5. Financial vs Physical Progress Gap
        fin_ratio = (expenditure / sanction * 100.0) if sanction > 0 else 0.0
        fin_phys_gap = float(abs(fin_ratio - rep_prog))

        # 6. Data Completeness
        completeness, _ = self.compute_data_completeness(project)

        return {
            "sanction_amount": sanction,
            "released_amount": released,
            "expenditure_amount": expenditure,
            "reported_progress": rep_prog,
            "elapsed_days": float(elapsed_days),
            "cost_log_ratio_sector": round(cost_log_ratio_sector, 4),
            "cost_log_ratio_state": round(cost_log_ratio_state, 4),
            "utilization_ratio": round(utilization_ratio, 4),
            "release_ratio": round(release_ratio, 4),
            "stalled_days_scaled": round(stalled_days_scaled, 4),
            "fin_phys_gap": round(fin_phys_gap, 2),
            "text_similarity_max": round(float(text_sim_max), 4),
            "data_completeness_ratio": round(completeness, 3),
        }

    def fit(self, projects: List[Any]) -> Dict[str, Any]:
        """
        Fits empirical baseline statistics and the Isolation Forest anomaly detector.
        """
        if len(projects) < 5:
            return {"status": "INSUFFICIENT_DATA", "message": f"Requires at least 5 projects, got {len(projects)}"}

        # 1. Compute empirical sector & state statistics
        sector_groups: Dict[str, List[float]] = {}
        state_groups: Dict[str, List[float]] = {}
        all_costs: List[float] = []
        corpus: List[str] = []

        for p in projects:
            amt = float(getattr(p, "sanction_amount", 0.0) or 0.0)
            if amt > 0:
                all_costs.append(amt)
                sec = str(getattr(p, "sector", "OTHER") or "OTHER")
                st = str(getattr(p, "state", "UNKNOWN") or "UNKNOWN")
                sector_groups.setdefault(sec, []).append(amt)
                state_groups.setdefault(st, []).append(amt)

            title = str(getattr(p, "project_name", ""))
            blk = str(getattr(p, "block", "") or "")
            dist = str(getattr(p, "district", "") or "")
            corpus.append(f"{title} {blk} {dist}")

        if all_costs:
            all_arr = np.array(all_costs)
            self.global_median_cost = float(np.median(all_arr))
            self.global_mad_cost = self._compute_mad(all_arr, self.global_median_cost)

        for sec, vals in sector_groups.items():
            arr = np.array(vals)
            med = float(np.median(arr))
            self.sector_medians[sec] = med
            self.sector_mads[sec] = self._compute_mad(arr, med)

        for st, vals in state_groups.items():
            arr = np.array(vals)
            med = float(np.median(arr))
            self.state_medians[st] = med
            self.state_mads[st] = self._compute_mad(arr, med)

        # 2. Fit TF-IDF Vectorizer
        if corpus:
            self.vectorizer.fit(corpus)

        # 3. Extract feature matrix for IsolationForest
        X_rows = []
        for p in projects:
            feat = self.extract_single_feature_vector(p, text_sim_max=0.0)
            row = [feat[col] for col in self.FEATURE_NAMES]
            X_rows.append(row)

        X = np.array(X_rows)
        self.model.fit(X)
        self.is_fitted = True

        scores = self.model.decision_function(X)
        self.metrics = {
            "num_projects_trained": len(projects),
            "num_features": len(self.FEATURE_NAMES),
            "contamination": self.contamination,
            "mean_decision_score": round(float(np.mean(scores)), 4),
            "min_decision_score": round(float(np.min(scores)), 4),
            "max_decision_score": round(float(np.max(scores)), 4),
            "global_median_sanction": round(self.global_median_cost, 2),
            "algorithm": "Isolation Forest (150 trees) + Robust Sector/State MAD",
            "training_timestamp": datetime.utcnow().isoformat(),
            "status": "ACTIVE",
        }
        return self.metrics

    def predict_project(self, project: Any, text_sim_max: float = 0.0) -> Dict[str, Any]:
        """
        Generates calibrated risk score, tier, confidence, and human-readable explanation factors.
        """
        feat = self.extract_single_feature_vector(project, text_sim_max=text_sim_max)
        completeness, missing_fields = self.compute_data_completeness(project)

        contributing_factors = []
        rule_subscores = []

        # Signal 1: Sector Cost Divergence
        cost_sec_z = feat["cost_log_ratio_sector"]
        if cost_sec_z > 2.5:
            rule_subscores.append(min(100.0, (cost_sec_z - 1.5) * 35.0))
            sanction = feat["sanction_amount"]
            sec = getattr(project, "sector", "sector")
            sec_med = self.sector_medians.get(sec, self.global_median_cost)
            contributing_factors.append(
                f"Sanction amount of ₹{sanction:,.0f} is {cost_sec_z:.1f} MADs above {sec} median (₹{sec_med:,.0f})"
            )
        elif cost_sec_z < -3.0 and feat["sanction_amount"] > 0:
            contributing_factors.append(
                f"Sub-nominal allocation of ₹{feat['sanction_amount']:,.0f} significantly below sector standard"
            )

        # Signal 2: Timeline Stall
        stalled = feat["stalled_days_scaled"]
        elapsed = feat["elapsed_days"]
        rep_prog = feat["reported_progress"]
        status = str(getattr(project, "status", "SANCTIONED")).upper()
        if stalled > 1.5 and status != "COMPLETED":
            stall_score = min(100.0, stalled * 25.0)
            rule_subscores.append(stall_score)
            contributing_factors.append(
                f"Work recommended/sanctioned {int(elapsed)} days ago with low reported progress ({rep_prog:.0f}%)"
            )

        # Signal 3: Financial vs Physical Mismatch
        fin_gap = feat["fin_phys_gap"]
        if fin_gap > 35.0:
            rule_subscores.append(min(100.0, fin_gap * 1.2))
            contributing_factors.append(
                f"Discrepancy of {fin_gap:.1f}% between financial release/expenditure and reported progress"
            )

        # Signal 4: Duplicate Similarity
        if text_sim_max >= 0.70:
            rule_subscores.append(min(100.0, text_sim_max * 100.0))
            contributing_factors.append(
                f"High textual similarity ({text_sim_max*100:.0f}%) detected with concurrent work in jurisdiction"
            )

        # Signal 5: Reality Gap (Observed evidence)
        obs_prog = getattr(project, "observed_progress", None)
        reality_gap = None
        if obs_prog is not None:
            reality_gap = round(abs(rep_prog - float(obs_prog)), 2)
            if reality_gap > 20.0:
                rule_subscores.append(min(100.0, reality_gap * 1.5))
                contributing_factors.append(
                    f"Physical reality gap: Claimed {rep_prog:.0f}% vs Observed {obs_prog:.0f}%"
                )

        # Isolation Forest inference
        if_score = 0.0
        if self.is_fitted:
            x_vec = np.array([[feat[col] for col in self.FEATURE_NAMES]])
            dec = float(self.model.decision_function(x_vec)[0])
            # Map decision score (-0.35 to 0.35) into 0-100 anomaly scale
            # Lower decision score = more anomalous
            if_score = float(np.clip((0.20 - dec) * 140.0, 0.0, 100.0))
            if if_score > 60.0 and not contributing_factors:
                contributing_factors.append(
                    f"Multi-feature spatial/structural divergence flagged by Isolation Forest (score {if_score:.1f})"
                )

        # Fused Dynamic Risk Score
        if rule_subscores:
            rule_max = max(rule_subscores)
            rule_avg = sum(rule_subscores) / len(rule_subscores)
            fused_score = 0.45 * if_score + 0.35 * rule_max + 0.20 * rule_avg
        else:
            fused_score = if_score * 0.75

        # Completed projects without flags should remain low risk
        if status == "COMPLETED" and not rule_subscores and if_score < 50.0:
            fused_score = min(25.0, fused_score)

        fused_score = round(float(np.clip(fused_score, 0.0, 100.0)), 2)

        # Dynamic Risk Tier Mapping
        if fused_score < 30.0:
            risk_level = "LOW"
        elif fused_score < 60.0:
            risk_level = "MEDIUM"
        elif fused_score < 80.0:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        # Confidence Calibration (0.0 to 1.0)
        # Completeness contributes 60%, Presence of physical verification contributes 40%
        base_confidence = 0.40 + (0.45 * completeness)
        if obs_prog is not None:
            confidence = round(min(1.0, base_confidence + 0.15), 2)
        else:
            confidence = round(min(0.85, base_confidence), 2)

        p_id = str(getattr(project, "project_id", "UNKNOWN"))
        source_name = getattr(getattr(project, "source", None), "source_name", "Official MoSPI MPLADS Records (ODbL)")

        return {
            "project_id": p_id,
            "risk_score": fused_score,
            "risk_level": risk_level,
            "confidence": confidence,
            "contributing_factors": contributing_factors,
            "feature_values": feat,
            "reality_gap_score": reality_gap,
            "missing_fields": missing_fields,
            "model_version": self.version,
            "data_source": source_name,
            "timestamp": datetime.utcnow().isoformat(),
            "disclaimer": "AI-generated risk indicators are analytical decision-support signals and do not constitute proof of fraud, corruption, or irregularity.",
        }

    def save(self, filepath: str):
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str):
        return joblib.load(filepath)
