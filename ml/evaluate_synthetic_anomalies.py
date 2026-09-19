import os
import json
import logging
from pathlib import Path
from datetime import datetime
import numpy as np
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support, confusion_matrix

from backend.core.database import SessionLocal
from backend.models.models import Project
from ml.models.project_risk_model import ProjectRiskModel
from backend.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("nirvana.ml.evaluate_synthetic_anomalies")

def evaluate():
    db = SessionLocal()
    try:
        from backend.models.models import RiskScore

        logger.info("Loading synthetic project scores from database for evaluation...")
        rows = (
            db.query(
                Project.project_id,
                Project.anomaly_label,
                Project.anomaly_category,
                RiskScore.fused_risk_score
            )
            .join(RiskScore, Project.project_id == RiskScore.project_id)
            .filter(Project.data_status == "SYNTHETIC")
            .all()
        )
        if not rows:
            logger.error("No synthetic projects found in database. Run synthetic generator first.")
            return

        logger.info(f"Loaded {len(rows)} synthetic project records.")

        y_true = []
        y_scores = []
        categories = []
        project_ids = []

        for r in rows:
            p_id, label, cat, score = r
            y_true.append(int(label or 0))
            y_scores.append(float(score or 0.0))
            categories.append(str(cat or "NORMAL"))
            project_ids.append(p_id)

        y_true = np.array(y_true)
        y_scores = np.array(y_scores)

        # Compute ROC-AUC
        auc = round(float(roc_auc_score(y_true, y_scores)), 4)

        # Threshold analysis (e.g., risk_score >= 50.0 as positive flag)
        threshold = 50.0
        y_pred = (y_scores >= threshold).astype(int)

        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="binary", zero_division=0)

        # Category-level recall analysis
        cat_metrics = {}
        unique_cats = sorted(list(set(categories)))
        for cat in unique_cats:
            indices = [i for i, c in enumerate(categories) if c == cat]
            sub_true = y_true[indices]
            sub_pred = y_pred[indices]
            total_cat = len(indices)
            flagged_cat = int(np.sum(sub_pred))
            if cat == "NORMAL":
                # For normal, specificity is what matters (true negative rate)
                specificity = round(float(np.sum(sub_pred == 0) / total_cat), 4)
                cat_metrics[cat] = {
                    "sample_count": total_cat,
                    "correctly_unflagged": int(np.sum(sub_pred == 0)),
                    "false_positive_count": flagged_cat,
                    "specificity": specificity
                }
            else:
                det_rate = round(float(flagged_cat / total_cat), 4) if total_cat > 0 else 0.0
                cat_metrics[cat] = {
                    "sample_count": total_cat,
                    "detected_anomalies": flagged_cat,
                    "detection_rate": det_rate
                }

        report = {
            "evaluation_title": "Project-Level Analytical Anomaly Detection — Synthetic Benchmark",
            "evaluation_type": "SYNTHETIC_TEST_DATA",
            "dataset": f"synthetic_projects ({len(rows)} records)",
            "evaluation_timestamp": datetime.utcnow().isoformat(),
            "sample_size": len(rows),
            "normal_samples": int(np.sum(y_true == 0)),
            "anomaly_samples": int(np.sum(y_true == 1)),
            "threshold_used": threshold,
            "overall_metrics": {
                "roc_auc": auc,
                "precision": round(float(precision), 4),
                "recall": round(float(recall), 4),
                "f1_score": round(float(f1), 4),
                "true_positives": int(tp),
                "false_positives": int(fp),
                "true_negatives": int(tn),
                "false_negatives": int(fn)
            },
            "category_detection_rates": cat_metrics,
            "statutory_classification": "Synthetic Development-Data Evaluation Only",
            "disclaimer": (
                "These evaluation metrics were obtained strictly on synthetic development datasets "
                "with controlled mathematical anomaly injections. They must NEVER be represented as "
                "real-world government audit precision, false-positive rates, or judicial fraud evidence."
            )
        }

        # Save report
        reports_dir = Path("ml/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_file = reports_dir / "synthetic_anomaly_evaluation.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Saved evaluation report to {report_file}")
        logger.info(f"Synthetic Anomaly Evaluation Summary: ROC-AUC={auc}, Precision={precision:.3f}, Recall={recall:.3f}, F1={f1:.3f}")
        return report

    finally:
        db.close()

if __name__ == "__main__":
    evaluate()
