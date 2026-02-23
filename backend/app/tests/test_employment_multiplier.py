"""
Testes para endpoint e serviço de impacto de emprego (Módulo 3).
"""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.services.employment_multiplier import (
    DEFAULT_SECTOR,
    EmploymentMultiplierService,
    MULTIPLIER_DEFAULTS,
)
from app.schemas.employment_multiplier import (
    CausalMultiplier,
    LiteratureMultiplier,
    EmploymentImpactResult,
)


@pytest.fixture
def service():
    return EmploymentMultiplierService()


@pytest.fixture
def sample_multiplier():
    return EmploymentMultiplierService.get_literature_multiplier()


class TestLiteratureMultiplier:
    def test_default_returns_valid(self, service):
        m = service.get_literature_multiplier()
        assert isinstance(m, LiteratureMultiplier)
        assert m.coefficient > 0
        assert m.range_low <= m.coefficient <= m.range_high
        assert m.confidence in ("strong", "moderate", "weak")

    def test_port_operations(self, service):
        m = service.get_literature_multiplier(sector="port_operations")
        assert m.coefficient == MULTIPLIER_DEFAULTS["port_operations"]["coefficient"]

    def test_port_logistics(self, service):
        m = service.get_literature_multiplier(sector="port_logistics")
        assert m.coefficient == MULTIPLIER_DEFAULTS["port_logistics"]["coefficient"]

    def test_brazil_region(self, service):
        m = service.get_literature_multiplier(region="Brasil")
        assert "Ministério" in m.source or "UNCTAD" in m.source

    def test_unknown_sector_fallback(self, service):
        m = service.get_literature_multiplier(sector="xyz")
        assert m.coefficient == MULTIPLIER_DEFAULTS[DEFAULT_SECTOR]["coefficient"]

    def test_all_sectors_valid(self):
        for key, data in MULTIPLIER_DEFAULTS.items():
            assert data["coefficient"] > 0
            assert "breakdown" in data


class TestCalculateIndirectJobs:
    def test_basic(self, service, sample_multiplier):
        r = service.calculate_indirect_jobs(1000, sample_multiplier, municipality_id="3548500")
        assert r.direct_jobs == 1000
        assert r.indirect_estimated > 0
        assert r.induced_estimated > 0
        assert r.total_impact > r.direct_jobs
        assert r.multiplier_type == "literature"

    def test_total_equals_sum(self, service, sample_multiplier):
        r = service.calculate_indirect_jobs(500, sample_multiplier)
        assert abs(r.total_impact - (r.direct_jobs + r.indirect_estimated + r.induced_estimated)) < 1.0

    def test_zero_jobs(self, service, sample_multiplier):
        r = service.calculate_indirect_jobs(0, sample_multiplier)
        assert r.total_impact == 0


class TestEvaluateConfidence:
    def test_strong(self, service):
        assert service.evaluate_causal_confidence(0.01, 50) == "strong"

    def test_moderate(self, service):
        assert service.evaluate_causal_confidence(0.07, 100) == "moderate"

    def test_weak(self, service):
        assert service.evaluate_causal_confidence(0.15, 100) == "weak"


class TestBuildCausalEstimate:
    def test_basic(self, service):
        c = CausalMultiplier(
            coefficient=2.3,
            std_error=0.5,
            p_value=0.01,
            ci_lower=1.3,
            ci_upper=3.3,
            confidence="strong",
            n_obs=100,
            method="iv_2sls",
        )
        r = service.build_causal_estimate(1000, c, municipality_id="3548500")
        assert r.multiplier_type == "causal"
        assert r.total_impact > r.direct_jobs


