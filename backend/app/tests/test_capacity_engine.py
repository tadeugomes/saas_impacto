"""Testes unitários para o motor de capacidade (Eq. 1b, mix, BOR/BUR)."""
from __future__ import annotations

import pytest

from app.services.capacity.capacity_engine import (
    allocate_by_mix,
    compute_berth_capacity,
    consolidate_system,
)


def _make_indicator(
    ano=2023,
    id_instalacao="BRSSZ",
    berco="B01",
    perfil_carga="Granel Sólido",
    sentido="Exportação",
    is_container=False,
    n_atracacoes=100,
    mean_ta_h=13.5,
    mean_lm=50000.0,
    ta_plus_a=16.5,
    mean_inop_pre_h=1.0,
    mean_t_op_h=12.0,
    mean_inop_pos_h=0.5,
    mean_produtividade=4166.67,
):
    return {
        "ano": ano,
        "id_instalacao": id_instalacao,
        "berco": berco,
        "perfil_carga": perfil_carga,
        "sentido": sentido,
        "is_container": is_container,
        "n_atracacoes": n_atracacoes,
        "mean_ta_h": mean_ta_h,
        "mean_lm": mean_lm,
        "ta_plus_a": ta_plus_a,
        "mean_inop_pre_h": mean_inop_pre_h,
        "mean_t_op_h": mean_t_op_h,
        "mean_inop_pos_h": mean_inop_pos_h,
        "mean_produtividade": mean_produtividade,
    }


# ---------------------------------------------------------------------------
# Eq. 1b
# ---------------------------------------------------------------------------


class TestComputeBerthCapacity:
    def test_basic_eq1b(self):
        """C = BOR_adm × H_ef × Lm / (Ta + a) com valores conhecidos."""
        ind = _make_indicator(
            mean_lm=50000.0,
            ta_plus_a=16.5,
            n_atracacoes=100,
            mean_ta_h=13.5,
        )
        results = compute_berth_capacity(
            [ind],
            n_bercos=1,
            h_ef=8000,
            clearance_h=3.0,
        )
        assert len(results) == 1
        r = results[0]
        # BOR_adm para Granel Sólido, 1 berço = 0.50
        expected = 0.50 * 8000 * 50000 / 16.5
        assert r["c_cais_bruta"] == pytest.approx(expected, rel=0.01)
        assert r["bor_adm"] == 0.50
        assert r["unidade_capacidade"] == "t/ano"

    def test_container_dual_unit(self):
        """Contêiner deve retornar capacidade em TEU/ano E t/ano."""
        ind = _make_indicator(
            perfil_carga="Carga Conteinerizada",
            is_container=True,
            mean_lm=3000,
            ta_plus_a=15.0,
        )
        results = compute_berth_capacity(
            [ind],
            n_bercos=2,
            h_ef=8000,
            fator_teu=1.55,
        )
        r = results[0]
        # BOR_adm contêiner 2 berços = 0.65
        assert r["bor_adm"] == 0.65
        assert r["unidade_capacidade"] == "TEU/ano"
        assert r["c_cais_tons"] is not None
        assert r["c_cais_tons"] == pytest.approx(r["c_cais_bruta"] * 1.55, rel=0.01)

    def test_bor_obs(self):
        """BOR observado = (N × Ta) / (b × H_ef) × 100."""
        ind = _make_indicator(n_atracacoes=200, mean_ta_h=20.0)
        results = compute_berth_capacity([ind], n_bercos=2, h_ef=8000)
        r = results[0]
        expected_bor = (200 * 20.0) / (2 * 8000) * 100  # = 25%
        assert r["bor_obs_pct"] == pytest.approx(expected_bor, rel=0.01)

    def test_saturation_flag(self):
        """Saturado quando BOR_obs > BOR_adm × 100."""
        # Muitas atracações com tempo longo = alta ocupação
        ind = _make_indicator(n_atracacoes=500, mean_ta_h=20.0)
        results = compute_berth_capacity([ind], n_bercos=1, h_ef=8000)
        r = results[0]
        # BOR_obs = (500 * 20) / (1 * 8000) * 100 = 125% > 50%
        assert r["saturado"] is True

    def test_bor_adm_override(self):
        """Override de BOR_adm deve ser usado no lugar do Quadro 17."""
        ind = _make_indicator()
        results = compute_berth_capacity([ind], bor_adm_override=0.75)
        assert results[0]["bor_adm"] == 0.75

    def test_empty_indicators(self):
        assert compute_berth_capacity([]) == []

    def test_invalid_ta_skipped(self):
        """Grupos com ta_plus_a <= 0 devem ser ignorados."""
        ind = _make_indicator(ta_plus_a=0)
        results = compute_berth_capacity([ind])
        assert results == []

    def test_folga_operacional(self):
        ind = _make_indicator(n_atracacoes=10, mean_lm=1000, ta_plus_a=16.5)
        results = compute_berth_capacity([ind], n_bercos=1, h_ef=8000)
        r = results[0]
        mov = 1000 * 10
        assert r["folga_operacional"] == pytest.approx(r["c_cais_bruta"] - mov, rel=0.01)


