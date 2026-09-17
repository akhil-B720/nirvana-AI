# Model Card: Project-Level MPLADS Risk Intelligence Model

## Model Details
- **Model Name:** ProjectRiskModel
- **Model Version:** 1.0.0
- **Algorithm:** Unsupervised Isolation Forest (150 estimators, 10% contamination) augmented with robust Sector & State Median Absolute Deviation (MAD), schedule stall momentum, financial-to-progress misalignment, and TF-IDF duplicate similarity.
- **Framework:** scikit-learn 1.8+, joblib, NumPy, Pandas
- **Training Data:** 3,390 active government project records stratified from MoSPI portal open data archive (`dataset/raw/real_mplads_works.csv`), covering Completed, Ongoing, and Sanctioned works across all Indian States and Union Territories.
- **License:** Open Source (NIRVANA Project / SIH26102)

## Intended Use
- **Primary Purpose:** Provide objective, empirical, decision-support risk intelligence on individual MPLADS projects to assist district collectors, vigilance authorities, and auditors in prioritizing inspections.
- **Output Labels:** Strictly designated as **"Potential Anomaly / Analytical Risk Indicator"**.
- **Appropriate Context:** Automated audit queue prioritization, early detection of stalled capital allocations, flagging potential duplicate work sanctions in the same administrative block.
- **Inappropriate Context:** Defamation, disciplinary actions, legal prosecutions, or automated contractor blacklisting without independent field verification and human audit.

## Input Features
The model operates on an 8-dimensional normalized analytical vector:
1. `cost_log_ratio_sector`: Log-cost deviation relative to sector median: $rac{\log_{10}(	ext{cost}) - 	ext{median}(\log_{10}(	ext{sector}))}{	ext{MAD}(\log_{10}(	ext{sector}))}$.
2. `cost_log_ratio_state`: Log-cost deviation relative to state-level median.
3. `utilization_ratio`: Ratio of expended funds to released budget ($	ext{expenditure} / 	ext{released}$).
4. `release_ratio`: Ratio of released funds to total sanctioned allocation ($	ext{released} / 	ext{sanction}$).
5. `stalled_days_scaled`: Elapsed timeline duration since sanction date for works with sub-nominal physical progress ($< 30\%$).
6. `fin_phys_gap`: Absolute discrepancy percentage between fund expenditure ratio and contractor-claimed physical progress.
7. `text_similarity_max`: Maximum TF-IDF n-gram cosine similarity between work description and other sanctioned projects within the same administrative block or district.
8. `data_completeness_ratio`: Ratio of observed non-null administrative and milestone fields, used to calibrate confidence.

## Scoring & Calibration
- **Empirical Risk Score:** $0.0$ to $100.0$ continuous scale.
- **Risk Tiers:**
  - `LOW`: $0.0 \le 	ext{score} < 30.0$ (Nominal statistical bounds).
  - `MEDIUM`: $30.0 \le 	ext{score} < 60.0$ (Moderate timeline or budget divergence).
  - `HIGH`: $60.0 \le 	ext{score} < 80.0$ (Significant multi-factor anomaly; field verification advised).
  - `CRITICAL`: $80.0 \le 	ext{score} \le 100.0$ (Severe schedule stall, extreme cost outlier, or reality gap).
- **Confidence Score:** $0.0$ to $1.0$ (calibrated against record completeness and presence of field photographic evidence).
- **Missing Data Policy:** Missing ground truth (e.g. satellite/drone surveys) remains `null` / `"NOT_AVAILABLE"`, reducing confidence rather than inflating artificial fraud penalties.

## Limitations & Biases
- Capital costs in remote, island, or Himalayan districts (e.g. Ladakh, Arunachal Pradesh, Andaman) naturally carry logistical premiums that shift sector medians upward.
- Absence of standardized physical dimension metrics (e.g. road kilometers or building floor area) in older portal exports limits unit-rate normalization.
- Does not inspect proprietary ledger books or bank account statements; assessments reflect public open government disclosures.

## Statutory Disclaimer
> "AI-generated risk indicators are analytical decision-support signals and do not constitute proof of fraud, corruption, or irregularity."
