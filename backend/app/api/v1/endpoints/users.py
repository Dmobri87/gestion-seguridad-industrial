from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, ensure_org_access
from app.core.security import get_password_hash
from app.core.audit import log_audit
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.work_group import WorkGroup
from app.schemas.user import UserResponse, UserCreateV1, UserUpdate, UserWithDetails

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    role: Optional[str] = None,
    department_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Listar usuarios con filtros.
    """
    query = db.query(User)

    # Filtrar por organización del usuario actual
    if current_user.organization_id:
        query = query.filter(User.organization_id == current_user.organization_id)

    # Aplicar filtros
    if role:
        query = query.filter(User.role == role)
    if department_id:
        query = query.filter(User.department_id == department_id)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.full_name.ilike(search_term)) |
            (User.email.ilike(search_term)) |
            (User.employee_code.ilike(search_term))
        )

    users = query.offset(skip).limit(limit).all()
    return users


@router.get("/taes", response_model=List[UserResponse])
async def get_taes(
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Listar todos los TAEs (para asignación de planes).
    """
    query = db.query(User).filter(
        User.role == UserRole.TAE.value,
        User.is_active == True
    )

    if current_user.organization_id:
        query = query.filter(User.organization_id == current_user.organization_id)

    if department_id:
        query = query.filter(User.department_id == department_id)

    return query.all()


@router.get("/assignable", response_model=List[UserResponse])
async def get_assignable_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Listar todo el personal activo asignable a planes.
    Incluye TAE, PSE, Supervisor y Coordinador.
    """
    assignable_roles = [
        UserRole.TAE.value,
        UserRole.PSE.value,
        UserRole.SUPERVISOR.value,
        UserRole.COORDINATOR.value,
    ]

    query = db.query(User).filter(
        User.role.in_(assignable_roles),
        User.is_active == True
    )

    if current_user.organization_id:
        query = query.filter(User.organization_id == current_user.organization_id)

    return query.order_by(User.full_name).all()


@router.get("/{user_id}", response_model=UserWithDetails)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener usuario por ID.
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    # Verificar permisos
    if current_user.organization_id and user.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver este usuario"
        )

    # Agregar detalles
    result = UserWithDetails.model_validate(user)
    if user.organization:
        result.organization_name = user.organization.name
    if user.department:
        result.department_name = user.department.name
    if user.supervisor:
        result.supervisor_name = user.supervisor.full_name

    return result


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreateV1,
    request: Request,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value])),
    db: Session = Depends(get_db)
):
    """
    Crear nuevo usuario.
    Solo Administradores y Coordinadores.
    """
    # Verificar si el email ya existe
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )

    # Usar la organización del usuario actual si no se especifica
    organization_id = user_data.organization_id or current_user.organization_id
    if current_user.organization_id and organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para asignar esta organización"
        )

    # Validar relaciones si se envían
    if user_data.department_id:
        dept = db.query(Department).filter(Department.id == user_data.department_id).first()
        if not dept:
            raise HTTPException(status_code=404, detail="Departamento no encontrado")
        ensure_org_access(current_user, dept, "departamento")
    if user_data.work_group_id:
        group = db.query(WorkGroup).filter(WorkGroup.id == user_data.work_group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Grupo de trabajo no encontrado")
        ensure_org_access(current_user, group, "grupo de trabajo")
    if user_data.supervisor_id:
        supervisor = db.query(User).filter(User.id == user_data.supervisor_id).first()
        if not supervisor:
            raise HTTPException(status_code=404, detail="Supervisor no encontrado")
        ensure_org_access(current_user, supervisor, "supervisor")

    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        employee_code=user_data.employee_code,
        phone=user_data.phone,
        role=user_data.role,
        organization_id=organization_id,
        department_id=user_data.department_id,
        work_group_id=user_data.work_group_id,
        supervisor_id=user_data.supervisor_id,
        is_active=True,
        is_verified=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_audit(
        db=None,
        action="USER_CREATED",
        resource_type="users",
        resource_id=new_user.id,
        current_user=current_user,
        request=request,
        description=f"Usuario creado: {new_user.email}",
    )

    return new_user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    request: Request,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value])),
    db: Session = Depends(get_db)
):
    """
    Actualizar usuario.
    Solo Administradores y Coordinadores.
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    # Verificar permisos de organización
    if current_user.organization_id and user.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para editar este usuario"
        )

    # Actualizar campos
    update_data = user_data.model_dump(exclude_unset=True)
    if "organization_id" in update_data and current_user.organization_id:
        if update_data["organization_id"] != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para cambiar la organización"
            )

    # Validar relaciones si se envían
    if "department_id" in update_data and update_data["department_id"]:
        dept = db.query(Department).filter(Department.id == update_data["department_id"]).first()
        if not dept:
            raise HTTPException(status_code=404, detail="Departamento no encontrado")
        ensure_org_access(current_user, dept, "departamento")
    if "work_group_id" in update_data and update_data["work_group_id"]:
        group = db.query(WorkGroup).filter(WorkGroup.id == update_data["work_group_id"]).first()
        if not group:
            raise HTTPException(status_code=404, detail="Grupo de trabajo no encontrado")
        ensure_org_access(current_user, group, "grupo de trabajo")
    if "supervisor_id" in update_data and update_data["supervisor_id"]:
        supervisor = db.query(User).filter(User.id == update_data["supervisor_id"]).first()
        if not supervisor:
            raise HTTPException(status_code=404, detail="Supervisor no encontrado")
        ensure_org_access(current_user, supervisor, "supervisor")
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    log_audit(
        db=None,
        action="USER_UPDATED",
        resource_type="users",
        resource_id=user.id,
        current_user=current_user,
        request=request,
        description=f"Usuario actualizado: {user.email}",
    )

    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    """
    Eliminar (desactivar) usuario.
    Solo Administradores.
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    # Verificar permisos de organización
    if current_user.organization_id and user.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para desactivar este usuario"
        )

    # No permitir eliminar a uno mismo
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar tu propio usuario"
        )

    # Soft delete
    user.is_active = False
    db.commit()

    log_audit(
        db=None,
        action="USER_DEACTIVATED",
        resource_type="users",
        resource_id=user.id,
        current_user=current_user,
        request=request,
        description=f"Usuario desactivado: {user.email}",
    )

    return {"message": "Usuario desactivado correctamente"}
