# NIRVANA - Authoritative Data Sources & Discovery Audit

**Project:** NIRVANA (National Infrastructure Reality & Verification Network using AI)  
**Team:** TYRANTS | SIH26102  
**Audit Date:** 2026-09-17  

---

## 1. Discovered Sources & Live Verification Matrix

| Source Name | Source URL | Source Type | Access Method | Verification Status | Available Fields | Missing / Inaccessible Fields | Licensing / Limitations |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **MPLADS Official Portal** | `https://mplads.gov.in/` | Central Government Web Portal | HTTPS Web Form | `REQUIRES_AUTHORIZATION` / `MISSING` (Bulk API) | Aggregated state/district totals on legacy ASP.NET UI | No public bulk machine-readable API endpoint; HTTP connections timed out on automated probe. Protected by server firewalls/CAPTCHA. | Proprietary MoSPI; scraping prohibited by terms of use. |
| **MPLADS ASP.NET Dashboard** | `https://mplads.gov.in/MPLADS/Dashboard/DashBoard.aspx` | Interactive Web Dashboard | HTTPS Browser Session | `SECONDARY_SOURCE` | High-level summary metrics | No machine-readable JSON/CSV export, session ViewState required. | Human browser interaction only. Automated extraction restricted. |
| **Open Government Data (data.gov.in)** | `https://data.gov.in/` | National Open Data Platform | CKAN / Data API (API Key required) | `AUTHORIZED` (Requires API Key) | Metadata catalog, historical district releases (varies by dataset) | Real-time project-level geo-coordinates and contractor records generally absent in public catalog. | National Data Sharing and Accessibility Policy (NDSAP). Requires registered API token. |
| **Authorized Officer Field CSV / Excel Ingestion** | Local / Secure Officer Upload | Direct Government Ingestion | Multi-part Form Upload / S3 / Local Path | `PUBLIC_VERIFIED` (when authenticated) | `project_id`, `project_name`, `sanction_amount`, `released_amount`, `expenditure_amount`, `coordinates`, `start_date`, `expected_completion` | Field progress photos, physical milestone sensor streams (unless uploaded) | Requires valid Officer/Admin role JWT credentials. |
| **Synthetic Development & Test Fixtures** | Embedded in NIRVANA Repository (`dataset/synthetic/`) | Test Fixture | File System Read | `SYNTHETIC` | Simulated schemas with boundary test cases, edge cases, deliberate anomalies | Real-world ground truth | STRICTLY FOR UNIT/INTEGRATION TESTS & BENCHMARKING. Never presented as official MoSPI records. |
| **Empowered Indian (Civic Aggregator)** | `https://empoweredindian.in/mplads` / `https://api.empoweredindian.in/api` | Third-Party Civic Tech Platform | Unauthenticated JSON REST API | `UNVERIFIED_THIRD_PARTY` | `work_id`, `work_description`, `cost`, `category`, `state`, `district`, `location` (IDA), `completion_date`, `completion_year`, `mp_details` (name, constituency, party) | Geo-coordinates (lat/lon), contractor names, milestone-level sensor logs, inspection photos | Non-government platform backed by Malpani Ventures; data secondary-aggregated from MoSPI. Tagged as UNVERIFIED_THIRD_PARTY. |

---

## 2. Technical Findings from Probe

1. **Automated Endpoint Probe Results (Executed 2026-09-17):**
   - `https://mplads.gov.in/`: Resulted in socket timeout. Server does not provide open REST endpoints.
   - `https://mplads.gov.in/MPLADS/Dashboard/DashBoard.aspx`: Timed out; uses ASPX session state.
   - `https://data.gov.in/api/1/action/package_search?q=MPLAD`: Returns HTML gateway requiring NDSAP API key registration.
   - `https://empoweredindian.in/mplads`: Accessible React SPA backed by live unauthenticated REST backend at `https://api.empoweredindian.in/api`.
2. **Empowered Indian Detailed Assessment:**
   - **Website Classification:** **Third-Party Dashboard / Civic Tech Platform** (Not an official `.gov.in` domain). Supported by Malpani Ventures / Dr. Aniruddha Malpani.
   - **Publicly Accessible Pages:** `/mplads`, `/mplads/mps`, `/mplads/states`, `/mplads/track-area`, `/mplads/compare`, `/mplads/search`, `/mplads/report`.
   - **Documented API & Downloadable Files:** No public API documentation or OpenAPI/Swagger specification exists (`/docs` returns 404). No direct bulk CSV/Excel download buttons on the UI; data is served via paginated JSON REST endpoints (`/api/works/completed`, `/api/works/recommended`, `/api/summary/states`, `/api/summary/mps`).
   - **Original Provider:** Platform explicitly cites *"Data sourced from official MPLADS portal"*. It secondary-scrapes MoSPI MPLADS reports (18th Lok Sabha & historical).
   - **Verification Feasibility:** Individual records can be cross-referenced against MoSPI IDA formats (e.g. `(DISTRICT COLLECTOR CHITTOOR_IDA)`), but because it is an unofficial secondary aggregator, it must remain tagged as `UNVERIFIED_THIRD_PARTY` in NIRVANA until reconciled against direct MoSPI nodal records.
   - **Test Importer:** Implemented in `data_pipeline/sources/empowered_indian.py` (`EmpoweredIndianDataSource`), verified with automated test `tests/test_empowered_indian.py` (26/26 tests passing).
3. **Policy Compliance:**
   - NIRVANA does **NOT** scrape protected portals or bypass CAPTCHAs/firewalls.
   - Authorized users can ingest verified government CSV/JSON extracts via the validated `data_pipeline` ingestion engine.
   - When external records are missing, the system emits `null` with `DATA NOT AVAILABLE`.
   - Third-party sources are never presented as verified government data.
