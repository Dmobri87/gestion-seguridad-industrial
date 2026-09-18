"""
Script de migracion para despliegues nuevos.

Crea todas las tablas si no existen (para despliegues fresh)
y marca el estado actual como 'head' en Alembic.

Uso:
    cd backend
    python scripts/migrate.py

Util para:
    - Primera vez configurando la base de datos en produccion
    - Inicializar la base de datos en un nuevo entorno
"""
import os
import sys
import logging
import subprocess

# Agregar el directorio backend al path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from dotenv import load_dotenv

load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("migrate")


def main():
    """Ejecutar migracion inicial."""
    from app.core.database import engine, DATABASE_URL, Base

    # Importar todos los modelos para registrar las tablas en Base.metadata
    import app.models  # noqa: F401

    db_type = DATABASE_URL.split("://")[0]
    logger.info(f"Conectando a base de datos: {db_type}://***")

    # Paso 1: Crear todas las tablas que no existen
    logger.info("Creando tablas (si no existen)...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tablas creadas exitosamente.")

    # Paso 2: Marcar el estado actual como 'head' en Alembic
    # Esto indica que la base de datos ya tiene todas las migraciones aplicadas
    logger.info("Marcando estado actual en Alembic (stamp head)...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "stamp", "head"],
            cwd=backend_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            logger.info("Alembic stamp head completado exitosamente.")
        else:
            logger.warning(f"Alembic stamp head retorno codigo {result.returncode}")
            if result.stderr:
                logger.warning(f"stderr: {result.stderr}")
    except FileNotFoundError:
        logger.warning(
            "No se pudo ejecutar alembic. "
            "Asegurese de que alembic este instalado: pip install alembic"
        )

    logger.info("Migracion inicial completada.")


if __name__ == "__main__":
    main()
