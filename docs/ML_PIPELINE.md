# NIRVANA - Machine Learning Pipeline Architecture

**Framework:** scikit-learn, joblib, NumPy, Pandas  
**Policy:** Zero Hallucination. When ground truth is unavailable or sample size is insufficient, output `INSUFFICIENT_DATA` or `MODEL_NOT_TRAINED`. Strictly designate outputs as **"Potential Anomaly / Analytical Risk Indicator"**.

---

## 1. Dual-Tier Intelligence Architecture

```text
========================================================================
LEVEL 1: MACRO MPLADS RISK INTELLIGENCE (State & UT Aggregates)
========================================================================
MoSPI Macro Data (Expenditure, Works, Sector Distributions, Unspent Balances)
       ↓
Feature Normalization (7-year trend, completion velocity, sector concentration)
       ↓
MacroRiskAnalyzer:
   ├─ Isolation Forest Anomaly Scoring (Identifies structural state outliers)
   └─ KMeans Clustering (k=3, Silhouette: 0.2226, PCA 2D: 64.0% variance)
       ↓
Macro API: /api/v1/macro/states, /risk-analysis, /audit-logs

========================================================================
LEVEL 2: PROJECT-LEVEL RISK INTELLIGENCE (Individual Capital Works)
========================================================================
Authentic MoSPI Works Archive (60,359 works → 3,232 stratified active projects)
       ↓
Data Quality Engine (Schema validation, coordinate bounding, date sequence)
       ↓
Feature Engineering (8-Dimensional Normalized Vector):
   ├─ 1. cost_log_ratio_sector: Deviation from sector median cost
   ├─ 2. cost_log_ratio_state: Deviation from state median cost
   ├─ 3. utilization_ratio: Expended funds vs released funds
   ├─ 4. release_ratio: Released funds vs sanctioned allocation
   ├─ 5. stalled_days_scaled: Elapsed timeline on low-progress projects
   ├─ 6. fin_phys_gap: Financial vs reported physical progress divergence
   ├─ 7. text_similarity_max: TF-IDF cosine duplicate score in same jurisdiction
   └─ 8. data_completeness_ratio: Proportion of non-null administrative fields
       ↓
ProjectRiskModel:
   ├─ Isolation Forest (150 trees, 10% contamination)
   ├─ Domain Rules Fusion (Maximum & average anomaly sub-scores)
   └─ Confidence Calibration (Function of record completeness & field evidence)
       ↓
Project Endpoints:
   ├─ GET /api/v1/projects/{id}/risk
   ├─ GET /api/v1/projects/{id}/anomalies
   ├─ GET /api/v1/projects/{id}/explanation
   ├─ GET /api/v1/projects/{id}/features
   └─ GET /api/v1/projects/{id}/data-quality
```

---

## 2. Integrity & Ethical Guarantees

1. **Missing Data Policy**: If a feature is unavailable (e.g. `observed_progress` is null because no field photo exists), the pipeline does NOT impute zero or assume completion. `observed_progress_status = NOT_AVAILABLE` is explicitly flagged and confidence is calibrated downward.
2. **Deterministic Baseline**: If labelled supervised data is missing, we use statistical anomaly baselines rather than manufacturing fake weights or synthetic training metrics.
3. **Traceability**: Every output stores the active model version, parameters, raw feature inputs, and confidence score.
4. **Mandatory Disclaimer**: All outputs carry:
   > "AI-generated risk indicators are analytical decision-support signals and do not constitute proof of fraud, corruption, or irregularity."
