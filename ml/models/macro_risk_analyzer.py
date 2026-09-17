import logging
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from typing import Dict, Any, Tuple, List, Optional

logger = logging.getLogger("nirvana.ml.macro_risk")

FEATURE_COLS = [
    "total_expenditure_4yr_crore",
    "total_works_completed_4yr",
    "cost_per_work_lakhs",
    "unspent_balance_crore",
    "backlog_absorption_years",
    "expenditure_volatility_cv",
    "covid_drop_19_20_pct",
    "infrastructure_dominance_pct",
    "social_infrastructure_pct",
    "sector_hhi"
]

FEATURE_LABELS = {
    "total_expenditure_4yr_crore": "Total 4-Year Expenditure (₹ Cr)",
    "total_works_completed_4yr": "Total Works Completed (4-Yr)",
    "cost_per_work_lakhs": "Cost per Completed Work (₹ Lakhs)",
    "unspent_balance_crore": "Unspent Liquidity Balance (₹ Cr)",
    "backlog_absorption_years": "Backlog Absorption Horizon (Years)",
    "expenditure_volatility_cv": "Expenditure Volatility (CV)",
    "covid_drop_19_20_pct": "FY 2019-20 Expenditure Contraction (%)",
    "infrastructure_dominance_pct": "Roads & Bridges Share (%)",
    "social_infrastructure_pct": "Social Infrastructure Share (%)",
    "sector_hhi": "Sector Concentration Index (HHI)"
}

FEATURE_CATEGORIES = {
    "total_expenditure_4yr_crore": "FINANCIAL_ANOMALY",
    "total_works_completed_4yr": "PHYSICAL_DELIVERY",
    "cost_per_work_lakhs": "FINANCIAL_ANOMALY",
    "unspent_balance_crore": "BACKLOG_PATTERN",
    "backlog_absorption_years": "BACKLOG_PATTERN",
    "expenditure_volatility_cv": "EXPENDITURE_VOLATILITY",
    "covid_drop_19_20_pct": "EXPENDITURE_VOLATILITY",
    "infrastructure_dominance_pct": "SECTORAL_CONCENTRATION",
    "social_infrastructure_pct": "SECTORAL_CONCENTRATION",
    "sector_hhi": "SECTORAL_CONCENTRATION"
}


