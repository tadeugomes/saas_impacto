"""Testes de RBAC para endpoints protegidos."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from fastapi import FastAPI

from app.api.deps import get_current_user
from app.api.v1.indicators import generic as indicator_router
from app.api.v1.impacto_economico import router as impacto_router
from app.core.tenant import get_tenant_id
from app.db.base import get_db
from app.schemas.indicators import GenericIndicatorResponse
from app.schemas.impacto_economico import (
    EconomicImpactAnalysisCreateRequest,
    EconomicImpactAnalysisResponse,
)
from app.api.deps import get_tenant_permission_service as _get_permission_dep
from app.services.tenant_policy_service import get_tenant_policy_service
from app.tests.http_test_client import make_sync_asgi_client


class _PolicyService:
    async def get_policy(self, _db, _tenant_id):
        return {}


class _PermissionService:
    def __init__(self, by_role: dict[str, list[tuple[int, str, bool]]]):
        self.by_role = {
            role.lower(): list(permissions)
            for role, permissions in by_role.items()
        }

    async def list_permissions_by_roles(
        self, db, tenant_id, roles,
    ):
        del db, tenant_id
        return {
            role: [
                {"module_number": module_number, "action": action}
                for module_number, action, allowed in perms
                if allowed
            ]
            for role, perms in self.by_role.items()
            if role in roles
        }

    async def list_permissions(self, db, tenant_id, role):
        del db, tenant_id
        normalized = role.lower()
        permissions = self.by_role.get(normalized, [])
        return [
            {"module_number": module_number, "action": action}
            for module_number, action, allowed in permissions
            if allowed
        ]

    async def set_permissions_for_role(self, db, tenant_id, role, permissions):
        del db, tenant_id
        normalized = role.lower()
        self.by_role[normalized] = list(permissions)
        return [dict(module_number=p[0], action=p[1]) for p in permissions if p[2]]


def _mock_db():
    async def _inner():
        yield AsyncMock()

    return _inner


def _mock_tenant(tenant_id: uuid.UUID):
    async def _inner() -> uuid.UUID:
        return tenant_id

    return _inner


def _mock_user(
    user_id: str,
    roles: list[str],
    plan: str,
    *,
    tenant_id: str = "00000000-0000-0000-0000-000000000001",
):
    return SimpleNamespace(
        id=uuid.UUID(user_id),
        tenant_id=uuid.UUID(tenant_id),
        roles=roles,
        is_admin=lambda: "admin" in {r.strip().lower() for r in roles},
        tenant=SimpleNamespace(plano=plan),
    )


def _build_indicator_response() -> GenericIndicatorResponse:
    return GenericIndicatorResponse(
        codigo_indicador="IND-5.01",
        nome="PIB Municipal",
        unidade="R$",
        unctad=False,
        modulo=5,
        data=[
            {
                "id_municipio": "3304557",
                "ano": 2023,
                "valor": 123.4,
            }
        ],
    )


class _IndicatorService:
    async def execute_indicator(self, *args, **kwargs) -> GenericIndicatorResponse:
        return _build_indicator_response()


def _build_indicator_app(
    user: SimpleNamespace,
    permission_service: _PermissionService | None = None,
):
    app = FastAPI()
    app.include_router(indicator_router.router)

    service = _IndicatorService()

    app.dependency_overrides[get_db] = _mock_db()
    app.dependency_overrides[get_tenant_id] = _mock_tenant(
        uuid.UUID("00000000-0000-0000-0000-000000000001")
    )
    app.dependency_overrides[indicator_router.get_generic_indicator_service] = (
        lambda: service
    )
    app.dependency_overrides[get_tenant_policy_service] = lambda: _PolicyService()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[_get_permission_dep] = (
        lambda: permission_service or _PermissionService({})
    )
    return app


def test_query_indicator_read_requires_plan_access():
    app = _build_indicator_app(_mock_user(
        "11111111-1111-1111-1111-111111111111",
        roles=["viewer"],
        plan="basic",
    ))
    client = make_sync_asgi_client(app)

    payload = {
        "codigo_indicador": "IND-5.01",
        "id_municipio": "3304557",
        "ano": 2023,
    }

    resp = client.post("/indicators/query", json=payload)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Forbidden: insufficient permissions"


def test_query_indicator_read_allows_plan_and_role():
    app = _build_indicator_app(_mock_user(
        "22222222-2222-2222-2222-222222222222",
        roles=["viewer"],
        plan="enterprise",
    ))
    client = make_sync_asgi_client(app)

    payload = {
        "codigo_indicador": "IND-5.01",
        "id_municipio": "3304557",
        "ano": 2023,
    }

    resp = client.post("/indicators/query", json=payload)
    assert resp.status_code == 200
    assert resp.json()["codigo_indicador"] == "IND-5.01"


def test_query_indicator_read_can_be_explicitly_restricted_by_tenant_role_permissions():
    app = _build_indicator_app(
        _mock_user(
            "55555555-5555-5555-5555-555555555555",
            roles=["viewer"],
            plan="enterprise",
        ),
        permission_service=_PermissionService({"viewer": [(1, "read", True)]}),
    )
    client = make_sync_asgi_client(app)

    payload = {
        "codigo_indicador": "IND-5.01",
        "id_municipio": "3304557",
        "ano": 2023,
    }

    resp = client.post("/indicators/query", json=payload)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Forbidden: insufficient permissions"


def test_tenant_permission_endpoints_allow_admin_only():
    tenant_service = _PermissionService({"viewer": []})

    app = _build_indicator_app(
        _mock_user(
            "66666666-6666-6666-6666-666666666666",
            roles=["viewer"],
            plan="enterprise",
        ),
        permission_service=tenant_service,
    )
    client = make_sync_asgi_client(app)

    list_resp = client.get("/indicators/permissions/viewer")
    assert list_resp.status_code == 403

    app = _build_indicator_app(
        _mock_user(
            "77777777-7777-7777-7777-777777777777",
            roles=["admin"],
            plan="enterprise",
        ),
        permission_service=tenant_service,
    )
    client = make_sync_asgi_client(app)

    list_resp = client.get("/indicators/permissions/viewer")
    assert list_resp.status_code == 200
    assert list_resp.json() == {"role": "viewer", "permissions": []}

    put_resp = client.put(
        "/indicators/permissions/viewer",
        json={
            "permissions": [
                {"module_number": 5, "action": "read", "allowed": True},
                {"module_number": 5, "action": "execute", "allowed": False},
            ]
        },
    )
    assert put_resp.status_code == 200
    assert put_resp.json() == {
        "role": "viewer",
        "permissions": [{"module_number": 5, "action": "read", "allowed": True}],
    }

    updated = client.get("/indicators/permissions/viewer").json()
    assert {"module_number": 5, "action": "read", "allowed": True} in updated["permissions"]


def _build_impacto_app(user: SimpleNamespace, service_result: Any):
    return _build_impacto_app_with_permissions(user, service_result)


def _build_impacto_app_with_permissions(
    user: SimpleNamespace,
    service_result: Any,
    permission_service: _PermissionService | None = None,
):
    app = FastAPI()
    app.include_router(impacto_router.router)

    async def _service_factory():
        return service_result

    app.dependency_overrides[get_db] = _mock_db()
    app.dependency_overrides[get_tenant_id] = _mock_tenant(
        uuid.UUID("00000000-0000-0000-0000-000000000001")
    )
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[impacto_router._get_analysis_service] = _service_factory
    app.dependency_overrides[_get_permission_dep] = (
        lambda: permission_service or _PermissionService({})
    )
    return app


def test_create_analysis_requires_execute_permission():
    user = _mock_user(
        "33333333-3333-3333-3333-333333333333",
        roles=["viewer"],
        plan="enterprise",
    )
    mock_service = MagicMock()
    request = EconomicImpactAnalysisCreateRequest(
        method="did",
        treated_ids=["2100055"],
        treatment_year=2015,
        scope="state",
        outcomes=["pib"],
        ano_inicio=2010,
        ano_fim=2024,
    )
    queued = EconomicImpactAnalysisResponse(
        id=uuid.UUID("11111111-1111-1111-1111-111111111122"),
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        user_id=user.id,
        status="queued",
        method="did",
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
    )
    mock_service.create_queued = AsyncMock(return_value=queued)
    app = _build_impacto_app(user, mock_service)
    client = make_sync_asgi_client(app)

    with patch(
        "app.api.v1.impacto_economico.router.run_economic_impact_analysis"
    ) as mocked_task:
        mocked_task.delay = MagicMock()
        resp = client.post("/impacto-economico/analises", json=request.model_dump())
        assert resp.status_code == 403


def test_create_analysis_allows_analyst_execute():
    user = _mock_user(
        "44444444-4444-4444-4444-444444444444",
        roles=["analyst"],
        plan="enterprise",
    )
    mock_service = MagicMock()
    request = EconomicImpactAnalysisCreateRequest(
        method="did",
        treated_ids=["2100055"],
        treatment_year=2015,
        scope="state",
        outcomes=["pib"],
        ano_inicio=2010,
        ano_fim=2024,
    )
    queued = EconomicImpactAnalysisResponse(
        id=uuid.UUID("11111111-1111-1111-1111-111111111133"),
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        user_id=user.id,
        status="queued",
        method="did",
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
    )
    mock_service.create_queued = AsyncMock(return_value=queued)
    app = _build_impacto_app(user, mock_service)
    client = make_sync_asgi_client(app)

    with patch(
        "app.api.v1.impacto_economico.router.run_economic_impact_analysis"
    ) as mocked_task:
        mocked_task.delay = MagicMock()
        resp = client.post("/impacto-economico/analises", json=request.model_dump())

    assert resp.status_code == 202
    assert resp.json()["status"] == "queued"
    assert mocked_task.delay.called is True
