"""
Tests para modelos SQLAlchemy.
Verifica creacion de instancias, relaciones y constraints.
"""

import pytest
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError

from app.models.user import User, UserRole
from app.models.organization import Organization
from app.models.department import Department
from app.models.planning import MonthlyPlan, PlanningCycle, PlannedActivity, PlanStatus
from app.models.execution import ActivityExecution, ExecutionStatus, ApprovalStatus
from app.models.emergency import Emergency, EmergencyType, EmergencyStatus, EmergencySeverity
from app.models.equipment import Equipment, EquipmentCategory, EquipmentStatus, EquipmentNovelty
from app.models.certification import CertificationType, UserCertification, CertificationStatus


class TestUserModel:
    """Tests para el modelo User."""

    def test_create_user(self, db, organization):
        """Crear usuario con todos los campos."""
        user = User(
            email="model@test.com",
            hashed_password="$2b$13$hashedpassword",
            full_name="Model Test",
            employee_code="MOD-001",
            role=UserRole.TAE.value,
            organization_id=organization.id,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        assert user.id is not None
        assert user.email == "model@test.com"
        assert user.role == "TAE"
        assert user.is_active is True
        assert user.created_at is not None

    def test_user_unique_email(self, db, organization):
        """Email duplicado lanza IntegrityError."""
        user1 = User(
            email="unique@test.com",
            hashed_password="hash1",
            full_name="User 1",
            organization_id=organization.id,
        )
        db.add(user1)
        db.commit()

        user2 = User(
            email="unique@test.com",
            hashed_password="hash2",
            full_name="User 2",
            organization_id=organization.id,
        )
        db.add(user2)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_user_default_role(self, db, organization):
        """Rol por defecto es Empleado."""
        user = User(
            email="default@test.com",
            hashed_password="hash",
            full_name="Default",
            organization_id=organization.id,
        )
        db.add(user)
        db.commit()
        assert user.role == "Empleado"

    def test_user_role_enum(self):
        """Verificar valores del enum UserRole."""
        assert UserRole.ADMIN.value == "Administrador"
        assert UserRole.COORDINATOR.value == "Coordinador"
        assert UserRole.TAE.value == "TAE"


class TestOrganizationModel:
    """Tests para el modelo Organization."""

    def test_create_organization(self, db):
        """Crear organizacion."""
        org = Organization(
            name="Test Org",
            code="TORG",
            is_active=True,
        )
        db.add(org)
        db.commit()
        db.refresh(org)

        assert org.id is not None
        assert org.code == "TORG"
        assert org.max_users == 100  # default

    def test_organization_unique_code(self, db):
        """Codigo de organizacion debe ser unico."""
        org1 = Organization(name="Org 1", code="DUP")
        db.add(org1)
        db.commit()

        org2 = Organization(name="Org 2", code="DUP")
        db.add(org2)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


class TestMonthlyPlanModel:
    """Tests para el modelo MonthlyPlan."""

    def test_create_plan(self, db, tae_user, coordinator_user, organization):
        """Crear plan mensual."""
        plan = MonthlyPlan(
            user_id=tae_user.id,
            year=2026,
            month=6,
            status=PlanStatus.DRAFT.value,
            created_by=coordinator_user.id,
            organization_id=organization.id,
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        assert plan.id is not None
        assert plan.status == "Borrador"
        assert plan.total_planned == 0
        assert plan.compliance_percentage == 0.0

    def test_plan_unique_constraint(self, db, tae_user, coordinator_user, organization):
        """Un usuario solo puede tener un plan por mes."""
        plan1 = MonthlyPlan(
            user_id=tae_user.id,
            year=2026,
            month=7,
            created_by=coordinator_user.id,
            organization_id=organization.id,
        )
        db.add(plan1)
        db.commit()

        plan2 = MonthlyPlan(
            user_id=tae_user.id,
            year=2026,
            month=7,
            created_by=coordinator_user.id,
            organization_id=organization.id,
        )
        db.add(plan2)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_plan_status_enum(self):
        """Verificar valores de PlanStatus."""
        assert PlanStatus.DRAFT.value == "Borrador"
        assert PlanStatus.APPROVED.value == "Aprobado"
        assert PlanStatus.IN_PROGRESS.value == "En Progreso"
        assert PlanStatus.COMPLETED.value == "Completado"


class TestExecutionModel:
    """Tests para el modelo ActivityExecution."""

    def test_execution_status_enum(self):
        """Verificar valores de ExecutionStatus."""
        assert ExecutionStatus.COMPLETED.value == "Completado"
        assert ExecutionStatus.PENDING.value == "Pendiente"
        assert ExecutionStatus.WITH_NOVELTY.value == "Con Novedad"

    def test_approval_status_enum(self):
        """Verificar valores de ApprovalStatus."""
        assert ApprovalStatus.PENDING.value == "Pendiente"
        assert ApprovalStatus.APPROVED.value == "Aprobado"
        assert ApprovalStatus.REJECTED.value == "Rechazado"


class TestEmergencyModel:
    """Tests para modelos de Emergency."""

    def test_emergency_status_enum(self):
        """Verificar valores de EmergencyStatus."""
        assert EmergencyStatus.REPORTED.value == "Reportada"
        assert EmergencyStatus.IN_PROGRESS.value == "En Atención"
        assert EmergencyStatus.CLOSED.value == "Cerrada"

    def test_emergency_severity_enum(self):
        """Verificar valores de EmergencySeverity."""
        assert EmergencySeverity.LOW.value == "Baja"
        assert EmergencySeverity.CRITICAL.value == "Crítica"


class TestEquipmentModel:
    """Tests para modelos de Equipment."""

    def test_equipment_status_enum(self):
        """Verificar valores de EquipmentStatus."""
        assert EquipmentStatus.OPERATIONAL.value == "Operativo"
        assert EquipmentStatus.IN_MAINTENANCE.value == "En Mantenimiento"
        assert EquipmentStatus.OUT_OF_SERVICE.value == "Fuera de Servicio"

    def test_create_equipment(self, db, equipment_category, organization):
        """Crear equipo."""
        eq = Equipment(
            code="SCBA-001",
            name="SCBA Test",
            category_id=equipment_category.id,
            status=EquipmentStatus.OPERATIONAL.value,
            organization_id=organization.id,
        )
        db.add(eq)
        db.commit()
        db.refresh(eq)

        assert eq.id is not None
        assert eq.is_available_day is True
        assert eq.is_available_night is True

    def test_equipment_unique_code(self, db, equipment_category, organization):
        """Codigo de equipo debe ser unico."""
        eq1 = Equipment(
            code="DUP-001",
            name="Eq 1",
            category_id=equipment_category.id,
            organization_id=organization.id,
        )
        db.add(eq1)
        db.commit()

        eq2 = Equipment(
            code="DUP-001",
            name="Eq 2",
            category_id=equipment_category.id,
            organization_id=organization.id,
        )
        db.add(eq2)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


class TestCertificationModel:
    """Tests para modelos de Certification."""

    def test_certification_status_enum(self):
        """Verificar valores de CertificationStatus."""
        assert CertificationStatus.ACTIVE.value == "Vigente"
        assert CertificationStatus.EXPIRED.value == "Vencido"
        assert CertificationStatus.EXPIRING_SOON.value == "Por Vencer"
