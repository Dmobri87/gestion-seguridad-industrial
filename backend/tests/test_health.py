"""
Tests para los endpoints de health check.
"""

import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test del endpoint /health básico."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_root_endpoint(client: TestClient):
    """Test del endpoint raíz."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "version" in data


def test_health_detailed(client: TestClient):
    """Test del endpoint /health/detailed."""
    response = client.get("/health/detailed")
    assert response.status_code in [200, 503]  # 503 si algún servicio no está disponible
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "database" in data["checks"]
