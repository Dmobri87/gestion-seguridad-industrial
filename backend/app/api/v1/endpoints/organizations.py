from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, ensure_org_access
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.models.department import Department
from app.schemas.organization import (
    OrganizationResponse, OrganizationCreate, OrganizationUpdate,
    DepartmentResponse, DepartmentCreate, DepartmentUpdate
)

router = APIRouter()


# ==========================================
# ORGANIZACIONES
# ==========================================

@router.get("/", response_model=List[OrganizationResponse])
async def get_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_roles([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    """
    Listar organizaciones.
    Solo Administradores del sistema.
    """
    organizations = db.query(Organization).offset(skip).limit(limit).all()
    return organizations


@router.get("/current", response_model=OrganizationResponse)
async def get_current_organization(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener la organización del usuario actual.
    """
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no tiene organización asignada"
        )

    org = db.query(Organization).filter(
        Organization.id == current_user.organization_id
    ).first()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organización no encontrada"
        )

    return org


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener organización por ID.
    """
    if current_user.role != UserRole.ADMIN.value and current_user.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver esta organización"
        )

    org = db.query(Organization).filter(Organization.id == org_id).first()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organización no encontrada"
        )

    return org


@router.post("/", response_model=OrganizationResponse)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    """
    Crear nueva organización.
    Solo Administradores del sistema.
    """
    # Verificar código único
    existing = db.query(Organization).filter(Organization.code == org_data.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de organización ya existe"
        )

    org = Organization(**org_data.model_dump())
    db.add(org)
    db.commit()
    db.refresh(org)

    return org


@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: int,
    org_data: OrganizationUpdate,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    """
    Actualizar organización.
    Solo Administradores.
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organización no encontrada"
        )

    update_data = org_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(org, field, value)

    db.commit()
    db.refresh(org)

    return org


# ==========================================
# DEPARTAMENTOS
# ==========================================

@router.get("/departments/", response_model=List[DepartmentResponse])
async def get_departments(
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Listar departamentos.
    """
    query = db.query(Department)

    # Filtrar por organización
    org_id = organization_id or current_user.organization_id
    if organization_id and current_user.organization_id and current_user.role != UserRole.ADMIN.value:
        if organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para consultar esta organización"
            )
    if org_id:
        query = query.filter(Department.organization_id == org_id)

    return query.filter(Department.is_active == True).all()


@router.get("/departments/{dept_id}", response_model=DepartmentResponse)
async def get_department(
    dept_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener departamento por ID.
    """
    dept = db.query(Department).filter(Department.id == dept_id).first()

    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Departamento no encontrado"
        )

    ensure_org_access(current_user, dept, "departamento")
    return dept


@router.post("/departments/", response_model=DepartmentResponse)
async def create_department(
    dept_data: DepartmentCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value])),
    db: Session = Depends(get_db)
):
    """
    Crear departamento.
    """
    if current_user.role != UserRole.ADMIN.value and current_user.organization_id:
        if dept_data.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para asignar este departamento"
            )

    dept = Department(**dept_data.model_dump())
    db.add(dept)
    db.commit()
    db.refresh(dept)

    return dept


@router.put("/departments/{dept_id}", response_model=DepartmentResponse)
async def update_department(
    dept_id: int,
    dept_data: DepartmentUpdate,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value])),
    db: Session = Depends(get_db)
):
    """
    Actualizar departamento.
    """
    dept = db.query(Department).filter(Department.id == dept_id).first()

    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Departamento no encontrado"
        )

    ensure_org_access(current_user, dept, "departamento")

    update_data = dept_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dept, field, value)

    db.commit()
    db.refresh(dept)

    return dept
