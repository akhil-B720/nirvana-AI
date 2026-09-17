# NIRVANA - Machine Learning Pipeline Architecture

**Framework:** scikit-learn, joblib, numpy, pandas  
**Policy:** Zero Hallucination. When ground truth is unavailable or sample size is insufficient, output `INSUFFICIENT_DATA` or `MODEL_NOT_TRAINED`.

---

## 1. Pipeline Flow

```text
Raw Ingested Data
       ↓
Data Quality Engine (Checks: coords, date coherence, non-negative amounts, bounds)
       ↓
Clean Normalized Dataset (dataset/processed/)
       ↓
Feature Engineering (Financial utilization, time elapsed, regional deviation, cost percentiles)
       ↓
ML Models / Detectors:
   ├─ 1. Cost Anomaly Model (IsolationForest + Regional Robust Z-score)
   ├─ 2. Delay Model (Historical completion regression / classification baseline)
   ├─ 3. Similarity Engine (TF-IDF + Cosine Distance + Haversine Geodesic Distance)
   ├─ 4. Physical Progress Estimator (Vision Architecture Interface: YOLO/ResNet)
   └─ 5. Reality Gap Engine (Expected vs Reported vs Observed Progress)
       ↓
Risk Fusion Engine (Configurable multi-signal weighted synthesis)
       ↓
Explainability Layer (Feature contributions, actual values, natural language narrative)
       ↓
Verification Recommender (Deterministic traceable rules triggered by anomaly vectors)
       ↓
Model Registry & Drift Monitoring (Feature distribution tracking, Kolmogorov-Smirnov / PSI)
```

---

## 2. Integrity Guarantees

1. **Missing Data Policy**: If a feature is unavailable (e.g. `observed_progress` is null because no field photo exists), the pipeline does NOT impute zero or assume completion. The weight for that missing dimension is redistributed dynamically, and `observed_progress_status = NOT_AVAILABLE` is explicitly flagged.
2. **Deterministic Baseline**: If labelled supervised data is missing, we use statistical anomaly baselines rather than manufacturing fake weights or synthetic training metrics.
3. **Traceability**: Every output stores the active model version, parameters, raw feature inputs, and confidence score.
