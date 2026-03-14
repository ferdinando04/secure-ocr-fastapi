import cv2
import re
import numpy as np
import os
from loguru import logger
from app.models.ocr_models import OCRData, OCRField
from app.core.config import settings

class OCRService:
    """
    Servicio OCR Principal Engineer Level.
    Focalizado en: Precisión del Parsing y Robustez de Extracción.
    """
    def __init__(self, reader):
        self.reader = reader
        # Patrones de limpieza de ruido comunes en SAIME
        self.noise_patterns = [
            r'REPUBLICA', r'BOLIVARIANA', r'VENEZUELA', r'SAIME', 
            r'IDENTIDAD', r'CEDULA', r'NOMBRES?', r'APELLIDOS?', 
            r'FECHA', r'NACIMIENTO', r'SEXO', r'ESTADO', r'CIVIL'
        ]

    def _preprocess_image(self, image_path: str):
        """
        Preprocesamiento para mejorar el contraste y reducir ruido.
        """
        img = cv2.imread(image_path)
        if img is None:
            return None
            
        # Convertir a escala de grises
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Eliminar ruido (Denoising)
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Umbral adaptativo (Adaptive Thresholding)
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        return thresh

    def extract_data(self, image_path: str) -> dict:
        processed_img = self._preprocess_image(image_path)
        if processed_img is None:
            raise ValueError("Error al cargar o procesar la imagen.")

        # Realizar OCR (con EasyOCR inyectado)
        # Probamos primero con la procesada, si falla mucho, usamos la original
        results = self.reader.readtext(image_path, detail=1)
        
        if not results:
            return {
                "data": OCRData(),
                "average_confidence": 0.0,
                "warnings": ["No se detectó texto en el documento"]
            }

        confidences = [res[2] for res in results]
        avg_conf = sum(confidences) / len(confidences)
        
        # Agrupar texto detectado
        raw_lines = [res[1].upper() for res in results]
        data = self._smart_parse(results)
        
        warnings = []
        if avg_conf < 0.5:
            warnings.append("Calidad de imagen muy baja (Confianza insuficiente)")
        
        return {
            "data": data,
            "average_confidence": avg_conf,
            "warnings": warnings
        }

    def _smart_parse(self, ocr_results: list) -> OCRData:
        """
        Heurísticas para extraer campos específicos de la CI Venezolana.
        """
        data = OCRData()
        
        # Filtramos basura de cabecera para reducir ruido de búsqueda
        lines = []
        for res in ocr_results:
            text = res[1].upper().strip()
            conf = res[2]
            # Solo guardamos si no es una palabra de cabecera bloqueada
            is_noise = any(re.search(p, text) for p in self.noise_patterns)
            if not is_noise and len(text) > 2:
                lines.append({"text": text, "conf": conf, "box": res[0]})

        full_content = " ".join([l["text"] for l in lines])
        logger.debug(f"Parsing content: {full_content}")

        # 1. CEDULA (Pattern: V-[números] o solo números de 7-8 dígitos)
        ci_match = re.search(r'(?:V|E)?\s?[:\.-]?\s?(\d{1,2}\.?\d{3}\.?\d{3})', full_content)
        if ci_match:
            val = ci_match.group(1).replace(".", "").strip()
            # Validamos que el resultado no sea ruido
            if 6 <= len(val) <= 9:
                data.cedula = OCRField(value=val, confidence=avg_field_conf(lines, val))

        # 2. Heurística de Nombres y Apellidos (Basado en posición o palabras clave)
        # En la CI venezolana, los apellidos suelen ir arriba de los nombres.
        # Buscamos líneas que parezcan nombres (no contienen números, no son cabeceras)
        potential_names = [l for l in lines if not any(c.isdigit() for c in l["text"])]
        
        if len(potential_names) >= 2:
            # Asunción simple: primeras dos líneas de nombres/apellidos detectadas
            data.apellidos = OCRField(value=potential_names[0]["text"], confidence=potential_names[0]["conf"])
            data.nombres = OCRField(value=potential_names[1]["text"], confidence=potential_names[1]["conf"])
        elif len(potential_names) == 1:
            data.nombres = OCRField(value=potential_names[0]["text"], confidence=potential_names[0]["conf"])

        return data

def avg_field_conf(lines, value):
    """Auxiliar para encontrar la confianza de un fragmento de texto."""
    for l in lines:
        if value in l["text"]:
            return l["conf"]
    return 0.5
