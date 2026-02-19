"""Serialização de resultados causais para JSON/API.

Converte saídas do engine causal (que podem conter ``pd.DataFrame``,
``np.float64``, ``np.int64``, ``float('nan')``, ``float('inf')``) em
estruturas nativas Python seguras para ``json.dumps`` e para o Pydantic.

Regras de normalização
----------------------
* ``np.floating`` / ``np.integer`` → ``float`` / ``int``
* ``float('nan')`` → ``None``
* ``float('inf')`` / ``float('-inf')`` → ``None``
* ``pd.DataFrame`` → ``list[dict]`` (via ``dataframe_to_records``)
* ``pd.Series`` → ``list``
* ``dict`` / ``list`` → recursão
* Outros escalares → mantidos como estão
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np

try:
    import pandas as pd

    _PANDAS_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PANDAS_AVAILABLE = False


# ---------------------------------------------------------------------------
# Primitivos
# ---------------------------------------------------------------------------


def sanitize_scalars(value: Any) -> Any:
    """Normaliza um escalar para tipos Python nativos JSON-seguros."""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, np.floating):
        v = float(value)
        return None if (math.isnan(v) or math.isinf(v)) else v
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def dataframe_to_records(df: Any) -> list[dict]:
    """Converte um ``pd.DataFrame`` em ``list[dict]`` com escalares sanitizados.

    Aceita silenciosamente valores não-DataFrame e retorna lista vazia.
    """
    if not _PANDAS_AVAILABLE:
        return []
    if not isinstance(df, pd.DataFrame):
        return []
    records = df.where(pd.notnull(df), None).to_dict(orient="records")
    return [
        {k: sanitize_scalars(v) for k, v in row.items()}
        for row in records
    ]


# ---------------------------------------------------------------------------
# Recursão principal
# ---------------------------------------------------------------------------


def _serialize_value(value: Any) -> Any:
    """Serializa recursivamente qualquer valor produzido pelo engine causal."""
    if _PANDAS_AVAILABLE:
        if isinstance(value, pd.DataFrame):
            return dataframe_to_records(value)
        if isinstance(value, pd.Series):
            return [_serialize_value(v) for v in value.tolist()]

    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value]

    return sanitize_scalars(value)


def serialize_causal_result(result: Any) -> Any:
    """Ponto de entrada: serializa o resultado completo de qualquer função causal.

    Garante que nenhum ``pd.DataFrame``, ``np.float64`` ou ``NaN``/``Inf``
    chegue ao layer de resposta da API.

    Parameters
    ----------
    result:
        Qualquer estrutura de dados retornada pelas funções do engine causal
        (dict, list, DataFrame, escalar).

    Returns
    -------
    Estrutura equivalente com apenas tipos nativos Python (dict/list/str/int/
    float/None/bool).

    Examples
    --------
    >>> from app.services.impacto_economico.causal import run_did_with_diagnostics
    >>> from app.services.impacto_economico.causal.serialize import serialize_causal_result
    >>> raw = run_did_with_diagnostics(panel, outcome="pib_log", treatment_year=2015)
    >>> payload = serialize_causal_result(raw)
    >>> import json; json.dumps(payload)  # deve funcionar sem erro
    """
    return _serialize_value(result)
