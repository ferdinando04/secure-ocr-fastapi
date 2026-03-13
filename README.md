# 🇻🇪 OCR Extractor Venezolano - Secure & Production Ready

![FastAPI](https://img.shields.io/badge/FastAPI-0.109.2-009688?style=flat-square&logo=fastapi)
![EasyOCR](https://img.shields.io/badge/EasyOCR-1.7.1-orange?style=flat-square)
![Security](https://img.shields.io/badge/Security-Staff%20Level-red?style=flat-square)

Este repositorio contiene un servicio OCR de alto rendimiento y seguridad endurecida para la extracción de datos de Cédulas de Identidad venezolanas. Refactorizado bajo estándares de **Staff Engineering** y **AppSec**.

## 🏗️ Arquitectura y Diseño
El sistema sigue una arquitectura modular y desacoplada:
- **`app/api`**: Gestión de endpoints, seguridad (API Key) y aislamiento de recursos.
- **`app/services`**: Lógica de procesamiento de imágenes (OpenCV) y motor OCR (EasyOCR).
- **`app/core`**: Configuración inmutable mediante Pydantic Settings.
- **`app/models`**: Contratos de datos y validación de esquemas.

## 🛡️ Características de Seguridad (Hardening)
- **Aislamiento por Request**: Cada solicitud utiliza un directorio efímero (`Request-ID`) que se elimina tras el procesamiento, evitando persistencia de PII (Información Sensible).
- **Protección Anti-DoS**: Validación temprana de bytes (Magic Numbers), límites de tamaño (5MB) y restricciones de resolución para evitar ataques de descompresión.
- **Autenticación Fuerte**: Validación de `X-API-KEY` en tiempo constante para mitigar ataques de timing.
- **Logging Seguro**: Logs estructurados en JSON que omiten datos sensibles pero facilitan el monitoreo.

## 🚀 Despliegue

### 1. Variables de Entorno
Crea un archivo `.env` basado en `.env.example`:
```bash
API_KEY=tu_clave_secreta_aqui
ALLOWED_ORIGINS=["*"]
```

### 2. Ejecución con Docker (Recomendado)
El contenedor está configurado para ejecutarse como **usuario no-root** y con el sistema de archivos endurecido.
```bash
docker build -t ocr-secure .
docker run -p 8000:8000 --env-file .env ocr-secure
```

### 3. Ejecución Local
```bash
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate en Windows
pip install -r requirements.txt
uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

## 🧪 Pruebas
Ejecuta la suite de pruebas unitarias y de integración:
```bash
pytest tests/
```

## 🛠️ Tecnologías
- **FastAPI**: CORE del servicio.
- **OpenCV**: Preprocesamiento avanzado de imágenes.
- **EasyOCR**: Motor de IA para reconocimiento de texto.
- **Pydantic V2**: Validación de datos y configuraciones.

## 👨‍💻 Autor e Intervención
Originalmente creado por [Fabianqc](https://github.com/Fabianqc). Intervención de seguridad y arquitectura por **Antigravity AI**.
