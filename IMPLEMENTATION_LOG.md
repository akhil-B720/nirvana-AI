# NIRVANA - Implementation Log

**Project:** National Infrastructure Reality & Verification Network using AI (NIRVANA)  
**Team:** TYRANTS | **Smart India Hackathon:** SIH26102  
**Platform Version:** 1.0.0-production-ready  
**Team Leader:** Akhil Bharath Godekari | **Team Member 1:** Rohith Vadra | **Team Member 2:** Kiranmai Janapana  

---

## 1. Environment & Base Infrastructure Setup
- **OS & Runtime Detection:** Identified Windows host with Python 3.14.3 (64-bit). Configured project repository.
- **Node.js & npm Runtime:** Configured Node.js LTS and npm for client builds.
- **Python Dependencies:** Installed required packages: astapi, uvicorn, pydantic, sqlalchemy,  lembic, pandas, 
umpy, scikit-learn, joblib, pytest, PyJWT, 
eportlab, httpx,  crypt, cryptography, pdfplumber.
- **Version Control:** Initialized Git repository, configured comprehensive .gitignore, and established versioned commit history.
- **Configuration Management:** Created .env and .env.example defining secrets, database URIs, JWT expiration, and service endpoints.

---

## 2. Database & Persistence Layer
- **Relational Schema (ackend/models/models.py):**
  - Implemented 19 core tables: projects, project_locations, project_financials, project_events, project_progress, project_evidence, project_documents, project_anomalies, 
isk_scores, model_versions, erification_cases, case_notes, case_evidence_links, data_sources, data_quality_issues, udit_logs, users, system_metrics.
- **Spatial Engine Integration (ackend/core/database.py):**
  - Created dual-mode spatial engine:
    - **PostgreSQL / PostGIS:** Leverages native ST_DWithin and ST_Distance functions.
    - **SQLite Geodesic Fallback:** Implemented custom Haversine trigonometric distance function (haversine_km) registered directly to SQLite connections, enabling spatial proximity and duplicate work detection out-of-the-box without external spatial database daemons.
- **Database Migrations:** Configured Alembic migration environment (migrations/) with env.py and script.py.mako.

---

## 3. Data Pipeline & Real Government Data Ingestion
- **Connectors (data_pipeline/sources/):**
  - BaseDataSource: Abstract base class with SHA-256 hash generation, provenance logging, and performance metrics.
  - CSVDataSource: Flexible CSV reader with autodetection of delimiters (,, ;, \t) and encoding fallbacks (utf-8, latin-1).
  - MPLADSDataSource: Honest interface to MoSPI portal documenting authentication requirements.
  - DataGovDataSource: Connector for Open Government Data (data.gov.in) APIs.
  - PDFDataSource: Document parser extracting monetary figures and sanction dates using pdfplumber.
- **Data Quality Engine (data_pipeline/validators/quality_engine.py):**
  - Deterministic evaluation of data quality across 5 dimensions: project ID integrity, coordinate boundaries ([-90, 90], [-180, 180]), non-negative finances, progress bounds [0, 100], and date sequence coherence.
- **Normalization & Geocoding (data_pipeline/normalizers/normalizer.py):**
  - Normalizes work categories into canonical project types (BUILDING, ROAD, BRIDGE, WATER_TANK, DRAINAGE, COMMUNITY_HALL, OTHER).
  - Implemented _normalize_mospi_export mapping raw MoSPI columns (WORK, ALLOCATION AMOUNT, IDA, RECOMMENDED DATE) to canonical schema.
  - Mapped real Indian state centroids across 33 states/UTs with deterministic micro-jittering for spatial visualization.
- **Ingestion Execution (data_pipeline/run.py):**
  - Ingested 8 synthetic test fixtures (ixtures.csv) tagged as SYNTHETIC.
  - Downloaded genuine 60,359-record MoSPI MPLADS dataset (Vonter/india-mplads-works, ODbL).
  - Ingested 150 real public verified government projects tagged as PUBLIC_VERIFIED.
  - Built synthetic ledger entries (ProjectFinancial) and chronological timelines (ProjectEvent).

---

## 4. Machine Learning & Anomaly Detection Suite
- **Ethical ML Compliance:** Strict adherence to decision-support principles. All model outputs include the mandatory statutory notice:
  > *AI-generated risk indicators are decision-support signals and do not constitute proof of fraud, corruption, or wrongdoing.*
