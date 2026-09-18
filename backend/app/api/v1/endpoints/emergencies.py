from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.emergency import Emergency, EmergencyType, EmergencyStatus
from pydantic import BaseModel, ConfigDict

router = APIRouter()


def _enforce_emergency_org_access(emergency: Emergency, current_user: User) -> None:
    if current_user.organization_id and emergency.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para acceder a emergencias de otra organización"
        )


# Schemas simplificados para emergencias
class EmergencyTypeResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    default_severity: str
    color: str
    model_config = ConfigDict(from_attributes=True)


class EmergencyCreate(BaseModel):
    emergency_type_id: int
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    severity: str = "Media"


class EmergencyResponse(BaseModel):
    id: int
    emergency_code: str
    emergency_type_id: int
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    severity: str
    status: str
    reported_at: datetime
    arrival_at: Optional[datetime] = None
    response_time_minutes: Optional[int] = None
    reported_by: int
    model_config = ConfigDict(from_attributes=True)


@router.get("/types", response_model=List[EmergencyTypeResponse])
async def get_emergency_types(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar tipos de emergencias."""
    types = db.query(EmergencyType).filter(
        EmergencyType.is_active == True
    ).order_by(EmergencyType.display_order).all()
    return types


@router.get("/", response_model=List[EmergencyResponse])
async def get_emergencies(
    year: int = Query(..., ge=2020, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    emergency_type_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar emergencias con filtros."""
    query = db.query(Emergency)

    if current_user.organization_id:
        query = query.filter(Emergency.organization_id == current_user.organization_id)

    # Filtro por año
    from sqlalchemy import extract
    query = query.filter(extract('year', Emergency.reported_at) == year)

    if month:
        query = query.filter(extract('month', Emergency.reported_at) == month)

    if emergency_type_id:
        query = query.filter(Emergency.emergency_type_id == emergency_type_id)

    if status:
        query = query.filter(Emergency.status == status)

    emergencies = query.order_by(Emergency.reported_at.desc()).offset(skip).limit(limit).all()
    return emergencies


@router.post("/", response_model=EmergencyResponse)
async def create_emergency(
    emergency_data: EmergencyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Registrar nueva emergencia."""
    # Generar código único
    year = datetime.utcnow().year
    count = db.query(Emergency).filter(
        Emergency.organization_id == current_user.organization_id
    ).count() + 1
    emergency_code = f"EMG-{year}-{count:04d}"

    emergency = Emergency(
        emergency_code=emergency_code,
        emergency_type_id=emergency_data.emergency_type_id,
        title=emergency_data.title,
        description=emergency_data.description,
        location=emergency_data.location,
        severity=emergency_data.severity,
        status=EmergencyStatus.REPORTED.value,
        reported_by=current_user.id,
        organization_id=current_user.organization_id
    )

    db.add(emergency)
    db.commit()
    db.refresh(emergency)

    return emergency


@router.post("/{emergency_id}/arrival")
async def register_arrival(
    emergency_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Registrar llegada a la emergencia."""
    emergency = db.query(Emergency).filter(Emergency.id == emergency_id).first()

    if not emergency:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Emergencia no encontrada")
    _enforce_emergency_org_access(emergency, current_user)

    now = datetime.utcnow()
    emergency.arrival_at = now
    emergency.attended_by = current_user.id
    emergency.status = EmergencyStatus.IN_PROGRESS.value

    # Calcular tiempo de respuesta
    if emergency.reported_at:
        delta = now - emergency.reported_at
        emergency.response_time_minutes = int(delta.total_seconds() / 60)

    db.commit()

    return {
        "message": "Llegada registrada",
        "response_time_minutes": emergency.response_time_minutes
    }


@router.post("/{emergency_id}/close")
async def close_emergency(
    emergency_id: int,
    actions_taken: str,
    result: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cerrar emergencia."""
    emergency = db.query(Emergency).filter(Emergency.id == emergency_id).first()

    if not emergency:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Emergencia no encontrada")
    _enforce_emergency_org_access(emergency, current_user)

    emergency.status = EmergencyStatus.CLOSED.value
    emergency.closed_at = datetime.utcnow()
    emergency.closed_by = current_user.id
    emergency.actions_taken = actions_taken
    emergency.result = result

    db.commit()

    return {"message": "Emergencia cerrada correctamente"}


@router.get("/summary")
async def get_emergencies_summary(
    year: int = Query(..., ge=2020, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener resumen de emergencias."""
    from sqlalchemy import extract, func

    query = db.query(Emergency)

    if current_user.organization_id:
        query = query.filter(Emergency.organization_id == current_user.organization_id)

    query = query.filter(extract('year', Emergency.reported_at) == year)
    if month:
        query = query.filter(extract('month', Emergency.reported_at) == month)

    emergencies = query.all()

    # Agrupar por tipo
    by_type = {}
    total_response_time = 0
    count_with_response = 0

    for e in emergencies:
        if e.emergency_type_id not in by_type:
            by_type[e.emergency_type_id] = 0
        by_type[e.emergency_type_id] += 1

        if e.response_time_minutes:
            total_response_time += e.response_time_minutes
            count_with_response += 1

    avg_response = total_response_time / count_with_response if count_with_response > 0 else None

    return {
        "total": len(emergencies),
        "by_type": by_type,
        "avg_response_time_minutes": avg_response,
        "closed": sum(1 for e in emergencies if e.status == EmergencyStatus.CLOSED.value),
        "open": sum(1 for e in emergencies if e.status != EmergencyStatus.CLOSED.value)
    }
