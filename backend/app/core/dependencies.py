from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from typing import List, Callable

from app.core.security import SECRET_KEY, ALGORITHM
from app.core.database import get_db
from app.models.user import User

# Configurar el esquema OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Obtener usuario actual desde el token JWT.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")

        if email is None or user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Buscar usuario en la base de datos
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado"
        )

    return user


def require_roles(allowed_roles: List[str]) -> Callable:
    """
    Dependencia para requerir roles específicos.

    Uso:
        @router.get("/admin-only")
        async def admin_endpoint(
            current_user: User = Depends(require_roles(["Administrador"]))
        ):
            ...
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para esta acción"
            )
        return current_user

    return role_checker


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


# Dependencias para roles específicos
def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Requiere rol de Administrador."""
    if current_user.role != "Administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de Administrador"
        )
    return current_user


def get_coordinator_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Requiere rol de Coordinador o superior."""
    allowed = ["Administrador", "Coordinador"]
    if current_user.role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de Coordinador o superior"
        )
    return current_user
