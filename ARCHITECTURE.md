# NIRVANA - System Architecture & Technical Specifications

**National Infrastructure Reality & Verification Network using AI (NIRVANA)**  
**Team TYRANTS | SIH26102**

---

## 1. High-Level System Architecture

NIRVANA is a multi-tier, human-in-the-loop decision-support platform designed to compare **Expected Reality**, **Reported Reality**, and **Observed Reality** across public infrastructure projects funded under the MPLAD scheme.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             PRESENTATION LAYER                              │
│  React 18 + Vite + TypeScript + Tailwind CSS                                │
│  - MapLibre GL JS (Geospatial Clustering, Risk & Reality Gap Choropleths)  │
│  - Three.js / React Three Fiber (Attribute-Driven 3D Digital Twins)         │
│  - Recharts (Financial S-Curves, Time-series, Radar DNA, Anomaly Chains)    │
│  - Contextual AI Assistant (Database-grounded verification Q&A)             │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ REST / JSON (JWT / RBAC)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                             APPLICATION LAYER                               │
│  FastAPI (Python 3.14 / 3.11+)                                              │
│  - Auth & RBAC (ADMIN, OFFICER, ANALYST, VIEWER)                            │
│  - Reality Gap Engine (Expected vs Reported vs Observed)                    │
│  - Risk Fusion Engine (Configurable weighted anomaly synthesis)             │
│  - Similarity Engine (TF-IDF + Cosine + Geodesic Haversine)                 │
│  - Verification Recommender (Traceable action generator)                    │
│  - Evidence & Document AI Engine (PyPDF2, PDFPlumber, MIME/Hash validation) │
│  - ReportLab Verification PDF Generator                                     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                             PERSISTENCE LAYER                               │
│  SQLAlchemy 2.0 ORM + Alembic Migrations                                    │
│  - Production: PostgreSQL 15+ with PostGIS Extension                        │
│  - Self-Contained Local Mode: SQLite with Haversine Geodesic Fallback       │
│  - Provenance Store: SHA-256 Hashing, Source URLs, Raw vs Normalized audit  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Engines

### 2.1 Reality Gap Engine
Quantifies divergence between three operational states:
1. **Reported Progress ($P_R$)**: Administrative percentage submitted by the executing agency.
2. **Expected Progress ($P_E$)**: Calculated from the project start date, scheduled duration, and historical sector S-curves ($0 \le P_E \le 100$).
3. **Observed Progress ($P_O$)**: Physically validated milestone from georeferenced photo evidence ($0 \le P_O \le 100$), or `null` if no verified field evidence exists.

When $P_O$ is missing:
- `observed_progress = null`
- `observed_progress_status = NOT_AVAILABLE`
- The system NEVER fabricates or substitutes $P_R$ for $P_O$.

### 2.2 Prototype Reality Gap Score
- **0 - 30**: NORMAL
- **31 - 60**: WATCH
- **61 - 80**: HIGH
- **81 - 100**: CRITICAL
*Notice: "This is a prototype/system-defined analytical score and is not an official government metric."*

### 2.3 Risk Fusion Engine
Combines individual anomaly detectors using configurable weights:
- Cost Anomaly ($w_1 = 0.20$)
- Payment-to-Progress Mismatch ($w_2 = 0.20$)
- Timeline Delay Risk ($w_3 = 0.15$)
- Project Duplicate / Similarity ($w_4 = 0.10$)
- Document Inconsistency ($w_5 = 0.10$)
- Reality Gap ($w_6 = 0.25$)

If any signal is unavailable, its weight is dynamically redistributed across the remaining active signals, preserving mathematical scale without penalizing projects for uncollected evidence.

---

## 3. Human-in-the-Loop Safeguard
All user-facing views and API responses mandate the advisory:
> *"AI-generated risk indicators are decision-support signals and do not constitute proof of fraud, corruption, or wrongdoing."*
