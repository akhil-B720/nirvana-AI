# NIRVANA - API Specification & Endpoint Documentation

Base URL: `http://localhost:8000/api/v1`

## Authentication
All secured endpoints expect header:
`Authorization: Bearer <jwt_token>`

Roles: `ADMIN`, `OFFICER`, `ANALYST`, `VIEWER`

---

## 1. System & Health
- `GET /health`: System health check, database status, active ML model versions.
- `GET /data/sources`: Ingested data sources and provenance records.
- `GET /data/quality`: Data quality audit metrics (missing coords, negative numbers, date order issues).
- `POST /data/refresh`: Trigger pipeline normalization and feature re-computation.

---

## 2. Projects & Verification
- `GET /projects`: Paginated project list with filtering by state, district, sector, risk tier, status.
- `GET /projects/{id}`: Detailed project profile with financials, provenance, and latest risk status.
- `GET /projects/{id}/risk`: Fused risk assessment, individual signal breakdowns, and model versions.
- `GET /projects/{id}/reality-gap`: Expected vs Reported vs Observed comparison, confidence, and gaps.
- `GET /projects/{id}/digital-twin`: Component-level structural state for 3D rendering (Building, Road, Bridge, Water Tank).
- `GET /projects/{id}/evidence`: Geotagged media and inspection records.
- `POST /evidence/upload`: Multi-part secure evidence upload (JPEG/PNG/PDF) with EXIF & SHA-256 validation.
- `GET /projects/{id}/timeline`: Historical milestone event series (Time Machine).
- `GET /projects/{id}/recommendations`: Traceable verification actions generated for vigilance officers.
- `GET /projects/{id}/report`: Downloadable PDF verification brief generated via ReportLab.

---

## 3. Machine Learning & Verification Cases
- `GET /models`: List active ML models, versions, algorithms, and training metadata.
- `GET /models/{id}`: Deep inspection of specific model card, features, and parameter weights.
- `GET /models/{id}/metrics`: Evaluated metrics (or honest `INSUFFICIENT_DATA` flag).
- `GET /verification-cases`: Case management list for field inspection actions.
- `POST /verification-cases`: Create an inspection escalation case.
- `PATCH /verification-cases/{id}`: Update officer findings and close case.
- `GET /analytics/overview`: High-level command-center metrics and choropleth summary.
- `POST /assistant/query`: Grounded project intelligence Q&A (retrieval-only, zero hallucination).
