import json
import logging
from datetime import datetime
from pathlib import Path
from backend.core.database import SessionLocal
from backend.models.models import Project, ModelVersion
from ml.models.project_risk_model import ProjectRiskModel
from backend.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("nirvana.ml.train.project_risk")


def train_project_risk_model():
    """
    Trains ProjectRiskModel on active projects in the database.
    Computes empirical sector/state baselines, fits Isolation Forest,
    saves the serialized artifact, and registers it in model_versions.
    """
    db = SessionLocal()
    try:
        logger.info("Loading projects from database for project risk model training...")
        projects = db.query(Project).all()
        logger.info(f"Loaded {len(projects)} total projects.")

        if len(projects) < 5:
            logger.warning(f"INSUFFICIENT_DATA: Found only {len(projects)} projects. Minimum 5 required.")
            return {"status": "INSUFFICIENT_DATA"}

        model = ProjectRiskModel(contamination=0.10, random_state=42)
        metrics = model.fit(projects)
        logger.info(f"Training completed successfully. Metrics: {metrics}")

        model_dir = settings.MODEL_DIR / "project_risk"
        model_dir.mkdir(parents=True, exist_ok=True)
        model_path = model_dir / "project_risk_model.joblib"
        model.save(str(model_path))
        logger.info(f"Saved project risk model artifact to {model_path}")

        # Register in ModelVersion table
        mv = db.query(ModelVersion).filter_by(model_id="project_risk_v1").first()
        if not mv:
            mv = ModelVersion(
                model_id="project_risk_v1",
                model_name="ProjectRiskModel",
                version="1.0.0",
                training_data_version="mospi_mplads_works_v1",
                algorithm="Isolation Forest (150 trees) + Robust Sector/State MAD",
                features_json=json.dumps(model.FEATURE_NAMES),
                metrics_json=json.dumps(metrics),
                status="ACTIVE"
            )
            db.add(mv)
        else:
            mv.metrics_json = json.dumps(metrics)
            mv.features_json = json.dumps(model.FEATURE_NAMES)
            mv.training_timestamp = datetime.utcnow()
            mv.status = "ACTIVE"

        db.commit()
        logger.info("Registered model version project_risk_v1 in model_versions table.")
        return metrics
    finally:
        db.close()


if __name__ == "__main__":
    train_project_risk_model()
