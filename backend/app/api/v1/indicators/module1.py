"""
API Endpoints para Indicadores do Módulo 1 - Operações de Navios.

Este módulo expõe os 12 indicadores de operações de navios através da API REST,
com suporte a filtros e paginação.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.services.indicator_service import (
    ShipOperationsIndicatorService,
    get_indicator_service,
)
from app.schemas.indicators import (
    TempoMedioEsperaResponse,
    TempoMedioPortoResponse,
    TempoBrutoAtracacaoResponse,
    TempoLiquidoOperacaoResponse,
    TaxaOcupacaoBercoesResponse,
    TempoOciosoTurnoResponse,
    ArqueacaoBrutaMediaResponse,
    ComprimentoMedioNavioResponse,
    CaladoMaximoOperacionalResponse,
    DistribuicaoTipoNavioResponse,
    NumeroAtracacoesResponse,
    IndiceParalisacaoResponse,
    OperacoesNaviosResumoResponse,
    OperacoesNaviosRequest,
    IndicatorListRequest,
)


router = APIRouter(
    prefix="/indicators/module1",
    tags=["Módulo 1 - Operações de Navios"],
)


# ============================================================================
# Endpoints Individuais por Indicador
# ============================================================================

@router.get(
    "/ind-101/tempo-medio-espera",
    response_model=List[TempoMedioEsperaResponse],
    summary="IND-1.01: Tempo Médio de Espera [UNCTAD]",
    description="Retorna o tempo médio entre a chegada e o início da atracação.",
)
async def get_tempo_medio_espera(
    id_instalacao: Optional[str] = Query(
        None,
        description="ID da instalação portuária",
    ),
    ano: Optional[int] = Query(
        None,
        description="Ano de referência (YYYY)",
        ge=2000,
        le=2100,
    ),
    ano_inicio: Optional[int] = Query(
        None,
        description="Ano inicial do período",
        ge=2000,
        le=2100,
    ),
    ano_fim: Optional[int] = Query(
        None,
        description="Ano final do período",
        ge=2000,
        le=2100,
    ),
    service: ShipOperationsIndicatorService = Depends(get_indicator_service),
) -> List[TempoMedioEsperaResponse]:
    """
    Consulta o IND-1.01: Tempo Médio de Espera.

    **Filtros:**
    - `id_instalacao`: Filtrar por instalação específica
    - `ano`: Ano específico OU
    - `ano_inicio` + `ano_fim`: Período de anos

    **Retorna:** Lista de resultados com tempos médios em horas
    """
    try:
        return await service.get_tempo_medio_espera(
            id_instalacao=id_instalacao,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar indicador: {str(e)}",
        )


@router.get(
    "/ind-102/tempo-medio-porto",
    response_model=List[TempoMedioPortoResponse],
    summary="IND-1.02: Tempo Médio em Porto [UNCTAD]",
    description="Retorna o tempo médio total no porto (atracado + espera).",
)
async def get_tempo_medio_porto(
    id_instalacao: Optional[str] = Query(None, description="ID da instalação"),
    ano: Optional[int] = Query(None, description="Ano de referência", ge=2000, le=2100),
    ano_inicio: Optional[int] = Query(None, description="Ano inicial", ge=2000, le=2100),
    ano_fim: Optional[int] = Query(None, description="Ano final", ge=2000, le=2100),
    service: ShipOperationsIndicatorService = Depends(get_indicator_service),
) -> List[TempoMedioPortoResponse]:
    """Consulta o IND-1.02: Tempo Médio em Porto."""
    try:
        return await service.get_tempo_medio_porto(
            id_instalacao=id_instalacao,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar indicador: {str(e)}",
        )


@router.get(
    "/ind-103/tempo-bruto-atracacao",
    response_model=List[TempoBrutoAtracacaoResponse],
    summary="IND-1.03: Tempo Bruto de Atracação [UNCTAD]",
    description="Retorna o tempo bruto médio de atracação.",
)
async def get_tempo_bruto_atracacao(
    id_instalacao: Optional[str] = Query(None, description="ID da instalação"),
    ano: Optional[int] = Query(None, description="Ano de referência", ge=2000, le=2100),
    ano_inicio: Optional[int] = Query(None, description="Ano inicial", ge=2000, le=2100),
    ano_fim: Optional[int] = Query(None, description="Ano final", ge=2000, le=2100),
    service: ShipOperationsIndicatorService = Depends(get_indicator_service),
) -> List[TempoBrutoAtracacaoResponse]:
    """Consulta o IND-1.03: Tempo Bruto de Atracação."""
    try:
        return await service.get_tempo_bruto_atracacao(
            id_instalacao=id_instalacao,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar indicador: {str(e)}",
        )


@router.get(
    "/ind-104/tempo-liquido-operacao",
    response_model=List[TempoLiquidoOperacaoResponse],
    summary="IND-1.04: Tempo Líquido de Operação [UNCTAD]",
    description="Retorna o tempo líquido médio de operação com carga.",
)
async def get_tempo_liquido_operacao(
    id_instalacao: Optional[str] = Query(None, description="ID da instalação"),
    ano: Optional[int] = Query(None, description="Ano de referência", ge=2000, le=2100),
    ano_inicio: Optional[int] = Query(None, description="Ano inicial", ge=2000, le=2100),
    ano_fim: Optional[int] = Query(None, description="Ano final", ge=2000, le=2100),
    service: ShipOperationsIndicatorService = Depends(get_indicator_service),
) -> List[TempoLiquidoOperacaoResponse]:
    """Consulta o IND-1.04: Tempo Líquido de Operação."""
    try:
        return await service.get_tempo_liquido_operacao(
            id_instalacao=id_instalacao,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar indicador: {str(e)}",
        )


@router.get(
    "/ind-105/taxa-ocupacao-bercos",
    response_model=List[TaxaOcupacaoBercoesResponse],
    summary="IND-1.05: Taxa de Ocupação de Berços [UNCTAD]",
    description="Retorna a taxa média de ocupação dos berços.",
)
async def get_taxa_ocupacao_bercos(
    id_instalacao: Optional[str] = Query(None, description="ID da instalação"),
    ano: Optional[int] = Query(None, description="Ano de referência", ge=2000, le=2100),
    ano_inicio: Optional[int] = Query(None, description="Ano inicial", ge=2000, le=2100),
    ano_fim: Optional[int] = Query(None, description="Ano final", ge=2000, le=2100),
    service: ShipOperationsIndicatorService = Depends(get_indicator_service),
) -> List[TaxaOcupacaoBercoesResponse]:
    """Consulta o IND-1.05: Taxa de Ocupação de Berços."""
    try:
        return await service.get_taxa_ocupacao_bercos(
            id_instalacao=id_instalacao,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar indicador: {str(e)}",
        )


@router.get(
    "/ind-106/tempo-ocioso-turno",
    response_model=List[TempoOciosoTurnoResponse],
    summary="IND-1.06: Tempo Ocioso Médio por Turno [UNCTAD]",
    description="Retorna o tempo médio de paralisação durante operação.",
)
async def get_tempo_ocioso_turno(
    id_instalacao: Optional[str] = Query(None, description="ID da instalação"),
    ano: Optional[int] = Query(None, description="Ano de referência", ge=2000, le=2100),
    ano_inicio: Optional[int] = Query(None, description="Ano inicial", ge=2000, le=2100),
    ano_fim: Optional[int] = Query(None, description="Ano final", ge=2000, le=2100),
    service: ShipOperationsIndicatorService = Depends(get_indicator_service),
) -> List[TempoOciosoTurnoResponse]:
    """Consulta o IND-1.06: Tempo Ocioso Médio por Turno."""
    try:
        return await service.get_tempo_ocioso_turno(
            id_instalacao=id_instalacao,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar indicador: {str(e)}",
        )


@router.get(
    "/ind-107/arqueacao-bruta-media",
    response_model=List[ArqueacaoBrutaMediaResponse],
    summary="IND-1.07: Arqueação Bruta Média [UNCTAD]",
    description="Retorna a arqueação bruta média dos navios em GT.",
)
async def get_arqueacao_bruta_media(
    id_instalacao: Optional[str] = Query(None, description="ID da instalação"),
    ano: Optional[int] = Query(None, description="Ano de referência", ge=2000, le=2100),
    ano_inicio: Optional[int] = Query(None, description="Ano inicial", ge=2000, le=2100),
    ano_fim: Optional[int] = Query(None, description="Ano final", ge=2000, le=2100),
    service: ShipOperationsIndicatorService = Depends(get_indicator_service),
) -> List[ArqueacaoBrutaMediaResponse]:
    """Consulta o IND-1.07: Arqueação Bruta Média."""
    try:
        return await service.get_arqueacao_bruta_media(
            id_instalacao=id_instalacao,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar indicador: {str(e)}",
        )


@router.get(
    "/ind-108/comprimento-medio-navios",
    response_model=List[ComprimentoMedioNavioResponse],
    summary="IND-1.08: Comprimento Médio de Navios [UNCTAD]",
    description="Retorna o comprimento médio dos navios em metros.",
)
async def get_comprimento_medio_navios(
    id_instalacao: Optional[str] = Query(None, description="ID da instalação"),
    ano: Optional[int] = Query(None, description="Ano de referência", ge=2000, le=2100),
    ano_inicio: Optional[int] = Query(None, description="Ano inicial", ge=2000, le=2100),
    ano_fim: Optional[int] = Query(None, description="Ano final", ge=2000, le=2100),
    service: ShipOperationsIndicatorService = Depends(get_indicator_service),
) -> List[ComprimentoMedioNavioResponse]:
    """Consulta o IND-1.08: Comprimento Médio de Navios."""
    try:
        return await service.get_comprimento_medio_navios(
            id_instalacao=id_instalacao,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar indicador: {str(e)}",
        )


@router.get(
    "/ind-109/calado-maximo-operacional",
    response_model=List[CaladoMaximoOperacionalResponse],
    summary="IND-1.09: Calado Máximo Operacional [UNCTAD]",
    description="Retorna o maior calado já registrado na instalação.",
)
async def get_calado_maximo_operacional(
    id_instalacao: Optional[str] = Query(None, description="ID da instalação"),
    service: ShipOperationsIndicatorService = Depends(get_indicator_service),
) -> List[CaladoMaximoOperacionalResponse]:
    """Consulta o IND-1.09: Calado Máximo Operacional."""
    try:
        return await service.get_calado_maximo_operacional(
            id_instalacao=id_instalacao,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar indicador: {str(e)}",
        )


@router.get(
    "/ind-110/distribuicao-tipo-navio",
    response_model=List[DistribuicaoTipoNavioResponse],
    summary="IND-1.10: Distribuição por Tipo de Navio [UNCTAD]",
    description="Retorna a distribuição de atracações por tipo de navegação.",
)
async def get_distribuicao_tipo_navio(
    id_instalacao: Optional[str] = Query(None, description="ID da instalação"),
    ano: Optional[int] = Query(None, description="Ano de referência", ge=2000, le=2100),
    service: ShipOperationsIndicatorService = Depends(get_indicator_service),
) -> List[DistribuicaoTipoNavioResponse]:
    """Consulta o IND-1.10: Distribuição por Tipo de Navio."""
    try:
        return await service.get_distribuicao_tipo_navio(
            id_instalacao=id_instalacao,
            ano=ano,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar indicador: {str(e)}",
        )


@router.get(
    "/ind-111/numero-atracacoes",
    response_model=List[NumeroAtracacoesResponse],
    summary="IND-1.11: Número de Atracações",
    description="Retorna o total de atracações no período.",
)
async def get_numero_atracacoes(
    id_instalacao: Optional[str] = Query(None, description="ID da instalação"),
    ano: Optional[int] = Query(None, description="Ano de referência", ge=2000, le=2100),
    ano_inicio: Optional[int] = Query(None, description="Ano inicial", ge=2000, le=2100),
    ano_fim: Optional[int] = Query(None, description="Ano final", ge=2000, le=2100),
    service: ShipOperationsIndicatorService = Depends(get_indicator_service),
) -> List[NumeroAtracacoesResponse]:
    """Consulta o IND-1.11: Número de Atracações."""
    try:
        return await service.get_numero_atracacoes(
            id_instalacao=id_instalacao,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar indicador: {str(e)}",
        )


@router.get(
    "/ind-112/indice-paralisacao",
    response_model=List[IndiceParalisacaoResponse],
    summary="IND-1.12: Índice de Paralisação",
    description="Retorna o índice de paralisação (tempo paralisado / tempo atracado).",
)
async def get_indice_paralisacao(
    id_instalacao: Optional[str] = Query(None, description="ID da instalação"),
    ano: Optional[int] = Query(None, description="Ano de referência", ge=2000, le=2100),
    ano_inicio: Optional[int] = Query(None, description="Ano inicial", ge=2000, le=2100),
    ano_fim: Optional[int] = Query(None, description="Ano final", ge=2000, le=2100),
    service: ShipOperationsIndicatorService = Depends(get_indicator_service),
) -> List[IndiceParalisacaoResponse]:
    """Consulta o IND-1.12: Índice de Paralisação."""
    try:
        return await service.get_indice_paralisacao(
            id_instalacao=id_instalacao,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar indicador: {str(e)}",
        )


# ============================================================================
# Endpoint Consolidado
# ============================================================================

@router.get(
    "/resumo",
    response_model=OperacoesNaviosResumoResponse,
    summary="Resumo Consolidado do Módulo 1",
    description="Retorna todos os 11 indicadores principais para uma instalação/ano.",
    responses={
        404: {"description": "Dados não encontrados para a instalação/ano"},
    },
)
async def get_resumo(
    id_instalacao: str = Query(..., description="ID da instalação portuária"),
    ano: int = Query(..., description="Ano de referência", ge=2000, le=2100),
    service: ShipOperationsIndicatorService = Depends(get_indicator_service),
) -> OperacoesNaviosResumoResponse:
    """
    Retorna todos os indicadores do Módulo 1 consolidados.

    **Parâmetros obrigatórios:**
    - `id_instalacao`: ID da instalação portuária
    - `ano`: Ano de referência

    **Retorna:** Objeto com todos os 11 indicadores calculados
    """
    try:
        result = await service.get_resumo(
            id_instalacao=id_instalacao,
            ano=ano,
        )

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dados não encontrados para instalação {id_instalacao} no ano {ano}",
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar resumo: {str(e)}",
        )


# ============================================================================
# Endpoint de Metadados
# ============================================================================

@router.get(
    "/metadados",
    summary="Metadados dos Indicadores do Módulo 1",
    description="Retorna informações sobre todos os indicadores disponíveis.",
)
async def get_metadados() -> JSONResponse:
    """
    Retorna metadados de todos os indicadores do Módulo 1.

    Inclui código, nome, unidade, se segue padrão UNCTAD e descrição.
    """
    metadados = {
        "modulo": "Módulo 1 - Operações de Navios",
        "total_indicadores": 12,
        "unctad_compliant": 10,
        "indicadores": [
            {
                "codigo": "IND-1.01",
                "nome": "Tempo Médio de Espera",
                "unidade": "Horas",
                "unctad": True,
                "endpoint": "/indicators/module1/ind-101/tempo-medio-espera",
            },
            {
                "codigo": "IND-1.02",
                "nome": "Tempo Médio em Porto",
                "unidade": "Horas",
                "unctad": True,
                "endpoint": "/indicators/module1/ind-102/tempo-medio-porto",
            },
            {
                "codigo": "IND-1.03",
                "nome": "Tempo Bruto de Atracação",
                "unidade": "Horas",
                "unctad": True,
                "endpoint": "/indicators/module1/ind-103/tempo-bruto-atracacao",
            },
            {
                "codigo": "IND-1.04",
                "nome": "Tempo Líquido de Operação",
                "unidade": "Horas",
                "unctad": True,
                "endpoint": "/indicators/module1/ind-104/tempo-liquido-operacao",
            },
            {
                "codigo": "IND-1.05",
                "nome": "Taxa de Ocupação de Berços",
                "unidade": "%",
                "unctad": True,
                "endpoint": "/indicators/module1/ind-105/taxa-ocupacao-bercos",
            },
            {
                "codigo": "IND-1.06",
                "nome": "Tempo Ocioso Médio por Turno",
                "unidade": "Horas",
                "unctad": True,
                "endpoint": "/indicators/module1/ind-106/tempo-ocioso-turno",
            },
            {
                "codigo": "IND-1.07",
                "nome": "Arqueação Bruta Média",
                "unidade": "GT",
                "unctad": True,
                "endpoint": "/indicators/module1/ind-107/arqueacao-bruta-media",
            },
            {
                "codigo": "IND-1.08",
                "nome": "Comprimento Médio de Navios",
                "unidade": "Metros",
                "unctad": True,
                "endpoint": "/indicators/module1/ind-108/comprimento-medio-navios",
            },
            {
                "codigo": "IND-1.09",
                "nome": "Calado Máximo Operacional",
                "unidade": "Metros",
                "unctad": True,
                "endpoint": "/indicators/module1/ind-109/calado-maximo-operacional",
            },
            {
                "codigo": "IND-1.10",
                "nome": "Distribuição por Tipo de Navio",
                "unidade": "%",
                "unctad": True,
                "endpoint": "/indicators/module1/ind-110/distribuicao-tipo-navio",
            },
            {
                "codigo": "IND-1.11",
                "nome": "Número de Atracações",
                "unidade": "Contagem",
                "unctad": False,
                "endpoint": "/indicators/module1/ind-111/numero-atracacoes",
            },
            {
                "codigo": "IND-1.12",
                "nome": "Índice de Paralisação",
                "unidade": "%",
                "unctad": False,
                "endpoint": "/indicators/module1/ind-112/indice-paralisacao",
            },
        ],
    }

    return JSONResponse(content=metadados)
