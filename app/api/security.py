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
    Valida la API Key usando comparación en tiempo constante.
    """
    if not secrets.compare_digest(api_key, settings.API_KEY):
        logger.warning("Falla de autenticación: API Key inválida.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de API inválidas"
        )
    return api_key

@contextmanager
def request_scope_dir():
    """
    Crea un directorio efímero para la request y garantiza su eliminación total (Cleanup).
    """
    req_id = str(uuid.uuid4())
    path = os.path.join(settings.TMP_DIR, f"req_{req_id}")
    os.makedirs(path, exist_ok=True)
    try:
        yield path
    finally:
        if os.path.exists(path):
            shutil.rmtree(path)
            logger.debug(f"PII Cleanup completado: {req_id}")
