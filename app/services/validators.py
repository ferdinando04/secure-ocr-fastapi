import magic
from PIL import Image
from fastapi import HTTPException, status
from app.core.config import settings
from loguru import logger
from io import BytesIO

class ImageValidator:
    @staticmethod
    def validate(file_content: bytes):
        # 1. Validación de tamaño (Early Exit)
        size_mb = len(file_content) / (1024 * 1024)
        if size_mb > settings.MAX_FILE_SIZE_MB:
            logger.error(f"Falla de validación: Archivo muy grande ({size_mb:.2f}MB)")
            raise HTTPException(
                status_code=status.HTTP_413_PAYLOAD_TOO_LARGE,
                detail=f"Archivo excede el límite de {settings.MAX_FILE_SIZE_MB}MB"
            )

        # 2. Validación de Magic Bytes (Deep Inspection)
        mime = magic.Magic(mime=True)
        detected_type = mime.from_buffer(file_content)
        
        if not detected_type.startswith("image/"):
            logger.error(f"Falla de validación: Tipo de archivo inválido ({detected_type})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo enviado no es una imagen válida o está corrupto"
            )

        # 3. Prevención de Decompression Bombs
        try:
            with Image.open(BytesIO(file_content)) as img:
                w, h = img.size
                if w > settings.MAX_IMAGE_RESOLUTION or h > settings.MAX_IMAGE_RESOLUTION:
                    logger.error(f"Falla de seguridad: Resolución sospechosa ({w}x{h})")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Resolución de imagen sospechosamente alta. Posible ataque de denegación de servicio."
                    )
                # Opcional: Stripping de EXIF/Metadatos guardando en un nuevo buffer si se requiere persistencia
                return True
        except Exception as e:
            logger.error(f"Error procesando imagen: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La imagen no pudo ser decodificada."
            )
