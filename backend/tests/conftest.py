"""
Configuración de pytest para tests del backend.
"""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Configurar variables de entorno para tests
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-minimum-32-characters"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["DEBUG"] = "True"

from app.main import app
from app.core.database import Base, get_db


# Crear motor de test con SQLite en memoria
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override de la dependencia get_db para tests."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Crear tablas antes de los tests y limpiar después."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    """Fixture para obtener una sesión de base de datos."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """Fixture para obtener un cliente de test."""
    return TestClient(app)


@pytest.fixture
def clean_db(db):
    """Fixture para limpiar la base de datos entre tests."""
    yield db
    # Limpiar todas las tablas después del test
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()
