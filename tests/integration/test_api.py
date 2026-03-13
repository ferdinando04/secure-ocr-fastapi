import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import os
import shutil
from app.api.main import app
from app.core.config import settings

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_unauthorized_access():
    response = client.post(
        f"{settings.API_PREFIX}/extract", 
        files={"file": ("test.jpg", b"fake", "image/jpeg")}
    )
    assert response.status_code == 401

def test_invalid_api_key():
    response = client.post(
        f"{settings.API_PREFIX}/extract",
        headers={"X-API-KEY": "bad-key"},
        files={"file": ("test.jpg", b"fake", "image/jpeg")}
    )
    assert response.status_code == 401

def test_file_size_limit():
    large_content = b"0" * (6 * 1024 * 1024)
    response = client.post(
        f"{settings.API_PREFIX}/extract",
        headers={"X-API-KEY": settings.API_KEY},
        files={"file": ("large.jpg", large_content, "image/jpeg")}
    )
    assert response.status_code == 413

def test_mime_spoofing():
    # Enviamos un texto pero decimos que es JPEG
    fake_image_content = b"THIS IS NOT AN IMAGE"
    response = client.post(
        f"{settings.API_PREFIX}/extract",
        headers={"X-API-KEY": settings.API_KEY},
        files={"file": ("test.jpg", fake_image_content, "image/jpeg")}
    )
    assert response.status_code == 400
    assert "no es una imagen válida" in response.json()["detail"]

@patch("app.api.main.ocr_service.extract_data")
def test_successful_extraction_and_cleanup(mock_extract):
    # Mock de respuesta exitosa
    mock_extract.return_value = {
        "data": {
            "Cedula": "12.345.678",
            "Nombres": "JUAN",
            "Apellidos": "PEREZ",
            "Tipo": "CEDULA"
        },
        "average_confidence": 0.95,
        "warnings": []
    }

    # Necesitamos una imagen real pequeña para pasar la validación de PIL y Magic
    # O mockear el validador. Preferimos usar un pixel real base64 compilado
    pixel_jpg = (
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06'
        b'\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a'
        b'\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00'
        b'\x01\x00\x01\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01'
        b'\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b'
        b'\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02'
        b'\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0'
        b'$3br\x82\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86'
        b'\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa'
        b'\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5'
        b'\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7'
        b'\xf8\xf9\xfa\xff\xc4\x00\x1f\x01\x00\x03\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00'
        b'\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x11\x00\x02\x01\x02'
        b'\x04\x04\x03\x04\x07\x05\x04\x04\x00\x01\x02w\x00\x01\x02\x03\x11\x04\x05!1\x06\x12AQ\x07'
        b'aq\x13"2\x81\x08\x14B\x91\xa1\xb1\xc1\t#3R\xd1\xf0\x15$4br\x82\x16\x17\x18\x19\x1a%&\'()*'
        b'56789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95'
        b'\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9'
        b'\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3'
        b'\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x0c\x03'
        b'\x01\x00\x02\x11\x03\x11\x00?\x00\xf7\xfa\x28\xa2\x8a\xff\xd9'
    )

    response = client.post(
        f"{settings.API_PREFIX}/extract",
        headers={"X-API-KEY": settings.API_KEY},
        files={"file": ("pixel.jpg", pixel_jpg, "image/jpeg")}
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["Cedula"] == "12.345.678"

    # Verificar que el directorio temporal de la request ya no existe
    # El ID es dinámico, chequeamos que TMP_DIR solo tenga directorios vacíos o ninguno
    # (En tests secuenciales TMP_DIR debería estar limpio al final)
    if os.path.exists(settings.TMP_DIR):
        contents = os.listdir(settings.TMP_DIR)
        # No debería haber carpetas 'req_...' residuales
        assert not any(c.startswith("req_") for c in contents)

@patch("app.api.main.ocr_service.extract_data")
def test_internal_error_handling(mock_extract):
    mock_extract.side_effect = Exception("OCR Engine Crash")
    
    # Imagen minimal para pasar validación
    pixel_jpg = b'\xff\xd8\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xd9'

    response = client.post(
        f"{settings.API_PREFIX}/extract",
        headers={"X-API-KEY": settings.API_KEY},
        files={"file": ("fail.jpg", pixel_jpg, "image/jpeg")}
    )

    assert response.status_code == 500
    assert "error interno" in response.json()["detail"].lower()
