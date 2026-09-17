import logging
import json
import pandas as pd
from backend.core.database import SessionLocal
from backend.models.models import Project
from ml.models.cost_anomaly import CostAnomalyModel
from ml.models.delay_model import DelayRiskModel
from ml.models.similarity_model import SimilarityEngine
from backend.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("nirvana.ml.evaluate")

def evaluate_models():
    db = SessionLocal()
    try:
        projects = db.query(Project).all()
        logger.info(f"Evaluating NIRVANA ML Suite across {len(projects)} projects...")

        # 1. Cost Anomaly Model Evaluation
        cost_model_path = settings.MODEL_DIR / "cost_anomaly" / "cost_anomaly.joblib"
        if cost_model_path.exists():
            cost_model = CostAnomalyModel.load(str(cost_model_path))
            df = pd.DataFrame([{
                "project_id": p.project_id,
                "sanction_amount": p.sanction_amount,
                "released_amount": p.released_amount,
                "expenditure_amount": p.expenditure_amount,
                "reported_progress": p.reported_progress
            } for p in projects])
            preds = cost_model.predict(df)
            anomalies = [p for p in preds if p["is_anomaly"]]
            logger.info(f"[Cost Anomaly Evaluation]")
            logger.info(f" - Sample count: {len(df)}")
            logger.info(f" - Detected anomalies: {len(anomalies)} ({len(anomalies)/len(df)*100:.1f}%)")
            logger.info(f" - Note: Ground truth fraud labels unavailable. Unsupervised distribution evaluated.")
        else:
            logger.warning("Cost model not found. Run 'python -m ml.train.cost_anomaly' first.")

        # 2. Delay Model Evaluation
        delay_model = DelayRiskModel()
        delayed_count = 0
        for p in projects:
            res = delay_model.predict_project(p)
            if res.get("delay_probability") and res["delay_probability"] > 0.5:
                delayed_count += 1
        logger.info(f"[Delay Model Evaluation]")
        logger.info(f" - Sample count: {len(projects)}")
        logger.info(f" - High delay risk (>50%): {delayed_count} projects")
        logger.info(f" - Evaluation: Baseline S-curve tracking active. Supervised precision/recall requires historical ground truth.")

        # 3. Physical Progress Model Status
        logger.info(f"[Physical Progress Vision Model]")
        logger.info(f" - Status: MODEL_NOT_TRAINED")
        logger.info(f" - Note: Domain-specific labelled construction image dataset not mounted.")

        return {
            "status": "COMPLETED",
            "eval_timestamp": pd.Timestamp.now().isoformat()
        }
    finally:
        db.close()

if __name__ == "__main__":
    evaluate_models()
