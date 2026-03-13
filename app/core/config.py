from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pydantic import Field

class Settings(BaseSettings):
    # API Metadata
    APP_NAME: str = "OCR Venezolano Elite"
    APP_VERSION: str = "1.0.1"
    DEBUG: bool = False

    # Security
    # Sin valor por defecto sensible para obligar uso de variables de entorno
    API_KEY: str = Field(..., min_length=32, description="Clave de API obligatoria")
    # Lista vacía por defecto para forzar configuración explícita
    ALLOWED_ORIGINS: List[str] = Field(default_factory=list)
    API_PREFIX: str = "/api/v1"

    # OCR Config
    OCR_LANGS: List[str] = ["es", "en"]
    OCR_GPU: bool = True
    MIN_CONFIDENCE: float = 0.50

    # Resource Limits
    MAX_FILE_SIZE_MB: int = 5
    ALLOWED_IMAGE_EXTENSIONS: List[str] = ["jpg", "jpeg", "png"]
    MAX_IMAGE_RESOLUTION: int = 4096

    # Infrastructure
    TMP_DIR: str = "/tmp/ocr_service"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=True
    )

settings = Settings()
