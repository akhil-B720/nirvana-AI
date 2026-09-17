# -*- coding: utf-8 -*-
import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

def test_get_state_dossier_structure():
    response = client.get("/api/v1/macro/states/Uttar%20Pradesh")
    assert response.status_code == 200
    data = response.json()

    expected_keys = [
        "state",
        "state_overview",
        "financials",
        "money_flow",
        "financial_ratios",
        "feature_baseline_comparisons",
        "risk_breakdown",
        "anomaly_explanation",
        "yearly_performance",
        "sector_distribution",
        "verification_recommendations",
        "source_provenance",
        "data_limitations",
        "metrics",
        "time_series",
        "advisory"
    ]
    for key in expected_keys:
        assert key in data, f"Missing expected key: {key}"

    assert data["state"] == "Uttar Pradesh"
    assert data["state_overview"]["state"] == "Uttar Pradesh"
    assert "analytical_risk_indicator" in data["state_overview"]
    assert "risk_tier" in data["state_overview"]
    assert "model_confidence" in data["state_overview"]


def test_state_dossier_financial_intelligence():
    response = client.get("/api/v1/macro/states/Uttar%20Pradesh")
    assert response.status_code == 200
    data = response.json()
    fin = data["financials"]

    # Observed disclosures match official records
    assert fin["total_expenditure_crore"] == pytest.approx(2145.06, abs=0.1)
    assert fin["unspent_balance_crore"] == pytest.approx(665.58, abs=0.1)
    assert fin["total_works_completed"] == 60467

    # Derived analytical metrics match exact formulas
    expected_avg_exp = fin["total_expenditure_crore"] / 4.0
    assert fin["avg_annual_expenditure_crore"] == pytest.approx(expected_avg_exp, abs=0.01)

    expected_cost_per_work = (fin["total_expenditure_crore"] * 100.0) / fin["total_works_completed"]
    assert fin["cost_per_completed_work_lakhs"] == pytest.approx(expected_cost_per_work, abs=0.01)

    expected_backlog = fin["unspent_balance_crore"] / expected_avg_exp
    assert fin["backlog_absorption_years"] == pytest.approx(expected_backlog, abs=0.02)

    # Honest reporting: released amount is NOT AVAILABLE in MoSPI yearly dataset
    assert fin["released_amount"] is None
    assert fin["released_amount_label"] == "NOT AVAILABLE"


def test_state_dossier_money_flow_and_ratios():
    response = client.get("/api/v1/macro/states/Uttar%20Pradesh")
    assert response.status_code == 200
    data = response.json()

    # Money flow
    flow = data["money_flow"]
    assert flow["released_funds"] is None
    assert flow["released_funds_status"] == "NOT AVAILABLE"
    assert "MoSPI" in flow["released_funds_note"]
    assert flow["expenditure_crore"] == pytest.approx(2145.06, abs=0.1)
    assert flow["completed_works"] == 60467
    assert flow["unspent_balance_crore"] == pytest.approx(665.58, abs=0.1)

    # Ratios
    ratios = data["financial_ratios"]
    assert ratios["expenditure_utilization"]["status"] == "NOT AVAILABLE"
    assert ratios["expenditure_utilization"]["value"] is None
    assert "Released funds not reported" in ratios["expenditure_utilization"]["reason"]

    assert ratios["unspent_ratio"]["status"] == "NOT AVAILABLE"
    assert ratios["unspent_ratio"]["value"] is None

    assert ratios["avg_expenditure_per_year_crore"]["status"] == "COMPUTED"
    assert ratios["avg_cost_per_completed_work_lakhs"]["status"] == "COMPUTED"
    assert ratios["backlog_absorption_years"]["status"] == "COMPUTED"


def test_state_dossier_baseline_comparisons():
    response = client.get("/api/v1/macro/states/Uttar%20Pradesh")
    assert response.status_code == 200
    data = response.json()

    baselines = data["feature_baseline_comparisons"]
    assert len(baselines) == 10

    for item in baselines:
        assert "feature_key" in item
        assert "feature_name" in item
        assert "category" in item
        assert "actual_value" in item
        assert "model_baseline" in item
        assert "baseline_type" in item
        assert "deviation" in item
        assert "deviation_pct" in item
        assert item["contribution"] in ["HIGH", "MEDIUM", "LOW"]


def test_state_dossier_anomaly_explanations():
    response = client.get("/api/v1/macro/states/Uttar%20Pradesh")
    assert response.status_code == 200
    data = response.json()

    expl = data["anomaly_explanation"]
    assert "why_flagged" in expl
    assert len(expl["why_flagged"]) > 0
    assert isinstance(expl["why_flagged"], list)
    assert "analytical_summary" in expl
    assert len(expl["analytical_summary"]) > 0

    # Advisory notice present
    assert "DECISION-SUPPORT NOTICE" in data["advisory"].upper() or "DECISION-SUPPORT" in data["advisory"].upper()


def test_state_dossier_provenance_and_limitations():
    response = client.get("/api/v1/macro/states/Uttar%20Pradesh")
    assert response.status_code == 200
    data = response.json()

    prov = data["source_provenance"]
    assert "Ministry of Statistics and Programme Implementation" in prov["source_name"]
    assert len(prov["original_files"]) == 3
    assert prov["record_provenance"] == "PUBLIC_VERIFIED"

    limits = data["data_limitations"]
    assert "observed_data" in limits
    assert "model_derived_analysis" in limits


def test_nonexistent_state_returns_404():
    response = client.get("/api/v1/macro/states/NonExistentState999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
