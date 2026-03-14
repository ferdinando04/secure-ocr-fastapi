# 🪪 Secure ID-OCR API - Enterprise Grade

![FastAPI](https://img.shields.io/badge/FastAPI-0.109.2-009688?style=flat-square&logo=fastapi)
![Security](https://img.shields.io/badge/AppSec-Ready-red?style=flat-square)

API profesional para la extracción automatizada de datos desde Documentos de Identidad (Cédulas, IDs). Diseñada para integraciones de **Onboarding**, **KYC** y **Automatización Documental**.

## 🎯 Alcance del Producto
Este servicio está optimizado para documentos de identidad de América Latina (Colombia, Hispanoamérica) mediante:
- **Adaptative Parsing**: Heurísticas inteligentes que detectan nombres y números de identificación sin depender de una plantilla fija.
- **Image Hardening**: Preprocesamiento por OpenCV para maximizar la lectura en condiciones de baja iluminación.
- **Zero-Persistence PII**: Los datos sensibles nunca se almacenan permanentemente; se procesan en memoria o en volúmenes efímeros auto-limpiables.

## 🚀 Inicio Rápido

### Prerrequisitos
- Docker / Python 3.10+
- `libmagic` (Instalado automáticamente en el contenedor)

### Configuración
Configura tu acceso en `.env`:
```bash
API_KEY="clave_robusta_de_32_caracteres"
ALLOWED_ORIGINS=["http://localhost:3000"]
```

### Uso del API
Envía un POST al endpoint de extracción:
```bash
curl -X POST "http://localhost:8000/api/v1/extract" \
     -H "X-API-KEY: tu_clave" \
     -F "file=@mi_cedula.jpg"
```

## 📊 Especificación de Respuesta
```json
{
  "success": true,
  "status": "processed",
  "data": {
    "cedula": { "value": "100200300", "confidence": 0.98 },
    "nombres": { "value": "CAMILO ANDRES", "confidence": 0.95 },
    "apellidos": { "value": "RODRIGUEZ", "confidence": 0.92 }
  },
  "confidence_score": 0.95,
  "process_time": 1.45
}
```

## 🛡️ Seguridad y Resiliencia
- **Protección Anti-Dos**: Límites de resolución y peso (5MB).
- **MIME Validation**: Inspección profunda de cabeceras para prevenir ejecución de código.
- **Rate Limiting**: Control de abuso integrado.

---
*Desarrollado con estándares Principal Engineer para máxima utilidad y confiabilidad.*
