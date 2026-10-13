from pathlib import Path
from pydantic_settings import BaseSettings

# Base directories
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"

class Settings(BaseSettings):
    APP_NAME: str = "AI Biomechanics Coach API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # Storage paths
    DATA_PATH: Path = DATA_DIR
    RAW_VIDEO_DIR: Path = DATA_DIR / "raw"
    OUTPUT_OVERLAY_DIR: Path = DATA_DIR / "outputs" / "overlays"
    OUTPUT_FRAME_DIR: Path = DATA_DIR / "outputs" / "evidence_frames"
    EXERCISES_CONFIG_DIR: Path = BACKEND_DIR / "app" / "exercises"
    
    # Model settings
    MODEL_PATH: Path = PROJECT_ROOT / "ai" / "models" / "pretrained" / "pose_landmarker_heavy.task"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
