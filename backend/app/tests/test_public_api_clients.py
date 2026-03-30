"""
Testes unitários para BasePublicApiClient, BacenClient, IbgeClient,
MaresClient, AnaClient, InpeClient, DeflationService e AmbientalService.

Usa httpx.MockTransport para simular respostas HTTP sem rede.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.clients.base import BasePublicApiClient, PublicApiError


# ============================================================================
# Helpers
# ============================================================================

def _json_response(data: Any, status: int = 200, headers: dict = None):
    return httpx.Response(status_code=status, json=data, headers=headers or {})


class NoOpCache:
    """Cache stub: sempre miss."""

    async def get(self, key: str):
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        pass


def _mock(client, handler):
    """Injeta MockTransport com base_url válida e NoOpCache."""
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url=client.base_url,
    )
    client._cache = NoOpCache()
    return client


# ============================================================================
# BasePublicApiClient
# ============================================================================

class TestBasePublicApiClient:

    @pytest.mark.asyncio
    async def test_successful_get(self):
        calls = []

        def handler(req):
            calls.append(req)
            return _json_response({"valor": "42"})

        client = _mock(BasePublicApiClient("https://api.test.com", "test"), handler)
        result = await client.get("/endpoint", params={"k": "v"})
        assert result == {"valor": "42"}
        assert len(calls) == 1
        await client.close()

    @pytest.mark.asyncio
    async def test_retry_on_500(self):
        attempt = 0

        def handler(req):
            nonlocal attempt
            attempt += 1
            if attempt == 1:
                return httpx.Response(500, text="err")
            return _json_response({"ok": True})

        client = _mock(BasePublicApiClient("https://api.test.com", "test"), handler)
        result = await client.get("/retry")
        assert result == {"ok": True}
        assert attempt == 2
        await client.close()

    @pytest.mark.asyncio
    async def test_retry_on_429(self):
        attempt = 0

        def handler(req):
            nonlocal attempt
            attempt += 1
            if attempt == 1:
                return httpx.Response(429, text="rate", headers={"Retry-After": "0"})
            return _json_response({"ok": True})

        client = _mock(BasePublicApiClient("https://api.test.com", "test"), handler)
        result = await client.get("/rl")
        assert result == {"ok": True}
        assert attempt == 2
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_on_404(self):
        def handler(req):
            return httpx.Response(404, text="Not Found")

        client = _mock(BasePublicApiClient("https://api.test.com", "test"), handler)
        with pytest.raises(PublicApiError) as exc:
            await client.get("/nf")
        assert exc.value.status_code == 404
        await client.close()

    @pytest.mark.asyncio
    async def test_exhausts_retries(self):
        calls = 0

        def handler(req):
            nonlocal calls
            calls += 1
            return httpx.Response(500, text="err")

        client = _mock(BasePublicApiClient("https://api.test.com", "test"), handler)
        with pytest.raises(PublicApiError, match="Falha após 3"):
            await client.get("/fail")
        assert calls == 3
        await client.close()

    @pytest.mark.asyncio
    async def test_cache_hit(self):
        client = BasePublicApiClient("https://api.test.com", "test")
        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value=[{"cached": True}])
        mock_cache.set = AsyncMock()
        client._cache = mock_cache
        fetcher = AsyncMock(return_value=[{"fresh": True}])

        result = await client.get_cached("key", fetcher)
        assert result == [{"cached": True}]
        fetcher.assert_not_awaited()
        await client.close()

    @pytest.mark.asyncio
    async def test_cache_miss(self):
        client = BasePublicApiClient("https://api.test.com", "test")
        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        client._cache = mock_cache

        async def fetcher():
            return [{"fresh": True}]

        result = await client.get_cached("key", fetcher, ttl=600)
        assert result == [{"fresh": True}]
        mock_cache.set.assert_awaited_once()
        await client.close()

    @pytest.mark.asyncio
    async def test_close_idempotent(self):
        client = BasePublicApiClient("https://api.test.com", "test")
        client._client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda r: _json_response({})),
            base_url="https://api.test.com",
        )
        await client.close()
        assert client._client is None
        await client.close()  # Segunda vez, sem erro


# ============================================================================
# BacenClient
# ============================================================================

class TestBacenClient:

    @pytest.mark.asyncio
    async def test_consultar_serie(self):
        from app.clients.bacen import BacenClient

        data = [{"data": "02/01/2025", "valor": "0.52"}, {"data": "03/01/2025", "valor": "0.48"}]

        def handler(req):
            assert "sgs.433/dados" in str(req.url)
            return _json_response(data)

        client = _mock(BacenClient(), handler)
        result = await client.consultar_serie(433, "01/01/2025", "31/01/2025")
        assert len(result) == 2
        assert result[0]["valor"] == "0.52"
        await client.close()

    @pytest.mark.asyncio
    async def test_indicadores_atuais(self):
        from app.clients.bacen import BacenClient

        def handler(req):
            url = str(req.url)
            if "sgs.4189/" in url:
                return _json_response([{"data": "01/01/2025", "valor": "1.04"}])
            if "sgs.433/" in url:
                return _json_response(
                    [{"data": f"01/{m:02d}/2024", "valor": "0.50"} for m in range(1, 13)]
                )
            if "sgs.3698/" in url:
                return _json_response([{"data": "01/01/2025", "valor": "5.05"}])
            if "sgs.24364/" in url:
                return _json_response([{"data": "01/01/2025", "valor": "150.3"}])
            return _json_response([])

        client = _mock(BacenClient(), handler)
        result = await client.indicadores_atuais()
        assert result["selic_meta_aa"] == 13.22
        assert result["cambio_ptax_venda"] == 5.05
        assert result["ipca_acumulado_12m"] > 0
        await client.close()

    @pytest.mark.asyncio
    async def test_get_deflator_ipca(self):
        from app.clients.bacen import BacenClient

        ipca_data = [
            {"data": f"01/{m:02d}/{y}", "valor": "0.50"}
            for y in [2022, 2023] for m in range(1, 13)
        ]

        client = _mock(BacenClient(), lambda r: _json_response(ipca_data))
        deflator = await client.get_deflator_ipca(2023, 2022, 2023)
        assert abs(deflator[2023] - 1.0) < 0.01
        assert deflator[2022] > 1.0
        await client.close()


# ============================================================================
# IbgeClient
# ============================================================================

class TestIbgeClient:

    @pytest.mark.asyncio
    async def test_buscar_municipios(self):
        from app.clients.ibge import IbgeClient

        data = [{"id": 3550308, "nome": "São Paulo"}, {"id": 3509502, "nome": "Campinas"}]

        client = _mock(IbgeClient(), lambda r: _json_response(data))
        result = await client.buscar_municipios("SP")
        assert len(result) == 2
        assert result[0]["nome"] == "São Paulo"
        await client.close()

    @pytest.mark.asyncio
    async def test_populacao_municipio(self):
        from app.clients.ibge import IbgeClient

        ibge_resp = [{
            "id": "6579", "variavel": "9324",
            "resultados": [{
                "classificacoes": [],
                "series": [{
                    "localidade": {"id": "3550308", "nivel": {"id": "N6"}, "nome": "São Paulo"},
                    "serie": {"2024": "11451245"},
                }],
            }],
        }]

        client = _mock(IbgeClient(), lambda r: _json_response(ibge_resp))
        result = await client.populacao_municipio("3550308", 2024)
        assert result is not None
        assert result["valor"] == 11451245.0
        await client.close()

    @pytest.mark.asyncio
    async def test_populacao_error_returns_none(self):
        from app.clients.ibge import IbgeClient

        client = _mock(IbgeClient(), lambda r: httpx.Response(404, text="NF"))
        result = await client.populacao_municipio("9999999")
        assert result is None
        await client.close()


# ============================================================================
# MaresClient
# ============================================================================

class TestMaresClient:

    @pytest.mark.asyncio
    async def test_fallback_simulado(self):
        """API indisponível → dados simulados."""
        from app.clients.mares import MaresClient

        client = _mock(MaresClient(), lambda r: httpx.Response(503, text="down"))
        result = await client.previsao_mares("23190", "2025-01-01", "2025-01-02")
        assert len(result) > 0
        assert result[0]["simulado"] is True
        assert "altura_metros" in result[0]
        await client.close()

    @pytest.mark.asyncio
    async def test_janelas_navegacao(self):
        from app.clients.mares import MaresClient

        previsao = [
            {"datetime": "2025-01-01T00:00", "altura_metros": 0.3, "tipo": "BM"},
            {"datetime": "2025-01-01T06:00", "altura_metros": 1.4, "tipo": "PM"},
            {"datetime": "2025-01-01T12:00", "altura_metros": 0.4, "tipo": "BM"},
            {"datetime": "2025-01-01T18:00", "altura_metros": 1.2, "tipo": "PM"},
        ]

        client = _mock(MaresClient(), lambda r: _json_response(previsao))
        result = await client.janelas_navegacao("23190", calado_minimo=1.0)
        assert result["percentual_janela"] == 50.0
        assert result["horas_navegaveis_por_dia"] == 12.0
        await client.close()

    def test_mapeamento_instalacao(self):
        from app.clients.mares import MaresClient
        client = MaresClient.__new__(MaresClient)
        assert client.get_estacao_for_instalacao("Santos")["id"] == "23190"
        assert client.get_estacao_for_instalacao("XXX") is None


# ============================================================================
# AnaClient
# ============================================================================

class TestAnaClient:

    @pytest.mark.asyncio
    async def test_risco_hidrico_alto(self):
        """Risco alto quando nível < calado mínimo."""
        from unittest.mock import patch
        from app.clients.ana import AnaClient

        client = AnaClient()
        client._cache = NoOpCache()

        # Mock consultar_nivel_rio para retornar dados diretamente
        async def mock_nivel(*a, **kw):
            return [{"data": "2025-01-01", "nivel_metros": 10.0, "vazao_m3s": 5000}]

        with patch.object(client, "consultar_nivel_rio", mock_nivel):
            result = await client.calcular_risco_hidrico("14990000", 12.0)

        assert result["classificacao"] == "alto"
        assert result["risco_normalizado"] == 1.0

    @pytest.mark.asyncio
    async def test_risco_hidrico_baixo(self):
        """Risco baixo quando nível >> calado mínimo."""
        from unittest.mock import patch
        from app.clients.ana import AnaClient

        client = AnaClient()
        client._cache = NoOpCache()

        async def mock_nivel(*a, **kw):
            return [{"data": "2025-01-01", "nivel_metros": 30.0, "vazao_m3s": 15000}]

        with patch.object(client, "consultar_nivel_rio", mock_nivel):
            result = await client.calcular_risco_hidrico("14990000", 12.0)

        assert result["classificacao"] == "baixo"
        assert result["risco_normalizado"] < 0.3

    def test_parse_xml_cotas(self):
        """Parseia XML diffgram real da ANA."""
        from app.clients.ana import AnaClient
        import xml.etree.ElementTree as ET

        xml_str = """<DataTable xmlns="http://MRCS/">
            <diffgr:diffgram xmlns:diffgr="urn:schemas-microsoft-com:xml-diffgram-v1">
                <DocumentElement xmlns="">
                    <SerieHistorica>
                        <DataHora>2025-01-01</DataHora>
                        <Cota01>1500</Cota01>
                        <Cota02>1520</Cota02>
                    </SerieHistorica>
                </DocumentElement>
            </diffgr:diffgram>
        </DataTable>"""

        root = ET.fromstring(xml_str)
        result = AnaClient._parse_xml_cotas(root)
        assert len(result) == 2
        assert result[0]["nivel_metros"] == 15.0  # 1500cm → 15.0m
        assert result[1]["nivel_metros"] == 15.2   # 1520cm → 15.2m

    def test_mapeamento_porto(self):
        from app.clients.ana import AnaClient
        client = AnaClient.__new__(AnaClient)
        est = client.get_estacao_for_porto("Manaus")
        assert est["codigo"] == "14990000"
        assert est["rio"] == "Rio Negro"


# ============================================================================
# InpeClient
# ============================================================================

class TestInpeClient:

    @pytest.mark.asyncio
    async def test_risco_baixo(self):
        from app.clients.inpe import InpeClient

        client = _mock(InpeClient(), lambda r: _json_response([]))
        result = await client.calcular_risco_incendio("Santos")
        assert result["classificacao"] == "baixo"
        assert result["focos_detectados"] == 0
        await client.close()

    @pytest.mark.asyncio
    async def test_risco_alto(self):
        from app.clients.inpe import InpeClient

        focos = [{"lat": -23.9 + i * 0.01, "lon": -46.3} for i in range(60)]
        client = _mock(InpeClient(), lambda r: _json_response(focos))
        result = await client.calcular_risco_incendio("Santos")
        assert result["classificacao"] == "alto"
        assert result["focos_detectados"] == 60
        await client.close()

    @pytest.mark.asyncio
    async def test_porto_desconhecido(self):
        from app.clients.inpe import InpeClient
        client = InpeClient()
        client._cache = NoOpCache()
        result = await client.calcular_risco_incendio("XXX")
        assert result["classificacao"] == "sem_dados"

    def test_haversine(self):
        from app.clients.inpe import InpeClient
        dist = InpeClient._haversine(-23.95, -46.33, -23.55, -46.63)
        assert 40 < dist < 80


# ============================================================================
# DeflationService
# ============================================================================

class TestDeflationService:

    @pytest.mark.asyncio
    async def test_deflacionar_serie(self):
        from app.clients.bacen import BacenClient
        from app.services.deflation_service import DeflationService

        ipca = [
            {"data": f"01/{m:02d}/{y}", "valor": "0.50"}
            for y in [2022, 2023] for m in range(1, 13)
        ]

        bacen = _mock(BacenClient(), lambda r: _json_response(ipca))
        svc = DeflationService(bacen=bacen)

        dados = [{"ano": 2022, "receita": 1_000_000}, {"ano": 2023, "receita": 1_100_000}]
        result = await svc.deflacionar_serie(dados, "receita", "ano", ano_base=2023)

        r2023 = next(r for r in result if r["ano"] == 2023)
        r2022 = next(r for r in result if r["ano"] == 2022)
        assert abs(r2023["receita_real"] - 1_100_000) < 1000
        assert r2022["receita_real"] > 1_000_000
        assert r2022["deflator_ipca"] > 1.0
        await bacen.close()

    @pytest.mark.asyncio
    async def test_serie_vazia(self):
        from app.services.deflation_service import DeflationService
        svc = DeflationService.__new__(DeflationService)
        assert await svc.deflacionar_serie([], "x", "ano") == []


# ============================================================================
# AmbientalService
# ============================================================================

class TestAmbientalService:

    @pytest.mark.asyncio
    async def test_porto_maritimo_somente_incendio(self):
        from app.clients.ana import AnaClient
        from app.clients.inpe import InpeClient
        from app.services.ambiental_service import AmbientalService

        focos = [{"lat": -23.9 + i * 0.01, "lon": -46.3} for i in range(10)]
        inpe = _mock(InpeClient(), lambda r: _json_response(focos))
        ana = AnaClient()
        ana._cache = NoOpCache()

        svc = AmbientalService(ana=ana, inpe=inpe)
        result = await svc.indice_risco_ambiental("Santos")

        assert result["valor"] is not None
        assert result["classificacao"] == "baixo"
        assert "composicao" in result
        comp = result["composicao"]
        assert comp["formula"]
        assert len(comp["componentes"]) >= 1
        assert comp["componentes"][0]["fonte"]
        assert comp["componentes"][0]["descricao"]
        await inpe.close()

    @pytest.mark.asyncio
    async def test_porto_fluvial_dois_componentes(self):
        from app.clients.ana import AnaClient
        from app.clients.inpe import InpeClient
        from app.services.ambiental_service import AmbientalService

        ana = _mock(
            AnaClient(),
            lambda r: _json_response([{"Data": "2025-01-01", "Nivel": "15.0"}]),
        )
        focos = [{"lat": -3.1 + i * 0.01, "lon": -60.0} for i in range(25)]
        inpe = _mock(InpeClient(), lambda r: _json_response(focos))

        svc = AmbientalService(ana=ana, inpe=inpe)
        result = await svc.indice_risco_ambiental("Manaus")

        assert result["valor"] is not None
        assert len(result["composicao"]["componentes"]) == 2
        assert result["composicao"]["nota_metodologica"]
        await ana.close()
        await inpe.close()


# ============================================================================
# Deflation Integration (GenericIndicatorService._apply_deflation)
# ============================================================================

class TestDeflationIntegration:

    @pytest.mark.asyncio
    async def test_apply_deflation_adds_real_fields(self):
        """_apply_deflation adiciona campos *_real a indicadores monetários."""
        from unittest.mock import patch, AsyncMock, MagicMock
        from app.services.generic_indicator_service import GenericIndicatorService

        svc = GenericIndicatorService.__new__(GenericIndicatorService)

        results = [
            {"ano": 2022, "icms": 5_000_000, "id_municipio": "3550308"},
            {"ano": 2023, "icms": 5_500_000, "id_municipio": "3550308"},
        ]

        mock_svc = MagicMock()

        async def fake_deflacionar(valores, campo_valor, campo_ano, ano_base=None):
            for v in valores:
                v[f"{campo_valor}_real"] = round(v[campo_valor] * 1.05, 2)
                v["deflator_ipca"] = 1.05
                v["ano_base_deflacao"] = 2023
            return valores

        mock_svc.deflacionar_serie = fake_deflacionar

        with patch("app.services.deflation_service.get_deflation_service", return_value=mock_svc):
            deflated, warnings = await svc._apply_deflation("IND-6.01", results, 2023)

        assert deflated[0]["icms_real"] is not None
        assert deflated[0]["deflator_ipca"] == 1.05
        assert any(w.tipo == "deflacao_aplicada" for w in warnings)

    @pytest.mark.asyncio
    async def test_apply_deflation_no_ano_field(self):
        """Sem campo 'ano', retorna warning e dados não alterados."""
        from app.services.generic_indicator_service import GenericIndicatorService

        svc = GenericIndicatorService.__new__(GenericIndicatorService)
        results = [{"valor": 100, "nome": "teste"}]

        deflated, warnings = await svc._apply_deflation("IND-1.01", results, None)
        assert any(w.tipo == "deflacao_sem_campo_ano" for w in warnings)

    @pytest.mark.asyncio
    async def test_apply_deflation_autodetect_fields(self):
        """Auto-detecta campos monetários quando não há mapeamento explícito."""
        from unittest.mock import patch, MagicMock
        from app.services.generic_indicator_service import GenericIndicatorService

        svc = GenericIndicatorService.__new__(GenericIndicatorService)
        results = [
            {"ano": 2023, "receita_total": 1_000_000, "populacao": 50000},
        ]

        mock_svc = MagicMock()

        async def fake_deflacionar(valores, campo_valor, campo_ano, ano_base=None):
            for v in valores:
                v[f"{campo_valor}_real"] = v[campo_valor]
                v["deflator_ipca"] = 1.0
            return valores

        mock_svc.deflacionar_serie = fake_deflacionar

        # Usa código sem mapeamento explícito para forçar auto-detecção
        with patch("app.services.deflation_service.get_deflation_service", return_value=mock_svc):
            deflated, warnings = await svc._apply_deflation("IND-99.99", results, None)

        # receita_total deve ser detectado; populacao não (não é monetário)
        assert "receita_total_real" in deflated[0]
        assert any(w.tipo == "deflacao_aplicada" for w in warnings)
        assert "receita_total" in [w.campo for w in warnings if w.tipo == "deflacao_aplicada"][0]