- **Cost Anomaly Model (ml/models/cost_anomaly.py):**
  - Unsupervised dual-engine: Sector-stratified Robust Z-scores (median & MAD) + scikit-learn IsolationForest.
  - Model weights saved to models/cost_anomaly/cost_anomaly.joblib.
- **Delay Risk Model (ml/models/delay_model.py):**
  - Analytical sigmoid S-curve benchmark comparing expected time elapsed against physical completion percentage.
  - Serialized to models/delay/delay_model.joblib.
- **Similarity Engine (ml/models/similarity_model.py):**
  - Dual spatial-semantic deduplication combining TF-IDF cosine similarity on work descriptions with geodesic Haversine distance (default threshold: 5.0 km).
  - Serialized to models/similarity/similarity_model.joblib.
- **Physical Progress Estimator:**
  - Interface defined in docs/MODEL_CARD_PROGRESS.md.
  - Transparently marked as MODEL_NOT_TRAINED with observed_progress = null until ground truth drone/orthomosaic imagery is supplied.
- **Reality Gap Engine (ackend/services/reality_gap.py):**
  - Compares Tripartite Reality: Expected vs Reported vs Observed.
  - Computes 
eality_gap_score and categorizes into NORMAL, WATCH, HIGH, CRITICAL.
- **Risk Fusion Engine (ackend/services/risk_fusion.py):**
  - Synthesizes cost anomaly, delay risk, reality gap, similarity score, and data quality into a unified fused risk score (0-100).
- **ML CLI Runners:**
  - Training: python -m ml.train.cost_anomaly, python -m ml.train.delay_model, python -m ml.train.similarity_model.
  - Evaluation: python -m ml.evaluate.
  - Inference: python -m ml.inference (processed all 158 active database records in <4 seconds).

---

## 5. Backend REST API & Services
- **FastAPI Application (ackend/main.py):**
  - CORS middleware, security headers, request logging, and static asset mounting.
- **REST Endpoints (ackend/api/router.py):**
  - GET /api/v1/health: System status, DB connectivity, model registry count.
  - GET /api/v1/projects: Filter by state, district, type, risk tier, status, and data_status (SYNTHETIC vs PUBLIC_VERIFIED).
  - GET /api/v1/projects/{id}: Detailed view with financials, events, evidence, anomalies, and recommendations.
  - GET /api/v1/risk: Risk summary and breakdown.
  - GET /api/v1/reality-gap: Reality gap distribution and high-discrepancy list.
  - GET /api/v1/digital-twin/{id}: 3D milestone stages, dimensions, and mesh specifications.
  - GET /api/v1/evidence/{id}: Ground truth field evidence list.
  - POST /api/v1/evidence/upload: File upload with MIME magic-byte verification, SHA-256 hashing, and GPS metadata extraction.
  - GET /api/v1/report/{id}/download: ReportLab PDF audit dossier export.
  - GET /api/v1/models: ML registry status, training date, version, and metrics.
  - GET /api/v1/verification-cases: Case management for vigilance officers.
  - GET /api/v1/data/quality: Data quality summary and issue breakdown.
  - POST /api/v1/assistant/query: Grounded AI query answering using DB context.
- **Security & RBAC (ackend/services/auth.py):**
  - JWT generation and verification (HS256).
  - Bcrypt password hashing.
  - Role-based authorization: ADMIN, OFFICER, ANALYST, VIEWER.
- **Audit Logging (ackend/services/audit.py):**
  - Structured audit trail recording every state change, document upload, and user action.

---

## 6. Frontend Command-Center Application
- **Modular React Architecture (rontend/):**
  - React 18, TypeScript, Tailwind CSS, Lucide icons, Three.js 3D viewport, MapLibre GL JS map.
- **Integrated High-Performance SPA (ackend/static/index.html):**
  - Self-contained, zero-compilation build served directly by FastAPI at http://localhost:8000/app (with / redirecting to /app).
  - Real-time map displaying project markers colored by risk tier.
  - Interactive Three.js 3D structural digital twin with stage slider (0% to 100%) and plane toggle (Expected, Reported, Observed).
  - Grounded AI Assistant drawer for natural language queries.
  - Audit dossier PDF generation download trigger.
  - Evidence upload modal with file inspection.
  - Reality Gap monitor with high-contrast discrepancy cards.

---

