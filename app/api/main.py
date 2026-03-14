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

# Lazy loading container
_ocr_engine = {"service": None}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Inicialización de recursos pesados fuera del import global.
    """
    logger.info("Lifespan: Inicializando motor de reconocimiento ID-OCR...")
    try:
        import easyocr
        reader = easyocr.Reader(settings.OCR_LANGS, gpu=settings.OCR_GPU)
        _ocr_engine["service"] = OCRService(reader)
        logger.success("Motor OCR listo para procesamiento documental.")
    except Exception as e:
        logger.critical(f"Falla al iniciar motor OCR: {e}")
    yield
    logger.info("Lifespan: Apagando servicio.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API de Extracción Documental por OCR para Documentos de Identidad (Latam/General)",
    lifespan=lifespan
)

# Configuración de Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Seguro y pragmático
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["X-API-KEY", "Content-Type"],
)

@app.get("/health", tags=["Infrastructure"])
async def health():
    return {
        "status": "ready" if _ocr_engine["service"] else "starting",
        "version": settings.APP_VERSION,
        "engine": "EasyOCR"
    }

@app.post(
    f"{settings.API_PREFIX}/extract",
    response_model=OCRResponse,
    dependencies=[Depends(get_api_key)],
    tags=["OCR"]
)
@limiter.limit("10/minute")
async def extract(request: Request, file: UploadFile = File(...)):
    """
    Endpoint principal: Transforma una imagen de identificación en datos estructurados.
    """
    start_time = time.time()
    
    if not _ocr_engine["service"]:
        raise HTTPException(status_code=503, detail="Servicio OCR en proceso de arranque")

    content = await file.read()
    # Validación de seguridad y formato
    ImageValidator.validate(content)

    with request_scope_dir() as tmp_path:
        input_file = os.path.join(tmp_path, f"input_{int(time.time())}.jpg")
        with open(input_file, "wb") as f:
            f.write(content)

        try:
            result = _ocr_engine["service"].extract_data(input_file)
            duration = round(time.time() - start_time, 3)
            
            # Clasificación del resultado
            status_result = "processed"
            if result["average_confidence"] < 0.4:
                status_result = "suspicious"
            elif not result["data"].cedula.value:
                status_result = "partial"

            return OCRResponse(
                success=True,
                status=status_result,
                filename=file.filename,
                data=result["data"],
                confidence_score=round(result["average_confidence"], 2),
                process_time=duration,
                warnings=result["warnings"]
            )
        except Exception as e:
            logger.exception("Error en pipeline de procesamiento OCR")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo procesar el documento. Intente de nuevo o use una imagen más clara."
            )
