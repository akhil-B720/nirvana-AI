import pytest
import pandas as pd
from ml.models.cost_anomaly import CostAnomalyModel
from ml.models.delay_model import DelayRiskModel
from ml.models.similarity_model import SimilarityEngine
from datetime import date, timedelta

class DummyProject:
    def __init__(self, p_id, name, p_type, sector, district, lat, lon, sanction, released, expenditure, rep_prog, start_d=None, exp_d=None):
        self.project_id = p_id
        self.project_name = name
        self.project_type = p_type
        self.sector = sector
        self.district = district
        self.block = "BlockA"
        self.village = "VillageA"
        self.latitude = lat
        self.longitude = lon
        self.sanction_amount = sanction
        self.released_amount = released
        self.expenditure_amount = expenditure
        self.reported_progress = rep_prog
        self.observed_progress = None
        self.start_date = start_d
        self.expected_completion_date = exp_d
        self.actual_completion_date = None

def test_cost_anomaly_model_fit_and_predict():
    data = [
        {"project_id": "P1", "sanction_amount": 1000000, "released_amount": 1000000, "expenditure_amount": 900000, "reported_progress": 80},
        {"project_id": "P2", "sanction_amount": 1200000, "released_amount": 1200000, "expenditure_amount": 1100000, "reported_progress": 85},
        {"project_id": "P3", "sanction_amount": 1100000, "released_amount": 1100000, "expenditure_amount": 1000000, "reported_progress": 80},
        {"project_id": "P4", "sanction_amount": 10000000, "released_amount": 5000000, "expenditure_amount": 4900000, "reported_progress": 10} # Outlier
    ]
    df = pd.DataFrame(data)
    model = CostAnomalyModel(contamination=0.25)
    metrics = model.fit(df)
    assert metrics["status"] == "ACTIVE"
    preds = model.predict(df)
    assert len(preds) == 4
    # The outlier should have higher anomaly score
    assert preds[3]["anomaly_score"] > preds[0]["anomaly_score"]

def test_delay_model_slippage_calculation():
    today = date.today()
    p_delayed = DummyProject(
        "P-DEL", "Rural Road", "ROAD", "Transport", "Jaipur", 26.9, 75.8,
        3000000, 3000000, 2900000, 20.0,
        today - timedelta(days=400), today - timedelta(days=100) # 100 days overdue, only 20% progress
    )
    delay_model = DelayRiskModel()
    res = delay_model.predict_project(p_delayed)
    assert res["delay_probability"] > 0.70
    assert res["predicted_delay_days"] > 100

def test_similarity_engine_duplicate_detection():
    p1 = DummyProject("P1", "Construction of Community Health Sub-Centre at Rampur", "BUILDING", "Health", "Pune", 18.52, 73.85, 2000000, 2000000, 1000000, 50)
    p2 = DummyProject("P2", "Construction of Community Health Centre Building at Rampur", "BUILDING", "Health", "Pune", 18.521, 73.851, 2100000, 2100000, 1100000, 48) # Near duplicate
    p3 = DummyProject("P3", "High Level Bridge on River Kaveri", "BRIDGE", "Transport", "Mysuru", 12.11, 76.68, 8000000, 4000000, 3000000, 30)

    sim = SimilarityEngine()
    sim.fit([p1, p2, p3])
    matches = sim.find_similar(p1)
    assert len(matches) > 0
    top_match = matches[0]
    assert top_match["compared_project_id"] == "P2"
    assert top_match["combined_similarity"] > 0.75
    assert top_match["status_label"] == "potentially_similar"
