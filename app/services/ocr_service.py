import cv2
import easyocr
import re
import numpy as np
import os
from loguru import logger
from app.models.ocr_models import OCRData
from app.core.config import settings

class OCRService:
    """
    Servicio de procesamiento de imágenes y OCR optimizado para IDs de Venezuela.
    """
    def __init__(self, reader: easyocr.Reader):
        self.reader = reader
        self.blacklist_exact = [
            "JUAN CARLOS DUGARTE", "GUSTAVO VIZCAINO GIL", "ANABEL JIMENEZ", 
            "FABRICIO PEREZ MORON", "DANTE RIVAS", "GUSTAVO VIZCAINO",
            "JUAN DUGARTE", "JUAN DUGARIE", "JUAN DXGARRE", "ANABEL JIMÉNEZ", 
            "GUCTAVO VIRCAINO", "DIRECTORA", "DIRECTOR", "MINISTERIO",
            "REPUBLICA", "SAIME", "VENEZUELA", "BOLIVARIANA", "NOMIBRES","NOMBRES", 
            "NOMBRE", "NONBRES", "AOSRES", "AO;SRES", "NOSBRES", "NOM3RES", 
            "NOMERES", '"OUPRES', 'OUPRES',"APELLIDOS", "APELLIDO", "AFELLIDOS", 
            "APELUIDOS", "APELLID0S", "APELLID0", "APELLIDOS", "ACALLIOS", "KPELLDOS"
        ]
        self.labels_nombres = ["NOMBRES", "NOMBRE", "NONBRES", "AOSRES", "AO;SRES", "NOSBRES", "NOM3RES", "NOMERES", '"OUPRES', 'OUPRES',"NOMIBRES"]
        self.labels_apellidos = ["APELLIDOS", "APELLIDO", "AFELLIDOS", "APELUIDOS", "APELLID0S", "APELLID0", "APELLIDOS", "ACALLIOS", "KPELLDOS"]

    def extract_data(self, image_path: str) -> dict:
        """
        Flujo de procesamiento de imagen: Escaneo -> ROI -> OCR -> Parsing.
        No realiza escrituras en directorios fuera del scope efímero.
        """
        logger.info(f"Iniciando procesamiento OCR: {os.path.basename(image_path)}")
        
        img_raw = cv2.imread(image_path)
        if img_raw is None:
            raise ValueError(f"No se pudo cargar la imagen: {image_path}")

        # 1. Escáner documental y orientación
        warped = self._scan_document(img_raw)
        warped_oriented = self._correct_orientation(warped)
        
        # 2. Preparación de zona de datos (ROI)
        roi = self._isolate_data_zone(warped_oriented)
        
        # 3. Optimización para OCR
        processed_ocr_img = self._preprocess_for_ocr(roi)
        
        # 4. Reconocimiento de Texto
        results_raw = self.reader.readtext(
            processed_ocr_img, 
            detail=1, 
            mag_ratio=1.5, 
            contrast_ths=0.3, 
            adjust_contrast=0.7
        )
        
        # 5. Filtrado por confianza y parsing
        confidences = [res[2] for res in results_raw if len(res) > 2]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        valid_results = [res[1] for res in results_raw if res[2] >= settings.MIN_CONFIDENCE]
        
        data = self._parse_venezuelan_id(valid_results)
        
        return {
            "data": data,
            "average_confidence": avg_confidence,
            "warnings": [] if avg_confidence > 0.6 else ["Baja confianza en la lectura OCR"]
        }

    def _scan_document(self, img):
        ratio = img.shape[0] / 800.0
        resized = cv2.resize(img, (int(img.shape[1] / ratio), 800))
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        edged = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 75, 200)
        
        cnts, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]
        
        doc_cnt = None
        for c in cnts:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4:
                doc_cnt = approx
                break
        
        if doc_cnt is None:
            return img
            
        pts = doc_cnt.reshape(4, 2) * ratio
        rect = self._order_points(pts)
        (tl, tr, br, bl) = rect
        
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        
        dst = np.array([
            [0, 0], 
            [maxWidth-1, 0], 
            [maxWidth-1, maxHeight-1], 
            [0, maxHeight-1]
        ], dtype="float32")
        
        M = cv2.getPerspectiveTransform(rect, dst)
        return cv2.warpPerspective(img, M, (maxWidth, maxHeight))

    def _correct_orientation(self, img_plana):
        h, w = img_plana.shape[:2]
        if h > w:
            img_plana = cv2.rotate(img_plana, cv2.ROTATE_90_CLOCKWISE)
            h, w = img_plana.shape[:2]

        recorte_superior = img_plana[0:int(h * 0.35), 0:w]
        gris = cv2.cvtColor(recorte_superior, cv2.COLOR_BGR2GRAY)
        gris = cv2.adaptiveThreshold(gris, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        text_top = " ".join(self.reader.readtext(gris, detail=0)).upper()
        keywords = ["REPUBLICA", "BOLIVARIANA", "VENEZUELA", "CEDULA"]
        
        if not any(k in text_top for k in keywords):
            return cv2.rotate(img_plana, cv2.ROTATE_180)
        return img_plana

    def _isolate_data_zone(self, img):
        h, w = img.shape[:2]
        x_min, x_max = int(w * 0.10), int(w * 0.65)
        y_min, y_max = int(h * 0.15), h
        return img[y_min:y_max, x_min:x_max]

    def _preprocess_for_ocr(self, img):
        h, w = img.shape[:2]
        img_resized = cv2.resize(img, (w*4, h*4), interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)
        gaussian = cv2.GaussianBlur(gray, (0, 0), 2.0)
        return cv2.addWeighted(gray, 1.5, gaussian, -0.5, 0)

    def _parse_venezuelan_id(self, texts: list) -> OCRData:
        data = OCRData(Tipo="CEDULA")
        texts_up = [t.upper().strip() for t in texts]
        full_text = " ".join(texts_up)

        for t in texts_up:
            nums = re.sub(r'\D', '', t)
            if 6 <= len(nums) <= 9 and not data.Cedula:
                data.Cedula = f"{int(nums):,}".replace(",", ".")

        for i, t in enumerate(texts_up):
            if any(k in t for k in self.labels_nombres):
                if i + 1 < len(texts) and self._is_valid_titular(texts[i+1]):
                    data.Nombres = self._clean_value(texts[i+1])
            if any(k in t for k in self.labels_apellidos):
                if i + 1 < len(texts) and self._is_valid_titular(texts[i+1]):
                    data.Apellidos = self._clean_value(texts[i+1])

        if "SOLTER" in full_text: data.Estado_Civil = "SOLTERO/A"
        elif "CASAD" in full_text: data.Estado_Civil = "CASADO/A"
        if "VENEZOLAN" in full_text: data.Nacionalidad = "Venezolano/a"
        
        match_date = re.search(r'(\d{2})[^\d]{1,2}(\d{2})[^\d]{1,2}(\d{4})', full_text)
        if match_date:
            data.Fecha_Nacimiento = f"{match_date.group(1)}/{match_date.group(2)}/{match_date.group(3)}"

        return data

    def _is_valid_titular(self, txt):
        val = self._clean_value(txt)
        if not val or len(val) < 3: return False
        return not any(b in val for b in self.blacklist_exact)

    def _clean_value(self, txt):
        if not txt: return None
        t = txt.upper().replace("@", "A").replace("0", "O")
        t = re.sub(r'[^A-ZÁÉÍÓÚÑ ]', '', t)
        return t.strip()

    def _order_points(self, pts):
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect
