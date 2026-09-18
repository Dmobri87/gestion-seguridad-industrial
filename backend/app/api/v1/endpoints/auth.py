from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import time
import secrets
import logging
import os

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash, needs_rehash
from app.core.audit import log_audit
from app.core.dependencies import get_current_user, get_admin_user
from app.core.email import send_otp_email, is_smtp_configured
from app.core.ratelimit import check_rate_limit_redis
from app.models.user import User
from app.schemas.user import (
    UserLogin, Token, UserResponse, PasswordChange, PasswordReset,
    UserCreateV1, ProfileUpdate, OTPVerifyRequest, LoginOTPResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Determinar si estamos en modo debug
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
# ─── Rate limiting simple para login ───
_login_attempts: dict = defaultdict(list)
MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300  # 5 minutos

# ─── Rate limiting para verificación OTP ───
_otp_attempts: dict = defaultdict(list)
MAX_OTP_ATTEMPTS = 5
OTP_WINDOW_SECONDS = 300  # 5 minutos

# ─── Duración del OTP ───
OTP_EXPIRATION_MINUTES = 5


def _check_rate_limit(identifier: str):
    """Verifica rate limit por IP/email. Máximo 5 intentos cada 5 minutos."""
    if not check_rate_limit_redis(f"rl:login:{identifier}", MAX_LOGIN_ATTEMPTS, LOGIN_WINDOW_SECONDS):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos de inicio de sesión. Intente de nuevo en 5 minutos."
        )

    now = time.time()
    # Limpiar intentos viejos
    _login_attempts[identifier] = [t for t in _login_attempts[identifier] if now - t < LOGIN_WINDOW_SECONDS]
    if len(_login_attempts[identifier]) >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos de inicio de sesión. Intente de nuevo en 5 minutos."
        )
    _login_attempts[identifier].append(now)


def _check_otp_rate_limit(identifier: str):
    """Verifica rate limit para intentos de OTP. Máximo 5 intentos cada 5 minutos."""
    if not check_rate_limit_redis(f"rl:otp:{identifier}", MAX_OTP_ATTEMPTS, OTP_WINDOW_SECONDS):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos de verificación. Intente de nuevo en 5 minutos."
        )

    now = time.time()
    _otp_attempts[identifier] = [t for t in _otp_attempts[identifier] if now - t < OTP_WINDOW_SECONDS]
    if len(_otp_attempts[identifier]) >= MAX_OTP_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos de verificación. Intente de nuevo en 5 minutos."
        )
    _otp_attempts[identifier].append(now)


def _generate_otp() -> str:
    """Genera un código OTP de 6 dígitos criptográficamente seguro."""
    return f"{secrets.randbelow(1000000):06d}"


