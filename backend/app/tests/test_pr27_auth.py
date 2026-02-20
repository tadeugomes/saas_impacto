"""Testes para hardening de autenticação (PR-27)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI

from app.api.deps import get_current_user
from app.core.security import blacklist_access_token, create_access_token, decode_access_token
from app.tests.http_test_client import make_sync_asgi_client
from app.db.base import get_db


def _build_auth_app() -> tuple[FastAPI, object]:
    import app.api.v1.auth as auth_router

    app = FastAPI()
    app.include_router(auth_router.router)

    async def _mock_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = _mock_db
    return app, auth_router


def _build_user() -> MagicMock:
    user = MagicMock()
    user.id = uuid.uuid4()
    user.tenant_id = uuid.uuid4()
    return user


class TestAuthRoutesPR27:
    """Cobertura de endpoints de senha e logout."""

    def test_password_reset_request_is_generic_and_calls_service(self):
        app, auth_router = _build_auth_app()
        service = MagicMock()
        service.request_password_reset = AsyncMock()

        with patch.object(auth_router, "AuthService", return_value=service):
            client = make_sync_asgi_client(app)
            response = client.post(
                "/auth/password-reset/request",
                json={"email": "user@example.com"},
            )

        assert response.status_code == 200
        service.request_password_reset.assert_awaited_once_with("user@example.com")
        assert (
            response.json()["message"]
            == "Se o e-mail estiver cadastrado, enviaremos instruções de recuperação."
        )

    def test_password_reset_confirm_validates_password_strength(self):
        app, _ = _build_auth_app()
        client = make_sync_asgi_client(app)

        response = client.post(
            "/auth/password-reset/confirm",
            json={
                "token": "a" * 36,
                "new_password": "123",
            },
        )

        assert response.status_code == 422

    def test_password_reset_confirm_calls_service(self):
        app, auth_router = _build_auth_app()
        service = MagicMock()
        service.confirm_password_reset = AsyncMock()

        with patch.object(auth_router, "AuthService", return_value=service):
            client = make_sync_asgi_client(app)
            response = client.post(
                "/auth/password-reset/confirm",
                json={
                    "token": "a" * 36,
                    "new_password": "NovaSenha123!",
                },
            )

        assert response.status_code == 200
        service.confirm_password_reset.assert_awaited_once_with(
            "a" * 36,
            "NovaSenha123!",
        )

    def test_logout_blacklists_access_token(self):
        app, auth_router = _build_auth_app()
        service = MagicMock()
        service.blacklist_access_token = AsyncMock()
        user = _build_user()

        async def _mock_user():
            return user

        app.dependency_overrides[get_current_user] = _mock_user

        with patch.object(auth_router, "AuthService", return_value=service):
            client = make_sync_asgi_client(app)
            response = client.post(
                "/auth/logout",
                headers={"Authorization": "Bearer token-abc"},
            )

        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"
        service.blacklist_access_token.assert_awaited_once_with("token-abc")


class TestSecurityBlacklistPR27:
    """Cobertura de blacklist em JWT."""

    def test_decode_access_token_checks_blacklist(self):
        token = create_access_token(
            {
                "sub": str(uuid.uuid4()),
                "tenant_id": str(uuid.uuid4()),
            }
        )

        with patch("app.core.security._is_jti_blacklisted", return_value=False):
            assert decode_access_token(token) is not None

        with patch("app.core.security._is_jti_blacklisted", return_value=True):
            assert decode_access_token(token) is None

    def test_blacklist_access_token_adds_jti_with_ttl(self):
        token = create_access_token(
            {
                "sub": str(uuid.uuid4()),
                "tenant_id": str(uuid.uuid4()),
            }
        )
        token_payload = decode_access_token(token, verify_expiration=False)
        assert token_payload is not None
        jti = token_payload["jti"]

        with patch("app.core.security._add_jti_blacklist") as mocked, patch(
            "app.core.security._seconds_until_exp", return_value=300
        ):
            blacklist_access_token(token)

        mocked.assert_called_once_with(jti, 300)
