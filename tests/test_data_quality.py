import pytest
import pandas as pd
from data_pipeline.validators.quality_engine import DataQualityEngine
from data_pipeline.normalizers.normalizer import DataNormalizer

def test_negative_financial_validation():
    df = pd.DataFrame([{
        "project_id": "TEST-001",
        "sanction_amount": -50000.0,
        "released_amount": 10000.0,
        "expenditure_amount": -2000.0
    }])
    issues, score = DataQualityEngine.validate_dataset(df)
    issue_types = [i["issue_type"] for i in issues]
    assert "NEGATIVE_FINANCIAL_VALUE" in issue_types
    assert score < 100.0

def test_invalid_coordinates_validation():
    df = pd.DataFrame([{
        "project_id": "TEST-002",
        "latitude": 105.0,  # Invalid (>90)
        "longitude": -200.0  # Invalid (<-180)
    }])
    issues, score = DataQualityEngine.validate_dataset(df)
    issue_types = [i["issue_type"] for i in issues]
    assert "INVALID_COORDINATES" in issue_types

def test_progress_bounds_validation():
    df = pd.DataFrame([{
        "project_id": "TEST-003",
        "reported_progress": 145.0  # >100
    }])
    issues, score = DataQualityEngine.validate_dataset(df)
    issue_types = [i["issue_type"] for i in issues]
    assert "PROGRESS_OUT_OF_BOUNDS" in issue_types

def test_duplicate_project_id_validation():
    df = pd.DataFrame([
        {"project_id": "DUP-001", "sanction_amount": 1000},
        {"project_id": "DUP-001", "sanction_amount": 2000}
    ])
    issues, score = DataQualityEngine.validate_dataset(df)
    issue_types = [i["issue_type"] for i in issues]
    assert "DUPLICATE_ID" in issue_types

def test_completion_precedes_start_date():
    df = pd.DataFrame([{
        "project_id": "TEST-005",
        "start_date": "2024-06-01",
        "actual_completion_date": "2024-01-15"
    }])
    issues, score = DataQualityEngine.validate_dataset(df)
    issue_types = [i["issue_type"] for i in issues]
    assert "COMPLETION_BEFORE_START" in issue_types

def test_normalizer_project_type():
    assert DataNormalizer.normalize_project_type("Primary School", "Govt Higher Sec School") == "BUILDING"
    assert DataNormalizer.normalize_project_type("Concrete Road", "Link Road CC") == "ROAD"
    assert DataNormalizer.normalize_project_type("Water Supply", "Overhead reservoir tank") == "WATER_TANK"
    assert DataNormalizer.normalize_project_type("Culvert bridge", "Minor Bridge") == "BRIDGE"
