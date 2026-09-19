import logging
import json
from datetime import datetime
from pathlib import Path
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, roc_auc_score

from backend.core.database import SessionLocal
from backend.models.models import Project, ModelVersion
from ml.models.delay_model import DelayRiskModel
from backend.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("nirvana.ml.train.delay_model")

def train():
    db = SessionLocal()
    try:
        # Load synthetic projects with defined timeline parameters
        projects = (
            db.query(Project)
            .filter(
                Project.data_status == "SYNTHETIC",
                Project.start_date.isnot(None),
                Project.expected_completion_date.isnot(None)
            )
            .all()
        )

        if len(projects) < 50:
            logger.warning(f"INSUFFICIENT_DATA: Found only {len(projects)} synthetic projects. Need at least 50.")
            return {"status": "INSUFFICIENT_DATA"}

        logger.info(f"Preparing supervised training dataset from {len(projects)} synthetic projects...")
        model = DelayRiskModel()

        X_list = []
        y_days_list = []
        y_delayed_list = []

        for p in projects:
            feat = model.extract_features(p)
            if feat is None:
                continue

            planned_days = feat[0]
            start_d = p.start_date
            exp_d = p.expected_completion_date
            act_d = p.actual_completion_date

            if act_d:
                actual_days = (act_d - start_d).days
                delay_days = max(0, actual_days - planned_days)
            elif p.status == "DELAYED":
                elapsed = (datetime.utcnow().date() - start_d).days
                delay_days = max(15, elapsed - planned_days + int((100.0 - (p.reported_progress or 0.0)) * 2.0))
            else:
                elapsed = (datetime.utcnow().date() - start_d).days
                if elapsed > planned_days and (p.reported_progress or 0) < 90:
                    delay_days = max(10, elapsed - planned_days)
                else:
                    delay_days = 0

            is_delayed = 1 if delay_days > 0 else 0

            X_list.append(feat)
            y_days_list.append(delay_days)
            y_delayed_list.append(is_delayed)

        X = np.array(X_list)
        y_days = np.array(y_days_list)
        y_delayed = np.array(y_delayed_list)

        # Train / Test Split (80% Train, 20% Test)
        X_train, X_test, y_train_days, y_test_days, y_train_del, y_test_del = train_test_split(
            X, y_days, y_delayed, test_size=0.2, random_state=42
        )

        logger.info(f"Training supervised models on {len(X_train)} samples, evaluating on {len(X_test)} hold-out samples...")
        model.fit(X_train, y_train_days, y_train_del)

        # Evaluate on Hold-out Test Set
        pred_days = model.regressor.predict(X_test)
        pred_days = np.clip(pred_days, 0, None)
        pred_probs = model.classifier.predict_proba(X_test)[:, 1]
        pred_del = model.classifier.predict(X_test)

        mae = round(float(mean_absolute_error(y_test_days, pred_days)), 2)
        rmse = round(float(np.sqrt(mean_squared_error(y_test_days, pred_days))), 2)
        r2 = round(float(r2_score(y_test_days, pred_days)), 3)
        acc = round(float(accuracy_score(y_test_del, pred_del)), 3)
        auc = round(float(roc_auc_score(y_test_del, pred_probs)), 3)

        metrics = {
            "dataset_type": "SYNTHETIC_TEST_DATA",
            "evaluation_note": "Synthetic development-data evaluation",
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "regression_mae_days": mae,
            "regression_rmse_days": rmse,
            "regression_r2_score": r2,
            "classification_accuracy": acc,
            "classification_roc_auc": auc,
            "algorithm": "Gradient Boosting Regressor & Classifier (100 estimators each)",
            "status": "ACTIVE"
        }
        model.metrics = metrics

        model_path = settings.MODEL_DIR / "delay" / "delay_model.joblib"
        model.save(str(model_path))
        logger.info(f"Saved trained delay model artifact to {model_path}")
        logger.info(f"Supervised Evaluation Metrics: {json.dumps(metrics, indent=2)}")

        # Register in ModelVersion table
        mv = db.query(ModelVersion).filter_by(model_id="delay_model_v2").first()
        if not mv:
            mv = ModelVersion(
                model_id="delay_model_v2",
                model_name="SupervisedDelayRiskModel",
                version="2.0.0",
                training_data_version="synthetic_multi_month_v1",
                algorithm="Gradient Boosting Regressor + Classifier",
                features_json=json.dumps(DelayRiskModel.FEATURE_NAMES),
                metrics_json=json.dumps(metrics),
                status="ACTIVE"
            )
            db.add(mv)
        else:
            mv.metrics_json = json.dumps(metrics)
            mv.training_timestamp = datetime.utcnow()
            mv.status = "ACTIVE"

        db.commit()
        logger.info("Delay model v2 registered successfully.")
        return metrics
    finally:
        db.close()

if __name__ == "__main__":
    train()
