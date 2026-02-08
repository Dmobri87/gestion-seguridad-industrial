"""
Tests para endpoints de autenticacion (/api/v1/auth).
"""

import pytest
import hashlib
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from unittest.mock import patch

from tests.conftest import auth_header


class TestLogin:
    """Tests para POST /api/v1/auth/login (paso 1 - 2FA)."""

    def test_login_valid_credentials(self, client, admin_user):
        """Login exitoso genera OTP y retorna requires_2fa."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin@test.com", "password": "Admin123!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["requires_2fa"] is True
        assert "message" in data
        # En modo dev (SMTP no configurado), el OTP se incluye en respuesta
        assert "dev_otp" in data
        assert len(data["dev_otp"]) == 8

    def test_login_wrong_email(self, client, admin_user):
        """Login con email inexistente retorna 401."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "noexiste@test.com", "password": "Admin123!"},
        )
        assert response.status_code == 401
        assert "incorrectos" in response.json()["detail"]

    def test_login_wrong_password(self, client, admin_user):
        """Login con contrasena incorrecta retorna 401."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin@test.com", "password": "WrongPass1!"},
        )
        assert response.status_code == 401

    def test_login_inactive_user(self, client, inactive_user):
        """Login de usuario desactivado retorna 403."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "inactive@test.com", "password": "Inact123!"},
        )
        assert response.status_code == 403
        assert "desactivado" in response.json()["detail"]


class TestVerifyOTP:
    """Tests para POST /api/v1/auth/verify-otp (paso 2 - 2FA)."""

    def _do_login(self, client, email="admin@test.com", password="Admin123!"):
        """Helper: realiza login y retorna el OTP."""
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
        )
        return resp.json().get("dev_otp")

    def test_verify_otp_success(self, client, admin_user):
        """OTP valido retorna token JWT."""
        otp = self._do_login(client)
        response = client.post(
            "/api/v1/auth/verify-otp",
            json={"email": "admin@test.com", "otp_code": otp},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "user" in data
        assert data["user"]["email"] == "admin@test.com"

    def test_verify_otp_wrong_code(self, client, admin_user):
        """OTP incorrecto retorna 401."""
        self._do_login(client)
        response = client.post(
            "/api/v1/auth/verify-otp",
            json={"email": "admin@test.com", "otp_code": "00000000"},
        )
        assert response.status_code == 401

    def test_verify_otp_nonexistent_user(self, client):
        """OTP para usuario inexistente retorna 401."""
        response = client.post(
            "/api/v1/auth/verify-otp",
            json={"email": "noexiste@test.com", "otp_code": "12345678"},
        )
        assert response.status_code == 401

    def test_verify_otp_invalid_format(self, client, admin_user):
        """OTP con formato invalido retorna 422."""
        response = client.post(
            "/api/v1/auth/verify-otp",
            json={"email": "admin@test.com", "otp_code": "abc"},
        )
        assert response.status_code == 422


class TestLogout:
    """Tests para POST /api/v1/auth/logout."""

    def test_logout_success(self, client, admin_user, admin_token):
        """Logout exitoso revoca el token."""
        response = client.post(
            "/api/v1/auth/logout",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        assert "cerrada" in response.json()["message"]

    def test_logout_no_token(self, client):
        """Logout sin token retorna 401."""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 401


class TestGetMe:
    """Tests para GET /api/v1/auth/me."""

    def test_get_me_success(self, client, admin_user, admin_token):
        """Obtener informacion del usuario actual."""
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@test.com"
        assert data["full_name"] == "Admin Test"
        assert data["role"] == "Administrador"

    def test_get_me_no_auth(self, client):
        """Sin autenticacion retorna 401."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401


class TestUpdateProfile:
    """Tests para PUT /api/v1/auth/me."""

    def test_update_profile_success(self, client, admin_user, admin_token):
        """Actualizar nombre del perfil."""
        response = client.put(
            "/api/v1/auth/me",
            headers=auth_header(admin_token),
            json={"full_name": "Admin Actualizado"},
        )
        assert response.status_code == 200
        assert response.json()["full_name"] == "Admin Actualizado"

    def test_update_profile_no_data(self, client, admin_user, admin_token):
        """Actualizar sin datos retorna 400."""
        response = client.put(
            "/api/v1/auth/me",
            headers=auth_header(admin_token),
            json={},
        )
        assert response.status_code == 400


class TestChangePassword:
    """Tests para POST /api/v1/auth/change-password."""

    def test_change_password_success(self, client, admin_user, admin_token):
        """Cambio de contrasena exitoso."""
        response = client.post(
            "/api/v1/auth/change-password",
            headers=auth_header(admin_token),
            json={
                "current_password": "Admin123!",
                "new_password": "NewAdmin123!",
            },
        )
        assert response.status_code == 200
        assert "actualizada" in response.json()["message"]

    def test_change_password_wrong_current(self, client, admin_user, admin_token):
        """Cambio con contrasena actual incorrecta retorna 400."""
        response = client.post(
            "/api/v1/auth/change-password",
            headers=auth_header(admin_token),
            json={
                "current_password": "WrongPass1!",
                "new_password": "NewAdmin123!",
            },
        )
        assert response.status_code == 400

    def test_change_password_weak_new(self, client, admin_user, admin_token):
        """Cambio con contrasena nueva debil retorna 422."""
        response = client.post(
            "/api/v1/auth/change-password",
            headers=auth_header(admin_token),
            json={
                "current_password": "Admin123!",
                "new_password": "weak",
            },
        )
        assert response.status_code == 422


class TestRegister:
    """Tests para POST /api/v1/auth/register."""

    def test_register_as_admin(self, client, admin_user, admin_token):
        """Admin puede registrar nuevo usuario."""
        response = client.post(
            "/api/v1/auth/register",
            headers=auth_header(admin_token),
            json={
                "email": "nuevo@test.com",
                "password": "NuevoUser123!",
                "full_name": "Nuevo Usuario",
                "role": "Empleado",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "nuevo@test.com"
        assert data["full_name"] == "Nuevo Usuario"

    def test_register_duplicate_email(self, client, admin_user, admin_token):
        """Registrar email duplicado retorna 400."""
        response = client.post(
            "/api/v1/auth/register",
            headers=auth_header(admin_token),
            json={
                "email": "admin@test.com",
                "password": "NuevoUser123!",
                "full_name": "Duplicado",
                "role": "Empleado",
            },
        )
        assert response.status_code == 400
        assert "registrado" in response.json()["detail"]

    def test_register_as_non_admin(self, client, tae_user, tae_token):
        """No-admin no puede registrar usuarios."""
        response = client.post(
            "/api/v1/auth/register",
            headers=auth_header(tae_token),
            json={
                "email": "nuevo@test.com",
                "password": "NuevoUser123!",
                "full_name": "Nuevo",
                "role": "Empleado",
            },
        )
        assert response.status_code == 403


class TestRefreshToken:
    """Tests para POST /api/v1/auth/refresh-token."""

    def test_refresh_token_success(self, client, admin_user, admin_token):
        """Refrescar token exitosamente."""
        response = client.post(
            "/api/v1/auth/refresh-token",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
