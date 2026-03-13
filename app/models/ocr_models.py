from pydantic import BaseModel, Field
from typing import Optional, List

class OCRData(BaseModel):
    Cedula: Optional[str] = None
    Nombres: Optional[str] = None
    Apellidos: Optional[str] = None
    Fecha_Nacimiento: Optional[str] = None
    Estado_Civil: Optional[str] = None
    Nacionalidad: Optional[str] = None
    Tipo: str = "DESCONOCIDO"

class OCRResponse(BaseModel):
    success: bool
    filename: str
    data: OCRData
    confidence_score: float = Field(..., ge=0, le=1.0)
    warnings: List[str] = []
