"""
Tests para endpoints de ejecuciones (/api/v1/executions).
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient

from tests.conftest import auth_header


class TestListExecutions:
    """Tests para GET /api/v1/executions/."""

    def test_list_executions(self, client, tae_user, tae_token):
        """Listar ejecuciones del mes."""
        response = client.get(
            "/api/v1/executions/?year=2026&month=2",
            headers=auth_header(tae_token),
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_executions_missing_params(self, client, tae_user, tae_token):
        """Falta year/month retorna 422."""
        response = client.get(
            "/api/v1/executions/",
            headers=auth_header(tae_token),
        )
        assert response.status_code == 422


class TestCreateExecution:
    """Tests para POST /api/v1/executions/."""

    def test_create_execution(
        self, client, tae_user, tae_token, planned_activity, organization
    ):
        """Registrar ejecucion de actividad."""
        response = client.post(
            "/api/v1/executions/",
            headers=auth_header(tae_token),
            json={
                "planned_activity_id": planned_activity.id,
                "user_id": tae_user.id,
                "execution_date": "2026-02-05",
                "cycle_number": 1,
                "status": "Completado",
                "observation": "Actividad completada correctamente",
                "quantity": 1,
                "organization_id": organization.id,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Completado"
        assert data["approval_status"] == "Pendiente"
        assert data["quantity"] == 1

    def test_create_execution_invalid_cycle(
        self, client, tae_user, tae_token, planned_activity, organization
    ):
        """Ciclo invalido retorna 422."""
        response = client.post(
            "/api/v1/executions/",
            headers=auth_header(tae_token),
            json={
                "planned_activity_id": planned_activity.id,
                "user_id": tae_user.id,
                "execution_date": "2026-02-05",
                "cycle_number": 5,
                "status": "Completado",
                "quantity": 1,
                "organization_id": organization.id,
            },
        )
        assert response.status_code == 422

    def test_create_execution_not_found_activity(
        self, client, tae_user, tae_token, organization
    ):
        """Actividad planeada inexistente retorna 404."""
        response = client.post(
            "/api/v1/executions/",
            headers=auth_header(tae_token),
            json={
                "planned_activity_id": 99999,
                "user_id": tae_user.id,
                "execution_date": "2026-02-05",
                "cycle_number": 1,
                "status": "Completado",
                "quantity": 1,
                "organization_id": organization.id,
            },
        )
        assert response.status_code == 404


class TestApproveExecution:
    """Tests para POST /api/v1/executions/{execution_id}/approve."""

    def _create_execution(self, client, tae_token, planned_activity, tae_user, organization):
        """Helper: crea una ejecucion."""
        resp = client.post(
            "/api/v1/executions/",
            headers=auth_header(tae_token),
            json={
                "planned_activity_id": planned_activity.id,
                "user_id": tae_user.id,
                "execution_date": "2026-02-05",
                "cycle_number": 1,
                "status": "Completado",
                "quantity": 1,
                "organization_id": organization.id,
            },
        )
        return resp.json()["id"]

    def test_approve_execution(
        self, client, supervisor_user, supervisor_token,
        tae_user, tae_token, planned_activity, organization
    ):
        """Supervisor aprueba ejecucion."""
        exec_id = self._create_execution(client, tae_token, planned_activity, tae_user, organization)
        response = client.post(
            f"/api/v1/executions/{exec_id}/approve",
            headers=auth_header(supervisor_token),
            json={"approved": True},
        )
        assert response.status_code == 200
        assert response.json()["approval_status"] == "Aprobado"

    def test_reject_execution(
        self, client, supervisor_user, supervisor_token,
        tae_user, tae_token, planned_activity, organization
    ):
        """Supervisor rechaza ejecucion."""
        exec_id = self._create_execution(client, tae_token, planned_activity, tae_user, organization)
        response = client.post(
            f"/api/v1/executions/{exec_id}/approve",
            headers=auth_header(supervisor_token),
            json={
                "approved": False,
                "rejection_reason": "Evidencia insuficiente",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "Rechazado"
        assert data["rejection_reason"] == "Evidencia insuficiente"

    def test_approve_not_found(self, client, supervisor_user, supervisor_token):
        """Ejecucion inexistente retorna 404."""
        response = client.post(
            "/api/v1/executions/99999/approve",
            headers=auth_header(supervisor_token),
            json={"approved": True},
        )
        assert response.status_code == 404


class TestExecutionStats:
    """Tests para GET /api/v1/executions/stats."""

    def test_get_stats(self, client, tae_user, tae_token):
        """Obtener estadisticas de ejecuciones."""
        response = client.get(
            "/api/v1/executions/stats?year=2026&month=2",
            headers=auth_header(tae_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_executions" in data
        assert "completed" in data
        assert "pending" in data
        assert "pending_approval" in data


class TestMyToday:
    """Tests para GET /api/v1/executions/my-today."""

    def test_get_my_today(self, client, tae_user, tae_token):
        """Obtener actividades de hoy."""
        response = client.get(
            "/api/v1/executions/my-today",
            headers=auth_header(tae_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "activities" in data