class TestImpactQuery:
    @pytest.mark.asyncio
    async def test_get_impacto_emprego_with_data(self, service):
        service._execute_query = AsyncMock(
            side_effect=[
                [{"id_municipio": "3548500", "nome_municipio": "Santos", "ano": 2023, "empregos_portuarios": 1200}],
                [{"id_municipio": "3548500", "nome_municipio": "Santos", "ano": 2023, "empregos_totais": 12000}],
                [{"id_municipio": "3548500", "nome_municipio": "Santos", "ano": 2023, "participacao_emprego_local": 10.0}],
                [{"id_municipio": "3548500", "nome_municipio": "Santos", "ano": 2023, "tonelagem_total": 2500000, "ton_por_empregado": 2083.33}],
            ]
        )
        rows = await service.get_impacto_emprego("3548500", ano=2023)
        assert len(rows) == 1
        item = rows[0]
        assert item.empregos_diretos == 1200
        assert item.empregos_totais == 12000
        assert item.participacao_emprego_local == 10.0
        assert item.metodo == "multiplicador_literatura"
        assert item.empregos_por_milhao_toneladas is not None
        assert item.empregos_por_milhao_toneladas > 0

    @pytest.mark.asyncio
    async def test_get_impacto_emprego_with_scenario(self, service):
        service._execute_query = AsyncMock(
            side_effect=[
                [{"id_municipio": "3548500", "nome_municipio": "Santos", "ano": 2023, "empregos_portuarios": 1000}],
                [{"id_municipio": "3548500", "nome_municipio": "Santos", "ano": 2023, "empregos_totais": 12000}],
                [{"id_municipio": "3548500", "nome_municipio": "Santos", "ano": 2023, "participacao_emprego_local": 8.3}],
                [{"id_municipio": "3548500", "nome_municipio": "Santos", "ano": 2023, "ton_por_empregado": 2000.0}],
            ]
        )
        rows = await service.get_impacto_emprego("3548500", ano=2023, delta_tonelagem_pct=10.0)
        assert len(rows) == 1
        item = rows[0]
        assert item.scenario is not None
        assert item.scenario.delta_tonelagem_pct == 10.0
        assert item.scenario.delta_emprego_total > 0

    @pytest.mark.asyncio
    async def test_get_impacto_emprego_no_data(self, service):
        service._execute_query = AsyncMock(return_value=[])
        rows = await service.get_impacto_emprego("0000000", ano=2023)
        assert rows == []


class TestEndpoint:
    def test_get_multiplier_with_data(self, monkeypatch):
        from app.api.v1 import employment
        from app.main import app
        from app.tests.http_test_client import make_sync_asgi_client

        async def _fake_get_impacto_emprego(self, municipality_id: str, ano=None, delta_tonelagem_pct=None):
            return [
                EmploymentImpactResult(
                    municipality_id="3548500",
                    municipality_name="Santos",
                    ano=2023,
                    empregos_diretos=1200,
                    empregos_totais=12000,
                    participacao_emprego_local=10.0,
                    tonelagem_antaq_milhoes=2.5,
                    empregos_por_milhao_toneladas=480000.0,
                    empregos_indiretos_estimados=1440.0,
                    empregos_induzidos_estimados=960.0,
                    emprego_total_estimado=3600.0,
                    metodologia="Proxy por multiplicador de literatura aplicado ao volume de empregos diretos e participação setorial; não constitui estimativa causal.",
                    indicador_de_confianca="moderado",
                    correlacao_ou_proxy=True,
                    metodo="multiplicador_literatura",
                    fonte="RAIS + ANTAQ (proxy de evidência de associação)",
                )
            ]

        monkeypatch.setattr(employment.EmploymentMultiplierService, "get_impacto_emprego", _fake_get_impacto_emprego)

        client = make_sync_asgi_client(app)
        response = client.get("/api/v1/employment/multipliers/3548500?ano=2023")
        assert response.status_code == 200
        payload = response.json()
        assert payload["data"]
        assert payload["municipality_id"] == "3548500"
        assert payload["metodo"] == "multiplicador_literatura"
        assert payload["estimate"]["direct_jobs"] == 1200

    def test_get_multiplier_no_data(self, monkeypatch):
        from app.api.v1 import employment
        from app.main import app
        from app.tests.http_test_client import make_sync_asgi_client

        async def _fake_get_impacto_emprego(self, municipality_id: str, ano=None, delta_tonelagem_pct=None):
            return []

        monkeypatch.setattr(employment.EmploymentMultiplierService, "get_impacto_emprego", _fake_get_impacto_emprego)

        client = make_sync_asgi_client(app)
        response = client.get("/api/v1/employment/multipliers/0000000?ano=2023")
        assert response.status_code == 200
        payload = response.json()
        assert payload["data"] == []

    def test_empty_id_returns_400(self):
        from app.api.v1 import employment
        from app.main import app
        from app.tests.http_test_client import make_sync_asgi_client

        # não patcha serviço: a validação do id deve ocorrer antes de chamar o service
        client = make_sync_asgi_client(app)
        response = client.get("/api/v1/employment/multipliers/%20")
        assert response.status_code == 400
