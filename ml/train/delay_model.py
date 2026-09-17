import logging
import json
from datetime import datetime
from backend.core.database import SessionLocal
from backend.models.models import Project, ModelVersion
from ml.models.delay_model import DelayRiskModel
from backend.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("nirvana.ml.train.delay_model")

def train():
    db = SessionLocal()
    try:
        projects = db.query(Project).all()
        if not projects:
            logger.warning("INSUFFICIENT_DATA: No projects found in database.")
            return {"status": "INSUFFICIENT_DATA"}

        model = DelayRiskModel()
        model_path = settings.MODEL_DIR / "delay" / "delay_model.joblib"
        model.save(str(model_path))
        logger.info(f"Saved delay model baseline to {model_path}")

        metrics = {
            "baseline_type": "Analytical Construction S-Curve",
            "sample_size": len(projects),
            "status": "ACTIVE"
        }

        mv = db.query(ModelVersion).filter_by(model_id="delay_model_v1").first()
        if not mv:
            mv = ModelVersion(
                model_id="delay_model_v1",
                model_name="DelayRiskModel",
                version="1.0.0",
                training_data_version="baseline_scurve_v1",
                algorithm="Mathematical Construction S-Curve + Rate Projection",
                features_json=json.dumps(["planned_duration", "elapsed_days", "reported_progress"]),
                metrics_json=json.dumps(metrics),
                status="ACTIVE"
            )
            db.add(mv)
        else:
            mv.metrics_json = json.dumps(metrics)
            mv.training_timestamp = datetime.utcnow()
        db.commit()
        logger.info("Delay model registered successfully.")
        return metrics
    finally:
        db.close()

if __name__ == "__main__":
    train()
