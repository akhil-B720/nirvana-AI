from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean, DateTime,
    ForeignKey, Index
)
from backend.core.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class StateYearlyPerformance(Base):
    """
    State-level yearly expenditure and completed works.
    Sourced from official MoSPI / Parliamentary reports (FY 2016-17 to 2019-20).
    """
    __tablename__ = "state_yearly_performance"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(128), index=True, nullable=False)
    financial_year = Column(String(16), index=True, nullable=False)  # 2016-17, 2017-18, 2018-19, 2019-20
    expenditure_crore = Column(Float, nullable=False)
    completed_works = Column(Integer, nullable=False)
    avg_cost_per_work_lakhs = Column(Float, nullable=True)
    
    # Provenance
    source_file = Column(String(255), default="mplads_state_yearly_expenditure_and_works.csv")
    verification_status = Column(String(32), default="PUBLIC_VERIFIED")
    raw_record_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        Index("ix_state_year", "state", "financial_year", unique=True),
    )

class StateSectoralAllocation(Base):
    """
    State-level percentage sectoral expenditure distribution under MPLADS.
    """
    __tablename__ = "state_sectoral_allocations"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(128), unique=True, index=True, nullable=False)
    railways_roads_bridges_pct = Column(Float, nullable=True)
    education_pct = Column(Float, nullable=True)
    drinking_water_pct = Column(Float, nullable=True)
    sanitation_health_pct = Column(Float, nullable=True)
    other_public_facilities_pct = Column(Float, nullable=True)
    others_pct = Column(Float, nullable=True)
    
    # Provenance
    source_file = Column(String(255), default="mplads_state_sector_distribution.csv")
    verification_status = Column(String(32), default="PUBLIC_VERIFIED")
    raw_record_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=utcnow)

class StateUnspentLiquidity(Base):
    """
    State-level unspent fund balances sitting in district authority bank accounts.
    """
    __tablename__ = "state_unspent_liquidity"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(128), unique=True, index=True, nullable=False)
    unspent_balance_crore = Column(Float, nullable=False)
    
    # Provenance
    source_file = Column(String(255), default="mplads_state_unspent_balance.csv")
    verification_status = Column(String(32), default="PUBLIC_VERIFIED")
    raw_record_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=utcnow)

class StateMacroMetrics(Base):
    """
    Master analytical snapshot synthesizing multi-year performance,
    backlog absorption ratio, sector concentration, and ML anomaly signals.
    """
    __tablename__ = "state_macro_metrics"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(128), unique=True, index=True, nullable=False)
    
    # Aggregated 4-Year Totals
    total_expenditure_4yr_crore = Column(Float, nullable=False)
    total_works_completed_4yr = Column(Integer, nullable=False)
    avg_annual_expenditure_crore = Column(Float, nullable=False)
    avg_annual_works = Column(Float, nullable=False)
    cost_per_work_lakhs = Column(Float, nullable=False)

    # Liquidity & Backlog
    unspent_balance_crore = Column(Float, nullable=True)
    backlog_absorption_years = Column(Float, nullable=True)  # unspent / avg_annual_expenditure

    # Dynamics & Volatility
    yoy_growth_17_18_pct = Column(Float, nullable=True)
    yoy_growth_18_19_pct = Column(Float, nullable=True)
    yoy_growth_19_20_pct = Column(Float, nullable=True)
    expenditure_volatility_cv = Column(Float, nullable=True)  # std / mean
    covid_drop_19_20_pct = Column(Float, nullable=True)

    # Sector Indicators
    infrastructure_dominance_pct = Column(Float, nullable=True)  # Roads & Bridges
    social_infrastructure_pct = Column(Float, nullable=True)     # Water + Sanitation + Education
    sector_hhi = Column(Float, nullable=True)                    # Concentration index

    # ML Output
    is_anomaly = Column(Boolean, default=False)
    anomaly_score = Column(Float, nullable=True)  # Continuous Isolation Forest score
    risk_cluster = Column(Integer, nullable=True) # K-Means cluster
    risk_tier = Column(String(32), default="NORMAL") # NORMAL, WATCH, HIGH_BACKLOG, CRITICAL_BOTTLENECK

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

class DataQualityAuditLog(Base):
    """
    Audit log preserving original vs cleaned values, rationale, and provenance.
    """
    __tablename__ = "data_quality_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    source_file = Column(String(255), nullable=False)
    row_identifier = Column(String(128), nullable=True)
    field_name = Column(String(128), nullable=False)
    original_value = Column(Text, nullable=True)
    cleaned_value = Column(Text, nullable=True)
    transformation_rule = Column(String(128), nullable=False)
    rationale = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=utcnow)
