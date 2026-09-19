import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from ml.models.delay_model import DelayRiskModel
from backend.core.config import settings

client = TestClient(app)

def test_synthetic_data_isolation():
    """
    Strict isolation test:
    - Default project listing MUST return only PUBLIC_VERIFIED government data.
    - Synthetic test records must never contaminate default listings.
    - Explicit query ?data_status=SYNTHETIC must return synthetic records.
    """
    # 1. Default listing
    resp_default = client.get("/api/v1/projects?limit=50")
    assert resp_default.status_code == 200
    default_projects = resp_default.json()
    assert len(default_projects) > 0

    for p in default_projects:
        assert p.get("data_status") == "PUBLIC_VERIFIED", f"Contamination: project {p['project_id']} has data_status={p.get('data_status')}"
        assert p.get("source_type") != "SYNTHETIC_TEST_DATA"

    # 2. Explicit verified listing
    resp_verified = client.get("/api/v1/projects?data_status=PUBLIC_VERIFIED&limit=20")
    assert resp_verified.status_code == 200
    for p in resp_verified.json():
        assert p.get("data_status") == "PUBLIC_VERIFIED"

    # 3. Explicit synthetic listing
    resp_synthetic = client.get("/api/v1/projects?data_status=SYNTHETIC&limit=20")
    assert resp_synthetic.status_code == 200
    synthetic_projects = resp_synthetic.json()
    assert len(synthetic_projects) > 0

    for p in synthetic_projects:
        assert p.get("data_status") == "SYNTHETIC"
        assert p.get("source_type") == "SYNTHETIC_TEST_DATA"
        assert "anomaly_label" in p

def test_project_components_endpoint():
    """Test GET /api/v1/projects/{id}/components returns physical component breakdown."""
    resp = client.get("/api/v1/projects?data_status=SYNTHETIC&limit=1")
    assert resp.status_code == 200
    p_id = resp.json()[0]["project_id"]

    comp_resp = client.get(f"/api/v1/projects/{p_id}/components")
    assert comp_resp.status_code == 200
    comps = comp_resp.json()
    assert isinstance(comps, list)
    assert len(comps) > 0

    for c in comps:
        assert c["project_id"] == p_id
        assert "component_name" in c
        assert "weight_pct" in c
        assert "completion_pct" in c
        assert "detected_status" in c
        assert c["data_status"] == "SYNTHETIC"

def test_project_progress_history_endpoint():
    """Test GET /api/v1/projects/{id}/progress-history returns chronological snapshots."""
    resp = client.get("/api/v1/projects?data_status=SYNTHETIC&limit=1")
    assert resp.status_code == 200
    p_id = resp.json()[0]["project_id"]

    hist_resp = client.get(f"/api/v1/projects/{p_id}/progress-history")
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert isinstance(history, list)
    assert len(history) > 0

    prev_date = None
    for h in history:
        assert h["project_id"] == p_id
        assert "record_date" in h
        assert "reported_progress" in h
        assert "financial_expenditure" in h
        assert h["data_status"] == "SYNTHETIC"
        if prev_date:
            assert h["record_date"] >= prev_date
        prev_date = h["record_date"]

def test_progress_estimator_component_breakdown():
    """Test ProgressEstimator evaluates component states and tags data status."""
    resp = client.get("/api/v1/projects?data_status=SYNTHETIC&limit=1")
    p_id = resp.json()[0]["project_id"]

    est_resp = client.get(f"/api/v1/projects/{p_id}/progress-estimate")
    assert est_resp.status_code == 200
    estimate = est_resp.json()

    assert estimate["data_status"] == "SYNTHETIC"
    assert estimate["is_synthetic"] is True
    assert estimate["model_status"] == "COMPONENT_DECOMPOSITION"
    assert isinstance(estimate["components_detail"], list)
    assert len(estimate["components_detail"]) > 0
    assert estimate["observed_progress"] is not None
    assert "DEVELOPMENT ONLY" in estimate["disclaimer"]

def test_supervised_delay_model_inference():
    """Test supervised delay model artifact and inference."""
    model_path = settings.MODEL_DIR / "delay" / "delay_model.joblib"
    assert model_path.exists(), f"Model artifact not found at {model_path}"

    model = DelayRiskModel.load(str(model_path))
    assert model.is_supervised is True
    assert model.regressor is not None
    assert model.classifier is not None

    # Test prediction on synthetic project
    resp = client.get("/api/v1/projects?data_status=SYNTHETIC&limit=5")
    projects = resp.json()
    for p_dict in projects:
        # Create an object with attributes for predict_project
        class DummyProj:
            def __init__(self, d):
                for k, v in d.items():
                    setattr(self, k, v)
        dummy = DummyProj(p_dict)
        pred = model.predict_project(dummy)
        assert "predicted_delay_days" in pred
        assert "delay_probability" in pred
        assert "confidence" in pred
        assert pred["is_synthetic"] is True

def test_synthetic_pdf_report_generation():
    """Test generating dossier for synthetic project succeeds with watermark."""
    resp = client.get("/api/v1/projects?data_status=SYNTHETIC&limit=1")
    p_id = resp.json()[0]["project_id"]

    pdf_resp = client.get(f"/api/v1/projects/{p_id}/report")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 1000

def test_synthetic_anomaly_evaluation_report_integrity():
    """Verify the synthetic benchmark evaluation JSON report exists and is valid."""
    report_file = Path("ml/reports/synthetic_anomaly_evaluation.json")
    assert report_file.exists(), "Benchmark report file does not exist"

    with open(report_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["evaluation_type"] == "SYNTHETIC_TEST_DATA"
    assert data["sample_size"] == 5000
    assert "overall_metrics" in data
    assert data["overall_metrics"]["roc_auc"] >= 0.85
    assert "category_detection_rates" in data
    assert "disclaimer" in data

def test_delay_risk_endpoint():
    """Verify GET /api/v1/projects/{project_id}/delay-risk works for synthetic and public projects."""
    resp = client.get("/api/v1/projects?data_status=SYNTHETIC&limit=1")
    p_id = resp.json()[0]["project_id"]

    d_resp = client.get(f"/api/v1/projects/{p_id}/delay-risk")
    assert d_resp.status_code == 200
    data = d_resp.json()
    assert data["project_id"] == p_id
    assert "predicted_delay_days" in data
    assert "delay_probability" in data
    assert data["data_status"] == "SYNTHETIC"
    assert data["is_synthetic"] is True

def test_digital_twin_with_granular_components():
    """Verify digital twin returns granular components for synthetic projects."""
    resp = client.get("/api/v1/projects?data_status=SYNTHETIC&limit=1")
    p_id = resp.json()[0]["project_id"]

    tw_resp = client.get(f"/api/v1/projects/{p_id}/digital-twin")
    assert tw_resp.status_code == 200
    data = tw_resp.json()
    assert data["project_id"] == p_id
    assert data["data_status"] == "SYNTHETIC"
    assert "granular_components" in data
    assert len(data["granular_components"]) > 0
    assert "completion_percentage" in data["granular_components"][0]

