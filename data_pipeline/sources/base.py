from abc import ABC, abstractmethod
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd

class BaseDataSource(ABC):
    def __init__(self, source_name: str, source_type: str, source_url: Optional[str] = None, license_info: str = "Government Open Data"):
        self.source_name = source_name
        self.source_type = source_type
        self.source_url = source_url
        self.license_info = license_info
        self.retrieval_timestamp = datetime.utcnow()
        self.file_hash: Optional[str] = None
        self.raw_data: Optional[pd.DataFrame] = None
        self.normalized_data: Optional[pd.DataFrame] = None
        self.quality_issues: List[Dict[str, Any]] = []

    def compute_sha256(self, content_bytes: bytes) -> str:
        sha = hashlib.sha256(content_bytes).hexdigest()
        self.file_hash = sha
        return sha

    @abstractmethod
    def fetch(self) -> pd.DataFrame:
        """Fetch or read source payload into DataFrame"""
        pass

    @abstractmethod
    def validate(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Validate records against domain constraints and return issues"""
        pass

    @abstractmethod
    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize schema, project types, coordinate formats, and dates"""
        pass

    @abstractmethod
    def load(self, db_session) -> int:
        """Persist records and provenance into relational database"""
        pass

    def record_provenance(self, db_session) -> int:
        """Create or update DataSource provenance entry in database"""
        from backend.models.models import DataSource
        
        ds = DataSource(
            source_name=self.source_name,
            source_url=self.source_url,
            source_type=self.source_type,
            retrieval_timestamp=self.retrieval_timestamp,
            license=self.license_info,
            access_method=getattr(self, "access_method", "FILE_INGEST"),
            verification_status=getattr(self, "verification_status", "PUBLIC_VERIFIED"),
            file_hash=self.file_hash
        )
        db_session.add(ds)
        db_session.commit()
        db_session.refresh(ds)
        return ds.id
