import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import os
import shutil
from app.api.main import app
from app.core.config import settings

# Instancia de cliente de prueba
client = TestClient(app)

def test_health_check():
    """Valida el punto de conexión de salud del servicio."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_auth_missing_key():
    """Valida que se bloquee el acceso sin API Key."""
    response = client.post(f"{settings.API_PREFIX}/extract")
    assert response.status_code == 401

def test_auth_invalid_key():
    """Valida que se bloquee el acceso con API Key incorrecta."""
    response = client.post(
        f"{settings.API_PREFIX}/extract",
        headers={"X-API-KEY": "wrong-key"}
    )
    assert response.status_code == 401

def test_payload_too_large():
    """Valida límite de tamaño de archivo (Anti-DoS)."""
    large_data = b"0" * (settings.MAX_FILE_SIZE_MB * 1024 * 1024 + 1024)
    response = client.post(
        f"{settings.API_PREFIX}/extract",
        headers={"X-API-KEY": settings.API_KEY},
        files={"file": ("large.jpg", large_data, "image/jpeg")}
    )
    assert response.status_code == 413

def test_mime_spoofing_protection():
    """Valida protección contra archivos falsos (MIME Spoofing)."""
    bad_content = b"%PDF-1.4 - este no es un jpg"
    response = client.post(
        f"{settings.API_PREFIX}/extract",
        headers={"X-API-KEY": settings.API_KEY},
        files={"file": ("test.jpg", bad_content, "image/jpeg")}
    )
    assert response.status_code == 400
    assert "no es una imagen válida" in response.json()["detail"].lower()

@patch("app.api.main.ocr_service.extract_data")
def test_successful_extraction_flow_and_pii_cleanup(mock_extract):
    """Prueba de flujo exitoso con mocking y validación de cleanup de PII."""
    mock_extract.return_value = {
        "data": {"Cedula": "12345678", "Nombres": "JUAN"},
        "average_confidence": 0.9,
        "warnings": []
    }
    
    # Imagen minimalista real para pasar el validador PIL
    pixel_jpg = (
        b'\xff\xd8\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b'
        b'\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f'
        b'\'9=82<.342\xff\xd9'
    )
    
    response = client.post(
        f"{settings.API_PREFIX}/extract",
        headers={"X-API-KEY": settings.API_KEY},
        files={"file": ("pixel.jpg", pixel_jpg, "image/jpeg")}
    )
    
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Validación de Cleanup: No deben quedar rastros en TMP_DIR
    if os.path.exists(settings.TMP_DIR):
        assert len(os.listdir(settings.TMP_DIR)) == 0

@patch("app.api.main.ocr_service.extract_data")
def test_internal_error_no_leakage(mock_extract):
    """Valida que errores internos no filtren detalles técnicos al cliente."""
    mock_extract.side_effect = Exception("Database connection failed - Secret: 12345")
    
    pixel_jpg = b'\xff\xd8\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xd9'
    
    response = client.post(
        f"{settings.API_PREFIX}/extract",
        headers={"X-API-KEY": settings.API_KEY},
        files={"file": ("pixel.jpg", pixel_jpg, "image/jpeg")}
    )
    
    assert response.status_code == 500
    assert "error interno" in response.json()["detail"].lower()
    assert "secret" not in response.json()["detail"].lower()
