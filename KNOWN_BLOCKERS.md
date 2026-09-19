# NIRVANA - Known Blockers & Technical Resolution Matrix

**Project:** National Infrastructure Reality & Verification Network using AI (NIRVANA)  
**Team:** TYRANTS | **Smart India Hackathon:** SIH26102  
**Platform Status:** Resolving via Synthetic Development Architecture  

---

## 1. Feature Status & Resolution Matrix

| Feature | Current Status | Root Cause | Fix Plan | Status |
|---|---|---|---|---|
| **Physical Progress Estimation** | Returns `observed_progress: null` / `NOT_AVAILABLE` for works lacking drone/orthomosaic imagery. | Official MoSPI MPLADS disclosures only provide high-level status and reported progress, omitting site photographs and milestone component breakdowns. | Build a component milestone breakdown generator for 4 infrastructure sectors (Building, Road, Bridge, Water Tank); implement `PhysicalProgressEstimator` that calculates stage completion and returns honest `data_status="SYNTHETIC"` attribution. | **RESOLVED IN SYNTHETIC DEV ARCHITECTURE** |
| **Project-Level Delay Model** | S-curve formula without supervised machine learning model. | Real MPLADS disclosures lack multi-month historical progress logs and intermediate inspection dates needed for supervised regression. | Create time-series progress history (`project_progress_history`) with realistic completion trajectories; train supervised `RandomForest` / `GradientBoosting` delay regressor; report actual MAE/RMSE on test split. | **RESOLVED IN SYNTHETIC DEV ARCHITECTURE** |
| **Project-Level Anomaly Ground Truth** | Unsupervised Isolation Forest; no labeled anomalies to evaluate precision, recall, or confusion matrices. | Public government records publish sanctioned and completed works without investigative vigilance findings or fraud labels. | Generate 5,000 synthetic projects with controlled ground-truth labels across 8 distinct anomaly categories (`PAYMENT_PROGRESS_MISMATCH`, `UNUSUAL_FINANCIAL_PATTERN`, etc.); evaluate classifier performance. | **RESOLVED IN SYNTHETIC DEV ARCHITECTURE** |
| **Real vs. Synthetic Data Separation** | Single database view where 8 synthetic test fixtures existed alongside 3,232 real works without prominent UI mode switching. | Initial application shell displayed combined database records. | Add `data_status` query parameter filtering to backend API endpoints (`?data_status=PUBLIC_VERIFIED` vs `SYNTHETIC`) and implement an explicit top Data Mode Switcher in the UI with a persistent warning banner. | **RESOLVED IN SYNTHETIC DEV ARCHITECTURE** |
| **Document Consistency Verification** | Basic schema without cross-document discrepancy tests. | Government portal does not publish individual work sanction letters or utilization certificate PDFs for public download. | Generate structured synthetic document records (Sanction Orders, Utilization Certificates) with controlled financial and progress inconsistencies for verification engine testing. | **RESOLVED IN SYNTHETIC DEV ARCHITECTURE** |
| **Satellite High-Res Orthomosaic Imagery** | Raster imagery provides 1m-10m optical overview; sub-30cm rebar-level drone feeds unavailable without commercial licensing. | Commercial high-resolution satellites (Maxar/Planet) and DGCA drone surveys require active mission tasking and paid enterprise licenses. | Utilize high-resolution Esri World Imagery with boundary overlays for geospatial context; maintain honest `observed_progress: null` for projects lacking field photographs. | **DOCUMENTED & ARCHITECTED** |

---

## 2. Real Government Data vs. Synthetic Data Boundary Rules

1. **Separation**: Real government records (`data_status = "PUBLIC_VERIFIED"`) and synthetic development records (`data_status = "SYNTHETIC"`, `source_type = "SYNTHETIC_TEST_DATA"`) must remain completely distinguishable in the database and API responses.
2. **UI Transparency**: When viewing synthetic records, the application must display a prominent warning banner:  
   *`"DEVELOPMENT MODE: Viewing Synthetic Evaluation Dataset. Not Government Records."`*
3. **Statutory Language**: Under no circumstances will synthetic anomaly labels be reported as real-world fraud or crime. Standardized wording must remain:  
   *`"Potential Anomaly / Analytical Risk Indicator — Requires Human Verification"`*.
4. **Model Performance**: Metrics computed on synthetic datasets (MAE, RMSE, F1, ROC-AUC) are explicitly tagged:  
   *`"Synthetic development-data evaluation — does not establish real-world predictive accuracy"`*.
