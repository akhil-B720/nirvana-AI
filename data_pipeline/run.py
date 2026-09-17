import sys
import logging
from pathlib import Path
from backend.core.database import SessionLocal, engine, Base
import backend.models
from data_pipeline.sources.csv_source import CSVDataSource
from backend.models.models import Project, ProjectEvent, ProjectFinancial

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("nirvana.data_pipeline")

def run_pipeline():
    logger.info("Initializing NIRVANA Data Pipeline...")
    
    # Ensure database schema is created
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        base_dir = Path(__file__).resolve().parent.parent
        synthetic_csv = base_dir / "dataset" / "synthetic" / "fixtures.csv"
        
        total_ingested = 0
        if synthetic_csv.exists():
            logger.info(f"Ingesting synthetic test fixtures from {synthetic_csv}...")
            src = CSVDataSource(
                file_path=str(synthetic_csv),
                source_name="Synthetic MPLADS Test Fixtures",
                is_synthetic=True
            )
            df_raw = src.fetch()
            logger.info(f"Fetched {len(df_raw)} records. SHA-256: {src.file_hash}")
            
            issues = src.validate(df_raw)
            logger.info(f"Data Quality Score: {src.quality_score}%. Identified {len(issues)} validation issues.")
            
            df_norm = src.normalize(df_raw)
            loaded = src.load(db)
            total_ingested += loaded
            logger.info(f"Successfully loaded {loaded} synthetic projects into relational database.")

        # Ingest real government records if available
        real_csv = base_dir / "dataset" / "raw" / "real_mplads_works.csv"
        if real_csv.exists():
            logger.info(f"Ingesting real government MPLADS records from {real_csv}...")
            gov_src = CSVDataSource(
                file_path=str(real_csv),
                source_name="Official MoSPI MPLADS Records (ODbL)",
                verification_status="PUBLIC_VERIFIED",
                is_synthetic=False,
                max_rows=150
            )
            gov_raw = gov_src.fetch()
            logger.info(f"Fetched {len(gov_raw)} real government records. SHA-256: {gov_src.file_hash}")
            
            gov_issues = gov_src.validate(gov_raw)
            logger.info(f"Real Data Quality Score: {gov_src.quality_score}%. Identified {len(gov_issues)} validation issues.")
            
            gov_norm = gov_src.normalize(gov_raw)
            gov_loaded = gov_src.load(db)
            total_ingested += gov_loaded
            logger.info(f"Successfully loaded {gov_loaded} real government projects into relational database.")

        # Seed financial transactions and events if needed
        for p in db.query(Project).all():
            if not p.financials and p.sanction_amount > 0:
                if p.start_date:
                    f1 = ProjectFinancial(
                        project_id=p.project_id,
                        transaction_date=p.start_date,
                        transaction_type="SANCTION",
                        amount=p.sanction_amount,
                        installment_number=1
                    )
                    db.add(f1)
                if p.released_amount > 0 and p.start_date:
                    f2 = ProjectFinancial(
                        project_id=p.project_id,
                        transaction_date=p.start_date,
                        transaction_type="RELEASE",
                        amount=p.released_amount,
                        installment_number=1
                    )
                    db.add(f2)
                if p.expenditure_amount > 0 and p.start_date:
                    f3 = ProjectFinancial(
                        project_id=p.project_id,
                        transaction_date=p.start_date,
                        transaction_type="EXPENDITURE",
                        amount=p.expenditure_amount,
                        installment_number=1
                    )
                    db.add(f3)
            
            if not p.events and p.start_date:
                ev = ProjectEvent(
                    project_id=p.project_id,
                    event_date=p.start_date,
                    event_type="SANCTION",
                    title=f"Work Sanctioned: {p.project_name[:50]}...",
                    description=f"Administrative sanction accorded under MPLADS for ₹{p.sanction_amount:,.2f}",
                    actor="District Authority"
                )
                db.add(ev)
        
        db.commit()
        logger.info("Financial ledger & project event timeline initialized.")
            
        logger.info(f"Pipeline execution completed successfully. Total active projects: {total_ingested}")
        return total_ingested
    finally:
        db.close()

if __name__ == "__main__":
    run_pipeline()
