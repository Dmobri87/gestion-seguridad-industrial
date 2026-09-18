"""
Script de inicialización: crea organización base y usuario admin.
Uso: docker compose exec backend python scripts/setup_initial_data.py
"""
import sys
import base64
import secrets

sys.path.insert(0, '/app')

from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash
try:
    import pyotp
except ImportError:
    pyotp = None

# Importa modelos para registrar metadata
import app.models.user
import app.models.organization
import app.models.certification
import app.models.planning


def main():
    print("Creando tablas si no existen...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        from app.models.user import User
        from app.models.organization import Organization

        # Crear organizacion si no existe
        org = db.query(Organization).filter_by(code='CRJ').first()
        if not org:
            org = Organization(
                name='Cerrejon',
                code='CRJ',
                is_active=True,
            )
            db.add(org)
            db.commit()
            db.refresh(org)
            print(f"Organización creada: {org.name} (id={org.id})")
        else:
            print(f"Organización ya existe: {org.name} (id={org.id})")

        # Crear admin si no existe
        admin = db.query(User).filter_by(email='admin@cerrejon.com').first()
        if not admin:
            if pyotp:
                two_factor_secret = pyotp.random_base32()
            else:
                two_factor_secret = base64.b32encode(secrets.token_bytes(20)).decode('ascii').rstrip('=')
            admin = User(
                email='admin@cerrejon.com',
                full_name='Administrador',
                hashed_password=get_password_hash('Dmb..872415'),
                role='Administrador',
                organization_id=org.id,
                is_active=True,
                is_verified=True,
                two_factor_secret=two_factor_secret,
            )
            db.add(admin)
            db.commit()
            print(f"Admin creado: {admin.email}")
        else:
            print(f"Admin ya existe: {admin.email}")

        print("\n✅ Inicialización completada.")
        print("   Email:      admin@cerrejon.com")
        print("   Contraseña: Dmb..872415")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == '__main__':
    main()
