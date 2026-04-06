"""
Tabela de BOR admissível (Quadro 17 UNCTAD/PIANC).

Implementa o lookup (perfil_carga, n_berços) → BOR_adm usado na Eq. 1b
para cálculo de capacidade de cais.

Referências:
- roteiro_capacidades_portuarias_v12.md, Quadro 17
- BD_Modelo_Memoria_Calculo.xlsx, aba Parametros
- Memoria_Calculo_Capacidade_Conteineres.ipynb, cell params
- Memoria_Calculo_Capacidade_Sem_Conteineres.ipynb, cell params
"""
from __future__ import annotations

from typing import Optional

from app.services.capacity.constants import (
    PERFIL_CARGA_GERAL,
    PERFIL_CONTEINER,
    PERFIL_GRANEL_LIQUIDO,
    PERFIL_GRANEL_SOLIDO,
    PERFIL_RORO,
    normalizar_perfil,
)

# ---------------------------------------------------------------------------
# BOR_adm fallback — reproduz o código antigo (Paranaguá) quando o perfil
# não bate com nenhuma entrada do Quadro 17.
# ---------------------------------------------------------------------------
BOR_ADM_FALLBACK: float = 0.80

# ---------------------------------------------------------------------------
# Quadro 17 — BOR admissível por perfil de carga e faixa de berços.
# Estrutura: { perfil_canonico: { faixa_bercos: bor_adm } }
#   faixa_bercos: 1  = 1 berço
#                 2  = 2-3 berços
#                 4  = 4+ berços
# ---------------------------------------------------------------------------
_QUADRO_17: dict[str, dict[int, float]] = {
    PERFIL_GRANEL_SOLIDO: {
        1: 0.50,
        2: 0.65,
        4: 0.65,
    },
    PERFIL_GRANEL_LIQUIDO: {
        1: 0.55,
        2: 0.60,
        4: 0.60,
    },
    PERFIL_CARGA_GERAL: {
        1: 0.45,
        2: 0.60,
        4: 0.60,
    },
    PERFIL_CONTEINER: {
        1: 0.50,
        2: 0.65,
        4: 0.70,
    },
    PERFIL_RORO: {
        1: 0.55,
        2: 0.55,
        4: 0.55,
    },
}


def _faixa_bercos(n_bercos: int) -> int:
    """Converte número de berços para a faixa do Quadro 17."""
    if n_bercos <= 1:
        return 1
    if n_bercos <= 3:
        return 2
    return 4


def get_bor_adm(
    perfil: str,
    n_bercos: int,
    *,
    is_container: bool = False,
    override: Optional[float] = None,
) -> float:
    """Retorna o BOR admissível para um perfil de carga e número de berços.

    Parameters
    ----------
    perfil : str
        Perfil de carga (string ANTAQ ou canônica).
    n_bercos : int
        Número de berços operacionais do terminal.
    is_container : bool
        Se True, força perfil CONTEINER (ignora ``perfil``).
    override : float | None
        Se fornecido, retorna diretamente (config do admin).

    Returns
    -------
    float
        BOR admissível (adimensional, ex: 0.65).
    """
    if override is not None:
        return override

    perfil_norm = PERFIL_CONTEINER if is_container else normalizar_perfil(perfil)
    faixa = _faixa_bercos(n_bercos)

    mapa = _QUADRO_17.get(perfil_norm)
    if mapa is None:
        return BOR_ADM_FALLBACK

    return mapa.get(faixa, BOR_ADM_FALLBACK)


def listar_quadro_17() -> list[dict[str, object]]:
    """Retorna o Quadro 17 completo como lista de dicts (para exposição na API)."""
    rows: list[dict[str, object]] = []
    faixa_label = {1: "1 berço", 2: "2-3 berços", 4: "4+ berços"}
    for perfil, mapa in _QUADRO_17.items():
        for faixa, bor in mapa.items():
            rows.append({
                "perfil": perfil,
                "faixa_bercos": faixa_label[faixa],
                "n_bercos_min": faixa,
                "bor_adm": bor,
            })
    return rows
