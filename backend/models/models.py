from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean, DateTime, Date,
    ForeignKey, Numeric, Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship
from backend.core.database import Base

# ---------------------------------------------------------
# 1. AUTHENTICATION & USERS
# ---------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(128), nullable=True)
    role = Column(String(32), default="OFFICER", nullable=False)  # ADMIN, OFFICER, ANALYST, VIEWER
    department = Column(String(128), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ---------------------------------------------------------
# 2. DATA SOURCES & PROVENANCE
# ---------------------------------------------------------
class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(255), nullable=False)
    source_url = Column(String(1024), nullable=True)
    source_type = Column(String(64), nullable=False)  # GOVERNMENT_PORTAL, OPEN_DATA_CSV, OFFICER_UPLOAD, SYNTHETIC
    retrieval_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_modified = Column(DateTime, nullable=True)
    license = Column(String(128), default="NDSAP / Government Open Data")
    access_method = Column(String(64), default="CSV_INGEST")
    verification_status = Column(String(64), default="PUBLIC_VERIFIED")  # PUBLIC_VERIFIED, AUTHORIZED, SYNTHETIC, MISSING
    file_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    projects = relationship("Project", back_populates="source")

# ---------------------------------------------------------
# 3. PROJECTS TABLE
# ---------------------------------------------------------
class Project(Base):
    __tablename__ = "projects"

    project_id = Column(String(64), primary_key=True, index=True)
    project_name = Column(String(512), nullable=False)
    project_type = Column(String(64), nullable=False, index=True)  # BUILDING, ROAD, BRIDGE, WATER_TANK, OTHER
    sector = Column(String(128), nullable=True, index=True)
    state = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=False, index=True)
    constituency = Column(String(150), nullable=True)
    block = Column(String(100), nullable=True)
    village = Column(String(150), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    sanction_amount = Column(Float, nullable=False, default=0.0)
    released_amount = Column(Float, nullable=False, default=0.0)
    expenditure_amount = Column(Float, nullable=False, default=0.0)
    start_date = Column(Date, nullable=True)
    expected_completion_date = Column(Date, nullable=True)
    actual_completion_date = Column(Date, nullable=True)
    reported_progress = Column(Float, nullable=False, default=0.0)  # 0 to 100
    observed_progress = Column(Float, nullable=True)  # null when evidence unavailable
    observed_progress_status = Column(String(32), default="NOT_AVAILABLE")  # NOT_AVAILABLE, AI_ESTIMATE, OFFICER_VERIFIED
    status = Column(String(32), default="SANCTIONED", index=True)  # SANCTIONED, IN_PROGRESS, COMPLETED, STALLED, CANCELLED
    agency = Column(String(255), nullable=True)
    source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=True)
    data_availability_status = Column(String(32), default="PUBLIC_VERIFIED")  # PUBLIC_VERIFIED, AUTHORIZED, SYNTHETIC, INSUFFICIENT_DATA
    data_status = Column(String(32), default="PUBLIC_VERIFIED", index=True)  # PUBLIC_VERIFIED vs SYNTHETIC
    source_type = Column(String(64), default="GOVERNMENT_DATA", index=True)  # GOVERNMENT_DATA vs SYNTHETIC_TEST_DATA
    anomaly_label = Column(Integer, default=0, index=True)  # 0 = normal, 1 = potential anomaly
    anomaly_category = Column(String(64), default="NORMAL", index=True)  # NORMAL, UNUSUAL_FINANCIAL_PATTERN, PAYMENT_PROGRESS_MISMATCH, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    source = relationship("DataSource", back_populates="projects")
    financials = relationship("ProjectFinancial", back_populates="project", cascade="all, delete-orphan")
    progress_records = relationship("ProjectProgress", back_populates="project", cascade="all, delete-orphan")
    progress_history = relationship("ProjectProgressHistory", back_populates="project", cascade="all, delete-orphan")
    components = relationship("ProjectComponentState", back_populates="project", cascade="all, delete-orphan")

    @property
    def component_states(self):
        return self.components
    events = relationship("ProjectEvent", back_populates="project", cascade="all, delete-orphan")
    evidence_items = relationship("ProjectEvidence", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("ProjectDocument", back_populates="project", cascade="all, delete-orphan")
    locations = relationship("ProjectLocation", back_populates="project", cascade="all, delete-orphan")
    anomalies = relationship("ProjectAnomaly", back_populates="project", cascade="all, delete-orphan")
    risk_scores = relationship("RiskScore", back_populates="project", cascade="all, delete-orphan")
    verification_cases = relationship("VerificationCase", back_populates="project", cascade="all, delete-orphan")
    inspection_requests = relationship("InspectionRequest", back_populates="project", cascade="all, delete-orphan")

# ---------------------------------------------------------
# 4. FINANCIALS & PROGRESS LEDGERS
# ---------------------------------------------------------
class ProjectFinancial(Base):
    __tablename__ = "project_financials"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(64), ForeignKey("projects.project_id"), nullable=False, index=True)
    transaction_date = Column(Date, nullable=False)
    transaction_type = Column(String(64), nullable=False)  # SANCTION, RELEASE, EXPENDITURE, REFUND
    amount = Column(Float, nullable=False)
    installment_number = Column(Integer, nullable=True)
    utilization_certificate_issued = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="financials")

