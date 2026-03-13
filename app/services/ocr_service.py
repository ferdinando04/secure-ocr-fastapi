import cv2
import re
import numpy as np
import os
from loguru import logger
from app.models.ocr_models import OCRData
from app.core.config import settings

class OCRService:
    """
    Servicio OCR especializado en IDs venezolanos.
    Usa un objeto reader inyectado para evitar acoplamiento global.
    """
    def __init__(self, reader):
        self.reader = reader
        self.blacklist = ["REPUBLICA", "BOLIVARIANA", "VENEZUELA", "SAIME", "DIRECTOR"]

    def extract_data(self, image_path: str) -> dict:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Imagen ilegible.")

        # Pre-procesamiento y OCR
        results = self.reader.readtext(img, detail=1)
        
        confidences = [res[2] for res in results]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0
        texts = [res[1] for res in results if res[2] >= settings.MIN_CONFIDENCE]
        
        data = self._parse_data(texts)
        
        return {
            "data": data,
            "average_confidence": avg_conf,
            "warnings": ["Baja confianza"] if avg_conf < 0.6 else []
        }

    def _parse_data(self, texts: list) -> OCRData:
        # Lógica de parsing simplificada para el repo profesional
        data = OCRData()
        full_text = " ".join([t.upper() for t in texts])
        
        # Ejemplo de extracción de cédula
        match_ci = re.search(r'V?\-?\s?(\d{6,9})', full_text)
        if match_ci:
            data.Cedula = match_ci.group(1)
            
        return data
