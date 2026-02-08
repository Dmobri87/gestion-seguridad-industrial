"""
Tests para endpoints de certificaciones (/api/v1/certifications).
"""

import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient

from app.models.certification import UserCertification, CertificationStatus
from tests.conftest import auth_header


class TestCertificationTypes:
    """Tests para GET /api/v1/certifications/types."""

    def test_list_types(self, client, admin_user, admin_token, certification_type):
        """Listar tipos de certificacion."""
        response = client.get(
            "/api/v1/certifications/types",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["code"] == "CAB"

    def test_list_types_filter(self, client, admin_user, admin_token, certification_type):
        """Filtrar tipos por applies_to."""
        response = client.get(
            "/api/v1/certifications/types?applies_to=personal",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


class TestUserCertifications:
    """Tests para GET /api/v1/certifications/user/{user_id}."""

    def test_get_user_certifications(self, client, admin_user, admin_token, tae_user, certification_type, db):
        """Listar certificaciones de un usuario."""
        # Crear certificacion
        cert = UserCertification(
            user_id=tae_user.id,
            certification_type_id=certification_type.id,
            issue_date=date.today() - timedelta(days=30),
            expiry_date=date.today() + timedelta(days=335),
            status=CertificationStatus.ACTIVE.value,
            organization_id=admin_user.organization_id,
        )
        db.add(cert)
        db.commit()

        response = client.get(
            f"/api/v1/certifications/user/{tae_user.id}",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1


class TestCreateCertification:
    """Tests para POST /api/v1/certifications/."""

    def test_create_certification(self, client, admin_user, admin_token, tae_user, certification_type):
        """Registrar nueva certificacion."""
        response = client.post(
            "/api/v1/certifications/",
            headers=auth_header(admin_token),
            json={
                "user_id": tae_user.id,
                "certification_type_id": certification_type.id,
                "certificate_number": "CERT-2026-001",
                "issuing_entity": "Instituto de Brigadas",
                "issue_date": "2026-01-15",
                "expiry_date": "2027-01-15",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Vigente"
        assert data["user_id"] == tae_user.id


class TestExpiringCertifications:
    """Tests para GET /api/v1/certifications/expiring."""

    def test_get_expiring(self, client, admin_user, admin_token, tae_user, certification_type, db):
        """Obtener certificaciones proximas a vencer."""
        # Crear certificacion que vence pronto
        cert = UserCertification(
            user_id=tae_user.id,
            certification_type_id=certification_type.id,
            issue_date=date.today() - timedelta(days=350),
            expiry_date=date.today() + timedelta(days=15),
            status=CertificationStatus.ACTIVE.value,
            organization_id=admin_user.organization_id,
        )
        db.add(cert)
        db.commit()

        response = client.get(
            "/api/v1/certifications/expiring?days=30",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        # Verificar que esta ordenado por dias hasta vencimiento
        if len(data) >= 2:
            assert data[0]["days_until_expiry"] <= data[1]["days_until_expiry"]


class TestCertificationsSummary:
    """Tests para GET /api/v1/certifications/summary."""

    def test_get_summary(self, client, admin_user, admin_token):
        """Obtener resumen de certificaciones."""
        response = client.get(
            "/api/v1/certifications/summary",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "active" in data
        assert "expired" in data
        assert "expiring_7_days" in data
        assert "expiring_15_days" in data
        assert "expiring_30_days" in data
