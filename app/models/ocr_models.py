from pydantic import BaseModel, Field
from typing import Optional, List

class OCRData(BaseModel):
    Cedula: Optional[str] = None
    Nombres: Optional[str] = None
    Apellidos: Optional[str] = None
    Tipo: str = "CEDULA"

class OCRResponse(BaseModel):
    success: bool
    filename: str
    data: Optional[OCRData] = None
    confidence_score: float
    process_time: float
    warnings: List[str] = []
