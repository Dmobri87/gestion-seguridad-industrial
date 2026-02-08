"""
Tests para endpoints de planificacion (/api/v1/planning).
"""

import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_header


class TestListPlans:
    """Tests para GET /api/v1/planning/plans."""

    def test_list_plans(self, client, coordinator_user, coordinator_token, monthly_plan):
        """Listar planes mensuales."""
        response = client.get(
            "/api/v1/planning/plans?year=2026&month=2",
            headers=auth_header(coordinator_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_plans_filter_status(self, client, coordinator_user, coordinator_token, monthly_plan):
        """Filtrar planes por estado."""
        response = client.get(
            "/api/v1/planning/plans?year=2026&month=2&status=Borrador",
            headers=auth_header(coordinator_token),
        )
        assert response.status_code == 200
        data = response.json()
        for plan in data:
            assert plan["status"] == "Borrador"

    def test_list_plans_no_year(self, client, coordinator_user, coordinator_token):
        """Falta parametro year retorna 422."""
        response = client.get(
            "/api/v1/planning/plans",
            headers=auth_header(coordinator_token),
        )
        assert response.status_code == 422


class TestGetPlan:
    """Tests para GET /api/v1/planning/plans/{plan_id}."""

    def test_get_plan_detail(self, client, coordinator_user, coordinator_token, monthly_plan):
        """Obtener detalle de plan."""
        response = client.get(
            f"/api/v1/planning/plans/{monthly_plan.id}",
            headers=auth_header(coordinator_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2026
        assert data["month"] == 2
        assert "cycles" in data
        assert "planned_activities" in data

    def test_get_plan_not_found(self, client, coordinator_user, coordinator_token):
        """Plan inexistente retorna 404."""
        response = client.get(
            "/api/v1/planning/plans/99999",
            headers=auth_header(coordinator_token),
        )
        assert response.status_code == 404


class TestCreatePlan:
    """Tests para POST /api/v1/planning/plans."""

    def test_create_plan_as_coordinator(self, client, coordinator_user, coordinator_token, tae_user, organization):
        """Coordinador puede crear plan."""
        response = client.post(
            "/api/v1/planning/plans",
            headers=auth_header(coordinator_token),
            json={
                "user_id": tae_user.id,
                "year": 2026,
                "month": 3,
                "notes": "Plan de marzo",
                "organization_id": organization.id,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2026
        assert data["month"] == 3
        assert data["status"] == "Borrador"

    def test_create_plan_duplicate(self, client, coordinator_user, coordinator_token, monthly_plan, tae_user, organization):
        """Plan duplicado (mismo usuario/mes) retorna 400."""
        response = client.post(
            "/api/v1/planning/plans",
            headers=auth_header(coordinator_token),
            json={
                "user_id": tae_user.id,
                "year": 2026,
                "month": 2,
                "organization_id": organization.id,
            },
        )
        assert response.status_code == 400

    def test_create_plan_as_tae_forbidden(self, client, tae_user, tae_token, organization):
        """TAE no puede crear planes."""
        response = client.post(
            "/api/v1/planning/plans",
            headers=auth_header(tae_token),
            json={
                "user_id": tae_user.id,
                "year": 2026,
                "month": 4,
                "organization_id": organization.id,
            },
        )
        assert response.status_code == 403


class TestUpdatePlan:
    """Tests para PUT /api/v1/planning/plans/{plan_id}."""

    def test_update_plan(self, client, coordinator_user, coordinator_token, monthly_plan):
        """Actualizar notas del plan."""
        response = client.put(
            f"/api/v1/planning/plans/{monthly_plan.id}",
            headers=auth_header(coordinator_token),
            json={"notes": "Notas actualizadas"},
        )
        assert response.status_code == 200
        assert response.json()["notes"] == "Notas actualizadas"


class TestApprovePlan:
    """Tests para POST /api/v1/planning/plans/{plan_id}/approve."""

    def test_approve_plan(self, client, coordinator_user, coordinator_token, monthly_plan):
        """Aprobar plan en estado Borrador."""
        response = client.post(
            f"/api/v1/planning/plans/{monthly_plan.id}/approve",
            headers=auth_header(coordinator_token),
        )
        assert response.status_code == 200
        assert "aprobado" in response.json()["message"]

    def test_approve_plan_not_found(self, client, coordinator_user, coordinator_token):
        """Plan inexistente retorna 404."""
        response = client.post(
            "/api/v1/planning/plans/99999/approve",
            headers=auth_header(coordinator_token),
        )
        assert response.status_code == 404


class TestPlannedActivities:
    """Tests para gestion de actividades planeadas."""

    def test_add_activity_to_plan(
        self, client, coordinator_user, coordinator_token,
        monthly_plan, activity_template
    ):
        """Agregar actividad al plan."""
        response = client.post(
            f"/api/v1/planning/plans/{monthly_plan.id}/activities",
            headers=auth_header(coordinator_token),
            json={
                "monthly_plan_id": monthly_plan.id,
                "activity_template_id": activity_template.id,
                "cycle_1_planned": 3,
                "cycle_2_planned": 3,
                "cycle_3_planned": 3,
                "cycle_4_planned": 3,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_planned"] == 12

    def test_add_activity_plan_not_found(
        self, client, coordinator_user, coordinator_token, activity_template
    ):
        """Plan inexistente retorna 404."""
        response = client.post(
            "/api/v1/planning/plans/99999/activities",
            headers=auth_header(coordinator_token),
            json={
                "monthly_plan_id": 99999,
                "activity_template_id": activity_template.id,
                "cycle_1_planned": 1,
                "cycle_2_planned": 1,
                "cycle_3_planned": 1,
                "cycle_4_planned": 1,
            },
        )
        assert response.status_code == 404

    def test_update_planned_activity(
        self, client, coordinator_user, coordinator_token, planned_activity
    ):
        """Actualizar actividad planeada."""
        response = client.put(
            f"/api/v1/planning/activities/{planned_activity.id}",
            headers=auth_header(coordinator_token),
            json={"cycle_1_planned": 5},
        )
        assert response.status_code == 200


class TestMyPlan:
    """Tests para GET /api/v1/planning/my-plan."""

    def test_get_my_plan(self, client, tae_user, tae_token, monthly_plan):
        """TAE obtiene su plan del mes."""
        response = client.get(
            "/api/v1/planning/my-plan?year=2026&month=2",
            headers=auth_header(tae_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2026
        assert data["month"] == 2

    def test_get_my_plan_not_found(self, client, tae_user, tae_token):
        """Plan inexistente para el mes retorna 404."""
        response = client.get(
            "/api/v1/planning/my-plan?year=2026&month=12",
            headers=auth_header(tae_token),
        )
        assert response.status_code == 404
