import json
import logging
import urllib.request
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import pandas as pd

from data_pipeline.sources.base import BaseDataSource
from data_pipeline.validators.quality_engine import DataQualityEngine
from data_pipeline.normalizers.normalizer import DataNormalizer
from backend.models.models import Project, DataQualityIssue, ProjectLocation

logger = logging.getLogger("nirvana.pipeline.empowered_indian")

class EmpoweredIndianDataSource(BaseDataSource):
    """
    Test importer for Empowered Indian (https://empoweredindian.in),
    a third-party citizen-led civic transparency platform backed by Malpani Ventures.
    
    PROVENANCE & COMPLIANCE:
    - Domain: empoweredindian.in (Non-government third-party civic aggregator).
    - Lawful Access: robots.txt allows public crawling; API does not require login or CAPTCHA bypass.
    - Status: Tagged strictly as UNVERIFIED_THIRD_PARTY.
    - Policy: Does NOT claim data as official government truth until cross-reconciled.
    """

    DEFAULT_API_URL = "https://api.empoweredindian.in/api/works/completed"

    def __init__(self, endpoint_url: Optional[str] = None, sample_size: int = 5):
        url = endpoint_url or f"{self.DEFAULT_API_URL}?page=1&limit={sample_size}"
        super().__init__(
            source_name="Empowered Indian (Third-Party Civic Aggregator)",
            source_type="THIRD_PARTY_CIVIC_AGGREGATOR",
            source_url=url,
            license_info="Open Civic Data / Attributed to MoSPI MPLADS Portal"
        )
        self.sample_size = sample_size
        self.verification_status = "UNVERIFIED_THIRD_PARTY"
        self.access_method = "REST_API_PAGINATED"
        self.raw_json: Optional[Dict[str, Any]] = None
        self.raw_payload_bytes: Optional[bytes] = None
        self.quality_score: float = 100.0

    def fetch(self) -> pd.DataFrame:
        logger.info(f"Fetching {self.sample_size} records from Empowered Indian API: {self.source_url}")
        self.retrieval_timestamp = datetime.now(timezone.utc)
        
        req = urllib.request.Request(self.source_url, headers={
            "User-Agent": "NIRVANA-Research-Agent/1.0 (Academic Verification System; SIH26102)",
            "Accept": "application/json"
        })

        with urllib.request.urlopen(req, timeout=15) as resp:
            self.raw_payload_bytes = resp.read()
            self.compute_sha256(self.raw_payload_bytes)
            self.raw_json = json.loads(self.raw_payload_bytes.decode("utf-8"))

        works = self.raw_json.get("data", {}).get("completedWorks", [])
        logger.info(f"Retrieved {len(works)} completed works from Empowered Indian. SHA-256: {self.file_hash}")

        # Transform into raw DataFrame preserving original fields
        records = []
        for w in works:
            mp = w.get("mp_details", {})
            w_id = str(w.get("work_id", w.get("_id", "")))
            records.append({
                "ei_id": str(w.get("_id", "")),
                "work_id": str(w.get("work_id", "")),
                "project_id": f"EI-WORK-{w_id}",
                "project_name": str(w.get("work_description", "")).strip(),
                "category": str(w.get("category", "Normal/Others")),
                "state": str(w.get("state", "Unknown")),
                "district": str(w.get("district", "Unknown")),
                "location_raw": str(w.get("location", "")),
                "cost": float(w.get("cost", 0.0) or 0.0),
                "completion_date": w.get("completion_date"),
                "completion_year": w.get("completion_year"),
                "beneficiaries": w.get("beneficiaries", 0),
                "mp_name": str(mp.get("name", "")),
                "mp_constituency": str(mp.get("constituency", "")),
                "mp_party": str(mp.get("party", "")),
                "retrieval_timestamp": self.retrieval_timestamp.isoformat(),
                "source_url": self.source_url
            })

        self.raw_data = pd.DataFrame(records)
        return self.raw_data

    def validate(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        target_df = self.normalize(df) if self.normalized_data is None else self.normalized_data
        self.quality_issues, self.quality_score = DataQualityEngine.validate_dataset(target_df)
        return self.quality_issues

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        norm_rows = []
        for idx, r in df.iterrows():
            st = r["state"]
            centroid = DataNormalizer.STATE_CENTROIDS.get(st, (22.5, 78.5))
            jitter_seed = (hash(str(r.get("location_raw", "")) + str(idx)) % 1000 - 500) / 1000.0
            lat = round(centroid[0] + (jitter_seed * 0.4), 4)
            lon = round(centroid[1] + (jitter_seed * 0.4), 4)

            p_type = DataNormalizer.normalize_project_type(r.get("category"), r.get("project_name"))
            cost = float(r.get("cost", 0.0))

            norm_rows.append({
                "project_id": r["project_id"],
                "project_name": r["project_name"],
                "project_type": p_type,
                "sector": r.get("category", "Community Infrastructure"),
                "state": st,
                "district": r["district"],
                "constituency": r.get("mp_constituency"),
                "block": None,
                "village": None,
                "latitude": lat,
                "longitude": lon,
                "sanction_amount": cost,
                "released_amount": cost,
                "expenditure_amount": cost,
                "start_date": None,
                "expected_completion_date": None,
                "actual_completion_date": DataNormalizer.clean_date(r.get("completion_date")),
                "reported_progress": 100.0,
                "observed_progress": None,  # Ground observation unverified
                "observed_progress_status": "NOT_AVAILABLE",
                "status": "COMPLETED",
                "agency": r.get("location_raw"),
                "data_availability_status": "UNVERIFIED_THIRD_PARTY"
            })

        self.normalized_data = pd.DataFrame(norm_rows)
        return self.normalized_data

    def load(self, db_session) -> int:
        if self.normalized_data is None:
            raise ValueError("Must normalize before loading.")

        source_id = self.record_provenance(db_session)
        loaded_count = 0

        for _, row in self.normalized_data.iterrows():
            p_id = row["project_id"]
            existing = db_session.query(Project).filter_by(project_id=p_id).first()
            if not existing:
                p = Project(
                    project_id=p_id,
                    project_name=row["project_name"],
                    project_type=row["project_type"],
                    sector=row["sector"],
                    state=row["state"],
                    district=row["district"],
                    constituency=row["constituency"],
                    latitude=row["latitude"],
                    longitude=row["longitude"],
                    sanction_amount=row["sanction_amount"],
                    released_amount=row["released_amount"],
                    expenditure_amount=row["expenditure_amount"],
                    actual_completion_date=pd.to_datetime(row["actual_completion_date"]).date() if row["actual_completion_date"] else None,
                    reported_progress=100.0,
                    observed_progress=None,
                    observed_progress_status="NOT_AVAILABLE",
                    status="COMPLETED",
                    agency=row["agency"],
                    source_id=source_id,
                    data_availability_status="UNVERIFIED_THIRD_PARTY"
                )
                db_session.add(p)
                loaded_count += 1

        db_session.commit()
        return loaded_count
