"""
Serviço de impacto de emprego (Módulo 3).

Objetivo:
- Estimar impacto de empregos (indireto + induzido) com base em RAIS e ANTAQ.
- Expor contrato de resposta com campos de negócio.
- Manter campos legados de frontend (`estimate`, `literature` etc).
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


MULTIPLIER_DEFAULTS: dict[str, dict] = {
    "port_operations": {
        "coefficient": 2.5,
        "range_low": 2.0,
        "range_high": 4.0,
        "confidence": "moderate",
        "source": "UNCTAD - Port Management Series, Vol. 7 (2023)",
        "year_published": 2023,
        "region": "Brasil",
        "breakdown": {"indirect": 1.2, "induced": 0.8},
    },
    "port_logistics": {
        "coefficient": 3.0,
        "range_low": 2.5,
        "range_high": 5.0,
        "confidence": "moderate",
        "source": "ECLAC Maritime Transport Review (2022)",
        "year_published": 2022,
        "region": "América Latina",
        "breakdown": {"indirect": 1.5, "induced": 1.0},
    },
    "port_brazil_minfra": {
        "coefficient": 2.8,
        "range_low": 2.2,
        "range_high": 3.5,
        "confidence": "moderate",
        "source": "Ministério da Infraestrutura - Estudo de Impacto Econômico dos Portos (2020)",
        "year_published": 2020,
        "region": "Brasil",
        "breakdown": {"indirect": 1.3, "induced": 0.9},
    },
}

DEFAULT_SECTOR = "port_operations"
DEFAULT_SOURCE = "RAIS + ANTAQ (proxy de evidência de associação)"


class EmploymentMultiplierService:
    """Cálculo de impacto de emprego com base em dados reais de base."""

    def __init__(self, bq_client: Optional[BigQueryClient] = None):
        self.bq_client = bq_client or get_bigquery_client()

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_municipio_id(value: str | None) -> str:
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
    # Multiplicador literário (legado)
    # ------------------------------------------------------------------

    @staticmethod
    def get_literature_multiplier(
        sector: str = DEFAULT_SECTOR, region: Optional[str] = None
    ) -> LiteratureMultiplier:
        data = MULTIPLIER_DEFAULTS.get(sector, MULTIPLIER_DEFAULTS[DEFAULT_SECTOR])
        if region and region.lower() == "brasil":
            data = MULTIPLIER_DEFAULTS.get("port_brazil_minfra", data)
        breakdown = data["breakdown"]
        return LiteratureMultiplier(
            coefficient=float(data["coefficient"]),
            range_low=float(data["range_low"]),
            range_high=float(data["range_high"]),
            confidence=data["confidence"],
            source=data["source"],
            year_published=data["year_published"],
            region=data.get("region", "Global"),
            breakdown_indirect=float(breakdown["indirect"]),
            breakdown_induced=float(breakdown["induced"]),
        )

    @staticmethod
    def calculate_indirect_jobs(
        direct_jobs: int, multiplier: LiteratureMultiplier, *,
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
        direct_jobs: int, causal: CausalMultiplier, *,
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
    def get_all_multiplier_metadata() -> list[MultiplierMetadataItem]:
        return [
            MultiplierMetadataItem(
                sector=sector,
                coefficient=float(values["coefficient"]),
                range_low=float(values["range_low"]),
                range_high=float(values["range_high"]),
                source=values["source"],
                year_published=int(values["year_published"]),
                region=values.get("region", "Global"),
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
    ) -> list[EmploymentImpactResult]:
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

        multiplier = self.get_literature_multiplier()
        legacy_estimate = self.calculate_indirect_jobs(
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
            empregos_indiretos_estimados=legacy_estimate.indirect_estimated,
            empregos_induzidos_estimados=legacy_estimate.induced_estimated,
            emprego_total_estimado=legacy_estimate.total_impact,
            metodologia=(
                "Proxy por multiplicador de literatura aplicado ao volume de empregos diretos "
                "e participação setorial; não constitui estimativa causal."
            ),
            indicador_de_confianca=(
                "moderado" if multiplier.confidence == "moderate"
                else "forte" if multiplier.confidence == "strong" else "baixo"
            ),
            correlacao_ou_proxy=True,
            metodo="multiplicador_literatura",
            fonte=DEFAULT_SOURCE,
        )

        if delta_tonelagem_pct is not None:
            shock_ratio = delta_tonelagem_pct / 100.0
            impact.scenario = EmploymentShockScenario(
                delta_tonelagem_pct=delta_tonelagem_pct,
                delta_empregos_diretos=round(legacy_estimate.direct_jobs * shock_ratio, 2),
                delta_empregos_indiretos=round(legacy_estimate.indirect_estimated * shock_ratio, 2),
                delta_empregos_induzidos=round(legacy_estimate.induced_estimated * shock_ratio, 2),
                delta_emprego_total=round(legacy_estimate.total_impact * shock_ratio, 2),
            )

        return [impact]
