# NIRVANA - Authoritative Data Sources & Discovery Audit

**Project:** NIRVANA (National Infrastructure Reality & Verification Network using AI)  
**Team:** TYRANTS | SIH26102  
**Audit Date:** 2026-09-17  

---

## 1. Discovered Sources & Live Verification Matrix

| Source Name | Source URL | Source Type | Access Method | Verification Status | Available Fields | Missing / Inaccessible Fields | Licensing / Limitations |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Authentic MoSPI MPLADS Project Archive** | `dataset/raw/real_mplads_works.csv` (MoSPI open portal archive) | Official Portal Export | Semicolon CSV Ingestion | `PUBLIC_VERIFIED` | 60,359 authentic works: `WORK`, `CATEGORY`, `STATE`, `CONSTITUENCY`, `IDA`, `BLOCK`, `VILLAGE`, `RECOMMENDED DATE`, `ALLOCATION AMOUNT`, `STATUS`, `HOUSE` | GPS pin-point coordinates (centroid-mapped), contractor PAN/GSTIN, milestone sensor logs | Open Data Commons Open Database License (ODbL) / MoSPI Open Data. Stratified 3,232 projects actively ingested into DB. |
| **Macro MoSPI Yearly Expenditure & Works** | `dataset/raw/mplads_state_yearly_expenditure_and_works.csv` | Official State Aggregate Export | CSV Ingestion | `PUBLIC_VERIFIED` | 258 records: `State`, `Financial_Year`, `Releases`, `Expenditure`, `Works_Recommended`, `Works_Sanctioned`, `Works_Completed` | Individual project-level records | MoSPI Official Reports (2014-2021). |
| **Macro MoSPI Sector Distribution** | `dataset/raw/mplads_state_sector_distribution.csv` | Official Sector Distribution Export | CSV Ingestion | `PUBLIC_VERIFIED` | State-level allocation across 12 infrastructure sectors | Sub-scheme line items | MoSPI Annual Aggregates. |
| **Macro MoSPI Unspent Balance** | `dataset/raw/mplads_state_unspent_balance.csv` | Official State Balance Audit | CSV Ingestion | `PUBLIC_VERIFIED` | Cumulative interest, unspent balances, release utilization | Bank transaction account numbers | MoSPI Central Financial Records. |
| **Empowered Indian (Civic Aggregator)** | `https://empoweredindian.in/mplads` / `https://api.empoweredindian.in/api` | Third-Party Civic Tech Platform | Unauthenticated JSON REST API | `UNVERIFIED_THIRD_PARTY` | `work_id`, `work_description`, `cost`, `category`, `state`, `district`, `location` (IDA), `completion_date`, `mp_details` | Geo-coordinates, contractor identities, drone/satellite evidence | Non-government platform; data secondary-aggregated from MoSPI. Tagged as UNVERIFIED_THIRD_PARTY. |
| **Synthetic Development & Test Fixtures** | Embedded in NIRVANA Repository (`dataset/synthetic/fixtures.csv`) | Test Fixture | File System Read | `SYNTHETIC` | Simulated edge cases with deliberate anomalies (8 benchmark fixtures) | Real-world ground truth | STRICTLY FOR UNIT/INTEGRATION TESTS & BENCHMARKING. Never presented as official MoSPI records. |

---

## 2. Technical Findings from Probe

1. **MoSPI Project Archive Processing:**
   - Total rows: 60,359 authentic government project records.
   - Status breakdown: 50,888 Unsanctioned/Recommended, 6,528 Sanctioned, 1,503 Completed, 629 Ongoing.
   - Active database ingestion uses stratified sampling: 1,503 Completed + 629 Ongoing + 1,000 Sanctioned + 100 Recommended = 3,232 public verified projects.
   - Geocoding: Official state and district centroids applied with deterministic hash jittering. Projects without coordinates have `latitude: null, longitude: null`.
2. **Empowered Indian Detailed Assessment:**
   - Website Classification: Third-Party Dashboard / Civic Tech Platform (supported by Malpani Ventures).
   - Serves unauthenticated JSON REST endpoints (`/api/works/completed`, `/api/works/recommended`).
   - Integrated via `data_pipeline/sources/empowered_indian.py` (`EmpoweredIndianDataSource`) with strict provenance tagging (`UNVERIFIED_THIRD_PARTY`).
3. **Policy Compliance:**
   - NIRVANA does NOT scrape protected portals or bypass CAPTCHAs/firewalls.
   - Missing data remains `null` / `"NOT_AVAILABLE"`.
   - AI outputs carry the mandatory statutory decision-support notice.
