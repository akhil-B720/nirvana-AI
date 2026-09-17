# Model Card: Cost Anomaly Model

## Model Details
- **Model Name:** CostAnomalyModel
- **Model Version:** 1.0.0
- **Algorithm:** Isolation Forest combined with Sector/Project-Type Median Absolute Deviation (Robust Z-Score)
- **Framework:** scikit-learn 1.8.0, joblib
- **License:** Open Source / MIT

## Intended Use
- **Primary Use:** Identify infrastructure projects where expenditure rates, utilization ratios, or unit costs deviate significantly from historical distributions within the same sector and project type.
- **Appropriate Context:** Decision-support triage for nodal district auditors and vigilance officers.
- **Inappropriate Context:** Automated disciplinary action, legal conviction, or public accusations of fraud without human audit.

## Features
1. `sanction_amount` (INR)
2. `released_amount` (INR)
3. `expenditure_amount` (INR)
4. `utilization_rate` (`expenditure_amount / released_amount`)
5. `release_rate` (`released_amount / sanction_amount`)
6. `cost_per_day` (based on planned duration)
7. `sector_normalized_cost_deviation`

## Limitations & Biases
- If project physical size (e.g. square meters or kilometers of road) is not captured in administrative data, cost-per-unit cannot be computed, leading to possible false alarms for legitimate high-capacity facilities.
- Remote/hilly districts naturally experience higher logistical transportation costs which may shift expenditure benchmarks.

## Disclaimer
"AI-generated risk indicators are decision-support signals and do not constitute proof of fraud, corruption, or wrongdoing."
