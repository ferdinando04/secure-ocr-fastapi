from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os

class Settings(BaseSettings):
    # API Metadata
    APP_NAME: str = "OCR Venezolano Elite"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Security
    API_KEY: str = "your-super-secret-production-key"  # Obligatorio en PROD
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    API_PREFIX: str = "/api/v1"

    # OCR Config
    OCR_LANGS: List[str] = ["es", "en"]
    OCR_GPU: bool = True
    MIN_CONFIDENCE: float = 0.50

    # Resource Limits
    MAX_FILE_SIZE_MB: int = 5
    ALLOWED_IMAGE_EXTENSIONS: List[str] = ["jpg", "jpeg", "png"]
    MAX_IMAGE_RESOLUTION: int = 4096  #px para prevenir decompression bombs

    # Infrastructure
    TMP_DIR: str = "/tmp/ocr_service"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
