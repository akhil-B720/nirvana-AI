import sys
import logging
from pathlib import Path
from datetime import datetime, timezone
import json

from data_pipeline.processors.macro_pipeline import MacroDataPipeline
from ml.models.macro_risk_analyzer import MacroRiskAnalyzer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("nirvana.ml.train_macro")

def run_macro_training():
    logger.info("Starting NIRVANA Macro Risk Pipeline & Model Training...")
    
    # 1. Pipeline: Ingest, Clean, Normalize, Engineer Features
    pipeline = MacroDataPipeline()
    df_yearly, df_sectors, df_unspent, df_master = pipeline.run()
    logger.info(f"Feature matrix built for {len(df_master)} State/UT entities.")

    # 2. Train ML Analyzer
    analyzer = MacroRiskAnalyzer(n_clusters=4, contamination=0.15, random_state=42)
    analyzer.fit(df_master)

    # 3. Predict & Stratify
    df_results = analyzer.predict(df_master)
    logger.info("Anomaly and risk clustering evaluation completed.")

    # 4. Save Model Artifact
    model_path = analyzer.save("models/macro_risk")
    
    # 5. Persist to Database
    inserted = pipeline.persist_to_database(df_yearly, df_sectors, df_unspent, df_results)
    logger.info(f"Successfully saved all {inserted} records to database.")

    # 6. Print Summary Report
    print("\n" + "="*70)
    print("NIRVANA MACRO MPLADS RISK ANALYSIS - TRAINING & INFERENCE REPORT")
    print("="*70)
    print(f"Total States & UTs Processed: {len(df_results)}")
    print(f"Model Artifact: {model_path}")
    print(f"Clustering Silhouette Score: {analyzer.metrics['silhouette_score']}")
    print(f"PCA Cumulative Variance (2D): {analyzer.metrics['pca_cumulative_variance']}")
    print(f"Cluster Profiles:")
    for cid, name in analyzer.metrics["cluster_profiles"].items():
        count = (df_results["risk_cluster"] == int(cid)).sum()
        print(f"  - Cluster {cid} ({name}): {count} States/UTs")

    print("\nRisk Tier Distribution:")
    print(df_results["risk_tier"].value_counts().to_string())

    print("\nTop Anomalous / High-Backlog States:")
    cols_display = ["state", "total_expenditure_4yr_crore", "unspent_balance_crore", "backlog_absorption_years", "anomaly_score", "risk_tier"]
    anom_states = df_results.sort_values(by="anomaly_score", ascending=False).head(8)
    print(anom_states[cols_display].to_string(index=False))

    print("\nStatutory Advisory:")
    print("AI-generated risk indicators are decision-support signals and do not constitute proof of fraud, corruption, or wrongdoing.")
    print("="*70)

    # Export report to reports/macro_training_summary.json
    rep_path = Path("reports/macro_training_summary.json")
    rep_path.parent.mkdir(parents=True, exist_ok=True)
    summary_data = {
        "metrics": analyzer.metrics,
        "risk_distribution": df_results["risk_tier"].value_counts().to_dict(),
        "top_anomalies": anom_states[cols_display].to_dict(orient="records"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    with open(rep_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    logger.info(f"Summary JSON saved to {rep_path}")
    return df_results

if __name__ == "__main__":
    run_macro_training()
