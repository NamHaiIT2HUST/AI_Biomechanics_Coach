from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / 'data'


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    APP_NAME: str = 'AI Biomechanics Coach API'
    APP_VERSION: str = '0.1.0'
    DEBUG: bool = True
    DATA_PATH: Path = DATA_DIR
    RAW_VIDEO_DIR: Path = DATA_DIR / 'raw'
    OUTPUT_OVERLAY_DIR: Path = DATA_DIR / 'outputs' / 'overlays'
    OUTPUT_FRAME_DIR: Path = DATA_DIR / 'outputs' / 'evidence_frames'
    EXERCISES_CONFIG_DIR: Path = BACKEND_DIR / 'app' / 'exercises'
    MODEL_PATH: Path = PROJECT_ROOT / 'ai' / 'models' / 'pretrained' / 'pose_landmarker_heavy.task'
    ANALYSES_DIR: Path = DATA_DIR / 'outputs' / 'analyses'
    MAX_UPLOAD_BYTES: int = 100 * 1024 * 1024


settings = Settings()
