"""
Tests para schemas Pydantic.
Verifica validaciones, valores por defecto y serializacion.
"""

import pytest
from pydantic import ValidationError
from datetime import date, datetime

from app.schemas.user import (
    UserCreateV1, UserResponse, UserUpdate, ProfileUpdate,
    PasswordChange, OTPVerifyRequest, _validate_password_strength,
)
from app.schemas.organization import (
    OrganizationCreate, OrganizationUpdate, DepartmentCreate,
)
from app.schemas.execution import (
    ActivityExecutionCreateV1, ActivityExecutionBase, ExecutionApprovalRequest,
)


class TestPasswordValidation:
    """Tests para validacion de fortaleza de contrasena."""

    def test_valid_password(self):
        """Contrasena fuerte pasa validacion."""
        assert _validate_password_strength("StrongPass1!") == "StrongPass1!"

    def test_too_short(self):
        """Contrasena corta falla."""
        with pytest.raises(ValueError, match="al menos 8"):
            _validate_password_strength("Ab1!")

    def test_too_long(self):
        """Contrasena muy larga falla."""
        with pytest.raises(ValueError, match="exceder 128"):
            _validate_password_strength("A" * 129 + "a1")

    def test_no_uppercase(self):
        """Sin mayuscula falla."""
        with pytest.raises(ValueError, match="mayúscula"):
            _validate_password_strength("lowercase1!")

    def test_no_lowercase(self):
        """Sin minuscula falla."""
        with pytest.raises(ValueError, match="minúscula"):
            _validate_password_strength("UPPERCASE1!")

    def test_no_digit(self):
        """Sin numero falla."""
        with pytest.raises(ValueError, match="número"):
            _validate_password_strength("NoDigitHere!")


class TestUserCreateV1Schema:
    """Tests para el schema UserCreateV1."""

    def test_valid_user_create(self):
        """Crear schema con datos validos."""
        user = UserCreateV1(
            email="test@test.com",
            password="StrongPass1!",
            full_name="Test User",
            role="TAE",
        )
        assert user.email == "test@test.com"
        assert user.role == "TAE"

    def test_invalid_role(self):
        """Rol invalido falla."""
        with pytest.raises(ValidationError):
            UserCreateV1(
                email="test@test.com",
                password="StrongPass1!",
                full_name="Test",
                role="RolInvalido",
            )

    def test_invalid_email(self):
        """Email invalido falla."""
        with pytest.raises(ValidationError):
            UserCreateV1(
                email="not-an-email",
                password="StrongPass1!",
                full_name="Test",
                role="Empleado",
            )

    def test_weak_password(self):
        """Contrasena debil falla."""
        with pytest.raises(ValidationError):
            UserCreateV1(
                email="test@test.com",
                password="weak",
                full_name="Test",
                role="Empleado",
            )


class TestOTPVerifyRequestSchema:
    """Tests para el schema OTPVerifyRequest."""

    def test_valid_otp(self):
        """OTP valido de 8 digitos."""
        req = OTPVerifyRequest(email="test@test.com", otp_code="12345678")
        assert req.otp_code == "12345678"

    def test_otp_too_short(self):
        """OTP corto falla."""
        with pytest.raises(ValidationError):
            OTPVerifyRequest(email="test@test.com", otp_code="1234")

    def test_otp_non_numeric(self):
        """OTP no numerico falla."""
        with pytest.raises(ValidationError):
            OTPVerifyRequest(email="test@test.com", otp_code="abcdefgh")


class TestProfileUpdateSchema:
    """Tests para el schema ProfileUpdate."""

    def test_partial_update(self):
        """Actualizacion parcial."""
        update = ProfileUpdate(full_name="Nuevo Nombre")
        assert update.full_name == "Nuevo Nombre"
        assert update.phone is None

    def test_empty_update(self):
        """Actualizacion vacia es valida (se valida en endpoint)."""
        update = ProfileUpdate()
        data = update.model_dump(exclude_unset=True)
        assert len(data) == 0


class TestPasswordChangeSchema:
    """Tests para el schema PasswordChange."""

    def test_valid_change(self):
        """Cambio valido de contrasena."""
        change = PasswordChange(
            current_password="OldPass123!",
            new_password="NewPass456!",
        )
        assert change.current_password == "OldPass123!"

    def test_weak_new_password(self):
        """Nueva contrasena debil falla."""
        with pytest.raises(ValidationError):
            PasswordChange(
                current_password="OldPass123!",
                new_password="weak",
            )


class TestOrganizationSchemas:
    """Tests para schemas de Organization."""

    def test_create_org(self):
        """Crear schema de organizacion."""
        org = OrganizationCreate(
            name="Test Org",
            code="TEST",
        )
        assert org.name == "Test Org"
        assert org.max_users == 100  # default

    def test_update_org_partial(self):
        """Actualizacion parcial de organizacion."""
        update = OrganizationUpdate(name="Nuevo Nombre")
        data = update.model_dump(exclude_unset=True)
        assert "name" in data
        assert "email" not in data


class TestExecutionSchemas:
    """Tests para schemas de Execution."""

    def test_valid_cycle_number(self):
        """Numero de ciclo valido (1-4)."""
        base = ActivityExecutionBase(
            execution_date=date.today(),
            cycle_number=1,
        )
        assert base.cycle_number == 1

    def test_invalid_cycle_number(self):
        """Numero de ciclo > 4 falla."""
        with pytest.raises(ValidationError):
            ActivityExecutionBase(
                execution_date=date.today(),
                cycle_number=5,
            )

    def test_approval_request(self):
        """Schema de aprobacion."""
        req = ExecutionApprovalRequest(approved=True)
        assert req.approved is True
        assert req.rejection_reason is None

    def test_rejection_request(self):
        """Schema de rechazo con razon."""
        req = ExecutionApprovalRequest(
            approved=False,
            rejection_reason="Falta evidencia",
        )
        assert req.approved is False
        assert req.rejection_reason == "Falta evidencia"
