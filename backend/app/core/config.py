"""
Configuracion centralizada de la aplicacion.

Carga todas las variables de entorno con valores por defecto seguros
y valida configuraciones criticas al momento de importar el modulo.
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────
# Seguridad y autenticacion
# ──────────────────────────────────────────────────────────────────
SECRET_KEY: str = os.getenv("SECRET_KEY", "")
ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# ──────────────────────────────────────────────────────────────────
# Aplicacion
# ──────────────────────────────────────────────────────────────────
DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
APP_NAME: str = os.getenv("APP_NAME", "Gestión GAE")
APP_VERSION: str = os.getenv("APP_VERSION", "2.0.0")

# ──────────────────────────────────────────────────────────────────
# Base de datos
# ──────────────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./seguridad_industrial.db")

# ──────────────────────────────────────────────────────────────────
# CORS y hosts
# ──────────────────────────────────────────────────────────────────
_cors_raw: str = os.getenv("CORS_ORIGINS", "http://localhost:3000")
CORS_ORIGINS: list[str] = [o.strip() for o in _cors_raw.split(",") if o.strip()]

_hosts_raw: str = os.getenv("ALLOWED_HOSTS", "*")
ALLOWED_HOSTS: list[str] = [h.strip() for h in _hosts_raw.split(",") if h.strip()]

# ──────────────────────────────────────────────────────────────────
# SMTP / Email
# ──────────────────────────────────────────────────────────────────
SMTP_HOST: str = os.getenv("SMTP_HOST", "")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM: str = os.getenv("SMTP_FROM", "noreply@seguridad-industrial.com")

# ──────────────────────────────────────────────────────────────────
# Rate limiting y OTP
# ──────────────────────────────────────────────────────────────────
MAX_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
OTP_EXPIRE_MINUTES: int = int(os.getenv("OTP_EXPIRE_MINUTES", "5"))


# ──────────────────────────────────────────────────────────────────
# Validacion al inicio
# ──────────────────────────────────────────────────────────────────
_INSECURE_DEFAULTS = {
    "CAMBIAR_ESTO_generar_con_python_secrets_token_urlsafe_64",
    "changeme",
    "secret",
    "your-secret-key",
    "",
}


def validate_settings() -> None:
    """
    Valida que los ajustes criticos esten correctamente configurados.
    Lanza ValueError si alguna validacion falla en produccion.
    En modo DEBUG solo emite advertencias.
    """
    errors: list[str] = []

    # SECRET_KEY obligatoria y segura
    if not SECRET_KEY:
        errors.append("SECRET_KEY no esta definida en las variables de entorno.")
    elif SECRET_KEY in _INSECURE_DEFAULTS:
        errors.append(
            "SECRET_KEY tiene un valor por defecto inseguro. "
            "Genere una clave con: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
        )
    elif len(SECRET_KEY) < 32:
        errors.append("SECRET_KEY debe tener al menos 32 caracteres.")

    # En produccion, verificar SMTP
    if not DEBUG:
        if not SMTP_HOST or not SMTP_USER:
            logger.warning(
                "SMTP no configurado en modo produccion. "
                "Los codigos OTP NO se enviaran por email."
            )

    # En produccion, verificar que no se use SQLite
    if not DEBUG and DATABASE_URL.startswith("sqlite"):
        logger.warning(
            "Usando SQLite en modo produccion. "
            "Se recomienda usar PostgreSQL para entornos de produccion."
        )

    # En produccion, verificar ALLOWED_HOSTS
    if not DEBUG and ALLOWED_HOSTS == ["*"]:
        logger.warning(
            "ALLOWED_HOSTS es '*' en modo produccion. "
            "Se recomienda restringir a los dominios esperados."
        )

    if errors:
        for err in errors:
            logger.critical("Error de configuracion: %s", err)
        raise ValueError(
            "Configuracion invalida al iniciar la aplicacion:\n  - "
            + "\n  - ".join(errors)
        )

    logger.info("Configuracion validada correctamente (DEBUG=%s)", DEBUG)


# Ejecutar validacion al importar el modulo
validate_settings()
