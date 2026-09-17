from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.core.database import SessionLocal
from backend.models.macro_models import (
    StateYearlyPerformance,
    StateSectoralAllocation,
    StateUnspentLiquidity,
    StateMacroMetrics,
    DataQualityAuditLog
)

macro_router = APIRouter(prefix="/macro", tags=["Macro MPLADS Analytics"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

ADVISORY_NOTICE = "AI-generated risk indicators are decision-support signals and do not constitute proof of fraud, corruption, or wrongdoing."

@macro_router.get("/states")
def list_macro_states(
    risk_tier: Optional[str] = None,
    sort_by: str = Query("anomaly_score", enum=["anomaly_score", "unspent_balance_crore", "backlog_absorption_years", "total_expenditure_4yr_crore", "state"]),
    order: str = Query("desc", enum=["asc", "desc"]),
    db: Session = Depends(get_db)
):
    """
    List all States and Union Territories with synthesized 4-year MPLADS metrics,
    unspent balances, backlog absorption ratios, and ML anomaly scores.
    """
    query = db.query(StateMacroMetrics)
    if risk_tier:
        query = query.filter(StateMacroMetrics.risk_tier == risk_tier)

    sort_attr = getattr(StateMacroMetrics, sort_by, StateMacroMetrics.anomaly_score)
    if order == "desc":
        query = query.order_by(desc(sort_attr))
    else:
        query = query.order_by(sort_attr)

    items = query.all()
    results = []
    for it in items:
        results.append({
            "state": it.state,
            "total_expenditure_4yr_crore": it.total_expenditure_4yr_crore,
            "total_works_completed_4yr": it.total_works_completed_4yr,
            "avg_annual_expenditure_crore": it.avg_annual_expenditure_crore,
            "avg_annual_works": it.avg_annual_works,
            "cost_per_work_lakhs": it.cost_per_work_lakhs,
            "unspent_balance_crore": it.unspent_balance_crore,
            "backlog_absorption_years": it.backlog_absorption_years,
            "expenditure_volatility_cv": it.expenditure_volatility_cv,
            "infrastructure_dominance_pct": it.infrastructure_dominance_pct,
            "social_infrastructure_pct": it.social_infrastructure_pct,
            "sector_hhi": it.sector_hhi,
            "is_anomaly": it.is_anomaly,
            "anomaly_score": it.anomaly_score,
            "risk_cluster": it.risk_cluster,
            "risk_tier": it.risk_tier
        })

    return {
        "count": len(results),
        "items": results,
        "advisory": ADVISORY_NOTICE
    }

@macro_router.get("/states/{state_name}")
def get_state_macro_detail(state_name: str, db: Session = Depends(get_db)):
    """
    Retrieve comprehensive state profile: 4-year time series, sector percentages,
    unspent balances, and ML anomaly profile.
    """
    metrics = db.query(StateMacroMetrics).filter(StateMacroMetrics.state.ilike(f"%{state_name}%")).first()
    if not metrics:
        raise HTTPException(status_code=404, detail=f"State '{state_name}' not found")

    st = metrics.state
    yearly = db.query(StateYearlyPerformance).filter_by(state=st).order_by(StateYearlyPerformance.financial_year).all()
    sectors = db.query(StateSectoralAllocation).filter_by(state=st).first()
    unspent = db.query(StateUnspentLiquidity).filter_by(state=st).first()

    return {
        "state": st,
        "metrics": {
            "total_expenditure_4yr_crore": metrics.total_expenditure_4yr_crore,
            "total_works_completed_4yr": metrics.total_works_completed_4yr,
            "avg_annual_expenditure_crore": metrics.avg_annual_expenditure_crore,
            "cost_per_work_lakhs": metrics.cost_per_work_lakhs,
            "unspent_balance_crore": metrics.unspent_balance_crore,
            "backlog_absorption_years": metrics.backlog_absorption_years,
            "expenditure_volatility_cv": metrics.expenditure_volatility_cv,
            "is_anomaly": metrics.is_anomaly,
            "anomaly_score": metrics.anomaly_score,
            "risk_cluster": metrics.risk_cluster,
            "risk_tier": metrics.risk_tier
        },
        "time_series": [
            {
                "financial_year": y.financial_year,
                "expenditure_crore": y.expenditure_crore,
                "completed_works": y.completed_works,
                "avg_cost_per_work_lakhs": y.avg_cost_per_work_lakhs
            } for y in yearly
        ],
        "sector_distribution": {
            "railways_roads_bridges_pct": sectors.railways_roads_bridges_pct if sectors else None,
            "education_pct": sectors.education_pct if sectors else None,
            "drinking_water_pct": sectors.drinking_water_pct if sectors else None,
            "sanitation_health_pct": sectors.sanitation_health_pct if sectors else None,
            "other_public_facilities_pct": sectors.other_public_facilities_pct if sectors else None,
            "others_pct": sectors.others_pct if sectors else None
        } if sectors else None,
        "advisory": ADVISORY_NOTICE
    }

@macro_router.get("/risk-analysis")
def get_macro_risk_analysis(db: Session = Depends(get_db)):
    """
    Overview of national MPLADS risk analysis, clustering distribution, and key bottlenecks.
    """
    all_states = db.query(StateMacroMetrics).all()
    if not all_states:
        raise HTTPException(status_code=404, detail="Macro metrics not yet calculated")

    tier_counts = {}
    cluster_counts = {}
    total_unspent = 0.0
    total_exp_4yr = 0.0

    for s in all_states:
        tier_counts[s.risk_tier] = tier_counts.get(s.risk_tier, 0) + 1
        cluster_counts[s.risk_cluster] = cluster_counts.get(s.risk_cluster, 0) + 1
        if s.unspent_balance_crore:
            total_unspent += s.unspent_balance_crore
        if s.total_expenditure_4yr_crore:
            total_exp_4yr += s.total_expenditure_4yr_crore

    top_anomalies = db.query(StateMacroMetrics).order_by(desc(StateMacroMetrics.anomaly_score)).limit(5).all()

    return {
        "total_states": len(all_states),
        "national_unspent_balance_crore": round(total_unspent, 2),
        "national_4yr_expenditure_crore": round(total_exp_4yr, 2),
        "national_backlog_ratio_years": round(total_unspent / (total_exp_4yr / 4.0), 2) if total_exp_4yr > 0 else 0.0,
        "risk_tier_distribution": tier_counts,
        "cluster_distribution": cluster_counts,
        "top_bottlenecks": [
            {
                "state": a.state,
                "anomaly_score": a.anomaly_score,
                "risk_tier": a.risk_tier,
                "backlog_absorption_years": a.backlog_absorption_years,
                "unspent_balance_crore": a.unspent_balance_crore,
                "expenditure_4yr_crore": a.total_expenditure_4yr_crore
            } for a in top_anomalies
        ],
        "advisory": ADVISORY_NOTICE
    }

@macro_router.get("/audit-logs")
def get_audit_logs(limit: int = 50, db: Session = Depends(get_db)):
    """
    Data quality audit trail logging all raw transformations, disambiguations, and cleaning rationales.
    """
    logs = db.query(DataQualityAuditLog).limit(limit).all()
    return {
        "count": len(logs),
        "logs": [
            {
                "id": l.id,
                "source_file": l.source_file,
                "row_identifier": l.row_identifier,
                "field_name": l.field_name,
                "original_value": l.original_value,
                "cleaned_value": l.cleaned_value,
                "transformation_rule": l.transformation_rule,
                "rationale": l.rationale,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None
            } for l in logs
        ]
    }
