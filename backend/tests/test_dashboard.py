"""
Tests para endpoints de dashboard (/api/v1/dashboard).
"""

import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_header


class TestDashboard:
    """Tests para GET /api/v1/dashboard/."""

    def test_get_dashboard(self, client, admin_user, admin_token):
        """Obtener datos del dashboard."""
        response = client.get(
            "/api/v1/dashboard/?year=2026&month=2",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "period" in data
        assert "main_kpis" in data
        assert "compliance" in data
        assert "emergencies" in data
        assert "alerts" in data
        assert "equipment" in data
        assert "certifications" in data

    def test_get_dashboard_kpis(self, client, admin_user, admin_token):
        """Verificar estructura de KPIs."""
        response = client.get(
            "/api/v1/dashboard/?year=2026&month=2",
            headers=auth_header(admin_token),
        )
        data = response.json()
        kpis = data["main_kpis"]
        assert "accidents" in kpis
        assert "emergencies" in kpis
        assert "compliance" in kpis
        assert "pending_activities" in kpis
        # Verificar estructura de KPI card
        assert "title" in kpis["accidents"]
        assert "value" in kpis["accidents"]
        assert "color" in kpis["accidents"]

    def test_get_dashboard_missing_params(self, client, admin_user, admin_token):
        """Falta year/month retorna 422."""
        response = client.get(
            "/api/v1/dashboard/",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 422

    def test_get_dashboard_no_auth(self, client):
        """Sin autenticacion retorna 401."""
        response = client.get("/api/v1/dashboard/?year=2026&month=2")
        assert response.status_code == 401


class TestComplianceChart:
    """Tests para GET /api/v1/dashboard/compliance-chart."""

    def test_get_compliance_chart(self, client, admin_user, admin_token):
        """Obtener datos de grafico de cumplimiento anual."""
        response = client.get(
            "/api/v1/dashboard/compliance-chart?year=2026",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 12  # 12 meses
        for month_data in data:
            assert "month" in month_data
            assert "month_name" in month_data
            assert "planned" in month_data
            assert "executed" in month_data
            assert "compliance" in month_data
