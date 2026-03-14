try:
    import magic
    LIBMAGIC_AVAILABLE = True
except (ImportError, Exception):
    LIBMAGIC_AVAILABLE = False

from PIL import Image
from fastapi import HTTPException, status
from app.core.config import settings
from loguru import logger
from io import BytesIO

class ImageValidator:
    """
    Validaciones de seguridad para archivos de entrada.
    """
    @staticmethod
    def validate(file_content: bytes):
        # 1. Límite de Tamaño
        if len(file_content) > (settings.MAX_FILE_SIZE_MB * 1024 * 1024):
            raise HTTPException(
                status_code=status.HTTP_413_PAYLOAD_TOO_LARGE,
                detail=f"Archivo excede {settings.MAX_FILE_SIZE_MB}MB"
            )

        # 2. Deep MIME Check (Magic Bytes) - Fallback si libmagic no está
        if LIBMAGIC_AVAILABLE:
            try:
                mime = magic.Magic(mime=True)
                detected = mime.from_buffer(file_content)
                if not detected.startswith("image/"):
                    logger.error(f"Intento de subida de archivo no-imagen: {detected}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="El archivo no es una imagen válida."
                    )
            except Exception as e:
                logger.warning(f"Error en validación libmagic (usando fallback): {e}")
        else:
            logger.info("libmagic no disponible. Omitiendo validación nativa de MIME (Fallback a PIL).")

        # 3. Anti-Decompression Bomb
        try:
            with Image.open(BytesIO(file_content)) as img:
                w, h = img.size
                if w > settings.MAX_IMAGE_RESOLUTION or h > settings.MAX_IMAGE_RESOLUTION:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Resolución de imagen sospechosa detectada."
                    )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Imagen corrupta o inválida."
            )
        return True
