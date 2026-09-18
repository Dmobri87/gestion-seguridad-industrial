from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User, UserRole
from app.models.equipment import Equipment, EquipmentCategory, EquipmentNovelty, EquipmentStatus

router = APIRouter()


# ==========================================
# SCHEMAS - EQUIPOS
# ==========================================

class EquipmentCategoryResponse(BaseModel):
    id: int
    name: str
    code: str
    color: str
    icon: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class EquipmentResponse(BaseModel):
    id: int
    code: str
    name: str
    category_id: int
    category_name: Optional[str] = None
    status: str
    location: Optional[str] = None
    last_maintenance_date: Optional[date] = None
    next_maintenance_date: Optional[date] = None
    is_available_day: bool = True
    is_available_night: bool = True
    description: Optional[str] = None
    notes: Optional[str] = None
    # Novedad activa (si existe)
    active_novelty: Optional[str] = None
    active_novelty_id: Optional[int] = None
    novelties_count: int = 0
    model_config = ConfigDict(from_attributes=True)


class EquipmentCreate(BaseModel):
    code: str
    name: str
    category_id: int
    location: Optional[str] = None
    status: Optional[str] = "Operativo"
    is_available_day: bool = True
    is_available_night: bool = True
    description: Optional[str] = None
    notes: Optional[str] = None


class EquipmentUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    category_id: Optional[int] = None
    location: Optional[str] = None
    status: Optional[str] = None
    next_maintenance_date: Optional[date] = None
    is_available_day: Optional[bool] = None
    is_available_night: Optional[bool] = None
    description: Optional[str] = None
    notes: Optional[str] = None


# ==========================================
# SCHEMAS - NOVEDADES
# ==========================================

class NoveltyCreate(BaseModel):
    novelty_type: str  # Fuera de Servicio, En Mantenimiento, Siniestro, Otro
    description: str
    shift: str  # Día, Noche, Ambos
    unavailable_hours: float = 0
    start_date: Optional[datetime] = None  # Si no se envía, usa now()


class NoveltyResolve(BaseModel):
    resolution: str
    unavailable_hours: Optional[float] = None  # Horas totales, si se quiere actualizar


class NoveltyResponse(BaseModel):
    id: int
    equipment_id: int
    novelty_type: str
    description: str
    shift: str
    unavailable_hours: float
    start_date: datetime
    end_date: Optional[datetime] = None
    is_resolved: bool
    resolution: Optional[str] = None
    previous_status: Optional[str] = None
    reported_by: int
    reporter_name: Optional[str] = None
    resolved_by: Optional[int] = None
    resolver_name: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# HELPERS
# ==========================================

def _build_equipment_response(item: Equipment, db: Session) -> EquipmentResponse:
    """Construir response con novedad activa."""
    data = EquipmentResponse.model_validate(item)
    if item.category:
        data.category_name = item.category.name

    # Contar novedades y buscar activa
    novelties = db.query(EquipmentNovelty).filter(
        EquipmentNovelty.equipment_id == item.id
    ).all()
    data.novelties_count = len(novelties)

    active = next((n for n in novelties if not n.is_resolved), None)
    if active:
        data.active_novelty = f"{active.novelty_type}: {active.description}"
        data.active_novelty_id = active.id

    return data


# ==========================================
# ENDPOINTS - CATEGORÍAS
# ==========================================

@router.get("/categories", response_model=List[EquipmentCategoryResponse])
async def get_equipment_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar categorías de equipos."""
    return db.query(EquipmentCategory).filter(EquipmentCategory.is_active == True).all()


# ==========================================
# ENDPOINTS - RESUMEN Y FLOTA
# ==========================================

@router.get("/summary")
async def get_equipment_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resumen de estado de equipos."""
    query = db.query(Equipment).filter(Equipment.is_active == True)
    if current_user.organization_id:
        query = query.filter(Equipment.organization_id == current_user.organization_id)

    equipment_list = query.all()
    today = date.today()

    return {
        "total": len(equipment_list),
        "operational": sum(1 for e in equipment_list if e.status == EquipmentStatus.OPERATIONAL.value),
        "in_maintenance": sum(1 for e in equipment_list if e.status == EquipmentStatus.IN_MAINTENANCE.value),
        "out_of_service": sum(1 for e in equipment_list if e.status == EquipmentStatus.OUT_OF_SERVICE.value),
        "pending_maintenance": sum(
            1 for e in equipment_list
            if e.next_maintenance_date and e.next_maintenance_date <= today
        )
    }


