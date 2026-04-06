"""
Filtro IQR (Interquartile Range) para remoção de outliers.

Utilizado no Passo 2 da metodologia de capacidade portuária para depurar
indicadores operacionais (Inop.Pré, Produtividade, Inop.Pós) antes da
agregação por grupo.

Referências:
- Memoria_Calculo_Capacidade_Conteineres.ipynb, células 6-7
- Memoria_Calculo_Capacidade_Sem_Conteineres.ipynb, células 6-7
"""
from __future__ import annotations

from typing import List, Optional, Tuple


def iqr_bounds(
    values: List[float],
    factor: float = 1.5,
) -> Tuple[float, float]:
    """Calcula os limites inferior e superior do filtro IQR.

    Parameters
    ----------
    values : list[float]
        Valores numéricos (devem ter ao menos 4 elementos para IQR útil).
    factor : float
        Multiplicador do IQR (padrão 1.5 = fences de Tukey).

    Returns
    -------
    tuple[float, float]
        (lower_bound, upper_bound)
    """
    if len(values) < 4:
        return (min(values), max(values)) if values else (0.0, 0.0)

    sorted_v = sorted(values)
    n = len(sorted_v)
    q1 = sorted_v[n // 4]
    q3 = sorted_v[(3 * n) // 4]
    iqr = q3 - q1
    return (q1 - factor * iqr, q3 + factor * iqr)


def iqr_filtered_mean(
    values: List[float],
    factor: float = 1.5,
) -> Optional[float]:
    """Retorna a média dos valores dentro dos limites IQR.

    Valores fora de [Q1 - factor*IQR, Q3 + factor*IQR] são descartados.
    Retorna None se não sobrar nenhum valor.
    """
    if not values:
        return None

    lb, ub = iqr_bounds(values, factor)
    filtered = [v for v in values if lb <= v <= ub]

    if not filtered:
        return None

    return sum(filtered) / len(filtered)


def iqr_filter_stats(
    values: List[float],
    factor: float = 1.5,
) -> dict:
    """Retorna estatísticas completas do filtro IQR.

    Útil para auditoria (equivalente ao Log_Depuracao_IQR dos notebooks).
    """
    if not values:
        return {
            "n_total": 0,
            "n_retained": 0,
            "n_removed": 0,
            "lower_bound": None,
            "upper_bound": None,
            "mean_filtered": None,
        }

    lb, ub = iqr_bounds(values, factor)
    filtered = [v for v in values if lb <= v <= ub]
    removed = len(values) - len(filtered)

    return {
        "n_total": len(values),
        "n_retained": len(filtered),
        "n_removed": removed,
        "lower_bound": round(lb, 4),
        "upper_bound": round(ub, 4),
        "mean_filtered": round(sum(filtered) / len(filtered), 4) if filtered else None,
    }
