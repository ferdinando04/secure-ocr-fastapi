import cv2
import re
import numpy as np
import os
from loguru import logger
from app.models.ocr_models import OCRData, OCRField
from app.core.config import settings

class OCRService:
    """
    Servicio de Extracción Documental (Generic ID-OCR).
    Diseñado para extraer datos estructurados de documentos de identidadLatinoamericanos.
    """
    def __init__(self, reader):
        self.reader = reader
        # Patrones de ruido comunes en documentos de identidad (Latam)
        self.noise_patterns = [
            r'REPUBLICA', r'IDENTIDAD', r'DOCUMENTO', r'NACIONAL',
            r'NOMBRES?', r'APELLIDOS?', r'FECHA', r'NACIMIENTO',
            r'SEXO', r'ESTADO', r'CIVIL', r'NUMERO'
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
            raise ValueError("Error al cargar imagen.")

        results = self.reader.readtext(image_path, detail=1)
        
        if not results:
            return {
                "data": OCRData(),
                "average_confidence": 0.0,
                "warnings": ["No se detectó texto legible"]
            }

        confidences = [res[2] for res in results]
        avg_conf = sum(confidences) / len(confidences)
        data = self._smart_parse(results, avg_conf)
        
        return {
            "data": data,
            "average_confidence": avg_conf,
            "warnings": ["Imagen de baja calidad"] if avg_conf < 0.5 else []
        }

    def _smart_parse(self, ocr_results: list, avg_conf: float) -> OCRData:
        """
        Heurística de extracción por bloques de texto y patrones numéricos.
        Compatible con formatos de 8 a 10 dígitos (Colombia/Latam).
        """
        data = OCRData()
        lines = []
        for res in ocr_results:
            text = res[1].upper().strip()
            conf = res[2]
            # Limpieza básica de ruido
            is_noise = any(re.search(p, text) for p in self.noise_patterns)
            if not is_noise and len(text) > 2:
                lines.append({"text": text, "conf": conf, "box": res[0]})

        full_content = " ".join([l["text"] for l in lines])

        # 1. Extracción de Identificación (8-10 dígitos, con o sin puntos)
        # Soporta formatos colombianos (ex: 1.000.500.600 o 52.345.678)
        id_match = re.search(r'(\d{1,2}\.?\d{3}\.?\d{3}(?:\.?\d{3})?)', full_content)
        if id_match:
            clean_id = id_match.group(1).replace(".", "").strip()
            if 6 <= len(clean_id) <= 11:
                data.cedula = OCRField(value=clean_id, confidence=avg_conf)

        # 2. Extracción de Nombres y Apellidos
        # Basado en la detección de bloques de texto puro (sin números)
        text_only_blocks = [l for l in lines if not any(c.isdigit() for c in l["text"])]
        
        # Heurística: Los apellidos y nombres suelen ser los bloques de texto más prominentes
        if len(text_only_blocks) >= 2:
            data.apellidos = OCRField(value=text_only_blocks[0]["text"], confidence=text_only_blocks[0]["conf"])
            data.nombres = OCRField(value=text_only_blocks[1]["text"], confidence=text_only_blocks[1]["conf"])
        elif len(text_only_blocks) == 1:
            data.nombres = OCRField(value=text_only_blocks[0]["text"], confidence=text_only_blocks[0]["conf"])

        return data
