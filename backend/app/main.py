import os
import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager

# ─── Logging ───
# Structured logging must be initialised before any logger is used.
from app.core.logging_config import setup_logging
setup_logging()

logger = logging.getLogger(__name__)

# Request logging middleware
from app.middleware.request_logging import RequestLoggingMiddleware

# Centralised config (validates settings on import)
from app.core.config import (
    DEBUG,
    CORS_ORIGINS,
    ALLOWED_HOSTS,
)

from app.core.database import engine, Base

# Directorio de uploads
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(os.path.join(UPLOAD_DIR, "evidences"), exist_ok=True)


class UTF8Middleware(BaseHTTPMiddleware):
    """Middleware para garantizar UTF-8 en todas las respuestas JSON."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type and "charset" not in content_type:
            response.headers["content-type"] = "application/json; charset=utf-8"
        return response


class SecurityHeadersMiddleware:
    """Middleware ASGI puro para agregar headers de seguridad."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                security_headers = [
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"x-xss-protection", b"1; mode=block"),
                    (b"referrer-policy", b"strict-origin-when-cross-origin"),
                    (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
                ]
                path = scope.get("path", "")
                if path.startswith("/api/"):
                    security_headers.extend([
                        (b"cache-control", b"no-store, no-cache, must-revalidate"),
                        (b"pragma", b"no-cache"),
                    ])
                existing = list(message.get("headers", []))
                existing.extend(security_headers)
                message["headers"] = existing
            await send(message)

        await self.app(scope, receive, send_with_headers)



# Importar todos los modelos para que SQLAlchemy los registre
from app.models import (
    # Core
    Organization, Department, User, WorkGroup,
    # Actividades
    ActivityCategory, ActivityTemplate,
    # Planificacion
    MonthlyPlan, PlanningCycle, PlannedActivity,
    # Ejecucion
    ActivityExecution, ExecutionFile, ExecutionHistory,
    # Emergencias
    EmergencyType, Emergency, EmergencyResource, EmergencyFile,
    # Equipos
    EquipmentCategory, Equipment, EquipmentMaintenance, EquipmentInspection, EquipmentFile, EquipmentNovelty,
    # Certificaciones
    CertificationType, UserCertification, VehicleDocument, CertificationAlert, Notification, NotificationSetting,
    # Cumplimiento
    ComplianceMetric, MonthlySummary, AnnualSummary, Accident, SavedReport, ScheduledReport, AuditLog,
)

def _run_migrations():
    """Ejecuta migraciones incrementales para agregar columnas nuevas a tablas existentes."""
    from sqlalchemy import inspect, text
    inspector = inspect(engine)

    # Migracion: Agregar columnas OTP al modelo User
    if "users" in inspector.get_table_names():
        existing_columns = {col["name"] for col in inspector.get_columns("users")}
        migrations = []

        if "otp_code" not in existing_columns:
            migrations.append("ALTER TABLE users ADD COLUMN otp_code VARCHAR(64)")
        if "otp_expires_at" not in existing_columns:
            migrations.append("ALTER TABLE users ADD COLUMN otp_expires_at DATETIME")
        if "otp_attempts" not in existing_columns:
            migrations.append("ALTER TABLE users ADD COLUMN otp_attempts INTEGER DEFAULT 0")

        if migrations:
            with engine.begin() as conn:
                for sql in migrations:
                    conn.execute(text(sql))
                    logger.info("Migracion ejecutada: %s", sql)
            logger.info("Migraciones de 2FA completadas exitosamente")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager para la aplicacion."""
    # Startup: Crear las tablas en la base de datos
    Base.metadata.create_all(bind=engine)
    logger.info("Tablas de base de datos creadas/verificadas")

    # Ejecutar migraciones incrementales
    try:
        _run_migrations()
    except Exception:
        logger.exception("Error ejecutando migraciones")

    logger.info("CORS origenes permitidos: %s", CORS_ORIGINS)
    logger.info("Hosts confiables: %s", ALLOWED_HOSTS)
    logger.info("DEBUG=%s", DEBUG)
    yield
    # Shutdown
    logger.info("Aplicacion cerrada")



# Crear la aplicacion FastAPI
# En produccion, deshabilitar docs interactivos
app = FastAPI(
    title="Gestión GAE",
    description="""
    API para Gestión GAE - Sistema de Gestión Empresarial.

    ## Módulos

    * **Planificación** - Gestión de planes mensuales por TAE
    * **Ejecución** - Registro de actividades ejecutadas
    * **Emergencias** - Gestión de emergencias y tiempos de respuesta
    * **Equipos** - Inventario y mantenimiento de equipos
    * **Certificaciones** - Control de vencimientos
    * **Cumplimiento** - Dashboard y reportes
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
)

