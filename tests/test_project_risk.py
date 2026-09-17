import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.database import SessionLocal
from backend.models.models import Project, RiskScore
from ml.models.project_risk_model import ProjectRiskModel


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def sample_project_id():
    db = SessionLocal()
    try:
        p = db.query(Project).filter(Project.project_id.like("GOV-%")).first()
        if not p:
            p = db.query(Project).first()
        assert p is not None, "At least one project must exist in the database for testing."
        return p.project_id
    finally:
        db.close()


def test_feature_extraction_and_completeness():
    """Verify feature extractor handles project objects and missing values gracefully."""
    model = ProjectRiskModel()

    class MockProject:
        project_id = "TEST-001"
        project_name = "Rural Pipeline Construction"
        project_type = "WATER_TANK"
        sector = "Community Development"
        state = "Rajasthan"
        district = "Dholpur"
        constituency = None
        block = "Rajakhera"
        village = "Nadauli"
        sanction_amount = 500000.0
        released_amount = 250000.0
        expenditure_amount = 100000.0
        reported_progress = 40.0
        observed_progress = None
        status = "IN_PROGRESS"
        start_date = "2023-01-15"
        actual_completion_date = None

    p = MockProject()
    feat = model.extract_single_feature_vector(p)
    assert isinstance(feat, dict)
    for expected_key in model.FEATURE_NAMES:
        assert expected_key in feat, f"Missing feature key: {expected_key}"
        assert isinstance(feat[expected_key], (int, float))

    completeness, missing = model.compute_data_completeness(p)
    assert 0.0 <= completeness <= 1.0
    assert "constituency" in missing


def test_project_risk_model_prediction_bounds():
    """Verify risk predictions are bounded and correctly categorized."""
    model = ProjectRiskModel()

    class MockProject:
        project_id = "TEST-002"
        project_name = "Community Hall Construction"
        project_type = "BUILDING"
        sector = "Community Development"
        state = "Bihar"
        district = "Darbhanga"
        constituency = "Darbhanga"
        block = "Manigachhi"
        village = "Raghopur"
        sanction_amount = 10000000.0  # High budget
        released_amount = 10000000.0
        expenditure_amount = 1000000.0
        reported_progress = 10.0
        observed_progress = None
        status = "SANCTIONED"
        start_date = "2021-01-01"  # Sanctioned >3 years ago
        actual_completion_date = None

    pred = model.predict_project(MockProject())
    assert 0.0 <= pred["risk_score"] <= 100.0
    assert pred["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert 0.0 <= pred["confidence"] <= 1.0
    assert isinstance(pred["contributing_factors"], list)
    assert len(pred["contributing_factors"]) > 0  # Should detect stall / cost divergence
    assert pred["disclaimer"] != ""


def test_api_project_risk_endpoint(client, sample_project_id):
    """Test GET /api/v1/projects/{id}/risk schema compliance."""
    res = client.get(f"/api/v1/projects/{sample_project_id}/risk")
    assert res.status_code == 200
    data = res.json()

    assert data["project_id"] == sample_project_id
    assert "risk_score" in data
    assert 0.0 <= data["risk_score"] <= 100.0
    assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert 0.0 <= data["confidence"] <= 1.0
    assert isinstance(data["contributing_factors"], list)
    assert isinstance(data["feature_values"], dict)
    assert "model_version" in data
    assert "data_source" in data
    assert "timestamp" in data
    assert "disclaimer" in data


def test_api_project_anomalies_endpoint(client, sample_project_id):
    """Test GET /api/v1/projects/{id}/anomalies endpoint."""
    res = client.get(f"/api/v1/projects/{sample_project_id}/anomalies")
    assert res.status_code == 200
    data = res.json()

    assert data["project_id"] == sample_project_id
    assert "active_anomaly_count" in data
    assert isinstance(data["anomalies"], list)
    assert "timestamp" in data


def test_api_project_explanation_endpoint(client, sample_project_id):
    """Test GET /api/v1/projects/{id}/explanation endpoint."""
    res = client.get(f"/api/v1/projects/{sample_project_id}/explanation")
    assert res.status_code == 200
    data = res.json()

    assert data["project_id"] == sample_project_id
    assert "risk_score" in data
    assert "risk_level" in data
    assert "confidence" in data
    assert "analytical_summary" in data
    assert "benchmark_comparisons" in data
    assert "sector" in data["benchmark_comparisons"]
    assert "state" in data["benchmark_comparisons"]
    assert "decision_support_guidance" in data


def test_api_project_features_endpoint(client, sample_project_id):
    """Test GET /api/v1/projects/{id}/features endpoint."""
    res = client.get(f"/api/v1/projects/{sample_project_id}/features")
    assert res.status_code == 200
    data = res.json()

    assert data["project_id"] == sample_project_id
    assert "feature_names" in data
    assert "raw_features" in data
    assert "normalized_features" in data
    assert len(data["feature_names"]) == 8


def test_api_project_data_quality_endpoint(client, sample_project_id):
    """Test GET /api/v1/projects/{id}/data-quality endpoint."""
    res = client.get(f"/api/v1/projects/{sample_project_id}/data-quality")
    assert res.status_code == 200
    data = res.json()

    assert data["project_id"] == sample_project_id
    assert "provenance" in data
    assert "source_name" in data["provenance"]
    assert "verification_status" in data["provenance"]
    assert 0.0 <= data["data_completeness_ratio"] <= 1.0
    assert isinstance(data["missing_fields"], list)
    assert "quality_issues" in data


def test_api_project_endpoints_404(client):
    """Test all 5 endpoints return 404 for nonexistent projects."""
    nonexistent = "GOV-NONEXISTENT-999999"
    endpoints = ["risk", "anomalies", "explanation", "features", "data-quality"]
    for ep in endpoints:
        res = client.get(f"/api/v1/projects/{nonexistent}/{ep}")
        assert res.status_code == 404, f"Endpoint {ep} did not return 404 for missing project"
