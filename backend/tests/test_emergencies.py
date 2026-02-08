"""
Tests para endpoints de emergencias (/api/v1/emergencies).
"""

import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_header


class TestEmergencyTypes:
    """Tests para GET /api/v1/emergencies/types."""

    def test_list_emergency_types(self, client, admin_user, admin_token, emergency_type):
        """Listar tipos de emergencia."""
        response = client.get(
            "/api/v1/emergencies/types",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["code"] == "INC"


class TestListEmergencies:
    """Tests para GET /api/v1/emergencies/."""

    def test_list_emergencies(self, client, admin_user, admin_token, emergency):
        """Listar emergencias del anio."""
        response = client.get(
            "/api/v1/emergencies/?year=2026",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_emergencies_missing_year(self, client, admin_user, admin_token):
        """Falta year retorna 422."""
        response = client.get(
            "/api/v1/emergencies/",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 422


class TestCreateEmergency:
    """Tests para POST /api/v1/emergencies/."""

    def test_create_emergency(self, client, admin_user, admin_token, emergency_type):
        """Crear emergencia."""
        response = client.post(
            "/api/v1/emergencies/",
            headers=auth_header(admin_token),
            json={
                "emergency_type_id": emergency_type.id,
                "title": "Derrame de sustancia quimica",
                "description": "Derrame en area de almacenamiento",
                "location": "Almacen Quimico",
                "severity": "Alta",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Derrame de sustancia quimica"
        assert data["status"] == "Reportada"
        assert data["emergency_code"].startswith("EMG-")


class TestEmergencyArrival:
    """Tests para POST /api/v1/emergencies/{id}/arrival."""

    def test_register_arrival(self, client, admin_user, admin_token, emergency):
        """Registrar llegada a emergencia."""
        response = client.post(
            f"/api/v1/emergencies/{emergency.id}/arrival",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "response_time_minutes" in data
        assert data["message"] == "Llegada registrada"

    def test_arrival_not_found(self, client, admin_user, admin_token):
        """Emergencia inexistente retorna 404."""
        response = client.post(
            "/api/v1/emergencies/99999/arrival",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 404


class TestCloseEmergency:
    """Tests para POST /api/v1/emergencies/{id}/close."""

    def test_close_emergency(self, client, admin_user, admin_token, emergency):
        """Cerrar emergencia."""
        response = client.post(
            f"/api/v1/emergencies/{emergency.id}/close",
            headers=auth_header(admin_token),
            params={
                "actions_taken": "Se extinguio el fuego",
                "result": "Sin danos mayores",
            },
        )
        assert response.status_code == 200
        assert "cerrada" in response.json()["message"]

    def test_close_not_found(self, client, admin_user, admin_token):
        """Emergencia inexistente retorna 404."""
        response = client.post(
            "/api/v1/emergencies/99999/close",
            headers=auth_header(admin_token),
            params={
                "actions_taken": "N/A",
                "result": "N/A",
            },
        )
        assert response.status_code == 404


class TestEmergencySummary:
    """Tests para GET /api/v1/emergencies/summary."""

    def test_get_summary(self, client, admin_user, admin_token):
        """Obtener resumen de emergencias."""
        response = client.get(
            "/api/v1/emergencies/summary?year=2026",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "closed" in data
        assert "open" in data
