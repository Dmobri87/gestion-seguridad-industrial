from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.dependencies import get_current_user
from app.core.database import get_db
from app.models.program import Program
from app.models.activity import Activity
from app.models.execution import Execution
from app.models.user import User
from typing import List, Dict
from datetime import datetime, timedelta

router = APIRouter(prefix="/reports", tags=["Reportes"])

@router.get("/")
def get_report_info(current_user: dict = Depends(get_current_user)):
    """
    Información general del módulo de reportes.
    """
    return {
        "status": "Módulo de reportes activo",
        "available_reports": [
            "/reports/programs - Resumen de todos los programas",
            "/reports/program/{id} - Detalle de un programa específico",
            "/reports/user/{id} - Rendimiento de un usuario",
            "/reports/activity/{id} - Estadísticas de una actividad",
            "/reports/general - Dashboard general del sistema"
        ]
    }


@router.get("/general")
def get_general_report(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Dashboard general con estadísticas del sistema.
    
    Solo accesible para Administradores y Supervisores.
    """
    if current_user["role"] not in ["Administrador", "Supervisor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver reportes generales"
        )
    
    # Contar totales
    total_users = db.query(User).count()
    total_programs = db.query(Program).count()
    total_activities = db.query(Activity).count()
    total_executions = db.query(Execution).count()
    
    # Ejecuciones por estado
    status_summary = db.query(
        Execution.status,
        func.count(Execution.id)
    ).group_by(Execution.status).all()
    
    # Últimas 30 días de actividad
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_executions = db.query(Execution).filter(
        Execution.execution_date >= thirty_days_ago
    ).count()
    
    return {
        "overview": {
            "total_users": total_users,
            "total_programs": total_programs,
            "total_activities": total_activities,
            "total_executions": total_executions
        },
        "executions_by_status": {status: count for status, count in status_summary},
        "recent_activity": {
            "last_30_days": recent_executions
        }
    }


@router.get("/programs")
def get_programs_report(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Resumen de todos los programas con sus actividades y ejecuciones.
    """
    programs = db.query(Program).all()
    
    report = []
    for program in programs:
        activities_count = db.query(Activity).filter(
            Activity.program_id == program.id
        ).count()
        
        executions_count = db.query(Execution).join(Activity).filter(
            Activity.program_id == program.id
        ).count()
        
        report.append({
            "program_id": program.id,
            "program_name": program.name,
            "coordinator_id": program.coordinator_id,
            "total_activities": activities_count,
            "total_executions": executions_count
        })
    
    return report


@router.get("/program/{program_id}")
def get_program_detail_report(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Reporte detallado de un programa específico.
    """
    program = db.query(Program).filter(Program.id == program_id).first()
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Programa con ID {program_id} no encontrado"
        )
    
    # Actividades del programa
    activities = db.query(Activity).filter(Activity.program_id == program_id).all()
    
    activities_detail = []
    for activity in activities:
        executions = db.query(Execution).filter(
            Execution.activity_id == activity.id
        ).all()
        
        status_count = {}
        for execution in executions:
            status_count[execution.status] = status_count.get(execution.status, 0) + 1
        
        activities_detail.append({
            "activity_id": activity.id,
            "activity_name": activity.name,
            "total_executions": len(executions),
            "status_summary": status_count
        })
    
    return {
        "program": {
            "id": program.id,
            "name": program.name,
            "description": program.description,
            "coordinator_id": program.coordinator_id
        },
        "activities": activities_detail,
        "summary": {
            "total_activities": len(activities),
            "total_executions": sum(len(db.query(Execution).filter(
                Execution.activity_id == a.id
            ).all()) for a in activities)
        }
    }


@router.get("/user/{user_id}")
def get_user_performance_report(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Reporte de rendimiento de un usuario específico.
    
    Los usuarios solo pueden ver su propio reporte.
    Administradores y Supervisores pueden ver cualquier reporte.
    """
    # Obtener el usuario actual
    current_user_obj = db.query(User).filter(User.email == current_user["email"]).first()
    
    # Validar permisos
    if current_user_obj.id != user_id and current_user["role"] not in ["Administrador", "Supervisor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver este reporte"
        )
    
    # Obtener el usuario del reporte
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {user_id} no encontrado"
        )
    
    # Ejecuciones del usuario
    executions = db.query(Execution).filter(Execution.user_id == user_id).all()
    
    # Estadísticas por estado
    status_summary = {}
    for execution in executions:
        status_summary[execution.status] = status_summary.get(execution.status, 0) + 1
    
    # Últimas ejecuciones
    recent = db.query(Execution).filter(
        Execution.user_id == user_id
    ).order_by(Execution.execution_date.desc()).limit(10).all()
    
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        },
        "statistics": {
            "total_executions": len(executions),
            "status_summary": status_summary
        },
        "recent_executions": [
            {
                "id": e.id,
                "activity_id": e.activity_id,
                "status": e.status,
                "date": e.execution_date,
                "observation": e.observation
            } for e in recent
        ]
    }


@router.get("/activity/{activity_id}")
def get_activity_report(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Estadísticas de una actividad específica.
    """
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Actividad con ID {activity_id} no encontrada"
        )
    
    # Ejecuciones de la actividad
    executions = db.query(Execution).filter(Execution.activity_id == activity_id).all()
    
    # Estadísticas por estado
    status_summary = {}
    for execution in executions:
        status_summary[execution.status] = status_summary.get(execution.status, 0) + 1
    
    # Usuarios que han ejecutado esta actividad
    users_involved = db.query(User).join(Execution).filter(
        Execution.activity_id == activity_id
    ).distinct().all()
    
    return {
        "activity": {
            "id": activity.id,
            "name": activity.name,
            "description": activity.description,
            "program_id": activity.program_id
        },
        "statistics": {
            "total_executions": len(executions),
            "status_summary": status_summary,
            "users_involved": len(users_involved)
        },
        "users": [
            {
                "id": user.id,
                "full_name": user.full_name,
                "role": user.role
            } for user in users_involved
        ]
    }