# NIRVANA - Known Blockers & External Dependencies

**Project:** National Infrastructure Reality & Verification Network using AI (NIRVANA)  
**Team:** TYRANTS | **Smart India Hackathon:** SIH26102  
**Status:** Documented for production rollout  

---

## 1. External Data Source Connectivity Blockers

### A. MoSPI MPLADS Portal Direct Scraping
- **Portal:** https://mplads.gov.in/ / http://164.100.68.116/
- **Blocker:** The government production portal enforces active CAPTCHA challenges, ASP.NET session state cookies, and IP rate-limiting firewalls. Direct unauthenticated automated scraping violates government terms of service and fails with connection timeouts.
- **Resolution in NIRVANA:** Ingested verified, public ODbL archive of 60,359 authentic MoSPI records (Vonter/india-mplads-works) with SHA-256 provenance tracking. Provided production batch upload interface and nodal officer API token placeholder for authenticated ministry deployments.

### B. data.gov.in API Key Rate Limits
- **Portal:** https://api.data.gov.in/
- **Blocker:** Public API keys are rate-limited to 1,000 calls per day. Real-time streaming across all 543 parliamentary constituencies requires a dedicated government NIC API gateway subscription.
- **Resolution in NIRVANA:** Structured caching and batch CSV ingest mode implemented in DataGovDataSource.

---

## 2. Satellite & Drone Sensor Data Feed Blockers

### A. High-Resolution Orthomosaic Satellite Imagery
- **Resolution required:** Ground Sampling Distance (GSD) < 30 cm is required to detect structural rebar, foundation trenches, and building floor milestones from space. Free public optical imagery (Sentinel-2 at 10m, Landsat at 30m) is insufficient for micro-level municipal construction verification.
- **Blocker:** Commercial satellite constellations (Maxar, PlanetScope) require paid institutional licensing and scheduled tasking passes.
- **Resolution in NIRVANA:** NIRVANA explicitly marks unverified projects as observed_progress = null with status NOT_AVAILABLE. Never fabricates satellite observations. Built a secure field evidence upload pipeline with GPS EXIF extraction so field engineers can supply ground-truth georeferenced photos.

### B. Computer Vision Physical Progress Model
- **Blocker:** Training a multi-class semantic segmentation model (YOLOv8 / Mask R-CNN) for 100+ structural milestones across 10 civil engineering sectors requires ~50,000 annotated field inspection images.
- **Resolution in NIRVANA:** The interface is architected and documented in docs/MODEL_CARD_PROGRESS.md. When image datasets are absent, the model status is honestly reported as MODEL_NOT_TRAINED.

---

## 3. Deployment & Infrastructure Blockers

### A. Native PostgreSQL / PostGIS on Developer Windows Host
- **Blocker:** Developer local machine lacks active local PostgreSQL service on port 5432 and Docker daemon is not in Windows system PATH.
- **Resolution in NIRVANA:** Built full SQLite spatial engine with custom Haversine SQL UDF (haversine_km). Full Docker compose scripts (docker-compose.yml, ackend.Dockerfile, rontend.Dockerfile) are provided for production servers.
