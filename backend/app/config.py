import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Project Root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"

class Settings(BaseSettings):
    PROJECT_NAME: str = "NeuroBroker"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Host & Port
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Security / Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "neurobroker-super-secret-key-btech-2026-distributed-dl")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    VOLUNTEER_REGISTRATION_TOKEN: str = os.getenv("VOLUNTEER_TOKEN", "NB_VOLUNTEER_SECRET_2026")
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{BASE_DIR}/storage/neurobroker.db"
    )
    
    # File Storage Directories
    STORAGE_PATH: Path = STORAGE_DIR
    DATASETS_DIR: Path = STORAGE_DIR / "datasets"
    MODEL_PACKAGES_DIR: Path = STORAGE_DIR / "model_packages"
    PARTITIONS_DIR: Path = STORAGE_DIR / "partitions"
    CHECKPOINTS_DIR: Path = STORAGE_DIR / "checkpoints"
    GLOBAL_MODELS_DIR: Path = STORAGE_DIR / "global_models"
    NODE_UPDATES_DIR: Path = STORAGE_DIR / "node_updates"
    LOGS_DIR: Path = STORAGE_DIR / "logs"
    REPORTS_DIR: Path = STORAGE_DIR / "reports"
    
    # Node Heartbeat & Telemetry Settings
    HEARTBEAT_INTERVAL_SECONDS: int = 5
    HEARTBEAT_TIMEOUT_SECONDS: int = 15
    MAX_NODE_RETRY_COUNT: int = 3
    
    # Scheduler Weights & Configuration
    SCHEDULER_MODE: str = os.getenv("SCHEDULER_MODE", "resource_aware") # resource_aware, hybrid, round_robin, random
    WEIGHT_CPU: float = 0.15
    WEIGHT_RAM: float = 0.15
    WEIGHT_GPU_CAPABILITY: float = 0.25
    WEIGHT_GPU_MEMORY: float = 0.15
    WEIGHT_NETWORK: float = 0.10
    WEIGHT_RELIABILITY: float = 0.10
    WEIGHT_HISTORICAL_PERF: float = 0.05
    WEIGHT_CURRENT_LOAD: float = 0.15
    WEIGHT_TRANSFER_PENALTY: float = 0.10
    
    # Fairness Settings
    FAIRNESS_PENALTY_FACTOR: float = 0.15
    MAX_ROUNDS_PER_NODE_DISPARITY: int = 3
    
    # Anomaly Detection Settings
    ANOMALY_CPU_SPIKE_PERCENT: float = 95.0
    ANOMALY_RAM_SPIKE_PERCENT: float = 95.0
    ANOMALY_GPU_SPIKE_PERCENT: float = 98.0
    ANOMALY_LATENCY_MAX_MS: float = 1500.0

    class Config:
        case_sensitive = True
        extra = "allow"

settings = Settings()

# Ensure all storage directories exist
for folder in [
    settings.STORAGE_PATH,
    settings.DATASETS_DIR,
    settings.MODEL_PACKAGES_DIR,
    settings.PARTITIONS_DIR,
    settings.CHECKPOINTS_DIR,
    settings.GLOBAL_MODELS_DIR,
    settings.NODE_UPDATES_DIR,
    settings.LOGS_DIR,
    settings.REPORTS_DIR,
]:
    folder.mkdir(parents=True, exist_ok=True)
