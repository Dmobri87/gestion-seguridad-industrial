import os
import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

# ─── Logging ───
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

from app.core.database import engine, Base

# Directorio de uploads
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(os.path.join(UPLOAD_DIR, "evidences"), exist_ok=True)

# ─── CORS: leer orígenes desde .env ───
_cors_raw = os.getenv("CORS_ORIGINS", "http://localhost:3000")
CORS_ORIGINS = [origin.strip() for origin in _cors_raw.split(",") if origin.strip()]


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
    # Planificación
    MonthlyPlan, PlanningCycle, PlannedActivity,
    # Ejecución
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

    # Migración: Agregar columnas OTP al modelo User
    if "users" in inspector.get_table_names():
        existing_columns = {col["name"] for col in inspector.get_columns("users")}
        migrations = []

        if "otp_code" not in existing_columns:
            migrations.append("ALTER TABLE users ADD COLUMN otp_code VARCHAR(6)")
        if "otp_expires_at" not in existing_columns:
            migrations.append("ALTER TABLE users ADD COLUMN otp_expires_at DATETIME")
        if "otp_attempts" not in existing_columns:
            migrations.append("ALTER TABLE users ADD COLUMN otp_attempts INTEGER DEFAULT 0")

        if migrations:
            with engine.begin() as conn:
                for sql in migrations:
                    conn.execute(text(sql))
                    logger.info("Migración ejecutada: %s", sql)
            logger.info("Migraciones de 2FA completadas exitosamente")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager para la aplicación."""
    # Startup: Crear las tablas en la base de datos
    Base.metadata.create_all(bind=engine)
    logger.info("Tablas de base de datos creadas/verificadas")

    # Ejecutar migraciones incrementales
    try:
        _run_migrations()
    except Exception:
        logger.exception("Error ejecutando migraciones")

    logger.info("CORS orígenes permitidos: %s", CORS_ORIGINS)
    yield
    # Shutdown
    logger.info("Aplicación cerrada")



# Determinar si estamos en modo debug
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

# Crear la aplicación FastAPI
# En producción, deshabilitar docs interactivos
app = FastAPI(
    title="Sistema de Gestión de Seguridad Industrial",
    description="""
    API para el Sistema Enterprise de Gestión de Seguridad Industrial y Salud Ocupacional.

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

# Middleware: LIFO - el último add_middleware es el más externo
# 1. UTF-8 (más interno)
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

# 3. Security headers (más externo - ASGI puro para fiabilidad)
app.add_middleware(SecurityHeadersMiddleware)

# ─── Global Exception Handlers ───

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Manejo de errores de validación sin exponer detalles internos."""
    logger.warning("Error de validación en %s: %s", request.url.path, str(exc))
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error.get("loc", []))
        errors.append({"field": field, "message": error.get("msg", "Error de validación")})
    return JSONResponse(
        status_code=422,
        content={"detail": "Error de validación en los datos enviados", "errors": errors},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Captura excepciones no manejadas. No expone detalles internos."""
    logger.exception("Error no manejado en %s: %s", request.url.path, str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
    )


# Servir archivos estáticos (uploads/evidencias)
# TODO: En producción, servir uploads detrás de autenticación
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Importar y registrar rutas
from app.api.v1 import api_router
app.include_router(api_router, prefix="/api/v1")

# Rutas legacy deshabilitadas - usar /api/v1 en su lugar
# from app.routes import users, auth, programs, activities, executions, reports, assignments
# app.include_router(auth.router, tags=["Auth (Legacy)"])
# app.include_router(users.router, tags=["Users (Legacy)"])
# app.include_router(programs.router, tags=["Programs (Legacy)"])
# app.include_router(activities.router, tags=["Activities (Legacy)"])
# app.include_router(executions.router, tags=["Executions (Legacy)"])
# app.include_router(reports.router, tags=["Reports (Legacy)"])
# app.include_router(assignments.router, tags=["Assignments (Legacy)"])


@app.get("/", tags=["Root"])
async def root():
    """Endpoint raíz con información del sistema."""
    return {
        "name": "Sistema de Gestión de Seguridad Industrial",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "api_v1": "/api/v1"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check para monitoreo."""
    return {"status": "healthy"}
