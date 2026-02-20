"""Testes de rate limiting por tenant."""

from __future__ import annotations

from fastapi import FastAPI
from unittest.mock import patch

from app.core import rate_limit
from app.core.security import create_access_token
from app.tests.http_test_client import make_sync_asgi_client


class _FakeRedis:
    def __init__(self) -> None:
        self.state: dict[str, int] = {}
        self.expirations: dict[str, int] = {}

    async def incr(self, key: str) -> int:
        value = self.state.get(key, 0) + 1
        self.state[key] = value
        return value

    async def expire(self, key: str, _seconds: int) -> bool:
        # Só registra para compatibilidade; não precisamos de cronômetro real nos testes.
        self.expirations[key] = _seconds
        return True

    async def aclose(self) -> None:
        return None


def _build_rate_limited_app() -> FastAPI:
    app = FastAPI()

    @app.get("/api/v1/indicators/modules")
    def modules():
        return {"ok": True}

    @app.get("/api/v1/impacto-economico/analises")
    def analises():
        return {"ok": True}

    app.add_middleware(rate_limit.RateLimitMiddleware)
    return app


def _build_token(tenant_plan: str) -> str:
    return create_access_token(
        {
            "sub": "00000000-0000-0000-0000-000000000001",
            "tenant_id": "00000000-0000-0000-0000-000000000001",
            "tenant_plan": tenant_plan,
        }
    )


def _set_limits(*, basic_rpm: int, basic_analysis_per_hour: int) -> None:
    rate_limit.settings.rate_limit_basic_rpm = basic_rpm
    rate_limit.settings.rate_limit_basic_analyses_per_hour = basic_analysis_per_hour


def test_rate_limit_general_routes_send_limit_headers():
    _set_limits(basic_rpm=2, basic_analysis_per_hour=100)

    fake_redis = _FakeRedis()
    app = _build_rate_limited_app()

    with patch.object(rate_limit.aioredis, "from_url", return_value=fake_redis):
        client = make_sync_asgi_client(app)
        token = _build_token("basic")

        first = client.get(
            "/api/v1/indicators/modules",
            headers={"Authorization": f"Bearer {token}"},
        )
        second = client.get(
            "/api/v1/indicators/modules",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.headers["X-RateLimit-Limit"] == "2"
    assert first.headers["X-RateLimit-Remaining"] in {"1", "2"}
    assert second.headers["X-RateLimit-Limit"] == "2"


def test_rate_limit_general_route_blocks_after_limit():
    _set_limits(basic_rpm=1, basic_analysis_per_hour=100)

    fake_redis = _FakeRedis()
    app = _build_rate_limited_app()

    with patch.object(rate_limit.aioredis, "from_url", return_value=fake_redis):
        client = make_sync_asgi_client(app)
        token = _build_token("basic")

        first = client.get(
            "/api/v1/indicators/modules",
            headers={"Authorization": f"Bearer {token}"},
        )
        second = client.get(
            "/api/v1/indicators/modules",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.headers["X-RateLimit-Limit"] == "1"
    assert second.headers["X-RateLimit-Remaining"] == "0"
    assert second.json()["detail"].startswith("Rate limit exceeded")


def test_rate_limit_analysis_route_uses_special_window():
    _set_limits(basic_rpm=1, basic_analysis_per_hour=1)

    fake_redis = _FakeRedis()
    app = _build_rate_limited_app()

    with patch.object(rate_limit.aioredis, "from_url", return_value=fake_redis):
        client = make_sync_asgi_client(app)
        token = _build_token("basic")

        first = client.get(
            "/api/v1/impacto-economico/analises",
            headers={"Authorization": f"Bearer {token}"},
        )
        second = client.get(
            "/api/v1/impacto-economico/analises",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.headers["X-RateLimit-Limit"] == "1"
