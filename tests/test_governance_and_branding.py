import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.database import SessionLocal
from backend.models.models import Project, ProjectEvidence, VerificationCase, AuditLog

client = TestClient(app)

def test_branding_assets_exist():
    """Verify all official NIRVANA branding assets exist in static assets directory."""
    brand_dir = Path("backend/static/assets/branding")
    assert brand_dir.exists(), "Branding directory must exist"
    
    expected_assets = [
        "nirvana-logo-primary.png",
        "nirvana-icon.png",
        "nirvana-banner.png",
        "nirvana-bg-watermark.png",
        "nirvana-favicon.png"
    ]
    for asset in expected_assets:
        file_path = brand_dir / asset
        assert file_path.exists(), f"Asset {asset} must exist"
        assert file_path.stat().st_size > 500, f"Asset {asset} must not be empty"

def test_data_mode_isolation():
    """Verify strictly separated counts between Real MoSPI data and Synthetic Benchmark data."""
    res_real = client.get("/api/v1/analytics/overview?data_status=PUBLIC_VERIFIED")
    assert res_real.status_code == 200
    data_real = res_real.json()
    assert data_real["total_projects"] == 3390
    assert data_real["data_status"] == "PUBLIC_VERIFIED"

    res_synth = client.get("/api/v1/analytics/overview?data_status=SYNTHETIC")
    assert res_synth.status_code == 200
    data_synth = res_synth.json()
    assert data_synth["total_projects"] == 5000
    assert data_synth["data_status"] == "SYNTHETIC"

def test_evidence_endpoint_and_synthetic_labeling():
    """Verify synthetic evidence includes the mandatory AI-generated disclaimer banner."""
    res = client.get("/api/v1/evidence?data_status=SYNTHETIC&limit=10")
    assert res.status_code == 200
    items = res.json()
    assert len(items) > 0

    for item in items:
        assert item["is_synthetic"] is True
        assert "AI-GENERATED / SYNTHETIC" in item["label"]
        assert item["sha256"] is not None
        assert len(item["sha256"]) == 64  # SHA-256 hex digest length
        assert item["image_url"].startswith("/assets/synthetic/evidence/")

def test_synthetic_stage_illustrations_exist_on_disk():
    """Verify all 21 stage illustrations across 4 sectors exist on disk and are valid PNGs."""
    evidence_dir = Path("backend/static/assets/synthetic/evidence")
    assert evidence_dir.exists()

    sectors = {
        "buildings": ["foundation.png", "columns.png", "beams.png", "walls.png", "roof.png", "finishing.png"],
        "roads": ["earthwork.png", "subbase.png", "base.png", "asphalt.png", "markings.png"],
        "bridges": ["foundation.png", "pillars.png", "deck.png", "railings.png", "finishing.png"],
        "water_tanks": ["foundation.png", "supports.png", "tank_body.png", "pipelines.png", "finishing.png"]
    }

    for sec, stages in sectors.items():
        sec_dir = evidence_dir / sec
        assert sec_dir.exists(), f"Sector directory {sec} must exist"
        for stg in stages:
            img_file = sec_dir / stg
            assert img_file.exists(), f"Stage image {stg} for {sec} must exist"
            assert img_file.stat().st_size > 1000, f"Stage image {stg} must be non-empty"

def test_verification_cases_workflow():
    """Verify listing verification cases with data_status filter and updating status."""
    res = client.get("/api/v1/verification-cases?data_status=SYNTHETIC")
    assert res.status_code == 200
    cases = res.json()
    assert len(cases) > 0

    target_case = cases[0]
    case_id = target_case["case_id"]

    # Login to get officer token
    login_res = client.post("/api/v1/auth/login", json={"username": "admin", "password": "NirvanaAdmin2026!"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Update case status
    patch_res = client.patch(
        f"/api/v1/verification-cases/{case_id}",
        json={"case_status": "UNDER_INVESTIGATION", "officer_findings": "Field verification initiated by demo officer."},
        headers=headers
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "UNDER_INVESTIGATION"

def test_audit_logs_endpoint():
    """Verify tamper-evident audit logs endpoint returns valid entries."""
    res = client.get("/api/v1/audit-logs?limit=10")
    assert res.status_code == 200
    logs = res.json()
    assert len(logs) > 0
    first = logs[0]
    assert "timestamp" in first
    assert "action" in first
    assert "actor" in first
    assert "project_id" in first

def test_models_registry_endpoint():
    """Verify models registry returns registered models with metrics and versions."""
    res = client.get("/api/v1/models")
    assert res.status_code == 200
    models = res.json()
    assert len(models) >= 4
    model_ids = [m["model_id"] for m in models]
    assert "cost_anomaly_v1" in model_ids
    assert "similarity_engine_v1" in model_ids
