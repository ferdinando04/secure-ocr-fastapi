from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from loguru import logger
import shutil
import os
import time
import easyocr

from app.core.config import settings
from app.api.security import get_api_key, request_scope_dir
from app.services.ocr_service import OCRService
from app.services.validators import ImageValidator
from app.models.ocr_models import OCRResponse

# Configuración de Logs Estructurados
logger.add(
    "logs/ocr_service.log", 
    rotation="10 MB", 
    serialize=True, 
    level=settings.LOG_LEVEL
)

# Inicializar Limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Servicio OCR Profesional para Cédulas Venezolanas - Hardened Version"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Seguro
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["X-API-KEY", "Content-Type"],
)

# Singleton del motor OCR
logger.info("Cargando motor EasyOCR en memoria...")
reader = easyocr.Reader(settings.OCR_LANGS, gpu=settings.OCR_GPU)
ocr_service = OCRService(reader)
logger.success("Motor Listo.")

@app.get("/health", tags=["Infraestructure"])
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION, "timestamp": time.time()}

@app.post(
    f"{settings.API_PREFIX}/extract",
    response_model=OCRResponse,
    dependencies=[Depends(get_api_key)],
    tags=["OCR"]
)
@limiter.limit("5/minute")
async def extract_id_data(file: UploadFile = File(...)):
    start_time = time.time()
    logger.info(f"Recibida solicitud para: {file.filename}")
    
    # 1. Leer contenido en memoria una sola vez
    content = await file.read()
    
    # 2. Validación de Seguridad (Early Exit)
    ImageValidator.validate(content)
    
    # 3. Procesamiento en aislamiento
    with request_scope_dir() as tmp_path:
        # Guardar solo en el directorio efímero
        input_path = os.path.join(tmp_path, "input_image.jpg")
        with open(input_path, "wb") as f:
            f.write(content)
            
        try:
            extraction = ocr_service.extract_data(input_path)
            
            process_time = time.time() - start_time
            logger.info(f"Extracción exitosa en {process_time:.2f}s")
            
            return OCRResponse(
                success=True,
                filename=file.filename,
                data=extraction["data"],
                confidence_score=extraction["average_confidence"],
                warnings=extraction["warnings"]
            )
            
        except Exception as e:
            logger.exception(f"Error crítico procesando {file.filename}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ocurrió un error interno al procesar el documento."
            )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
