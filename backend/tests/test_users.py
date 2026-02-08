"""
Tests para endpoints de usuarios (/api/v1/users).
"""

import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_header


class TestListUsers:
    """Tests para GET /api/v1/users/."""

    def test_list_users_authenticated(self, client, admin_user, admin_token):
        """Usuario autenticado puede listar usuarios."""
        response = client.get(
            "/api/v1/users/",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_users_no_auth(self, client):
        """Sin autenticacion retorna 401."""
        response = client.get("/api/v1/users/")
        assert response.status_code == 401

    def test_list_users_filter_by_role(self, client, admin_user, tae_user, admin_token):
        """Filtrar usuarios por rol."""
        response = client.get(
            "/api/v1/users/?role=TAE",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        for user in data:
            assert user["role"] == "TAE"

    def test_list_users_search(self, client, admin_user, admin_token):
        """Buscar usuarios por nombre/email."""
        response = client.get(
            "/api/v1/users/?search=Admin",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_list_users_pagination(self, client, admin_user, admin_token):
        """Paginacion de usuarios."""
        response = client.get(
            "/api/v1/users/?skip=0&limit=1",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 1


class TestGetTAEs:
    """Tests para GET /api/v1/users/taes."""

    def test_get_taes(self, client, admin_user, tae_user, admin_token):
        """Listar TAEs activos."""
        response = client.get(
            "/api/v1/users/taes",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        for user in data:
            assert user["role"] == "TAE"


class TestGetAssignableUsers:
    """Tests para GET /api/v1/users/assignable."""

    def test_get_assignable(self, client, tae_user, coordinator_user, admin_token, admin_user):
        """Listar usuarios asignables a planes."""
        response = client.get(
            "/api/v1/users/assignable",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assignable_roles = {"TAE", "PSE", "Supervisor", "Coordinador"}
        for user in data:
            assert user["role"] in assignable_roles


class TestGetUser:
    """Tests para GET /api/v1/users/{user_id}."""

    def test_get_user_by_id(self, client, admin_user, admin_token):
        """Obtener usuario por ID."""
        response = client.get(
            f"/api/v1/users/{admin_user.id}",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@test.com"

    def test_get_user_not_found(self, client, admin_user, admin_token):
        """Usuario inexistente retorna 404."""
        response = client.get(
            "/api/v1/users/99999",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 404


class TestCreateUser:
    """Tests para POST /api/v1/users/."""

    def test_create_user_as_admin(self, client, admin_user, admin_token):
        """Admin puede crear usuario."""
        response = client.post(
            "/api/v1/users/",
            headers=auth_header(admin_token),
            json={
                "email": "newuser@test.com",
                "password": "NewUser123!",
                "full_name": "New User",
                "role": "Empleado",
            },
        )
        assert response.status_code == 200
        assert response.json()["email"] == "newuser@test.com"

    def test_create_user_as_coordinator(self, client, coordinator_user, coordinator_token):
        """Coordinador puede crear usuario."""
        response = client.post(
            "/api/v1/users/",
            headers=auth_header(coordinator_token),
            json={
                "email": "newcoord@test.com",
                "password": "NewCoord123!",
                "full_name": "New Coord User",
                "role": "TAE",
            },
        )
        assert response.status_code == 200

    def test_create_user_as_employee_forbidden(self, client, employee_user, employee_token):
        """Empleado no puede crear usuarios."""
        response = client.post(
            "/api/v1/users/",
            headers=auth_header(employee_token),
            json={
                "email": "forbidden@test.com",
                "password": "Forbidden1!",
                "full_name": "Forbidden",
                "role": "Empleado",
            },
        )
        assert response.status_code == 403

    def test_create_user_duplicate_email(self, client, admin_user, admin_token):
        """Email duplicado retorna 400."""
        response = client.post(
            "/api/v1/users/",
            headers=auth_header(admin_token),
            json={
                "email": "admin@test.com",
                "password": "Duplicate1!",
                "full_name": "Duplicate",
                "role": "Empleado",
            },
        )
        assert response.status_code == 400


class TestUpdateUser:
    """Tests para PUT /api/v1/users/{user_id}."""

    def test_update_user_as_admin(self, client, admin_user, tae_user, admin_token):
        """Admin puede actualizar usuario."""
        response = client.put(
            f"/api/v1/users/{tae_user.id}",
            headers=auth_header(admin_token),
            json={"full_name": "TAE Actualizado"},
        )
        assert response.status_code == 200
        assert response.json()["full_name"] == "TAE Actualizado"

    def test_update_user_not_found(self, client, admin_user, admin_token):
        """Actualizar usuario inexistente retorna 404."""
        response = client.put(
            "/api/v1/users/99999",
            headers=auth_header(admin_token),
            json={"full_name": "No Existe"},
        )
        assert response.status_code == 404


class TestDeleteUser:
    """Tests para DELETE /api/v1/users/{user_id}."""

    def test_delete_user_soft(self, client, admin_user, tae_user, admin_token):
        """Admin puede desactivar usuario (soft delete)."""
        response = client.delete(
            f"/api/v1/users/{tae_user.id}",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        assert "desactivado" in response.json()["message"]

    def test_delete_self_forbidden(self, client, admin_user, admin_token):
        """No se puede eliminar a si mismo."""
        response = client.delete(
            f"/api/v1/users/{admin_user.id}",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 400

    def test_delete_user_not_found(self, client, admin_user, admin_token):
        """Eliminar usuario inexistente retorna 404."""
        response = client.delete(
            "/api/v1/users/99999",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 404

    def test_delete_user_as_non_admin(self, client, coordinator_user, tae_user, coordinator_token):
        """Solo admin puede eliminar usuarios."""
        response = client.delete(
            f"/api/v1/users/{tae_user.id}",
            headers=auth_header(coordinator_token),
        )
        assert response.status_code == 403
