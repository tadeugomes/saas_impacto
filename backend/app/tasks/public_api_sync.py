"""
Celery tasks para sincronização periódica de dados de APIs externas.

Pré-popula o cache Redis com dados que mudam raramente (Selic a cada 45 dias,
IPCA mensal, câmbio diário). Garante resposta <10ms durante horário comercial.
"""

from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Helper para executar coroutine em task Celery (sync)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def sync_bacen_series():
    """
    Atualiza séries BACEN no cache Redis.

    Agenda recomendada: diariamente às 10h (após abertura do mercado).
    """
    from app.clients.bacen import get_bacen_client

    async def _sync():
        bacen = get_bacen_client()
        try:
            await bacen.indicadores_atuais()
            logger.info("sync_bacen_indicadores_ok")
        except Exception as e:
            logger.error("sync_bacen_indicadores_error", error=str(e))

    _run_async(_sync())


def sync_ibge_dados():
    """
    Atualiza dados de população e PIB do IBGE.

    Agenda recomendada: mensalmente (IBGE atualiza estimativas anualmente).
    """
    from app.clients.ibge import get_ibge_client

    async def _sync():
        ibge = get_ibge_client()
        # Pre-fetch lista de municípios das UFs com portos
        ufs_portuarias = ["SP", "RJ", "ES", "BA", "PE", "CE", "MA", "PA", "AM", "RS", "SC", "PR"]
        for uf in ufs_portuarias:
            try:
                await ibge.buscar_municipios(uf)
            except Exception as e:
                logger.warning("sync_ibge_municipios_error", uf=uf, error=str(e))
        logger.info("sync_ibge_dados_ok")

    _run_async(_sync())
