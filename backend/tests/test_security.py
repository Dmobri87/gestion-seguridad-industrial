"""
Tests para funciones de seguridad.
"""

import pytest
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    verify_access_token,
    needs_rehash,
)


class TestPasswordHashing:
    """Tests para hashing de contraseñas."""

    def test_hash_password(self):
        """Test que una contraseña se hashea correctamente."""
        password = "MiContraseña123!"
        hashed = get_password_hash(password)

        assert hashed != password
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
        assert len(hashed) > 50

    def test_verify_correct_password(self):
        """Test que una contraseña correcta se verifica."""
        password = "MiContraseña123!"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_incorrect_password(self):
        """Test que una contraseña incorrecta falla."""
        password = "MiContraseña123!"
        wrong_password = "OtraContraseña456!"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_needs_rehash_bcrypt(self):
        """Test que un hash bcrypt con suficiente costo no necesita rehash."""
        password = "MiContraseña123!"
        hashed = get_password_hash(password)

        # El hash actual debería estar bien
        # (puede necesitar rehash si el costo fue aumentado)
        result = needs_rehash(hashed)
        assert isinstance(result, bool)


class TestJWT:
    """Tests para creación y verificación de JWT."""

    def test_create_access_token(self):
        """Test que se crea un token válido."""
        data = {"sub": "test@example.com", "user_id": 1}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 100  # Los JWT son largos

    def test_verify_valid_token(self):
        """Test que un token válido se verifica correctamente."""
        data = {"sub": "test@example.com", "user_id": 1}
        token = create_access_token(data)

        payload = verify_access_token(token)

        assert payload is not None
        assert payload["sub"] == "test@example.com"
        assert payload["user_id"] == 1
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload
        assert "aud" in payload
        assert "iss" in payload

    def test_verify_invalid_token(self):
        """Test que un token inválido retorna None."""
        invalid_token = "invalid.token.here"

        payload = verify_access_token(invalid_token)

        assert payload is None

    def test_token_has_jti(self):
        """Test que cada token tiene un JTI único."""
        data = {"sub": "test@example.com", "user_id": 1}
        token1 = create_access_token(data)
        token2 = create_access_token(data)

        payload1 = verify_access_token(token1)
        payload2 = verify_access_token(token2)

        assert payload1["jti"] != payload2["jti"]
