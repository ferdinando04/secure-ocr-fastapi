from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from app.core.config import settings
import secrets
import os
import shutil
import uuid
from loguru import logger
from contextlib import contextmanager

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=True)

async def get_api_key(api_key: str = Security(api_key_header)):
    """
    Validación de API Key en tiempo constante para mitigar ataques de timing.
    """
    if not secrets.compare_digest(api_key, settings.API_KEY):
        logger.warning("Intento de acceso con API Key inválida.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de API inválidas"
        )
    return api_key

@contextmanager
def request_scope_dir():
    """
    Context Manager para asegurar aislamiento y limpieza de archivos sensibles.
    Cada request genera un ID único y su propio espacio en /tmp.
    """
    req_id = str(uuid.uuid4())
    path = os.path.join(settings.TMP_DIR, f"req_{req_id}")
    os.makedirs(path, exist_ok=True)
    
    try:
        logger.debug(f"Espacio efímero creado: {path}")
        yield path
    finally:
        # Garantía absoluta de borrado de PII al finalizar la request
        if os.path.exists(path):
            shutil.rmtree(path)
            logger.debug(f"Limpieza de PII completada para request {req_id}")
