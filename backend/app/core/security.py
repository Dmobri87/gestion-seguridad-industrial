import hmac
import hashlib
import uuid
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import jwt, JWTError

from app.core.config import SECRET_KEY, ALGORITHM, TOKEN_EXPIRE_MINUTES, APP_NAME

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────────────────────────
BCRYPT_ROUNDS = 13  # Aumentado de 12 a 13 para mayor seguridad en 2026
JWT_AUDIENCE = "api.seguridad-industrial"
JWT_ISSUER = APP_NAME


# ──────────────────────────────────────────────────────────────────
# Redis connection for token revocation (persistent)
# ──────────────────────────────────────────────────────────────────
_redis_client = None
_REVOKED_TOKEN_PREFIX = "revoked_token:"
_TOKEN_EXPIRY_SECONDS = 86400  # 24 hours (tokens expire anyway)


def _get_redis_client():
    """
    Obtiene el cliente Redis para revocación de tokens.
    Crea la conexión la primera vez que se llama.
    Falls back to in-memory if Redis is unavailable.
    """
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "")
        if redis_url:
            try:
                import redis
                _redis_client = redis.from_url(redis_url, decode_responses=True)
                # Test connection
                _redis_client.ping()
                logger.info("Conexión a Redis establecida para revocación de tokens")
            except Exception as e:
                logger.warning(
                    "No se pudo conectar a Redis (%s). Usando fallback en memoria. "
                    "Los tokens revocados NO persistirán entre reinicios.",
                    str(e)
                )
                _redis_client = "fallback"
        else:
            logger.warning(
                "REDIS_URL no configurada. Usando almacenamiento en memoria para tokens revocados. "
                "Los tokens revocados NO persistirán entre reinicios."
            )
            _redis_client = "fallback"
    return _redis_client


# Fallback in-memory storage (solo si Redis no está disponible)
_revoked_jtis_fallback: set[str] = set()


def revoke_token(jti: str, expires_in: int = _TOKEN_EXPIRY_SECONDS) -> None:
    """
    Agrega un JTI al conjunto de tokens revocados.
    Usa Redis si está disponible, fallback a memoria si no.

    Args:
        jti: El JWT ID del token a revocar.
        expires_in: Tiempo en segundos hasta que expire el registro de revocación.
    """
    client = _get_redis_client()

    if client and client != "fallback":
        try:
            key = f"{_REVOKED_TOKEN_PREFIX}{jti}"
            client.setex(key, expires_in, "1")
            logger.info("Token revocado en Redis: jti=%s", jti)
            return
        except Exception as e:
            logger.warning("Error guardando token revocado en Redis: %s", str(e))

    # Fallback a memoria
    _revoked_jtis_fallback.add(jti)
    logger.info("Token revocado en memoria: jti=%s", jti)


def is_token_revoked(jti: str) -> bool:
    """
    Verifica si un JTI ha sido revocado.
    Consulta Redis si está disponible, fallback a memoria si no.

    Args:
        jti: El JWT ID a verificar.

    Returns:
        True si el token ha sido revocado.
    """
    client = _get_redis_client()

    if client and client != "fallback":
        try:
            key = f"{_REVOKED_TOKEN_PREFIX}{jti}"
            return client.exists(key) > 0
        except Exception as e:
            logger.warning("Error verificando token revocado en Redis: %s", str(e))

    # Fallback a memoria
    return jti in _revoked_jtis_fallback


# ──────────────────────────────────────────────────────────────────
# Password hashing
# ──────────────────────────────────────────────────────────────────
def get_password_hash(password: str) -> str:
    """
    Encripta una contrasena usando bcrypt con factor de costo 12.

    Args:
        password: Contrasena en texto plano

    Returns:
        Hash bcrypt de la contrasena
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contrasena coincide con su hash.
    Soporta tanto el nuevo formato bcrypt como el legacy SHA-256.

    Args:
        plain_password: Contrasena en texto plano
        hashed_password: Hash almacenado en la base de datos

    Returns:
        True si coinciden, False en caso contrario
    """
    try:
        # Nuevo formato: bcrypt (empieza con $2b$ o $2a$)
        if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8")
            )

        # Legacy: SHA-256 con salt (formato: salt$hash)
        if "$" in hashed_password and not hashed_password.startswith("$"):
            salt, stored_hash = hashed_password.split("$", 1)
            hash_obj = hashlib.sha256((salt + plain_password).encode())
            return hmac.compare_digest(hash_obj.hexdigest(), stored_hash)

        return False
    except (ValueError, TypeError) as e:
        logger.warning("Error verificando contrasena: %s", str(e))
        return False


def needs_rehash(hashed_password: str) -> bool:
    """Verifica si un hash necesita ser actualizado (de SHA-256 a bcrypt)."""
    if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
        try:
            cost = int(hashed_password.split("$")[2])
            return cost < BCRYPT_ROUNDS
        except (IndexError, ValueError):
            return True
    return True  # Legacy SHA-256 siempre necesita rehash


# ──────────────────────────────────────────────────────────────────
# JWT creation and verification
# ──────────────────────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT con jti (JWT ID) para tracking y revocacion.
    Incluye claims de seguridad: aud (audience), iss (issuer), nbf (not before).

    Args:
        data: Informacion a codificar en el token
        expires_delta: Tiempo de expiracion personalizado

    Returns:
        Token JWT como string
    """
    to_encode = data.copy()

    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": now,
        "nbf": now,  # Not Before: token válido desde ahora
        "jti": uuid.uuid4().hex,
        "aud": JWT_AUDIENCE,  # Audience: para qué API es este token
        "iss": JWT_ISSUER,  # Issuer: quién emitió el token
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_access_token(token: str) -> Optional[dict]:
    """
    Decodifica y valida un token JWT, incluyendo verificacion de revocacion.
    Valida: firma, expiración, audience, issuer, y revocación.

    Args:
        token: Token JWT como string.

    Returns:
        El payload decodificado si el token es valido, None en caso contrario.
    """
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
            options={
                "require_exp": True,
                "require_iat": True,
                "require_sub": True,
            }
        )
    except JWTError as e:
        logger.debug("Error decodificando JWT: %s", str(e))
        return None

    # Verificar campos obligatorios adicionales
    if payload.get("user_id") is None:
        logger.warning("Token sin user_id")
        return None

    # Verificar revocacion por JTI
    jti = payload.get("jti")
    if jti and is_token_revoked(jti):
        logger.warning("Intento de uso de token revocado: jti=%s, sub=%s", jti, payload.get("sub"))
        return None

    return payload
