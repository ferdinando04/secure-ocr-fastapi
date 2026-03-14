from pydantic import BaseModel, Field
from typing import Optional, List

class OCRField(BaseModel):
    value: Optional[str] = None
    confidence: float = 0.0

class OCRData(BaseModel):
    cedula: OCRField = Field(default_factory=OCRField)
    nombres: OCRField = Field(default_factory=OCRField)
    apellidos: OCRField = Field(default_factory=OCRField)
    fecha_nacimiento: OCRField = Field(default_factory=OCRField)
    estado_civil: OCRField = Field(default_factory=OCRField)
    tipo: str = "CEDULA"

class OCRResponse(BaseModel):
    success: bool
    status: str = "processed" # processed, partial, failed, suspicious
    filename: str
    data: Optional[OCRData] = None
    confidence_score: float = 0.0
    process_time: float = 0.0
    warnings: List[str] = []
