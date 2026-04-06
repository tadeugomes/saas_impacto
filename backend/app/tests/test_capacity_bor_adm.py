"""Testes unitários para BOR_adm (Quadro 17) e constantes de capacidade."""
from __future__ import annotations

import pytest

from app.services.capacity.constants import (
    DEFAULT_CLEARANCE_H,
    DEFAULT_FATOR_TEU,
    DEFAULT_H_EF,
    H_CAL,
    PERFIL_CARGA_GERAL,
    PERFIL_CONTEINER,
    PERFIL_GRANEL_LIQUIDO,
    PERFIL_GRANEL_SOLIDO,
    PERFIL_RORO,
    normalizar_perfil,
)
from app.services.capacity.bor_adm_table import (
    BOR_ADM_FALLBACK,
    get_bor_adm,
    listar_quadro_17,
)


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------


class TestConstants:
    def test_h_cal(self):
        assert H_CAL == 8760

    def test_default_h_ef(self):
        assert DEFAULT_H_EF == 8000.0

    def test_default_clearance(self):
        assert DEFAULT_CLEARANCE_H == 3.0

    def test_default_fator_teu(self):
        assert DEFAULT_FATOR_TEU == 1.55


# ---------------------------------------------------------------------------
# Normalização de perfil ANTAQ
# ---------------------------------------------------------------------------


class TestNormalizarPerfil:
    @pytest.mark.parametrize(
        "antaq_str, expected",
        [
            ("Granel Sólido", PERFIL_GRANEL_SOLIDO),
            ("GRANEL SÓLIDO", PERFIL_GRANEL_SOLIDO),
            ("Granel Solido", PERFIL_GRANEL_SOLIDO),
            ("Granel Líquido e Gasoso", PERFIL_GRANEL_LIQUIDO),
            ("Granel Líquido", PERFIL_GRANEL_LIQUIDO),
            ("Carga Geral", PERFIL_CARGA_GERAL),
            ("Carga Conteinerizada", PERFIL_CONTEINER),
            ("Container", PERFIL_CONTEINER),
            ("Ro-Ro", PERFIL_RORO),
            ("Veículos", PERFIL_RORO),
        ],
    )
    def test_mapeamentos_conhecidos(self, antaq_str, expected):
        assert normalizar_perfil(antaq_str) == expected

    def test_perfil_desconhecido_retorna_upper(self):
        assert normalizar_perfil("tipo exótico") == "TIPO EXÓTICO"


# ---------------------------------------------------------------------------
# Quadro 17 — BOR admissível
# ---------------------------------------------------------------------------


class TestGetBorAdm:
    """Testa todas as entradas do Quadro 17 UNCTAD."""

    # Granel Sólido
    def test_granel_solido_1_berco(self):
        assert get_bor_adm("Granel Sólido", 1) == 0.50

    def test_granel_solido_2_bercos(self):
        assert get_bor_adm("Granel Sólido", 2) == 0.65

    def test_granel_solido_3_bercos(self):
        assert get_bor_adm("Granel Sólido", 3) == 0.65

    def test_granel_solido_5_bercos(self):
        assert get_bor_adm("Granel Sólido", 5) == 0.65

    # Granel Líquido
    def test_granel_liquido_1_berco(self):
        assert get_bor_adm("Granel Líquido", 1) == 0.55

    def test_granel_liquido_2_bercos(self):
        assert get_bor_adm("Granel Líquido", 2) == 0.60

    def test_granel_liquido_4_bercos(self):
        assert get_bor_adm("Granel Líquido", 4) == 0.60

    # Carga Geral
    def test_carga_geral_1_berco(self):
        assert get_bor_adm("Carga Geral", 1) == 0.45

    def test_carga_geral_3_bercos(self):
        assert get_bor_adm("Carga Geral", 3) == 0.60

    def test_carga_geral_6_bercos(self):
        assert get_bor_adm("Carga Geral", 6) == 0.60

    # Contêiner
    def test_conteiner_1_berco(self):
        assert get_bor_adm("Carga Conteinerizada", 1, is_container=True) == 0.50

    def test_conteiner_2_bercos(self):
        assert get_bor_adm("qualquer", 2, is_container=True) == 0.65

    def test_conteiner_3_bercos(self):
        assert get_bor_adm("qualquer", 3, is_container=True) == 0.65

    def test_conteiner_4_bercos(self):
        assert get_bor_adm("qualquer", 4, is_container=True) == 0.70

    def test_conteiner_10_bercos(self):
        assert get_bor_adm("qualquer", 10, is_container=True) == 0.70

    # Ro-Ro
    def test_roro_1_berco(self):
        assert get_bor_adm("Ro-Ro", 1) == 0.55

    def test_roro_3_bercos(self):
        assert get_bor_adm("Ro-Ro", 3) == 0.55

    def test_roro_5_bercos(self):
        assert get_bor_adm("Ro-Ro", 5) == 0.55

    # Fallback
    def test_perfil_desconhecido_usa_fallback(self):
        assert get_bor_adm("Tipo Desconhecido", 2) == BOR_ADM_FALLBACK

    def test_fallback_valor(self):
        assert BOR_ADM_FALLBACK == 0.80

    # Override
    def test_override_ignora_quadro17(self):
        assert get_bor_adm("Granel Sólido", 1, override=0.75) == 0.75

    def test_override_none_usa_quadro17(self):
        assert get_bor_adm("Granel Sólido", 1, override=None) == 0.50

    # Edge cases
    def test_zero_bercos_usa_faixa_1(self):
        assert get_bor_adm("Granel Sólido", 0) == 0.50

    def test_um_berco_negativo_usa_faixa_1(self):
        assert get_bor_adm("Granel Sólido", -1) == 0.50


# ---------------------------------------------------------------------------
# Listar Quadro 17
# ---------------------------------------------------------------------------


class TestListarQuadro17:
    def test_retorna_lista_nao_vazia(self):
        rows = listar_quadro_17()
        assert len(rows) > 0

    def test_cada_row_tem_campos_esperados(self):
        rows = listar_quadro_17()
        for row in rows:
            assert "perfil" in row
            assert "faixa_bercos" in row
            assert "n_bercos_min" in row
            assert "bor_adm" in row

    def test_total_entradas(self):
        # 5 perfis × 3 faixas = 15 entradas
        rows = listar_quadro_17()
        assert len(rows) == 15

    def test_bor_adm_entre_0_e_1(self):
        for row in listar_quadro_17():
            assert 0 < row["bor_adm"] <= 1.0
