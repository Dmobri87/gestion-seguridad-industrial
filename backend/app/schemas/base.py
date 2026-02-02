from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class BaseSchema(BaseModel):
    """Schema base con configuración común."""
    model_config = ConfigDict(from_attributes=True)


class TimestampMixin(BaseModel):
    """Mixin para timestamps."""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaginationParams(BaseModel):
    """Parámetros de paginación."""
    page: int = 1
    page_size: int = 20

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """Respuesta paginada genérica."""
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


class MessageResponse(BaseModel):
    """Respuesta simple con mensaje."""
    message: str
    success: bool = True
