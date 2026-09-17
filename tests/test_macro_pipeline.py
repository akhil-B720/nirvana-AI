import pytest
from fastapi.testclient import TestClient
import pandas as pd
import numpy as np

from backend.main import app
from backend.core.database import SessionLocal
from backend.models.macro_models import StateMacroMetrics, DataQualityAuditLog
from data_pipeline.processors.macro_pipeline import MacroDataPipeline
from ml.models.macro_risk_analyzer import MacroRiskAnalyzer

client = TestClient(app)

def test_macro_data_pipeline_execution():
    pipeline = MacroDataPipeline()
    df_yearly, df_sectors, df_unspent, df_master = pipeline.run()

    # 37 State/UT/Nominated entities across 4 years = 148 yearly records
    assert len(df_yearly) == 148
    assert len(df_sectors) == 36
    assert len(df_unspent) == 37
    assert len(df_master) == 37

    # Validate essential calculated columns
    assert "total_expenditure_4yr_crore" in df_master.columns
    assert "backlog_absorption_years" in df_master.columns
    assert "expenditure_volatility_cv" in df_master.columns

    # Non-negative amounts
    assert (df_master["total_expenditure_4yr_crore"] >= 0).all()
    assert (df_master["total_works_completed_4yr"] >= 0).all()

def test_macro_data_quality_audit_logging():
    pipeline = MacroDataPipeline()
    pipeline.run()

    # Verify audit logs captured header disambiguation and state canonicalization
    rules = [a["transformation_rule"] for a in pipeline.audit_logs]
    assert "DISAMBIGUATE_DUPLICATE_YEAR_HEADER" in rules
    assert "CANONICALIZE_STATE_NAME" in rules
    assert len(pipeline.audit_logs) >= 10

def test_macro_ml_analyzer_fit_predict():
    pipeline = MacroDataPipeline()
    _, _, _, df_master = pipeline.run()

    analyzer = MacroRiskAnalyzer(n_clusters=4, contamination=0.15, random_state=42)
    analyzer.fit(df_master)

    assert analyzer.is_fitted
    assert analyzer.metrics["silhouette_score"] > 0
    assert len(analyzer.metrics["pca_explained_variance"]) == 2

    # Predict
    res_df = analyzer.predict(df_master)
    assert "is_anomaly" in res_df.columns
    assert "anomaly_score" in res_df.columns
    assert "risk_tier" in res_df.columns
    assert (res_df["anomaly_score"] >= 0.0).all()
    assert (res_df["anomaly_score"] <= 100.0).all()

    # Model save & load verification
    saved_path = analyzer.save("models/macro_risk")
    loaded_analyzer = MacroRiskAnalyzer.load(saved_path)
    res_loaded = loaded_analyzer.predict(df_master)
    np.testing.assert_allclose(res_df["anomaly_score"].values, res_loaded["anomaly_score"].values)

def test_macro_api_states_endpoint():
    resp = client.get("/api/v1/macro/states")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 37
    assert len(data["items"]) == 37
    assert "advisory" in data

def test_macro_api_state_detail_endpoint():
    resp = client.get("/api/v1/macro/states/Uttar Pradesh")
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "Uttar Pradesh"
    assert len(data["time_series"]) == 4
    assert data["metrics"]["unspent_balance_crore"] == 665.58

def test_macro_api_risk_analysis_endpoint():
    resp = client.get("/api/v1/macro/risk-analysis")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_states"] == 37
    assert data["national_unspent_balance_crore"] > 4000.0
    assert "risk_tier_distribution" in data
    assert len(data["top_bottlenecks"]) > 0

def test_macro_api_audit_logs_endpoint():
    resp = client.get("/api/v1/macro/audit-logs?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 5
    assert len(data["logs"]) == 5
