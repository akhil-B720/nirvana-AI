import logging
import json
from datetime import datetime
from backend.core.database import SessionLocal
from backend.models.models import Project, ModelVersion
from ml.models.similarity_model import SimilarityEngine
from backend.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("nirvana.ml.train.similarity_model")

def train():
    db = SessionLocal()
    try:
        projects = db.query(Project).all()
        if not projects:
            logger.warning("INSUFFICIENT_DATA: No projects found in database.")
            return {"status": "INSUFFICIENT_DATA"}

        engine_model = SimilarityEngine()
        res = engine_model.fit(projects)
        logger.info(f"Similarity Engine fit complete: {res}")

        model_path = settings.MODEL_DIR / "similarity" / "similarity_model.joblib"
        engine_model.save(str(model_path))
        logger.info(f"Saved similarity model to {model_path}")

        mv = db.query(ModelVersion).filter_by(model_id="similarity_engine_v1").first()
        if not mv:
            mv = ModelVersion(
                model_id="similarity_engine_v1",
                model_name="SimilarityEngine",
                version="1.0.0",
                training_data_version="corpus_v1",
                algorithm="TF-IDF Cosine Similarity + Geodesic Haversine",
                features_json=json.dumps(["project_name", "sector", "project_type", "latitude", "longitude"]),
                metrics_json=json.dumps(res),
                status="ACTIVE"
            )
            db.add(mv)
        else:
            mv.metrics_json = json.dumps(res)
            mv.training_timestamp = datetime.utcnow()
        db.commit()
        logger.info("Similarity engine registered successfully.")
        return res
    finally:
        db.close()

if __name__ == "__main__":
    train()