class ProjectProgress(Base):
    __tablename__ = "project_progress"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(64), ForeignKey("projects.project_id"), nullable=False, index=True)
    record_date = Column(Date, nullable=False)
    reported_percentage = Column(Float, nullable=False)
    observed_percentage = Column(Float, nullable=True)
    stage_description = Column(String(255), nullable=True)
    source_type = Column(String(64), default="CONTRACTOR_REPORT")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="progress_records")

class ProjectProgressHistory(Base):
    __tablename__ = "project_progress_history"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(64), ForeignKey("projects.project_id"), nullable=False, index=True)
    record_date = Column(Date, nullable=False)
    reported_progress = Column(Float, nullable=False)
    financial_expenditure = Column(Float, nullable=False, default=0.0)
    status = Column(String(32), default="IN_PROGRESS")
    data_status = Column(String(32), default="SYNTHETIC")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="progress_history")

class ProjectComponentState(Base):
    __tablename__ = "project_component_states"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(64), ForeignKey("projects.project_id"), nullable=False, index=True)
    sector = Column(String(64), nullable=False)  # BUILDING, ROAD, BRIDGE, WATER_TANK
    component_name = Column(String(64), nullable=False)
    weight_pct = Column(Float, nullable=False)
    completion_pct = Column(Float, nullable=False, default=0.0)
    detected_status = Column(String(32), default="NOT_STARTED")  # COMPLETED, IN_PROGRESS, NOT_STARTED, MISSING
    data_status = Column(String(32), default="SYNTHETIC")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="components")

class ProjectEvent(Base):
    __tablename__ = "project_events"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(64), ForeignKey("projects.project_id"), nullable=False, index=True)
    event_date = Column(Date, nullable=False)
    event_type = Column(String(64), nullable=False)  # SANCTION, TENDER, WORK_ORDER, INSPECTION, UC_SUBMISSION, ANOMALY_FLAGGED
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    actor = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="events")

# ---------------------------------------------------------
# 5. EVIDENCE & DOCUMENTS
# ---------------------------------------------------------
class ProjectEvidence(Base):
    __tablename__ = "project_evidence"

    evidence_id = Column(String(64), primary_key=True, index=True)
    project_id = Column(String(64), ForeignKey("projects.project_id"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False)
    mime_type = Column(String(100), nullable=False)  # image/jpeg, image/png, application/pdf
    file_size = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    source = Column(String(128), default="FIELD_INSPECTION")
    metadata_json = Column(Text, nullable=True)
    availability_status = Column(String(32), default="AVAILABLE")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="evidence_items")

class ProjectDocument(Base):
    __tablename__ = "project_documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(64), ForeignKey("projects.project_id"), nullable=False, index=True)
    doc_name = Column(String(255), nullable=False)
    doc_type = Column(String(64), nullable=False)  # SANCTION_ORDER, UTILIZATION_CERTIFICATE, TENDER_DOC, INSPECTION_REPORT
    file_path = Column(String(512), nullable=False)
    file_hash = Column(String(64), nullable=False)
    extracted_text = Column(Text, nullable=True)
    extracted_data_json = Column(Text, nullable=True)
    consistency_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="documents")

class ProjectLocation(Base):
    __tablename__ = "project_locations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(64), ForeignKey("projects.project_id"), nullable=False, index=True)
    location_type = Column(String(64), default="PROJECT_SITE")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(512), nullable=True)
    geocoding_source = Column(String(64), default="OFFICIAL_RECORD")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="locations")

# ---------------------------------------------------------
# 6. ANOMALIES, RISK SCORES & PREDICTIONS
# ---------------------------------------------------------
class ProjectAnomaly(Base):
    __tablename__ = "project_anomalies"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(64), ForeignKey("projects.project_id"), nullable=False, index=True)
    anomaly_type = Column(String(64), nullable=False)  # COST_ANOMALY, PAYMENT_PROGRESS_MISMATCH, DELAY_RISK, SIMILARITY, REALITY_GAP, DOC_MISMATCH
    severity = Column(String(32), default="WATCH")  # NORMAL, WATCH, HIGH, CRITICAL
    score = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    evidence_data_json = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="anomalies")

class RiskScore(Base):
    __tablename__ = "risk_scores"

    risk_score_id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(64), ForeignKey("projects.project_id"), nullable=False, index=True)
    fused_risk_score = Column(Float, nullable=False)  # 0 to 100
    risk_tier = Column(String(32), nullable=False)  # NORMAL, WATCH, HIGH, CRITICAL
    reality_gap_score = Column(Float, nullable=True)
    financial_anomaly_score = Column(Float, nullable=True)
    delay_probability = Column(Float, nullable=True)
    similarity_score = Column(Float, nullable=True)
    document_inconsistency_score = Column(Float, nullable=True)
    contributing_factors_json = Column(Text, nullable=True)
    weights_used_json = Column(Text, nullable=True)
    model_versions_json = Column(Text, nullable=True)
    confidence_score = Column(Float, default=100.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="risk_scores")

