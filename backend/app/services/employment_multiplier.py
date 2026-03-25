"""
Serviço de impacto de emprego (Módulo 3).

Objetivo:
- Estimar impacto de empregos (indireto + induzido) com base em RAIS e ANTAQ.
- Expor contrato de resposta com campos de negócio.
- Manter campos legados de frontend (`estimate`, `literature` etc).

Metodologia de multiplicadores:
    Os coeficientes derivam da MIP Brasil 2015 (IBGE), 12 setores,
    tabulada por Vale & Perobelli (2020), setor "Transporte, Armazenagem
    e Correios" (divisões CNAE 49-53).

    O multiplicador de emprego Tipo II (MEII = 3.43) é usado como
    referência nacional. Para cada município com dados RAIS disponíveis,
    o MEII é ajustado via Quociente Locacional (QL) conforme Miller &
    Blair (2009, cap. 3), usando a participação local no emprego formal
    como proxy da especialização regional em transporte.

    Decomposição:
        indireto = empregos_diretos × (MEI − 1)
        induzido = empregos_diretos × (MEII − MEI)
        total    = empregos_diretos × MEII

Referências:
    - Miller, R.E. & Blair, P.D. (2009). Input-Output Analysis, 2nd ed.
    - Vale, V.A. & Perobelli, F.S. (2020). Análise de Insumo-Produto no R.
    - Flegg, A.T. et al. (1995). On the appropriate use of location quotients.
      Regional Studies, 29(6), 547-561.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Any

from app.db.bigquery.client import BigQueryClient, BigQueryError, get_bigquery_client
from app.db.bigquery.queries.module3_human_resources import (
    query_empregos_diretos_portuarios,
    query_massa_salarial_portuaria,
    query_produtividade_ton_empregado,
    query_total_municipal_employment,
)
from app.schemas.employment_multiplier import (
    ConfidenceLiteral,
    CausalMultiplier,
    EmploymentShockScenario,
    EmploymentImpactResult,
    IndirectJobsEstimate,
    LiteratureMultiplier,
    MultiplierMetadataItem,
)
from app.services.io_analysis.national_multipliers import (
    TRANSPORT_EMPLOYMENT,
    TRANSPORT_PRODUCTION,
    TRANSPORT_INCOME,
    AdjustmentMethod,
    RegionalMultiplierResult,
    adjust_multipliers,
    compute_location_quotient,
    decompose_production_impact,
    decompose_income_impact,
)

# ---------------------------------------------------------------------------
# Constantes derivadas da MIP IBGE 2015 — Vale & Perobelli (2020)
# ---------------------------------------------------------------------------

# Emprego formal nacional — referência RAIS para cálculo do QL.
# RAIS 2022: setor Transporte, Armazenagem e Correios (CNAE 49-53).
# Valores usados como denominador do QL via compute_location_quotient().
# Atualizáveis quando houver dados RAIS mais recentes.
_NATIONAL_TRANSPORT_EMPLOYMENT = 2_150_000   # ~2,15 M empregos no setor
_NATIONAL_TOTAL_EMPLOYMENT = 49_500_000      # ~49,5 M empregos formais
# Participação implícita: ~4,3 %

# Multiplicadores nacionais do setor Transporte (MIP 2015)
_MEI = TRANSPORT_EMPLOYMENT.type_i    # 1.827595 — Tipo I  (direto + indireto)
_MEII = TRANSPORT_EMPLOYMENT.type_ii  # 3.430779 — Tipo II (direto + indireto + induzido)

_SOURCE_MIP = "Vale & Perobelli (2020) — MIP IBGE 2015, setor Transporte"
_YEAR_MIP = 2020

# VBP por emprego direto — derivado de ME simples (MIP 2015)
# ME_simples = 17.07 empregos / R$ 1.000.000 → R$ 58.582 / emprego direto
_VBP_PER_DIRECT_JOB = 1_000_000.0 / TRANSPORT_EMPLOYMENT.simple  # ~R$ 58.582

# Renda anual média setor Transporte (RAIS 2015, proxy)
# ~R$ 3.000/mês × 13 meses (inclui 13º salário) — fallback quando não
# há massa salarial real no BQ
_RENDA_ANUAL_MEDIA_FALLBACK = 39_000.0

# MR simples = participação da renda direta no VBP direto do setor Transporte
# Se renda direta conhecida: VBP = renda / MR_simples
_MR_SIMPLES = TRANSPORT_INCOME.simple  # 0.443788


# ---------------------------------------------------------------------------
# Tabela de referência de multiplicadores
# ---------------------------------------------------------------------------
# Três cenários derivados da mesma MIP, diferindo pela hipótese de fechamento:
#   port_operations : Tipo II — multiplicador pleno (inclui efeito induzido
#                     via consumo das famílias). Valor padrão.
#   port_type_i     : Tipo I  — multiplicador conservador (apenas efeitos
#                     diretos e indiretos; modelo aberto).
#   port_wozniak    : Tipo II ajustado para contexto portuário brasileiro,
#                     com base no TCC de Wozniak & Andrade Junior (2023),
#                     que obteve multiplicadores acima do nacional em Paranaguá.
#                     Usado como limite superior para municípios com QL > 2.

MULTIPLIER_DEFAULTS: dict = {
    "port_operations": {
        # MEII nacional — estimativa central, modelo fechado
        "coefficient": round(_MEII, 4),                        # 3.4308
        "range_low": 2.5,
        "range_high": 4.5,
        "confidence": "moderate",
        "source": _SOURCE_MIP,
        "year_published": _YEAR_MIP,
        "region": "Brasil",
        "breakdown": {
            "indirect": round(_MEI - 1.0, 4),                 # 0.8276
            "induced": round(_MEII - _MEI, 4),                # 1.6032
        },
    },
    "port_type_i": {
        # MEI nacional — estimativa conservadora, modelo aberto
        "coefficient": round(_MEI, 4),                         # 1.8276
        "range_low": 1.4,
        "range_high": 2.3,
        "confidence": "moderate",
        "source": _SOURCE_MIP + " (Tipo I — sem efeito induzido)",
        "year_published": _YEAR_MIP,
        "region": "Brasil",
        "breakdown": {
            "indirect": round(_MEI - 1.0, 4),                 # 0.8276
            "induced": 0.0,
        },
    },
    "port_wozniak": {
        # Limite superior — contexto portuário especializado (Paranaguá)
        # Wozniak & Andrade Junior (2023) reportaram VBP×18.1 para o setor
        # portuário desagregado; como proxy de emprego, usamos MEII × 1.3.
        "coefficient": round(_MEII * 1.3, 4),                 # ~4.46
        "range_low": round(_MEII, 4),                          # 3.43
        "range_high": 6.0,
        "confidence": "moderate",
        "source": (
            "Wozniak & Andrade Junior (2023), TCC Paranaguá — "
            "ajuste sobre MIP IBGE 2015 (Vale & Perobelli, 2020)"
        ),
        "year_published": 2023,
        "region": "Paranaguá / portos especializados",
        "breakdown": {
            "indirect": round((_MEI - 1.0) * 1.3, 4),
            "induced": round((_MEII - _MEI) * 1.3, 4),
        },
    },
}

DEFAULT_SECTOR = "port_operations"
DEFAULT_SOURCE = "RAIS + ANTAQ + MIP IBGE 2015 (Vale & Perobelli, 2020)"


# ---------------------------------------------------------------------------
# Helpers de QL a partir de dados municipais
# ---------------------------------------------------------------------------

def _compute_ql(
    direct_jobs: int,
    total_jobs: int,
) -> float:
    """Calcula o QL do setor Transporte para o município via RAIS.

    Usa ``compute_location_quotient()`` de ``national_multipliers`` com
    os dados que o service já possui (empregos diretos portuários e
    emprego total municipal, ambos da RAIS), sem chamada adicional ao
    BigQuery.

    Args:
        direct_jobs: empregos portuários (CNAE 49-53) no município.
        total_jobs: emprego formal total no município.

    Returns:
        QL (Simple Location Quotient). Retorna 1.0 se dados insuficientes.
    """
    if direct_jobs <= 0 or total_jobs <= 0:
        return 1.0  # sem dados → usar multiplicador nacional sem ajuste
    return compute_location_quotient(
        employment_sector_region=float(direct_jobs),
        employment_total_region=float(total_jobs),
        employment_sector_national=float(_NATIONAL_TRANSPORT_EMPLOYMENT),
        employment_total_national=float(_NATIONAL_TOTAL_EMPLOYMENT),
    )


class EmploymentMultiplierService:
    """Cálculo de impacto de emprego com base em dados reais de base."""

    def __init__(self, bq_client: Optional[BigQueryClient] = None):
        self.bq_client = bq_client or get_bigquery_client()

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_municipio_id(value: Optional[str]) -> str:
        if not value:
            return ""
        return str(value).strip()

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, bool):
            return None
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_int(value: Any) -> Optional[int]:
        number = EmploymentMultiplierService._to_float(value)
        if number is None:
            return None
        try:
            return int(round(number))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _first_row_value(
        rows: List[dict],
        key: str,
        as_type: type,
    ) -> Any:
        if not rows:
            return None
        raw = rows[0].get(key)
        if as_type is int:
            return EmploymentMultiplierService._to_int(raw)
        if as_type is float:
            return EmploymentMultiplierService._to_float(raw)
        return raw

    async def _execute_query(self, query: str) -> List[dict]:
        try:
            return await self.bq_client.execute_query(query)
        except BigQueryError as exc:
            raise RuntimeError(f"Falha na consulta BigQuery: {exc.message}") from exc

    # ------------------------------------------------------------------
    # Multiplicador de referência (MIP)
    # ------------------------------------------------------------------

    @staticmethod
    def get_literature_multiplier(
        sector: str = DEFAULT_SECTOR,
        region: Optional[str] = None,
    ) -> LiteratureMultiplier:
        """Retorna o multiplicador de referência (MIP IBGE 2015).

        Args:
            sector: chave em MULTIPLIER_DEFAULTS. Padrão: "port_operations"
                    (Tipo II, estimativa central).
            region: ignorado — mantido por compatibilidade. Todos os
                    setores agora referenciam a mesma MIP Brasil 2015.
        """
        data = MULTIPLIER_DEFAULTS.get(sector, MULTIPLIER_DEFAULTS[DEFAULT_SECTOR])
        breakdown = data["breakdown"]
        return LiteratureMultiplier(
            coefficient=float(data["coefficient"]),
            range_low=float(data["range_low"]),
            range_high=float(data["range_high"]),
            confidence=data["confidence"],
            source=data["source"],
            year_published=data["year_published"],
            region=data.get("region", "Brasil"),
            breakdown_indirect=float(breakdown["indirect"]),
            breakdown_induced=float(breakdown["induced"]),
        )

    @staticmethod
    def get_literature_multiplier_ql_adjusted(
        ql: float,
    ) -> LiteratureMultiplier:
        """Retorna multiplicador Tipo II ajustado pelo QL municipal.

        Aplica ajuste CAPPED_LINEAR sobre os multiplicadores nacionais
        da MIP (Vale & Perobelli, 2020) usando o QL já calculado via
        ``compute_location_quotient()``.

        Args:
            ql: Quociente Locacional do setor Transporte no município,
                calculado via ``_compute_ql(direct_jobs, total_jobs)``.

        Returns:
            LiteratureMultiplier com coeficiente e breakdown ajustados.
        """
        regional = adjust_multipliers(
            ql=ql,
            adjustment_method=AdjustmentMethod.CAPPED_LINEAR,
            cap=2.5,
        )
        indirect = regional.employment_type_i - 1.0
        induced = regional.employment_type_ii - regional.employment_type_i

        if ql >= 2.0:
            confidence: ConfidenceLiteral = "strong"
        elif ql >= 0.8:
            confidence = "moderate"
        else:
            confidence = "weak"

        source = (
            f"{_SOURCE_MIP}; ajuste regional via QL={ql:.2f} "
            f"(Miller & Blair, 2009, cap. 3)"
        )

        return LiteratureMultiplier(
            coefficient=round(regional.employment_type_ii, 4),
            range_low=round(max(1.0, regional.employment_type_ii * 0.75), 4),
            range_high=round(regional.employment_type_ii * 1.3, 4),
            confidence=confidence,
            source=source,
            year_published=_YEAR_MIP,
            region="Regional (ajustado por QL)",
            breakdown_indirect=round(indirect, 4),
            breakdown_induced=round(induced, 4),
        )

    @staticmethod
    def calculate_indirect_jobs(
        direct_jobs: int,
        multiplier: LiteratureMultiplier,
        *,
        municipality_id: str = "",
        municipality_name: Optional[str] = None,
        year: Optional[int] = None,
    ) -> IndirectJobsEstimate:
        indirect = direct_jobs * multiplier.breakdown_indirect
        induced = direct_jobs * multiplier.breakdown_induced
        total = direct_jobs + indirect + induced
        return IndirectJobsEstimate(
            municipality_id=municipality_id,
            municipality_name=municipality_name,
            year=year,
            direct_jobs=direct_jobs,
            indirect_estimated=round(indirect, 2),
            induced_estimated=round(induced, 2),
            total_impact=round(total, 2),
            multiplier_used=multiplier.coefficient,
            multiplier_type="literature",
            confidence=multiplier.confidence,
            source=multiplier.source,
        )

    @staticmethod
    def evaluate_causal_confidence(
        p_value: Optional[float], n_obs: Optional[int]
    ) -> ConfidenceLiteral:
        if p_value is not None and p_value < 0.05 and (n_obs is None or n_obs >= 30):
            return "strong"
        if p_value is not None and p_value < 0.10:
            return "moderate"
        return "weak"

    @staticmethod
    def build_causal_estimate(
        direct_jobs: int,
        causal: CausalMultiplier,
        *,
        municipality_id: str = "",
        municipality_name: Optional[str] = None,
        year: Optional[int] = None,
    ) -> IndirectJobsEstimate:
        multiplier = max(1.0, min(6.0, abs(causal.coefficient)))
        indirect = direct_jobs * (multiplier - 1.0) * 0.6
        induced = direct_jobs * (multiplier - 1.0) * 0.4
        total = direct_jobs + indirect + induced
        return IndirectJobsEstimate(
            municipality_id=municipality_id,
            municipality_name=municipality_name,
            year=year,
            direct_jobs=direct_jobs,
            indirect_estimated=round(indirect, 2),
            induced_estimated=round(induced, 2),
            total_impact=round(total, 2),
            multiplier_used=round(multiplier, 2),
            multiplier_type="causal",
            confidence=causal.confidence,
            source=f"Estimativa causal ({causal.method})",
        )

    @staticmethod
    def get_all_multiplier_metadata() -> List[MultiplierMetadataItem]:
        return [
            MultiplierMetadataItem(
                sector=sector,
                coefficient=float(values["coefficient"]),
                range_low=float(values["range_low"]),
                range_high=float(values["range_high"]),
                source=values["source"],
                year_published=int(values["year_published"]),
                region=values.get("region", "Brasil"),
                confidence=values["confidence"],
            )
            for sector, values in MULTIPLIER_DEFAULTS.items()
        ]

    # ------------------------------------------------------------------
    # Impacto em emprego (PR-28)
    # ------------------------------------------------------------------

    async def get_impacto_emprego(
        self,
        municipality_id: str,
        ano: Optional[int] = None,
        delta_tonelagem_pct: Optional[float] = None,
    ) -> List[EmploymentImpactResult]:
        municipality = self._normalize_municipio_id(municipality_id)
        if not municipality:
            return []

        year = int(ano or datetime.now(timezone.utc).year)
        direct_rows = await self._execute_query(
            query_empregos_diretos_portuarios(id_municipio=municipality, ano=year)
        )
        if not direct_rows:
            return []

        total_rows = await self._execute_query(
            query_total_municipal_employment(id_municipio=municipality, ano=year)
        )
        produt_rows = await self._execute_query(
            query_produtividade_ton_empregado(id_municipio=municipality, ano=year)
        )
        massa_rows = await self._execute_query(
            query_massa_salarial_portuaria(id_municipio=municipality, ano=year)
        )

        direct_jobs = self._first_row_value(direct_rows, "empregos_portuarios", int) or 0
        nome_municipio = self._first_row_value(direct_rows, "nome_municipio", str)
        total_jobs = self._first_row_value(total_rows, "empregos_totais", int)
        ton_por_empregado = self._first_row_value(
            produt_rows,
            "ton_por_empregado",
            float,
        )
        massa_salarial_anual = self._first_row_value(
            massa_rows,
            "massa_salarial_anual",
            float,
        )

        # Participação local: calculada dos dados já consultados (sem query extra)
        participacao: Optional[float] = None
        if total_jobs and total_jobs > 0:
            participacao = (direct_jobs * 100.0) / total_jobs

        toneladas_total_antoq = None
        empregos_por_milhao_toneladas = None
        if ton_por_empregado is not None and direct_jobs > 0:
            toneladas_total_antoq = ton_por_empregado * direct_jobs
            if toneladas_total_antoq > 0:
                empregos_por_milhao_toneladas = direct_jobs / (toneladas_total_antoq / 1_000_000)
                empregos_por_milhao_toneladas = round(empregos_por_milhao_toneladas, 4)

        if toneladas_total_antoq is not None:
            toneladas_total_antoq = round(toneladas_total_antoq / 1_000_000, 4)

        if direct_jobs < 0 or (total_jobs is not None and total_jobs < 0):
            return []

        # ------------------------------------------------------------------
        # QL e multiplicador ajustado (MIP IBGE 2015)
        # ------------------------------------------------------------------
        # O QL é calculado via compute_location_quotient() com os dados
        # já disponíveis (direct_jobs, total_jobs) — sem query adicional.
        ql_estimado: Optional[float] = None
        regional: Optional[RegionalMultiplierResult] = None
        nat_share_pct = (_NATIONAL_TRANSPORT_EMPLOYMENT / _NATIONAL_TOTAL_EMPLOYMENT) * 100

        if direct_jobs > 0 and total_jobs and total_jobs > 0:
            ql_estimado = _compute_ql(direct_jobs, total_jobs)
            multiplier = self.get_literature_multiplier_ql_adjusted(ql_estimado)
            regional = adjust_multipliers(
                ql=ql_estimado,
                region_code=municipality,
                adjustment_method=AdjustmentMethod.CAPPED_LINEAR,
                cap=2.5,
                ql_method="simple",
            )
            metodologia = (
                f"MIP IBGE 2015 (Vale & Perobelli, 2020), setor Transporte. "
                f"QL = {ql_estimado:.2f} (compute_location_quotient: "
                f"{direct_jobs:,} port. / {total_jobs:,} total vs. "
                f"nacional {nat_share_pct:.1f}%). "
                f"Método de ajuste: CAPPED_LINEAR (Miller & Blair, 2009). "
                f"MEII ajustado = {multiplier.coefficient:.3f} "
                f"(nacional = {_MEII:.3f}). "
                "Não constitui estimativa causal."
            )
        else:
            multiplier = self.get_literature_multiplier()
            regional = adjust_multipliers(
                ql=1.0,
                region_code=municipality,
                adjustment_method=AdjustmentMethod.CAPPED_LINEAR,
                cap=2.5,
                ql_method="simple",
            )
            metodologia = (
                "MIP IBGE 2015 (Vale & Perobelli, 2020), setor Transporte. "
                f"Multiplicador Tipo II nacional = {_MEII:.3f} "
                "(sem ajuste regional — emprego total municipal não disponível). "
                "Não constitui estimativa causal."
            )

        estimate = self.calculate_indirect_jobs(
            direct_jobs=direct_jobs,
            multiplier=multiplier,
            municipality_id=municipality,
            municipality_name=nome_municipio,
            year=year,
        )

        # ------------------------------------------------------------------
        # Impacto econômico — produção (VBP) e renda
        # ------------------------------------------------------------------
        # Prioridade: dados reais RAIS (massa salarial) → proxy MIP.
        # - Renda direta: massa_salarial_anual do BQ (RAIS) ou fallback.
        # - VBP direto: renda / MR_simples (da MIP) ou fallback.
        prod_result = None
        income_result = None
        dados_producao_renda = False
        nota_producao_renda: Optional[str] = None

        if direct_jobs > 0:
            # --- Renda direta ---
            renda_source = "proxy"
            if massa_salarial_anual is not None and massa_salarial_anual > 0:
                renda_direta = massa_salarial_anual
                renda_source = "RAIS"
            else:
                renda_direta = direct_jobs * _RENDA_ANUAL_MEDIA_FALLBACK
                renda_source = "proxy"

            # --- VBP direto ---
            # Derivado da renda via MR simples (MIP 2015):
            # MR = renda_direta / VBP_direto → VBP = renda / MR
            # Quando renda vem da RAIS, o VBP reflete o perfil real do município.
            # Quando é proxy, usa a constante nacional como fallback.
            vbp_source = "proxy"
            if renda_source == "RAIS":
                vbp_direto = renda_direta / _MR_SIMPLES
                vbp_source = "derivado RAIS/MIP"
            else:
                vbp_direto = direct_jobs * _VBP_PER_DIRECT_JOB
                vbp_source = "proxy"

            prod_result = decompose_production_impact(vbp_direto, regional)
            income_result = decompose_income_impact(renda_direta, regional)

            dados_producao_renda = True
            if renda_source == "RAIS":
                nota_producao_renda = (
                    f"Renda direta: massa salarial RAIS ({municipality}/{year}) = "
                    f"R$ {renda_direta:,.0f}. "
                    f"VBP direto derivado via MR simples (MIP 2015): "
                    f"R$ {renda_direta:,.0f} / {_MR_SIMPLES:.4f} = R$ {vbp_direto:,.0f}. "
                    "Dados regionalizados."
                )
            else:
                nota_producao_renda = (
                    "VBP e renda estimados via proxy MIP nacional "
                    f"(VBP/emp = R$ {_VBP_PER_DIRECT_JOB:,.0f}, "
                    f"renda/emp = R$ {_RENDA_ANUAL_MEDIA_FALLBACK:,.0f}/ano). "
                    "Valores aproximados — massa salarial RAIS não disponível "
                    "para este município/ano."
                )
        else:
            nota_producao_renda = (
                "Dados de VBP/renda não calculados: sem empregos diretos registrados."
            )

        impact = EmploymentImpactResult(
            municipality_id=municipality,
            municipality_name=nome_municipio,
            ano=year,
            empregos_diretos=direct_jobs,
            empregos_totais=total_jobs,
            participacao_emprego_local=round(participacao, 4) if participacao is not None else None,
            tonelagem_antaq_milhoes=toneladas_total_antoq,
            empregos_por_milhao_toneladas=empregos_por_milhao_toneladas,
            empregos_indiretos_estimados=estimate.indirect_estimated,
            empregos_induzidos_estimados=estimate.induced_estimated,
            emprego_total_estimado=estimate.total_impact,
            metodologia=metodologia,
            indicador_de_confianca=(
                "forte" if multiplier.confidence == "strong"
                else "moderado" if multiplier.confidence == "moderate"
                else "baixo"
            ),
            correlacao_ou_proxy=True,
            metodo="mip_ql_ajustado" if ql_estimado is not None else "mip_nacional",
            fonte=DEFAULT_SOURCE,
            # Produção (VBP)
            producao_direta_brl=round(prod_result.direct, 2) if prod_result else None,
            producao_indireta_brl=round(prod_result.indirect, 2) if prod_result else None,
            producao_induzida_brl=round(prod_result.induced, 2) if prod_result else None,
            producao_total_brl=round(prod_result.total, 2) if prod_result else None,
            # Renda
            renda_direta_brl=round(income_result.direct, 2) if income_result else None,
            renda_indireta_brl=round(income_result.indirect, 2) if income_result else None,
            renda_induzida_brl=round(income_result.induced, 2) if income_result else None,
            renda_total_brl=round(income_result.total, 2) if income_result else None,
            # Multiplicadores / transparência
            multiplicador_emprego_tipo_ii=round(regional.employment_type_ii, 4),
            multiplicador_producao_tipo_ii=round(regional.production_type_ii, 4),
            multiplicador_renda_tipo_ii=round(regional.income_type_ii, 4),
            ql_estimado=round(ql_estimado, 4) if ql_estimado is not None else None,
            dados_producao_renda_disponiveis=dados_producao_renda,
            nota_dados_producao_renda=nota_producao_renda,
        )

        if delta_tonelagem_pct is not None:
            shock_ratio = delta_tonelagem_pct / 100.0
            impact.scenario = EmploymentShockScenario(
                delta_tonelagem_pct=delta_tonelagem_pct,
                delta_empregos_diretos=round(estimate.direct_jobs * shock_ratio, 2),
                delta_empregos_indiretos=round(estimate.indirect_estimated * shock_ratio, 2),
                delta_empregos_induzidos=round(estimate.induced_estimated * shock_ratio, 2),
                delta_emprego_total=round(estimate.total_impact * shock_ratio, 2),
            )

        return [impact]
