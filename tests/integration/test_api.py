import pytest
from fastapi.testclient import TestClient
from app.api.main import app
from app.core.config import settings

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_unauthorized_access():
    response = client.post(f"{settings.API_PREFIX}/extract", files={"file": ("test.jpg", b"fakecontent", "image/jpeg")})
    assert response.status_code == 401

def test_invalid_api_key():
    response = client.post(
        f"{settings.API_PREFIX}/extract", 
        headers={"X-API-KEY": "wrong-key"},
        files={"file": ("test.jpg", b"fakecontent", "image/jpeg")}
    )
    assert response.status_code == 401

def test_file_size_limit():
    # Simulamos un archivo de 6MB (el límite es 5MB)
    large_content = b"0" * (6 * 1024 * 1024)
    response = client.post(
        f"{settings.API_PREFIX}/extract",
        headers={"X-API-KEY": settings.API_KEY},
        files={"file": ("large.jpg", large_content, "image/jpeg")}
    )
    assert response.status_code == 413