# ──────────────────────────────────────────────────────────────────
# Middleware (LIFO - el ultimo add_middleware es el mas externo)
# ──────────────────────────────────────────────────────────────────

# 1. UTF-8 (mas interno)
app.add_middleware(UTF8Middleware)

# 2. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Total-Count"],
)

# 3. Trusted Host middleware
#    Solo se activa si ALLOWED_HOSTS no es ["*"] (wildcard = sin restriccion)
if ALLOWED_HOSTS != ["*"]:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=ALLOWED_HOSTS,
    )

# 4. Security headers (ASGI puro para fiabilidad)
app.add_middleware(SecurityHeadersMiddleware)

# 5. Request logging (outermost - captures total duration including all middleware)
app.add_middleware(RequestLoggingMiddleware)


# ─── Global Exception Handlers ───

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Manejo de errores de validacion sin exponer detalles internos."""
    logger.warning("Error de validacion en %s: %s", request.url.path, str(exc))

    if DEBUG:
        errors = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error.get("loc", []))
            errors.append({"field": field, "message": error.get("msg", "Error de validacion")})
        return JSONResponse(
            status_code=422,
            content={"detail": "Error de validacion en los datos enviados", "errors": errors},
        )

    # Production: no field-level detail
    return JSONResponse(
        status_code=422,
        content={"detail": "Error de validacion en los datos enviados"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Captura excepciones no manejadas. No expone detalles internos en produccion."""
    logger.exception("Error no manejado en %s: %s", request.url.path, str(exc))

    if DEBUG:
        # En debug, incluir tipo de excepcion y mensaje para facilitar desarrollo
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Error interno del servidor",
                "error": f"{type(exc).__name__}: {exc}",
            },
        )

    # Production: mensaje generico, sin stack traces ni nombres de clase
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
    )


# Servir archivos estaticos (uploads/evidencias)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Importar y registrar rutas
from app.api.v1 import api_router
app.include_router(api_router, prefix="/api/v1")


# ──────────────────────────────────────────────────────────────────
# Root and health endpoints
# ──────────────────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
async def root():
    """Endpoint raiz con informacion del sistema."""
    return {
        "name": "Sistema de Gestion de Seguridad Industrial",
        "version": "2.0.0",
        "status": "running",
        "api_v1": "/api/v1",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check basico para Docker healthchecks y balanceadores de carga.
    Retorna status y timestamp UTC.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health/detailed", tags=["Health"])
async def health_check_detailed():
    """
    Health check detallado que verifica todas las dependencias:
    - Base de datos (PostgreSQL/SQLite)
    - Redis (si está configurado)
    - Sistema de archivos (directorio de uploads)
    """
    from sqlalchemy import text
    from app.core.database import SessionLocal
    import os
    import shutil

    checks = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {}
    }

    # Check 1: Database
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["checks"]["database"] = {"status": "healthy", "message": "Connected"}
    except Exception as e:
        checks["checks"]["database"] = {"status": "unhealthy", "message": str(e)}
        checks["status"] = "degraded"

    # Check 2: Redis (if configured)
    redis_url = os.getenv("REDIS_URL", "")
    if redis_url:
        try:
            import redis
            r = redis.from_url(redis_url)
            r.ping()
            checks["checks"]["redis"] = {"status": "healthy", "message": "Connected"}
        except Exception as e:
            checks["checks"]["redis"] = {"status": "unhealthy", "message": str(e)}
            checks["status"] = "degraded"
    else:
        checks["checks"]["redis"] = {"status": "skipped", "message": "REDIS_URL not configured"}

    # Check 3: Filesystem (uploads directory)
    try:
        if os.path.exists(UPLOAD_DIR) and os.access(UPLOAD_DIR, os.W_OK):
            # Get disk usage
            total, used, free = shutil.disk_usage(UPLOAD_DIR)
            free_gb = free / (1024 ** 3)
            checks["checks"]["filesystem"] = {
                "status": "healthy" if free_gb > 1 else "warning",
                "message": f"Writable, {free_gb:.2f} GB free"
            }
            if free_gb < 1:
                checks["status"] = "degraded"
        else:
            checks["checks"]["filesystem"] = {"status": "unhealthy", "message": "Upload directory not writable"}
            checks["status"] = "degraded"
    except Exception as e:
        checks["checks"]["filesystem"] = {"status": "unhealthy", "message": str(e)}
        checks["status"] = "degraded"

    # Return appropriate status code
    status_code = 200 if checks["status"] == "healthy" else 503 if checks["status"] == "unhealthy" else 200
    return JSONResponse(content=checks, status_code=status_code)