class MacroRiskAnalyzer:
    """
    Explainable Machine Learning Risk & Anomaly Analyzer for State/UT-level MPLADS data.
    - Unsupervised Isolation Forest Anomaly Detection
    - K-Means Operational Performance Clustering
    - PCA Dimensionality Reduction for Visual Risk Mapping
    - Empirical Feature-Level Attribution & Baseline Comparison Engine
    """

    def __init__(self, n_clusters: int = 4, contamination: float = 0.15, random_state: int = 42):
        self.n_clusters = n_clusters
        self.contamination = contamination
        self.random_state = random_state

        self.scaler = StandardScaler()
        self.isolation_forest = IsolationForest(
            n_estimators=100,
            contamination=self.contamination,
            random_state=self.random_state
        )
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=self.random_state, n_init=10)
        self.pca = PCA(n_components=2, random_state=self.random_state)

        self.feature_names = FEATURE_COLS
        self.medians: Dict[str, float] = {}
        self.means: Dict[str, float] = {}
        self.stds: Dict[str, float] = {}
        self.mads: Dict[str, float] = {}
        self.cluster_labels_map: Dict[int, str] = {}
        self.is_fitted = False
        self.metrics: Dict[str, Any] = {}

    def _prepare_features(self, df: pd.DataFrame, is_training: bool = True) -> np.ndarray:
        X_df = df[self.feature_names].copy()

        for col in self.feature_names:
            if is_training:
                med = float(X_df[col].median()) if not pd.isna(X_df[col].median()) else 0.0
                self.medians[col] = round(med, 3)
            else:
                med = self.medians.get(col, 0.0)
            X_df[col] = X_df[col].fillna(med)

        X_mat = X_df.values.astype(float)
        return X_mat

    def fit(self, df: pd.DataFrame) -> "MacroRiskAnalyzer":
        logger.info(f"Fitting MacroRiskAnalyzer on {len(df)} State/UT entities...")
        X_raw = self._prepare_features(df, is_training=True)

        # Record empirical baseline statistics
        for i, col in enumerate(self.feature_names):
            vals = X_raw[:, i]
            mean_val = float(np.mean(vals))
            std_val = float(np.std(vals))
            med_val = float(np.median(vals))
            mad_val = float(np.median(np.abs(vals - med_val)))
            self.means[col] = round(mean_val, 3)
            self.stds[col] = round(std_val if std_val > 1e-4 else 1.0, 3)
            self.medians[col] = round(med_val, 3)
            self.mads[col] = round(mad_val if mad_val > 1e-4 else 1.0, 3)

        X_scaled = self.scaler.fit_transform(X_raw)

        # 1. Isolation Forest
        self.isolation_forest.fit(X_scaled)
        dec_scores = self.isolation_forest.decision_function(X_scaled)

        # 2. KMeans Clustering
        cluster_ids = self.kmeans.fit_predict(X_scaled)
        sil_score = float(silhouette_score(X_scaled, cluster_ids)) if len(set(cluster_ids)) > 1 else 0.0

        # 3. PCA
        pca_coords = self.pca.fit_transform(X_scaled)
        explained_variance = [float(x) for x in self.pca.explained_variance_ratio_]

        # Profile clusters to assign meaningful domain tags
        cluster_df = pd.DataFrame(X_raw, columns=self.feature_names)
        cluster_df["cluster"] = cluster_ids
        grouped = cluster_df.groupby("cluster").mean()

        for c_id in range(self.n_clusters):
            if c_id in grouped.index:
                row = grouped.loc[c_id]
                backlog = row["backlog_absorption_years"]
                volatility = row["expenditure_volatility_cv"]
                exp = row["total_expenditure_4yr_crore"]

                if backlog > 1.8:
                    label = "CRITICAL_BACKLOG_BOTTLENECK"
                elif volatility > 0.5:
                    label = "HIGH_VOLATILITY_EXPENDITURE"
                elif exp > 1000.0:
                    label = "HIGH_VOLUME_ABSORPTION"
                else:
                    label = "MODERATE_BALANCED_EXECUTION"
                self.cluster_labels_map[c_id] = label

        self.metrics = {
            "samples_count": len(df),
            "features_count": len(self.feature_names),
            "contamination": self.contamination,
            "silhouette_score": round(sil_score, 4),
            "pca_explained_variance": [round(x, 4) for x in explained_variance],
            "pca_cumulative_variance": round(float(sum(explained_variance)), 4),
            "cluster_profiles": {str(k): v for k, v in self.cluster_labels_map.items()},
            "baselines_mean": self.means,
            "baselines_median": self.medians,
            "baselines_std": self.stds,
        }

        self.is_fitted = True
        logger.info(f"Training complete. Silhouette: {sil_score:.4f}, PCA Cumulative Variance: {self.metrics['pca_cumulative_variance']}")
        return self

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self.is_fitted:
            raise ValueError("Model must be fitted before predict()")

        X_raw = self._prepare_features(df, is_training=False)
        X_scaled = self.scaler.transform(X_raw)

        preds = self.isolation_forest.predict(X_scaled)
        dec_scores = self.isolation_forest.decision_function(X_scaled)

        min_s, max_s = dec_scores.min(), dec_scores.max()
        range_s = (max_s - min_s) if max_s > min_s else 1.0
        normalized_anomaly = ((max_s - dec_scores) / range_s) * 100.0

        cluster_ids = self.kmeans.predict(X_scaled)
        pca_coords = self.pca.transform(X_scaled)

        result_df = df.copy()
        result_df["is_anomaly"] = [bool(p == -1) for p in preds]
        result_df["anomaly_score"] = [round(float(s), 2) for s in normalized_anomaly]
        result_df["risk_cluster"] = [int(c) for c in cluster_ids]
        result_df["cluster_name"] = [self.cluster_labels_map.get(c, "BALANCED") for c in cluster_ids]
        result_df["pca_x"] = [round(float(pt[0]), 3) for pt in pca_coords]
        result_df["pca_y"] = [round(float(pt[1]), 3) for pt in pca_coords]

        def assign_tier(row):
            backlog = row.get("backlog_absorption_years") or 0.0
            anomaly_sc = row.get("anomaly_score") or 0.0
            vol = row.get("expenditure_volatility_cv") or 0.0

            if backlog >= 2.0 or anomaly_sc >= 85.0:
                return "CRITICAL_BOTTLENECK"
            elif backlog >= 1.3 or anomaly_sc >= 70.0:
                return "HIGH_BACKLOG"
            elif backlog >= 0.8 or vol >= 0.5:
                return "WATCH"
            else:
                return "NORMAL"

        result_df["risk_tier"] = result_df.apply(assign_tier, axis=1)
        return result_df

    def explain_state_risk(self, state_name: str, metrics: Any) -> Dict[str, Any]:
        """
        Produces fully transparent, feature-level empirical explanation for a state's risk indicator.
        Compares actual state observations against national baseline reference values.
        """
        comparisons = []
        why_flagged = []
        recommendations = []
        cat_scores = {
            "FINANCIAL_ANOMALY": [],
            "BACKLOG_PATTERN": [],
            "EXPENDITURE_VOLATILITY": [],
            "SECTORAL_CONCENTRATION": [],
            "PHYSICAL_DELIVERY": []
        }

        # Extract values
        for feat in self.feature_names:
            val = getattr(metrics, feat, None)
            val_f = float(val) if val is not None and not pd.isna(val) else None
            med = self.medians.get(feat, 0.0)
            mean_val = self.means.get(feat, 0.0)
            std_val = self.stds.get(feat, 1.0)

            if val_f is not None:
                dev = round(val_f - med, 2)
                dev_pct = round(((val_f - med) / med) * 100.0, 1) if med > 0 else 0.0
                z_sc = round((val_f - mean_val) / std_val, 2)
                abs_z = abs(z_sc)

                # Contribution rating
                if abs_z >= 1.8:
                    contrib = "HIGH"
                elif abs_z >= 1.0:
                    contrib = "MEDIUM"
                else:
                    contrib = "LOW"

                cat = FEATURE_CATEGORIES.get(feat, "FINANCIAL_ANOMALY")
                sub_score = min(100.0, abs_z * 35.0)
                cat_scores[cat].append(sub_score)

                comparisons.append({
                    "feature_key": feat,
                    "feature_name": FEATURE_LABELS.get(feat, feat),
                    "category": cat,
                    "actual_value": round(val_f, 2),
                    "model_baseline": med,
                    "baseline_type": "National Median",
                    "deviation": dev,
                    "deviation_pct": dev_pct,
                    "z_score": z_sc,
                    "contribution": contrib
                })
            else:
                comparisons.append({
                    "feature_key": feat,
                    "feature_name": FEATURE_LABELS.get(feat, feat),
                    "category": FEATURE_CATEGORIES.get(feat, "FINANCIAL_ANOMALY"),
                    "actual_value": None,
                    "model_baseline": med,
                    "baseline_type": "National Median",
                    "deviation": None,
                    "deviation_pct": None,
                    "z_score": None,
                    "contribution": "Contribution unavailable"
                })

        # Dynamic Reason Construction (strictly non-accusatory empirical language)
        unspent = getattr(metrics, "unspent_balance_crore", None)
        backlog = getattr(metrics, "backlog_absorption_years", None)
        vol = getattr(metrics, "expenditure_volatility_cv", None)
        cost_pw = getattr(metrics, "cost_per_work_lakhs", None)
        covid_drop = getattr(metrics, "covid_drop_19_20_pct", None)
        exp_total = getattr(metrics, "total_expenditure_4yr_crore", None)
        works_total = getattr(metrics, "total_works_completed_4yr", None)

        med_unspent = self.medians.get("unspent_balance_crore", 100.0)
        med_backlog = self.medians.get("backlog_absorption_years", 0.9)
        med_vol = self.medians.get("expenditure_volatility_cv", 0.3)
        med_cost = self.medians.get("cost_per_work_lakhs", 2.5)

        if unspent is not None and unspent > (med_unspent * 1.5):
            why_flagged.append(
                f"High unspent balance relative to model baseline: ₹{unspent:,.2f} Cr sitting in accounts vs national median of ₹{med_unspent:,.2f} Cr."
            )
            recommendations.append(
                "Review district-level unspent fund balances and reconcile pending utilization certificates (UCs) with nodal authorities."
            )

        if backlog is not None and backlog > (med_backlog * 1.4):
            why_flagged.append(
                f"Elevated backlog absorption horizon: Estimated {backlog:.2f} years required to absorb unspent funds at historical spending velocity (national reference: {med_backlog:.2f} years)."
            )
            recommendations.append(
                "Prioritize clearance of administrative sanctions for pending works to accelerate fund absorption."
            )

        if vol is not None and vol > 0.45:
            why_flagged.append(
                f"Elevated expenditure volatility: Coefficient of variation of {vol:.2f} indicates statistically unusual year-on-year disbursement fluctuations."
            )
            recommendations.append(
                "Audit annual fund release and expenditure chronologies to assess fiscal year-end allocation surges."
            )

        if cost_pw is not None and cost_pw > (med_cost * 2.0):
            why_flagged.append(
                f"Statistically unusual financial pattern: Cost per completed work of ₹{cost_pw:,.2f} Lakhs is elevated compared to national baseline (₹{med_cost:,.2f} Lakhs)."
            )
            recommendations.append(
                "Perform sample on-site physical audits of completed infrastructure assets to verify work scale and unit cost conformity."
            )
        elif cost_pw is not None and cost_pw < (med_cost * 0.3) and cost_pw > 0:
            why_flagged.append(
                f"Sub-nominal cost per work: ₹{cost_pw:,.2f} Lakhs suggests preponderance of minor repair or fragmented works."
            )

        if covid_drop is not None and covid_drop > 40.0:
            why_flagged.append(
                f"Severe expenditure deceleration: Recorded a {covid_drop:.1f}% contraction in capital utilization in FY 2019-20."
            )
            recommendations.append(
                "Reconcile FY 2019-20 project records to identify works delayed by pandemic disruptions and confirm remobilization status."
            )

        if not why_flagged:
            why_flagged.append(
                "Statistically nominal profile: Capital absorption, unit costs, and expenditure volatility align within expected baseline distributions."
            )
            recommendations.append(
                "Maintain periodic monitoring of annual utilization certificates and expenditure reporting."
            )

        # Risk indicator breakdown sub-signals
        risk_breakdown = {
            "financial_anomaly": {
                "score": round(float(np.mean(cat_scores["FINANCIAL_ANOMALY"])), 1) if cat_scores["FINANCIAL_ANOMALY"] else 0.0,
                "label": "Financial Magnitude Deviation",
                "status": "ELEVATED" if (cat_scores["FINANCIAL_ANOMALY"] and max(cat_scores["FINANCIAL_ANOMALY"]) > 60) else "NOMINAL"
            },
            "backlog_pattern": {
                "score": round(float(np.mean(cat_scores["BACKLOG_PATTERN"])), 1) if cat_scores["BACKLOG_PATTERN"] else 0.0,
                "label": "Unspent Backlog Pattern",
                "status": "ELEVATED" if (cat_scores["BACKLOG_PATTERN"] and max(cat_scores["BACKLOG_PATTERN"]) > 60) else "NOMINAL"
            },
            "expenditure_volatility": {
                "score": round(float(np.mean(cat_scores["EXPENDITURE_VOLATILITY"])), 1) if cat_scores["EXPENDITURE_VOLATILITY"] else 0.0,
                "label": "Year-on-Year Volatility",
                "status": "ELEVATED" if (cat_scores["EXPENDITURE_VOLATILITY"] and max(cat_scores["EXPENDITURE_VOLATILITY"]) > 60) else "NOMINAL"
            },
            "sectoral_concentration": {
                "score": round(float(np.mean(cat_scores["SECTORAL_CONCENTRATION"])), 1) if cat_scores["SECTORAL_CONCENTRATION"] else 0.0,
                "label": "Sectoral Distribution Focus",
                "status": "ELEVATED" if (cat_scores["SECTORAL_CONCENTRATION"] and max(cat_scores["SECTORAL_CONCENTRATION"]) > 60) else "NOMINAL"
            }
        }

        # Expenditure trend classification
        if vol is not None and vol >= 0.55:
            trend = "HIGH_VOLATILITY"
        elif getattr(metrics, "yoy_growth_18_19_pct", 0.0) and getattr(metrics, "yoy_growth_19_20_pct", 0.0) and getattr(metrics, "yoy_growth_18_19_pct", 0.0) < -10 and getattr(metrics, "yoy_growth_19_20_pct", 0.0) < -10:
            trend = "DECLINING"
        elif getattr(metrics, "yoy_growth_18_19_pct", 0.0) and getattr(metrics, "yoy_growth_19_20_pct", 0.0) and getattr(metrics, "yoy_growth_18_19_pct", 0.0) > 10 and getattr(metrics, "yoy_growth_19_20_pct", 0.0) > 10:
            trend = "ACCELERATING"
        else:
            trend = "STABLE"

        # Model confidence: High if all core fields present
        has_unspent = unspent is not None
        has_sectors = getattr(metrics, "sector_hhi", None) is not None
        confidence = 0.95 if (has_unspent and has_sectors) else (0.85 if has_unspent else 0.70)

        return {
            "why_flagged": why_flagged,
            "analytical_summary": " ".join(why_flagged),
            "feature_comparisons": comparisons,
            "risk_breakdown": risk_breakdown,
            "verification_recommendations": recommendations,
            "expenditure_trend": trend,
            "confidence": confidence
        }

    def save(self, model_dir: str = "models/macro_risk") -> str:
        p = Path(model_dir)
        p.mkdir(parents=True, exist_ok=True)
        out_file = p / "macro_risk_model.joblib"

        payload = {
            "scaler": self.scaler,
            "isolation_forest": self.isolation_forest,
            "kmeans": self.kmeans,
            "pca": self.pca,
            "feature_names": self.feature_names,
            "medians": self.medians,
            "means": self.means,
            "stds": self.stds,
            "mads": self.mads,
            "cluster_labels_map": self.cluster_labels_map,
            "metrics": self.metrics,
            "is_fitted": self.is_fitted
        }
        joblib.dump(payload, out_file)
        logger.info(f"Saved MacroRiskAnalyzer artifact to {out_file}")
        return str(out_file)

    @classmethod
    def load(cls, model_path: str = "models/macro_risk/macro_risk_model.joblib") -> "MacroRiskAnalyzer":
        p = Path(model_path)
        if not p.exists():
            raise FileNotFoundError(f"Model artifact not found at {p}")
        payload = joblib.load(p)

        analyzer = cls()
        analyzer.scaler = payload["scaler"]
        analyzer.isolation_forest = payload["isolation_forest"]
        analyzer.kmeans = payload["kmeans"]
        analyzer.pca = payload["pca"]
        analyzer.feature_names = payload["feature_names"]
        analyzer.medians = payload.get("medians", {})
        analyzer.means = payload.get("means", {})
        analyzer.stds = payload.get("stds", {})
        analyzer.mads = payload.get("mads", {})
        analyzer.cluster_labels_map = payload["cluster_labels_map"]
        analyzer.metrics = payload["metrics"]
        analyzer.is_fitted = payload["is_fitted"]
        return analyzer
