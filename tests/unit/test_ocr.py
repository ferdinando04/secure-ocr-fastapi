import pytest
from app.services.ocr_service import OCRService
from app.models.ocr_models import OCRData

def test_parse_venezuelan_id_basic():
    # Mocking Service with dummy reader
    service = OCRService(reader=None)
    texts = ["REPUBLICA BOLIVARIANA", "CEDULA DE IDENTIDAD", "V-12345678", "APELLIDOS", "PEREZ", "NOMBRES", "JUAN", "VENEZOLANO", "FECHA NAC 01-01-1990"]
    
    data = service._parse_venezuelan_id(texts)
    
    assert data.Cedula == "12.345.678"
    assert data.Nombres == "JUAN"
    assert data.Apellidos == "PEREZ"
    assert data.Nacionalidad == "Venezolano/a"
    assert data.Fecha_Nacimiento == "01/01/1990"

def test_is_valid_titular_blacklist():
    service = OCRService(reader=None)
    assert service._is_valid_titular("JUAN PEREZ") is True
    assert service._is_valid_titular("GUSTAVO VIZCAINO") is False
    assert service._is_valid_titular("DIRECTOR") is False
