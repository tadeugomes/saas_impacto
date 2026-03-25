"""
Testes para src/io_analysis/national_multipliers.py

Execucao:
    pytest tests/test_national_multipliers.py -v
"""

import pytest
import numpy as np

from app.services.io_analysis.national_multipliers import (
    TRANSPORT_PRODUCTION,
    TRANSPORT_EMPLOYMENT,
    TRANSPORT_INCOME,
    NATIONAL_PRODUCTION_ALL_SECTORS,
    compute_location_quotient,
    QLMethod,
    AdjustmentMethod,
    adjust_multipliers,
    decompose_employment_impact,
    decompose_production_impact,
    decompose_income_impact,
    compute_port_impact,
    _compute_adjustment_factor,
)


# -------------------------------------------------------------------
# Constantes nacionais: sanity checks
# -------------------------------------------------------------------

class TestNationalConstants:
    """Verifica consistencia dos multiplicadores nacionais."""

    def test_production_type_i_greater_than_one(self):
        """Todo multiplicador de producao tipo I deve ser > 1."""
        assert TRANSPORT_PRODUCTION.simple > 1.0

    def test_production_type_ii_greater_than_type_i(self):
        """Tipo II >= tipo I (induzido nao e negativo)."""
        assert TRANSPORT_PRODUCTION.total_truncated >= TRANSPORT_PRODUCTION.simple

    def test_employment_type_i_greater_than_one(self):
        assert TRANSPORT_EMPLOYMENT.type_i > 1.0

    def test_employment_type_ii_greater_than_type_i(self):
        assert TRANSPORT_EMPLOYMENT.type_ii >= TRANSPORT_EMPLOYMENT.type_i

    def test_income_type_i_greater_than_one(self):
        assert TRANSPORT_INCOME.type_i > 1.0

    def test_income_type_ii_greater_than_type_i(self):
        assert TRANSPORT_INCOME.type_ii >= TRANSPORT_INCOME.type_i

    def test_all_12_sectors_present(self):
        """Tabelas completas devem ter 12 setores."""
        assert len(NATIONAL_PRODUCTION_ALL_SECTORS) == 12

    def test_transport_values_match(self):
        """Valores de Transp nas tabelas completas devem bater."""
        mp, mpt, mptt = NATIONAL_PRODUCTION_ALL_SECTORS["Transp"]
        assert mp == pytest.approx(TRANSPORT_PRODUCTION.simple, rel=1e-4)
        assert mptt == pytest.approx(TRANSPORT_PRODUCTION.total_truncated, rel=1e-4)


# -------------------------------------------------------------------
# Quociente Locacional
# -------------------------------------------------------------------

class TestLocationQuotient:

    def test_ql_equal_distribution(self):
        """Se distribuicao regional = nacional, QL = 1."""
        ql = compute_location_quotient(100, 1000, 10000, 100000)
        assert ql == pytest.approx(1.0)

    def test_ql_concentrated(self):
        """Regiao com mais que a media nacional: QL > 1."""
        ql = compute_location_quotient(200, 1000, 10000, 100000)
        assert ql > 1.0
        assert ql == pytest.approx(2.0)

    def test_ql_underrepresented(self):
        """Regiao com menos que a media nacional: QL < 1."""
        ql = compute_location_quotient(50, 1000, 10000, 100000)
        assert ql < 1.0
        assert ql == pytest.approx(0.5)

    def test_ql_zero_sector(self):
        """Setor ausente na regiao: QL = 0."""
        ql = compute_location_quotient(0, 1000, 10000, 100000)
        assert ql == 0.0

    def test_ql_invalid_total_raises(self):
        with pytest.raises(ValueError):
            compute_location_quotient(100, 0, 10000, 100000)

    def test_flq_smaller_than_slq(self):
        """FLQ deve ser <= SLQ para regioes pequenas."""
        slq = compute_location_quotient(
            100, 1000, 10000, 100000, method=QLMethod.SIMPLE
        )
        flq = compute_location_quotient(
            100, 1000, 10000, 100000, method=QLMethod.FLQ
        )
        # Para regiao que e 1% do pais, FLQ < SLQ
        assert flq <= slq

    def test_flq_converges_for_large_regions(self):
        """Para regioes grandes, FLQ se aproxima do SLQ."""
        slq = compute_location_quotient(
            5000, 50000, 10000, 100000, method=QLMethod.SIMPLE
        )
        flq = compute_location_quotient(
            5000, 50000, 10000, 100000, method=QLMethod.FLQ
        )
        assert abs(flq - slq) < 0.3 * slq


# -------------------------------------------------------------------
# Fator de ajuste
# -------------------------------------------------------------------

class TestAdjustmentFactor:

    def test_linear_caps_at_one(self):
        """LINEAR nunca excede 1.0."""
        f = _compute_adjustment_factor(3.0, AdjustmentMethod.LINEAR)
        assert f == 1.0

    def test_linear_passes_below_one(self):
        f = _compute_adjustment_factor(0.6, AdjustmentMethod.LINEAR)
        assert f == pytest.approx(0.6)

    def test_capped_respects_cap(self):
        f = _compute_adjustment_factor(5.0, AdjustmentMethod.CAPPED_LINEAR, cap=2.5)
        assert f == 2.5

    def test_capped_passes_ql(self):
        f = _compute_adjustment_factor(1.8, AdjustmentMethod.CAPPED_LINEAR, cap=2.5)
        assert f == pytest.approx(1.8)

    def test_damped_sublinear(self):
        """DAMPED cresce mais devagar que LINEAR para QL > 1."""
        f_damped = _compute_adjustment_factor(4.0, AdjustmentMethod.DAMPED)
        assert f_damped < 4.0
        assert f_damped > 1.0

    def test_zero_ql_returns_zero(self):
        f = _compute_adjustment_factor(0.0, AdjustmentMethod.LINEAR)
        assert f == 0.0


