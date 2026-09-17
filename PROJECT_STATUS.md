# NIRVANA - Project Status Tracker

**National Infrastructure Reality & Verification Network using AI (NIRVANA)**  
**Team:** TYRANTS | **Smart India Hackathon:** SIH26102  
**Last Updated:** 2026-09-17  
**Platform Status:** Operational, runnable end-to-end, verified with real government data.

---

## 1. Executive Summary & Verification Metrics

| Category | Metric | Status | Details |
|---|---|---|---|
| **Python Environment** | Python 3.14.3 (64-bit) | VERIFIED | Core backend, ML, and API packages installed |
| **Node.js Environment** | Node v20.18.0 / npm 10.8.2 | VERIFIED | Installed in tools directory |
| **Relational Database** | SQLite (with PostGIS/Haversine support) | VERIFIED | 19 relational tables, custom Haversine distance UDF |
| **Total Active Projects** | 3,240 Projects in DB | VERIFIED | 8 Synthetic Fixtures + 3,232 Stratified MoSPI Government Works |
| **Macro State/UT Records** | 258 Records in DB | VERIFIED | 37 States & UTs across 7 fiscal years (2014-2021) |
| **Data Quality Score** | 100.0% | VERIFIED | 0 critical schema or boundary violations |
| **Automated Tests** | 48 Passed / 0 Failed | VERIFIED | 100% test pass rate across 9 test suites |
| **ML Models Serialized** | 4 Production Models | VERIFIED | ProjectRiskModel, MacroRiskAnalyzer (Explainable), DelayRiskModel, SimilarityEngine |
| **Physical Progress CV** | MODEL_NOT_TRAINED | VERIFIED | Honest interface: observed_progress = null when field evidence is absent |
| **Frontend Application** | Mounted on /app | VERIFIED | Three.js 3D twins, MapLibre GIS, Explainable State Macro Intelligence, AI assistant |
| **Report Generation** | ReportLab PDF Engine | VERIFIED | Downloadable confidential decision-support dossiers |

---

## 2. Ingested Data Provenance

1. **Synthetic Test Fixtures (8 Projects):**
   - Source: `dataset/synthetic/fixtures.csv`
   - Data Availability Status: `SYNTHETIC`
   - Purpose: Extreme edge-case calibration for high reality gaps, duplicate works, and cost overruns.
2. **Authentic MoSPI MPLADS Records (3,232 Projects Active / 60,359 Downloaded):**
   - Source: `dataset/raw/real_mplads_works.csv` (ODbL open data from official MoSPI portal `http://164.100.68.116/mpladssbi/Default.aspx`)
   - Stratified Coverage: 1,503 Completed, 629 Ongoing, 1,000 Sanctioned, 100 Unsanctioned works across all 37 Indian States and UTs.
   - Data Availability Status: `PUBLIC_VERIFIED`
   - SHA-256 Checksum: `aa1d0b7c9c6bbe014a1af772a22ab3dc0a6eb24d043695060abaa0f94333e413`
3. **Macro State-Level MoSPI MPLADS Datasets (258 Records across 37 States/UTs):**
   - State yearly expenditure and works: `dataset/raw/mplads_state_yearly_expenditure_and_works.csv`
   - State sector distribution: `dataset/raw/mplads_state_sector_distribution.csv`
   - State unspent balance: `dataset/raw/mplads_state_unspent_balance.csv`

---

## 3. Operational Machine Learning Suite

### A. Project-Level Risk Intelligence Model (`ProjectRiskModel`)
- **Algorithm:** Isolation Forest (150 trees, 10% contamination) + Robust Sector/State MAD + S-Curve Schedule Momentum + TF-IDF Title Similarity.
- **Weights:** `models/project_risk/project_risk_model.joblib`.
- **Training Population:** 3,390 projects (global median sanction: ₹400,000).
- **Outputs:** Dynamic `risk_score` (0-100), `risk_level` (`LOW`/`MEDIUM`/`HIGH`/`CRITICAL`), `confidence` (0.0-1.0), and plain-English `contributing_factors`.
- **Dedicated Endpoints:**
  - `GET /api/v1/projects/{id}/risk`
  - `GET /api/v1/projects/{id}/anomalies`
  - `GET /api/v1/projects/{id}/explanation`
  - `GET /api/v1/projects/{id}/features`
  - `GET /api/v1/projects/{id}/data-quality`

