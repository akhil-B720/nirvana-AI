import logging
from pathlib import Path
import pandas as pd
from backend.core.database import SessionLocal
from backend.models.models import Project, ModelVersion
from ml.models.cost_anomaly import CostAnomalyModel
from backend.core.config import settings
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("nirvana.ml.train.cost_anomaly")

def train():
    db = SessionLocal()
    try:
        projects = db.query(Project).all()
        if len(projects) < 3:
            logger.warning(f"INSUFFICIENT_DATA: Found only {len(projects)} projects. Minimum 3 required.")
            return {"status": "INSUFFICIENT_DATA"}

        data = [{
            "project_id": p.project_id,
            "sanction_amount": p.sanction_amount,
            "released_amount": p.released_amount,
            "expenditure_amount": p.expenditure_amount,
            "reported_progress": p.reported_progress
        } for p in projects]
        df = pd.DataFrame(data)

        model = CostAnomalyModel()
        metrics = model.fit(df)
        logger.info(f"Model fit complete. Metrics: {metrics}")

        model_path = settings.MODEL_DIR / "cost_anomaly" / "cost_anomaly.joblib"
        model.save(str(model_path))
        logger.info(f"Saved model to {model_path}")

        # Register in ModelVersion table
        mv = db.query(ModelVersion).filter_by(model_id="cost_anomaly_v1").first()
        if not mv:
            mv = ModelVersion(
                model_id="cost_anomaly_v1",
                model_name="CostAnomalyModel",
                version="1.0.0",
                training_data_version="dataset_v1",
                algorithm="Isolation Forest + Sector Robust Z-Score",
                features_json=json.dumps(model.feature_names),
                metrics_json=json.dumps(metrics),
                status="ACTIVE"
            )
            db.add(mv)
        else:
            mv.metrics_json = json.dumps(metrics)
            mv.training_timestamp = datetime.utcnow()
            mv.status = "ACTIVE"
        db.commit()
        logger.info("Registered model in model_versions table.")
        return metrics
    finally:
        db.close()

if __name__ == "__main__":
    train()
