"""
Tests para endpoints de ejecuciones (/api/v1/executions).
Incluye filtrado por rol, corrección de rechazadas y estadísticas.
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient

from tests.conftest import auth_header


# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────

def _create_execution_via_api(client, token, planned_activity, user, organization):
    """Helper: crea una ejecución vía API y retorna el id."""
    resp = client.post(
        "/api/v1/executions/",
        headers=auth_header(token),
        json={
            "planned_activity_id": planned_activity.id,
            "user_id": user.id,
            "execution_date": "2026-02-05",
            "cycle_number": 1,
            "status": "Completado",
            "observation": "Ejecución de prueba",
            "quantity": 1,
            "organization_id": organization.id,
        },
    )
    assert resp.status_code == 200, f"Fallo creando ejecución: {resp.json()}"
    return resp.json()["id"]


# ──────────────────────────────────────────────────────────────────
# Tests básicos
# ──────────────────────────────────────────────────────────────────

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

    def test_approve_execution(
        self, client, supervisor_user, supervisor_token,
        tae_user, tae_token, planned_activity, organization
    ):
        """Supervisor aprueba ejecucion."""
        exec_id = _create_execution_via_api(
            client, tae_token, planned_activity, tae_user, organization
        )
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
        exec_id = _create_execution_via_api(
            client, tae_token, planned_activity, tae_user, organization
        )
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


# ──────────────────────────────────────────────────────────────────
# Tests de filtrado por rol
# ──────────────────────────────────────────────────────────────────

class TestRoleFilterExecutions:
    """Tests para verificar que el filtrado por rol funciona correctamente."""

    def test_tae_only_sees_own_executions(
        self, client, tae_user, tae_token, planned_activity, organization
    ):
        """TAE solo ve sus propias ejecuciones."""
        _create_execution_via_api(
            client, tae_token, planned_activity, tae_user, organization
        )
        response = client.get(
            "/api/v1/executions/?year=2026&month=2",
            headers=auth_header(tae_token),
        )
        assert response.status_code == 200
        data = response.json()
        for ex in data:
            assert ex["user_id"] == tae_user.id

    def test_admin_sees_all_executions(
        self, client, admin_user, admin_token,
        tae_user, tae_token, planned_activity, organization
    ):
        """Admin ve todas las ejecuciones."""
        _create_execution_via_api(
            client, tae_token, planned_activity, tae_user, organization
        )
        response = client.get(
            "/api/v1/executions/?year=2026&month=2",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        # Admin debe poder ver al menos la ejecución creada
        data = response.json()
        assert isinstance(data, list)

    def test_coordinator_sees_own_taes_executions(
        self, client, db, coordinator_user, coordinator_token,
        tae_user, tae_token, planned_activity, organization, monthly_plan
    ):
        """Coordinador ve ejecuciones de TAEs cuyos planes creó."""
        # El monthly_plan ya tiene created_by=coordinator_user.id (conftest)
        _create_execution_via_api(
            client, tae_token, planned_activity, tae_user, organization
        )
        response = client.get(
            "/api/v1/executions/?year=2026&month=2",
            headers=auth_header(coordinator_token),
        )
        assert response.status_code == 200
        data = response.json()
        # El coordinador debe ver la ejecución del TAE cuyo plan creó
        assert len(data) >= 1
        for ex in data:
            assert ex["user_id"] == tae_user.id

    def test_supervisor_sees_subordinate_executions(
        self, client, db, supervisor_user, supervisor_token,
        tae_user, tae_token, planned_activity, organization
    ):
        """Supervisor ve ejecuciones de sus subordinados."""
        # Vincular TAE como subordinado del supervisor
        tae_user.supervisor_id = supervisor_user.id
        db.commit()

        _create_execution_via_api(
            client, tae_token, planned_activity, tae_user, organization
        )
        response = client.get(
            "/api/v1/executions/?year=2026&month=2",
            headers=auth_header(supervisor_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        for ex in data:
            assert ex["user_id"] == tae_user.id

    def test_supervisor_without_subordinates_sees_nothing(
        self, client, db, supervisor_user, supervisor_token,
        tae_user, tae_token, planned_activity, organization
    ):
        """Supervisor sin subordinados no ve ejecuciones ajenas."""
        # Asegurar que TAE NO es subordinado
        tae_user.supervisor_id = None
        db.commit()

        _create_execution_via_api(
            client, tae_token, planned_activity, tae_user, organization
        )
        response = client.get(
            "/api/v1/executions/?year=2026&month=2",
            headers=auth_header(supervisor_token),
        )
        assert response.status_code == 200
        assert len(response.json()) == 0


class TestRoleFilterStats:
    """Tests para verificar filtrado por rol en /executions/stats."""

    def test_tae_stats_only_own(
        self, client, tae_user, tae_token, planned_activity, organization
    ):
        """TAE solo ve stats de sus propias ejecuciones."""
        _create_execution_via_api(
            client, tae_token, planned_activity, tae_user, organization
        )
        response = client.get(
            "/api/v1/executions/stats?year=2026&month=2",
            headers=auth_header(tae_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_executions"] >= 1
        assert data["completed"] >= 1

    def test_admin_stats_all(
        self, client, admin_user, admin_token,
        tae_user, tae_token, planned_activity, organization
    ):
        """Admin ve stats de todas las ejecuciones."""
        _create_execution_via_api(
            client, tae_token, planned_activity, tae_user, organization
        )
        response = client.get(
            "/api/v1/executions/stats?year=2026&month=2",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_executions"] >= 1


# ──────────────────────────────────────────────────────────────────
# Tests de corrección de ejecuciones rechazadas
# ──────────────────────────────────────────────────────────────────

class TestCorrectExecution:
    """Tests para PUT /api/v1/executions/{id}/correct."""

    def _create_and_reject(self, client, tae_token, supervisor_token,
                           planned_activity, tae_user, organization):
        """Helper: crea una ejecución y la rechaza."""
        exec_id = _create_execution_via_api(
            client, tae_token, planned_activity, tae_user, organization
        )
        client.post(
            f"/api/v1/executions/{exec_id}/approve",
            headers=auth_header(supervisor_token),
            json={"approved": False, "rejection_reason": "Falta evidencia"},
        )
        return exec_id

    def test_correct_rejected_execution(
        self, client, supervisor_user, supervisor_token,
        tae_user, tae_token, planned_activity, organization
    ):
        """TAE corrige y reenvía ejecución rechazada."""
        exec_id = self._create_and_reject(
            client, tae_token, supervisor_token,
            planned_activity, tae_user, organization
        )
        response = client.put(
            f"/api/v1/executions/{exec_id}/correct",
            headers=auth_header(tae_token),
            json={
                "observation": "Corregido: se adjuntó nueva evidencia",
                "status": "Completado",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "Pendiente"
        assert data["rejection_reason"] is None
        assert data["observation"] == "Corregido: se adjuntó nueva evidencia"

    def test_correct_non_rejected_fails(
        self, client, tae_user, tae_token, planned_activity, organization
    ):
        """No se puede corregir una ejecución que no está rechazada."""
        exec_id = _create_execution_via_api(
            client, tae_token, planned_activity, tae_user, organization
        )
        response = client.put(
            f"/api/v1/executions/{exec_id}/correct",
            headers=auth_header(tae_token),
            json={"observation": "Intento inválido"},
        )
        assert response.status_code == 400

    def test_correct_by_other_user_forbidden(
        self, client, db, supervisor_user, supervisor_token,
        tae_user, tae_token, employee_user, employee_token,
        planned_activity, organization
    ):
        """Otro usuario no puede corregir la ejecución de un TAE."""
        exec_id = self._create_and_reject(
            client, tae_token, supervisor_token,
            planned_activity, tae_user, organization
        )
        response = client.put(
            f"/api/v1/executions/{exec_id}/correct",
            headers=auth_header(employee_token),
            json={"observation": "Intento inválido"},
        )
        assert response.status_code == 403

    def test_correct_not_found(self, client, tae_user, tae_token):
        """Ejecución inexistente retorna 404."""
        response = client.put(
            "/api/v1/executions/99999/correct",
            headers=auth_header(tae_token),
            json={"observation": "No existe"},
        )
        assert response.status_code == 404

    def test_correct_updates_quantity(
        self, client, supervisor_user, supervisor_token,
        tae_user, tae_token, planned_activity, organization
    ):
        """Corregir cantidad en ejecución rechazada."""
        exec_id = self._create_and_reject(
            client, tae_token, supervisor_token,
            planned_activity, tae_user, organization
        )
        response = client.put(
            f"/api/v1/executions/{exec_id}/correct",
            headers=auth_header(tae_token),
            json={"quantity": 3, "location": "Sector Norte"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 3
        assert data["location"] == "Sector Norte"
        assert data["approval_status"] == "Pendiente"
