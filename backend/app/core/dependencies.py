from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Callable, Optional
from enum import Enum
import logging

from app.core.security import verify_access_token
from app.core.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

# Configurar el esquema OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ──────────────────────────────────────────────────────────────────
# Enum de Roles del Sistema
# ──────────────────────────────────────────────────────────────────
class UserRole(str, Enum):
    """
    Roles disponibles en el sistema.
    Usar este enum en lugar de strings para evitar errores de tipeo.
    """
    ADMIN = "Administrador"          # Acceso total al sistema
    COORDINATOR = "Coordinador"       # Crea planes, aprueba, gestiona equipos
    SUPERVISOR = "Supervisor"         # Revisa, aprueba ejecuciones
    TAE = "TAE"                       # Técnico Atención Emergencias - Ejecuta tareas
    PSE = "PSE"                       # Personal Soporte Emergencias - Ejecuta tareas
    PARAMEDIC = "Paramedico"          # Personal médico
    EMPLOYEE = "Empleado"             # Usuario general
    GUEST = "Invitado"                # Acceso limitado de solo lectura


# Conjuntos de roles para validaciones comunes
ADMIN_ROLES = {UserRole.ADMIN}
MANAGEMENT_ROLES = {UserRole.ADMIN, UserRole.COORDINATOR}
SUPERVISOR_ROLES = {UserRole.ADMIN, UserRole.COORDINATOR, UserRole.SUPERVISOR}
OPERATIONAL_ROLES = {UserRole.TAE, UserRole.PSE, UserRole.PARAMEDIC}
ALL_ROLES = set(UserRole)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Obtener usuario actual desde el token JWT.
    Valida firma, expiracion, revocacion y organization_id del token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: int = payload.get("user_id")
    token_org_id: Optional[int] = payload.get("organization_id")

    # Buscar usuario en la base de datos
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado"
        )

    # Validar que el organization_id del token coincida con el del usuario
    # Esto previene el uso de tokens si el usuario fue movido a otra organización
    if token_org_id is not None and user.organization_id != token_org_id:
        logger.warning(
            "Token con organization_id inconsistente: token=%s, user=%s, user_id=%s",
            token_org_id, user.organization_id, user_id
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido. Por favor inicie sesion nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_roles(allowed_roles: List[str]) -> Callable:
    """
    Dependencia para requerir roles especificos.
    Acepta strings con los nombres de los roles.

    Uso:
        @router.get("/admin-only")
        async def admin_endpoint(
            current_user: User = Depends(require_roles(["Administrador"]))
        ):
            ...

        # También puede usar los valores del enum
        current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value]))
    """
    # Crear conjunto de valores permitidos
    allowed_role_values = set(allowed_roles)

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_role_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para esta accion"
            )
        return current_user

    return role_checker


def require_same_organization(
    resource_org_id: int,
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verifica que el usuario pertenezca a la misma organización que el recurso.
    Útil para validaciones multi-tenant.
    """
    if current_user.organization_id != resource_org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a recursos de otra organizacion"
        )
    return current_user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Obtener usuario activo actual.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    return current_user


# ──────────────────────────────────────────────────────────────────
# Dependencias para roles especificos (usando enum)
# ──────────────────────────────────────────────────────────────────
def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Requiere rol de Administrador."""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de Administrador"
        )
    return current_user


def get_coordinator_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Requiere rol de Coordinador o superior."""
    allowed_values = {UserRole.ADMIN.value, UserRole.COORDINATOR.value}
    if current_user.role not in allowed_values:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de Coordinador o superior"
        )
    return current_user


def get_supervisor_or_above(
    current_user: User = Depends(get_current_user)
) -> User:
    """Requiere rol de Supervisor o superior."""
    allowed_values = {r.value for r in SUPERVISOR_ROLES}
    if current_user.role not in allowed_values:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de Supervisor o superior"
        )
    return current_user


def get_operational_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Requiere rol operativo (TAE, PSE, Paramedico) o superior."""
    allowed_values = {r.value for r in (OPERATIONAL_ROLES | SUPERVISOR_ROLES)}
    if current_user.role not in allowed_values:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol operativo o de supervision"
        )
    return current_user
