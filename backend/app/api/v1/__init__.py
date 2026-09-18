from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    users,
    organizations,
    work_groups,
    activity_categories,
    activity_templates,
    planning,
    executions,
    emergencies,
    equipment,
    certifications,
    notifications,
    alerts,
    dashboard,
    reports,
)

api_router = APIRouter()

# Autenticación
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])

# Usuarios y organizaciones
api_router.include_router(users.router, prefix="/users", tags=["Usuarios"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizaciones"])
api_router.include_router(work_groups.router, prefix="/work-groups", tags=["Grupos de Trabajo"])

# Catálogos
api_router.include_router(activity_categories.router, prefix="/activity-categories", tags=["Categorías de Actividades"])
api_router.include_router(activity_templates.router, prefix="/activity-templates", tags=["Plantillas de Actividades"])

# Core del sistema
api_router.include_router(planning.router, prefix="/planning", tags=["Planificación"])
api_router.include_router(executions.router, prefix="/executions", tags=["Ejecuciones"])
api_router.include_router(emergencies.router, prefix="/emergencies", tags=["Emergencias"])

# Equipos y certificaciones
api_router.include_router(equipment.router, prefix="/equipment", tags=["Equipos"])
api_router.include_router(certifications.router, prefix="/certifications", tags=["Certificaciones"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notificaciones"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alertas"])

# Dashboard y reportes
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reportes"])
