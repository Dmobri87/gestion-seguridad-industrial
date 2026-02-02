import os
import hmac
import hashlib
import uuid
import logging
from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración desde variables de entorno
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Validar que existe la SECRET_KEY y tiene suficiente entropía
if not SECRET_KEY:
    raise ValueError("SECRET_KEY no está definida en las variables de entorno")
if len(SECRET_KEY) < 32:
    raise ValueError("SECRET_KEY debe tener al menos 32 caracteres")

# Factor de costo para bcrypt (2^12 = 4096 iteraciones)
BCRYPT_ROUNDS = 12


def get_password_hash(password: str) -> str:
    """
    Encripta una contraseña usando bcrypt con factor de costo 12.

    Args:
        password: Contraseña en texto plano

    Returns:
        Hash bcrypt de la contraseña
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña coincide con su hash.
    Soporta tanto el nuevo formato bcrypt como el legacy SHA-256.

    Args:
        plain_password: Contraseña en texto plano
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
        logger.warning("Error verificando contraseña: %s", str(e))
        return False


def needs_rehash(hashed_password: str) -> bool:
    """Verifica si un hash necesita ser actualizado (de SHA-256 a bcrypt)."""
    if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
        # Verificar si el factor de costo es el actual
        try:
            # Formato bcrypt: $2b$XX$ donde XX es el costo
            cost = int(hashed_password.split("$")[2])
            return cost < BCRYPT_ROUNDS
        except (IndexError, ValueError):
            return True
    return True  # Legacy SHA-256 siempre necesita rehash


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Crea un token JWT con jti (JWT ID) para tracking.

    Args:
        data: Información a codificar en el token
        expires_delta: Tiempo de expiración personalizado

    Returns:
        Token JWT como string
    """
    to_encode = data.copy()

    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": uuid.uuid4().hex,
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt
