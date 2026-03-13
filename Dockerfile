# FASE 1: Builder
FROM python:3.10-slim as builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# FASE 2: Producción
FROM python:3.10-slim

# Evitar que python genere archivos .pyc y forzar salida sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TMP_DIR=/tmp/ocr_service

# Instalar dependencias del sistema necesarias para OpenCV y EasyOCR
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no root
RUN useradd -m -u 10001 appuser
USER appuser

# Copiar dependencias instaladas del builder
COPY --from=builder /home/appuser/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

WORKDIR /app
COPY --chown=appuser:appuser . .

# Asegurar que el directorio temporal exista y tenga permisos
RUN mkdir -p /tmp/ocr_service && chmod 700 /tmp/ocr_service

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
