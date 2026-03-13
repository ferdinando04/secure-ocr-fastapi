import pytest
from app.services.ocr_service import OCRService

def test_ocr_data_parsing_basic():
    """Valida la lógica de parsing sin dependencias pesadas."""
    service = OCRService(reader=None)
    texts = ["HOLA", "CEDULA", "12345678", "VEN", "JUAN"]
    data = service._parse_data(texts)
    assert data.Cedula == "12345678"
