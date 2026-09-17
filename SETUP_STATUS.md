# NIRVANA - Setup and Environment Status (Phase 1 Inspection)

**Generated:** 2026-09-17  
**Platform:** Windows  
**Project Path:** `C:\Users\madhu\.gemini\antigravity\scratch\nirvana`

---

## 1. Environment Tool Inspection

| Tool | Expected / Requested | Actual System Status | Version / Details |
| :--- | :--- | :--- | :--- |
| **Python** | 3.11+ | **AVAILABLE** | `Python 3.14.3` (64-bit) |
| **pip** | Latest | **AVAILABLE** | `pip 26.0.1` |
| **Git** | Any modern | **AVAILABLE** | `git version 2.52.0.windows.1` |
| **Node.js** | 18+ LTS | **INSTALLING / PENDING** | Installing via Windows Package Manager (`winget install OpenJS.NodeJS.LTS`) |
| **npm** | 9+ | **INSTALLING / PENDING** | Bundled with Node.js LTS |
| **Docker** | Optional / Runtime | **NOT INSTALLED / NOT IN PATH** | Docker daemon / CLI not available in PATH |
| **Docker Compose** | Optional / Runtime | **NOT INSTALLED / NOT IN PATH** | Docker Compose CLI not available in PATH |
| **PostgreSQL / PostGIS** | Optional system service | **NOT INSTALLED / IN SERVICE** | System PostgreSQL not in PATH; SQLite with Spatial/Geodesic fallback or containerized PostgreSQL |

---

## 2. Python Package Inventory (Inspected)

### Already Installed & Ready:
- **Web & API Framework**: `fastapi` (0.141.1), `uvicorn` (0.53.0), `starlette` (1.6.0), `pydantic` (2.13.5), `python-multipart` (0.0.32)
- **Data & Analytics**: `pandas` (2.3.3), `numpy` (2.4.2), `scipy` (1.17.0), `pyarrow` (23.0.0)
- **Machine Learning**: `scikit-learn` (1.8.0), `joblib` (1.5.3)
- **HTTP & Networking**: `httpx` (0.28.1), `requests` (2.32.5), `httpcore` (1.0.9)
- **Security & Crypto**: `cryptography` (46.0.4), `bcrypt` (5.0.0)
- **PDF & Document Processing**: `pdfplumber` (0.11.9), `PyPDF2` (3.0.1), `pypdfium2` (5.3.0), `pdfminer.six` (20251230), `pillow` (12.1.0)
- **Dashboard / Prototyping (Pre-existing)**: `streamlit` (1.54.0), `pydeck` (0.9.1), `altair` (6.0.0)

### To Install / Validate via `python -m pip`:
- `sqlalchemy` (>=2.0)
- `alembic`
- `pytest`
- `PyJWT`
- `reportlab`
- `shap` (optional / fallback to scikit-learn feature importances + TreeExplainer if C-extensions conflict on Python 3.14)

---

## 3. Fallbacks & Architecture Strategy

1. **Database Fallback**: 
   - Primary: SQLAlchemy 2.0 with PostgreSQL/PostGIS connection string support.
   - Self-contained development mode: SQLite (with Haversine/geodesic distance calculations in pure Python/SQL functions and JSON geometry) when no external PostgreSQL server is active. This guarantees 100% runnable offline functionality without requiring manual DBA setup.
2. **Containerization**:
   - Provide complete production `docker-compose.yml`, `backend.Dockerfile`, and `frontend.Dockerfile` for deployments.
3. **Machine Learning**:
   - Python 3.14 compatible pipelines using `scikit-learn` (IsolationForest, RandomForest, GradientBoosting, TF-IDF, cosine similarity), `numpy`, `pandas`, and `joblib`.
   - Clear honesty markers: `NOT_TRAINED` or `INSUFFICIENT_DATA` when ground truth labels do not exist.
