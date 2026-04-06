"""
Projeção de saturação e análise de tendência de capacidade (Passos 9-10).

Projeta o ano em que a demanda observada ultrapassará a capacidade do cais,
usando regressão linear sobre a movimentação histórica.

Referências:
- roteiro_capacidades_portuarias_v12.md, Passos 9-10
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple


def _linear_regression(
    xs: List[float],
    ys: List[float],
) -> Tuple[float, float]:
    """Regressão linear simples: y = a + b*x.

    Returns
    -------
    tuple[float, float]
        (intercepto, coeficiente angular)
    """
    n = len(xs)
    if n < 2:
        return (ys[0] if ys else 0, 0)

    sum_x = sum(xs)
    sum_y = sum(ys)
    sum_xy = sum(x * y for x, y in zip(xs, ys))
    sum_x2 = sum(x * x for x in xs)

    denom = n * sum_x2 - sum_x * sum_x
    if denom == 0:
        return (sum_y / n, 0)

    b = (n * sum_xy - sum_x * sum_y) / denom
    a = (sum_y - b * sum_x) / n
    return (a, b)


def project_saturation_year(
    historical: List[dict],
    capacity: float,
    demand_field: str = "mov_realizada",
    year_field: str = "ano",
    max_horizon: int = 2060,
) -> dict:
    """Projeta o ano de saturação via regressão linear.

    Parameters
    ----------
    historical : list[dict]
        Dados históricos com campos ``year_field`` e ``demand_field``.
    capacity : float
        Capacidade do cais (C_cais) em t/ano ou TEU/ano.
    demand_field : str
        Campo com a movimentação realizada.
    year_field : str
        Campo com o ano.
    max_horizon : int
        Ano máximo para projeção.

    Returns
    -------
    dict
        {
            "ano_saturacao": int | None,
            "anos_ate_saturacao": int | None,
            "capacidade": float,
            "demanda_atual": float,
            "taxa_crescimento_anual": float,
            "projecao": list[dict]  # [{ano, demanda_projetada}]
        }
    """
    if not historical or capacity <= 0:
        return {
            "ano_saturacao": None,
            "anos_ate_saturacao": None,
            "capacidade": capacity,
            "demanda_atual": 0,
            "taxa_crescimento_anual": 0,
            "projecao": [],
        }

    # Ordenar por ano
    sorted_h = sorted(historical, key=lambda r: r[year_field])
    anos = [float(r[year_field]) for r in sorted_h]
    demandas = [float(r[demand_field]) for r in sorted_h if r.get(demand_field) is not None]

    if len(demandas) < 2:
        return {
            "ano_saturacao": None,
            "anos_ate_saturacao": None,
            "capacidade": capacity,
            "demanda_atual": demandas[0] if demandas else 0,
            "taxa_crescimento_anual": 0,
            "projecao": [],
        }

    # Regressão linear
    a, b = _linear_regression(anos[:len(demandas)], demandas)

    ano_atual = int(max(anos))
    demanda_atual = a + b * ano_atual

    # Taxa de crescimento anual (absoluto)
    taxa_crescimento = b

    # Projetar até encontrar saturação ou horizonte máximo
    projecao = []
    ano_saturacao = None

    for ano in range(ano_atual + 1, max_horizon + 1):
        demanda_proj = a + b * ano
        projecao.append({
            "ano": ano,
            "demanda_projetada": round(demanda_proj, 2),
            "capacidade": round(capacity, 2),
        })
        if demanda_proj >= capacity and ano_saturacao is None:
            ano_saturacao = ano

    anos_ate_saturacao = (ano_saturacao - ano_atual) if ano_saturacao else None

    return {
        "ano_saturacao": ano_saturacao,
        "anos_ate_saturacao": anos_ate_saturacao,
        "capacidade": round(capacity, 2),
        "demanda_atual": round(demanda_atual, 2),
        "taxa_crescimento_anual": round(taxa_crescimento, 2),
        "projecao": projecao[:30],  # Limitar a 30 anos
    }


def compute_capacity_trend(
    yearly_results: List[dict],
) -> List[dict]:
    """Calcula a tendência ano-a-ano de capacidade e BOR.

    Parameters
    ----------
    yearly_results : list[dict]
        Resultados de capacidade por ano (output de compute_berth_capacity).
        Cada dict deve ter: ano, c_cais_bruta, bor_obs_pct, bur_obs_pct

    Returns
    -------
    list[dict]
        Lista ordenada com: ano, c_cais, bor_obs, bur_obs,
        variacao_c_cais_pct, variacao_bor_pct
    """
    if not yearly_results:
        return []

    sorted_r = sorted(yearly_results, key=lambda r: r.get("ano", 0))

    trend = []
    prev = None

    for r in sorted_r:
        entry = {
            "ano": r.get("ano"),
            "c_cais": r.get("c_cais_bruta") or r.get("c_alocada"),
            "bor_obs_pct": r.get("bor_obs_pct"),
            "bur_obs_pct": r.get("bur_obs_pct"),
            "bor_adm_pct": (r.get("bor_adm", 0) * 100) if r.get("bor_adm") else None,
            "saturado": r.get("saturado", False),
        }

        if prev and prev.get("c_cais") and entry["c_cais"]:
            entry["variacao_c_cais_pct"] = round(
                (entry["c_cais"] - prev["c_cais"]) / prev["c_cais"] * 100, 2
            )
        else:
            entry["variacao_c_cais_pct"] = None

        if prev and prev.get("bor_obs_pct") is not None and entry["bor_obs_pct"] is not None:
            entry["variacao_bor_pp"] = round(
                entry["bor_obs_pct"] - prev["bor_obs_pct"], 2
            )
        else:
            entry["variacao_bor_pp"] = None

        trend.append(entry)
        prev = entry

    return trend


def identify_bottleneck(
    c_cais: float,
    c_armazenagem: Optional[float] = None,
    c_hinterland: Optional[float] = None,
) -> dict:
    """Identifica o subsistema gargalo (Eq. 13).

    Returns
    -------
    dict
        {
            "gargalo": str,
            "c_sistema": float,
            "subsistemas": dict
        }
    """
    subsistemas: Dict[str, Optional[float]] = {
        "cais": c_cais,
        "armazenagem": c_armazenagem,
        "hinterland": c_hinterland,
    }

    configured = {k: v for k, v in subsistemas.items() if v is not None}

    if not configured:
        return {
            "gargalo": "sem_dados",
            "c_sistema": 0,
            "subsistemas": subsistemas,
        }

    gargalo = min(configured, key=configured.get)

    return {
        "gargalo": gargalo,
        "c_sistema": round(configured[gargalo], 2),
        "subsistemas": {
            k: round(v, 2) if v is not None else None
            for k, v in subsistemas.items()
        },
    }
