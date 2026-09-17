import os
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import requests

from data_pipeline.sources.base import BaseDataSource
from data_pipeline.validators.quality_engine import DataQualityEngine
from data_pipeline.normalizers.normalizer import DataNormalizer

logger = logging.getLogger("nirvana.pipeline.data_gov")

class DataGovDataSource(BaseDataSource):
    """
    Connector for National Open Government Data Platform (data.gov.in).
    Queries open datasets adhering to NDSAP policy.
    Requires registered API Key for real-time live queries.
    """

    def __init__(self, api_key: Optional[str] = None, resource_id: Optional[str] = None):
        super().__init__(
            source_name="Open Government Data Platform India (data.gov.in)",
            source_type="GOVERNMENT_PORTAL",
            source_url="https://data.gov.in/api/1/action/datastore_search",
            license_info="National Data Sharing and Accessibility Policy (NDSAP)"
        )
        self.api_key = api_key or os.getenv("DATA_GOV_API_KEY")
        self.resource_id = resource_id
        self.verification_status = "AUTHORIZED" if self.api_key else "REQUIRES_AUTHORIZATION"
        self.access_method = "REST_API"

    def fetch(self) -> pd.DataFrame:
        if not self.api_key:
            logger.info("data.gov.in API key not supplied in environment. Status: REQUIRES_AUTHORIZATION.")
            return pd.DataFrame()

        params = {
            "api-key": self.api_key,
            "format": "json",
            "resource_id": self.resource_id,
            "limit": 500
        }
        resp = requests.get(self.source_url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            records = data.get("records", [])
            self.raw_data = pd.DataFrame(records)
            self.compute_sha256(resp.content)
            return self.raw_data
        else:
            raise RuntimeError(f"Failed to query data.gov.in: HTTP {resp.status_code} - {resp.text}")

    def validate(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        self.quality_issues, _ = DataQualityEngine.validate_dataset(df)
        return self.quality_issues

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        self.normalized_data = DataNormalizer.normalize_dataframe(df)
        return self.normalized_data

    def load(self, db_session) -> int:
        return 0
