# -*- coding: utf-8 -*-
"""
Master Synthetic Dataset Generator and Database Loader.
Usage:
    python -m data_pipeline.synthetic.generate_all [--count 5000] [--seed 42]
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime, date
import pandas as pd

from backend.core.database import SessionLocal, engine, Base
from backend.models.models import (
    Project, ProjectFinancial, ProjectComponentState,
    ProjectProgressHistory, ProjectDocument, RiskScore, DataSource
)
from data_pipeline.synthetic.project_generator import generate_synthetic_projects
from data_pipeline.synthetic.component_generator import generate_project_components
from data_pipeline.synthetic.timeseries_generator import generate_progress_history
from data_pipeline.synthetic.document_generator import generate_project_documents

def compute_synthetic_risk(p: dict) -> dict:
    """
    Computes deterministic risk score and contributing factors for synthetic records.
    Higher risk for anomalies.
    """
    score = 15.0  # baseline
    factors = []

    # Financial checks
    sanction = p["sanction_amount"]
    released = p["released_amount"]
    expenditure = p["expenditure_amount"]
    progress = p["reported_progress"]

    if released > 0:
        utilization = (expenditure / released) * 100.0
        gap = utilization - progress
        if gap > 35.0:
            score += 35.0
            factors.append(f"Severe payment-progress mismatch: {utilization:.1f}% funds expended vs {progress:.1f}% physical progress")
        elif gap > 20.0:
            score += 20.0
            factors.append(f"Moderate disbursement lead: {utilization:.1f}% spent vs {progress:.1f}% progress")

    if expenditure > released:
        score += 30.0
        factors.append(f"Expenditure exceeds released funds (Overdraft of INR {expenditure - released:,.0f})")

    # Delay checks
    if p["status"] == "DELAYED":
        score += 25.0
        factors.append("Project timeline exceeded scheduled completion milestone")
    elif p["status"] == "STALLED":
        score += 40.0
        factors.append("Project stalled indefinitely with frozen execution")

    # Anomaly adjustments
    if p["anomaly_label"] == 1:
        score = max(score, 72.0)
        factors.append(f"Controlled synthetic anomaly pattern: {p['anomaly_category']}")

    final_score = min(98.5, max(5.0, score))
    tier = "CRITICAL" if final_score >= 80.0 else "HIGH" if final_score >= 60.0 else "MEDIUM" if final_score >= 30.0 else "LOW"

    return {
        "fused_risk_score": round(final_score, 1),
        "risk_tier": tier,
        "contributing_factors": factors if factors else ["Standard civil engineering schedule and disbursement"]
    }

def run_generator(count: int = 5000, seed: int = 42):
    print(f"\n=======================================================")
    print(f" NIRVANA Synthetic Development Dataset Generator")
    print(f" Target Projects: {count} | Deterministic Seed: {seed}")
    print(f"=======================================================\n")

    # Ensure all tables exist in SQLite
    Base.metadata.create_all(bind=engine)

    # 1. Generate Projects
    print(f"[1/5] Generating {count} synthetic project records...")
    projects = generate_synthetic_projects(count=count, seed=seed)
    
    # 2. Generate Components, History & Documents
    print(f"[2/5] Generating civil components, time-series history, and documents...")
    all_components = []
    all_history = []
    all_documents = []
    all_risk_scores = []

    today = date.today()

    for p in projects:
        proj_id = p["project_id"]
        ptype = p["project_type"]
        prog = p["reported_progress"]

        # Components
        comps = generate_project_components(proj_id, ptype, prog)
        all_components.extend(comps)

        # Progress history
        end_ref = p["actual_completion_date"] or (p["expected_completion_date"] if p["expected_completion_date"] < today else today)
        hist = generate_progress_history(
            proj_id, p["start_date"], end_ref, prog, p["expenditure_amount"], p["status"], p["anomaly_category"]
        )
        all_history.extend(hist)

        # Documents
        docs = generate_project_documents(
            proj_id, p["sanction_amount"], p["expenditure_amount"], prog, p["start_date"], p["agency"], p["anomaly_category"]
        )
        all_documents.extend(docs)

        # Risk scoring
        risk_info = compute_synthetic_risk(p)
        p["fused_risk_score"] = risk_info["fused_risk_score"]
        p["risk_tier"] = risk_info["risk_tier"]
        all_risk_scores.append({
            "project_id": proj_id,
            "fused_risk_score": risk_info["fused_risk_score"],
            "risk_tier": risk_info["risk_tier"],
            "contributing_factors_json": json.dumps(risk_info["contributing_factors"]),
            "confidence_score": 95.0,
            "created_at": datetime.utcnow()
        })

    # 3. Export CSV files
    print(f"[3/5] Exporting CSV files to dataset/synthetic/...")
    out_dir = Path("dataset/synthetic")
    out_dir.mkdir(parents=True, exist_ok=True)

    df_projects = pd.DataFrame(projects)
    df_projects.to_csv(out_dir / "synthetic_projects.csv", index=False)
    
    df_components = pd.DataFrame(all_components)
    df_components.to_csv(out_dir / "synthetic_components.csv", index=False)

    df_history = pd.DataFrame(all_history)
    df_history.to_csv(out_dir / "synthetic_progress_history.csv", index=False)

    df_documents = pd.DataFrame(all_documents)
    df_documents.to_csv(out_dir / "synthetic_documents.csv", index=False)

    print(f"   -> Wrote {len(df_projects)} projects to synthetic_projects.csv")
    print(f"   -> Wrote {len(df_components)} components to synthetic_components.csv")
    print(f"   -> Wrote {len(df_history)} history snapshots to synthetic_progress_history.csv")
    print(f"   -> Wrote {len(df_documents)} documents to synthetic_documents.csv")

    # 4. Database Persistence (SQLite)
    print(f"[4/5] Inserting synthetic records into database (strictly separating from real data)...")
    db = SessionLocal()
    try:
        # Create DataSource record if not present
        syn_source = db.query(DataSource).filter_by(source_type="SYNTHETIC").first()
        if not syn_source:
            syn_source = DataSource(
                source_name="NIRVANA Synthetic Development Architecture v1",
                source_url="internal://dataset/synthetic",
                source_type="SYNTHETIC",
                verification_status="SYNTHETIC",
                license="Internal Development & Evaluation Only",
                access_method="GENERATOR_PIPELINE"
            )
            db.add(syn_source)
            db.commit()
            db.refresh(syn_source)

        # Clear PREVIOUS synthetic projects without touching real data
        print("   -> Purging previous synthetic records (preserving all PUBLIC_VERIFIED government data)...")
        real_count_before = db.query(Project).filter(Project.data_status == "PUBLIC_VERIFIED").count()
        
        # Delete old synthetic records
        old_syn_ids = [row[0] for row in db.query(Project.project_id).filter(Project.data_status == "SYNTHETIC").all()]
        if old_syn_ids:
            # Batch delete in chunks of 500
            for i in range(0, len(old_syn_ids), 500):
                chunk = old_syn_ids[i:i+500]
                db.query(ProjectComponentState).filter(ProjectComponentState.project_id.in_(chunk)).delete(synchronize_session=False)
                db.query(ProjectProgressHistory).filter(ProjectProgressHistory.project_id.in_(chunk)).delete(synchronize_session=False)
                db.query(ProjectDocument).filter(ProjectDocument.project_id.in_(chunk)).delete(synchronize_session=False)
                db.query(RiskScore).filter(RiskScore.project_id.in_(chunk)).delete(synchronize_session=False)
                db.query(Project).filter(Project.project_id.in_(chunk)).delete(synchronize_session=False)
            db.commit()

        # Batch insert synthetic projects using bulk insert mappings
        print(f"   -> Inserting {len(projects)} synthetic projects...")
        for p in projects:
            p["source_id"] = syn_source.id
        
        db.bulk_insert_mappings(Project, projects)
        db.commit()

        print(f"   -> Inserting {len(all_components)} component states...")
        db.bulk_insert_mappings(ProjectComponentState, all_components)
        db.commit()

        print(f"   -> Inserting {len(all_history)} progress history records...")
        db.bulk_insert_mappings(ProjectProgressHistory, all_history)
        db.commit()

        print(f"   -> Inserting {len(all_documents)} document records...")
        db.bulk_insert_mappings(ProjectDocument, all_documents)
        db.commit()

        print(f"   -> Inserting {len(all_risk_scores)} risk score records...")
        db.bulk_insert_mappings(RiskScore, all_risk_scores)
        db.commit()

        # 5. Verification Check
        real_count_after = db.query(Project).filter(Project.data_status == "PUBLIC_VERIFIED").count()
        syn_count_after = db.query(Project).filter(Project.data_status == "SYNTHETIC").count()
        total_count = db.query(Project).count()

        assert real_count_before == real_count_after, "REAL DATA INTEGRITY VIOLATION DETECTED!"
        print(f"\n[5/5] Database Verification Successful:")
        print(f"   -> Verified Real MoSPI Projects Preserved: {real_count_after}")
        print(f"   -> Verified Synthetic Development Projects: {syn_count_after}")
        print(f"   -> Total Projects in Database: {total_count}")

    finally:
        db.close()

    print("\n=======================================================")
    print(" SYNTHETIC PIPELINE GENERATION COMPLETED SUCCESSFULLY!")
    print("=======================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic MPLADS development dataset")
    parser.add_argument("--count", type=int, default=5000, help="Number of synthetic projects to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    run_generator(count=args.count, seed=args.seed)
