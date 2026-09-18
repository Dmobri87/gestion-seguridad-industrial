from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, ensure_org_access
from app.models.user import User, UserRole
from app.models.work_group import WorkGroup

router = APIRouter()


# ==========================================
# SCHEMAS
# ==========================================

class WorkGroupCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    color: str = "#1890ff"
    coordinator_id: Optional[int] = None


class WorkGroupUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    coordinator_id: Optional[int] = None
    is_active: Optional[bool] = None


class WorkGroupMember(BaseModel):
    id: int
    full_name: str
    email: str
    employee_code: Optional[str] = None
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class WorkGroupResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    color: str
    coordinator_id: Optional[int] = None
    coordinator_name: Optional[str] = None
    organization_id: int
    is_active: bool
    members_count: int = 0
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WorkGroupWithMembers(WorkGroupResponse):
    members: List[WorkGroupMember] = []


# ==========================================
# ENDPOINTS
# ==========================================

@router.get("/", response_model=List[WorkGroupResponse])
async def get_work_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar todos los grupos de trabajo."""
    query = db.query(WorkGroup).options(
        joinedload(WorkGroup.coordinator),
        joinedload(WorkGroup.members)
    )

    if current_user.organization_id:
        query = query.filter(WorkGroup.organization_id == current_user.organization_id)

    groups = query.filter(WorkGroup.is_active == True).order_by(WorkGroup.name).offset(skip).limit(limit).all()

    result = []
    for g in groups:
        result.append(WorkGroupResponse(
            id=g.id,
            name=g.name,
            code=g.code,
            description=g.description,
            color=g.color,
            coordinator_id=g.coordinator_id,
            coordinator_name=g.coordinator.full_name if g.coordinator else None,
            organization_id=g.organization_id,
            is_active=g.is_active,
            members_count=len([m for m in g.members if m.is_active]),
            created_at=g.created_at,
        ))

    return result


@router.get("/{group_id}", response_model=WorkGroupWithMembers)
async def get_work_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener grupo con sus miembros."""
    group = db.query(WorkGroup).options(
        joinedload(WorkGroup.coordinator),
        joinedload(WorkGroup.members)
    ).filter(WorkGroup.id == group_id).first()

    if not group:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")

    ensure_org_access(current_user, group, "grupo de trabajo")

    members = [
        WorkGroupMember(
            id=m.id,
            full_name=m.full_name,
            email=m.email,
            employee_code=m.employee_code,
            role=m.role,
            is_active=m.is_active,
        )
        for m in group.members if m.is_active
    ]

    return WorkGroupWithMembers(
        id=group.id,
        name=group.name,
        code=group.code,
        description=group.description,
        color=group.color,
        coordinator_id=group.coordinator_id,
        coordinator_name=group.coordinator.full_name if group.coordinator else None,
        organization_id=group.organization_id,
        is_active=group.is_active,
        members_count=len(members),
        created_at=group.created_at,
        members=members,
    )


@router.post("/", response_model=WorkGroupResponse)
async def create_work_group(
    data: WorkGroupCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.SUPERVISOR.value])),
    db: Session = Depends(get_db)
):
    """Crear nuevo grupo de trabajo. Solo Admin/Supervisor."""
    existing = db.query(WorkGroup).filter(WorkGroup.code == data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un grupo con ese código")

    # Validar que el coordinador no esté asignado a otro grupo
    if data.coordinator_id:
        existing_coord = db.query(WorkGroup).filter(
            WorkGroup.coordinator_id == data.coordinator_id,
            WorkGroup.is_active == True
        ).first()
        if existing_coord:
            raise HTTPException(
                status_code=400,
                detail="Este usuario ya es coordinador de otro grupo de trabajo"
            )

        coord_user = db.query(User).filter(User.id == data.coordinator_id).first()
        if not coord_user:
            raise HTTPException(status_code=404, detail="Coordinador no encontrado")
        ensure_org_access(current_user, coord_user, "coordinador")

    group = WorkGroup(
        name=data.name,
        code=data.code,
        description=data.description,
        color=data.color,
        coordinator_id=data.coordinator_id,
        organization_id=current_user.organization_id,
    )
    db.add(group)
    db.commit()
    db.refresh(group)

    return WorkGroupResponse(
        id=group.id,
        name=group.name,
        code=group.code,
        description=group.description,
        color=group.color,
        coordinator_id=group.coordinator_id,
        coordinator_name=None,
        organization_id=group.organization_id,
        is_active=group.is_active,
        members_count=0,
        created_at=group.created_at,
    )


@router.put("/{group_id}", response_model=WorkGroupResponse)
async def update_work_group(
    group_id: int,
    data: WorkGroupUpdate,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.SUPERVISOR.value])),
    db: Session = Depends(get_db)
):
    """Actualizar grupo de trabajo."""
    group = db.query(WorkGroup).filter(WorkGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    ensure_org_access(current_user, group, "grupo de trabajo")

    # Validar que el coordinador no esté asignado a otro grupo
    if data.coordinator_id is not None and data.coordinator_id:
        existing_coord = db.query(WorkGroup).filter(
            WorkGroup.coordinator_id == data.coordinator_id,
            WorkGroup.is_active == True,
            WorkGroup.id != group_id
        ).first()
        if existing_coord:
            raise HTTPException(
                status_code=400,
                detail="Este usuario ya es coordinador de otro grupo de trabajo"
            )

        coord_user = db.query(User).filter(User.id == data.coordinator_id).first()
        if not coord_user:
            raise HTTPException(status_code=404, detail="Coordinador no encontrado")
        ensure_org_access(current_user, coord_user, "coordinador")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(group, field, value)

    db.commit()
    db.refresh(group)

    coordinator_name = None
    if group.coordinator_id:
        coord = db.query(User).filter(User.id == group.coordinator_id).first()
        coordinator_name = coord.full_name if coord else None

    members_count = db.query(User).filter(
        User.work_group_id == group.id, User.is_active == True
    ).count()

    return WorkGroupResponse(
        id=group.id,
        name=group.name,
        code=group.code,
        description=group.description,
        color=group.color,
        coordinator_id=group.coordinator_id,
        coordinator_name=coordinator_name,
        organization_id=group.organization_id,
        is_active=group.is_active,
        members_count=members_count,
        created_at=group.created_at,
    )


@router.post("/{group_id}/members/{user_id}")
async def add_member_to_group(
    group_id: int,
    user_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.SUPERVISOR.value, UserRole.COORDINATOR.value])),
    db: Session = Depends(get_db)
):
    """Agregar un usuario a un grupo."""
    group = db.query(WorkGroup).filter(WorkGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    ensure_org_access(current_user, group, "grupo de trabajo")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    ensure_org_access(current_user, user, "usuario")

    user.work_group_id = group_id
    db.commit()

    return {"message": f"{user.full_name} agregado a {group.name}"}


@router.delete("/{group_id}/members/{user_id}")
async def remove_member_from_group(
    group_id: int,
    user_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.SUPERVISOR.value, UserRole.COORDINATOR.value])),
    db: Session = Depends(get_db)
):
    """Remover un usuario de un grupo."""
    user = db.query(User).filter(User.id == user_id, User.work_group_id == group_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en este grupo")
    ensure_org_access(current_user, user, "usuario")

    user.work_group_id = None
    db.commit()

    return {"message": f"{user.full_name} removido del grupo"}
