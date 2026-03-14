import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import os
from app.api.main import app
from app.core.config import settings

client = TestClient(app)

def test_health_check_api():
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()

def test_unauthorized_extraction():
    # Sin API Key
    response = client.post(f"{settings.API_PREFIX}/extract")
    assert response.status_code == 401

@patch("app.api.main._ocr_engine")
def test_successful_general_id_extraction(mock_engine):
    # Mockeamos el servicio para un ID general (Colombia/Latam)
    mock_service = MagicMock()
    mock_service.extract_data.return_value = {
        "data": MagicMock(
            cedula=MagicMock(value="1000500600", confidence=0.99),
            nombres=MagicMock(value="PEDRO", confidence=0.9),
            apellidos=MagicMock(value="RODRIGUEZ", confidence=0.9),
            tipo="CEDULA"
        ),
        "average_confidence": 0.96,
        "warnings": []
    }
    mock_engine["service"] = mock_service
    
    # Pixel dummy
    pixel_jpg = b'\xff\xd8\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xd9'
    
    response = client.post(
        f"{settings.API_PREFIX}/extract",
        headers={"X-API-KEY": settings.API_KEY},
        files={"file": ("cedula.jpg", pixel_jpg, "image/jpeg")}
    )
    
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["data"]["cedula"]["value"] == "1000500600"
    assert res_json["status"] == "processed"

def test_payload_too_large_general():
    large_data = b"0" * (6 * 1024 * 1024) # 6MB
    response = client.post(
        f"{settings.API_PREFIX}/extract",
        headers={"X-API-KEY": settings.API_KEY},
        files={"file": ("too_big.jpg", large_data, "image/jpeg")}
    )
    assert response.status_code == 413
