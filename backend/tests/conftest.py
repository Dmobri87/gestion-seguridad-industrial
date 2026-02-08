"""
Configuracion de pytest para tests del backend.
Incluye fixtures para base de datos, autenticacion y datos de prueba.
"""

import os
import pytest
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Configurar variables de entorno ANTES de importar la app
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-minimum-32-characters-long-enough"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["DEBUG"] = "True"
os.environ["REDIS_URL"] = ""

from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.organization import Organization
from app.models.department import Department
from app.models.planning import MonthlyPlan, PlanningCycle, PlannedActivity, PlanStatus
from app.models.execution import ActivityExecution, ExecutionFile, ExecutionStatus, ApprovalStatus
from app.models.emergency import EmergencyType, Emergency, EmergencyStatus
from app.models.equipment import EquipmentCategory, Equipment, EquipmentNovelty, EquipmentStatus
from app.models.certification import CertificationType, UserCertification, CertificationStatus
from app.models.activity_category import ActivityCategory, ActivityTemplate
from app.models.compliance import Accident


# ──────────────────────────────────────────────────────────────────
# Base de datos de test
# ──────────────────────────────────────────────────────────────────
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
    """Crear tablas antes de los tests y limpiar despues."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # Limpiar archivo de test.db
    if os.path.exists("./test.db"):
        os.remove("./test.db")


@pytest.fixture
def db():
    """Fixture para obtener una sesion de base de datos."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """Fixture para obtener un cliente de test."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_db(db):
    """Fixture para limpiar la base de datos entre tests."""
    yield
    # Limpiar todas las tablas despues del test
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()


# ──────────────────────────────────────────────────────────────────
# Fixtures de datos base
# ──────────────────────────────────────────────────────────────────

