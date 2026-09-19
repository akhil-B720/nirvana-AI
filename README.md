# NIRVANA
### National Infrastructure Reality & Verification Network using AI

[![Smart India Hackathon](https://img.shields.io/badge/SIH-SIH26102-blue.svg)](https://www.sih.gov.in/)
[![Team](https://img.shields.io/badge/Team-TYRANTS-indigo.svg)](#team)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/Tests-71%2F71%20Passed-brightgreen.svg)](#verification)
[![Render Ready](https://img.shields.io/badge/Render-Deploy%20Ready-black.svg)](https://render.com)

**NIRVANA** is an AI-powered decision-support platform engineered to detect statistical anomalies, expenditure inefficiencies, execution delays, and reality divergences in the implementation of the Member of Parliament Local Area Development Scheme (MPLADS).

---

> ### ⚖️ Mandatory Human-in-the-Loop Advisory
> **"AI-generated risk indicators are decision-support signals and do not constitute proof of fraud, corruption, or wrongdoing."**  
> Authorized human vigilance officers retain ultimate verification, inspection, and administrative decision-making authority.

---

## 👥 Project Team & Credits

- **Team:** TYRANTS
- **Hackathon:** Smart India Hackathon — SIH26102
- **Team Leader:** Akhil Bharath Godekari
- **Team Member 1:** Rohith Vadra
- **Team Member 2:** Kiranmai Janapana

---

## 🏛️ Platform Architecture & 3 Planes of Reality

NIRVANA continuously reconciles three planes of information:
1. **Expected Reality:** What should exist according to sanction orders, milestone schedules, and approved engineering estimates.
2. **Reported Reality:** What executing agencies and contractors submit in official physical returns and financial utilization certificates.
3. **Observed Reality:** What physical inspections, geotagged evidence photos, and spatial audits objectively confirm.

Where these planes diverge, NIRVANA calculates the **Reality Gap**, triggers multi-signal **Risk Fusion**, and generates traceable **Verification Dossiers**.

---

## 🌟 Core Capabilities

- **Attribute-Driven 3D Digital Twins:** Dynamic Three.js structural models reflecting 4 core asset typologies (Building, Road, Bridge, Water Tank) across Expected, Reported, and Observed states with component-level reality discrepancies.
- **Explainable Anomaly & Delay Machine Learning:**
  - Cost outlier detection via Isolation Forest and Robust Interquartile Z-Scores.
  - Completion delay risk forecasting via Ridge regression trained on real MoSPI historical execution cycles.
  - Spatial duplicate detection via TF-IDF, Cosine Similarity, and Geodesic Haversine clustering.
- **Dual Data Operating Modes:**
  - **REAL DATA Mode:** Ingests official Ministry of Statistics and Programme Implementation (MoSPI) disclosures (3,232 project works + 258 state-level macro expenditure records). Missing ground evidence is strictly represented as `null` with `DATA NOT AVAILABLE`.
  - **SYNTHETIC DATA Mode:** An isolated evaluation benchmark (5,000 multi-sector projects across 37 States/UTs, 31,235 civil components, 10,000 documents) for stress-testing vigilance algorithms without corrupting official government statistics.
- **Executive PDF Dossiers:** Cryptographically verifiable inspection and audit dossiers generated on-demand via ReportLab.
- **Interactive GIS Map & Analytics:** Geospatial cluster visualization, constituency heatmaps, financial burn-rate analysis, and macro regression projections.
- **Role-Based Security & Tamper-Evident Audit:** Strict JWT-based authorization (`ADMIN`, `OFFICER`, `ANALYST`, `VIEWER`) and append-only cryptographic event logging.

---

## 🚀 Quick Start (Local Setup)

### 1. Prerequisites
- Python 3.11+ (Python 3.14 compatible)
- Node.js 18+ (optional, for frontend development build)

### 2. Clone & Environment Setup
```bash
git clone https://github.com/akhil-B720/nirvana-AI.git
cd nirvana-AI
cp .env.example .env
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Data Pipeline & Train ML Models
```bash
python -m data_pipeline.run
python -m ml.train.cost_anomaly
python -m ml.train.delay_model
python -m ml.train.similarity_model
```

### 5. Start NIRVANA Full-Stack Server
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Open your browser at:
- **Application Portal:** [http://localhost:8000/app](http://localhost:8000/app)
- **API Documentation (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Endpoint:** [http://localhost:8000/health](http://localhost:8000/health)

---

## ☁️ Render Cloud Deployment

NIRVANA is configured for one-click deployment on [Render](https://render.com) using the included `render.yaml`.

### Manual Render Setup:
1. Create a new **Web Service** connected to your GitHub repository `https://github.com/akhil-B720/nirvana-AI.git`.
2. Configure the following service settings:
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path:** `/health`
3. Add Environment Variables:
   - `PYTHON_VERSION`: `3.11.9`
   - `APP_NAME`: `NIRVANA`
   - `APP_ENV`: `production`
   - `DEBUG`: `false`
   - `DATA_MODE`: `REAL` (or `SYNTHETIC`)
   - `SECRET_KEY`: `(click generate or provide 32+ char secret)`

---

## 🧪 Verification & Testing

NIRVANA includes a comprehensive test suite covering data pipeline integrity, ML model contracts, role-based authorization, PDF dossier generation, and frontend API contracts:

```bash
pytest
```
Expected result: **71/71 tests passed (100% pass rate)**.
