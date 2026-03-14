# 🇻🇪 OCR Extractor Venezolano Elite - Principal Level

![FastAPI](https://img.shields.io/badge/FastAPI-0.109.2-009688?style=flat-square&logo=fastapi)
![EasyOCR](https://img.shields.io/badge/EasyOCR-1.7.2-orange?style=flat-square)
![Docs](https://img.shields.io/badge/API-Swagger-blue?style=flat-square)

API profesional diseñada para la extracción de datos de Cédulas de Identidad venezolanas. Focalizada en la **utilidad del dato**, la **facilidad de integración** y una **seguridad pragmática** de grado producción.

## 🚀 Propuesta de Valor
A diferencia de OCRs genéricos, este servicio incluye:
- **Heurísticas Específicas**: Optimizado para la estructura del SAIME (Nombres, Apellidos, Cédula).
- **Preprocesamiento OpenCV**: Mejora automática de contraste y reducción de ruido antes del OCR.
- **Modelo de Respuesta Rico**: Confianza por campo y tiempos de procesamiento para optimizar la experiencia del usuario final.
- **Aislamiento de Seguridad**: Limpieza automática de datos sensibles tras cada procesamiento.

## 🛠️ Configuración de Inicio Rápido

### 1. Preparar el entorno
Crea tu archivo `.env`:
```bash
API_KEY="tu_clave_de_32_caracteres_minimo"
# Lista explícita de orígenes permitidos (CORS)
ALLOWED_ORIGINS=["http://localhost:3000", "https://tuapp.com"]
```

### 2. Ejecutar con Docker (Recomendado)
```bash
docker build -t ocr-elite .
docker run -p 8000:8000 --env-file .env ocr-elite
```

### 3. Integración Básica (Ejemplo Python)
```python
import requests

url = "http://localhost:8000/api/v1/extract"
headers = {"X-API-KEY": "tu_clave_aqui"}
files = {"file": open("cedula.jpg", "rb")}

response = requests.post(url, headers=headers, files=files)
print(response.json())
```

## 📊 Modelo de Respuesta
El servicio no solo devuelve texto, sino datos estructurados útiles para tu lógica de negocio:
```json
{
  "success": true,
  "status": "processed",
  "data": {
    "cedula": { "value": "12345678", "confidence": 0.99 },
    "nombres": { "value": "PEDRO PABLO", "confidence": 0.85 },
    "apellidos": { "value": "PEREZ", "confidence": 0.91 }
  },
  "confidence_score": 0.92,
  "process_time": 1.23,
  "warnings": []
}
```

## 🧪 Calidad y Testing
Probado rigurosamente contra:
- **MIME Spoofing**: Protección contra archivos falsos.
- **Resource Limits**: Límites de resolución y peso para evitar DoS.
- **Eficacia Extraccción**: Pruebas de parsing de campos venezolano.

Para ejecutar tests locales:
```bash
pytest tests/
```

---
*Intervención de ingeniería por Antigravity AI - Enfocada en Producto y Utilidad.*