### B. Explainable Macro MPLADS Risk Intelligence Analyzer (`MacroRiskAnalyzer`)
- **Algorithm:** Isolation Forest + KMeans Clustering (k=3, Silhouette: 0.2226, PCA 2D: 64.0% variance) + Empirical National Baseline Deviation Engine.
- **Weights:** `models/macro_risk/macro_risk_model.joblib`.
- **Coverage:** 37 State/UT entities across 4 fiscal years (FY 2016-17 to FY 2019-20).
- **Explainability Engine:**
  - Dynamic `why_flagged` contextual narratives derived from statistical deviations (e.g. ₹665.58 Cr unspent vs national median of ₹71.34 Cr).
  - 10 Empirical feature baseline comparisons (Actual vs Median Baseline vs Deviation vs Risk Contribution).
  - Explicit distinction between **OBSERVED DATA** and **MODEL-DERIVED ANALYSIS**.
  - Honest data handling: `released_amount: null` labeled `"NOT AVAILABLE"` (ratios depending on missing releases marked `"NOT AVAILABLE"`).
- **Dedicated Endpoints:**
  - `GET /api/v1/macro/states` (list & sort by risk, unspent balance, backlog, expenditure)
  - `GET /api/v1/macro/states/{name}` (comprehensive Explainable State Dossier)
  - `GET /api/v1/macro/risk-analysis` (national KPIs, bottlenecks, cluster breakdown)
  - `GET /api/v1/macro/audit-logs`

### C. Auxiliary Models
- **Delay Risk Model:** Non-linear Sigmoid Construction S-Curve (`models/delay/delay_model.joblib`).
- **Similarity Engine:** TF-IDF Textual Vectorization + Geodesic Haversine Proximity (`models/similarity/similarity_model.joblib`).
- **Physical Progress Estimator:** Transparently marked `MODEL_NOT_TRAINED` with `observed_progress = null`.
- **Reality Gap Engine:** Tripartite Reality evaluation: Expected vs Reported vs Observed Progress.

---

## 4. Automated Test Suite Summary

Executed via `python -m pytest`:
- `tests/test_macro_dossier.py`: **7 PASSED** (Dossier structure, Financial intelligence calculations, Money flow & NOT AVAILABLE handling, Baseline comparisons, Anomaly explanations, Provenance, 404 handling).
- `tests/test_api.py`: **8 PASSED** (Health, Projects List, Project Detail, Reality Gap, 404 Handling, PDF Report Export).
- `tests/test_project_risk.py`: **8 PASSED** (Feature extraction, Model prediction bounds, 5 Dedicated project endpoints, 404 handling).
- `tests/test_macro_pipeline.py`: **7 PASSED** (Macro pipeline, DB ingestion, Anomaly analyzer, Clustering, State lookup, Risk API).
- `tests/test_data_quality.py`: **6 PASSED** (Boundaries, Negatives, Dates, Duplicates, Quality Scoring).
- `tests/test_security.py`: **6 PASSED** (Password Hashing, JWT Tokens, Auth Login, File Magic-Byte Validation).
- `tests/test_models.py`: **3 PASSED** (Cost Anomaly, Delay Risk, Similarity Engine).
- `tests/test_reality_gap.py`: **2 PASSED** (Reality Gap Calculation, Null Observation Handling).
- `tests/test_empowered_indian.py`: **1 PASSED** (Provenance and normalization of third-party sources).

Total: **48 Passed, 0 Failed (100% Pass Rate)** in ~7.5 seconds.

---

## 5. Mandatory Ethical Compliance Notice

All outputs, APIs, reports, and UI screens bear the statutory decision-support notice:
> **Notice:** AI-generated risk indicators are decision-support signals and do not constitute proof of fraud, corruption, or wrongdoing.
