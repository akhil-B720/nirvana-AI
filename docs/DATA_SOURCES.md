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

---

## 2. Technical Findings from Probe

1. **Automated Endpoint Probe Results (Executed 2026-09-17):**
   - `https://mplads.gov.in/`: Resulted in socket timeout. Server does not provide open REST endpoints.
   - `https://mplads.gov.in/MPLADS/Dashboard/DashBoard.aspx`: Timed out; uses ASPX session state.
   - `https://data.gov.in/api/1/action/package_search?q=MPLAD`: Returns HTML gateway requiring NDSAP API key registration.
2. **Policy Compliance:**
   - NIRVANA does **NOT** scrape protected portals or bypass CAPTCHAs/firewalls.
   - Authorized users can ingest verified government CSV/JSON extracts via the validated `data_pipeline` ingestion engine.
   - When external records are missing, the system emits `null` with `DATA NOT AVAILABLE`.
