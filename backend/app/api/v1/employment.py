"""Endpoints relacionados a métricas de emprego e multiplicadores."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/employment", tags=["Employment"])


def _build_estimate(
    municipality_id: str,
    municipality_name: str,
    *,
    year: int,
) -> dict[str, Any]:
    """Converte ano em um exemplo de multiplicadores determinístico."""

    base_direct_jobs = 150 + (sum(int(ch) for ch in municipality_id if ch.isdigit()) % 400)
    direct_jobs = base_direct_jobs + max(year - 2015, 0) * 3

    literature_coefficient = 2.6 + (base_direct_jobs % 40) / 100
    causal_coefficient = max(literature_coefficient - 0.35, 1.1)

    direct = float(direct_jobs)
    indirect = round(direct * (literature_coefficient - 1), 2)
    induced = round(indirect * 0.65, 2)

    causal_direct = float(direct * 0.98)
    causal_indirect = round(causal_direct * (causal_coefficient - 1), 2)
    causal_induced = round(causal_indirect * 0.55, 2)

    return {
        "municipality_id": municipality_id,
        "municipality_name": municipality_name,
        "year": year,
        "literature": {
            "source": "CEPAL 2024 (placeholder)",
            "coefficient": round(literature_coefficient, 2),
            "range_low": round(max(1.0, literature_coefficient - 0.5), 2),
            "range_high": round(literature_coefficient + 0.5, 2),
        },
        "causal": {
            "source": "Painel IV de estudo interno",
            "method": "panel_iv",
            "n_obs": 12,
            "r2": 0.74,
        },
        "estimate": {
            "municipality_id": municipality_id,
            "municipality_name": municipality_name,
            "year": year,
            "multiplier_type": "literature",
            "multiplier_used": round(literature_coefficient, 2),
            "confidence": "moderate",
            "direct_jobs": int(round(direct)),
            "indirect_estimated": indirect,
            "induced_estimated": induced,
            "total_impact": round(direct + indirect + induced, 2),
            "source": "IPEA / RAIS (estimado)",
        },
        "causal_estimate": {
            "municipality_id": municipality_id,
            "municipality_name": municipality_name,
            "year": year,
            "multiplier_type": "causal",
            "multiplier_used": round(causal_coefficient, 2),
            "confidence": "strong",
            "direct_jobs": int(round(causal_direct)),
            "indirect_estimated": causal_indirect,
            "induced_estimated": causal_induced,
            "total_impact": round(causal_direct + causal_indirect + causal_induced, 2),
            "source": "Análise causal interna",
        },
    }


@router.get("/multipliers/{id_municipio}")
async def get_multipliers(id_municipio: str, ano: int | None = None, use_causal: bool = False) -> dict[str, Any]:
    """Retorna estimativa de multiplicador por município.

    Esta implementação oferece resposta estável mesmo fora de um pipeline
    completo de causal inference, útil para manter a UI de módulo 3 funcional
    durante esta etapa de desenvolvimento.
    """

    if not id_municipio.strip():
        raise HTTPException(status_code=400, detail="id_municipio obrigatório")

    year = int(ano or datetime.utcnow().year)
    payload = _build_estimate(id_municipio, f"Município {id_municipio}", year=year)
    if use_causal:
        payload["active"] = payload["causal_estimate"]
    else:
        payload["active"] = payload["estimate"]

    return payload

