# NIRVANA
### National Infrastructure Reality & Verification Network using AI
**Team:** TYRANTS | **Smart India Hackathon:** SIH26102  
**Problem Statement:** Development of an AI-powered system to identify anomalies, inefficiencies, inconsistencies, and potential irregularities in MPLAD Scheme implementation.

---

> ### Mandatory Human-in-the-Loop Advisory
> **"AI-generated risk indicators are decision-support signals and do not constitute proof of fraud, corruption, or wrongdoing."**  
> Authorized human vigilance officers retain ultimate verification and decision-making authority.

---

## 1. What is NIRVANA?
NIRVANA solves the fundamental disconnect in public works governance by continuously comparing three planes of information:
1. **Expected Reality:** What should exist given the sanctioned timeline, budget, and engineering schedule.
2. **Reported Reality:** What executing agencies and contractors officially claim in financial and physical returns.
3. **Observed Reality:** What physical ground-truth sensors, geotagged photos, and verified inspection media actually confirm.

Where these planes diverge, NIRVANA calculates the **Reality Gap**, triggers multi-signal **Risk Fusion**, and generates traceable **Verification Recommendations**.

---

## 2. Key Capabilities
- **Attribute-Driven 3D Digital Twins:** Dynamic Three.js structural models reflecting progressive stages (Building, Road, Bridge, Water Tank) across Expected, Reported, and Observed states.
- **Explainable Anomaly Detection:** Cost anomaly analysis (Isolation Forest + Robust Z-Scores), schedule delay estimation, and semantic duplicate detection (TF-IDF + Cosine Similarity + Geodesic Haversine).
- **Data Provenance & Integrity:** Strict SHA-256 tracking of every uploaded record. If ground evidence is missing, the system outputs `null` with `DATA NOT AVAILABLE` rather than inventing false progress.
- **Executive PDF Dossiers:** On-demand generation of comprehensive verification audit reports via ReportLab.
- **Role-Based Security:** Strict JWT authorization enforcing `ADMIN`, `OFFICER`, `ANALYST`, and `VIEWER` permissions.

---

## 3. Quick Start

### Backend:
```powershell
cd C:\Users\madhu\.gemini\antigravity\scratch\nirvana
python -m data_pipeline.run
python -m uvicorn backend.main:app --reload --port 8000
```

### Frontend:
```powershell
cd frontend
npm install
npm run dev
```

Visit the API Swagger documentation at `http://localhost:8000/docs` and the web portal at `http://localhost:5173`.
