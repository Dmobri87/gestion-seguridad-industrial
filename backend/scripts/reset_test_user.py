"""
Script para resetear la contrasena de un usuario de prueba.
Ejecutar desde el directorio backend:
    python -m scripts.reset_test_user
"""

import os
import sys

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar variables de entorno necesarias
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-minimum-32-characters")
os.environ.setdefault("DATABASE_URL", "sqlite:///./seguridad_industrial.db")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import get_password_hash
from app.models.user import User
from app.core.database import Base

# Conectar a la base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./seguridad_industrial.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def reset_password(email: str, new_password: str):
    """Resetea la contrasena de un usuario."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"Usuario con email '{email}' no encontrado.")
            return False

        # Generar nuevo hash
        new_hash = get_password_hash(new_password)
        user.hashed_password = new_hash

        # Desactivar 2FA para pruebas
        user.two_factor_enabled = False
        user.otp_code = None
        user.otp_expires_at = None
        user.otp_attempts = 0

        db.commit()
        print(f"Contrasena actualizada para: {user.email}")
        print(f"  - Nombre: {user.full_name}")
        print(f"  - Rol: {user.role}")
        print(f"  - 2FA desactivado para pruebas")
        return True
    finally:
        db.close()


def list_users():
    """Lista todos los usuarios."""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"\nUsuarios en la base de datos ({len(users)}):")
        print("-" * 60)
        for user in users:
            print(f"  - {user.email} | {user.role} | Activo: {user.is_active}")
    finally:
        db.close()


if __name__ == "__main__":
    TEST_EMAIL = "deivinsonn1187@outlook.es"
    TEST_PASSWORD = "Test123456!"

    print("=" * 60)
    print("Reset de usuario de prueba")
    print("=" * 60)

    list_users()

    print("\n" + "=" * 60)
    print(f"Reseteando contrasena para: {TEST_EMAIL}")
    print(f"Nueva contrasena: {TEST_PASSWORD}")
    print("=" * 60)

    if reset_password(TEST_EMAIL, TEST_PASSWORD):
        print("\n[OK] Usuario listo para pruebas!")
        print(f"\nCredenciales de prueba:")
        print(f"  Email: {TEST_EMAIL}")
        print(f"  Password: {TEST_PASSWORD}")
    else:
        print("\n[ERROR] No se pudo resetear el usuario")
