import logging
import json
import numpy as np
import pandas as pd
from backend.core.database import SessionLocal
from backend.models.models import Project, RiskScore, ProjectAnomaly
from ml.models.cost_anomaly import CostAnomalyModel
from ml.models.delay_model import DelayRiskModel
from ml.models.similarity_model import SimilarityEngine
from backend.core.config import settings
from data_pipeline.processors.feature_extractor import FeatureExtractor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("nirvana.ml.inference")

def run_inference():
    db = SessionLocal()
    try:
        projects = db.query(Project).all()
        if not projects:
            logger.warning("No projects found for inference.")
            return

        cost_model_path = settings.MODEL_DIR / "cost_anomaly" / "cost_anomaly.joblib"
        cost_model = CostAnomalyModel.load(str(cost_model_path)) if cost_model_path.exists() else CostAnomalyModel()

        delay_model = DelayRiskModel()

        sim_path = settings.MODEL_DIR / "similarity" / "similarity_model.joblib"
        sim_engine = SimilarityEngine.load(str(sim_path)) if sim_path.exists() else None

        df_all = pd.DataFrame([{
            "project_id": p.project_id,
            "sanction_amount": p.sanction_amount,
            "released_amount": p.released_amount,
            "expenditure_amount": p.expenditure_amount,
            "reported_progress": p.reported_progress
        } for p in projects])

        cost_preds = cost_model.predict(df_all) if len(df_all) >= 1 else []

        for idx, p in enumerate(projects):
            feat = FeatureExtractor.calculate_project_features(p)
            c_pred = cost_preds[idx] if idx < len(cost_preds) else {"anomaly_score": 0.0, "contributing_factors": []}
            d_pred = delay_model.predict_project(p)
            similar_matches = sim_engine.find_similar(p, top_k=2) if sim_engine else []

            # Reality Gap Calculation
            # Components:
            # - Financial Progress Gap
            # - Reported vs Observed Gap (if observed exists)
            # - Expected vs Observed Gap (if observed exists)
            # - Time Progress Gap (Schedule slippage)
            rep_prog = float(p.reported_progress or 0.0)
            obs_prog = float(p.observed_progress) if p.observed_progress is not None else None
            exp_prog = feat.get("expected_progress")

            gaps = []
            contributing = []

            # 1. Financial Progress Gap (Weight: 0.20)
            fin_gap = feat.get("financial_progress_gap", 0.0)
            gaps.append(("financial_progress_gap", min(100.0, fin_gap), 0.20))
            if fin_gap > 30.0:
                contributing.append(f"Financial-to-progress misalignment of {fin_gap:.1f}%")

            # 2. Reality Gap (Weight: 0.25)
            if obs_prog is not None:
                reality_diff = abs(rep_prog - obs_prog)
                gaps.append(("reality_gap", min(100.0, reality_diff), 0.25))
                if reality_diff > 20.0:
                    contributing.append(f"Reality gap: Reported {rep_prog:.1f}% vs Observed {obs_prog:.1f}%")
            else:
                # If observed evidence is missing, do NOT penalize project as fraudulent.
                contributing.append("Observed physical evidence unavailable on record")

            # 3. Cost Anomaly (Weight: 0.20)
            cost_score = c_pred.get("anomaly_score", 0.0)
            gaps.append(("cost_anomaly", cost_score, 0.20))
            for f in c_pred.get("contributing_factors", []):
                contributing.append(f)

            # 4. Delay Risk (Weight: 0.15)
            delay_prob = d_pred.get("delay_probability") or 0.0
            gaps.append(("delay_risk", delay_prob * 100.0, 0.15))
            if delay_prob > 0.6:
                contributing.append(f"High timeline delay risk ({delay_prob*100:.1f}%)")

            # 5. Similarity Risk (Weight: 0.10)
            sim_score = 0.0
            if similar_matches and similar_matches[0]["status_label"] == "potentially_similar":
                sim_score = similar_matches[0]["combined_similarity"] * 100.0
                contributing.append(f"Potential duplicate overlap with {similar_matches[0]['compared_project_name'][:40]}...")
            gaps.append(("similarity", sim_score, 0.10))

            # Dynamic weight redistribution for missing signals
            total_active_weight = sum(g[2] for g in gaps)
            if total_active_weight > 0:
                fused_score = sum(g[1] * (g[2] / total_active_weight) for g in gaps)
            else:
                fused_score = 0.0

            fused_score = round(float(np.clip(fused_score, 0.0, 100.0)), 2)

            # Risk Tier mapping
            if fused_score <= 30.0:
                tier = "NORMAL"
            elif fused_score <= 60.0:
                tier = "WATCH"
            elif fused_score <= 80.0:
                tier = "HIGH"
            else:
                tier = "CRITICAL"

            # Reality Gap score specific
            rg_score = round(abs(rep_prog - obs_prog), 2) if obs_prog is not None else None

            # Persist RiskScore
            existing_rs = db.query(RiskScore).filter_by(project_id=p.project_id).first()
            if not existing_rs:
                existing_rs = RiskScore(project_id=p.project_id)
                db.add(existing_rs)

            existing_rs.fused_risk_score = fused_score
            existing_rs.risk_tier = tier
            existing_rs.reality_gap_score = rg_score
            existing_rs.financial_anomaly_score = cost_score
            existing_rs.delay_probability = round(delay_prob, 2)
            existing_rs.similarity_score = sim_score
            existing_rs.contributing_factors_json = json.dumps(contributing)
            existing_rs.weights_used_json = json.dumps({g[0]: g[2] for g in gaps})
            existing_rs.model_versions_json = json.dumps({
                "cost_anomaly": "1.0.0",
                "delay_model": "1.0.0",
                "similarity": "1.0.0"
            })
            existing_rs.confidence_score = 85.0 if obs_prog is not None else 65.0

            # Generate Project Anomalies
            db.query(ProjectAnomaly).filter_by(project_id=p.project_id).delete()
            if fused_score > 30.0:
                pa = ProjectAnomaly(
                    project_id=p.project_id,
                    anomaly_type="REALITY_GAP" if (rg_score and rg_score > 30.0) else "COMPOSITE_RISK",
                    severity=tier,
                    score=fused_score,
                    description="; ".join(contributing) or "Elevated statistical divergence noted."
                )
                db.add(pa)

        db.commit()
        logger.info(f"Inference completed across {len(projects)} projects.")
    finally:
        db.close()

if __name__ == "__main__":
    run_inference()
