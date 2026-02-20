"""Testes do cache de consulta de indicadores genéricos."""

import uuid
from unittest.mock import AsyncMock

from fastapi import FastAPI
from types import SimpleNamespace

from app.schemas.indicators import GenericIndicatorRequest
from app.services.generic_indicator_service import GenericIndicatorService
import pytest

from app.api.v1.indicators import generic as generic_router
from app.api.deps import get_current_user, get_tenant_permission_service
from app.core.tenant import get_tenant_id
from app.db.base import get_db
from app.services.tenant_policy_service import get_tenant_policy_service
from .http_test_client import make_sync_asgi_client

class _MemoryQueryCache:
    """Cache em memória para validar read/write no fluxo de serviço."""

    def __init__(self):
        self.store: dict[str, list[dict]] = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: list[dict]):
        self.store[key] = value


class _CountingBigQueryClient:
    """Cliente fake para garantir reuso por cache."""

    def __init__(self):
        self.executions = 0

    async def execute_query(self, query: str, *_, **__):
        self.executions += 1
        return [
            {
                "id_municipio": "3304557",
                "ano": 2023,
                "pib_municipal": 1000.0,
            }
        ]

    async def get_dry_run_results(self, _query: str):
        return {
            "total_bytes_processed": 10,
            "total_bytes_billed": 10,
            "cache_hit": False,
        }


@pytest.mark.asyncio
async def test_query_cache_hit_prevents_second_bigquery_execution():
    service = GenericIndicatorService(
        bq_client=_CountingBigQueryClient(),
        query_cache=_MemoryQueryCache(),
    )
    request = GenericIndicatorRequest(
        codigo_indicador="IND-5.01",
        id_municipio="3304557",
        ano=2023,
    )

    assert service.bq_client.executions == 0

    r1 = await service.execute_indicator(request, tenant_id="00000000-0000-0000-0000-000000000001")
    assert r1.cache_hit is False
    assert r1.data
    assert service.bq_client.executions == 1

    r2 = await service.execute_indicator(request, tenant_id="00000000-0000-0000-0000-000000000001")
    assert r2.cache_hit is True
    assert r2.data == r1.data
    assert service.bq_client.executions == 1


@pytest.mark.asyncio
async def test_query_cache_is_parameter_sensitive():
    service = GenericIndicatorService(
        bq_client=_CountingBigQueryClient(),
        query_cache=_MemoryQueryCache(),
    )
    req_2023 = GenericIndicatorRequest(
        codigo_indicador="IND-5.01",
        id_municipio="3304557",
        ano=2023,
    )
    req_2024 = GenericIndicatorRequest(
        codigo_indicador="IND-5.01",
        id_municipio="3304557",
        ano=2024,
    )

    await service.execute_indicator(req_2023)
    await service.execute_indicator(req_2024)

    assert service.bq_client.executions == 2


class _PolicyService:
    async def get_policy(self, _db, _tenant_id):
        return {}


def test_cache_header_set_from_generic_endpoint():
    service = GenericIndicatorService(
        bq_client=_CountingBigQueryClient(),
        query_cache=_MemoryQueryCache(),
    )
    policy_service = _PolicyService()
    tenant_id = uuid.uuid4()

    test_app = FastAPI()
    test_app.include_router(generic_router.router)

    async def _mock_db():
        yield AsyncMock()

    async def _mock_tenant():
        return tenant_id

    async def _mock_user():
        return SimpleNamespace(
            id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
            tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            roles=["viewer"],
            tenant=SimpleNamespace(plano="enterprise"),
        )

    test_app.dependency_overrides[get_db] = _mock_db
    test_app.dependency_overrides[get_tenant_id] = _mock_tenant
    test_app.dependency_overrides[get_current_user] = _mock_user
    test_app.dependency_overrides[generic_router.get_generic_indicator_service] = lambda: service
    test_app.dependency_overrides[get_tenant_policy_service] = lambda: policy_service
    async def _mock_permission_service():
        class _PermissionService:
            async def list_permissions_by_roles(self, _db, _tenant_id, _roles):
                return {}

        return _PermissionService()

    test_app.dependency_overrides[get_tenant_permission_service] = _mock_permission_service

    client = make_sync_asgi_client(test_app)

    payload = {
        "codigo_indicador": "IND-5.01",
        "id_municipio": "3304557",
        "ano": 2023,
    }

    resp1 = client.post("/indicators/query", json=payload)
    assert resp1.status_code == 200
    assert resp1.headers.get("X-Cache-Hit") == "false"

    resp2 = client.post("/indicators/query", json=payload)
    assert resp2.status_code == 200
    assert resp2.headers.get("X-Cache-Hit") == "true"
    assert service.bq_client.executions == 1
