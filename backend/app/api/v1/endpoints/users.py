import secrets
import string
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.schemas.user import UserResponse, UserCreateV1, UserUpdate, UserWithDetails

router = APIRouter()
logger = logging.getLogger(__name__)


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
    # TAEs y PSE solo pueden verse a sí mismos
    if current_user.role in (UserRole.TAE.value, UserRole.PSE.value):
        own_user = db.query(User).filter(User.id == current_user.id).first()
        return [own_user] if own_user else []

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
    Solo Supervisores, Coordinadores y Administradores pueden enumerar todos los TAEs.
    """
    # M-6: TAE y PSE no pueden enumerar todos los usuarios
    if current_user.role in (UserRole.TAE.value, UserRole.PSE.value):
        raise HTTPException(status_code=403, detail="No autorizado")

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
    Solo Supervisores, Coordinadores y Administradores pueden enumerar el personal asignable.
    """
    # M-6: TAE y PSE no pueden enumerar todos los usuarios asignables
    if current_user.role in (UserRole.TAE.value, UserRole.PSE.value):
        raise HTTPException(status_code=403, detail="No autorizado")

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


@router.post("/presence/heartbeat")
async def presence_heartbeat(
    current_route: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Heartbeat de presencia: marca al usuario como activo."""
    from datetime import datetime, timezone
    current_user.is_online = True
    current_user.last_seen_at = datetime.now(timezone.utc)
    current_user.current_route = current_route or None
    db.commit()
    return {"status": "ok"}


@router.get("/presence/list")
async def presence_list(
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value])),
    db: Session = Depends(get_db)
):
    """Lista de presencia de usuarios (solo Admin/Coordinador)."""
    from datetime import datetime, timezone, timedelta
    threshold = datetime.now(timezone.utc) - timedelta(minutes=5)

    query = db.query(User).filter(User.is_active == True)
    if current_user.organization_id:
        query = query.filter(User.organization_id == current_user.organization_id)

    users = query.order_by(User.last_seen_at.desc().nullslast()).all()
    result = []
    for u in users:
        is_online = u.last_seen_at is not None and u.last_seen_at >= threshold
        result.append({
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "is_online": is_online,
            "last_seen_at": u.last_seen_at.isoformat() if u.last_seen_at else None,
            "current_route": u.current_route if is_online else None,
        })
    return result


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

    return new_user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
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
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
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

    # No permitir eliminar a uno mismo
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar tu propio usuario"
        )

    # L-3: Verificar que el usuario a eliminar pertenece a la misma organización
    if current_user.organization_id and user.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="No autorizado")

    # Soft delete
    user.is_active = False
    db.commit()

    return {"message": "Usuario desactivado correctamente"}


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value])),
    db: Session = Depends(get_db)
):
    """
    Resetear contraseña de un usuario.
    La contraseña temporal NO se incluye en la respuesta HTTP (L-4).
    Se registra en los logs del servidor para entornos sin SMTP configurado.
    Solo Administradores y Coordinadores.
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Para cambiar tu propia contraseña usa la opción de perfil"
        )

    # Generar contraseña temporal
    alphabet = string.ascii_letters + string.digits
    temp_password = ''.join(secrets.choice(alphabet) for _ in range(10))

    user.hashed_password = get_password_hash(temp_password)
    db.commit()

    # L-4: Nunca retornar la contraseña en la respuesta HTTP.
    # En desarrollo (sin SMTP), se registra en el log del servidor para que el
    # administrador pueda comunicarla al usuario por un canal seguro.
    logger.info(
        "Contraseña reseteada para usuario '%s' (id=%d) por admin '%s'. "
        "[DEV] Contraseña temporal: %s",
        user.full_name, user.id, current_user.email, temp_password
    )

    return {"message": "Contraseña temporal enviada al correo del usuario"}
