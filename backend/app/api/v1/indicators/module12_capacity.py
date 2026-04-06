"""Router — Módulo 12: Capacidade Portuária."""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.db.base import get_db
from app.db.bigquery.client import get_bigquery_client
from app.db.models.terminal_capacity_config import TerminalCapacityConfig
from app.db.models.user import User
from app.schemas.capacity import (
    Quadro17Response,
    TerminalCapacityConfigCreate,
    TerminalCapacityConfigListResponse,
    TerminalCapacityConfigResponse,
    TerminalCapacityConfigUpdate,
)
from app.services.capacity.bor_adm_table import (
    BOR_ADM_FALLBACK,
    listar_quadro_17,
)
from app.services.capacity.capacity_service import CapacityAnalysisService
from app.services.capacity.saturation_projection import (
    compute_capacity_trend,
    project_saturation_year,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/indicators/module12",
    tags=["Módulo 12 — Capacidade Portuária"],
)


# ── Config CRUD ──────────────────────────────────────────────────────────────


@router.post(
    "/config",
    response_model=TerminalCapacityConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar configuração de terminal",
)
async def create_config(
    payload: TerminalCapacityConfigCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Cria a configuração de parâmetros de capacidade para um terminal."""
    # Verificar duplicata
    existing = await db.execute(
        select(TerminalCapacityConfig).where(
            TerminalCapacityConfig.tenant_id == current_user.tenant_id,
            TerminalCapacityConfig.id_instalacao == payload.id_instalacao,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Configuração para instalação '{payload.id_instalacao}' já existe",
        )

    config = TerminalCapacityConfig(
        tenant_id=current_user.tenant_id,
        **payload.model_dump(),
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    logger.info(
        "terminal_capacity_config_created",
        extra={"id_instalacao": config.id_instalacao, "tenant_id": str(config.tenant_id)},
    )
    return config


@router.get(
    "/config",
    response_model=TerminalCapacityConfigListResponse,
    summary="Listar configurações de terminal",
)
async def list_configs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista todas as configurações de capacidade do tenant."""
    result = await db.execute(
        select(TerminalCapacityConfig)
        .where(TerminalCapacityConfig.tenant_id == current_user.tenant_id)
        .order_by(TerminalCapacityConfig.id_instalacao)
    )
    items = list(result.scalars().all())
    return TerminalCapacityConfigListResponse(items=items, total=len(items))


@router.get(
    "/config/{id_instalacao}",
    response_model=TerminalCapacityConfigResponse,
    summary="Obter configuração de terminal",
)
async def get_config(
    id_instalacao: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtém a configuração de capacidade de uma instalação."""
    result = await db.execute(
        select(TerminalCapacityConfig).where(
            TerminalCapacityConfig.tenant_id == current_user.tenant_id,
            TerminalCapacityConfig.id_instalacao == id_instalacao,
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuração para instalação '{id_instalacao}' não encontrada",
        )
    return config


@router.put(
    "/config/{id_instalacao}",
    response_model=TerminalCapacityConfigResponse,
    summary="Atualizar configuração de terminal",
)
async def update_config(
    id_instalacao: str,
    payload: TerminalCapacityConfigUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Atualiza parcialmente a configuração de capacidade de uma instalação."""
    result = await db.execute(
        select(TerminalCapacityConfig).where(
            TerminalCapacityConfig.tenant_id == current_user.tenant_id,
            TerminalCapacityConfig.id_instalacao == id_instalacao,
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuração para instalação '{id_instalacao}' não encontrada",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    await db.commit()
    await db.refresh(config)
    logger.info(
        "terminal_capacity_config_updated",
        extra={"id_instalacao": id_instalacao, "fields": list(update_data.keys())},
    )
    return config


# ── Referência: Quadro 17 ────────────────────────────────────────────────────


@router.get(
    "/quadro17",
    response_model=Quadro17Response,
    summary="Quadro 17 UNCTAD — BOR admissível por perfil e berços",
)
async def get_quadro17():
    """Retorna a tabela de referência BOR admissível (Quadro 17 UNCTAD/PIANC)."""
    return Quadro17Response(
        items=listar_quadro_17(),
        fallback=BOR_ADM_FALLBACK,
    )


# ── Metadados ────────────────────────────────────────────────────────────────


@router.get(
    "/metadados",
    summary="Metadados do Módulo 12",
)
async def get_metadados():
    """Retorna metadados descritivos do módulo de capacidade portuária."""
    return {
        "modulo": 12,
        "nome": "Capacidade Portuária",
        "descricao": (
            "Análise de capacidade de cais baseada na metodologia LabPortos/UFMA "
            "com indicadores BOR/BUR, projeção de saturação e identificação de "
            "gargalos para apoio à decisão de investimento portuário."
        ),
        "metodologia": "Eq. 1b (ciclo de berço) + Quadro 17 UNCTAD/PIANC",
        "fonte_dados": "ANTAQ Estatístico Aquaviário (BigQuery)",
        "indicadores_total": 10,
        "status": "em_implementacao",
    }


# ── Análise de Capacidade ────────────────────────────────────────────────────


@router.get(
    "/capacidade-cais",
    summary="Análise completa de capacidade de cais",
)
async def get_capacidade_cais(
    id_instalacao: str = Query(..., description="Código da instalação ANTAQ"),
    ano: Optional[int] = Query(None, ge=2000, le=2100),
    ano_inicio: Optional[int] = Query(None, ge=2000, le=2100),
    ano_fim: Optional[int] = Query(None, ge=2000, le=2100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Executa a análise completa de capacidade de cais para uma instalação.

    Implementa Eq. 1b com BOR_adm Quadro 17, filtro IQR, alocação por mix
    e cálculos BOR/BUR. Usa parâmetros da configuração do terminal quando
    disponíveis, senão usa defaults.
    """
    # Buscar config do terminal (se existir)
    result = await db.execute(
        select(TerminalCapacityConfig).where(
            TerminalCapacityConfig.tenant_id == current_user.tenant_id,
            TerminalCapacityConfig.id_instalacao == id_instalacao,
        )
    )
    config = result.scalar_one_or_none()

    # Parâmetros: config do terminal ou defaults
    n_bercos = config.n_bercos if config else 1
    h_ef = config.h_ef if config else 8000.0
    clearance_h = config.clearance_h if config else 3.0
    fator_teu = config.fator_teu if config else 1.55
    bor_adm_override = config.bor_adm_override if config else None

    try:
        bq = get_bigquery_client()
        service = CapacityAnalysisService(bq)
        analysis = await service.compute_capacity(
            id_instalacao=id_instalacao,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
            n_bercos=n_bercos,
            h_ef=h_ef,
            clearance_h=clearance_h,
            fator_teu=fator_teu,
            bor_adm_override=bor_adm_override,
        )
    except Exception as exc:
        logger.error("capacity_analysis_error", exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na análise de capacidade: {exc}",
        )

    analysis["config_terminal"] = {
        "fonte": "config" if config else "defaults",
        "nome_terminal": config.nome_terminal if config else None,
    }

    return JSONResponse(content=analysis)


@router.get(
    "/resumo",
    summary="Resumo consolidado de capacidade (Quadro 5)",
)
async def get_resumo(
    id_instalacao: str = Query(..., description="Código da instalação ANTAQ"),
    ano: Optional[int] = Query(None, ge=2000, le=2100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retorna o resumo sistêmico (Quadro 5) com C_cais total, gargalo e parâmetros."""
    result = await db.execute(
        select(TerminalCapacityConfig).where(
            TerminalCapacityConfig.tenant_id == current_user.tenant_id,
            TerminalCapacityConfig.id_instalacao == id_instalacao,
        )
    )
    config = result.scalar_one_or_none()

    n_bercos = config.n_bercos if config else 1
    h_ef = config.h_ef if config else 8000.0
    clearance_h = config.clearance_h if config else 3.0
    fator_teu = config.fator_teu if config else 1.55
    bor_adm_override = config.bor_adm_override if config else None

    try:
        bq = get_bigquery_client()
        service = CapacityAnalysisService(bq)
        analysis = await service.compute_capacity(
            id_instalacao=id_instalacao,
            ano=ano,
            n_bercos=n_bercos,
            h_ef=h_ef,
            clearance_h=clearance_h,
            fator_teu=fator_teu,
            bor_adm_override=bor_adm_override,
        )
    except Exception as exc:
        logger.error("capacity_resumo_error", exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no resumo de capacidade: {exc}",
        )

    return JSONResponse(content={
        "id_instalacao": id_instalacao,
        "ano": ano,
        "consolidacao": analysis["consolidacao"],
        "parametros": analysis["parametros"],
    })


# ── Projeção de Saturação ────────────────────────────────────────────────────


@router.get(
    "/projecao-saturacao",
    summary="Projeção do ano de saturação",
)
async def get_projecao_saturacao(
    id_instalacao: str = Query(..., description="Código da instalação ANTAQ"),
    ano_inicio: int = Query(2018, ge=2000, le=2100, description="Ano inicial do histórico"),
    ano_fim: int = Query(2024, ge=2000, le=2100, description="Ano final do histórico"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Projeta o ano em que a demanda ultrapassará a capacidade do cais.

    Usa regressão linear sobre o histórico de movimentação para extrapolar
    a demanda e encontrar o cruzamento com C_cais.
    """
    result = await db.execute(
        select(TerminalCapacityConfig).where(
            TerminalCapacityConfig.tenant_id == current_user.tenant_id,
            TerminalCapacityConfig.id_instalacao == id_instalacao,
        )
    )
    config = result.scalar_one_or_none()

    n_bercos = config.n_bercos if config else 1
    h_ef = config.h_ef if config else 8000.0
    clearance_h = config.clearance_h if config else 3.0
    fator_teu = config.fator_teu if config else 1.55
    bor_adm_override = config.bor_adm_override if config else None

    try:
        bq = get_bigquery_client()
        service = CapacityAnalysisService(bq)
        analysis = await service.compute_capacity(
            id_instalacao=id_instalacao,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
            n_bercos=n_bercos,
            h_ef=h_ef,
            clearance_h=clearance_h,
            fator_teu=fator_teu,
            bor_adm_override=bor_adm_override,
        )
    except Exception as exc:
        logger.error("saturation_projection_error", exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na projeção de saturação: {exc}",
        )

    all_results = analysis["nao_conteiner"] + analysis["conteiner"]
    c_cais_total = analysis["consolidacao"]["c_cais_total"]

    # Dados históricos por ano
    yearly_mov: dict[int, float] = {}
    for r in all_results:
        ano = r["ano"]
        yearly_mov[ano] = yearly_mov.get(ano, 0) + r["mov_realizada"]

    historical = [{"ano": a, "mov_realizada": m} for a, m in sorted(yearly_mov.items())]

    projection = project_saturation_year(
        historical=historical,
        capacity=c_cais_total,
    )

    # Tendência de capacidade
    trend = compute_capacity_trend(all_results)

    return JSONResponse(content={
        "id_instalacao": id_instalacao,
        "projecao_saturacao": projection,
        "tendencia_capacidade": trend,
        "parametros": analysis["parametros"],
    })
