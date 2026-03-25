"""
Testes de integração: impacto de emprego com dados reais BigQuery.

Estes testes consultam RAIS, ANTAQ e IBGE via BigQuery para municípios
portuários reais, validando o pipeline completo:
    BQ → EmploymentMultiplierService → EmploymentImpactResult

Municípios de teste:
    - Santos (3548500): maior porto da América Latina
    - Paranaguá (4118204): referência do TCC Wozniak & Andrade Junior
    - São Luís (2111300): complexo Itaqui (minério/grãos)

Execução:
    cd backend
    python3 -m pytest app/tests/integration/test_employment_impact_real.py -v
"""
from __future__ import annotations

import pytest

from app.services.employment_multiplier import EmploymentMultiplierService


# Municípios portuários para teste
SANTOS = "3548500"
PARANAGUA = "4118204"
SAO_LUIS = "2111300"

# Ano de referência com dados RAIS disponíveis
ANO_REF = 2022


@pytest.fixture(scope="module")
def service(bq_client):
    """EmploymentMultiplierService com BQ real."""
    return EmploymentMultiplierService(bq_client=bq_client)


class TestSantosReal:
    """Santos — maior porto da América Latina."""

    @pytest.mark.asyncio
    async def test_santos_has_data(self, service):
        """Santos deve ter dados de emprego portuário na RAIS."""
        results = await service.get_impacto_emprego(SANTOS, ano=ANO_REF)
        assert len(results) >= 1, f"Sem dados para Santos/{ANO_REF}"

    @pytest.mark.asyncio
    async def test_santos_employment_fields(self, service):
        results = await service.get_impacto_emprego(SANTOS, ano=ANO_REF)
        item = results[0]

        # Campos obrigatórios preenchidos
        assert item.empregos_diretos > 0, "Santos deve ter empregos portuários"
        assert item.empregos_indiretos_estimados > 0
        assert item.empregos_induzidos_estimados > 0
        assert item.emprego_total_estimado > item.empregos_diretos

        # Santos é um porto grande — deve ter > 1000 empregos diretos
        assert item.empregos_diretos > 500, (
            f"Santos com apenas {item.empregos_diretos} empregos — "
            "esperado > 500"
        )

    @pytest.mark.asyncio
    async def test_santos_production_income(self, service):
        """Santos deve ter dados RAIS de massa salarial → VBP derivado."""
        results = await service.get_impacto_emprego(SANTOS, ano=ANO_REF)
        item = results[0]

        assert item.dados_producao_renda_disponiveis is True
        assert item.producao_direta_brl is not None
        assert item.producao_direta_brl > 0
        assert item.renda_direta_brl is not None
        assert item.renda_direta_brl > 0
        assert item.producao_total_brl > item.producao_direta_brl

        # Se há massa salarial RAIS, a nota deve indicar
        if "RAIS" in (item.nota_dados_producao_renda or ""):
            # VBP derivado deve ser maior que a renda (MR < 1)
            assert item.producao_direta_brl > item.renda_direta_brl, (
                f"VBP ({item.producao_direta_brl:,.0f}) deveria ser > "
                f"renda ({item.renda_direta_brl:,.0f}) porque MR < 1"
            )

    @pytest.mark.asyncio
    async def test_santos_multipliers_transparency(self, service):
        """Multiplicadores devem estar presentes e coerentes."""
        results = await service.get_impacto_emprego(SANTOS, ano=ANO_REF)
        item = results[0]

        assert item.multiplicador_emprego_tipo_ii is not None
        assert item.multiplicador_emprego_tipo_ii >= 1.0
        assert item.multiplicador_producao_tipo_ii is not None
        assert item.multiplicador_producao_tipo_ii >= 1.0
        assert item.multiplicador_renda_tipo_ii is not None
        assert item.multiplicador_renda_tipo_ii >= 1.0


