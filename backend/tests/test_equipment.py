"""
Tests para endpoints de equipos (/api/v1/equipment).
"""

import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_header


class TestEquipmentCategories:
    """Tests para GET /api/v1/equipment/categories."""

    def test_list_categories(self, client, admin_user, admin_token, equipment_category):
        """Listar categorias de equipos."""
        response = client.get(
            "/api/v1/equipment/categories",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["code"] == "AMB"


class TestListEquipment:
    """Tests para GET /api/v1/equipment/."""

    def test_list_equipment(self, client, admin_user, admin_token, equipment):
        """Listar equipos."""
        response = client.get(
            "/api/v1/equipment/",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_equipment_filter_category(self, client, admin_user, admin_token, equipment):
        """Filtrar equipos por categoria."""
        response = client.get(
            f"/api/v1/equipment/?category_id={equipment.category_id}",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_list_equipment_search(self, client, admin_user, admin_token, equipment):
        """Buscar equipos."""
        response = client.get(
            "/api/v1/equipment/?search=Ambulancia",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200


class TestGetEquipment:
    """Tests para GET /api/v1/equipment/{equipment_id}."""

    def test_get_equipment(self, client, admin_user, admin_token, equipment):
        """Obtener equipo por ID."""
        response = client.get(
            f"/api/v1/equipment/{equipment.id}",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "AMB-001"
        assert data["status"] == "Operativo"

    def test_get_equipment_not_found(self, client, admin_user, admin_token):
        """Equipo inexistente retorna 404."""
        response = client.get(
            "/api/v1/equipment/99999",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 404


class TestCreateEquipment:
    """Tests para POST /api/v1/equipment/."""

    def test_create_equipment(self, client, admin_user, admin_token, equipment_category):
        """Admin crea equipo."""
        response = client.post(
            "/api/v1/equipment/",
            headers=auth_header(admin_token),
            json={
                "code": "AMB-002",
                "name": "Ambulancia Secundaria",
                "category_id": equipment_category.id,
                "location": "CAE Secundario",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "AMB-002"
        assert data["status"] == "Operativo"

    def test_create_equipment_duplicate_code(self, client, admin_user, admin_token, equipment):
        """Codigo duplicado retorna 400."""
        response = client.post(
            "/api/v1/equipment/",
            headers=auth_header(admin_token),
            json={
                "code": "AMB-001",
                "name": "Duplicada",
                "category_id": equipment.category_id,
            },
        )
        assert response.status_code == 400

    def test_create_equipment_as_employee_forbidden(self, client, employee_user, employee_token, equipment_category):
        """Empleado no puede crear equipos."""
        response = client.post(
            "/api/v1/equipment/",
            headers=auth_header(employee_token),
            json={
                "code": "AMB-003",
                "name": "No Permitido",
                "category_id": equipment_category.id,
            },
        )
        assert response.status_code == 403


class TestUpdateEquipment:
    """Tests para PUT /api/v1/equipment/{equipment_id}."""

    def test_update_equipment(self, client, admin_user, admin_token, equipment):
        """Actualizar equipo."""
        response = client.put(
            f"/api/v1/equipment/{equipment.id}",
            headers=auth_header(admin_token),
            json={"name": "Ambulancia Actualizada", "location": "CAE Norte"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Ambulancia Actualizada"
        assert data["location"] == "CAE Norte"

    def test_update_equipment_not_found(self, client, admin_user, admin_token):
        """Equipo inexistente retorna 404."""
        response = client.put(
            "/api/v1/equipment/99999",
            headers=auth_header(admin_token),
            json={"name": "No Existe"},
        )
        assert response.status_code == 404


class TestEquipmentSummary:
    """Tests para GET /api/v1/equipment/summary."""

    def test_get_summary(self, client, admin_user, admin_token, equipment):
        """Obtener resumen de equipos."""
        response = client.get(
            "/api/v1/equipment/summary",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "operational" in data
        assert data["total"] >= 1


class TestFleetAvailability:
    """Tests para GET /api/v1/equipment/fleet."""

    def test_get_fleet(self, client, admin_user, admin_token, equipment):
        """Obtener disponibilidad de flota."""
        response = client.get(
            "/api/v1/equipment/fleet",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "available_day" in data
        assert "available_night" in data
        assert "by_category" in data
        assert "by_location" in data


class TestEquipmentNovelties:
    """Tests para novedades de equipos."""

    def test_list_novelties(self, client, admin_user, admin_token, equipment):
        """Listar novedades de un equipo."""
        response = client.get(
            f"/api/v1/equipment/{equipment.id}/novelties",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_novelty(self, client, admin_user, admin_token, equipment):
        """Reportar novedad en equipo."""
        response = client.post(
            f"/api/v1/equipment/{equipment.id}/novelties",
            headers=auth_header(admin_token),
            json={
                "novelty_type": "En Mantenimiento",
                "description": "Cambio de aceite programado",
                "shift": "Ambos",
                "unavailable_hours": 4.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["novelty_type"] == "En Mantenimiento"
        assert data["is_resolved"] is False

    def test_resolve_novelty(self, client, admin_user, admin_token, equipment):
        """Resolver novedad de equipo."""
        # Crear novedad
        create_resp = client.post(
            f"/api/v1/equipment/{equipment.id}/novelties",
            headers=auth_header(admin_token),
            json={
                "novelty_type": "Fuera de Servicio",
                "description": "Problema mecanico",
                "shift": "Dia",
                "unavailable_hours": 2.0,
            },
        )
        novelty_id = create_resp.json()["id"]

        # Resolver
        response = client.put(
            f"/api/v1/equipment/{equipment.id}/novelties/{novelty_id}/resolve",
            headers=auth_header(admin_token),
            json={
                "resolution": "Problema mecanico reparado",
                "unavailable_hours": 3.5,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_resolved"] is True
        assert data["resolution"] == "Problema mecanico reparado"

    def test_create_novelty_equipment_not_found(self, client, admin_user, admin_token):
        """Novedad para equipo inexistente retorna 404."""
        response = client.post(
            "/api/v1/equipment/99999/novelties",
            headers=auth_header(admin_token),
            json={
                "novelty_type": "En Mantenimiento",
                "description": "Test",
                "shift": "Ambos",
            },
        )
        assert response.status_code == 404
