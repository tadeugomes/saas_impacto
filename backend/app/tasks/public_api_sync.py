"""
Celery tasks para sincronização periódica de dados de APIs externas.

Pré-popula o cache Redis com dados que mudam raramente (Selic a cada 45 dias,
IPCA mensal, câmbio diário). Garante resposta <10ms durante horário comercial.

Schedules definidos em celery_app.py (beat_schedule):
  - sync_bacen_series: diário 10h
  - sync_ibge_dados: mensal dia 1 às 6h
  - sync_focos_incendio: a cada 3h
  - sync_nivel_rios: a cada 6h
"""

from __future__ import annotations

import asyncio
import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Helper para executar coroutine em task Celery (sync)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.tasks.public_api_sync.sync_bacen_series")
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


@celery_app.task(name="app.tasks.public_api_sync.sync_ibge_dados")
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


@celery_app.task(name="app.tasks.public_api_sync.sync_focos_incendio")
def sync_focos_incendio():
    """
    Atualiza focos de incêndio INPE para portos principais.

    Agenda recomendada: a cada 3h (dados INPE atualizam frequentemente).
    """
    from app.clients.inpe import get_inpe_client, PORTO_COORDENADAS

    async def _sync():
        inpe = get_inpe_client()
        portos_prioritarios = [
            "Santos", "Paranaguá", "Vitória", "Rio de Janeiro",
            "Salvador", "Manaus", "Belém", "São Luís",
        ]
        for porto in portos_prioritarios:
            coords = PORTO_COORDENADAS.get(porto)
            if coords:
                try:
                    await inpe.buscar_focos_incendio(
                        coords["lat"], coords["lon"], raio_km=50, dias=7
                    )
                except Exception as e:
                    logger.warning("sync_inpe_error", porto=porto, error=str(e))
        logger.info("sync_focos_incendio_ok")

    _run_async(_sync())


@celery_app.task(name="app.tasks.public_api_sync.sync_nivel_rios")
def sync_nivel_rios():
    """
    Atualiza nível de rios para portos fluviais.

    Agenda recomendada: a cada 6h.
    """
    from app.clients.ana import get_ana_client, PORTO_TO_ESTACAO_HIDRO

    async def _sync():
        ana = get_ana_client()
        for porto, estacao in PORTO_TO_ESTACAO_HIDRO.items():
            try:
                await ana.consultar_nivel_rio(estacao["codigo"])
            except Exception as e:
                logger.warning("sync_ana_error", porto=porto, error=str(e))
        logger.info("sync_nivel_rios_ok")

    _run_async(_sync())