# ---------------------------------------------------------------------------
# Alocação por mix
# ---------------------------------------------------------------------------


class TestAllocateByMix:
    def test_single_profile_gets_100pct(self):
        ind = _make_indicator()
        caps = compute_berth_capacity([ind], n_bercos=1, h_ef=8000)
        allocated = allocate_by_mix(caps)
        assert len(allocated) == 1
        assert allocated[0]["fracao_tempo"] == 1.0
        assert allocated[0]["c_alocada"] == allocated[0]["c_cais_bruta"]

    def test_two_profiles_same_berth(self):
        ind1 = _make_indicator(perfil_carga="Granel Sólido", n_atracacoes=100, ta_plus_a=16.5)
        ind2 = _make_indicator(perfil_carga="Granel Líquido", n_atracacoes=100, ta_plus_a=16.5)
        caps = compute_berth_capacity([ind1, ind2], n_bercos=1, h_ef=8000)
        allocated = allocate_by_mix(caps)
        assert len(allocated) == 2
        # Equal time → 50/50 split
        assert allocated[0]["fracao_tempo"] == pytest.approx(0.5, abs=0.01)
        assert allocated[1]["fracao_tempo"] == pytest.approx(0.5, abs=0.01)
        # Sum of allocated capacities should be < sum of brute (they share the berth)
        total_alocada = sum(r["c_alocada"] for r in allocated)
        total_bruta = sum(r["c_cais_bruta"] for r in allocated)
        assert total_alocada < total_bruta

    def test_different_berths_independent(self):
        ind1 = _make_indicator(berco="B01")
        ind2 = _make_indicator(berco="B02")
        caps = compute_berth_capacity([ind1, ind2], n_bercos=1, h_ef=8000)
        allocated = allocate_by_mix(caps)
        # Different berths → each gets 100%
        for r in allocated:
            assert r["fracao_tempo"] == 1.0


# ---------------------------------------------------------------------------
# Consolidação sistêmica
# ---------------------------------------------------------------------------


class TestConsolidateSystem:
    def test_cais_only(self):
        ind = _make_indicator()
        caps = compute_berth_capacity([ind], n_bercos=1, h_ef=8000)
        caps = allocate_by_mix(caps)
        result = consolidate_system(caps)
        assert result["gargalo"] == "cais"
        assert result["c_cais_total"] > 0
        assert result["c_sistema"] == result["c_cais_total"]

    def test_armazenagem_bottleneck(self):
        ind = _make_indicator()
        caps = compute_berth_capacity([ind], n_bercos=1, h_ef=8000)
        caps = allocate_by_mix(caps)
        c_cais = caps[0]["c_alocada"]
        result = consolidate_system(caps, c_armazenagem=c_cais * 0.5)
        assert result["gargalo"] == "armazenagem"
        assert result["c_sistema"] < result["c_cais_total"]

    def test_empty_results(self):
        result = consolidate_system([])
        assert result["gargalo"] == "sem_dados"
        assert result["c_sistema"] == 0
