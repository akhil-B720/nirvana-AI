# Model Card: Project Delay Risk Model

## Model Details
- **Model Name:** DelayRiskModel
- **Model Version:** 1.0.0
- **Algorithm:** Interpretable Logistic / Gradient Boosting Baseline with S-Curve Schedule Projections
- **Framework:** scikit-learn 1.8.0, joblib

## Intended Use
- Predict the probability and magnitude of timeline slippage for sanctioned infrastructure works based on elapsed time ratio, current reported progress, and historical sectoral completion curves.

## Features
1. `time_elapsed_ratio` (`elapsed_days / planned_duration_days`)
2. `reported_progress` (%)
3. `schedule_slippage_gap` (`time_elapsed_ratio * 100 - reported_progress`)
4. `financial_progress_alignment` (`utilization_rate - reported_progress/100`)
5. `project_type_encoded`

## Limitations & Biases
- Without historical weather/monsoon disruption data, sudden regional seasonal stalls may be flagged as unexplained delays.
- Where historical completion date labels are incomplete, outputs revert to interpretable mathematical schedule deviation.

## Disclaimer
"AI-generated risk indicators are decision-support signals and do not constitute proof of fraud, corruption, or wrongdoing."
