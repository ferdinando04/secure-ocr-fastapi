from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from loguru import logger
import os
import time
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.security import get_api_key, request_scope_dir
from app.services.ocr_service import OCRService
from app.services.validators import ImageValidator
from app.models.ocr_models import OCRResponse

# Pre-crear directorios necesarios
os.makedirs("logs", exist_ok=True)
os.makedirs(settings.TMP_DIR, exist_ok=True)

# Configuración de Logs Estructurados
logger.add(
    "logs/ocr_service.log",
    rotation="10 MB",
    serialize=True,
    level=settings.LOG_LEVEL
)

# Inicializar Limiter
limiter = Limiter(key_func=get_remote_address)

# OCR Service Placeholder (Lazy init en lifespan)
ocr_service: OCRService = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida: Carga el motor OCR al arrancar el servicio.
    Esto desacopla la inicialización pesada de los imports globales.
    """
    global ocr_service
    logger.info("Inicializando motor EasyOCR (Lifespan)...")
    try:
        import easyocr
        reader = easyocr.Reader(settings.OCR_LANGS, gpu=settings.OCR_GPU)
        ocr_service = OCRService(reader)
        logger.success("Motor OCR cargado satisfactoriamente.")
    except Exception as e:
        logger.critical(f"Falla catastrófica cargando EasyOCR: {e}")
        raise e
    yield
    logger.info("Apagando servicio OCR...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Servicio OCR Profesional - Versión Endurecida Staff Level",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS: Configuración coherente y segura
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["X-API-KEY", "Content-Type"],
)

@app.get("/health", tags=["Infrastructure"])
async def health_check():
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "timestamp": time.time(),
        "gpu": settings.OCR_GPU,
        "engine_ready": ocr_service is not None
    }

@app.post(
    f"{settings.API_PREFIX}/extract",
    response_model=OCRResponse,
    dependencies=[Depends(get_api_key)],
    tags=["OCR"]
)
@limiter.limit("5/minute")
async def extract_id_data(request: Request, file: UploadFile = File(...)):
    """
    Endpoint principal para extracción de datos de Cédula.
    Requiere X-API-KEY válida y sigue política de aislamiento efímero.
    """
    start_time = time.time()
    logger.info(f"Procesando archivo: {file.filename}")

    # 1. Validación de Seguridad Temprana (En memoria)
    content = await file.read()
    ImageValidator.validate(content)

    # 2. Procesamiento en aislamiento del Sistema de Archivos
    with request_scope_dir() as tmp_path:
        input_path = os.path.join(tmp_path, "input_image.jpg")
        with open(input_path, "wb") as f:
            f.write(content)

        try:
            if ocr_service is None:
                raise RuntimeError("El motor OCR no ha sido inicializado.")
            
            extraction = ocr_service.extract_data(input_path)
            
            return OCRResponse(
                success=True,
                filename=file.filename,
                data=extraction["data"],
                confidence_score=extraction["average_confidence"],
                warnings=extraction["warnings"],
                process_time=time.time() - start_time
            )

        except Exception as e:
            logger.exception(f"Error interno procesando {file.filename}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ocurrió un error interno al procesar el documento. No se revelaron detalles sensibles."
            )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
