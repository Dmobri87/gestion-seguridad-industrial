from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from typing import Optional, List, Dict, Any


# ==========================================
# KPIs PRINCIPALES
# ==========================================

class KPICard(BaseModel):
    """Schema para tarjeta de KPI."""
    title: str
    value: Any
    unit: Optional[str] = None
    change: Optional[float] = None  # Cambio porcentual vs periodo anterior
    change_type: Optional[str] = None  # "increase", "decrease", "neutral"
    icon: Optional[str] = None
    color: Optional[str] = None


class MainKPIs(BaseModel):
    """KPIs principales del dashboard."""
    accidents: KPICard
    emergencies: KPICard
    compliance: KPICard
    pending_activities: KPICard


# ==========================================
# CUMPLIMIENTO
# ==========================================

class ComplianceByCategory(BaseModel):
    """Cumplimiento por categoría."""
    category_id: int
    category_name: str
    category_code: str
    category_color: str
    total_planned: int
    total_executed: int
    compliance_percentage: float


class ComplianceByCycle(BaseModel):
    """Cumplimiento por ciclo."""
    cycle_number: int
    start_date: date
    end_date: date
    total_planned: int
    total_executed: int
    compliance_percentage: float
    is_current: bool


class ComplianceByUser(BaseModel):
    """Cumplimiento por usuario (TAE)."""
    user_id: int
    user_name: str
    department_name: Optional[str] = None
    total_planned: int
    total_executed: int
    compliance_percentage: float


class MonthlyCompliance(BaseModel):
    """Cumplimiento mensual."""
    year: int
    month: int
    month_name: str
    compliance_percentage: float


class ComplianceSummary(BaseModel):
    """Resumen de cumplimiento."""
    overall_compliance: float
    by_category: List[ComplianceByCategory]
    by_cycle: List[ComplianceByCycle]
    monthly_trend: List[MonthlyCompliance]


# ==========================================
# EMERGENCIAS
# ==========================================

class EmergencyByType(BaseModel):
    """Emergencias por tipo."""
    type_id: int
    type_name: str
    type_code: str
    count: int
    color: str


class EmergencySummary(BaseModel):
    """Resumen de emergencias."""
    total: int
    by_type: List[EmergencyByType]
    avg_response_time: Optional[float] = None  # En minutos
    this_month: int
    vs_last_month: Optional[float] = None  # Cambio porcentual


# ==========================================
# ALERTAS
# ==========================================

class Alert(BaseModel):
    """Alerta del sistema."""
    id: int
    type: str  # certification, equipment, activity
    priority: str  # info, warning, urgent, critical
    title: str
    description: str
    related_id: Optional[int] = None
    related_type: Optional[str] = None
    due_date: Optional[date] = None
    created_at: datetime


class AlertsSummary(BaseModel):
    """Resumen de alertas."""
    total: int
    critical: int
    urgent: int
    warning: int
    info: int
    alerts: List[Alert]


# ==========================================
# ACTIVIDADES PENDIENTES
# ==========================================

class PendingActivity(BaseModel):
    """Actividad pendiente."""
    planned_activity_id: int
    activity_name: str
    category_name: str
    user_id: int
    user_name: str
    planned_quantity: int
    executed_quantity: int
    pending_quantity: int
    due_date: Optional[date] = None


class PendingActivitiesSummary(BaseModel):
    """Resumen de actividades pendientes."""
    total_pending: int
    activities: List[PendingActivity]


# ==========================================
# TOP PERFORMERS
# ==========================================

class TopPerformer(BaseModel):
    """Top performer (TAE con mejor cumplimiento)."""
    user_id: int
    user_name: str
    department_name: Optional[str] = None
    compliance_percentage: float
    total_executed: int
    rank: int


class TopPerformersSummary(BaseModel):
    """Resumen de top performers."""
    top_performers: List[TopPerformer]


# ==========================================
# EQUIPOS
# ==========================================

class EquipmentStatusSummary(BaseModel):
    """Resumen de estado de equipos."""
    total: int
    operational: int
    in_maintenance: int
    out_of_service: int
    pending_maintenance: int


# ==========================================
# CERTIFICACIONES
# ==========================================

class CertificationStatusSummary(BaseModel):
    """Resumen de estado de certificaciones."""
    total_personal: int
    expiring_30_days: int
    expiring_15_days: int
    expiring_7_days: int
    expired: int


# ==========================================
# DASHBOARD COMPLETO
# ==========================================

class DashboardData(BaseModel):
    """Datos completos del dashboard."""
    period: str  # "Enero 2026", "Q1 2026", etc.
    year: int
    month: int

    # KPIs principales
    main_kpis: MainKPIs

    # Cumplimiento
    compliance: ComplianceSummary

    # Emergencias
    emergencies: EmergencySummary

    # Alertas
    alerts: AlertsSummary

    # Actividades pendientes
    pending_activities: PendingActivitiesSummary

    # Top performers
    top_performers: TopPerformersSummary

    # Equipos
    equipment: EquipmentStatusSummary

    # Certificaciones
    certifications: CertificationStatusSummary

    # Timestamp de generación
    generated_at: datetime


# ==========================================
# FILTROS DE DASHBOARD
# ==========================================

class DashboardFilters(BaseModel):
    """Filtros para el dashboard."""
    year: int
    month: Optional[int] = None
    department_id: Optional[int] = None
    user_id: Optional[int] = None
    category_id: Optional[int] = None


# ==========================================
# REPORTES RÁPIDOS
# ==========================================

class QuickReportRequest(BaseModel):
    """Solicitud de reporte rápido."""
    report_type: str  # compliance, emergencies, equipment, certifications
    year: int
    month: Optional[int] = None
    format: str = "json"  # json, excel, pdf


class QuickReportResponse(BaseModel):
    """Respuesta de reporte rápido."""
    report_type: str
    generated_at: datetime
    data: Dict[str, Any]
    download_url: Optional[str] = None
