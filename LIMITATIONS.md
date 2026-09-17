# NIRVANA - Known Limitations & Transparency Report

## 1. Data Availability Realities
1. **Public Machine-Readable MPLADS API:** Official MoSPI portals (`mplads.gov.in`) do not offer an unauthenticated public REST API. The system provides robust CSV/JSON ingestion connectors for authorized state/district exports.
2. **Field Observation Gap:** In the absence of geo-tagged inspection photos or drone surveys, `observed_progress` evaluates to `null`. The system explicitly denotes this as `DATA NOT AVAILABLE` and does not synthesize observations.
3. **Historical Schedule Granularity:** Many sanctioned records only contain a single sanctioned completion year rather than a structured CPM/PERT milestone chart.

## 2. Machine Learning Boundaries
1. **Unsupervised Nature:** In the absence of publicly released ground-truth lists of audited irregularities, fraud labels do not exist. Therefore, models operate on unsupervised statistical divergence (Isolation Forest, robust Z-scores, text/geo similarity).
2. **Physical Progress Vision Model:** The computer vision structural pipeline is architected for YOLO/ResNet inference, but is honestly designated `MODEL_NOT_TRAINED` until trained on a domain-specific Indian rural/urban public infrastructure inspection dataset.
3. **Synthetic Data Quarantine:** Synthetic fixtures created for testing and interface verification are strictly segregated under `dataset/synthetic/` and tagged `data_availability_status: SYNTHETIC`. They are never mingled with official records.

## 3. Geospatial Precision
- Projects without GPS coordinates are represented at the district/block centroid with explicit flags indicating missing coordinates (`latitude: null, longitude: null`).
