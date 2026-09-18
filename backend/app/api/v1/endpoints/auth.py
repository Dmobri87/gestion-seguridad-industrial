from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import secrets
import logging
import hmac

from app.core.config import (
    MAX_LOGIN_ATTEMPTS,
    OTP_EXPIRE_MINUTES,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SECRET_KEY,
)
from app.core.database import get_db
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    hash_refresh_token,
    needs_rehash,
    revoke_token,
    verify_access_token,
)
from app.core.dependencies import get_current_user, get_admin_user, oauth2_scheme
from app.core.email import send_otp_email, is_smtp_configured
from app.core.rate_limiter import get_rate_limiter
from app.models.user import User
from app.schemas.user import (
    UserLogin, Token, UserResponse, PasswordChange, PasswordReset,
    UserCreateV1, ProfileUpdate, OTPVerifyRequest, LoginOTPResponse,
    RefreshTokenRequest, RefreshTokenResponse, ResendOTPRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter()

LOGIN_WINDOW_SECONDS = 300  # 5 minutos

MAX_OTP_ATTEMPTS = 5
OTP_WINDOW_SECONDS = 300  # 5 minutos


def _generate_otp() -> str:
    """Genera un codigo OTP de 8 digitos criptograficamente seguro."""
    return f"{secrets.randbelow(100000000):08d}"


def _hash_otp(otp_code: str) -> str:
    """
    Hashea un codigo OTP para almacenamiento seguro.
    Usa HMAC-SHA256 con la SECRET_KEY del servidor como clave,
    protegiendose contra ataques de rainbow table y extension de longitud.
    """
    import hashlib
    return hmac.new(SECRET_KEY.encode(), otp_code.encode(), hashlib.sha256).hexdigest()


def _verify_otp_hash(otp_code: str, stored_hash: str) -> bool:
    """
    Verifica un codigo OTP contra su hash almacenado.
    Usa comparación segura contra timing attacks.
    """
    computed_hash = _hash_otp(otp_code)
    return secrets.compare_digest(computed_hash, stored_hash)


@router.post("/login")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Paso 1 de autenticacion: Valida email + contraseña y envia codigo OTP.
    Retorna requires_2fa=true indicando que se necesita verificacion OTP.
    Rate limited: max N intentos cada 5 minutos.
    """
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"login:{client_ip}:{form_data.username}"
    limiter = get_rate_limiter()
    if not limiter.is_allowed(rate_key, MAX_LOGIN_ATTEMPTS, LOGIN_WINDOW_SECONDS):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos. Espera 5 minutos."
        )

    # Buscar usuario por email
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user:
        logger.warning("Login fallido - email no encontrado: %s desde IP: %s", form_data.username, client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verificar contraseña
    if not verify_password(form_data.password, user.hashed_password):
        logger.warning("Login fallido - contraseña incorrecta para: %s desde IP: %s", form_data.username, client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verificar si el usuario esta activo
    if not user.is_active:
        logger.warning("Login fallido - usuario desactivado: %s", form_data.username)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado"
        )

    # Rehash automatico de SHA-256 legacy a bcrypt
    if needs_rehash(user.hashed_password):
        user.hashed_password = get_password_hash(form_data.password)
        logger.info("Contraseña migrada a bcrypt para usuario: %s", user.email)

    # Generar OTP, hashearlo y almacenarlo
    otp_code = _generate_otp()
    user.otp_code = _hash_otp(otp_code)  # Almacenar hash, no el código en texto plano
    user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES)
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
    limiter.reset(rate_key)

    # Construir respuesta
    response_data = {
        "requires_2fa": True,
        "message": "Codigo de verificacion enviado a su email"
    }

    # En modo desarrollo (SMTP no configurado), incluir el OTP en la respuesta
    if not is_smtp_configured():
        response_data["dev_otp"] = otp_code

    return response_data


@router.post("/verify-otp")
async def verify_otp(
    request: Request,
    otp_data: OTPVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Paso 2 de autenticacion: Verifica el codigo OTP.
    Si es valido, retorna el token JWT de acceso.
    Rate limited: max 5 intentos cada 5 minutos por email.
    """
    client_ip = request.client.host if request.client else "unknown"
    otp_rate_key = f"otp:{client_ip}:{otp_data.email}"
    limiter = get_rate_limiter()
    if not limiter.is_allowed(otp_rate_key, MAX_OTP_ATTEMPTS, OTP_WINDOW_SECONDS):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos de verificación."
        )

    # Buscar usuario por email
    user = db.query(User).filter(User.email == otp_data.email).first()

    if not user:
        logger.warning("Verify OTP - usuario no encontrado: %s desde IP: %s", otp_data.email, client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Codigo de verificacion invalido o expirado"
        )

    # Verificar que el usuario tiene un OTP pendiente
    if not user.otp_code or not user.otp_expires_at:
        logger.warning("Verify OTP - sin OTP pendiente para: %s desde IP: %s", otp_data.email, client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Codigo de verificacion invalido o expirado"
        )

    # Verificar que el OTP no ha expirado
    now = datetime.now(timezone.utc)
    # Asegurar que otp_expires_at tenga timezone info para comparacion
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
        logger.warning("Verify OTP - codigo expirado para: %s desde IP: %s", otp_data.email, client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Codigo de verificacion invalido o expirado"
        )

    # Verificar intentos maximos de OTP a nivel de usuario
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
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos fallidos. Solicite un nuevo codigo de verificacion."
        )

    # Verificar el codigo OTP (comparacion segura contra timing attacks)
    if not _verify_otp_hash(otp_data.otp_code, user.otp_code):
        user.otp_attempts = (user.otp_attempts or 0) + 1
        try:
            db.commit()
        except Exception:
            db.rollback()
        logger.warning(
            "Verify OTP - codigo incorrecto para: %s (intento %d) desde IP: %s",
            otp_data.email, user.otp_attempts, client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Codigo de verificacion invalido o expirado"
        )

    # OTP valido: limpiar campos OTP
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
    limiter.reset(otp_rate_key)

    # Crear token JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.email,
            "user_id": user.id,
            "role": user.role,
            "organization_id": user.organization_id
        },
        expires_delta=access_token_expires
    )

    refresh_token_raw, refresh_token_hash = create_refresh_token()
    user.refresh_token_hash = refresh_token_hash
    user.refresh_token_expires_at = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        logger.exception("Error guardando refresh token para: %s", user.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

    logger.info("Login 2FA exitoso: %s desde IP: %s", user.email, client_ip)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_raw,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": UserResponse.model_validate(user)
    }