@pytest.fixture
def organization(db):
    """Crear una organizacion de prueba."""
    org = Organization(
        name="Minera Test S.A.",
        code="MINTEST",
        description="Organizacion de prueba",
        address="Calle Test 123",
        phone="+57 300 000 0000",
        email="info@mineratest.com",
        is_active=True,
        max_users=100,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@pytest.fixture
def department(db, organization):
    """Crear un departamento de prueba."""
    dept = Department(
        name="Seguridad Industrial",
        code="SEG-IND",
        description="Departamento de seguridad",
        organization_id=organization.id,
        is_active=True,
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@pytest.fixture
def admin_user(db, organization):
    """Crear un usuario administrador."""
    user = User(
        email="admin@test.com",
        hashed_password=get_password_hash("Admin123!"),
        full_name="Admin Test",
        employee_code="ADM-001",
        role="Administrador",
        organization_id=organization.id,
        is_active=True,
        is_verified=True,
        two_factor_enabled=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def coordinator_user(db, organization):
    """Crear un usuario coordinador."""
    user = User(
        email="coordinator@test.com",
        hashed_password=get_password_hash("Coord123!"),
        full_name="Coordinador Test",
        employee_code="COO-001",
        role="Coordinador",
        organization_id=organization.id,
        is_active=True,
        is_verified=True,
        two_factor_enabled=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def supervisor_user(db, organization):
    """Crear un usuario supervisor."""
    user = User(
        email="supervisor@test.com",
        hashed_password=get_password_hash("Super123!"),
        full_name="Supervisor Test",
        employee_code="SUP-001",
        role="Supervisor",
        organization_id=organization.id,
        is_active=True,
        is_verified=True,
        two_factor_enabled=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def tae_user(db, organization):
    """Crear un usuario TAE."""
    user = User(
        email="tae@test.com",
        hashed_password=get_password_hash("Tae12345!"),
        full_name="TAE Test",
        employee_code="TAE-001",
        role="TAE",
        organization_id=organization.id,
        is_active=True,
        is_verified=True,
        two_factor_enabled=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def employee_user(db, organization):
    """Crear un usuario empleado."""
    user = User(
        email="employee@test.com",
        hashed_password=get_password_hash("Empl1234!"),
        full_name="Empleado Test",
        employee_code="EMP-001",
        role="Empleado",
        organization_id=organization.id,
        is_active=True,
        is_verified=True,
        two_factor_enabled=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def inactive_user(db, organization):
    """Crear un usuario desactivado."""
    user = User(
        email="inactive@test.com",
        hashed_password=get_password_hash("Inact123!"),
        full_name="Inactivo Test",
        employee_code="INA-001",
        role="Empleado",
        organization_id=organization.id,
        is_active=False,
        is_verified=True,
        two_factor_enabled=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ──────────────────────────────────────────────────────────────────
# Fixtures de autenticacion (tokens)
# ──────────────────────────────────────────────────────────────────

def _make_token(user):
    """Crea un token JWT valido para un usuario."""
    return create_access_token(data={
        "sub": user.email,
        "user_id": user.id,
        "role": user.role,
        "organization_id": user.organization_id,
    })


@pytest.fixture
def admin_token(admin_user):
    """Token JWT para admin."""
    return _make_token(admin_user)


@pytest.fixture
def coordinator_token(coordinator_user):
    """Token JWT para coordinador."""
    return _make_token(coordinator_user)


@pytest.fixture
def supervisor_token(supervisor_user):
    """Token JWT para supervisor."""
    return _make_token(supervisor_user)


@pytest.fixture
def tae_token(tae_user):
    """Token JWT para TAE."""
    return _make_token(tae_user)


@pytest.fixture
def employee_token(employee_user):
    """Token JWT para empleado."""
    return _make_token(employee_user)


def auth_header(token):
    """Crea el header Authorization con el token."""
    return {"Authorization": f"Bearer {token}"}


# ──────────────────────────────────────────────────────────────────
# Fixtures de catalogo
# ──────────────────────────────────────────────────────────────────

@pytest.fixture
def activity_category(db):
    """Crear una categoria de actividad."""
    cat = ActivityCategory(
        name="Seguridad Industrial y Operacional",
        code="SIO",
        description="Actividades de seguridad industrial",
        color="#1890ff",
        icon="SafetyOutlined",
        is_active=True,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@pytest.fixture
def activity_template(db, activity_category):
    """Crear una plantilla de actividad."""
    tmpl = ActivityTemplate(
        name="Inspeccion de Extintores",
        code="SIO-001",
        description="Inspeccion mensual de extintores",
        category_id=activity_category.id,
        requires_evidence=True,
        is_critical=False,
        default_frequency=4,
        is_active=True,
    )
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)
    return tmpl


@pytest.fixture
def emergency_type(db):
    """Crear un tipo de emergencia."""
    etype = EmergencyType(
        name="Conato de Incendio",
        code="INC",
        description="Principio de incendio",
        default_severity="Alta",
        requires_immediate_response=True,
        target_response_time=10,
        icon="FireOutlined",
        color="#ff4d4f",
        display_order=1,
        is_active=True,
    )
    db.add(etype)
    db.commit()
    db.refresh(etype)
    return etype


@pytest.fixture
def equipment_category(db):
    """Crear una categoria de equipo."""
    cat = EquipmentCategory(
        name="Ambulancias",
        code="AMB",
        description="Vehiculos de emergencia",
        default_maintenance_frequency_days=30,
        icon="CarOutlined",
        color="#52c41a",
        display_order=1,
        is_active=True,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@pytest.fixture
def certification_type(db):
    """Crear un tipo de certificacion."""
    ctype = CertificationType(
        name="Curso Avanzado de Brigadas",
        code="CAB",
        applies_to="personal",
        default_validity_days=365,
        is_mandatory=True,
        is_active=True,
    )
    db.add(ctype)
    db.commit()
    db.refresh(ctype)
    return ctype


# ──────────────────────────────────────────────────────────────────
# Fixtures de datos complejos
# ──────────────────────────────────────────────────────────────────

@pytest.fixture
def monthly_plan(db, tae_user, coordinator_user, organization):
    """Crear un plan mensual de prueba."""
    plan = MonthlyPlan(
        user_id=tae_user.id,
        year=2026,
        month=2,
        status=PlanStatus.DRAFT.value,
        created_by=coordinator_user.id,
        organization_id=organization.id,
        total_planned=0,
        total_executed=0,
        compliance_percentage=0.0,
    )
    db.add(plan)
    db.flush()

    # Crear 4 ciclos
    first_day = date(2026, 2, 1)
    for i in range(1, 5):
        start = first_day + timedelta(days=(i - 1) * 7)
        end = start + timedelta(days=6)
        if i == 4:
            end = date(2026, 2, 28)
        cycle = PlanningCycle(
            monthly_plan_id=plan.id,
            cycle_number=i,
            start_date=start,
            end_date=end,
            is_current=(i == 1),
        )
        db.add(cycle)

    db.commit()
    db.refresh(plan)
    return plan


@pytest.fixture
def planned_activity(db, monthly_plan, activity_template):
    """Crear una actividad planeada."""
    pa = PlannedActivity(
        monthly_plan_id=monthly_plan.id,
        activity_template_id=activity_template.id,
        cycle_1_planned=2,
        cycle_2_planned=2,
        cycle_3_planned=2,
        cycle_4_planned=2,
        total_planned=8,
        total_executed=0,
        compliance_percentage=0.0,
        is_active=True,
    )
    db.add(pa)
    db.commit()
    db.refresh(pa)

    # Actualizar plan
    monthly_plan.total_planned = 8
    db.commit()
    db.refresh(monthly_plan)

    return pa


@pytest.fixture
def equipment(db, equipment_category, organization):
    """Crear un equipo de prueba."""
    eq = Equipment(
        code="AMB-001",
        name="Ambulancia Principal",
        category_id=equipment_category.id,
        status=EquipmentStatus.OPERATIONAL.value,
        location="CAE Principal",
        is_available_day=True,
        is_available_night=True,
        organization_id=organization.id,
        is_active=True,
    )
    db.add(eq)
    db.commit()
    db.refresh(eq)
    return eq


@pytest.fixture
def emergency(db, emergency_type, admin_user, organization):
    """Crear una emergencia de prueba."""
    emg = Emergency(
        emergency_code="EMG-2026-0001",
        emergency_type_id=emergency_type.id,
        title="Conato de incendio en bodega",
        description="Se detecta humo en bodega 3",
        location="Bodega 3",
        severity="Alta",
        status=EmergencyStatus.REPORTED.value,
        reported_by=admin_user.id,
        organization_id=organization.id,
    )
    db.add(emg)
    db.commit()
    db.refresh(emg)
    return emg
