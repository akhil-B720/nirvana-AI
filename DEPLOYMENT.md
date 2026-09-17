# NIRVANA - Deployment & Operations Guide

## 1. Quick Local Development (Windows / Linux / macOS)

### Backend Requirements:
- Python 3.11+ (Python 3.14 compatible)
- Node.js 18+ LTS

```powershell
# 1. Clone or navigate to the repository
cd C:\Users\madhu\.gemini\antigravity\scratch\nirvana

# 2. Configure environment
Copy-Item .env.example .env

# 3. Ingest Data & Train Baseline ML Models
python -m data_pipeline.run
python -m ml.train.cost_anomaly
python -m ml.train.delay_model
python -m ml.train.similarity_model

# 4. Start FastAPI Backend (Port 8000)
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Start React Frontend (Port 5173) in a separate terminal
cd frontend
npm install
npm run dev
```

---

## 2. Production Docker Deployment

```bash
# Build and run all microservices with PostgreSQL & PostGIS
docker compose up --build -d

# Verify services
docker compose ps

# Run pipeline inside backend container
docker compose exec backend python -m data_pipeline.run
```