@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Cierra la sesion del usuario revocando el token JWT actual.
    El token queda invalidado inmediatamente y no podra usarse de nuevo.
    """
    payload = verify_access_token(token)
    if payload and payload.get("jti"):
        revoke_token(payload["jti"])
        logger.info("Logout exitoso: %s (jti=%s)", current_user.email, payload["jti"])

    current_user.refresh_token_hash = None
    current_user.refresh_token_expires_at = None
    current_user.is_online = False
    current_user.current_route = None
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Error invalidando refresh token en logout para: %s", current_user.email)

    return {"message": "Sesion cerrada correctamente"}


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreateV1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Registro de nuevo usuario. Requiere autenticacion como Administrador.
    Solo un admin puede crear usuarios y asignar roles.
    """
    # Verificar si el email ya existe
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya esta registrado"
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
    return new_user


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Obtener informacion del usuario actual.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualizar perfil del usuario actual (nombre, telefono).
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
    return {"message": "Contraseña actualizada correctamente"}


@router.post("/refresh-token", response_model=RefreshTokenResponse)
async def refresh_token(
    body: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Intercambia refresh token valido por nuevo access token y nuevo refresh token.
    Rota el refresh token en cada uso.
    """
    token_hash = hash_refresh_token(body.refresh_token)
    user = db.query(User).filter(User.refresh_token_hash == token_hash).first()

    if not user or not user.refresh_token_expires_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido"
        )

    now = datetime.now(timezone.utc)
    refresh_expires = user.refresh_token_expires_at
    if refresh_expires.tzinfo is None:
        refresh_expires = refresh_expires.replace(tzinfo=timezone.utc)

    if now > refresh_expires:
        user.refresh_token_hash = None
        user.refresh_token_expires_at = None
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expirado"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo"
        )

    new_refresh_raw, new_refresh_hash = create_refresh_token()
    user.refresh_token_hash = new_refresh_hash
    user.refresh_token_expires_at = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.email,
            "user_id": user.id,
            "role": user.role,
            "organization_id": user.organization_id
        },
        expires_delta=access_token_expires
    )

    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_raw,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/resend-otp")
async def resend_otp(
    body: ResendOTPRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Reenvía OTP. Cooldown de 60 segundos entre reenvíos.
    Solo reenvía si hay un flujo de login pendiente (otp_code no es None).
    Evita que usuarios no autenticados generen OTPs para cuentas arbitrarias.
    """
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        return {"message": "Si el email existe y hay una sesión pendiente, se enviará un código"}

    # L-2: Solo reenviar si hay un OTP pendiente (sesión de login activa).
    # Si no hay OTP pendiente, retornar respuesta genérica sin generar nada.
    if user.otp_code is None:
        return {"message": "Si el email existe y hay una sesión pendiente, se enviará un código"}

    now = datetime.now(timezone.utc)
    if user.otp_expires_at:
        otp_expires = user.otp_expires_at
        if otp_expires.tzinfo is None:
            otp_expires = otp_expires.replace(tzinfo=timezone.utc)
        created_approximately = otp_expires - timedelta(minutes=OTP_EXPIRE_MINUTES)
        if now - created_approximately < timedelta(seconds=60):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Espera 60 segundos antes de solicitar un nuevo código"
            )

    otp_code = _generate_otp()
    user.otp_code = _hash_otp(otp_code)
    user.otp_expires_at = now + timedelta(minutes=OTP_EXPIRE_MINUTES)
    user.otp_attempts = 0
    db.commit()

    send_otp_email(
        to_email=user.email,
        otp_code=otp_code,
        user_name=user.full_name
    )

    response = {
        "message": "Código reenviado",
        "expires_in": OTP_EXPIRE_MINUTES * 60
    }
    if not is_smtp_configured():
        response["dev_otp"] = otp_code
    return response
