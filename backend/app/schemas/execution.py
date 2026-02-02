from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime, date
from typing import Optional, List


# ==========================================
# SCHEMAS LEGACY (mantener compatibilidad)
# ==========================================

class ExecutionCreate(BaseModel):
    """Schema para crear una ejecución nueva (legacy)"""
    activity_id: int
    observation: Optional[str] = None
    status: str = "Completado"


class ExecutionUpdate(BaseModel):
    """Schema para actualizar una ejecución existente (legacy)"""
    observation: Optional[str] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


class ExecutionOut(BaseModel):
    """Schema para devolver información de una ejecución (legacy)"""
    id: int
    activity_id: int
    user_id: int
    execution_date: datetime
    observation: Optional[str]
    status: str

    class Config:
        from_attributes = True


# ==========================================
# SCHEMAS NUEVOS (API v1)
# ==========================================

class ExecutionStatusEnum:
    COMPLETED = "Completado"
    PENDING = "Pendiente"
    WITH_NOVELTY = "Con Novedad"
    CANCELLED = "Cancelado"


class ApprovalStatusEnum:
    PENDING = "Pendiente"
    APPROVED = "Aprobado"
    REJECTED = "Rechazado"


# ==========================================
# EJECUCIÓN DE ACTIVIDADES
# ==========================================

class ActivityExecutionBase(BaseModel):
    """Schema base para ejecución de actividad."""
    execution_date: date
    cycle_number: int
    status: str = ExecutionStatusEnum.COMPLETED
    observation: Optional[str] = None
    novelty_description: Optional[str] = None
    location: Optional[str] = None
    quantity: int = 1

    @field_validator('cycle_number')
    @classmethod
    def validate_cycle(cls, v):
        if v < 1 or v > 4:
            raise ValueError('El ciclo debe estar entre 1 y 4')
        return v


class ActivityExecutionCreateV1(ActivityExecutionBase):
    """Schema para crear ejecución (API v1)."""
    planned_activity_id: int
    user_id: int
    organization_id: int


class ActivityExecutionUpdateV1(BaseModel):
    """Schema para actualizar ejecución (API v1)."""
    status: Optional[str] = None
    observation: Optional[str] = None
    novelty_description: Optional[str] = None
    location: Optional[str] = None
    quantity: Optional[int] = None


class ActivityExecutionResponse(ActivityExecutionBase):
    """Schema de respuesta para ejecución."""
    id: int
    planned_activity_id: int
    user_id: int
    execution_time: datetime
    approval_status: str
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    is_editable: bool
    edit_deadline: Optional[datetime] = None
    organization_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ActivityExecutionWithDetails(ActivityExecutionResponse):
    """Ejecución con detalles de actividad y usuario."""
    user_name: str
    activity_name: str
    activity_code: str
    category_name: str
    files_count: int = 0


# ==========================================
# ARCHIVOS DE EJECUCIÓN
# ==========================================

class ExecutionFileBase(BaseModel):
    """Schema base para archivo de ejecución."""
    file_name: str
    file_type: str
    file_url: str
    description: Optional[str] = None
    is_primary: bool = False


class ExecutionFileCreate(ExecutionFileBase):
    """Schema para crear archivo."""
    execution_id: int
    uploaded_by: int
    file_size: Optional[int] = None


class ExecutionFileResponse(ExecutionFileBase):
    """Schema de respuesta para archivo."""
    id: int
    execution_id: int
    file_size: Optional[int] = None
    created_at: datetime
    uploaded_by: int

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# APROBACIÓN
# ==========================================

class ExecutionApprovalRequest(BaseModel):
    """Schema para aprobar/rechazar ejecución."""
    approved: bool
    rejection_reason: Optional[str] = None


class ExecutionApprovalResponse(BaseModel):
    """Schema de respuesta de aprobación."""
    execution_id: int
    approval_status: str
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None


# ==========================================
# HISTORIAL
# ==========================================

class ExecutionHistoryResponse(BaseModel):
    """Schema de respuesta para historial."""
    id: int
    execution_id: int
    action: str
    field_changed: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    changed_by: int
    reason: Optional[str] = None
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# BULK OPERATIONS
# ==========================================

class BulkExecutionCreate(BaseModel):
    """Schema para crear múltiples ejecuciones."""
    executions: List[ActivityExecutionCreateV1]


class ExecutionWithFiles(ActivityExecutionWithDetails):
    """Ejecución con lista de archivos."""
    files: List[ExecutionFileResponse]
    history: List[ExecutionHistoryResponse]


# ==========================================
# ESTADÍSTICAS
# ==========================================

class ExecutionStats(BaseModel):
    """Estadísticas de ejecuciones."""
    total_executions: int
    completed: int
    pending: int
    with_novelty: int
    pending_approval: int
    approved: int
    rejected: int
