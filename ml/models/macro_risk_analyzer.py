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
from typing import Dict, Any, Tuple

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

class MacroRiskAnalyzer:
    """
    Real Machine Learning Risk & Anomaly Analyzer for State/UT-level MPLADS data.
    - Unsupervised Isolation Forest Anomaly Detection
    - K-Means Operational Performance Clustering
    - PCA Dimensionality Reduction for Visual Risk Mapping
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
        self.cluster_labels_map: Dict[int, str] = {}
        self.is_fitted = False
        self.metrics: Dict[str, Any] = {}

    def _prepare_features(self, df: pd.DataFrame, is_training: bool = True) -> np.ndarray:
        X_df = df[self.feature_names].copy()
        
        # Calculate or use saved medians for missing sector/balance values
        for col in self.feature_names:
            if is_training:
                med = float(X_df[col].median()) if not pd.isna(X_df[col].median()) else 0.0
                self.medians[col] = med
            else:
                med = self.medians.get(col, 0.0)
            X_df[col] = X_df[col].fillna(med)

        # Log transform skewed monetary/count scales for numerical stability
        X_mat = X_df.values.astype(float)
        return X_mat

    def fit(self, df: pd.DataFrame) -> "MacroRiskAnalyzer":
        logger.info(f"Fitting MacroRiskAnalyzer on {len(df)} State/UT entities...")
        X_raw = self._prepare_features(df, is_training=True)
        X_scaled = self.scaler.fit_transform(X_raw)

        # 1. Isolation Forest
        self.isolation_forest.fit(X_scaled)
        # raw decision function: negative values are anomalies
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
            "cluster_profiles": {str(k): v for k, v in self.cluster_labels_map.items()}
        }

        self.is_fitted = True
        logger.info(f"Training complete. Silhouette score: {sil_score:.4f}, PCA Variance: {self.metrics['pca_cumulative_variance']}")
        return self

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self.is_fitted:
            raise ValueError("Model must be fitted before predict()")

        X_raw = self._prepare_features(df, is_training=False)
        X_scaled = self.scaler.transform(X_raw)

        # Anomaly predictions (-1 = anomaly, 1 = normal)
        preds = self.isolation_forest.predict(X_scaled)
        dec_scores = self.isolation_forest.decision_function(X_scaled)
        # Normalize anomaly score to [0, 100] scale where 100 = most anomalous
        min_s, max_s = dec_scores.min(), dec_scores.max()
        range_s = (max_s - min_s) if max_s > min_s else 1.0
        normalized_anomaly = ((max_s - dec_scores) / range_s) * 100.0

        # Clusters & PCA
        cluster_ids = self.kmeans.predict(X_scaled)
        pca_coords = self.pca.transform(X_scaled)

        result_df = df.copy()
        result_df["is_anomaly"] = [bool(p == -1) for p in preds]
        result_df["anomaly_score"] = [round(float(s), 2) for s in normalized_anomaly]
        result_df["risk_cluster"] = [int(c) for c in cluster_ids]
        result_df["cluster_name"] = [self.cluster_labels_map.get(c, "BALANCED") for c in cluster_ids]
        result_df["pca_x"] = [round(float(pt[0]), 3) for pt in pca_coords]
        result_df["pca_y"] = [round(float(pt[1]), 3) for pt in pca_coords]

        # Assign domain risk tier
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
        analyzer.medians = payload["medians"]
        analyzer.cluster_labels_map = payload["cluster_labels_map"]
        analyzer.metrics = payload["metrics"]
        analyzer.is_fitted = payload["is_fitted"]
        return analyzer
