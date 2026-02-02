import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener la URL de la base de datos desde las variables de entorno
# Si no existe, usar SQLite como fallback para desarrollo local
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./seguridad_industrial.db")

# Para SQLite con ruta relativa, resolver siempre relativo al directorio backend/
if DATABASE_URL.startswith("sqlite:///./"):
    _backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _db_filename = DATABASE_URL.replace("sqlite:///./", "")
    _db_path = os.path.join(_backend_dir, _db_filename)
    DATABASE_URL = f"sqlite:///{_db_path}"

# Crear el engine de SQLAlchemy
if DATABASE_URL.startswith("sqlite"):
    # SQLite necesita connect_args especial
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )

    # Forzar UTF-8 y WAL mode en SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA encoding = 'UTF-8'")
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.close()
else:
    # PostgreSQL u otras bases de datos
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False
    )

# Crear la sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()

# Dependency para FastAPI
def get_db():
    """
    Dependencia que provee una sesión de base de datos.
    
    Se usa en los endpoints así:
    def my_endpoint(db: Session = Depends(get_db)):
        ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()