@router.post("/login")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Paso 1 de autenticación: Valida email + contraseña y envía código OTP.
    Retorna requires_2fa=true indicando que se necesita verificación OTP.
    Rate limited: máx 5 intentos cada 5 minutos.
    """
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"{client_ip}:{form_data.username}"
    _check_rate_limit(rate_key)

    # Buscar usuario por email
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user:
        logger.warning("Login fallido - email no encontrado: %s desde IP: %s", form_data.username, client_ip)
        log_audit(
            db=None,
            action="LOGIN_FAILED",
            resource_type="auth",
            resource_id=None,
            current_user=None,
            request=request,
            description=f"Login fallido - email no encontrado: {form_data.username}",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verificar contraseña
    if not verify_password(form_data.password, user.hashed_password):
        logger.warning("Login fallido - contraseña incorrecta para: %s desde IP: %s", form_data.username, client_ip)
        log_audit(
            db=None,
            action="LOGIN_FAILED",
            resource_type="auth",
            resource_id=user.id,
            current_user=None,
            request=request,
            description=f"Login fallido - contraseña incorrecta para: {form_data.username}",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verificar si el usuario está activo
    if not user.is_active:
        logger.warning("Login fallido - usuario desactivado: %s", form_data.username)
        log_audit(
            db=None,
            action="LOGIN_BLOCKED",
            resource_type="auth",
            resource_id=user.id,
            current_user=None,
            request=request,
            description=f"Login bloqueado - usuario desactivado: {form_data.username}",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado"
        )

    # Rehash automático de SHA-256 legacy a bcrypt
    if needs_rehash(user.hashed_password):
        user.hashed_password = get_password_hash(form_data.password)
        logger.info("Contraseña migrada a bcrypt para usuario: %s", user.email)

    # Generar OTP y almacenarlo
    otp_code = _generate_otp()
    user.otp_code = otp_code
    user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRATION_MINUTES)
    user.otp_attempts = 0

    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Error guardando OTP para: %s", user.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

    # Enviar OTP por email
    email_sent = send_otp_email(
        to_email=user.email,
        otp_code=otp_code,
        user_name=user.full_name
    )

    logger.info(
        "OTP generado para %s desde IP: %s (email enviado: %s)",
        user.email, client_ip, email_sent
    )
    log_audit(
        db=None,
        action="OTP_SENT",
        resource_type="auth",
        resource_id=user.id,
        current_user=user,
        request=request,
        description="OTP generado y enviado",
    )

    # Construir respuesta
    response_data = {
        "requires_2fa": True,
        "message": "Código de verificación enviado a su email"
    }

    # En modo desarrollo (SMTP no configurado), incluir el OTP en la respuesta
    if DEBUG and not is_smtp_configured():
        response_data["dev_otp"] = otp_code

    return response_data


@router.post("/verify-otp")
async def verify_otp(
    request: Request,
    otp_data: OTPVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Paso 2 de autenticación: Verifica el código OTP.
    Si es válido, retorna el token JWT de acceso.
    Rate limited: máx 5 intentos cada 5 minutos por email.
    """
    client_ip = request.client.host if request.client else "unknown"
    otp_rate_key = f"otp:{client_ip}:{otp_data.email}"
    _check_otp_rate_limit(otp_rate_key)

    # Buscar usuario por email
    user = db.query(User).filter(User.email == otp_data.email).first()

    if not user:
        logger.warning("Verify OTP - usuario no encontrado: %s desde IP: %s", otp_data.email, client_ip)
        log_audit(
            db=None,
            action="OTP_VERIFY_FAILED",
            resource_type="auth",
            resource_id=None,
            current_user=None,
            request=request,
            description=f"OTP verify fallido - usuario no encontrado: {otp_data.email}",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código de verificación inválido o expirado"
        )

    # Verificar que el usuario tiene un OTP pendiente
    if not user.otp_code or not user.otp_expires_at:
        logger.warning("Verify OTP - sin OTP pendiente para: %s desde IP: %s", otp_data.email, client_ip)
        log_audit(
            db=None,
            action="OTP_VERIFY_FAILED",
            resource_type="auth",
            resource_id=user.id,
            current_user=user,
            request=request,
            description="OTP verify fallido - sin OTP pendiente",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código de verificación inválido o expirado"
        )

    # Verificar que el OTP no ha expirado
    now = datetime.now(timezone.utc)
    # Asegurar que otp_expires_at tenga timezone info para comparación
    otp_expires = user.otp_expires_at
    if otp_expires.tzinfo is None:
        otp_expires = otp_expires.replace(tzinfo=timezone.utc)

    if now > otp_expires:
        # Limpiar OTP expirado
        user.otp_code = None
        user.otp_expires_at = None
        user.otp_attempts = 0
        try:
            db.commit()
        except Exception:
            db.rollback()
        logger.warning("Verify OTP - código expirado para: %s desde IP: %s", otp_data.email, client_ip)
        log_audit(
            db=None,
            action="OTP_VERIFY_FAILED",
            resource_type="auth",
            resource_id=user.id,
            current_user=user,
            request=request,
            description="OTP expirado",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código de verificación inválido o expirado"
        )

    # Verificar intentos máximos de OTP a nivel de usuario
    if user.otp_attempts >= MAX_OTP_ATTEMPTS:
        # Invalidar OTP por demasiados intentos
        user.otp_code = None
        user.otp_expires_at = None
        user.otp_attempts = 0
        try:
            db.commit()
        except Exception:
            db.rollback()
        logger.warning("Verify OTP - demasiados intentos para: %s desde IP: %s", otp_data.email, client_ip)
        log_audit(
            db=None,
            action="OTP_VERIFY_BLOCKED",
            resource_type="auth",
            resource_id=user.id,
            current_user=user,
            request=request,
            description="OTP bloqueado por demasiados intentos",
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos fallidos. Solicite un nuevo código de verificación."
        )

    # Verificar el código OTP (comparación segura contra timing attacks)
    if not secrets.compare_digest(user.otp_code, otp_data.otp_code):
        user.otp_attempts = (user.otp_attempts or 0) + 1
        try:
            db.commit()
        except Exception:
            db.rollback()
        logger.warning(
            "Verify OTP - código incorrecto para: %s (intento %d) desde IP: %s",
            otp_data.email, user.otp_attempts, client_ip
        )
        log_audit(
            db=None,
            action="OTP_VERIFY_FAILED",
            resource_type="auth",
            resource_id=user.id,
            current_user=user,
            request=request,
            description="OTP inválido",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código de verificación inválido o expirado"
        )

    # OTP válido: limpiar campos OTP
    user.otp_code = None
    user.otp_expires_at = None
    user.otp_attempts = 0
    user.last_login = now

    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Error limpiando OTP para: %s", user.email)

    # Limpiar rate limits de OTP y login
    _otp_attempts.pop(otp_rate_key, None)

    # Crear token JWT
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={
            "sub": user.email,
            "user_id": user.id,
            "role": user.role,
            "organization_id": user.organization_id
        },
        expires_delta=access_token_expires
    )

    logger.info("Login 2FA exitoso: %s desde IP: %s", user.email, client_ip)
    log_audit(
        db=None,
        action="LOGIN_SUCCESS",
        resource_type="auth",
        resource_id=user.id,
        current_user=user,
        request=request,
        description="Login 2FA exitoso",
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 30 * 60,
        "user": UserResponse.model_validate(user)
    }


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreateV1,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Registro de nuevo usuario. Requiere autenticación como Administrador.
    Solo un admin puede crear usuarios y asignar roles.
    """
    # Verificar si el email ya existe
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )

    # Crear usuario
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        employee_code=user_data.employee_code,
        phone=user_data.phone,
        role=user_data.role,
        organization_id=user_data.organization_id,
        department_id=user_data.department_id,
        supervisor_id=user_data.supervisor_id,
        is_active=True,
        is_verified=False
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        logger.exception("Error creando usuario: %s", user_data.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al crear el usuario"
        )

    logger.info("Usuario creado: %s por admin: %s", new_user.email, current_user.email)
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


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Obtener información del usuario actual.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualizar perfil del usuario actual (nombre, teléfono).
    """
    update_data = profile_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se proporcionaron datos para actualizar"
        )

    for field, value in update_data.items():
        setattr(current_user, field, value)

    try:
        db.commit()
        db.refresh(current_user)
    except Exception:
        db.rollback()
        logger.exception("Error actualizando perfil para: %s", current_user.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al actualizar el perfil"
        )

    logger.info("Perfil actualizado para usuario: %s", current_user.email)
    log_audit(
        db=None,
        action="PROFILE_UPDATED",
        resource_type="users",
        resource_id=current_user.id,
        current_user=current_user,
        request=None,
        description="Perfil actualizado",
    )
    return current_user


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cambiar contraseña del usuario actual.
    """
    # Verificar contraseña actual
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )

    # Actualizar contraseña
    current_user.hashed_password = get_password_hash(password_data.new_password)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Error actualizando contraseña para: %s", current_user.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al actualizar la contraseña"
        )

    logger.info("Contraseña cambiada para usuario: %s", current_user.email)
    log_audit(
        db=None,
        action="PASSWORD_CHANGED",
        resource_type="users",
        resource_id=current_user.id,
        current_user=current_user,
        request=None,
        description="Contraseña actualizada",
    )
    return {"message": "Contraseña actualizada correctamente"}


@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user)
):
    """
    Refrescar token JWT.
    """
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={
            "sub": current_user.email,
            "user_id": current_user.id,
            "role": current_user.role,
            "organization_id": current_user.organization_id
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 30 * 60,
        "user": current_user
    }
