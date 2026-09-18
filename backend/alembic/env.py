"""
Alembic Environment Configuration

Configura Alembic para usar la misma DATABASE_URL que la aplicacion
y detectar automaticamente los modelos de SQLAlchemy.
"""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar el directorio backend al path para poder importar los modelos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar Base y todos los modelos para que Alembic los detecte
from app.core.database import Base
import app.models  # noqa: F401 - importa todos los modelos registrados en Base.metadata

# Configuracion de Alembic
config = context.config

# Configurar logging desde alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata de los modelos para autogenerate
target_metadata = Base.metadata

# Obtener DATABASE_URL desde el entorno
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./seguridad_industrial.db")

# Para SQLite con ruta relativa, resolver relativo al directorio backend/
if DATABASE_URL.startswith("sqlite:///./"):
    _backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _db_filename = DATABASE_URL.replace("sqlite:///./", "")
    _db_path = os.path.join(_backend_dir, _db_filename)
    DATABASE_URL = f"sqlite:///{_db_path}"


def run_migrations_offline() -> None:
    """
    Ejecutar migraciones en modo 'offline'.

    Genera SQL sin conectarse a la base de datos.
    Util para generar scripts SQL para revision manual.
    """
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Ejecutar migraciones en modo 'online'.

    Se conecta a la base de datos y aplica las migraciones directamente.
    """
    # Configurar el engine segun el tipo de base de datos
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = DATABASE_URL

    if DATABASE_URL.startswith("postgresql"):
        connectable = engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
    elif DATABASE_URL.startswith("sqlite"):
        connectable = engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            connect_args={"check_same_thread": False},
        )
    else:
        connectable = engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
