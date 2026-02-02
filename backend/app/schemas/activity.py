from pydantic import BaseModel
from typing import Optional

class ActivityCreate(BaseModel):
    """Schema para crear una actividad nueva"""
    name: str
    description: Optional[str] = None
    program_id: int


class ActivityUpdate(BaseModel):
    """
    Schema para actualizar una actividad existente.
    
    Todos los campos son opcionales para permitir actualizaciones parciales.
    Solo se actualizan los campos que se envíen en el JSON.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    program_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class ActivityOut(BaseModel):
    """Schema para devolver información de una actividad"""
    id: int
    name: str
    description: Optional[str] = None
    program_id: int

    class Config:
        from_attributes = True