import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import os
from app.api.main import app
from app.core.config import settings

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in ["ready", "starting"]

def test_auth_missing_key():
    response = client.post(f"{settings.API_PREFIX}/extract")
    assert response.status_code == 401

@patch("app.api.main._ocr_engine")
def test_successful_extraction_flow_v2(mock_engine):
    # Mockeamos el motor OCR para evitar carga pesada
    mock_service = MagicMock()
    mock_service.extract_data.return_value = {
        "data": MagicMock(
            cedula=MagicMock(value="12345678", confidence=0.99),
            nombres=MagicMock(value="JUAN", confidence=0.9),
            apellidos=MagicMock(value="PEREZ", confidence=0.9),
            tipo="CEDULA"
        ),
        "average_confidence": 0.95,
        "warnings": []
    }
    # Simulamos que el motor está listo
    mock_engine["service"] = mock_service
    
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
    json_data = response.json()
    assert json_data["success"] is True
    assert "process_time" in json_data
    assert json_data["data"]["cedula"]["value"] == "12345678"
    assert json_data["confidence_score"] == 0.95

def test_mime_spoofing():
    bad_content = b"PDF-1.4 Fake Document"
    response = client.post(
        f"{settings.API_PREFIX}/extract",
        headers={"X-API-KEY": settings.API_KEY},
        files={"file": ("test.jpg", bad_content, "image/jpeg")}
    )
    assert response.status_code == 400
