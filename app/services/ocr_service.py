import cv2
import re
import numpy as np
import os
from loguru import logger
from app.models.ocr_models import OCRData, OCRField
from app.core.config import settings

class OCRService:
    """
    Servicio de Extracción Documental (General ID OCR).
    Especializado en Documentos de Identidad Latinoamericanos.
    """
    def __init__(self, reader):
        self.reader = reader
        # Patrones de ruido genéricos presentes en documentos de identidad
        self.noise_patterns = [
            r'REPUBLICA', r'IDENTIDAD', r'CEDULA', r'DOCUMENTO', 
            r'NACIONAL', r'NOMBRES?', r'APELLIDOS?', r'FECHA', 
            r'NACIMIENTO', r'SEXO', r'ESTADO', r'CIVIL', r'NUMERO'
        ]

    def _preprocess_image(self, image_path: str):
        img = cv2.imread(image_path)
        if img is None:
            return None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        return thresh

    def extract_data(self, image_path: str) -> dict:
        processed_img = self._preprocess_image(image_path)
        if processed_img is None:
            raise ValueError("Error de carga de imagen.")

        results = self.reader.readtext(image_path, detail=1)
        
        if not results:
            return {
                "data": OCRData(),
                "average_confidence": 0.0,
                "warnings": ["Sin texto detectable"]
            }

        confidences = [res[2] for res in results]
        avg_conf = sum(confidences) / len(confidences)
        data = self._smart_parse(results)
        
        return {
            "data": data,
            "average_confidence": avg_conf,
            "warnings": ["Confianza baja"] if avg_conf < 0.5 else []
        }

    def _smart_parse(self, ocr_results: list) -> OCRData:
        """
        Heurística adaptable para documentos de identidad (Latam/Colombia).
        """
        data = OCRData()
        lines = []
        for res in ocr_results:
            text = res[1].upper().strip()
            conf = res[2]
            is_noise = any(re.search(p, text) for p in self.noise_patterns)
            if not is_noise and len(text) > 2:
                lines.append({"text": text, "conf": conf, "box": res[0]})

        full_text = " ".join([l["text"] for l in lines])

        # 1. Identificación Numérica (8-10 dígitos común en Colombia/Latam)
        id_match = re.search(r'(\d{1,2}\.?\d{3}\.?\d{3})', full_text)
        if id_match:
            clean_id = id_match.group(1).replace(".", "").strip()
            if 6 <= len(clean_id) <= 10:
                data.cedula = OCRField(value=clean_id, confidence=id_match.group(0).count('.')*0.1 + 0.8) # Heurística de confianza base

        # 2. Extracción de Nombres/Apellidos (Lógica de Bloques)
        # Buscamos las líneas de texto puras más largas que no contienen números
        text_blobs = [l for l in lines if not any(c.isdigit() for c in l["text"])]
        
        # En la mayoría de IDs, los nombres/apellidos forman los bloques de texto más claros
        if len(text_blobs) >= 2:
            data.apellidos = OCRField(value=text_blobs[0]["text"], confidence=text_blobs[0]["conf"])
            data.nombres = OCRField(value=text_blobs[1]["text"], confidence=text_blobs[1]["conf"])
        elif len(text_blobs) == 1:
            data.nombres = OCRField(value=text_blobs[0]["text"], confidence=text_blobs[0]["conf"])

        return data
