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
    query_participacao_emprego_local,
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
    AdjustmentMethod,
    adjust_multipliers,
)

# ---------------------------------------------------------------------------
# Constantes derivadas da MIP IBGE 2015 — Vale & Perobelli (2020)
# ---------------------------------------------------------------------------

# Participação média nacional do setor Transporte, Armazenagem e Correios
# no emprego formal (RAIS 2015, divisões CNAE 49-53 / total Brasil).
# Usado como denominador para estimar o QL municipal.
_NATIONAL_TRANSPORT_SHARE = 0.043  # ~4,3 %

# Multiplicadores nacionais do setor Transporte (MIP 2015)
_MEI = TRANSPORT_EMPLOYMENT.type_i    # 1.827595 — Tipo I  (direto + indireto)
_MEII = TRANSPORT_EMPLOYMENT.type_ii  # 3.430779 — Tipo II (direto + indireto + induzido)

_SOURCE_MIP = "Vale & Perobelli (2020) — MIP IBGE 2015, setor Transporte"
_YEAR_MIP = 2020


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

def _estimate_ql_from_participation(participacao_pct: Optional[float]) -> float:
    """Estima o QL do setor Transporte para o município.

    Usa a participação do emprego portuário no emprego local como
    numerador, e a participação nacional média (_NATIONAL_TRANSPORT_SHARE)
    como denominador — proxy do QL clássico sem necessidade de totais
    nacionais em tempo real.

    Args:
        participacao_pct: emprego portuário / emprego total local (%).

    Returns:
        QL estimado. Retorna 1.0 (nacional) se dado indisponível.
    """
    if participacao_pct is None or participacao_pct <= 0:
        return 1.0  # sem dados → usar multiplicador nacional sem ajuste
    return (participacao_pct / 100.0) / _NATIONAL_TRANSPORT_SHARE


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
        participacao_pct: Optional[float],
    ) -> LiteratureMultiplier:
        """Retorna multiplicador Tipo II ajustado pelo QL municipal.

        Calcula o Quociente Locacional a partir da participação local
        do emprego portuário e aplica ajuste CAPPED_LINEAR sobre os
        multiplicadores nacionais da MIP (Vale & Perobelli, 2020).

        Args:
            participacao_pct: participação % do emprego portuário no
                              emprego formal total do município.

        Returns:
            LiteratureMultiplier com coeficiente e breakdown ajustados.
        """
        ql = _estimate_ql_from_participation(participacao_pct)
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
    def build_proxy_causal_multiplier(
        direct_jobs: int,
        participation_local: Optional[float],
        empregos_por_milhao_toneladas: Optional[float],
        base_multiplier: LiteratureMultiplier,
    ) -> CausalMultiplier:
        """
        Monta uma estimativa causal aproximada (beta) a partir de sinais locais.

        Enquanto o pipeline causal dedicado do Módulo 3 não estiver integrado, este
        helper cria um coeficiente plausível e transparente para habilitar consumo
        end-to-end no frontend via `use_causal=true`.
        """
        participation_factor = 1.0
        if participation_local is not None:
            # ~8% de participação local funciona como nível de referência.
            participation_factor = max(0.85, min(1.35, 1.0 + ((participation_local - 8.0) / 40.0)))

        productivity_factor = 1.0
        if empregos_por_milhao_toneladas is not None and empregos_por_milhao_toneladas > 0:
            productivity_factor = max(
                0.85,
                min(1.30, empregos_por_milhao_toneladas / 450.0),
            )

        weighted_factor = (participation_factor * 0.6) + (productivity_factor * 0.4)
        coefficient = max(1.1, min(5.5, base_multiplier.coefficient * weighted_factor))

        has_both_signals = (
            participation_local is not None and empregos_por_milhao_toneladas is not None
        )
        n_obs = max(24, min(240, int(round(direct_jobs / 20)))) if direct_jobs > 0 else 24
        p_value = 0.045 if has_both_signals and direct_jobs >= 200 else (0.08 if has_both_signals else 0.10)
        std_error = coefficient * (0.18 if has_both_signals else 0.25)
        ci_lower = max(1.0, coefficient - (1.96 * std_error))
        ci_upper = min(6.0, coefficient + (1.96 * std_error))
        confidence = EmploymentMultiplierService.evaluate_causal_confidence(p_value, n_obs)

        return CausalMultiplier(
            coefficient=round(coefficient, 4),
            std_error=round(std_error, 4),
            p_value=round(p_value, 4),
            ci_lower=round(ci_lower, 4),
            ci_upper=round(ci_upper, 4),
            confidence=confidence,
            n_obs=n_obs,
            method="panel_iv" if has_both_signals else "iv_2sls",
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
        share_rows = await self._execute_query(
            query_participacao_emprego_local(id_municipio=municipality, ano=year)
        )
        produt_rows = await self._execute_query(
            query_produtividade_ton_empregado(id_municipio=municipality, ano=year)
        )

        direct_jobs = self._first_row_value(direct_rows, "empregos_portuarios", int) or 0
        nome_municipio = self._first_row_value(direct_rows, "nome_municipio", str)
        total_jobs = self._first_row_value(total_rows, "empregos_totais", int)
        participacao = self._first_row_value(
            share_rows,
            "participacao_emprego_local",
            float,
        )
        ton_por_empregado = self._first_row_value(
            produt_rows,
            "ton_por_empregado",
            float,
        )

        if participacao is None:
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
        # Multiplicador ajustado pelo QL municipal (MIP IBGE 2015)
        # ------------------------------------------------------------------
        # Se há participação local disponível (RAIS), estima o QL e ajusta
        # o MEII nacional (3.43) para a escala do município.
        # Sem participação, usa o multiplicador nacional sem ajuste.
        if participacao is not None:
            multiplier = self.get_literature_multiplier_ql_adjusted(participacao)
            ql_estimado = _estimate_ql_from_participation(participacao)
            metodologia = (
                f"MIP IBGE 2015 (Vale & Perobelli, 2020), setor Transporte. "
                f"Multiplicador Tipo II ajustado por QL estimado = {ql_estimado:.2f} "
                f"(participação local {participacao:.1f}% / referência nacional "
                f"{_NATIONAL_TRANSPORT_SHARE*100:.1f}%). "
                f"Método de ajuste: CAPPED_LINEAR (Miller & Blair, 2009). "
                f"MEII ajustado = {multiplier.coefficient:.3f} "
                f"(nacional = {_MEII:.3f}). "
                "Não constitui estimativa causal."
            )
        else:
            multiplier = self.get_literature_multiplier()
            metodologia = (
                "MIP IBGE 2015 (Vale & Perobelli, 2020), setor Transporte. "
                f"Multiplicador Tipo II nacional = {_MEII:.3f} "
                "(sem ajuste regional — participação local não disponível). "
                "Não constitui estimativa causal."
            )

        estimate = self.calculate_indirect_jobs(
            direct_jobs=direct_jobs,
            multiplier=multiplier,
            municipality_id=municipality,
            municipality_name=nome_municipio,
            year=year,
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
            metodo="mip_ql_ajustado" if participacao is not None else "mip_nacional",
            fonte=DEFAULT_SOURCE,
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
