"""Testes de compliance/auditoria (registro e consulta de trilhas)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock
import asyncio

from fastapi import FastAPI
from types import SimpleNamespace

from app.api.deps import get_current_user
from app.api.v1 import admin as admin_router_module
from app.api.v1.admin import router as admin_router
from app.db.base import get_db
from app.core.tenant import get_tenant_id
from app.services.audit_service import AuditService
from app.tests.http_test_client import make_sync_asgi_client


class _FakeAuditService:
    """Implementação mínima para interceptar chamadas e retornar payload controlado."""

    def __init__(self, items, total: int):
        self.items = items
        self.total = total
        self.calls: list[dict] = []

    async def list_logs(self, db, tenant_id, **kwargs):  # noqa: ANN001
        del db
        self.calls.append({"tenant_id": tenant_id, "kwargs": kwargs})
        return self.items, self.total


def _mock_db():
    async def _inner():
        yield AsyncMock()

    return _inner


def _mock_tenant(tenant_id: uuid.UUID):
    async def _inner() -> uuid.UUID:
        return tenant_id

    return _inner


def _mock_user(is_admin: bool):
    return SimpleNamespace(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        is_admin=lambda: is_admin,
    )


def _build_admin_app(
    tenant_id: uuid.UUID,
    audit_service,
    user,
):
    app = FastAPI()
    app.include_router(admin_router, prefix="/api/v1")

    app.dependency_overrides[get_db] = _mock_db()
    app.dependency_overrides[get_tenant_id] = _mock_tenant(tenant_id)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[admin_router_module.get_audit_service] = lambda: audit_service
    return app


def _build_audit_items(tenant_id: uuid.UUID, user_id: uuid.UUID):
    return [
        SimpleNamespace(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            action="query_indicator",
            resource="/api/v1/indicators/query",
            status_code=200,
            duration_ms=12,
            bytes_processed=10,
            ip="127.0.0.1",
            details={"codigo_indicador": "IND-5.01"},
            request_id="req-1",
            created_at=datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        ),
        SimpleNamespace(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            action="create_analysis",
            resource="/api/v1/impacto-economico/analises",
            status_code=202,
            duration_ms=20,
            bytes_processed=None,
            ip="127.0.0.1",
            details={"method": "did"},
            request_id="req-2",
            created_at=datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
        ),
    ]


def test_audit_logs_requires_admin():
    tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    app = _build_admin_app(
        tenant_id=tenant_id,
        audit_service=_FakeAuditService([], 0),
        user=_mock_user(is_admin=False),
    )
    client = make_sync_asgi_client(app)

    resp = client.get("/api/v1/admin/audit-logs")

    assert resp.status_code == 403
    assert resp.json()["detail"] == "Admin privileges required"


def test_audit_logs_list_with_filters():
    tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    user_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
    service = _FakeAuditService(_build_audit_items(tenant_id, user_id), total=2)

    app = _build_admin_app(
        tenant_id=tenant_id,
        audit_service=service,
        user=_mock_user(is_admin=True),
    )
    client = make_sync_asgi_client(app)

    resp = client.get(
        "/api/v1/admin/audit-logs",
        params={
            "page": 1,
            "page_size": 50,
            "action": "query_indicator",
            "status_code": 200,
            "user_id": str(user_id),
        },
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["total"] == 2
    assert payload["page"] == 1
    assert payload["page_size"] == 50
    assert payload["total_pages"] == 1
    assert len(payload["items"]) == 2
    assert payload["items"][0]["tenant_id"] == str(tenant_id)
    assert payload["items"][0]["user_id"] == str(user_id)
    assert service.calls, "service list_logs deve ser chamado"
    assert service.calls[0]["tenant_id"] == tenant_id
    assert service.calls[0]["kwargs"]["action"] == "query_indicator"
    assert service.calls[0]["kwargs"]["status_code"] == 200


def test_record_action_is_tolerant_to_invalid_tenant():
    service = AuditService()
    db = AsyncMock()
    db.add = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()

    # tenant inválido não deve quebrar o fluxo de negócio
    result = asyncio.run(
        service.record_action(
            db=db,
            tenant_id="not-a-uuid",
            action="test",
            resource="/invalid",
        )
    )

    assert result is None
    db.rollback.assert_awaited_once()