class ModelPrediction(Base):
    __tablename__ = "model_predictions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(64), ForeignKey("projects.project_id"), nullable=False, index=True)
    model_name = Column(String(128), nullable=False)
    model_version = Column(String(32), nullable=False)
    input_features_json = Column(Text, nullable=False)
    prediction_output_json = Column(Text, nullable=False)
    confidence = Column(Float, nullable=True)
    execution_time_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ModelVersion(Base):
    __tablename__ = "model_versions"

    model_id = Column(String(64), primary_key=True)
    model_name = Column(String(128), nullable=False)
    version = Column(String(32), nullable=False)
    training_data_version = Column(String(64), nullable=False)
    training_timestamp = Column(DateTime, default=datetime.utcnow)
    metrics_json = Column(Text, nullable=True)
    features_json = Column(Text, nullable=True)
    algorithm = Column(String(128), nullable=False)
    status = Column(String(32), default="ACTIVE")  # ACTIVE, RETIRED, EXPERIMENTAL, INSUFFICIENT_DATA

# ---------------------------------------------------------
# 7. DATA QUALITY & AUDIT
# ---------------------------------------------------------
class DataQualityIssue(Base):
    __tablename__ = "data_quality_issues"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(64), nullable=True, index=True)
    issue_type = Column(String(64), nullable=False)  # INVALID_COORDINATES, NEGATIVE_AMOUNT, INVALID_DATES, COMPLETION_BEFORE_START, PROGRESS_OUT_OF_BOUNDS, DUPLICATE_ID
    severity = Column(String(32), default="WARNING")  # INFO, WARNING, ERROR, CRITICAL
    details = Column(Text, nullable=False)
    original_value = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(64), nullable=False)
    action = Column(String(128), nullable=False)
    project_id = Column(String(64), nullable=True, index=True)
    previous_value_json = Column(Text, nullable=True)
    new_value_json = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class OfficerFeedback(Base):
    __tablename__ = "officer_feedback"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(64), ForeignKey("projects.project_id"), nullable=False, index=True)
    officer_id = Column(String(64), nullable=False)
    anomaly_id = Column(Integer, nullable=True)
    feedback_type = Column(String(64), nullable=False)  # CONFIRMED_ANOMALY, FALSE_POSITIVE, EXPLAINED_VARIANCE
    comments = Column(Text, nullable=True)
    action_taken = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ---------------------------------------------------------
# 8. VERIFICATION CASES & ACTIONS
# ---------------------------------------------------------
class VerificationCase(Base):
    __tablename__ = "verification_cases"

    case_id = Column(String(64), primary_key=True, index=True)
    project_id = Column(String(64), ForeignKey("projects.project_id"), nullable=False, index=True)
    assigned_officer_id = Column(String(64), nullable=True)
    case_status = Column(String(32), default="OPEN", index=True)  # OPEN, IN_REVIEW, VERIFIED_NORMAL, IRREGULARITY_CONFIRMED, CLOSED
    priority = Column(String(32), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    trigger_reason = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)
    officer_findings = Column(Text, nullable=True)
    resolution_timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="verification_cases")
    actions = relationship("VerificationAction", back_populates="case", cascade="all, delete-orphan")

class VerificationAction(Base):
    __tablename__ = "verification_actions"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("verification_cases.case_id"), nullable=False, index=True)
    action_type = Column(String(64), nullable=False)  # FIELD_VISIT_ORDERED, DOCUMENT_AUDIT_REQUESTED, EXPLANATION_SOUGHT, CASE_RESOLVED
    officer_id = Column(String(64), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("VerificationCase", back_populates="actions")


# ---------------------------------------------------------
# 9. FIELD INSPECTION REQUESTS & APPROVAL WORKFLOW
# ---------------------------------------------------------
class InspectionRequest(Base):
    __tablename__ = "inspection_requests"

    request_id = Column(String(64), primary_key=True, index=True)
    project_id = Column(String(64), ForeignKey("projects.project_id"), nullable=False, index=True)
    inspector_name = Column(String(128), nullable=False)
    state = Column(String(128), nullable=False)
    district = Column(String(128), nullable=False)
    reason_for_inspection = Column(Text, nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_tier = Column(String(32), nullable=False)
    contributing_factors_json = Column(Text, nullable=True)
    evidence_available = Column(Text, nullable=True)
    evidence_missing = Column(Text, nullable=True)
    proposed_date = Column(String(32), nullable=False)
    priority = Column(String(32), default="HIGH")  # LOW, MEDIUM, HIGH, CRITICAL
    requested_by = Column(String(128), nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow)
    approving_officer = Column(String(128), nullable=True)
    approval_status = Column(String(32), default="DRAFT", index=True)  # DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED, COMPLETED
    approval_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="inspection_requests")
