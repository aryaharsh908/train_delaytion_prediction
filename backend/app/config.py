import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "SIH26028 - Dynamic Train ETA Forecast System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Simulation settings
    DEFAULT_SPEED_MULTIPLIER: int = 5  # 1 real sec = 5 sim mins by default
    KALMAN_FILTER_ENABLED: bool = True
    MONTE_CARLO_SAMPLES: int = 100
    
    # Model Cache & Storage
    MODEL_DIR: str = os.path.join(os.path.dirname(__file__), "..", "models")
    MODEL_PATH: str = os.path.join(MODEL_DIR, "eta_model_v001.pkl")
    METRICS_PATH: str = os.path.join(MODEL_DIR, "model_metadata.json")
    RAW_DATA_DIR: str = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "where_is_my_train")
    
    # Database
    DATABASE_URL: str = "sqlite:///./railway_eta.db"

    # Where Is My Train / RailRadar API Configuration
    WHERE_IS_MY_TRAIN_API_KEY: str = "rg_91e5671b9dff48c999432f1e89df2793"
    WHERE_IS_MY_TRAIN_BASE_URL: str = "https://api.railradar.in/v1"
    WHERE_IS_MY_TRAIN_API_VERSION: str = "v1"
    WHERE_IS_MY_TRAIN_CLIENT_ID: str = ""
    WHERE_IS_MY_TRAIN_CLIENT_SECRET: str = ""
    WHERE_IS_MY_TRAIN_AUTH_HEADER: str = "x-api-key"
    WHERE_IS_MY_TRAIN_ENDPOINT: str = "/trains/{number}/live"

    # Rate Limiting Configuration
    REQUEST_DELAY: float = 1.0
    MAX_REQUESTS_PER_MINUTE: int = 60
    MAX_CONCURRENT_REQUESTS: int = 1

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

settings = Settings()
os.makedirs(settings.MODEL_DIR, exist_ok=True)
os.makedirs(settings.RAW_DATA_DIR, exist_ok=True)

