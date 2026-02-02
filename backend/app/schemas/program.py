from pydantic import BaseModel
from typing import Optional

class ProgramCreate(BaseModel):
    """Schema para crear un programa nuevo"""
    name: str
    description: Optional[str] = None
    coordinator_id: int


class ProgramUpdate(BaseModel):
    """
    Schema para actualizar un programa existente.
    
    Todos los campos son opcionales para permitir actualizaciones parciales.
    Solo se actualizan los campos que se envíen en el JSON.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    coordinator_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class ProgramOut(BaseModel):
    """Schema para devolver información de un programa"""
    id: int
    name: str
    description: Optional[str] = None
    coordinator_id: int

    class Config:
        from_attributes = True