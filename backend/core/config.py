import os
from pathlib import Path
from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "NIRVANA"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DATA_MODE: str = os.getenv("DATA_MODE", "REAL")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "nirvana_development_secret_key_change_in_production_32bytes_minimum_length")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    API_V1_PREFIX: str = "/api/v1"
    PORT: int = int(os.getenv("PORT", 8000))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./nirvana.db")
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UPLOAD_DIR: Path = Path(__file__).resolve().parent.parent.parent / "uploads"
    REPORTS_DIR: Path = Path(__file__).resolve().parent.parent.parent / "reports"
    MODEL_DIR: Path = Path(__file__).resolve().parent.parent.parent / "models"
    DATASET_DIR: Path = Path(__file__).resolve().parent.parent.parent / "dataset"

settings = Settings()

# Ensure runtime directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
settings.MODEL_DIR.mkdir(parents=True, exist_ok=True)
(settings.DATASET_DIR / "raw").mkdir(parents=True, exist_ok=True)
(settings.DATASET_DIR / "processed").mkdir(parents=True, exist_ok=True)
(settings.DATASET_DIR / "synthetic").mkdir(parents=True, exist_ok=True)