## 7. Quality Assurance & Testing
- **Test Suite (	ests/):**
  - 	est_api.py: Health endpoint, project listing, detail retrieval, reality gap, 404 handling, PDF report generation (8 tests).
  - 	est_data_quality.py: Coordinate boundary checking, duplicate ID detection, negative amounts, date coherence, score calculation (6 tests).
  - 	est_models.py: Cost anomaly model scoring, delay risk S-curve computation, similarity engine deduplication (3 tests).
  - 	est_reality_gap.py: Reality gap formula correctness, unobserved project handling (2 tests).
  - 	est_security.py: Password hashing, JWT creation & expiration, login success & failure, MIME file validation (6 tests).
- **Execution Results:**
  - Total: **25 passed, 0 failed** in 3.84 seconds.


---

## 8. Macro MPLADS Intelligence System
- **Macro Data Pipeline (`data_pipeline/processors/macro_pipeline.py`):**
  - Ingested 3 authentic MoSPI datasets covering 37 States/UTs over 7 fiscal years (2014-2021): state yearly expenditures, sector distributions, and unspent balances.
  - Validated and persisted 258 macro records in `backend/models/macro_models.py`.
- **Macro Risk & Clustering Analyzer (`ml/models/macro_risk_analyzer.py`):**
  - Unsupervised Isolation Forest anomaly detection combined with KMeans state clustering ($k=3$, Silhouette: 0.2226, PCA 2D: 64.0% variance).
  - Model artifact persisted at `models/macro_risk/macro_risk_model.joblib`.
- **Macro Endpoints (`backend/api/macro_router.py`):**
  - `/api/v1/macro/states`, `/api/v1/macro/states/{name}`, `/api/v1/macro/risk-analysis`, `/api/v1/macro/audit-logs`.
- **Test Suite (`tests/test_macro_pipeline.py`):**
  - 7 automated tests covering ingestion, clustering, PCA, state lookups, and API endpoints (100% pass rate).

---

## 9. Project-Level MPLADS Risk Intelligence System
- **Authentic Stratified Ingestion (`data_pipeline/run.py` & `data_pipeline/sources/csv_source.py`):**
  - Ingested 3,232 authentic MoSPI government works from `dataset/raw/real_mplads_works.csv` across all States/UTs.
  - Stratified across all 1,503 Completed, 629 Ongoing, 1,000 Sanctioned, and 100 Unsanctioned works.
  - Tagged with `PUBLIC_VERIFIED` provenance and tracked in `data_sources` table. Total active database projects: 3,240.
  - Initialized relational financial ledgers (`ProjectFinancial`) and chronological event timelines (`ProjectEvent`).
- **Project-Level ML Anomaly Model (`ml/models/project_risk_model.py`):**
  - Built `ProjectRiskModel` with 8-dimensional normalized feature matrix:
    1. `cost_log_ratio_sector`: Log-cost deviation relative to sector median.
    2. `cost_log_ratio_state`: Log-cost deviation relative to state median.
    3. `utilization_ratio`: Fund expenditure relative to releases.
    4. `release_ratio`: Fund release relative to sanctioned budget.
    5. `stalled_days_scaled`: Elapsed days since recommendation for stalled low-progress projects.
    6. `fin_phys_gap`: Financial vs reported progress misalignment percentage.
    7. `text_similarity_max`: TF-IDF duplicate similarity within administrative jurisdiction.
    8. `data_completeness_ratio`: Proportion of non-null administrative fields.
  - Unsupervised `IsolationForest` (150 trees, 10% contamination) trained on 3,390 projects (global median sanction: ₹400,000).
  - Dynamic `risk_score` (0-100), `risk_level` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), `confidence` (0.0-1.0), and plain-English `contributing_factors`.
  - Serialized model artifact to `models/project_risk/project_risk_model.joblib` and registered in `model_versions` table.
- **Batch Inference & Anomaly Persistence (`ml/inference.py`):**
  - Executed inference across all active projects, generating calibrated risk scores and persisting 1,578 active analytical anomalies in `project_anomalies` table.
- **Dedicated Project REST Endpoints (`backend/api/router.py`):**
  - `GET /api/v1/projects/{id}/risk`: Full standardized payload with risk score, tier, confidence, factors, features, version, source, timestamp.
  - `GET /api/v1/projects/{id}/anomalies`: Active anomaly breakdown and severity tags.
  - `GET /api/v1/projects/{id}/explanation`: Plain-English summary and sector/state median benchmarks.
  - `GET /api/v1/projects/{id}/features`: Raw and normalized feature vectors.
  - `GET /api/v1/projects/{id}/data-quality`: Provenance, field completeness ratio, missing field tags, quality issues.
