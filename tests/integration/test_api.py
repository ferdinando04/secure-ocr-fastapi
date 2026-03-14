import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import os
from app.api.main import app
from app.core.config import settings

client = TestClient(app)
app.state.limiter.enabled = False

# Mock global para evitar que EasyOCR intente cargar pesos/GPU en tests
patch("easyocr.Reader", autospec=True).start()

def test_health_check_api():
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()

def test_unauthorized_extraction():
    # Sin API Key
    response = client.post(f"{settings.API_PREFIX}/extract")
    assert response.status_code == 401

@patch("app.api.main._ocr_engine")
@patch("app.services.validators.Image.open")
def test_successful_colombia_10_digit_id(mock_pil, mock_engine):
    # Mock PIL para aceptar cualquier dummy data como válida
    mock_img = MagicMock()
    mock_img.size = (1000, 1000)
    mock_pil.return_value.__enter__.return_value = mock_img

    # Demostramos soporte real para IDs de 10 dígitos (Colombia)
    from app.models.ocr_models import OCRData, OCRField
    mock_service = MagicMock()
    mock_service.extract_data.return_value = {
        "data": OCRData(
            cedula=OCRField(value="1000200300", confidence=0.99),
            nombres=OCRField(value="CAMILO", confidence=0.95),
            apellidos=OCRField(value="RODRIGUEZ", confidence=0.92)
        ),
        "average_confidence": 0.95,
        "warnings": []
    }
    mock_engine.__getitem__.return_value = mock_service
    
    pixel_jpg = b'\xff\xd8\x00\x00' # Minimal dummy data
    
    response = client.post(
        f"{settings.API_PREFIX}/extract",
        headers={"X-API-KEY": settings.API_KEY},
        files={"file": ("cedula_col.jpg", pixel_jpg, "image/jpeg")}
    )
    
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["data"]["cedula"]["value"] == "1000200300"
    assert len(res_json["data"]["cedula"]["value"]) == 10

def test_payload_too_large_general():
    large_data = b"0" * (51 * 1024 * 100) # 5.1MB aproximadamente
    response = client.post(
        f"{settings.API_PREFIX}/extract",
        headers={"X-API-KEY": settings.API_KEY},
        files={"file": ("too_big.jpg", large_data, "image/jpeg")}
    )
    assert response.status_code == 413
