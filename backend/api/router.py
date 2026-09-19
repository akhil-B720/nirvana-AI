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
    VerificationCase, VerificationAction, User, AuditLog, InspectionRequest,
    ProjectComponentState, ProjectProgressHistory
)
from backend.schemas.schemas import (
    Token, LoginRequest, UserResponse, ProjectListItem, ProjectDetail,
    RealityGapResponse, VerificationCaseCreate, VerificationCaseUpdate,
    AssistantQueryRequest, AssistantQueryResponse,
    InspectionRequestCreate, InspectionStatusUpdate,
    ComponentStateItem, ProgressHistoryItem
)
from backend.services.auth import (
    verify_password, create_access_token, get_current_user, require_role, seed_default_users
)
from backend.services.reality_gap import RealityGapEngine
from backend.services.recommendations import VerificationRecommendationEngine
from backend.services.digital_twin import DigitalTwinEngine
from backend.services.pdf_report import PDFReportGenerator
from backend.services.assistant import ContextualAssistant
from backend.services.progress_estimator import ProgressEstimator
from ml.models.similarity_model import SimilarityEngine
from ml.models.project_risk_model import ProjectRiskModel
from ml.models.delay_model import DelayRiskModel

_cached_project_risk_model = None

def get_project_risk_model():
    global _cached_project_risk_model
    if _cached_project_risk_model is None:
        model_path = settings.MODEL_DIR / "project_risk" / "project_risk_model.joblib"
        if model_path.exists():
            _cached_project_risk_model = ProjectRiskModel.load(str(model_path))
        else:
            _cached_project_risk_model = ProjectRiskModel()
    return _cached_project_risk_model

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
        if data_status.upper() in ("SYNTHETIC", "PUBLIC_VERIFIED"):
            query = query.filter(Project.data_status == data_status.upper())
        elif data_status.upper() == "ALL":
            pass
        else:
            query = query.filter((Project.data_status == data_status) | (Project.data_availability_status == data_status))
    else:
        # Strictly preserve isolation: default to PUBLIC_VERIFIED government records
        query = query.filter(Project.data_status == "PUBLIC_VERIFIED")
    if search:
        query = query.filter(Project.project_name.ilike(f"%{search}%") | Project.project_id.ilike(f"%{search}%"))

    projects = query.offset(skip).limit(limit).all()

    results = []
    for p in projects:
        rs = db.query(RiskScore).filter_by(project_id=p.project_id).first()
        item = ProjectListItem.model_validate(p)
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

    model = get_project_risk_model()
    feat = model.extract_single_feature_vector(p)
    contributing = json.loads(rs.contributing_factors_json) if (rs and rs.contributing_factors_json) else []

    tier_map = {"NORMAL": "LOW", "WATCH": "MEDIUM", "HIGH": "HIGH", "CRITICAL": "CRITICAL"}
    risk_level = tier_map.get(rs.risk_tier, rs.risk_tier) if rs else "LOW"
    conf_val = round((rs.confidence_score / 100.0) if (rs and rs.confidence_score) else 0.70, 2)
    source_name = p.source.source_name if p.source else "Official MoSPI MPLADS Records (ODbL)"

    return {
        "project_id": project_id,
        "risk_score": rs.fused_risk_score if rs else 0.0,
        "risk_level": risk_level,
        "confidence": conf_val,
        "contributing_factors": contributing,
        "feature_values": feat,
        "model_version": model.version,
        "data_source": source_name,
        "timestamp": datetime.utcnow().isoformat(),
        # Backward-compatibility fields
        "fused_risk_score": rs.fused_risk_score if rs else 0.0,
        "risk_tier": rs.risk_tier if rs else "NORMAL",
        "reality_gap_score": rs.reality_gap_score if rs else None,
        "financial_anomaly_score": rs.financial_anomaly_score if rs else None,
        "delay_probability": rs.delay_probability if rs else None,
        "similarity_score": rs.similarity_score if rs else None,
        "weights_used": json.loads(rs.weights_used_json) if (rs and rs.weights_used_json) else {},
        "model_versions": json.loads(rs.model_versions_json) if (rs and rs.model_versions_json) else {},
        "disclaimer": "AI-generated risk indicators are analytical decision-support signals and do not constitute proof of fraud, corruption, or irregularity."
    }

