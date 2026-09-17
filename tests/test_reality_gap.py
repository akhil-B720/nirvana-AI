import pytest
from datetime import date, timedelta
from backend.services.reality_gap import RealityGapEngine

class MockProject:
    def __init__(self, project_id, p_type, sanction, released, expenditure, start_d, exp_d, rep_prog, obs_prog=None):
        self.project_id = project_id
        self.project_name = f"Mock {project_id}"
        self.project_type = p_type
        self.sanction_amount = sanction
        self.released_amount = released
        self.expenditure_amount = expenditure
        self.start_date = start_d
        self.expected_completion_date = exp_d
        self.actual_completion_date = None
        self.reported_progress = rep_prog
        self.observed_progress = obs_prog
        self.observed_progress_status = "AI_ESTIMATE" if obs_prog is not None else "NOT_AVAILABLE"

def test_reality_gap_with_missing_observed_progress():
    today = date.today()
    p = MockProject(
        project_id="TEST-GAP-01",
        p_type="BUILDING",
        sanction=1000000,
        released=1000000,
        expenditure=500000,
        start_d=today - timedelta(days=100),
        exp_d=today + timedelta(days=100),
        rep_prog=50.0,
        obs_prog=None  # Explicitly missing observed progress
    )
    res = RealityGapEngine.evaluate(p)
    assert res["observed_progress"] is None
    assert res["observed_progress_status"] == "NOT_AVAILABLE"
    assert "Observed physical ground evidence unavailable. Status: NOT_AVAILABLE" in res["contributing_factors"]
    # Reality gap score should NOT blow up to 100 just because photo is missing
    assert res["reality_gap_score"] <= 50.0

def test_critical_reality_gap_detected():
    today = date.today()
    p = MockProject(
        project_id="TEST-GAP-02",
        p_type="ROAD",
        sanction=2000000,
        released=2000000,
        expenditure=1900000,
        start_d=today - timedelta(days=200),
        exp_d=today - timedelta(days=10),
        rep_prog=95.0,  # Claimed 95%
        obs_prog=15.0   # Observed only 15%
    )
    res = RealityGapEngine.evaluate(p)
    assert res["observed_progress"] == 15.0
    assert res["reality_gap_score"] > 50.0
    assert any("Reality Gap: Reported progress" in f for f in res["contributing_factors"])
