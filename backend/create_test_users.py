"""
Script para crear usuarios de prueba con todos los perfiles.
Ejecutar: python create_test_users.py
"""
from datetime import datetime, date, timedelta
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.organization import Organization
from app.models.department import Department

def create_test_users():
    db = SessionLocal()

    try:
        org = db.query(Organization).first()
        if not org:
            print("ERROR: No existe una organización. Ejecuta primero init_db.py")
            return

        # Buscar departamento de emergencias o crear uno
        dept = db.query(Department).filter(Department.code == "EMER").first()
        if not dept:
            dept = db.query(Department).first()

        print("=== CREANDO/ACTUALIZANDO USUARIOS DE PRUEBA ===\n")

        # Definir usuarios a crear
        test_users = [
            {
                "email": "admin@empresa.com",
                "password": "admin123",
                "full_name": "Administrador Sistema",
                "employee_code": "ADM001",
                "role": "Administrador",
            },
            {
                "email": "coordinador@empresa.com",
                "password": "coord123",
                "full_name": "Pedro Coordinador",
                "employee_code": "COORD001",
                "role": "Coordinador",
            },
            {
                "email": "supervisor@empresa.com",
                "password": "super123",
                "full_name": "Ana Martinez Supervisor",
                "employee_code": "SUP001",
                "role": "Supervisor",
            },
            {
                "email": "tae1@empresa.com",
                "password": "tae123",
                "full_name": "Juan Perez TAE",
                "employee_code": "TAE001",
                "role": "TAE",
            },
            {
                "email": "tae2@empresa.com",
                "password": "tae123",
                "full_name": "Maria Garcia TAE",
                "employee_code": "TAE002",
                "role": "TAE",
            },
            {
                "email": "tae3@empresa.com",
                "password": "tae123",
                "full_name": "Carlos Lopez TAE",
                "employee_code": "TAE003",
                "role": "TAE",
            },
            {
                "email": "paramedico@empresa.com",
                "password": "para123",
                "full_name": "Luis Gomez Paramedico",
                "employee_code": "PAR001",
                "role": "Paramédico",
            },
        ]

        created = 0
        updated = 0

        for user_data in test_users:
            existing = db.query(User).filter(User.email == user_data["email"]).first()

            if existing:
                # Actualizar contraseña y datos
                existing.hashed_password = get_password_hash(user_data["password"])
                existing.full_name = user_data["full_name"]
                existing.role = user_data["role"]
                existing.is_active = True
                existing.is_verified = True
                updated += 1
                print(f"  [ACTUALIZADO] {user_data['email']} - {user_data['role']}")
            else:
                # Crear nuevo usuario
                new_user = User(
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    full_name=user_data["full_name"],
                    employee_code=user_data["employee_code"],
                    role=user_data["role"],
                    organization_id=org.id,
                    department_id=dept.id if dept else None,
                    is_active=True,
                    is_verified=True,
                )
                db.add(new_user)
                created += 1
                print(f"  [CREADO] {user_data['email']} - {user_data['role']}")

        db.commit()

        print("\n" + "="*50)
        print("    USUARIOS DE PRUEBA LISTOS")
        print("="*50)
        print(f"\nCreados: {created} | Actualizados: {updated}")
        print("\n" + "-"*50)
        print("CREDENCIALES DE ACCESO:")
        print("-"*50)
        print("")
        print("ADMINISTRADOR:")
        print("  Email: admin@empresa.com")
        print("  Clave: admin123")
        print("  Permisos: Acceso total, gestión de usuarios")
        print("")
        print("COORDINADOR:")
        print("  Email: coordinador@empresa.com")
        print("  Clave: coord123")
        print("  Permisos: Crear planes, aprobar ejecuciones")
        print("")
        print("SUPERVISOR:")
        print("  Email: supervisor@empresa.com")
        print("  Clave: super123")
        print("  Permisos: Aprobar ejecuciones, ver reportes")
        print("")
        print("TAE (Técnicos de Atención de Emergencias):")
        print("  Email: tae1@empresa.com | Clave: tae123")
        print("  Email: tae2@empresa.com | Clave: tae123")
        print("  Email: tae3@empresa.com | Clave: tae123")
        print("  Permisos: Registrar ejecuciones, ver su plan")
        print("")
        print("PARAMÉDICO:")
        print("  Email: paramedico@empresa.com")
        print("  Clave: para123")
        print("  Permisos: Atender emergencias, registrar ejecuciones")
        print("")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_test_users()