# -------------------------------------------------------------------
# Ajuste de multiplicadores
# -------------------------------------------------------------------

class TestAdjustMultipliers:

    def test_ql_one_returns_national(self):
        """QL=1 deve retornar os multiplicadores nacionais."""
        result = adjust_multipliers(ql=1.0, region_code="0000000")
        assert result.production_type_i == pytest.approx(
            TRANSPORT_PRODUCTION.simple, rel=1e-3
        )
        assert result.employment_type_i == pytest.approx(
            TRANSPORT_EMPLOYMENT.type_i, rel=1e-3
        )

    def test_ql_below_one_reduces(self):
        """QL < 1 reduz multiplicadores."""
        result = adjust_multipliers(ql=0.5, region_code="TEST")
        assert result.production_type_i < TRANSPORT_PRODUCTION.simple
        assert result.employment_type_i < TRANSPORT_EMPLOYMENT.type_i

    def test_ql_above_one_increases(self):
        """QL > 1 com CAPPED_LINEAR aumenta multiplicadores."""
        result = adjust_multipliers(
            ql=2.0,
            region_code="TEST",
            adjustment_method=AdjustmentMethod.CAPPED_LINEAR,
        )
        assert result.production_type_i > TRANSPORT_PRODUCTION.simple
        assert result.employment_type_i > TRANSPORT_EMPLOYMENT.type_i

    def test_multiplier_never_below_one(self):
        """Nenhum multiplicador tipo I fica abaixo de 1."""
        result = adjust_multipliers(ql=0.1, region_code="TEST")
        assert result.production_type_i >= 1.0
        assert result.employment_type_i >= 1.0
        assert result.income_type_i >= 1.0

    def test_type_ii_geq_type_i(self):
        """Tipo II sempre >= tipo I."""
        for ql in [0.3, 0.7, 1.0, 1.5, 2.5]:
            result = adjust_multipliers(ql=ql)
            assert result.production_type_ii >= result.production_type_i
            assert result.employment_type_ii >= result.employment_type_i
            assert result.income_type_ii >= result.income_type_i

    def test_notes_low_ql(self):
        result = adjust_multipliers(ql=0.3, region_code="TEST")
        assert "QL baixo" in result.notes

    def test_notes_high_ql(self):
        result = adjust_multipliers(ql=4.0, region_code="TEST")
        assert "QL alto" in result.notes


# -------------------------------------------------------------------
# Decomposicao de impacto
# -------------------------------------------------------------------

class TestDecomposition:

    @pytest.fixture
    def mult_result(self):
        return adjust_multipliers(ql=1.2, region_code="TEST")

    def test_employment_total_consistent(self, mult_result):
        """direto + indireto + induzido = direto * tipo_II."""
        impact = decompose_employment_impact(1000, mult_result)
        expected_total = 1000 * mult_result.employment_type_ii
        assert impact.total == pytest.approx(expected_total, rel=1e-3)

    def test_production_total_consistent(self, mult_result):
        impact = decompose_production_impact(1_000_000, mult_result)
        expected_total = 1_000_000 * mult_result.production_type_ii
        assert impact.total == pytest.approx(expected_total, rel=1e-3)

    def test_income_total_consistent(self, mult_result):
        impact = decompose_income_impact(500_000, mult_result)
        expected_total = 500_000 * mult_result.income_type_ii
        assert impact.total == pytest.approx(expected_total, rel=1e-3)

    def test_all_components_positive(self, mult_result):
        impact = decompose_employment_impact(100, mult_result)
        assert impact.direct > 0
        assert impact.indirect >= 0
        assert impact.induced >= 0


# -------------------------------------------------------------------
# Pipeline completo
# -------------------------------------------------------------------

class TestComputePortImpact:

    def test_returns_all_keys(self):
        result = compute_port_impact(
            direct_jobs=500,
            direct_output_brl=10_000_000,
            direct_income_brl=3_000_000,
            ql=1.5,
            region_code="2111300",
        )
        assert "multipliers" in result
        assert "impact" in result
        assert "methodology" in result
        assert "employment" in result["impact"]
        assert "production_brl" in result["impact"]
        assert "income_brl" in result["impact"]

    def test_paranagua_high_ql(self):
        """Paranagua tem QL alto no setor Transporte.
        O TCC reportou multiplicador VBP total de 18.1 para o
        setor portuario desagregado. Com QL=2.5 (cap), nosso
        ajuste simplificado nao vai chegar a 18.1 (que requer
        MIP regional completa com RAS), mas deve estar acima
        do nacional.
        """
        result = compute_port_impact(
            direct_jobs=9000,
            direct_output_brl=1_574_000_000,
            direct_income_brl=500_000_000,
            ql=4.0,  # Transportes em Paranagua
            region_code="4118204",
        )
        prod_ii = result["multipliers"]["production"]["type_ii"]
        # Deve exceder o nacional (3.37)
        assert prod_ii > TRANSPORT_PRODUCTION.total_truncated

    def test_small_municipality_low_ql(self):
        """Municipio pequeno sem atividade portuaria."""
        result = compute_port_impact(
            direct_jobs=50,
            direct_output_brl=1_000_000,
            direct_income_brl=300_000,
            ql=0.3,
            region_code="0000001",
        )
        emp_ii = result["multipliers"]["employment"]["type_ii"]
        # Deve ser menor que o nacional
        assert emp_ii < TRANSPORT_EMPLOYMENT.type_ii
        # Mas nunca abaixo de 1.0
        assert emp_ii >= 1.0