@api_router.get("/projects/{project_id}/delay-risk")
def get_project_delay_risk(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter_by(project_id=project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    dm = DelayRiskModel()
    pred = dm.predict_project(p)
    return {
        "project_id": project_id,
        "predicted_delay_days": pred.get("predicted_delay_days"),
        "delay_probability": pred.get("delay_probability"),
        "confidence": pred.get("confidence", 70.0),
        "model_status": pred.get("model_status"),
        "data_status": getattr(p, "data_status", "PUBLIC_VERIFIED"),
        "is_synthetic": getattr(p, "data_status", "PUBLIC_VERIFIED") == "SYNTHETIC",
        "explanation": pred.get("explanation"),
        "disclaimer": "AI-generated risk indicators are analytical decision-support signals and do not constitute proof of fraud, corruption, or irregularity."
    }

@api_router.get("/projects/{project_id}/anomalies")
def get_project_anomalies(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter_by(project_id=project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    anomalies = db.query(ProjectAnomaly).filter_by(project_id=project_id, is_active=True).all()
    source_name = p.source.source_name if p.source else "Official MoSPI MPLADS Records (ODbL)"

    return {
        "project_id": project_id,
        "active_anomaly_count": len(anomalies),
        "anomalies": [{
            "id": a.id,
            "anomaly_type": a.anomaly_type,
            "severity": a.severity,
            "score": a.score,
            "description": a.description,
            "evidence_data": json.loads(a.evidence_data_json) if a.evidence_data_json else None,
            "created_at": a.created_at.isoformat() if a.created_at else None
        } for a in anomalies],
        "data_source": source_name,
        "timestamp": datetime.utcnow().isoformat(),
        "disclaimer": "AI-generated risk indicators are analytical decision-support signals and do not constitute proof of fraud, corruption, or irregularity."
    }

@api_router.get("/projects/{project_id}/explanation")
def get_project_explanation(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter_by(project_id=project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    rs = db.query(RiskScore).filter_by(project_id=project_id).first()
    model = get_project_risk_model()
    feat = model.extract_single_feature_vector(p)

    contributing = json.loads(rs.contributing_factors_json) if (rs and rs.contributing_factors_json) else []
    tier_map = {"NORMAL": "LOW", "WATCH": "MEDIUM", "HIGH": "HIGH", "CRITICAL": "CRITICAL"}
    risk_level = tier_map.get(rs.risk_tier, rs.risk_tier) if rs else "LOW"

    sec = p.sector or "OTHER"
    sec_med = model.sector_medians.get(sec, model.global_median_cost)
    st = p.state or "UNKNOWN"
    st_med = model.state_medians.get(st, model.global_median_cost)

    return {
        "project_id": project_id,
        "risk_score": rs.fused_risk_score if rs else 0.0,
        "risk_level": risk_level,
        "confidence": round((rs.confidence_score / 100.0) if (rs and rs.confidence_score) else 0.70, 2),
        "analytical_summary": "; ".join(contributing) if contributing else "No statistical or timeline irregularities identified in current administrative records.",
        "contributing_factors": contributing,
        "benchmark_comparisons": {
            "sector": sec,
            "project_sanction_amount": p.sanction_amount,
            "sector_median_amount": sec_med,
            "sector_cost_deviation_mads": feat["cost_log_ratio_sector"],
            "state": st,
            "state_median_amount": st_med,
            "state_cost_deviation_mads": feat["cost_log_ratio_state"]
        },
        "decision_support_guidance": "Recommended for on-site physical verification" if (rs and rs.fused_risk_score >= 60.0) else "Within nominal statistical distribution bounds.",
        "model_version": model.version,
        "timestamp": datetime.utcnow().isoformat(),
        "disclaimer": "AI-generated risk indicators are analytical decision-support signals and do not constitute proof of fraud, corruption, or irregularity."
    }

@api_router.get("/projects/{project_id}/features")
def get_project_features(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter_by(project_id=project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    model = get_project_risk_model()
    feat = model.extract_single_feature_vector(p)

    return {
        "project_id": project_id,
        "feature_names": model.FEATURE_NAMES,
        "raw_features": {
            "sanction_amount": feat["sanction_amount"],
            "released_amount": feat["released_amount"],
            "expenditure_amount": feat["expenditure_amount"],
            "reported_progress": feat["reported_progress"],
            "elapsed_days": feat["elapsed_days"]
        },
        "normalized_features": {
            "cost_log_ratio_sector": feat["cost_log_ratio_sector"],
            "cost_log_ratio_state": feat["cost_log_ratio_state"],
            "utilization_ratio": feat["utilization_ratio"],
            "release_ratio": feat["release_ratio"],
            "stalled_days_scaled": feat["stalled_days_scaled"],
            "fin_phys_gap": feat["fin_phys_gap"],
            "text_similarity_max": feat["text_similarity_max"],
            "data_completeness_ratio": feat["data_completeness_ratio"]
        },
        "model_version": model.version,
        "timestamp": datetime.utcnow().isoformat()
    }

@api_router.get("/projects/{project_id}/data-quality")
def get_project_data_quality(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter_by(project_id=project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    model = get_project_risk_model()
    completeness, missing_fields = model.compute_data_completeness(p)
    issues = db.query(DataQualityIssue).filter_by(project_id=project_id).all()

    src = p.source
    return {
        "project_id": project_id,
        "provenance": {
            "source_name": src.source_name if src else "Official MoSPI MPLADS Records (ODbL)",
            "source_url": src.source_url if src else None,
            "source_type": src.source_type if src else "GOVERNMENT_PORTAL",
            "verification_status": p.data_availability_status or (src.verification_status if src else "PUBLIC_VERIFIED"),
            "license": src.license if src else "NDSAP / Government Open Data",
            "retrieval_timestamp": src.retrieval_timestamp.isoformat() if (src and src.retrieval_timestamp) else None
        },
        "data_completeness_ratio": completeness,
        "missing_fields": missing_fields,
        "observed_evidence_status": p.observed_progress_status,
        "quality_issues": [{
            "issue_type": issue.issue_type,
            "severity": issue.severity,
            "details": issue.details,
            "original_value": issue.original_value
        } for issue in issues],
        "is_synthetic": p.data_availability_status == "SYNTHETIC",
        "timestamp": datetime.utcnow().isoformat()
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
# ---------------------------------------------------------
# 4. EVIDENCE INGESTION & ARCHIVE
# ---------------------------------------------------------
@api_router.get("/evidence")
def list_all_evidence(
    project_id: Optional[str] = None,
    sector: Optional[str] = None,
    data_status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    q = db.query(ProjectEvidence)
    if project_id:
        q = q.filter(ProjectEvidence.project_id == project_id)
    if data_status:
        if data_status.upper() in ("SYNTHETIC", "PUBLIC_VERIFIED"):
            q = q.filter(ProjectEvidence.project.has(Project.data_status == data_status.upper()))

    evs = q.order_by(desc(ProjectEvidence.timestamp)).limit(limit).all()
    results = []
    for e in evs:
        meta = json.loads(e.metadata_json) if e.metadata_json else {}
        img_url = meta.get("image_url", f"/assets/synthetic/evidence/buildings/{e.file_name}")
        results.append({
            "evidence_id": e.evidence_id,
            "project_id": e.project_id,
            "project_name": e.project.project_name if e.project else "Unknown",
            "sector": e.project.project_type if e.project else "BUILDING",
            "file_name": e.file_name,
            "mime_type": e.mime_type,
            "file_size": e.file_size,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "latitude": e.latitude,
            "longitude": e.longitude,
            "source": e.source,
            "label": meta.get("label", "AI-GENERATED / SYNTHETIC ILLUSTRATION - NOT FIELD EVIDENCE"),
            "is_synthetic": meta.get("is_synthetic", True),
            "stage": meta.get("stage", "Construction"),
            "image_url": img_url,
            "sha256": e.file_hash
        })
    return results

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
# 4B. TAMPER-EVIDENT AUDIT TRAIL
# ---------------------------------------------------------
@api_router.get("/audit-logs")
def list_audit_logs(
    project_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    q = db.query(AuditLog)
    if project_id:
        q = q.filter(AuditLog.project_id == project_id)
    if action:
        q = q.filter(AuditLog.action == action)
    logs = q.order_by(desc(AuditLog.timestamp)).limit(limit).all()
    results = []
    for l in logs:
        detail_txt = l.action
        if l.new_value_json:
            try:
                parsed = json.loads(l.new_value_json)
                detail_txt = parsed.get("event") or parsed.get("message") or parsed.get("file_name") or l.new_value_json
            except Exception:
                detail_txt = l.new_value_json

        results.append({
            "id": l.id,
            "timestamp": l.timestamp.isoformat() if l.timestamp else None,
            "action": l.action,
            "actor": l.user_id,
            "project_id": l.project_id or "GLOBAL",
            "details": detail_txt,
            "ip_address": l.ip_address or "127.0.0.1"
        })
    return results

# ---------------------------------------------------------
# 5. VERIFICATION CASES (HUMAN-IN-THE-LOOP)
# ---------------------------------------------------------
@api_router.get("/verification-cases")
def list_verification_cases(
    case_status: Optional[str] = None,
    priority: Optional[str] = None,
    data_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(VerificationCase)
    if case_status:
        q = q.filter(VerificationCase.case_status == case_status)
    if priority:
        q = q.filter(VerificationCase.priority == priority)
    if data_status and data_status.upper() in ("SYNTHETIC", "PUBLIC_VERIFIED"):
        q = q.filter(VerificationCase.project.has(Project.data_status == data_status.upper()))

    cases = q.order_by(desc(VerificationCase.created_at)).all()

    return [{
        "case_id": c.case_id,
        "project_id": c.project_id,
        "project_name": c.project.project_name if c.project else "Unknown",
        "assigned_officer_id": c.assigned_officer_id or "Unassigned",
        "case_status": c.case_status,
        "priority": c.priority,
        "trigger_reason": c.trigger_reason,
        "recommended_action": c.recommended_action,
        "officer_findings": c.officer_findings,
        "data_status": c.project.data_status if c.project else "SYNTHETIC",
        "created_at": c.created_at.isoformat() if c.created_at else None
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
# 5B. FIELD INSPECTION REQUESTS & APPROVAL WORKFLOW
# ---------------------------------------------------------
@api_router.get("/inspections")
def list_inspection_requests(
    approval_status: Optional[str] = None,
    priority: Optional[str] = None,
    project_id: Optional[str] = None,
    data_status: Optional[str] = None,
    sort_by: str = Query("requested_at"),
    order: str = Query("desc", enum=["asc", "desc"]),
    db: Session = Depends(get_db)
):
    q = db.query(InspectionRequest)
    if approval_status:
        q = q.filter(InspectionRequest.approval_status == approval_status)
    if priority:
        q = q.filter(InspectionRequest.priority == priority)
    if project_id:
        q = q.filter(InspectionRequest.project_id == project_id)
    if data_status and data_status.upper() in ("SYNTHETIC", "PUBLIC_VERIFIED"):
        q = q.filter(InspectionRequest.project.has(Project.data_status == data_status.upper()))

    sort_col = getattr(InspectionRequest, sort_by, InspectionRequest.requested_at)
    if order == "desc":
        q = q.order_by(desc(sort_col))
    else:
        q = q.order_by(sort_col)

    items = q.all()
    return [{
        "request_id": i.request_id,
        "project_id": i.project_id,
        "project_name": i.project.project_name if i.project else "Unknown",
        "inspector_name": i.inspector_name,
        "state": i.state,
        "district": i.district,
        "reason_for_inspection": i.reason_for_inspection,
        "risk_score": i.risk_score,
        "risk_tier": i.risk_tier,
        "contributing_factors": i.contributing_factors_json.split("; ") if i.contributing_factors_json else [],
        "evidence_available": i.evidence_available,
        "evidence_missing": i.evidence_missing,
        "proposed_date": i.proposed_date,
        "priority": i.priority,
        "requested_by": i.requested_by,
        "requested_at": i.requested_at.isoformat() if i.requested_at else None,
        "approving_officer": i.approving_officer,
        "approval_status": i.approval_status,
        "approval_notes": i.approval_notes,
        "resolved_at": i.resolved_at.isoformat() if i.resolved_at else None,
        "advisory": "AI-generated risk indicators are analytical decision-support signals requiring physical inspection authorization."
    } for i in items]

@api_router.post("/inspections")
def create_inspection_request(
    payload: InspectionRequestCreate,
    current_user: User = Depends(require_role(["ADMIN", "OFFICER", "ANALYST"])),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter_by(project_id=payload.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    risk_record = db.query(RiskScore).filter_by(project_id=payload.project_id).first()
    fused_score = risk_record.fused_risk_score if risk_record else (project.fused_risk_score or 0.0)
    risk_tier = risk_record.risk_tier if risk_record else (project.risk_tier or "NORMAL")
    factors = []
    if risk_record and risk_record.contributing_factors_json:
        try:
            factors = json.loads(risk_record.contributing_factors_json)
        except Exception:
            factors = [risk_record.contributing_factors_json]

    req_id = f"INSP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    inspection = InspectionRequest(
        request_id=req_id,
        project_id=payload.project_id,
        inspector_name=payload.inspector_name or current_user.username,
        state=project.state,
        district=project.district,
        reason_for_inspection=payload.reason_for_inspection or f"Elevated analytical risk indicator ({fused_score:.1f}) requiring human-in-the-loop physical audit.",
        risk_score=round(fused_score, 2),
        risk_tier=risk_tier,
        contributing_factors_json="; ".join(factors) if factors else "Statistical deviation in timeline vs expenditure",
        evidence_available=payload.evidence_available or ("Verified MoSPI Records, Geocoded Coordinates" if project.latitude else "MoSPI Administrative Records"),
        evidence_missing=payload.evidence_missing or "Certified physical site inspection photos, completion certificate",
        proposed_date=payload.proposed_date or (datetime.utcnow().strftime('%Y-%m-%d')),
        priority=payload.priority,
        requested_by=current_user.username,
        approving_officer=payload.approving_officer or "Superintending Engineer / Chief Vigilance Officer",
        approval_status="DRAFT"
    )
    db.add(inspection)

    audit = AuditLog(
        user_id=current_user.username,
        action="INSPECTION_REQUEST_CREATED",
        project_id=payload.project_id,
        new_value_json=json.dumps({"request_id": req_id, "priority": payload.priority, "status": "DRAFT"})
    )
    db.add(audit)
    db.commit()

    return {
        "status": "CREATED",
        "request_id": req_id,
        "approval_status": "DRAFT",
        "message": "Field inspection request drafted successfully. Submit to superior officer for authorization."
    }

@api_router.get("/inspections/{request_id}")
def get_inspection_request_detail(request_id: str, db: Session = Depends(get_db)):
    i = db.query(InspectionRequest).filter_by(request_id=request_id).first()
    if not i:
        raise HTTPException(status_code=404, detail="Inspection request not found")

    return {
        "request_id": i.request_id,
        "project_id": i.project_id,
        "project_name": i.project.project_name if i.project else "Unknown",
        "inspector_name": i.inspector_name,
        "state": i.state,
        "district": i.district,
        "reason_for_inspection": i.reason_for_inspection,
        "risk_score": i.risk_score,
        "risk_tier": i.risk_tier,
        "contributing_factors": i.contributing_factors_json.split("; ") if i.contributing_factors_json else [],
        "evidence_available": i.evidence_available,
        "evidence_missing": i.evidence_missing,
        "proposed_date": i.proposed_date,
        "priority": i.priority,
        "requested_by": i.requested_by,
        "requested_at": i.requested_at.isoformat() if i.requested_at else None,
        "approving_officer": i.approving_officer,
        "approval_status": i.approval_status,
        "approval_notes": i.approval_notes,
        "resolved_at": i.resolved_at.isoformat() if i.resolved_at else None,
        "pdf_url": f"/api/v1/inspections/{i.request_id}/pdf",
        "advisory": "AI-generated risk indicators are analytical decision-support signals and do not constitute proof of fraud, corruption, or wrongdoing."
    }

@api_router.patch("/inspections/{request_id}/status")
def update_inspection_status(
    request_id: str,
    payload: InspectionStatusUpdate,
    current_user: User = Depends(require_role(["ADMIN", "OFFICER"])),
    db: Session = Depends(get_db)
):
    valid_statuses = ("DRAFT", "SUBMITTED", "UNDER_REVIEW", "APPROVED", "REJECTED", "COMPLETED")
    if payload.approval_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid approval status. Must be one of: {valid_statuses}")

    i = db.query(InspectionRequest).filter_by(request_id=request_id).first()
    if not i:
        raise HTTPException(status_code=404, detail="Inspection request not found")

    prev_status = i.approval_status
    i.approval_status = payload.approval_status
    if payload.approving_officer:
        i.approving_officer = payload.approving_officer
    if payload.approval_notes:
        i.approval_notes = payload.approval_notes
    if payload.approval_status in ("APPROVED", "REJECTED", "COMPLETED"):
        i.resolved_at = datetime.utcnow()

    audit = AuditLog(
        user_id=current_user.username,
        action="INSPECTION_STATUS_CHANGED",
        project_id=i.project_id,
        previous_value_json=json.dumps({"status": prev_status}),
        new_value_json=json.dumps({"status": i.approval_status, "officer": i.approving_officer, "notes": i.approval_notes})
    )
    db.add(audit)
    db.commit()

    return {
        "request_id": request_id,
        "previous_status": prev_status,
        "approval_status": i.approval_status,
        "approving_officer": i.approving_officer,
        "resolved_at": i.resolved_at.isoformat() if i.resolved_at else None,
        "message": f"Inspection request status updated to {i.approval_status}."
    }

@api_router.get("/inspections/{request_id}/pdf")
def download_inspection_request_pdf(request_id: str, db: Session = Depends(get_db)):
    i = db.query(InspectionRequest).filter_by(request_id=request_id).first()
    if not i:
        raise HTTPException(status_code=404, detail="Inspection request not found")

    pdf_dir = Path("reports/inspections")
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / f"{request_id}_inspection_request.pdf"

    PDFReportGenerator.generate_inspection_request_pdf(i, str(pdf_path))
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"{request_id}_Inspection_Request.pdf"
    )

# ---------------------------------------------------------
# 5C. PROGRESS ESTIMATOR & DRAFT VERIFICATION REPORTS
# ---------------------------------------------------------
@api_router.get("/projects/{project_id}/progress-estimate")
def get_project_progress_estimate(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter_by(project_id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    estimate = ProgressEstimator.estimate(project, project.evidence_items, project.component_states)
    return estimate

@api_router.get("/projects/{project_id}/components", response_model=List[ComponentStateItem])
def get_project_components(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter_by(project_id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    comps = db.query(ProjectComponentState).filter_by(project_id=project_id).all()
    return comps

@api_router.get("/projects/{project_id}/progress-history", response_model=List[ProgressHistoryItem])
def get_project_progress_history(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter_by(project_id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    history = db.query(ProjectProgressHistory).filter_by(project_id=project_id).order_by(ProjectProgressHistory.record_date.asc()).all()
    return history

@api_router.get("/reports/verification-draft/{project_id}")
def get_draft_verification_report(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter_by(project_id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    risk_data = db.query(RiskScore).filter_by(project_id=project_id).first()
    fused_score = risk_data.fused_risk_score if risk_data else (project.fused_risk_score or 0.0)
    risk_tier = risk_data.risk_tier if risk_data else (project.risk_tier or "NORMAL")
    factors = []
    if risk_data and risk_data.contributing_factors_json:
        try:
            factors = json.loads(risk_data.contributing_factors_json)
        except Exception:
            factors = [risk_data.contributing_factors_json]

    rg_eval = RealityGapEngine.evaluate(project)
    estimate = ProgressEstimator.estimate(project, project.evidence_items, project.component_states)

    pdf_dir = Path("reports/draft_reports")
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / f"DRAFT_VERIFICATION_{project_id}.pdf"

    PDFReportGenerator.generate_verification_report_pdf(
        project=project,
        risk_summary={
            "fused_risk_score": fused_score,
            "risk_tier": risk_tier,
            "contributing_factors": factors or ["Analytical divergence in progress velocity relative to capital outlay"]
        },
        output_path=str(pdf_path)
    )

    return {
        "project_id": project.project_id,
        "project_name": project.project_name,
        "jurisdiction": f"{project.district}, {project.state}",
        "report_type": "DRAFT_VERIFICATION_REPORT",
        "analytical_risk_score": round(fused_score, 2),
        "risk_tier": risk_tier,
        "wording_standard": "Potential Anomaly / Analytical Risk Indicator",
        "statutory_classification": "AI-generated analytical output requiring human verification",
        "financial_summary": {
            "sanction_amount": project.sanction_amount,
            "released_amount": project.released_amount,
            "expenditure_amount": project.expenditure_amount,
            "utilization_rate": round(project.expenditure_amount / project.released_amount, 4) if (project.released_amount and project.released_amount > 0) else None
        },
        "progress_tripartite": {
            "expected_progress": estimate["expected_progress"],
            "reported_progress": estimate["reported_progress"],
            "observed_progress": estimate["observed_progress"],
            "observed_status": estimate["observed_status"]
        },
        "key_contributing_factors": factors,
        "evidence_summary": {
            "evidence_count": len(project.evidence_items),
            "status": "EVIDENCE_AVAILABLE" if len(project.evidence_items) > 0 else "EVIDENCE_MISSING"
        },
        "pdf_download_url": f"/api/v1/reports/pdf/{project.project_id}",
        "advisory": "AI-generated risk indicators are decision-support signals and do not constitute proof of fraud, corruption, or wrongdoing."
    }

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
def get_analytics_overview(data_status: Optional[str] = None, db: Session = Depends(get_db)):
    q_proj = db.query(Project)
    q_risk = db.query(RiskScore).join(Project, RiskScore.project_id == Project.project_id)
    if data_status and data_status.upper() in ("SYNTHETIC", "PUBLIC_VERIFIED"):
        q_proj = q_proj.filter(Project.data_status == data_status.upper())
        q_risk = q_risk.filter(Project.data_status == data_status.upper())
    elif not data_status:
        # Default to PUBLIC_VERIFIED for statutory separation
        q_proj = q_proj.filter(Project.data_status == "PUBLIC_VERIFIED")
        q_risk = q_risk.filter(Project.data_status == "PUBLIC_VERIFIED")

    total = q_proj.count()
    monitored = q_risk.count()
    high_risk = q_risk.filter(RiskScore.risk_tier == "HIGH").count()
    critical = q_risk.filter(RiskScore.risk_tier == "CRITICAL").count()
    delayed = q_risk.filter(RiskScore.delay_probability > 0.5).count()
    reality_gaps = q_risk.filter(RiskScore.reality_gap_score > 30.0).count()

    return {
        "total_projects": total,
        "projects_monitored": monitored,
        "high_risk_projects": high_risk,
        "critical_risk_projects": critical,
        "delayed_projects": delayed,
        "active_reality_gaps": reality_gaps,
        "data_status": data_status.upper() if data_status else "PUBLIC_VERIFIED",
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
