"""
Tests para endpoints de organizaciones (/api/v1/organizations).
"""

import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_header


class TestListOrganizations:
    """Tests para GET /api/v1/organizations/."""

    def test_list_orgs_as_admin(self, client, admin_user, admin_token, organization):
        """Admin puede listar organizaciones."""
        response = client.get(
            "/api/v1/organizations/",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_orgs_as_non_admin(self, client, tae_user, tae_token):
        """No-admin no puede listar organizaciones."""
        response = client.get(
            "/api/v1/organizations/",
            headers=auth_header(tae_token),
        )
        assert response.status_code == 403


class TestGetCurrentOrganization:
    """Tests para GET /api/v1/organizations/current."""

    def test_get_current_org(self, client, admin_user, admin_token, organization):
        """Obtener organizacion del usuario actual."""
        response = client.get(
            "/api/v1/organizations/current",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "MINTEST"
        assert data["name"] == "Minera Test S.A."


class TestGetOrganization:
    """Tests para GET /api/v1/organizations/{org_id}."""

    def test_get_org_by_id(self, client, admin_user, admin_token, organization):
        """Obtener organizacion por ID."""
        response = client.get(
            f"/api/v1/organizations/{organization.id}",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        assert response.json()["code"] == "MINTEST"

    def test_get_org_not_found(self, client, admin_user, admin_token):
        """Organizacion inexistente retorna 404."""
        response = client.get(
            "/api/v1/organizations/99999",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 404


class TestCreateOrganization:
    """Tests para POST /api/v1/organizations/."""

    def test_create_org_as_admin(self, client, admin_user, admin_token):
        """Admin puede crear organizacion."""
        response = client.post(
            "/api/v1/organizations/",
            headers=auth_header(admin_token),
            json={
                "name": "Nueva Minera",
                "code": "NUEVA",
                "description": "Nueva organizacion",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Nueva Minera"
        assert data["code"] == "NUEVA"

    def test_create_org_duplicate_code(self, client, admin_user, admin_token, organization):
        """Codigo duplicado retorna 400."""
        response = client.post(
            "/api/v1/organizations/",
            headers=auth_header(admin_token),
            json={
                "name": "Duplicada",
                "code": "MINTEST",
            },
        )
        assert response.status_code == 400


class TestUpdateOrganization:
    """Tests para PUT /api/v1/organizations/{org_id}."""

    def test_update_org(self, client, admin_user, admin_token, organization):
        """Admin puede actualizar organizacion."""
        response = client.put(
            f"/api/v1/organizations/{organization.id}",
            headers=auth_header(admin_token),
            json={"name": "Minera Actualizada"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Minera Actualizada"

    def test_update_org_not_found(self, client, admin_user, admin_token):
        """Organizacion inexistente retorna 404."""
        response = client.put(
            "/api/v1/organizations/99999",
            headers=auth_header(admin_token),
            json={"name": "No Existe"},
        )
        assert response.status_code == 404


class TestDepartments:
    """Tests para endpoints de departamentos."""

    def test_list_departments(self, client, admin_user, admin_token, department):
        """Listar departamentos."""
        response = client.get(
            "/api/v1/organizations/departments/",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_department(self, client, admin_user, admin_token, department):
        """Obtener departamento por ID."""
        response = client.get(
            f"/api/v1/organizations/departments/{department.id}",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        assert response.json()["code"] == "SEG-IND"

    def test_create_department(self, client, admin_user, admin_token, organization):
        """Crear departamento."""
        response = client.post(
            "/api/v1/organizations/departments/",
            headers=auth_header(admin_token),
            json={
                "name": "Operaciones",
                "code": "OPS",
                "organization_id": organization.id,
            },
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Operaciones"

    def test_update_department(self, client, admin_user, admin_token, department):
        """Actualizar departamento."""
        response = client.put(
            f"/api/v1/organizations/departments/{department.id}",
            headers=auth_header(admin_token),
            json={"name": "Seguridad Actualizada"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Seguridad Actualizada"
