from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class OCRData(BaseModel):
    Cedula: Optional[str] = None
    Nombres: Optional[str] = None
    Apellidos: Optional[str] = None
    Fecha_Nacimiento: Optional[str] = None
    Estado_Civil: Optional[str] = None
    Nacionalidad: Optional[str] = None
    Tipo: str = "CEDULA"

    model_config = ConfigDict(populate_by_name=True)

class OCRResponse(BaseModel):
    success: bool
    filename: str
    data: Optional[OCRData] = None
    confidence_score: float
    warnings: List[str] = []
