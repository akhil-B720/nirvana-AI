# NIRVANA - Deployment & Operations Guide

**System:** NIRVANA — National Infrastructure Reality & Verification Network using AI  
**Team:** TYRANTS | **Hackathon:** Smart India Hackathon — SIH26102  

---

## 1. Quick Local Development (Windows / Linux / macOS)

### Prerequisites:
- Python 3.11+ (Python 3.14 compatible)
- pip and virtual environment (`venv`)

### Setup Instructions:
```bash
# 1. Clone repository
git clone https://github.com/akhil-B720/nirvana-AI.git
cd nirvana-AI

# 2. Configure environment
cp .env.example .env

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Ingest Official Data & Train ML Models
python -m data_pipeline.run
python -m ml.train.cost_anomaly
python -m ml.train.delay_model
python -m ml.train.similarity_model

# 5. Start Unified FastAPI Full-Stack Server (Port 8000)
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The portal is immediately accessible at `http://localhost:8000/app` and API docs at `http://localhost:8000/docs`.

---

## 2. Render Cloud Deployment Guide

NIRVANA is architected to run seamlessly on Render as a single web service that hosts both the FastAPI REST backend and the production SPA interface.

### Option A: Automatic Blueprint Deployment
1. Log in to your [Render Dashboard](https://dashboard.render.com).
2. Click **New +** -> **Blueprint**.
3. Connect your repository: `https://github.com/akhil-B720/nirvana-AI.git`.
4. Render will automatically read `render.yaml` and configure all build and runtime parameters.
5. Click **Apply**.

### Option B: Manual Web Service Setup
1. On Render, click **New +** -> **Web Service**.
2. Select your repository `https://github.com/akhil-B720/nirvana-AI`.
3. Fill in the deployment details:
   - **Name:** `nirvana-ai`
   - **Region:** Any (e.g. Oregon / Singapore / Frankfurt)
   - **Branch:** `main`
   - **Root Directory:** (leave blank)
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path:** `/health`
4. In the **Environment Variables** section, add:
   - `PYTHON_VERSION`: `3.11.9`
   - `APP_NAME`: `NIRVANA`
   - `APP_ENV`: `production`
   - `DEBUG`: `false`
   - `DATA_MODE`: `REAL` (or `SYNTHETIC`)
   - `SECRET_KEY`: `(generate a strong 32+ character random string)`
5. Click **Create Web Service**.
6. Once deployed, Render will verify the `/health` endpoint and your NIRVANA platform will be live at `https://nirvana-ai.onrender.com/app`.

---

## 3. Production Docker Deployment

```bash
# Build and run microservices with PostgreSQL & PostGIS
docker compose up --build -d

# Verify services status
docker compose ps

# Run pipeline inside container if starting with empty database
docker compose exec backend python -m data_pipeline.run
```

---

## 4. Operational Health Verification

To verify that the service is operational in any environment:
```bash
curl -f http://localhost:8000/health
```
Expected output:
```json
{
  "status": "HEALTHY",
  "app": "NIRVANA",
  "version": "1.0.0",
  "mode": "REAL",
  "environment": "production"
}
```
