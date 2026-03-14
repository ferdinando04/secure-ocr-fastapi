# 🪪 ID-OCR Extraction Base

API para la extracción de datos desde documentos de identidad (Cédulas, Identificaciones) con enfoque en América Latina (Colombia y región).

## 🚀 Propósito del Proyecto
Este repositorio proporciona una **base técnica funcional** para automatizar la lectura de identificaciones civiles. No es una solución mágica de "10/10", sino un pipeline de ingeniería sólido que utiliza:
- **EasyOCR**: Motor de reconocimiento de texto multi-lenguaje.
- **OpenCV**: Preprocesamiento de imagen para mejorar la legibilidad.
- **FastAPI**: Interfaz de API moderna y segura.

## 🎯 Capacidades Actuales (Verificadas)
- **Extracción Numérica**: Soporte verificado para números de documento de 8 a 10 dígitos (Formato Colombia y similares).
- **Detección de Texto**: Heurísticas básicas para identificar Nombres y Apellidos por bloques de texto.
- **Hardening de Seguridad**: Aislamiento por directorio temporal (`Request-ID`), validación de tipos MIME y límite de carga (5MB).

## 🛠️ Configuración y Uso

### Configuración (.env)
Configura tu acceso en el archivo `.env`:
```bash
API_KEY="clave_robusta_de_32_caracteres_minimo"
# NUNCA usar "*" en producción; define orígenes explícitos
ALLOWED_ORIGINS=["http://localhost:3000"]
```

### Ejecución (Docker)
```bash
docker build -t ocr-base .
docker run -p 8000:8000 --env-file .env ocr-base
```

## 📊 Especificación de Respuesta
El servicio devuelve datos estructurados con un score de confianza:
```json
{
  "success": true,
  "status": "processed",
  "data": {
    "cedula": { "value": "100200300", "confidence": 0.95 },
    "nombres": { "value": "JUAN PABLO", "confidence": 0.90 },
    "apellidos": { "value": "RODRIGUEZ", "confidence": 0.88 }
  },
  "confidence_score": 0.91,
  "process_time": 1.25
}
```

## ⚠️ Estado del Proyecto y Limitaciones
- **Nivel**: Beta / Base Adaptable.
- **Limitación**: El OCR puede fallar en documentos con fondos complejos o baja resolución. Se recomienda pre-recortar la imagen antes de subirla para maximizar precisión.
- **Garantía**: No hay garantía de precisión perfecta; se proporciona score de confianza para validación por parte del integrador.

---
*Mantenido como una herramienta de utilidad para desarrolladores e integradores.*
