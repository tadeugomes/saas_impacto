"""Testes E4/E5 para Modulo 5: município de influencia, allowlist e quota."""

import uuid
import pytest

from app.schemas.indicators import GenericIndicatorRequest
from app.services.generic_indicator_service import (
    GenericIndicatorService,
    IndicatorAccessError,
    IndicatorQuotaError,
)
from app.services.tenant_policy_service import TenantPolicyService


class _AreaBigQueryClient:
    """Client fake com respostas por municipio e dry run controlado."""

    def __init__(self, bytes_processed: int = 50):
        self.bytes_processed = bytes_processed
        self.executed_queries = 0

    async def execute_query(self, query: str, *_, **__):
        self.executed_queries += 1
        if "arrecadacao_iss" in query:
            if "id_municipio = '1111111'" in query:
                return [{"id_municipio": "1111111", "ano": 2023, "arrecadacao_iss": 10.0}]
            if "id_municipio = '2222222'" in query:
                return [{"id_municipio": "2222222", "ano": 2023, "arrecadacao_iss": 20.0}]
            if "id_municipio = '3304557'" in query:
                return [{"id_municipio": "3304557", "ano": 2023, "arrecadacao_iss": 15.0}]
            return []
        if "arrecadacao_icms" in query:
            if "id_municipio = '1111111'" in query:
                return [{"id_municipio": "1111111", "ano": 2023, "arrecadacao_icms": 11.0}]
            if "id_municipio = '2222222'" in query:
                return [{"id_municipio": "2222222", "ano": 2023, "arrecadacao_icms": 22.0}]
            if "id_municipio = '3304557'" in query:
                return [{"id_municipio": "3304557", "ano": 2023, "arrecadacao_icms": 33.0}]
            return []
        if "id_municipio = '1111111'" in query:
            return [{"id_municipio": "1111111", "ano": 2023, "pib_municipal": 100.0}]
        if "id_municipio = '2222222'" in query:
            return [{"id_municipio": "2222222", "ano": 2023, "pib_municipal": 200.0}]
        if "id_municipio = '3304557'" in query:
            return [{"id_municipio": "3304557", "ano": 2023, "pib_municipal": 123.0}]
        return []

    async def get_dry_run_results(self, _query: str):
        return {
            "total_bytes_processed": self.bytes_processed,
            "total_bytes_billed": self.bytes_processed,
            "cache_hit": False,
        }


class _PolicyBigQueryClient:
    """Client fake para validar existencia de municipios no diretorio IBGE."""

    def __init__(self, existing_ids: list[str]):
        self.existing_ids = set(existing_ids)

    async def execute_query(self, query: str, *_, **__):
        found = []
        for item in self.existing_ids:
            if f"'{item}'" in query:
                found.append({"id_municipio": item})
        return found


class _PolicyServiceNoDB(TenantPolicyService):
    """Servico de politica para testes sem dependencia de banco SQL."""

    async def get_policy(self, db, tenant_id):
        return {
            "allowed_installations": [],
            "allowed_municipios": [],
            "area_influencia": {},
            "municipio_influencia": {},
            "max_bytes_per_query": None,
        }

    async def save_policy(self, db, tenant_id, policy):
        return policy


@pytest.mark.asyncio
async def test_module5_e4_area_influence_aggregates_municipios_with_breakdown():
    service = GenericIndicatorService(bq_client=_AreaBigQueryClient(bytes_processed=10))
    request = GenericIndicatorRequest(
        codigo_indicador="IND-5.01",
        id_instalacao="INST_TESTE",
        ano=2023,
        include_breakdown=True,
    )
    tenant_policy = {
        "area_influencia": {
            "INST_TESTE": [
                {"id_municipio": "1111111", "peso": 1.0},
                {"id_municipio": "2222222", "peso": 1.0},
            ]
        },
        "allowed_municipios": ["1111111", "2222222"],
        "max_bytes_per_query": 10_000,
    }

    response = await service.execute_indicator(
        request,
        tenant_policy=tenant_policy,
        tenant_id="00000000-0000-0000-0000-000000000001",
        user_id="00000000-0000-0000-0000-000000000002",
    )

    assert response.data
    assert response.data[0]["pib_municipal"] == 300.0
    assert response.data[0]["ano"] == 2023
    assert response.data[0]["municipios_agregados"] == 2
    assert "breakdown" in response.data[0]
    assert any(
        w.tipo in {"area_influencia_agregada", "municipio_influencia_agregada"}
        for w in response.warnings
    )


