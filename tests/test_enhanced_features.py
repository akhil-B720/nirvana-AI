# -*- coding: utf-8 -*-
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.auth import create_access_token

client = TestClient(app)

def get_auth_header():
    token = create_access_token(data={"sub": "admin", "role": "ADMIN"})
    return {"Authorization": f"Bearer {token}"}

def test_states_loading_all_37_entities():
    response = client.get("/api/v1/macro/states")
    assert response.status_code == 200
    data = response.json()

    assert "count" in data
    assert "items" in data
    assert data["count"] == 37
    assert len(data["items"]) == 37

    # Verify key properties on items
    for item in data["items"]:
        assert "state" in item
        assert "total_expenditure_4yr_crore" in item
        assert "unspent_balance_crore" in item
        assert "anomaly_score" in item
        assert "analytical_risk_indicator" in item
        assert "risk_tier" in item

def test_tamil_nadu_and_andhra_pradesh_dossiers():
    for state_name in ["Tamil Nadu", "Andhra Pradesh"]:
        response = client.get(f"/api/v1/macro/states/{state_name}")
        assert response.status_code == 200
        d = response.json()

        assert d["state"] == state_name
        assert "state_overview" in d
        assert "financials" in d
        assert "yearly_performance" in d
        assert len(d["yearly_performance"]) == 4
        assert "sector_distribution" in d
        assert "feature_baseline_comparisons" in d
        assert len(d["feature_baseline_comparisons"]) == 10

        # Validate non-negative financial values
        assert d["financials"]["total_expenditure_crore"] > 0
        assert d["financials"]["unspent_balance_crore"] > 0
        assert d["financials"]["total_works_completed"] > 0

        # Honest data reporting for missing released funds
        assert d["financials"]["released_amount"] is None
        assert d["financials"]["released_amount_label"] == "NOT AVAILABLE"
        assert d["financial_ratios"]["expenditure_utilization"]["status"] == "NOT AVAILABLE"

def test_inspection_request_crud_and_approval_workflow():
    headers = get_auth_header()

    # 1. Fetch a real project
    projects_res = client.get("/api/v1/projects?limit=1")
    assert projects_res.status_code == 200
    project_id = projects_res.json()[0]["project_id"]

    # 2. Create inspection request draft
    payload = {
        "project_id": project_id,
        "inspector_name": "Vigilance Officer Sharma",
        "proposed_date": "2026-10-15",
        "priority": "HIGH",
        "reason_for_inspection": "Analytical anomaly divergence in progress timeline vs capital outlay.",
        "evidence_available": "Official MoSPI Records",
        "evidence_missing": "Certified physical site inspection photos"
    }
    create_res = client.post("/api/v1/inspections", json=payload, headers=headers)
    assert create_res.status_code == 200
    create_data = create_res.json()
    assert create_data["status"] == "CREATED"
    req_id = create_data["request_id"]
    assert req_id.startswith("INSP-")

    # 3. Retrieve inspection detail
    detail_res = client.get(f"/api/v1/inspections/{req_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["request_id"] == req_id
    assert detail["approval_status"] == "DRAFT"
    assert detail["inspector_name"] == "Vigilance Officer Sharma"

    # 4. Superior Officer review and approval
    update_payload = {
        "approval_status": "APPROVED",
        "approving_officer": "Chief Vigilance Commissioner",
        "approval_notes": "Field inspection authorized. Deploy nodal engineer team with GPS equipment."
    }
    patch_res = client.patch(f"/api/v1/inspections/{req_id}/status", json=update_payload, headers=headers)
    assert patch_res.status_code == 200
    patch_data = patch_res.json()
    assert patch_data["approval_status"] == "APPROVED"
    assert patch_data["approving_officer"] == "Chief Vigilance Commissioner"
    assert patch_data["resolved_at"] is not None

    # 5. List inspections and verify presence
    list_res = client.get("/api/v1/inspections?approval_status=APPROVED")
    assert list_res.status_code == 200
    all_inspections = list_res.json()
    found = any(i["request_id"] == req_id for i in all_inspections)
    assert found

def test_inspection_request_pdf_generation():
    headers = get_auth_header()

    # Fetch an existing inspection or create one
    list_res = client.get("/api/v1/inspections?limit=1")
    if len(list_res.json()) == 0:
        projects_res = client.get("/api/v1/projects?limit=1")
        project_id = projects_res.json()[0]["project_id"]
        create_res = client.post("/api/v1/inspections", json={"project_id": project_id, "inspector_name": "Auditor"}, headers=headers)
        req_id = create_res.json()["request_id"]
    else:
        req_id = list_res.json()[0]["request_id"]

    pdf_res = client.get(f"/api/v1/inspections/{req_id}/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 1000

def test_progress_estimator_honest_handling():
    projects_res = client.get("/api/v1/projects?limit=5")
    projects = projects_res.json()

    for p in projects:
        res = client.get(f"/api/v1/projects/{p['project_id']}/progress-estimate")
        assert res.status_code == 200
        data = res.json()

        assert "expected_progress" in data
        assert "reported_progress" in data
        assert "observed_progress" in data
        assert "model_status" in data
        assert "confidence" in data
        assert "detected_components" in data
        assert "missing_components" in data

        # If evidence was absent, observed_progress must be null, never 0%
        if data["evidence_count"] == 0 and p.get("observed_progress") is None:
            assert data["observed_progress"] is None
            assert data["observed_status"] == "NOT_AVAILABLE"
            assert data["model_status"] == "NO_EVIDENCE"

def test_draft_verification_report_endpoint():
    projects_res = client.get("/api/v1/projects?limit=1")
    project_id = projects_res.json()[0]["project_id"]

    res = client.get(f"/api/v1/reports/verification-draft/{project_id}")
    assert res.status_code == 200
    data = res.json()

    assert data["report_type"] == "DRAFT_VERIFICATION_REPORT"
    assert data["project_id"] == project_id
    assert "analytical_risk_score" in data
    assert "risk_tier" in data
    assert "financial_summary" in data
    assert "progress_tripartite" in data
    assert "wording_standard" in data
    assert "Potential Anomaly" in data["wording_standard"]
