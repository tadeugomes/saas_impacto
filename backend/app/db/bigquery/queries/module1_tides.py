"""
Indicadores de maré para o Módulo 1 — Operações de Navios.

Funções async que consultam a API de marés da Marinha
e cruzam com dados operacionais existentes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.clients.mares import get_mares_client


async def query_taxa_aproveitamento_mare(
    id_instalacao: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    IND-1.13: Taxa de Aproveitamento de Maré.

    % do tempo em que a maré oferece calado suficiente para operação.
    """
    if not id_instalacao:
        return []

    mares = get_mares_client()
    estacao = mares.get_estacao_for_instalacao(id_instalacao)
    if not estacao:
        return [{
            "id_instalacao": id_instalacao,
            "taxa_aproveitamento_mare": None,
            "nota": "Estação de maré não mapeada para esta instalação",
        }]

    janela = await mares.janelas_navegacao(
        estacao["id"], calado_minimo=10.0  # Calado padrão de referência
    )

    return [{
        "id_instalacao": id_instalacao,
        "estacao_mare": estacao["nome"],
        "taxa_aproveitamento_mare": janela.get("percentual_janela"),
        "horas_navegaveis_por_dia": janela.get("horas_navegaveis_por_dia"),
        "calado_referencia_metros": 10.0,
    }]


async def query_janela_navegavel_media(
    id_instalacao: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    IND-1.14: Janela Navegável Média — horas/dia com calado suficiente.
    """
    if not id_instalacao:
        return []

    mares = get_mares_client()
    estacao = mares.get_estacao_for_instalacao(id_instalacao)
    if not estacao:
        return [{
            "id_instalacao": id_instalacao,
            "janela_navegavel_horas_dia": None,
            "nota": "Estação de maré não mapeada para esta instalação",
        }]

    janela = await mares.janelas_navegacao(estacao["id"], calado_minimo=10.0)

    return [{
        "id_instalacao": id_instalacao,
        "estacao_mare": estacao["nome"],
        "janela_navegavel_horas_dia": janela.get("horas_navegaveis_por_dia"),
        "percentual_janela": janela.get("percentual_janela"),
    }]


QUERIES_MODULE_1_TIDES = {
    "IND-1.13": query_taxa_aproveitamento_mare,
    "IND-1.14": query_janela_navegavel_media,
}
