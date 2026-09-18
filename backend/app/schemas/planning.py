from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime, date
from typing import Optional, List
from app.models.planning import PlanStatus


# ==========================================
# CATEGORÍAS DE ACTIVIDADES
# ==========================================

class ActivityCategoryBase(BaseModel):
    """Schema base para categoría de actividades."""
    name: str
    code: str
    description: Optional[str] = None
    display_order: int = 0
    color: str = "#1890ff"
    icon: Optional[str] = None
    coordinator_only: bool = False


class ActivityCategoryCreate(ActivityCategoryBase):
    """Schema para crear categoría."""
    organization_id: Optional[int] = None


class ActivityCategoryResponse(ActivityCategoryBase):
    """Schema de respuesta para categoría."""
    id: int
    is_active: bool
    coordinator_only: bool = False
    organization_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActivityCategoryUpdate(BaseModel):
    """Schema para actualizar categoría."""
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    display_order: Optional[int] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    coordinator_only: Optional[bool] = None


class ActivityCategoryWithCount(ActivityCategoryResponse):
    """Categoría con conteo de actividades."""
    activities_count: int = 0


# ==========================================
# PLANTILLAS DE ACTIVIDADES
# ==========================================

class ActivityTemplateBase(BaseModel):
    """Schema base para plantilla de actividad."""
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    requires_evidence: bool = False
    is_critical: bool = False
    default_frequency: int = 1
    display_order: int = 0
    coordinator_only: bool = False


class ActivityTemplateCreate(ActivityTemplateBase):
    """Schema para crear plantilla."""
    category_id: int
    organization_id: Optional[int] = None


class ActivityTemplateUpdate(BaseModel):
    """Schema para actualizar plantilla."""
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    requires_evidence: Optional[bool] = None
    is_critical: Optional[bool] = None
    default_frequency: Optional[int] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    coordinator_only: Optional[bool] = None


class ActivityTemplateResponse(ActivityTemplateBase):
    """Schema de respuesta para plantilla."""
    id: int
    category_id: int
    is_active: bool
    coordinator_only: bool = False
    organization_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActivityTemplateWithCategory(ActivityTemplateResponse):
    """Plantilla con información de categoría."""
    category_name: str
    category_code: str
    category_color: str


# ==========================================
# PLAN MENSUAL
# ==========================================

class MonthlyPlanBase(BaseModel):
    """Schema base para plan mensual."""
    year: int
    month: int
    notes: Optional[str] = None

    @field_validator('month')
    @classmethod
    def validate_month(cls, v):
        if v < 1 or v > 12:
            raise ValueError('El mes debe estar entre 1 y 12')
        return v


class MonthlyPlanCreate(MonthlyPlanBase):
    """Schema para crear plan mensual."""
    user_id: int
    organization_id: Optional[int] = None


class MonthlyPlanUpdate(BaseModel):
    """Schema para actualizar plan mensual."""
    status: Optional[str] = None
    notes: Optional[str] = None


class MonthlyPlanResponse(MonthlyPlanBase):
    """Schema de respuesta para plan mensual."""
    id: int
    user_id: int
    status: str
    created_by: int
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    organization_id: int
    total_planned: int
    total_executed: int
    compliance_percentage: float
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MonthlyPlanWithDetails(MonthlyPlanResponse):
    """Plan mensual con detalles de usuario."""
    user_name: str = ""
    user_email: str = ""
    created_by_name: str = ""


# ==========================================
# CICLOS DE PLANIFICACIÓN
# ==========================================

class PlanningCycleBase(BaseModel):
    """Schema base para ciclo de planificación."""
    cycle_number: int
    start_date: date
    end_date: date

    @field_validator('cycle_number')
    @classmethod
    def validate_cycle(cls, v):
        if v < 1 or v > 4:
            raise ValueError('El ciclo debe estar entre 1 y 4')
        return v


class PlanningCycleResponse(PlanningCycleBase):
    """Schema de respuesta para ciclo."""
    id: int
    monthly_plan_id: int
    total_planned: int
    total_executed: int
    compliance_percentage: float
    is_current: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# ACTIVIDADES PLANEADAS
# ==========================================

class PlannedActivityBase(BaseModel):
    """Schema base para actividad planeada."""
    activity_template_id: int
    cycle_1_planned: int = 0
    cycle_2_planned: int = 0
    cycle_3_planned: int = 0
    cycle_4_planned: int = 0
    requires_evidence: bool = True
    notes: Optional[str] = None


class PlannedActivityCreate(PlannedActivityBase):
    """Schema para crear actividad planeada."""
    monthly_plan_id: int


class PlannedActivityUpdate(BaseModel):
    """Schema para actualizar actividad planeada."""
    cycle_1_planned: Optional[int] = None
    cycle_2_planned: Optional[int] = None
    cycle_3_planned: Optional[int] = None
    cycle_4_planned: Optional[int] = None
    requires_evidence: Optional[bool] = None
    notes: Optional[str] = None


class PlannedActivityResponse(PlannedActivityBase):
    """Schema de respuesta para actividad planeada."""
    id: int
    monthly_plan_id: int
    cycle_1_executed: int
    cycle_2_executed: int
    cycle_3_executed: int
    cycle_4_executed: int
    total_planned: int
    total_executed: int
    compliance_percentage: float
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlannedActivityWithTemplate(PlannedActivityResponse):
    """Actividad planeada con información de la plantilla."""
    activity_name: str
    activity_code: str
    category_id: int
    category_name: str
    category_code: str
    requires_evidence: bool
    is_critical: bool
    coordinator_only: bool = False


# ==========================================
# BULK OPERATIONS
# ==========================================

class BulkPlannedActivityCreate(BaseModel):
    """Schema para crear múltiples actividades planeadas."""
    monthly_plan_id: int
    activities: List[PlannedActivityBase]


class MonthYear(BaseModel):
    """Par año-mes para creación masiva."""
    year: int
    month: int

    @field_validator('month')
    @classmethod
    def validate_month(cls, v):
        if v < 1 or v > 12:
            raise ValueError('El mes debe estar entre 1 y 12')
        return v


class BulkMonthlyPlanCreate(BaseModel):
    """Schema para crear planes mensuales en lote."""
    user_ids: List[int]
    months: List[MonthYear]
    notes: Optional[str] = None
    organization_id: Optional[int] = None
    load_activities: bool = False  # Cargar actividades del catálogo automáticamente


class BulkCreateResponse(BaseModel):
    """Respuesta de creación masiva de planes."""
    created: int = 0
    skipped: int = 0
    plan_ids: List[int] = []
    details: List[str] = []


class PlanWithActivities(MonthlyPlanResponse):
    """Plan mensual con todas sus actividades planeadas."""
    user_name: str = ""
    user_email: str = ""
    created_by_name: str = ""
    planned_activities: List[PlannedActivityWithTemplate] = []
    cycles: List[PlanningCycleResponse] = []
