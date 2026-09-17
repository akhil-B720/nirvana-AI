import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd

from data_pipeline.sources.base import BaseDataSource
from data_pipeline.validators.quality_engine import DataQualityEngine
from data_pipeline.normalizers.normalizer import DataNormalizer
from backend.models.models import Project, DataQualityIssue, ProjectLocation

class CSVDataSource(BaseDataSource):
    def __init__(self, file_path: str, source_name: Optional[str] = None, verification_status: str = "PUBLIC_VERIFIED", is_synthetic: bool = False, max_rows: Optional[int] = None, stratified: bool = False):
        p = Path(file_path)
        name = source_name or f"CSV Import: {p.name}"
        source_type = "SYNTHETIC" if is_synthetic else "GOVERNMENT_PORTAL"
        v_status = "SYNTHETIC" if is_synthetic else verification_status
        super().__init__(source_name=name, source_type=source_type, source_url=f"file://{p.resolve()}")
        self.file_path = p
        self.verification_status = v_status
        self.is_synthetic = is_synthetic
        self.max_rows = max_rows
        self.stratified = stratified
        self.access_method = "CSV_INGEST"
        self.quality_score: float = 100.0

    def fetch(self) -> pd.DataFrame:
        if not self.file_path.exists():
            raise FileNotFoundError(f"Source file not found at: {self.file_path}")

        raw_bytes = self.file_path.read_bytes()
        self.compute_sha256(raw_bytes)

        # Handle delimiters and encodings gracefully
        df = None
        for sep in [";", ",", "\t"]:
            try:
                candidate = pd.read_csv(self.file_path, sep=sep, nrows=None if self.stratified else self.max_rows, encoding="utf-8", low_memory=False)
                if len(candidate.columns) > 1:
                    df = candidate
                    break
            except UnicodeDecodeError:
                try:
                    candidate = pd.read_csv(self.file_path, sep=sep, nrows=None if self.stratified else self.max_rows, encoding="latin-1", low_memory=False)
                    if len(candidate.columns) > 1:
                        df = candidate
                        break
                except Exception:
                    pass
            except Exception:
                continue

        if df is None:
            df = pd.read_csv(self.file_path, nrows=self.max_rows)

        if self.stratified and "STATUS" in df.columns:
            completed = df[df["STATUS"] == "Completed"]
            ongoing = df[df["STATUS"] == "Ongoing"]
            sanctioned = df[df["STATUS"] == "Sanctioned"]
            if len(sanctioned) > 1000:
                sanctioned = sanctioned.sample(n=1000, random_state=42)
            unsanctioned = df[df["STATUS"] == "Unsanctioned"]
            if len(unsanctioned) > 100:
                unsanctioned = unsanctioned.sample(n=100, random_state=42)
            df = pd.concat([completed, ongoing, sanctioned, unsanctioned])

        self.raw_data = df
        return self.raw_data

    def validate(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        target_df = DataNormalizer.normalize_dataframe(df) if "WORK" in df.columns else df
        self.quality_issues, self.quality_score = DataQualityEngine.validate_dataset(target_df)
        return self.quality_issues

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        self.normalized_data = DataNormalizer.normalize_dataframe(df)
        return self.normalized_data

    def load(self, db_session) -> int:
        if self.normalized_data is None:
            raise ValueError("Cannot load data before normalization. Call normalize() first.")

        # 1. Record provenance
        source_id = self.record_provenance(db_session)

        # 2. Record data quality issues
        for issue in self.quality_issues:
            dqi = DataQualityIssue(
                project_id=issue.get("project_id"),
                issue_type=issue.get("issue_type", "UNKNOWN"),
                severity=issue.get("severity", "WARNING"),
                details=issue.get("details", ""),
                original_value=issue.get("original_value")
            )
            db_session.add(dqi)

        # 3. Ingest projects with cached lookup
        existing_projects = {p.project_id: p for p in db_session.query(Project).all()}
        loaded_count = 0
        for _, row in self.normalized_data.iterrows():
            p_id = str(row.get("project_id", "")).strip()
            if not p_id or p_id.lower() in ("nan", "none", "null"):
                continue

            existing = existing_projects.get(p_id)
            if existing:
                # Update existing
                existing.project_name = str(row.get("project_name", existing.project_name))
                existing.project_type = str(row.get("project_type", existing.project_type))
                existing.sector = row.get("sector")
                existing.state = str(row.get("state", existing.state))
                existing.district = str(row.get("district", existing.district))
                existing.constituency = row.get("constituency")
                existing.block = row.get("block")
                existing.village = row.get("village")
                existing.latitude = float(row["latitude"]) if pd.notna(row.get("latitude")) else None
                existing.longitude = float(row["longitude"]) if pd.notna(row.get("longitude")) else None
                existing.sanction_amount = float(row.get("sanction_amount", 0.0))
                existing.released_amount = float(row.get("released_amount", 0.0))
                existing.expenditure_amount = float(row.get("expenditure_amount", 0.0))
                existing.reported_progress = float(row.get("reported_progress", 0.0))
                existing.observed_progress = float(row["observed_progress"]) if pd.notna(row.get("observed_progress")) else None
                existing.observed_progress_status = "AI_ESTIMATE" if pd.notna(row.get("observed_progress")) else "NOT_AVAILABLE"
                existing.source_id = source_id
                existing.data_availability_status = "SYNTHETIC" if self.is_synthetic else "PUBLIC_VERIFIED"
                existing.updated_at = datetime.utcnow()
            else:
                p = Project(
                    project_id=p_id,
                    project_name=str(row.get("project_name", f"Project {p_id}")),
                    project_type=str(row.get("project_type", "OTHER")),
                    sector=row.get("sector"),
                    state=str(row.get("state", "Unknown")),
                    district=str(row.get("district", "Unknown")),
                    constituency=row.get("constituency"),
                    block=row.get("block"),
                    village=row.get("village"),
                    latitude=float(row["latitude"]) if pd.notna(row.get("latitude")) else None,
                    longitude=float(row["longitude"]) if pd.notna(row.get("longitude")) else None,
                    sanction_amount=float(row.get("sanction_amount", 0.0)),
                    released_amount=float(row.get("released_amount", 0.0)),
                    expenditure_amount=float(row.get("expenditure_amount", 0.0)),
                    start_date=pd.to_datetime(row.get("start_date")).date() if pd.notna(row.get("start_date")) else None,
                    expected_completion_date=pd.to_datetime(row.get("expected_completion_date")).date() if pd.notna(row.get("expected_completion_date")) else None,
                    actual_completion_date=pd.to_datetime(row.get("actual_completion_date")).date() if pd.notna(row.get("actual_completion_date")) else None,
                    reported_progress=float(row.get("reported_progress", 0.0)),
                    observed_progress=float(row["observed_progress"]) if pd.notna(row.get("observed_progress")) else None,
                    observed_progress_status="AI_ESTIMATE" if pd.notna(row.get("observed_progress")) else "NOT_AVAILABLE",
                    status=str(row.get("status", "IN_PROGRESS")),
                    agency=row.get("agency"),
                    source_id=source_id,
                    data_availability_status="SYNTHETIC" if self.is_synthetic else "PUBLIC_VERIFIED"
                )
                db_session.add(p)

                # Add location record if coordinates exist
                if p.latitude is not None and p.longitude is not None:
                    loc = ProjectLocation(
                        project_id=p.project_id,
                        latitude=p.latitude,
                        longitude=p.longitude,
                        address=f"{p.village or ''}, {p.block or ''}, {p.district}, {p.state}".strip(", ")
                    )
                    db_session.add(loc)

            loaded_count += 1

        db_session.commit()
        return loaded_count
