import os
import json
import hashlib
from datetime import datetime
from typing import Optional, List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.core.database import get_db
from backend.core.config import settings
from backend.models.models import (
    Project, ProjectFinancial, ProjectEvent, ProjectEvidence, ProjectDocument,
    RiskScore, ProjectAnomaly, ModelVersion, DataSource, DataQualityIssue,
    VerificationCase, VerificationAction, User, AuditLog
)
from backend.schemas.schemas import (
    Token, LoginRequest, UserResponse, ProjectListItem, ProjectDetail,
    RealityGapResponse, VerificationCaseCreate, VerificationCaseUpdate,
    AssistantQueryRequest, AssistantQueryResponse
)
from backend.services.auth import (
    verify_password, create_access_token, get_current_user, require_role, seed_default_users
)
from backend.services.reality_gap import RealityGapEngine
from backend.services.recommendations import VerificationRecommendationEngine
from backend.services.digital_twin import DigitalTwinEngine
from backend.services.pdf_report import PDFReportGenerator
from backend.services.assistant import ContextualAssistant
from ml.models.similarity_model import SimilarityEngine

api_router = APIRouter()

# ---------------------------------------------------------
# 1. SYSTEM HEALTH & DATA MONITORING
# ---------------------------------------------------------
@api_router.get("/health")
def health_check(db: Session = Depends(get_db)):
    project_count = db.query(Project).count()
    model_count = db.query(ModelVersion).filter_by(status="ACTIVE").count()
    return {
        "status": "HEALTHY",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "CONNECTED",
        "active_projects": project_count,
        "active_models": model_count,
        "version": settings.APP_VERSION,
        "advisory": "AI-generated risk indicators are decision-support signals and do not constitute proof of fraud, corruption, or wrongdoing."
    }

@api_router.get("/data/sources")
def get_data_sources(db: Session = Depends(get_db)):
    sources = db.query(DataSource).all()
    return [{
        "id": s.id,
        "source_name": s.source_name,
        "source_url": s.source_url,
        "source_type": s.source_type,
        "retrieval_timestamp": s.retrieval_timestamp.isoformat() if s.retrieval_timestamp else None,
        "verification_status": s.verification_status,
        "access_method": s.access_method,
        "file_hash": s.file_hash
    } for s in sources]

@api_router.get("/data/quality")
def get_data_quality(db: Session = Depends(get_db)):
    issues = db.query(DataQualityIssue).order_by(desc(DataQualityIssue.created_at)).limit(50).all()
    total_projects = db.query(Project).count()
    projects_with_coords = db.query(Project).filter(Project.latitude.isnot(None), Project.longitude.isnot(None)).count()
    projects_with_evidence = db.query(Project).filter(Project.observed_progress.isnot(None)).count()

    quality_score = 100.0
    if total_projects > 0:
        coord_pct = (projects_with_coords / total_projects) * 100.0
        evidence_pct = (projects_with_evidence / total_projects) * 100.0
        quality_score = round(0.5 * coord_pct + 0.5 * evidence_pct, 1)

    return {
        "overall_data_quality_score": quality_score,
        "total_projects": total_projects,
        "projects_with_valid_coordinates": projects_with_coords,
        "projects_with_ground_evidence": projects_with_evidence,
        "recent_quality_issues": [{
            "id": i.id,
            "project_id": i.project_id,
            "issue_type": i.issue_type,
            "severity": i.severity,
            "details": i.details,
            "original_value": i.original_value,
            "created_at": i.created_at.isoformat()
        } for i in issues]
    }

@api_router.post("/data/refresh")
def refresh_data_pipeline(
    current_user: User = Depends(require_role(["ADMIN", "OFFICER"])),
    db: Session = Depends(get_db)
):
    from data_pipeline.run import run_pipeline
    from ml.inference import run_inference
    loaded = run_pipeline()
    run_inference()
    return {"status": "SUCCESS", "message": f"Pipeline refreshed. Processed {loaded} projects."}

