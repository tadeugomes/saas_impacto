"""Testes para recuperação de senha em AuthService (PR-27)."""

from __future__ import annotations

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from fastapi import HTTPException

from app.services.auth_service import AuthService
from app.config import get_settings

settings = get_settings()


class _FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.setex_calls: list[tuple] = []
        self.get_calls: list[str] = []
        self.delete_calls: list[str] = []

    async def setex(self, key: str, ttl: int, value: str) -> None:
        self.store[key] = value
        self.setex_calls.append((key, ttl, value))

    async def get(self, key: str) -> str | None:
        self.get_calls.append(key)
        return self.store.get(key)

    async def delete(self, key: str) -> int:
        self.delete_calls.append(key)
        if key in self.store:
            del self.store[key]
            return 1
        return 0

    async def aclose(self) -> None:
        return None


def _build_user():
    tenant = SimpleNamespace(ativo=True)
    return SimpleNamespace(id=uuid.uuid4(), ativo=True, tenant=tenant)


def _fake_db_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


class TestAuthServicePasswordReset:
    """Cobertura de geração e consumo de token de recuperação."""

    @pytest.mark.asyncio
    async def test_request_password_reset_stores_token_and_sends_email(self):
        user = _build_user()
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_fake_db_result(user))
        db.commit = AsyncMock()
        service = AuthService(db)

        fake_redis = _FakeRedis()
        with patch.object(
            AuthService,
            "_find_active_user_by_email",
            new=AsyncMock(return_value=user),
        ), \
             patch.object(
                AuthService,
                "_send_reset_email",
                new=AsyncMock(),
             ) as send_email, \
             patch("app.services.auth_service.aioredis.from_url", return_value=fake_redis):
            await service.request_password_reset("user@example.com")
            assert fake_redis.setex_calls
            assert fake_redis.setex_calls[0][1] == settings.password_reset_token_ttl_seconds
            send_email.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_request_password_reset_when_email_not_found_does_nothing(self):
        db = AsyncMock()
        service = AuthService(db)
        fake_redis = _FakeRedis()

        with patch.object(
            AuthService,
            "_find_active_user_by_email",
            new=AsyncMock(return_value=None),
        ), \
             patch("app.services.auth_service.aioredis.from_url", return_value=fake_redis):
            await service.request_password_reset("missing@example.com")
            assert not fake_redis.setex_calls

    @pytest.mark.asyncio
    async def test_confirm_password_reset_updates_hash_and_releases_token(self):
        user = _build_user()
        token = "token-123"
        db = AsyncMock()
        service = AuthService(db)
        fake_redis = _FakeRedis()
        fake_redis.store[f"password-reset:{token}"] = str(user.id)

        with patch.object(AuthService, "_consume_password_reset_token",
                          new=AsyncMock(return_value=user.id)), \
             patch.object(
                 AuthService,
                 "_get_user_by_id",
                 new=AsyncMock(return_value=user),
             ), \
             patch("app.services.auth_service.get_password_hash", return_value="hashed"), \
             patch("app.services.auth_service.aioredis.from_url", return_value=fake_redis):
            await service.confirm_password_reset(token, "NovaSenha123!")
            assert user.hashed_password == "hashed"
            db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_confirm_password_reset_rejects_invalid_token(self):
        db = AsyncMock()
        service = AuthService(db)

        with patch.object(
            AuthService,
            "_consume_password_reset_token",
            new=AsyncMock(return_value=None),
        ), \
             patch("app.services.auth_service.aioredis.from_url", return_value=_FakeRedis()):
            try:
                await service.confirm_password_reset("bad", "NovaSenha123!")
            except HTTPException as exc:
                assert exc.status_code == 400
            else:
                raise AssertionError("Expected HTTPException")