@pytest.mark.asyncio
async def test_module6_e4_area_influence_aggregates_iss_with_breakdown():
    service = GenericIndicatorService(bq_client=_AreaBigQueryClient(bytes_processed=10))
    request = GenericIndicatorRequest(
        codigo_indicador="IND-6.02",
        id_instalacao="INST_TESTE",
        ano=2023,
        include_breakdown=True,
    )
    tenant_policy = {
        "area_influencia": {
            "INST_TESTE": [
                {"id_municipio": "1111111", "peso": 1.0},
                {"id_municipio": "2222222", "peso": 1.0},
            ]
        },
        "allowed_municipios": ["1111111", "2222222"],
        "max_bytes_per_query": 10_000,
    }

    response = await service.execute_indicator(
        request,
        tenant_policy=tenant_policy,
        tenant_id="00000000-0000-0000-0000-000000000001",
        user_id="00000000-0000-0000-0000-000000000002",
    )

    assert response.data
    assert response.data[0]["arrecadacao_iss"] == 30.0
    assert response.data[0]["ano"] == 2023
    assert response.data[0]["municipios_agregados"] == 2
    assert "breakdown" in response.data[0]
    assert any(
        w.tipo in {"area_influencia_agregada", "municipio_influencia_agregada"}
        for w in response.warnings
    )


@pytest.mark.asyncio
async def test_module5_e5_blocks_not_allowed_municipio():
    service = GenericIndicatorService(bq_client=_AreaBigQueryClient(bytes_processed=10))
    request = GenericIndicatorRequest(
        codigo_indicador="IND-5.01",
        id_municipio="3304557",
        ano=2023,
    )

    with pytest.raises(IndicatorAccessError):
        await service.execute_indicator(
            request,
            tenant_policy={"allowed_municipios": ["3550308"]},
        )


@pytest.mark.asyncio
async def test_module5_e5_blocks_when_query_exceeds_tenant_bytes_limit():
    service = GenericIndicatorService(bq_client=_AreaBigQueryClient(bytes_processed=1000))
    request = GenericIndicatorRequest(
        codigo_indicador="IND-5.01",
        id_municipio="3304557",
        ano=2023,
    )

    with pytest.raises(IndicatorQuotaError):
        await service.execute_indicator(
            request,
            tenant_policy={"allowed_municipios": ["3304557"], "max_bytes_per_query": 100},
        )


def test_tenant_policy_service_parse_backward_compatible_formats():
    service = TenantPolicyService()

    parsed_legacy = service.parse_policy('["Porto de Santos","Porto de Vitoria"]')
    assert parsed_legacy["allowed_installations"] == ["Porto de Santos", "Porto de Vitoria"]
    assert parsed_legacy["area_influencia"] == {}
    assert parsed_legacy["municipio_influencia"] == {}

    parsed_v2 = service.parse_policy(
        """
        {
          "allowed_installations": ["Porto de Santos"],
          "allowed_municipios": ["3548500"],
          "max_bytes_per_query": 2048,
            "municipio_influencia": {
                "Porto de Santos": [
                  {"id_municipio": "3548500", "peso": 1.2},
                  {"id_municipio": "3551009", "peso": 0.8}
                ]
            }
        }
        """
    )
    assert parsed_v2["allowed_municipios"] == ["3548500"]
    assert parsed_v2["max_bytes_per_query"] == 2048
    assert len(parsed_v2["area_influencia"]["Porto de Santos"]) == 2
    assert len(parsed_v2["municipio_influencia"]["Porto de Santos"]) == 2


@pytest.mark.asyncio
async def test_tenant_policy_service_rejects_missing_ibge_municipios():
    service = TenantPolicyService(bq_client=_PolicyBigQueryClient(existing_ids=["3548500"]))

    with pytest.raises(ValueError):
        await service._validate_municipios_exist_in_ibge(["3548500", "3551009"])


@pytest.mark.asyncio
async def test_tenant_policy_service_accepts_existing_ibge_municipios():
    service = TenantPolicyService(
        bq_client=_PolicyBigQueryClient(existing_ids=["3548500", "3551009"])
    )

    await service._validate_municipios_exist_in_ibge(["3548500", "3551009"])


@pytest.mark.asyncio
async def test_tenant_policy_service_set_allowlist_rejects_invalid_format():
    service = _PolicyServiceNoDB(
        bq_client=_PolicyBigQueryClient(existing_ids=["3548500", "3551009"])
    )
    tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

    with pytest.raises(ValueError):
        await service.set_allowlist_policy(
            db=None,
            tenant_id=tenant_id,
            allowed_municipios=["35A8500"],
            max_bytes_per_query=1000,
        )


@pytest.mark.asyncio
async def test_tenant_policy_service_set_allowlist_rejects_missing_ibge():
    service = _PolicyServiceNoDB(bq_client=_PolicyBigQueryClient(existing_ids=["3548500"]))
    tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

    with pytest.raises(ValueError):
        await service.set_allowlist_policy(
            db=None,
            tenant_id=tenant_id,
            allowed_municipios=["3548500", "3551009"],
            max_bytes_per_query=1000,
        )


@pytest.mark.asyncio
async def test_tenant_policy_service_set_allowlist_accepts_valid_ids_and_deduplicates():
    service = _PolicyServiceNoDB(
        bq_client=_PolicyBigQueryClient(existing_ids=["3548500", "3551009"])
    )
    tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

    updated = await service.set_allowlist_policy(
        db=None,
        tenant_id=tenant_id,
        allowed_municipios=["3548500", "3551009", "3551009", " 3548500 "],
        max_bytes_per_query=2048,
    )

    assert updated["allowed_municipios"] == ["3548500", "3551009"]
    assert updated["max_bytes_per_query"] == 2048
