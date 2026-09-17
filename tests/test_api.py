import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check_endpoint():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "HEALTHY"
    assert "advisory" in data

def test_projects_list_endpoint():
    resp = client.get("/api/v1/projects")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_project_detail_endpoint():
    resp = client.get("/api/v1/projects/SYN-MP-001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_id"] == "SYN-MP-001"
    assert "financials" in data
    assert "events" in data
    assert "reality_gap_summary" in data

def test_project_reality_gap_endpoint():
    resp = client.get("/api/v1/projects/SYN-UP-002/reality-gap")
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_id"] == "SYN-UP-002"
    assert "reality_gap_score" in data
    assert "components" in data
    assert "notice" in data

def test_project_digital_twin_endpoint():
    resp = client.get("/api/v1/projects/SYN-MP-001/digital-twin")
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_type"] == "BUILDING"
    assert "reported_state" in data
    assert "observed_state" in data

def test_pdf_report_download():
    resp = client.get("/api/v1/projects/SYN-MP-001/report")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert len(resp.content) > 1000

def test_ai_assistant_grounded_response():
    resp = client.post("/api/v1/assistant/query", json={
        "query": "Why was this project flagged as high risk?",
        "project_id": "SYN-UP-002"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert len(data["citations"]) > 0
    assert "disclaimer" in data

def test_model_registry_endpoint():
    resp = client.get("/api/v1/models")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    model_ids = [m["model_id"] for m in data]
    assert "cost_anomaly_v1" in model_ids
