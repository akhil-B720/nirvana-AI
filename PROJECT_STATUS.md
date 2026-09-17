# NIRVANA - Project Status Tracker

**National Infrastructure Reality & Verification Network using AI (NIRVANA)**  
**Team:** TYRANTS | **Smart India Hackathon:** SIH26102  
**Last Updated:** 2026-09-17

---

## 1. Status Overview

- **COMPLETED:**
  - **Phase 1: Environment & Runtime Discovery**: Python 3.14.3 verified, Node.js 20.18.0 & npm 10.8.2 portable runtimes set up, core packages installed (`fastapi`, `uvicorn`, `pydantic`, `sqlalchemy`, `alembic`, `pandas`, `numpy`, `scikit-learn`, `joblib`, `pytest`, `PyJWT`, `reportlab`, `httpx`, `bcrypt`, `cryptography`, `pdfplumber`).
  - **Phase 2: Architecture & Policies**: Full specifications in `README.md`, `ARCHITECTURE.md`, `SECURITY.md`, `ETHICS.md`, `LIMITATIONS.md`, `API.md`, `DEPLOYMENT.md`, `docs/DATA_SOURCES.md`, `docs/DATA_DICTIONARY.md`, `docs/ML_PIPELINE.md`, and Model Cards (`MODEL_CARD_COST.md`, `MODEL_CARD_DELAY.md`, `MODEL_CARD_PROGRESS.md`).
  - **Phase 3: Authoritative Data Discovery**: Live network probe of `mplads.gov.in` and `data.gov.in` performed; verified connection timeouts / terms-of-use constraints and documented in `docs/DATA_SOURCES.md`.
  - **Phase 4: Database & Spatially-Aware Persistence**: Complete SQLAlchemy 2.0 ORM schemas for 19 tables (`projects`, `project_financials`, `project_progress`, `project_events`, `project_documents`, `project_evidence`, `project_locations`, `project_anomalies`, `risk_scores`, `model_versions`, `verification_cases`, etc.) with SQLite spatial geodesic fallback and PostGIS production support.
  - **Phase 5 & 6: Ingestion, Validation & Provenance**: `data_pipeline` with `BaseDataSource`, `CSVDataSource`, `MPLADSDataSource`, `DataGovDataSource`, `PDFDataSource`, `DataQualityEngine` (coordinate boundaries, negative values, dates, duplicates), and SHA-256 provenance tracking.
  - **Phase 8 - 13: ML Suite & Reality Gap Engine**:
    - `CostAnomalyModel`: Isolation Forest + Sector Robust Z-Scores (`python -m ml.train.cost_anomaly`).
    - `DelayRiskModel`: Analytical Construction S-Curve and Schedule Slippage (`python -m ml.train.delay_model`).
    - `SimilarityEngine`: TF-IDF Cosine Similarity + Geodesic Haversine Distance (`python -m ml.train.similarity_model`).
    - `RealityGapEngine`: Expected Reality vs Reported Reality vs Observed Reality with prototype score (0-30 NORMAL, 31-60 WATCH, 61-80 HIGH, 81-100 CRITICAL).
    - `RiskFusionEngine`: Multi-signal weighted risk synthesis.
    - `VerificationRecommendationEngine`: Deterministic, traceable recommendations for nodal vigilance officers.
    - Unified inference and evaluation: `python -m ml.evaluate` and `python -m ml.inference`.
  - **Phase 14 & 15: Evidence Ingestion & Document AI**: Multi-part upload with MIME magic-byte validation, SHA-256 hashing, and PDF entity extractor via `pdfplumber`.
  - **Phase 16: Physical Progress Computer Vision Interface**: Architected for YOLO/ResNet structural milestones, marked honestly as `MODEL_NOT_TRAINED` until domain-specific construction image dataset is mounted.
  - **Phase 17: 3D Digital Twin Engine**: Three.js attribute-driven structural twin for Building, Road, Bridge, and Water Tank with milestone progression (0%, 20%, 40%, 60%, 80%, 100% and slider) and plane toggle (Expected, Reported, Observed, Simulation). Never fabricates an observed twin when ground evidence is null.
  - **Phase 18: GIS Mapping**: MapLibre GL JS integration supporting Risk Mode, Reality Gap Mode, and Progress Mode.
  - **Phase 19 & 20: Frontend Application**: Full responsive government command-center dashboard (served directly at `http://localhost:8000/app` and standalone in `frontend/`) featuring live analytics, project registry, GIS map, 3D digital twins, Reality Gap monitor, Model Registry, Grounded AI Assistant, and Field Evidence upload.
  - **Phase 22: Formal Dossier Reports**: ReportLab PDF generator exporting comprehensive verification audit briefs with legal advisory disclaimers.
  - **Phase 23 & 24: Security, RBAC & Audit Trail**: JWT stateless authentication, bcrypt hashing, RBAC dependencies (`ADMIN`, `OFFICER`, `ANALYST`, `VIEWER`), and immutable `audit_logs`.
  - **Phase 26: Automated Testing**: 25 comprehensive automated tests passing with 100% success rate across API, Data Quality, ML models, Reality Gap, and Security.
  - **Phase 28: Containerization**: Complete `docker-compose.yml`, `backend.Dockerfile`, and `frontend.Dockerfile`.

---

## 2. In Progress & Next Steps

- **IN_PROGRESS:**
  - Continuous runtime monitoring and background ingestion daemon.
- **BLOCKED / EXTERNAL DEPENDENCIES:**
  - Automated direct REST streaming from `mplads.gov.in` (Requires government API gateway credentials or official district session login).
  - High-resolution drone/satellite imagery subscription (requires district-level sensor integration).
- **DATA_LIMITATIONS:**
  - Public MPLADS portal does not provide an open unauthenticated bulk JSON API; authenticated CSV/JSON batch pipeline is provided.
  - Supervised fraud classification models are unfeasible due to absence of public judicial conviction datasets; unsupervised anomaly detection (Isolation Forest + robust Z-scores) is strictly used.
  - When field evidence photos are missing, `observed_progress` is set to `null` with status `NOT_AVAILABLE`.
- **TEST_STATUS:**
  - Pytest Suite: **25 PASSED, 0 FAILED** (tests/test_api.py, tests/test_data_quality.py, tests/test_models.py, tests/test_reality_gap.py, tests/test_security.py).
