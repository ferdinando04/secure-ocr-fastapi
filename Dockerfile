# FASE 1: Builder
FROM python:3.10-slim as builder

WORKDIR /build

# Instalar dependencias necesarias para compilar/instalar (si hubiera)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Install to a specific local path to avoid permission issues and simplify copy
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# FASE 2: Producción
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TMP_DIR=/tmp/ocr_service
ENV PYTHONPATH=/app

# Instalar dependencias de runtime y curl para healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no root y directorio temporal
RUN useradd -m -u 10001 appuser && \
    mkdir -p /tmp/ocr_service && \
    chmod 700 /tmp/ocr_service && \
    chown appuser:appuser /tmp/ocr_service

# Copiar dependencias del builder
COPY --from=builder /install /usr/local

WORKDIR /app
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

# Healthcheck usando curl al endpoint seguro de la app
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