@router.get("/fleet")
async def get_fleet_availability(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disponibilidad de flota completa por turnos de 12 horas."""
    query = db.query(Equipment).filter(Equipment.is_active == True)
    if current_user.organization_id:
        query = query.filter(Equipment.organization_id == current_user.organization_id)

    equipment_list = query.all()

    # Agrupar por categoría
    categories_map = {}
    for eq in equipment_list:
        cat_name = eq.category.name if eq.category else "Sin categoría"
        cat_id = eq.category_id or 0
        if cat_id not in categories_map:
            categories_map[cat_id] = {
                "category_id": cat_id, "category_name": cat_name,
                "total": 0, "operational": 0,
                "available_day": 0, "available_night": 0,
                "in_maintenance": 0, "out_of_service": 0,
            }
        cat = categories_map[cat_id]
        cat["total"] += 1
        is_op = eq.status == EquipmentStatus.OPERATIONAL.value
        if is_op:
            cat["operational"] += 1
        if is_op and getattr(eq, 'is_available_day', True):
            cat["available_day"] += 1
        if is_op and getattr(eq, 'is_available_night', True):
            cat["available_night"] += 1
        if eq.status == EquipmentStatus.IN_MAINTENANCE.value:
            cat["in_maintenance"] += 1
        if eq.status == EquipmentStatus.OUT_OF_SERVICE.value:
            cat["out_of_service"] += 1

    # Agrupar por ubicación (CAE)
    locations_map = {}
    for eq in equipment_list:
        loc = eq.location or "Sin ubicación"
        if loc not in locations_map:
            locations_map[loc] = {"location": loc, "total": 0, "available_day": 0, "available_night": 0}
        locations_map[loc]["total"] += 1
        is_op = eq.status == EquipmentStatus.OPERATIONAL.value
        if is_op and getattr(eq, 'is_available_day', True):
            locations_map[loc]["available_day"] += 1
        if is_op and getattr(eq, 'is_available_night', True):
            locations_map[loc]["available_night"] += 1

    total = len(equipment_list)
    operational = sum(1 for e in equipment_list if e.status == EquipmentStatus.OPERATIONAL.value)
    total_day = sum(1 for e in equipment_list if e.status == EquipmentStatus.OPERATIONAL.value and getattr(e, 'is_available_day', True))
    total_night = sum(1 for e in equipment_list if e.status == EquipmentStatus.OPERATIONAL.value and getattr(e, 'is_available_night', True))

    return {
        "total": total, "operational": operational,
        "available_day": total_day, "available_night": total_night,
        "by_category": list(categories_map.values()),
        "by_location": list(locations_map.values()),
    }


# ==========================================
# ENDPOINTS - EQUIPOS CRUD
# ==========================================

@router.get("/", response_model=List[EquipmentResponse])
async def get_equipment(
    category_id: Optional[int] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar equipos con filtros."""
    query = db.query(Equipment)
    if current_user.organization_id:
        query = query.filter(Equipment.organization_id == current_user.organization_id)
    if category_id:
        query = query.filter(Equipment.category_id == category_id)
    if status:
        query = query.filter(Equipment.status == status)
    if search:
        query = query.filter(
            (Equipment.name.ilike(f"%{search}%")) |
            (Equipment.code.ilike(f"%{search}%"))
        )

    items = query.filter(Equipment.is_active == True).all()
    return [_build_equipment_response(item, db) for item in items]


@router.get("/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment_detail(
    equipment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener detalle de equipo."""
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    if equipment.organization_id and current_user.organization_id and equipment.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    return _build_equipment_response(equipment, db)


@router.post("/", response_model=EquipmentResponse)
async def create_equipment(
    data: EquipmentCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value])),
    db: Session = Depends(get_db)
):
    """Crear nuevo equipo."""
    existing = db.query(Equipment).filter(Equipment.code == data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="El código ya existe")

    equipment = Equipment(
        **data.model_dump(),
        organization_id=current_user.organization_id
    )
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return _build_equipment_response(equipment, db)


@router.put("/{equipment_id}", response_model=EquipmentResponse)
async def update_equipment(
    equipment_id: int,
    data: EquipmentUpdate,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value])),
    db: Session = Depends(get_db)
):
    """Actualizar equipo existente."""
    equipment = db.query(Equipment).filter(
        Equipment.id == equipment_id, Equipment.is_active == True
    ).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    update_data = data.model_dump(exclude_unset=True)

    # Si se cambia el código, validar unicidad
    if 'code' in update_data and update_data['code'] != equipment.code:
        existing = db.query(Equipment).filter(
            Equipment.code == update_data['code'],
            Equipment.id != equipment_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="El código ya existe")

    for field, value in update_data.items():
        setattr(equipment, field, value)

    db.commit()
    db.refresh(equipment)
    return _build_equipment_response(equipment, db)


# ==========================================
# ENDPOINTS - NOVEDADES DE EQUIPOS
# ==========================================

@router.get("/{equipment_id}/novelties", response_model=List[NoveltyResponse])
async def get_equipment_novelties(
    equipment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar novedades/historial de un equipo."""
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    novelties = db.query(EquipmentNovelty).filter(
        EquipmentNovelty.equipment_id == equipment_id
    ).order_by(EquipmentNovelty.start_date.desc()).all()

    result = []
    for n in novelties:
        resp = NoveltyResponse.model_validate(n)
        # Agregar nombres de usuarios
        reporter = db.query(User).filter(User.id == n.reported_by).first()
        resp.reporter_name = reporter.full_name if reporter else ""
        if n.resolved_by:
            resolver = db.query(User).filter(User.id == n.resolved_by).first()
            resp.resolver_name = resolver.full_name if resolver else ""
        result.append(resp)

    return result


@router.post("/{equipment_id}/novelties", response_model=NoveltyResponse)
async def create_equipment_novelty(
    equipment_id: int,
    data: NoveltyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Registrar una novedad en un equipo (marca como fuera de servicio/mantenimiento)."""
    equipment = db.query(Equipment).filter(
        Equipment.id == equipment_id, Equipment.is_active == True
    ).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    # Guardar estado previo
    previous_status = equipment.status

    # Cambiar estado del equipo según tipo de novedad
    if data.novelty_type == "En Mantenimiento":
        equipment.status = EquipmentStatus.IN_MAINTENANCE.value
    elif data.novelty_type in ["Fuera de Servicio", "Siniestro"]:
        equipment.status = EquipmentStatus.OUT_OF_SERVICE.value

    # Actualizar disponibilidad según turno
    if data.shift == "Día":
        equipment.is_available_day = False
    elif data.shift == "Noche":
        equipment.is_available_night = False
    elif data.shift == "Ambos":
        equipment.is_available_day = False
        equipment.is_available_night = False

    novelty = EquipmentNovelty(
        equipment_id=equipment_id,
        novelty_type=data.novelty_type,
        description=data.description,
        shift=data.shift,
        unavailable_hours=data.unavailable_hours,
        start_date=data.start_date or datetime.utcnow(),
        is_resolved=False,
        previous_status=previous_status,
        reported_by=current_user.id,
        organization_id=current_user.organization_id,
    )

    db.add(novelty)
    db.commit()
    db.refresh(novelty)

    resp = NoveltyResponse.model_validate(novelty)
    resp.reporter_name = current_user.full_name
    return resp


@router.put("/{equipment_id}/novelties/{novelty_id}/resolve", response_model=NoveltyResponse)
async def resolve_equipment_novelty(
    equipment_id: int,
    novelty_id: int,
    data: NoveltyResolve,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resolver una novedad (equipo vuelve a servicio)."""
    novelty = db.query(EquipmentNovelty).filter(
        EquipmentNovelty.id == novelty_id,
        EquipmentNovelty.equipment_id == equipment_id,
        EquipmentNovelty.is_resolved == False
    ).first()
    if not novelty:
        raise HTTPException(status_code=404, detail="Novedad no encontrada o ya resuelta")

    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()

    # Resolver la novedad
    novelty.is_resolved = True
    novelty.end_date = datetime.utcnow()
    novelty.resolution = data.resolution
    novelty.resolved_by = current_user.id
    if data.unavailable_hours is not None:
        novelty.unavailable_hours = data.unavailable_hours

    # Restaurar estado previo del equipo
    if equipment and novelty.previous_status:
        equipment.status = novelty.previous_status
        equipment.is_available_day = True
        equipment.is_available_night = True

    db.commit()
    db.refresh(novelty)

    resp = NoveltyResponse.model_validate(novelty)
    reporter = db.query(User).filter(User.id == novelty.reported_by).first()
    resp.reporter_name = reporter.full_name if reporter else ""
    resp.resolver_name = current_user.full_name
    return resp
