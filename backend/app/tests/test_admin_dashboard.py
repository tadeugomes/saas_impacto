"""Testes do endpoint administrativo de uso por plano do tenant."""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi import FastAPI

from app.api.deps import get_tenant_id, require_admin
from app.api.v1 import admin_dashboard as admin_dashboard_router_module
from app.api.v1.admin_dashboard import router as admin_dashboard_router
from app.db.base import get_db
from app.schemas.admin import TenantUsageResponse
from app.tests.http_test_client import make_sync_asgi_client


class _FakeDashboardService:
    """Intercepta chamada do serviço e registra parâmetros de entrada."""

    def __init__(self, response: TenantUsageResponse):
        self.response = response
        self.calls: list[tuple[uuid.UUID, int]] = []

    async def usage(self, db, tenant_id: uuid.UUID, rate_limit_cap: int) -> TenantUsageResponse:
        self.calls.append((tenant_id, rate_limit_cap))
        return self.response


def _mock_db(tenant_plan: str | None):
    async def _inner():
        row = SimpleNamespace(
            scalar_one_or_none=lambda: tenant_plan,
        )
        db = AsyncMock()
        db.execute = AsyncMock(return_value=row)
        yield db

    return _inner


def _mock_tenant(tenant_id: uuid.UUID):
    async def _inner() -> uuid.UUID:
        return tenant_id

    return _inner


def _build_admin_app(tenant_id: uuid.UUID, tenant_plan: str | None, service: _FakeDashboardService):
    app = FastAPI()
    app.include_router(admin_dashboard_router, prefix="/api/v1")

    app.dependency_overrides[get_db] = _mock_db(tenant_plan)
    app.dependency_overrides[get_tenant_id] = _mock_tenant(tenant_id)
    app.dependency_overrides[require_admin] = lambda: SimpleNamespace()
    app.dependency_overrides[admin_dashboard_router_module.get_dashboard_service] = lambda: service
    return app


def _make_response():
    return TenantUsageResponse(
        total_analises=3,
        analises_sucesso=2,
        analises_falha=1,
        usuarios_ativos_7d=5,
        usuarios_ativos_30d=8,
        bq_bytes_last_30d=1_024,
        taxa_rate_limit=0.05,
        top_indicadores=[],
    )


def test_admin_dashboard_uses_tenant_plan_to_set_rate_limit_cap():
    tenant_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    service = _FakeDashboardService(_make_response())
    app = _build_admin_app(tenant_id, tenant_plan="pro", service=service)
    client = make_sync_asgi_client(app)

    response = client.get("/api/v1/admin/dashboard/usage")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_analises"] == 3
    assert service.calls
    assert service.calls[0][0] == tenant_id
    assert service.calls[0][1] == 500


def test_admin_dashboard_defaults_to_basic_for_invalid_plan():
    tenant_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    service = _FakeDashboardService(_make_response())
    app = _build_admin_app(tenant_id, tenant_plan="ultra", service=service)
    client = make_sync_asgi_client(app)

    response = client.get("/api/v1/admin/dashboard/usage")

    assert response.status_code == 200
    assert service.calls[0][1] == 100
