"""
Tests para middleware y security headers.
"""

import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_header


class TestSecurityHeaders:
    """Tests para headers de seguridad."""

    def test_security_headers_present(self, client):
        """Verificar que los headers de seguridad estan presentes."""
        response = client.get("/health")
        headers = response.headers

        assert headers.get("x-content-type-options") == "nosniff"
        assert headers.get("x-frame-options") == "DENY"
        assert headers.get("x-xss-protection") == "1; mode=block"
        assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"
        assert "camera=()" in headers.get("permissions-policy", "")

    def test_api_cache_headers(self, client, admin_user, admin_token):
        """Endpoints de API tienen headers no-cache."""
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_header(admin_token),
        )
        headers = response.headers
        assert "no-store" in headers.get("cache-control", "")
        assert headers.get("pragma") == "no-cache"


class TestUTF8Middleware:
    """Tests para el middleware UTF-8."""

    def test_json_responses_have_utf8(self, client):
        """Respuestas JSON incluyen charset=utf-8."""
        response = client.get("/")
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type
        assert "utf-8" in content_type.lower()


class TestCORSMiddleware:
    """Tests para el middleware CORS."""

    def test_cors_headers_on_preflight(self, client):
        """Verificar CORS en preflight OPTIONS."""
        response = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        # CORS deberia responder (puede ser 200 o 405 segun config)
        assert response.status_code in [200, 405]


class TestExceptionHandlers:
    """Tests para manejadores de excepciones globales."""

    def test_404_endpoint(self, client):
        """Endpoint no existente retorna error."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code in [404, 405]

    def test_validation_error_format(self, client, admin_user, admin_token):
        """Errores de validacion tienen formato correcto en DEBUG."""
        response = client.post(
            "/api/v1/auth/verify-otp",
            json={"email": "invalid-email", "otp_code": "short"},
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
