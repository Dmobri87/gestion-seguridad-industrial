"""
Script para inicializar la base de datos con datos semilla.
"""
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models import (
    Organization, Department, User, UserRole,
    ActivityCategory, ActivityTemplate,
    EmergencyType, EquipmentCategory, CertificationType
)
from app.core.security import get_password_hash
from app.db.seed_data import (
    ACTIVITY_CATEGORIES, ACTIVITY_TEMPLATES, EMERGENCY_TYPES,
    EQUIPMENT_CATEGORIES, CERTIFICATION_TYPES
)


def init_db(db: Session) -> None:
    """Inicializa la base de datos con datos semilla."""

    # Verificar si ya hay datos
    existing_org = db.query(Organization).first()
    if existing_org:
        print("La base de datos ya está inicializada.")
        return

    print("Inicializando base de datos...")

    # 1. Crear organización por defecto
    org = Organization(
        name="Empresa Minera Demo",
        code="MINERA_DEMO",
        description="Organización de demostración",
        is_active=True,
        max_users=100
    )
    db.add(org)
    db.flush()  # Para obtener el ID
    print(f"✓ Organización creada: {org.name}")

    # 2. Crear departamentos
    departments_data = [
        {"name": "CAE Norte", "code": "CAE_NORTE"},
        {"name": "CAE Sur", "code": "CAE_SUR"},
        {"name": "CAE Central", "code": "CAE_CENTRAL"},
        {"name": "Coordinación de Seguridad", "code": "COORD_SEG"},
        {"name": "Administración", "code": "ADMIN"},
    ]

    departments = {}
    for dept_data in departments_data:
        dept = Department(
            name=dept_data["name"],
            code=dept_data["code"],
            organization_id=org.id,
            is_active=True
        )
        db.add(dept)
        db.flush()
        departments[dept_data["code"]] = dept
    print(f"✓ {len(departments)} departamentos creados")

    # 3. Crear usuario administrador
    admin_user = User(
        email="admin@empresa.com",
        hashed_password=get_password_hash("admin123"),
        full_name="Administrador del Sistema",
        employee_code="EMP-001",
        role=UserRole.ADMIN.value,
        organization_id=org.id,
        department_id=departments["ADMIN"].id,
        is_active=True,
        is_verified=True
    )
    db.add(admin_user)
    db.flush()
    print(f"✓ Usuario administrador creado: {admin_user.email}")

    # 4. Crear usuarios de ejemplo
    sample_users = [
        {"email": "coordinador@empresa.com", "name": "María García", "code": "EMP-002", "role": UserRole.COORDINATOR.value, "dept": "COORD_SEG"},
        {"email": "supervisor@empresa.com", "name": "Carlos Rodríguez", "code": "EMP-003", "role": UserRole.SUPERVISOR.value, "dept": "CAE_NORTE"},
        {"email": "tae1@empresa.com", "name": "Juan Pérez", "code": "EMP-004", "role": UserRole.TAE.value, "dept": "CAE_NORTE"},
        {"email": "tae2@empresa.com", "name": "Ana Martínez", "code": "EMP-005", "role": UserRole.TAE.value, "dept": "CAE_SUR"},
        {"email": "tae3@empresa.com", "name": "Pedro López", "code": "EMP-006", "role": UserRole.TAE.value, "dept": "CAE_CENTRAL"},
    ]

    for user_data in sample_users:
        user = User(
            email=user_data["email"],
            hashed_password=get_password_hash("password123"),
            full_name=user_data["name"],
            employee_code=user_data["code"],
            role=user_data["role"],
            organization_id=org.id,
            department_id=departments[user_data["dept"]].id,
            is_active=True,
            is_verified=True
        )
        db.add(user)
    print(f"✓ {len(sample_users)} usuarios de ejemplo creados")

    # 5. Crear categorías de actividades
    categories = {}
    for cat_data in ACTIVITY_CATEGORIES:
        category = ActivityCategory(
            code=cat_data["code"],
            name=cat_data["name"],
            description=cat_data["description"],
            display_order=cat_data["display_order"],
            color=cat_data["color"],
            icon=cat_data["icon"],
            is_active=True
        )
        db.add(category)
        db.flush()
        categories[cat_data["code"]] = category
    print(f"✓ {len(categories)} categorías de actividades creadas")

    # 6. Crear plantillas de actividades
    activity_count = 0
    for act_data in ACTIVITY_TEMPLATES:
        category = categories.get(act_data["category_code"])
        if category:
            activity = ActivityTemplate(
                code=act_data["code"],
                name=act_data["name"],
                category_id=category.id,
                requires_evidence=act_data["requires_evidence"],
                is_critical=act_data["is_critical"],
                default_frequency=act_data["default_frequency"],
                display_order=act_data["display_order"],
                is_active=True
            )
            db.add(activity)
            activity_count += 1
    print(f"✓ {activity_count} plantillas de actividades creadas")

    # 7. Crear tipos de emergencias
    for emg_data in EMERGENCY_TYPES:
        emergency_type = EmergencyType(
            code=emg_data["code"],
            name=emg_data["name"],
            description=emg_data["description"],
            default_severity=emg_data["default_severity"],
            requires_immediate_response=emg_data["requires_immediate_response"],
            target_response_time=emg_data["target_response_time"],
            color=emg_data["color"],
            display_order=emg_data["display_order"],
            is_active=True
        )
        db.add(emergency_type)
    print(f"✓ {len(EMERGENCY_TYPES)} tipos de emergencias creados")

    # 8. Crear categorías de equipos
    for equip_data in EQUIPMENT_CATEGORIES:
        equip_cat = EquipmentCategory(
            code=equip_data["code"],
            name=equip_data["name"],
            default_maintenance_frequency_days=equip_data["default_maintenance_frequency_days"],
            icon=equip_data["icon"],
            color=equip_data["color"],
            is_active=True
        )
        db.add(equip_cat)
    print(f"✓ {len(EQUIPMENT_CATEGORIES)} categorías de equipos creadas")

    # 9. Crear tipos de certificaciones
    for cert_data in CERTIFICATION_TYPES:
        cert_type = CertificationType(
            code=cert_data["code"],
            name=cert_data["name"],
            applies_to=cert_data["applies_to"],
            default_validity_days=cert_data["default_validity_days"],
            is_mandatory=cert_data["is_mandatory"],
            blocks_on_expiry=cert_data["blocks_on_expiry"],
            is_active=True
        )
        db.add(cert_type)
    print(f"✓ {len(CERTIFICATION_TYPES)} tipos de certificaciones creados")

    # Commit final
    db.commit()
    print("\n✅ Base de datos inicializada correctamente!")
    print("\nCredenciales de acceso:")
    print("  Admin: admin@empresa.com / admin123")
    print("  Coordinador: coordinador@empresa.com / password123")
    print("  TAE: tae1@empresa.com / password123")


def create_tables():
    """Crea todas las tablas en la base de datos."""
    Base.metadata.create_all(bind=engine)
    print("✓ Tablas creadas")


def main():
    """Función principal para inicializar la BD."""
    print("=" * 50)
    print("INICIALIZACIÓN DE BASE DE DATOS")
    print("=" * 50)

    # Crear tablas
    create_tables()

    # Inicializar datos
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