- **Frontend Dashboard Integration (`backend/static/index.html`):**
  - Integrated Project-Level Risk Intelligence card displaying real-time empirical risk score, confidence gauge, data completeness, and contributing factor bullet points.
- **Automated Tests (`tests/test_project_risk.py`):**
  - 8 new tests verifying feature extraction, bounds, prediction consistency, all 5 endpoints, and 404 responses.
  - **Full Test Suite Status:** **41 passed, 0 failed** across all 8 test files.

---

## 10. Explainable Macro Financial Risk Intelligence Upgrade
- **Explainable ML Engine Upgrade (`ml/models/macro_risk_analyzer.py`):**
  - Calibrated and persisted empirical national baselines (means, medians, standard deviations, and median absolute deviations) for all 10 macro features during `fit()`.
  - Added `explain_state_risk(state_name, metrics)` calculating feature deviations, risk contributions (`HIGH`, `MEDIUM`, `LOW`), dynamic `why_flagged` contextual narratives, and human-in-the-loop verification recommendations.
  - Retrained and serialized model to `models/macro_risk/macro_risk_model.joblib`.
- **State Dossier API Upgrade (`backend/api/macro_router.py`):**
  - Upgraded `GET /api/v1/macro/states/{state}` to return comprehensive State Dossier payload:
    - `state_overview`: `analytical_risk_indicator` (0-100), `risk_tier`, `risk_cluster_name`, `model_confidence`, `data_quality_status`.
    - `financials`: Audited 4-year cumulative figures, cost per work, backlog absorption, volatility CV, trend, and honest `released_amount: null` labeled `"NOT AVAILABLE"`.
    - `money_flow`: Flow diagram data structure tracing Released Funds (`NOT AVAILABLE`) -> Expenditure -> Completed Works, and separate Unspent Balance.
    - `financial_ratios`: Explicit status (`NOT AVAILABLE` vs `COMPUTED`), formulas, and explanation reasons.
    - `feature_baseline_comparisons`: 10-feature comparison table (State Value vs Model Baseline vs Deviation vs Risk Contribution).
    - `anomaly_explanation`: Dynamic `why_flagged` points and synthesis narrative.
    - `yearly_performance`: 4-year time series with yearly costs and YoY changes.
    - `sector_distribution`: 6-sector infrastructure percentage breakdown.
    - `verification_recommendations`: Actionable audit recommendations.
    - `source_provenance`: MoSPI attribution, ingested filenames, retrieval timestamps, verification status.
    - `data_limitations`: Clear demarcation between observed disclosures and model analytics.
- **Frontend State Macro Intelligence Interface (`backend/static/index.html`):**
  - Added dedicated navigation tab `State Macro Intelligence`.
  - Implemented National Macro KPI Summary cards (Unspent Balance, 4-Yr Expenditure, Backlog Absorption, Entity count, Bottlenecks).
  - Integrated State Selector dropdown and quick-select pills for major States/UTs.
  - Built full Explainable State Dossier view:
    - Prominent `Analytical Risk Indicator: [Score]` banner with colored tier and confidence badges.
    - Dynamic *"Why is this state flagged?"* callout box.
    - Financial Intelligence Panel with explicit `OBSERVED DATA` vs `MODEL-DERIVED ANALYSIS` labels.
    - Fiscal Liquidity Flow diagram and Financial Ratios table.
    - Interactive Financial Trend Chart powered by Chart.js with toggle buttons: `Expenditure (₹ Cr)` | `Completed Works` | `Cost per Work (₹ Lakhs)` and tooltips.
    - 10-feature Model Baseline Deviation table with risk contribution badges.
    - Sectoral expenditure distribution progress bars.
    - Verification recommendations and provenance / limitations sections.
    - Comparative 37 States/UTs ranking table with multi-criteria sorting.
- **Automated Tests (`tests/test_macro_dossier.py`):**
  - Added 7 comprehensive tests covering dossier schema, financial intelligence math, missing released amount handling, baseline deviations, explanations, provenance, and 404 responses.
  - **Full Test Suite Status:** **48 passed, 0 failed (100% pass rate)** in ~7.5 seconds.

