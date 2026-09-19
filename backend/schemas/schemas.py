from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str

class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    full_name: Optional[str] = None
    department: Optional[str] = None

    class Config:
        from_attributes = True

# Sub-item Schemas
class FinancialItem(BaseModel):
    id: int
    transaction_date: date
    transaction_type: str
    amount: float
    installment_number: Optional[int] = None
    utilization_certificate_issued: Optional[bool] = False

    class Config:
        from_attributes = True

class EventItem(BaseModel):
    id: int
    event_date: date
    event_type: str
    title: str
    description: Optional[str] = None
    actor: Optional[str] = None

    class Config:
        from_attributes = True

class EvidenceItem(BaseModel):
    evidence_id: str
    file_name: str
    mime_type: str
    file_size: int
    timestamp: datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source: str

    class Config:
        from_attributes = True

# Project Schemas
class ProjectBase(BaseModel):
    project_id: str
    project_name: str
    project_type: str
    sector: Optional[str] = None
    state: str
    district: str
    constituency: Optional[str] = None
    block: Optional[str] = None
    village: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    sanction_amount: float
    released_amount: float
    expenditure_amount: float
    start_date: Optional[date] = None
    expected_completion_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    reported_progress: float
    observed_progress: Optional[float] = None
    observed_progress_status: str = "NOT_AVAILABLE"
    status: str
    agency: Optional[str] = None
    data_availability_status: str = "PUBLIC_VERIFIED"
    data_status: Optional[str] = "PUBLIC_VERIFIED"
    source_type: Optional[str] = "OFFICIAL_MPLADS"
    anomaly_label: Optional[int] = 0
    anomaly_category: Optional[str] = None

class ComponentStateItem(BaseModel):
    id: int
    project_id: str
    sector: str
    component_name: str
    weight_pct: float
    completion_pct: float
    detected_status: str
    data_status: str = "SYNTHETIC"
    source_type: Optional[str] = "SYNTHETIC_TEST_DATA"

    model_config = {"from_attributes": True}

class ProgressHistoryItem(BaseModel):
    id: int
    project_id: str
    record_date: date
    reported_progress: float
    financial_expenditure: float
    status: str
    data_status: str = "SYNTHETIC"
    source_type: Optional[str] = "SYNTHETIC_TEST_DATA"

    model_config = {"from_attributes": True}

class ProjectListItem(ProjectBase):
    fused_risk_score: Optional[float] = 0.0
    risk_tier: Optional[str] = "NORMAL"
    reality_gap_score: Optional[float] = None

    model_config = {"from_attributes": True}

class ProjectDetail(ProjectBase):
    created_at: datetime
    updated_at: Optional[datetime] = None
    financials: List[FinancialItem] = []
    events: List[EventItem] = []
    evidence_items: List[EvidenceItem] = []
    component_states: List[ComponentStateItem] = []
    progress_history: List[ProgressHistoryItem] = []
    risk_summary: Optional[Dict[str, Any]] = None
    reality_gap_summary: Optional[Dict[str, Any]] = None
    recommendations: List[Dict[str, Any]] = []

    model_config = {"from_attributes": True}

# Reality Gap & Risk
class RealityGapResponse(BaseModel):
    project_id: str
    project_name: str
    expected_progress: Optional[float] = None
    expected_lower_bound: Optional[float] = None
    expected_upper_bound: Optional[float] = None
    reported_progress: float
    observed_progress: Optional[float] = None
    observed_progress_status: str
    financial_utilization: float
    time_elapsed_ratio: Optional[float] = None
    reality_gap_score: float
    reality_gap_tier: str
    confidence: float
    components: Dict[str, Any]
    contributing_factors: List[str]
    notice: str
    disclaimer: str

# Verification Cases
class VerificationCaseCreate(BaseModel):
    project_id: str
    priority: str = "MEDIUM"
    trigger_reason: str
    recommended_action: str

class VerificationCaseUpdate(BaseModel):
    case_status: str
    officer_findings: Optional[str] = None

class AssistantQueryRequest(BaseModel):
    query: str
    project_id: Optional[str] = None

class AssistantQueryResponse(BaseModel):
    answer: str
    citations: List[str]
    disclaimer: str

# Field Inspection Requests & Superior Approval
class InspectionRequestCreate(BaseModel):
    project_id: str
    inspector_name: str
    proposed_date: Optional[str] = None
    priority: str = "HIGH"
    reason_for_inspection: Optional[str] = None
    evidence_available: Optional[str] = None
    evidence_missing: Optional[str] = None
    approving_officer: Optional[str] = None

class InspectionStatusUpdate(BaseModel):
    approval_status: str  # DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED, COMPLETED
    approving_officer: Optional[str] = None
    approval_notes: Optional[str] = None
