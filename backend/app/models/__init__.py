# Modelos del Sistema de Gestión de Seguridad Industrial
# Importar en orden de dependencias

# Core
from app.models.organization import Organization
from app.models.department import Department
from app.models.work_group import WorkGroup
from app.models.user import User, UserRole

# Categorías y plantillas de actividades
from app.models.activity_category import ActivityCategory, ActivityTemplate

# Planificación
from app.models.planning import (
    MonthlyPlan,
    PlanningCycle,
    PlannedActivity,
    PlanStatus
)

# Ejecución
from app.models.execution import (
    ActivityExecution,
    ExecutionFile,
    ExecutionHistory,
    ExecutionStatus,
    ApprovalStatus
)

# Emergencias
from app.models.emergency import (
    EmergencyType,
    Emergency,
    EmergencyResource,
    EmergencyFile,
    EmergencySeverity,
    EmergencyStatus
)

# Equipos
from app.models.equipment import (
    EquipmentCategory,
    Equipment,
    EquipmentMaintenance,
    EquipmentInspection,
    EquipmentFile,
    EquipmentNovelty,
    EquipmentStatus,
    MaintenanceType
)

# Certificaciones
from app.models.certification import (
    CertificationType,
    UserCertification,
    VehicleDocument,
    CertificationAlert,
    Notification,
    NotificationSetting,
    CertificationStatus,
    AlertPriority
)

# Cumplimiento y reportes
from app.models.compliance import (
    ComplianceMetric,
    MonthlySummary,
    AnnualSummary,
    Accident,
    SavedReport,
    ScheduledReport,
    AuditLog
)

__all__ = [
    # Core
    "Organization",
    "Department",
    "WorkGroup",
    "User",
    "UserRole",

    # Actividades
    "ActivityCategory",
    "ActivityTemplate",

    # Planificación
    "MonthlyPlan",
    "PlanningCycle",
    "PlannedActivity",
    "PlanStatus",

    # Ejecución
    "ActivityExecution",
    "ExecutionFile",
    "ExecutionHistory",
    "ExecutionStatus",
    "ApprovalStatus",

    # Emergencias
    "EmergencyType",
    "Emergency",
    "EmergencyResource",
    "EmergencyFile",
    "EmergencySeverity",
    "EmergencyStatus",

    # Equipos
    "EquipmentCategory",
    "Equipment",
    "EquipmentMaintenance",
    "EquipmentInspection",
    "EquipmentFile",
    "EquipmentNovelty",
    "EquipmentStatus",
    "MaintenanceType",

    # Certificaciones
    "CertificationType",
    "UserCertification",
    "VehicleDocument",
    "CertificationAlert",
    "Notification",
    "NotificationSetting",
    "CertificationStatus",
    "AlertPriority",

    # Cumplimiento
    "ComplianceMetric",
    "MonthlySummary",
    "AnnualSummary",
    "Accident",
    "SavedReport",
    "ScheduledReport",
    "AuditLog",
]
