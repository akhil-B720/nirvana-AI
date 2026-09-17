import pytest
from unittest.mock import patch, MagicMock
from data_pipeline.sources.empowered_indian import EmpoweredIndianDataSource

def test_empowered_indian_provenance_and_normalization():
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"success":true,"data":{"completedWorks":[{"_id":"mock_id_001","work_id":99901,"work_description":"Construction of CC Road","category":"Road","state":"Rajasthan","district":"JAIPUR","location":"JAIPUR_IDA","cost":750000.0,"completion_date":"2025-02-15T00:00:00.000Z","completion_year":2025,"beneficiaries":1200,"mp_details":{"name":"Test MP","constituency":"JAIPUR","party":"Lok Sabha"}}]}}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        importer = EmpoweredIndianDataSource(sample_size=1)
        df_raw = importer.fetch()

        assert len(df_raw) == 1
        assert importer.verification_status == 'UNVERIFIED_THIRD_PARTY'
        assert importer.source_type == 'THIRD_PARTY_CIVIC_AGGREGATOR'
        assert importer.file_hash is not None

        # Validate
        issues = importer.validate(df_raw)
        assert importer.quality_score == 100.0

        # Normalize
        df_norm = importer.normalize(df_raw)
        row = df_norm.iloc[0]
        assert row['project_id'] == 'EI-WORK-99901'
        assert row['project_type'] == 'ROAD'
        assert row['status'] == 'COMPLETED'
        assert row['reported_progress'] == 100.0
        assert row['observed_progress'] is None  # Never fabricates observation
        assert row['data_availability_status'] == 'UNVERIFIED_THIRD_PARTY'