# ---------------------------------------------------------
# 2. AUTHENTICATION & USER MANAGEMENT
# ---------------------------------------------------------
@api_router.post("/auth/login", response_model=Token)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    # Ensure default users exist
    seed_default_users(db)
    user = db.query(User).filter_by(username=req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    token = create_access_token(data={"sub": user.username, "role": user.role})
    return Token(access_token=token, token_type="bearer", role=user.role, username=user.username)

@api_router.get("/auth/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        full_name=current_user.full_name,
        department=current_user.department
    )

# ---------------------------------------------------------
# 3. PROJECTS & INTELLIGENCE
# ---------------------------------------------------------
@api_router.get("/projects", response_model=List[ProjectListItem])
def list_projects(
    state: Optional[str] = None,
    district: Optional[str] = None,
    project_type: Optional[str] = None,
    risk_tier: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    data_status: Optional[str] = Query(None, alias="data_status"),
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Project)
    if state:
        query = query.filter(Project.state.ilike(f"%{state}%"))
    if district:
        query = query.filter(Project.district.ilike(f"%{district}%"))
    if project_type:
        query = query.filter(Project.project_type == project_type)
    if status_filter:
        query = query.filter(Project.status == status_filter)
    if data_status:
        query = query.filter(Project.data_availability_status == data_status)
    if search:
        query = query.filter(Project.project_name.ilike(f"%{search}%") | Project.project_id.ilike(f"%{search}%"))

    projects = query.offset(skip).limit(limit).all()

    results = []
    for p in projects:
        rs = db.query(RiskScore).filter_by(project_id=p.project_id).first()
        item = ProjectListItem.from_orm(p)
        if rs:
            item.fused_risk_score = rs.fused_risk_score
            item.risk_tier = rs.risk_tier
            item.reality_gap_score = rs.reality_gap_score

        if risk_tier and item.risk_tier != risk_tier:
            continue
        results.append(item)

    return results

@api_router.get("/projects/{project_id}", response_model=ProjectDetail)
def get_project_detail(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter_by(project_id=project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    rs = db.query(RiskScore).filter_by(project_id=project_id).first()
    rg_data = RealityGapEngine.evaluate(p)

    sim_path = settings.MODEL_DIR / "similarity" / "similarity_model.joblib"
    sim_engine = SimilarityEngine.load(str(sim_path)) if sim_path.exists() else None
    sim_matches = sim_engine.find_similar(p, top_k=3) if sim_engine else []

    recs = VerificationRecommendationEngine.generate_recommendations(p, rs, rg_data, sim_matches)

    detail = ProjectDetail.model_validate(p)
    if rs:
        detail.risk_summary = {
            "fused_risk_score": rs.fused_risk_score,
            "risk_tier": rs.risk_tier,
            "reality_gap_score": rs.reality_gap_score,
            "financial_anomaly_score": rs.financial_anomaly_score,
            "delay_probability": rs.delay_probability,
            "similarity_score": rs.similarity_score,
            "contributing_factors": json.loads(rs.contributing_factors_json) if rs.contributing_factors_json else []
        }
    detail.reality_gap_summary = rg_data
    detail.recommendations = recs
    return detail

@api_router.get("/projects/{project_id}/risk")
def get_project_risk(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter_by(project_id=project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    rs = db.query(RiskScore).filter_by(project_id=project_id).first()
    if not rs:
        from ml.inference import run_inference
        run_inference()
        rs = db.query(RiskScore).filter_by(project_id=project_id).first()

    return {
        "project_id": project_id,
        "fused_risk_score": rs.fused_risk_score if rs else 0.0,
        "risk_tier": rs.risk_tier if rs else "NORMAL",
        "reality_gap_score": rs.reality_gap_score if rs else None,
        "financial_anomaly_score": rs.financial_anomaly_score if rs else None,
        "delay_probability": rs.delay_probability if rs else None,
        "similarity_score": rs.similarity_score if rs else None,
        "contributing_factors": json.loads(rs.contributing_factors_json) if (rs and rs.contributing_factors_json) else [],
        "weights_used": json.loads(rs.weights_used_json) if (rs and rs.weights_used_json) else {},
        "model_versions": json.loads(rs.model_versions_json) if (rs and rs.model_versions_json) else {},
        "disclaimer": "AI-generated risk indicators are decision-support signals and do not constitute proof of fraud, corruption, or wrongdoing."
    }

@api_router.get("/projects/{project_id}/reality-gap", response_model=RealityGapResponse)
def get_project_reality_gap(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter_by(project_id=project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return RealityGapEngine.evaluate(p)

@api_router.get("/projects/{project_id}/digital-twin")
def get_project_digital_twin(
    project_id: str,
    simulated_progress: Optional[float] = None,
    db: Session = Depends(get_db)
):
    p = db.query(Project).filter_by(project_id=project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return DigitalTwinEngine.generate_twin_scene(p, simulated_progress=simulated_progress)

@api_router.get("/projects/{project_id}/timeline")
def get_project_timeline(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter_by(project_id=project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    events = db.query(ProjectEvent).filter_by(project_id=project_id).order_by(ProjectEvent.event_date).all()
    if not events:
        return {
            "project_id": project_id,
            "status": "NO_HISTORICAL_DATA",
            "message": "Historical evidence unavailable.",
            "events": []
        }
    return {
        "project_id": project_id,
        "status": "AVAILABLE",
        "events": [{
            "id": e.id,
            "date": e.event_date.isoformat(),
            "type": e.event_type,
            "title": e.title,
            "description": e.description,
            "actor": e.actor
        } for e in events]
    }

@api_router.get("/projects/{project_id}/recommendations")
def get_project_recommendations(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter_by(project_id=project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    rs = db.query(RiskScore).filter_by(project_id=project_id).first()
    rg_data = RealityGapEngine.evaluate(p)
    
    sim_path = settings.MODEL_DIR / "similarity" / "similarity_model.joblib"
    sim_engine = SimilarityEngine.load(str(sim_path)) if sim_path.exists() else None
    sim_matches = sim_engine.find_similar(p, top_k=2) if sim_engine else []

    return VerificationRecommendationEngine.generate_recommendations(p, rs, rg_data, sim_matches)

@api_router.get("/projects/{project_id}/report")
def download_project_report(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter_by(project_id=project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    
    rs = db.query(RiskScore).filter_by(project_id=project_id).first()
    rg_data = RealityGapEngine.evaluate(p)
    recs = VerificationRecommendationEngine.generate_recommendations(p, rs, rg_data, [])

    report_path = str(settings.REPORTS_DIR / f"NIRVANA_Dossier_{project_id}.pdf")
    PDFReportGenerator.generate_project_dossier(
        project=p,
        reality_gap_data=rg_data,
        risk_data={"fused_risk_score": rs.fused_risk_score, "risk_tier": rs.risk_tier} if rs else {},
        recommendations=recs,
        output_path=report_path
    )
    return FileResponse(report_path, media_type="application/pdf", filename=f"NIRVANA_Dossier_{project_id}.pdf")

# ---------------------------------------------------------
# 4. EVIDENCE INGESTION
# ---------------------------------------------------------
@api_router.get("/projects/{project_id}/evidence")
def list_project_evidence(project_id: str, db: Session = Depends(get_db)):
    evidence = db.query(ProjectEvidence).filter_by(project_id=project_id).all()
    return [{
        "evidence_id": ev.evidence_id,
        "project_id": ev.project_id,
        "file_name": ev.file_name,
        "file_hash": ev.file_hash,
        "mime_type": ev.mime_type,
        "file_size": ev.file_size,
        "timestamp": ev.timestamp.isoformat(),
        "latitude": ev.latitude,
        "longitude": ev.longitude,
        "source": ev.source
    } for ev in evidence]

@api_router.post("/evidence/upload")
async def upload_evidence(
    project_id: str = Form(...),
    source: str = Form("FIELD_INSPECTION"),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    observed_progress: Optional[float] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(["ADMIN", "OFFICER"])),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter_by(project_id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    content = await file.read()
    file_size = len(content)

    if file_size > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 15MB limit")

    # MIME Validation (never trust extension alone)
    allowed_mimes = ["image/jpeg", "image/png", "application/pdf"]
    content_type = file.content_type
    if content_type not in allowed_mimes:
        # Magic bytes check
        if content.startswith(b"\xff\xd8\xff"):
            content_type = "image/jpeg"
        elif content.startswith(b"\x89PNG\r\n\x1a\n"):
            content_type = "image/png"
        elif content.startswith(b"%PDF"):
            content_type = "application/pdf"
        else:
            raise HTTPException(status_code=400, detail="Invalid file type. Allowed: JPEG, PNG, PDF")

    sha256 = hashlib.sha256(content).hexdigest()
    evidence_id = f"EV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{sha256[:8]}"
    save_path = settings.UPLOAD_DIR / f"{evidence_id}_{file.filename}"
    save_path.write_bytes(content)

    ev = ProjectEvidence(
        evidence_id=evidence_id,
        project_id=project_id,
        file_name=file.filename,
        file_hash=sha256,
        mime_type=content_type,
        file_size=file_size,
        latitude=latitude,
        longitude=longitude,
        source=source
    )
    db.add(ev)

    # If observed progress was submitted by officer, update project observed progress
    if observed_progress is not None:
        project.observed_progress = max(0.0, min(100.0, float(observed_progress)))
        project.observed_progress_status = "OFFICER_VERIFIED"
        project.updated_at = datetime.utcnow()

    # Audit log
    audit = AuditLog(
        user_id=current_user.username,
        action="EVIDENCE_UPLOAD",
        project_id=project_id,
        new_value_json=json.dumps({"evidence_id": evidence_id, "file_name": file.filename, "sha256": sha256})
    )
    db.add(audit)
    db.commit()

    return {
        "status": "SUCCESS",
        "evidence_id": evidence_id,
        "file_hash": sha256,
        "message": "Evidence uploaded, verified, and linked to project."
    }

# ---------------------------------------------------------
# 5. VERIFICATION CASES (HUMAN-IN-THE-LOOP)
# ---------------------------------------------------------
@api_router.get("/verification-cases")
def list_verification_cases(
    case_status: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(VerificationCase)
    if case_status:
        q = q.filter(VerificationCase.case_status == case_status)
    if priority:
        q = q.filter(VerificationCase.priority == priority)
    cases = q.order_by(desc(VerificationCase.created_at)).all()

    return [{
        "case_id": c.case_id,
        "project_id": c.project_id,
        "project_name": c.project.project_name if c.project else "Unknown",
        "case_status": c.case_status,
        "priority": c.priority,
        "trigger_reason": c.trigger_reason,
        "recommended_action": c.recommended_action,
        "officer_findings": c.officer_findings,
        "created_at": c.created_at.isoformat()
    } for c in cases]

@api_router.post("/verification-cases")
def create_verification_case(
    payload: VerificationCaseCreate,
    current_user: User = Depends(require_role(["ADMIN", "OFFICER", "ANALYST"])),
    db: Session = Depends(get_db)
):
    case_id = f"CASE-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    case = VerificationCase(
        case_id=case_id,
        project_id=payload.project_id,
        assigned_officer_id=current_user.username,
        priority=payload.priority,
        trigger_reason=payload.trigger_reason,
        recommended_action=payload.recommended_action,
        case_status="OPEN"
    )
    db.add(case)
    db.commit()
    return {"case_id": case_id, "status": "CREATED"}

@api_router.patch("/verification-cases/{case_id}")
def update_verification_case(
    case_id: str,
    payload: VerificationCaseUpdate,
    current_user: User = Depends(require_role(["ADMIN", "OFFICER"])),
    db: Session = Depends(get_db)
):
    case = db.query(VerificationCase).filter_by(case_id=case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case.case_status = payload.case_status
    if payload.officer_findings:
        case.officer_findings = payload.officer_findings
    if payload.case_status in ("CLOSED", "VERIFIED_NORMAL", "IRREGULARITY_CONFIRMED"):
        case.resolution_timestamp = datetime.utcnow()

    action = VerificationAction(
        case_id=case_id,
        action_type="STATUS_UPDATE",
        officer_id=current_user.username,
        notes=f"Status set to {payload.case_status}. Findings: {payload.officer_findings or 'None'}"
    )
    db.add(action)
    db.commit()
    return {"case_id": case_id, "status": case.case_status}

# ---------------------------------------------------------
# 6. MODEL REGISTRY & ML MONITORING
# ---------------------------------------------------------
@api_router.get("/models")
def list_models(db: Session = Depends(get_db)):
    mvs = db.query(ModelVersion).all()
    return [{
        "model_id": m.model_id,
        "model_name": m.model_name,
        "version": m.version,
        "training_data_version": m.training_data_version,
        "algorithm": m.algorithm,
        "training_timestamp": m.training_timestamp.isoformat() if m.training_timestamp else None,
        "status": m.status,
        "metrics": json.loads(m.metrics_json) if m.metrics_json else {}
    } for m in mvs]

@api_router.get("/models/{model_id}")
def get_model_detail(model_id: str, db: Session = Depends(get_db)):
    m = db.query(ModelVersion).filter_by(model_id=model_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Model version not found")
    return {
        "model_id": m.model_id,
        "model_name": m.model_name,
        "version": m.version,
        "training_data_version": m.training_data_version,
        "algorithm": m.algorithm,
        "status": m.status,
        "features": json.loads(m.features_json) if m.features_json else [],
        "metrics": json.loads(m.metrics_json) if m.metrics_json else {}
    }

@api_router.get("/models/{model_id}/metrics")
def get_model_metrics(model_id: str, db: Session = Depends(get_db)):
    m = db.query(ModelVersion).filter_by(model_id=model_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Model version not found")
    return json.loads(m.metrics_json) if m.metrics_json else {"status": "INSUFFICIENT_DATA"}

# ---------------------------------------------------------
# 7. ANALYTICS & ASSISTANT
# ---------------------------------------------------------
@api_router.get("/analytics/overview")
def get_analytics_overview(db: Session = Depends(get_db)):
    total = db.query(Project).count()
    monitored = db.query(RiskScore).count()
    high_risk = db.query(RiskScore).filter_by(risk_tier="HIGH").count()
    critical = db.query(RiskScore).filter_by(risk_tier="CRITICAL").count()
    delayed = db.query(RiskScore).filter(RiskScore.delay_probability > 0.5).count()
    reality_gaps = db.query(RiskScore).filter(RiskScore.reality_gap_score > 30.0).count()

    return {
        "total_projects": total,
        "projects_monitored": monitored,
        "high_risk_projects": high_risk,
        "critical_risk_projects": critical,
        "delayed_projects": delayed,
        "active_reality_gaps": reality_gaps,
        "advisory": "AI-generated risk indicators are decision-support signals and do not constitute proof of fraud, corruption, or wrongdoing."
    }

@api_router.post("/assistant/query", response_model=AssistantQueryResponse)
def query_ai_assistant(req: AssistantQueryRequest, db: Session = Depends(get_db)):
    res = ContextualAssistant.answer_query(query=req.query, project_id=req.project_id, db=db)
    return AssistantQueryResponse(
        answer=res["answer"],
        citations=res["citations"],
        disclaimer=res["disclaimer"]
    )
