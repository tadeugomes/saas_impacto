"""
Testes de benchmark: multiplicadores MIP vs. TCC Paranaguá.

Dados de referência: Wozniak & Andrade Junior (2023), TCC.
O TCC usou MIP regional completa (52 setores, balanceamento RAS).
Este SaaS usa MIP nacional (12 setores, ajuste via QL).

O objetivo NÃO é reproduzir exatamente os resultados do TCC —
isso só seria possível com a mesma MIP regional. O objetivo é
verificar se os resultados do SaaS estão na mesma ordem de grandeza.

Divergência esperada e suas causas:
  - O TCC desagregou o setor portuário da categoria Transporte,
    obtendo multiplicadores de VBP até 18,1 (muito acima do
    nacional de 3,37). A MIP nacional é agregada (12 setores)
    e o ajuste por QL com cap=2,5 limita a expansão.
  - O balanceamento RAS da MIP regional redistribui os fluxos
    intersetoriais para refletir a estrutura produtiva local.
  - Apesar dessas diferenças, os resultados do SaaS devem estar
    dentro de uma faixa plausível: acima do nacional, mas abaixo
    da MIP regional completa.

Execução:
    pytest app/tests/test_paranagua_benchmark.py -v
"""
from __future__ import annotations

import pytest

from app.services.io_analysis.national_multipliers import (
    TRANSPORT_PRODUCTION,
    TRANSPORT_EMPLOYMENT,
    TRANSPORT_INCOME,
    compute_port_impact,
    adjust_multipliers,
    AdjustmentMethod,
)


# Dados de referência — TCC Paranaguá (Wozniak & Andrade Junior, 2023)
PARANAGUA_DIRECT_JOBS = 9_000
PARANAGUA_VBP_DIRETO = 1_574_000_000.0   # R$ 1,574 bilhão
PARANAGUA_RENDA_DIRETA = 500_000_000.0   # R$ 500 milhões (proxy)
PARANAGUA_PIB = 9_860_000_000.0          # R$ 9,86 bilhões
PARANAGUA_QL = 4.0                        # QL setor Transporte estimado
PARANAGUA_CODE = "4118204"

# Multiplicadores do TCC (MIP regional completa, 52 setores, RAS)
TCC_MULT_VBP_TOTAL = 18.1
TCC_MULT_VAB_TOTAL = 14.5
# Ratio induzido / indireto no TCC: efeito induzido = 5.74, indireto = 10.33
TCC_RATIO_INDUZIDO_INDIRETO = 5.74 / 10.33  # ~0.556


class TestParanaguaBenchmark:
    """Compara output do SaaS com valores de referência do TCC."""

    @pytest.fixture
    def result(self):
        """Resultado do pipeline completo para Paranaguá."""
        return compute_port_impact(
            direct_jobs=PARANAGUA_DIRECT_JOBS,
            direct_output_brl=PARANAGUA_VBP_DIRETO,
            direct_income_brl=PARANAGUA_RENDA_DIRETA,
            ql=PARANAGUA_QL,
            region_code=PARANAGUA_CODE,
        )

    @pytest.fixture
    def regional_mult(self):
        """Multiplicadores regionais ajustados para Paranaguá."""
        return adjust_multipliers(
            ql=PARANAGUA_QL,
            region_code=PARANAGUA_CODE,
            adjustment_method=AdjustmentMethod.CAPPED_LINEAR,
            cap=2.5,
        )

    def test_vbp_total_order_of_magnitude(self, result):
        """VBP total deve estar entre R$ 3B e R$ 10B.

        O TCC reportou VBP total de R$ 1.574B × 18.1 = ~R$ 28.5B
        (com MIP regional desagregada). O SaaS, com MIP nacional
        e cap=2.5, deve produzir valor menor mas acima do nacional
        puro (R$ 1.574B × 3.37 = ~R$ 5.3B).
        """
        vbp_total = result["impact"]["production_brl"]["total"]
        assert vbp_total > 3_000_000_000.0, (
            f"VBP total ({vbp_total/1e9:.1f}B) abaixo do mínimo esperado (3B)"
        )
        assert vbp_total < 10_000_000_000.0, (
            f"VBP total ({vbp_total/1e9:.1f}B) acima do máximo esperado (10B)"
        )

    def test_employment_type_ii_exceeds_national(self, regional_mult):
        """Multiplicador de emprego regional deve exceder o nacional (3.43).

        Com QL=4.0, o QL é cappado em 2.5 (CAPPED_LINEAR), então
        o MEII ajustado deve ser significativamente maior que 3.43.
        """
        assert regional_mult.employment_type_ii > TRANSPORT_EMPLOYMENT.type_ii, (
            f"MEII regional ({regional_mult.employment_type_ii:.3f}) não excede "
            f"nacional ({TRANSPORT_EMPLOYMENT.type_ii:.3f})"
        )

    def test_production_type_ii_exceeds_national(self, regional_mult):
        """Multiplicador de produção regional deve exceder o nacional (3.37)."""
        assert regional_mult.production_type_ii > TRANSPORT_PRODUCTION.total_truncated

    def test_ratio_induced_indirect_in_range(self, result):
        """Ratio induzido/indireto deve ser consistente com MIP 12 setores.

        Nota: o TCC reportou ratio de ~0.556, mas para o setor portuário
        desagregado (52 setores). Na MIP nacional de 12 setores, o setor
        Transporte tem efeito induzido > indireto (MEII-MEI=1.60 vs
        MEI-1=0.83), resultando em ratio nacional ~1.94. Com ajuste por
        QL via factor^0.7 (amortecimento do induzido), o ratio fica em
        torno de 1.3 a 1.6 — divergência estrutural esperada por conta
        da agregação setorial.
        """
        emp = result["impact"]["employment"]
        indirect = emp["indirect"]
        induced = emp["induced"]

        if indirect > 0:
            ratio = induced / indirect
            assert 1.0 <= ratio <= 2.0, (
                f"Ratio induzido/indireto ({ratio:.3f}) fora da faixa [1.0, 2.0] "
                "esperada para MIP nacional 12 setores com QL cappado"
            )

    def test_ql_high_triggers_warning(self, result):
        """QL alto (>3.0) deve gerar nota de alerta no resultado."""
        notes = result.get("notes", "")
        assert "QL alto" in notes, (
            f"Nota sobre QL alto não encontrada. Notes: '{notes}'"
        )

    def test_total_employment_exceeds_direct(self, result):
        """Total de empregos deve ser > diretos × 1 (tem efeitos indiretos)."""
        emp = result["impact"]["employment"]
        assert emp["total"] > emp["direct"]

    def test_income_total_plausible(self, result):
        """Renda total deve ser maior que a direta mas não absurda."""
        inc = result["impact"]["income_brl"]
        assert inc["total"] > inc["direct"]
        # O multiplicador de renda tipo II é ~2.97, com QL alto ~5+
        # Renda total não deve exceder 10× a direta
        assert inc["total"] < inc["direct"] * 10
