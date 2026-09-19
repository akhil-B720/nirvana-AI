# Model Card: NIRVANA Supervised Delay Risk Model (v2.0.0)

## 1. Model Details
- **Model Name:** Supervised Delay Risk Model (`DelayRiskModel`)
- **Version:** 2.0.0
- **Type:** Ensemble Learning — Supervised Gradient Boosting Regressor (Delay Days) + Supervised Gradient Boosting Classifier (Delay Probability)
- **Framework:** scikit-learn
- **Serialized Artifact:** `models/delay/delay_model.joblib`
- **Registered Model ID:** `delay_model_v2`
- **Fallback Heuristic:** Calibrated Logistical Construction S-Curve Rate Projection

## 2. Intended Use & Context
- **Primary Objective:** Provide nodal and vigilance officers with data-driven predictive estimates of project completion slippage and delay likelihood based on elapsed time ratio, progress velocity, and capital utilization.
- **Evaluation Dataset:** Trained on multi-month project trajectory snapshots from the synthetic development benchmark (`synthetic_projects.csv` and `synthetic_progress_history.csv`).
- **Classification of Output:** Decision-support analytical signal. Predictive estimates highlight risk of delay and do NOT represent contractual fault or administrative malfeasance.

## 3. Features & Inputs (7-Dimensional Vector)
| Feature Name | Type | Description |
| :--- | :--- | :--- |
| `planned_days` | Float | Scheduled duration between sanction/commencement and target completion |
| `elapsed_days` | Float | Days elapsed from start date to current reference audit date |
| `time_ratio` | Float | Ratio of elapsed days to planned duration (`elapsed / planned`) |
| `reported_progress` | Float | Claimed administrative physical progress percentage (0-100) |
| `utilization_ratio` | Float | Cumulative expenditure divided by sanctioned capital allocation |
| `progress_velocity` | Float | Daily progress burn rate (`reported_progress / elapsed_days`) |
| `progress_deficit` | Float | Difference between expected S-curve progress and reported progress |

## 4. Training & Evaluation Metrics
> [!IMPORTANT]
> **Evaluation Dataset:** Synthetic Development Dataset (5,000 projects; 4,000 train / 1,000 test hold-out split).
> These metrics reflect performance on mathematically modeled synthetic timelines and must never be represented as real-world government project accuracy.

| Metric | Hold-out Test Set Value | Evaluation Scope |
| :--- | :--- | :--- |
| **Regression MAE** | **7.59 days** | Mean Absolute Error in predicted delay days |
| **Regression RMSE** | **14.44 days** | Root Mean Squared Error in predicted delay days |
| **Regression $R^2$** | **0.999** | Coefficient of Determination on test trajectories |
| **Classification Accuracy** | **1.000 (100.0%)** | Accuracy in separating delayed vs on-time projects |
| **Classification ROC-AUC** | **1.000** | Area under ROC curve for delay probability |
| **Test Sample Size** | **1,000 projects** | 20% hold-out evaluation sample |

## 5. Ethical & Legal Considerations
- **Statutory Notice:** AI delay predictions are advisory signals for administrative prioritization.
- **Data Boundary:** When evaluated on synthetic projects, results are explicitly flagged `data_status: "SYNTHETIC"`.
