"""Endpoints relacionados a métricas de emprego e multiplicadores."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.services.employment_multiplier import EmploymentMultiplierService

router = APIRouter(prefix="/employment", tags=["Employment"])


@router.get("/multipliers/{id_municipio}")
async def get_multipliers(
    id_municipio: str,
    ano: Optional[int] = Query(default=None, description="Ano de referência"),
    use_causal: bool = Query(
        default=False,
        description="Requer estimativa causal (ainda indisponível)",
    ),
    delta_tonelagem_pct: Optional[float] = Query(
        default=None,
        description="Variação percentual da tonelagem para cenário de impacto simulado",
    ),
) -> dict[str, Any]:
    """Retorna estimativa de impacto de emprego por município."""

    municipality = id_municipio.strip()
    if not municipality:
        raise HTTPException(status_code=400, detail="id_municipio obrigatório")

    service = EmploymentMultiplierService()
    try:
        rows = await service.get_impacto_emprego(
            municipality_id=municipality,
            ano=ano,
            delta_tonelagem_pct=delta_tonelagem_pct,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )

    year = int(ano or datetime.now(timezone.utc).year)
    if not rows:
        return {
            "data": [],
            "municipality_id": municipality,
            "municipality_name": None,
            "year": year,
            "metodologia": "sem_dados",
            "indicador_de_confianca": "baixo",
            "correlacao_ou_proxy": True,
            "metodo": "multiplicador_literatura",
            "fonte": "RAIS + ANTAQ",
            "literature": None,
            "estimate": None,
            "active": None,
            "causal": None,
            "causal_estimate": None,
        }

    impact = rows[0]
    multiplier = service.get_literature_multiplier()
    estimate = service.calculate_indirect_jobs(
        direct_jobs=impact.empregos_diretos,
        multiplier=multiplier,
        municipality_id=impact.municipality_id,
        municipality_name=impact.municipality_name,
        year=impact.ano,
    )
    causal_multiplier = service.build_proxy_causal_multiplier(
        direct_jobs=impact.empregos_diretos,
        participation_local=impact.participacao_emprego_local,
        empregos_por_milhao_toneladas=impact.empregos_por_milhao_toneladas,
        base_multiplier=multiplier,
    )
    causal_estimate = service.build_causal_estimate(
        direct_jobs=impact.empregos_diretos,
        causal=causal_multiplier,
        municipality_id=impact.municipality_id,
        municipality_name=impact.municipality_name,
        year=impact.ano,
    )
    active_estimate = causal_estimate if use_causal else estimate

    response: dict[str, Any] = impact.model_dump()
    response.update(
        {
            "municipality_id": impact.municipality_id,
            "municipality_name": impact.municipality_name,
            "year": impact.ano,
            "correlacao_ou_proxy": impact.correlacao_ou_proxy,
            "metodologia": impact.metodologia,
            "indicador_de_confianca": impact.indicador_de_confianca,
            "metodo": impact.metodo,
            "fonte": impact.fonte,
            "data": [impact.model_dump()],
            "literature": {
                "source": multiplier.source,
                "coefficient": multiplier.coefficient,
                "range_low": multiplier.range_low,
                "range_high": multiplier.range_high,
                "confidence": multiplier.confidence,
                "year_published": multiplier.year_published,
            },
            "causal": {
                "source": "Estimativa causal aproximada (beta) com sinais locais RAIS + ANTAQ",
                "method": causal_multiplier.method,
                "n_obs": causal_multiplier.n_obs,
                "r2": None,
                "coefficient": causal_multiplier.coefficient,
                "p_value": causal_multiplier.p_value,
                "ci_lower": causal_multiplier.ci_lower,
                "ci_upper": causal_multiplier.ci_upper,
                "confidence": causal_multiplier.confidence,
            },
            "estimate": estimate.model_dump(),
            "causal_estimate": causal_estimate.model_dump(),
            "active": active_estimate.model_dump(),
        }
    )

    return response
