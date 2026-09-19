# Model Benchmark Card: Project-Level Analytical Anomaly Detection

## 1. Benchmark Overview
- **Benchmark Name:** Project-Level Analytical Anomaly Detection Synthetic Evaluation
- **Evaluation Engine:** `ProjectRiskModel` (Fused Isolation Forest 150 Trees + Robust Sector/State MAD + S-Curve Deficit + Text Similarity)
- **Evaluation Dataset:** `dataset/synthetic/synthetic_projects.csv` (5,000 records)
- **Artifact Report:** `ml/reports/synthetic_anomaly_evaluation.json`
- **Execution Date:** 2026-09-19

## 2. Evaluation Methodology
- **Ground Truth Labels:** Injected controlled mathematical anomalies across 7 anomaly categories (`anomaly_label = 1`) and realistic baseline projects (`anomaly_label = 0`).
- **Decision Threshold:** Analytical Risk Score $\ge 50.0$ flagged as potential anomaly.
- **Sample Distribution:**
  - Normal baseline works: **4,250 projects (85.0%)**
  - Controlled anomaly works: **750 projects (15.0%)**
  - Total benchmark population: **5,000 projects**

## 3. Benchmark Metrics
> [!WARNING]
> **Synthetic Development-Data Evaluation Only:**
> These evaluation metrics were measured exclusively on synthetic development datasets with injected anomalies. They reflect synthetic detection performance and do NOT represent real-world government audit precision, false-positive rates, or judicial fraud evidence.

| Metric | Measured Value | Meaning |
| :--- | :--- | :--- |
| **ROC-AUC** | **1.000** | Area under the Receiver Operating Characteristic curve |
| **Precision** | **1.000 (100.0%)** | Fraction of flagged projects that correspond to injected anomalies |
| **Recall** | **1.000 (100.0%)** | Fraction of injected anomalies successfully flagged |
| **F1-Score** | **1.000** | Harmonic mean of Precision and Recall |
| **True Positives (TP)** | **750** | Correctly identified anomaly projects |
| **False Positives (FP)** | **0** | Normal projects incorrectly flagged |
| **True Negatives (TN)** | **4,250** | Normal projects correctly recognized as normal |
| **False Negatives (FN)** | **0** | Injected anomalies missed |

## 4. Detection Rates by Injected Anomaly Category
| Anomaly Category | Injected Count | Detected Count | Detection Rate | Typical Analytical Signal |
| :--- | :--- | :--- | :--- | :--- |
| `UNUSUAL_FINANCIAL_PATTERN` | 107 | 107 | **100.0%** | Overdraft beyond release / 95% unspent after 2 years |
| `PAYMENT_PROGRESS_MISMATCH` | 110 | 110 | **100.0%** | Expenditure near 100% of release with low progress |
| `DELAY_PATTERN` | 90 | 90 | **100.0%** | Ongoing work sanctioned >3 years ago with low completion |
| `LOCATION_INCONSISTENCY` | 94 | 94 | **100.0%** | Spatial divergence outside state/district administrative bounding box |
| `POTENTIAL_SIMILARITY` | 116 | 116 | **100.0%** | Exact title/scope duplication within same block/district |
| `DOCUMENT_INCONSISTENCY` | 123 | 123 | **100.0%** | Financial discrepancy between sanction orders and utilization claims |
| `REALITY_GAP` | 110 | 110 | **100.0%** | Divergence between self-reported administrative progress and physical observations |
| `NORMAL` (Baseline Control) | 4,250 | 4,250 | **100.0% Specificity** | All normal works correctly unflagged |

## 5. Statutory Compliance & Zero-Hallucination Guardrails
- **Decision Support Semantics:** All outputs use standardized terminology: *"Potential Anomaly / Analytical Risk Indicator"*.
- **No Judicial Accusations:** Indicators are explicitly defined as administrative prioritization signals requiring human verification.
- **Provenance Isolation:** Real government records (3,390 projects) are strictly isolated from synthetic development data.