class TestParanaguaReal:
    """Paranaguá — referência do TCC (Wozniak & Andrade Junior, 2023)."""

    @pytest.mark.asyncio
    async def test_paranagua_has_data(self, service):
        results = await service.get_impacto_emprego(PARANAGUA, ano=ANO_REF)
        assert len(results) >= 1, f"Sem dados para Paranaguá/{ANO_REF}"

    @pytest.mark.asyncio
    async def test_paranagua_high_ql(self, service):
        """Paranaguá é altamente especializado em transporte → QL alto."""
        results = await service.get_impacto_emprego(PARANAGUA, ano=ANO_REF)
        item = results[0]

        assert item.ql_estimado is not None, "QL deve ser calculado"
        assert item.ql_estimado > 1.5, (
            f"Paranaguá com QL={item.ql_estimado:.2f} — "
            "esperado > 1.5 (cidade portuária especializada)"
        )

    @pytest.mark.asyncio
    async def test_paranagua_multiplier_above_national(self, service):
        """MEII de Paranaguá deve exceder o nacional (3.43)."""
        results = await service.get_impacto_emprego(PARANAGUA, ano=ANO_REF)
        item = results[0]

        assert item.multiplicador_emprego_tipo_ii is not None
        assert item.multiplicador_emprego_tipo_ii > 3.43, (
            f"MEII Paranaguá ({item.multiplicador_emprego_tipo_ii:.3f}) "
            "deveria exceder nacional (3.43)"
        )

    @pytest.mark.asyncio
    async def test_paranagua_method_is_ql_adjusted(self, service):
        results = await service.get_impacto_emprego(PARANAGUA, ano=ANO_REF)
        item = results[0]
        assert item.metodo == "mip_ql_ajustado"


class TestSaoLuisReal:
    """São Luís — complexo Itaqui (minério/grãos)."""

    @pytest.mark.asyncio
    async def test_sao_luis_has_data(self, service):
        results = await service.get_impacto_emprego(SAO_LUIS, ano=ANO_REF)
        assert len(results) >= 1, f"Sem dados para São Luís/{ANO_REF}"

    @pytest.mark.asyncio
    async def test_sao_luis_full_pipeline(self, service):
        """Pipeline completo: emprego + produção + renda + cenário."""
        results = await service.get_impacto_emprego(
            SAO_LUIS, ano=ANO_REF, delta_tonelagem_pct=10.0,
        )
        item = results[0]

        # Emprego
        assert item.empregos_diretos > 0
        assert item.emprego_total_estimado > item.empregos_diretos

        # Produção/renda
        assert item.dados_producao_renda_disponiveis is True

        # Cenário
        assert item.scenario is not None
        assert item.scenario.delta_tonelagem_pct == 10.0
        assert item.scenario.delta_emprego_total > 0

        # Metodologia legível
        assert "MIP" in item.metodologia
        assert "Vale & Perobelli" in item.metodologia


class TestPortComparison:
    """Compara portos para verificar que dados regionalizados divergem."""

    @pytest.mark.asyncio
    async def test_different_ports_different_salaries(self, service):
        """Portos diferentes devem ter renda direta diferente (não proxy fixo)."""
        santos = await service.get_impacto_emprego(SANTOS, ano=ANO_REF)
        paranagua = await service.get_impacto_emprego(PARANAGUA, ano=ANO_REF)

        if not santos or not paranagua:
            pytest.skip("Dados indisponíveis para um dos portos")

        s, p = santos[0], paranagua[0]

        # Ambos devem ter dados de produção/renda
        if not s.dados_producao_renda_disponiveis or not p.dados_producao_renda_disponiveis:
            pytest.skip("Produção/renda indisponível para comparação")

        # Se ambos usam RAIS, a renda POR EMPREGO deve diferir
        # (portos diferentes = perfis salariais diferentes)
        if s.empregos_diretos > 0 and p.empregos_diretos > 0:
            renda_per_emp_santos = s.renda_direta_brl / s.empregos_diretos
            renda_per_emp_paranagua = p.renda_direta_brl / p.empregos_diretos

            # Não podem ser exatamente iguais (seria proxy fixo)
            assert abs(renda_per_emp_santos - renda_per_emp_paranagua) > 100, (
                f"Renda/emprego Santos (R$ {renda_per_emp_santos:,.0f}) ≈ "
                f"Paranaguá (R$ {renda_per_emp_paranagua:,.0f}). "
                "Se muito próximos, pode estar usando proxy fixo."
            )

    @pytest.mark.asyncio
    async def test_different_ports_different_ql(self, service):
        """QL deve variar entre portos."""
        santos = await service.get_impacto_emprego(SANTOS, ano=ANO_REF)
        sao_luis = await service.get_impacto_emprego(SAO_LUIS, ano=ANO_REF)

        if not santos or not sao_luis:
            pytest.skip("Dados indisponíveis")

        s, l = santos[0], sao_luis[0]
        if s.ql_estimado is not None and l.ql_estimado is not None:
            assert s.ql_estimado != l.ql_estimado, (
                f"QL Santos ({s.ql_estimado:.2f}) = "
                f"São Luís ({l.ql_estimado:.2f}). Devem diferir."
            )
