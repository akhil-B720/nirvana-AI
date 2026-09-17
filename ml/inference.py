import json
import logging
from datetime import datetime
import numpy as np
import pandas as pd
from backend.core.database import SessionLocal
from backend.models.models import Project, RiskScore, ProjectAnomaly
from ml.models.project_risk_model import ProjectRiskModel
from ml.models.cost_anomaly import CostAnomalyModel
from ml.models.delay_model import DelayRiskModel
from ml.models.similarity_model import SimilarityEngine
from backend.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("nirvana.ml.inference")


def run_inference():
    """
    Executes project-level risk analysis, reality gap evaluation,
    and anomaly detection across all active projects.
    """
    db = SessionLocal()
    try:
        projects = db.query(Project).all()
        if not projects:
            logger.warning("No projects found for inference.")
            return

        logger.info(f"Running inference across {len(projects)} projects...")

        # Load Project Risk Model
        proj_risk_path = settings.MODEL_DIR / "project_risk" / "project_risk_model.joblib"
        if proj_risk_path.exists():
            risk_model = ProjectRiskModel.load(str(proj_risk_path))
        else:
            logger.warning("ProjectRiskModel artifact not found; initializing new model.")
            risk_model = ProjectRiskModel()
            risk_model.fit(projects)

        # Load Auxiliary Models
        delay_model = DelayRiskModel()
        sim_path = settings.MODEL_DIR / "similarity" / "similarity_model.joblib"
        sim_engine = SimilarityEngine.load(str(sim_path)) if sim_path.exists() else None

        # Pre-fetch existing risk scores for O(1) lookups
        existing_rs_map = {rs.project_id: rs for rs in db.query(RiskScore).all()}
        # Clear old anomalies to re-generate clean active signals
        db.query(ProjectAnomaly).delete()

        anomalies_to_add = []
        for p in projects:
            sim_matches = sim_engine.find_similar(p, top_k=1) if sim_engine else []
            text_sim_max = sim_matches[0]["combined_similarity"] if (sim_matches and sim_matches[0]["status_label"] == "potentially_similar") else 0.0

            pred = risk_model.predict_project(p, text_sim_max=text_sim_max)
            d_pred = delay_model.predict_project(p)

            fused_score = pred["risk_score"]
            contributing = pred["contributing_factors"]
            conf = pred["confidence"]

            # Map tier for compatibility with frontend/schema
            if fused_score <= 30.0:
                tier = "NORMAL"
            elif fused_score <= 60.0:
                tier = "WATCH"
            elif fused_score <= 80.0:
                tier = "HIGH"
            else:
                tier = "CRITICAL"

            rep_prog = float(p.reported_progress or 0.0)
            obs_prog = float(p.observed_progress) if p.observed_progress is not None else None
            rg_score = round(abs(rep_prog - obs_prog), 2) if obs_prog is not None else None
            delay_prob = d_pred.get("delay_probability")

            rs = existing_rs_map.get(p.project_id)
            if not rs:
                rs = RiskScore(project_id=p.project_id)
                db.add(rs)
                existing_rs_map[p.project_id] = rs

            rs.fused_risk_score = fused_score
            rs.risk_tier = tier
            rs.reality_gap_score = rg_score
            rs.financial_anomaly_score = round(max(0.0, min(100.0, pred["feature_values"]["cost_log_ratio_sector"] * 25.0)), 2)
            rs.delay_probability = round(delay_prob, 2) if delay_prob is not None else None
            rs.similarity_score = round(text_sim_max * 100.0, 2)
            rs.contributing_factors_json = json.dumps(contributing)
            rs.weights_used_json = json.dumps({
                "isolation_forest": 0.45,
                "domain_rules_max": 0.35,
                "domain_rules_avg": 0.20
            })
            rs.model_versions_json = json.dumps({
                "project_risk": risk_model.version,
                "delay_model": delay_model.version,
                "similarity": "1.0.0"
            })
            rs.confidence_score = round(conf * 100.0, 1)

            # Generate project anomalies if above threshold
            if fused_score > 30.0:
                pa = ProjectAnomaly(
                    project_id=p.project_id,
                    anomaly_type="REALITY_GAP" if (rg_score and rg_score > 30.0) else "COMPOSITE_RISK",
                    severity=tier,
                    score=fused_score,
                    description="; ".join(contributing) if contributing else "Statistical feature divergence flagged by unsupervised anomaly engine."
                )
                anomalies_to_add.append(pa)

        db.bulk_save_objects(anomalies_to_add)
        db.commit()
        logger.info(f"Inference completed successfully across {len(projects)} projects. {len(anomalies_to_add)} anomalies recorded.")
    finally:
        db.close()


if __name__ == "__main__":
    run_inference()
