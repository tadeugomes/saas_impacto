"""
API Endpoints Genéricos para Todos os Indicadores.

Este módulo fornece endpoints universais que podem ser usados
para consultar qualquer indicador de qualquer módulo (1-7).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse

from app.services.generic_indicator_service import (
    GenericIndicatorService,
    get_generic_indicator_service,
)
from app.schemas.indicators import (
    GenericIndicatorRequest,
    GenericIndicatorResponse,
    IndicatorMetadata,
    AllIndicatorsResponse,
)


router = APIRouter(
    prefix="/indicators",
    tags=["Indicadores - Todos os Módulos"],
)


# ============================================================================
# Endpoint Universal de Indicadores
# ============================================================================

@router.post(
    "/query",
    response_model=GenericIndicatorResponse,
    summary="Consulta Universal de Indicadores",
    description="""
    Consulta qualquer indicador de qualquer módulo usando seu código.

    **Códigos de exemplo:**
    - `IND-1.01`: Tempo Médio de Espera
    - `IND-2.06`: Produtividade Bruta
    - `IND-3.01`: Empregos Diretos Portuários
    - `IND-4.01`: Valor FOB Exportações
    - `IND-5.01`: PIB Municipal
    - `IND-6.01`: Arrecadação de ICMS
    - `IND-7.01`: Índice de Eficiência Operacional

    Use GET /indicators/metadata para ver todos os códigos disponíveis.
    """,
)
async def query_indicator(
    request: GenericIndicatorRequest,
    service: GenericIndicatorService = Depends(get_generic_indicator_service),
) -> GenericIndicatorResponse:
    """
    Endpoint universal para consulta de qualquer indicador.

    **Parâmetros:**
    - `codigo_indicador`: Código do indicador (obrigatório)
    - `id_instalacao`: ID da instalação (para indicadores portuários)
    - `id_municipio`: ID do município IBGE (para indicadores regionais)
    - `ano`: Ano específico OU
    - `ano_inicio` + `ano_fim`: Período de anos
    - `mes`: Mês de referência (opcional)

    **Retorna:** Dados do indicador com metadados
    """
    try:
        return await service.execute_indicator(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao executar consulta: {str(e)}",
        )


@router.get(
    "/metadata",
    response_model=AllIndicatorsResponse,
    summary="Metadados de Todos os Indicadores",
    description="Retorna informações sobre todos os 78 indicadores disponíveis.",
)
async def get_all_metadata(
    service: GenericIndicatorService = Depends(get_generic_indicator_service),
) -> AllIndicatorsResponse:
    """
    Retorna metadados de todos os indicadores disponíveis.

    **Inclui:**
    - Código do indicador
    - Nome
    - Módulo (1-7)
    - Unidade de medida
    - Segue padrão UNCTAD
    - Descrição
    - Granularidade
    - Fonte de dados
    """
    return service.get_all_metadata()


@router.get(
    "/metadata/{codigo}",
    response_model=IndicatorMetadata,
    summary="Metadados de um Indicador",
    description="Retorna informações detalhadas de um indicador específico.",
)
async def get_indicator_metadata(
    codigo: str,
    service: GenericIndicatorService = Depends(get_generic_indicator_service),
) -> IndicatorMetadata:
    """
    Retorna metadados de um indicador específico.

    **Parâmetros:**
    - `codigo`: Código do indicador (ex: IND-1.01)
    """
    try:
        return service.get_indicator_metadata(codigo)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/modules",
    summary="Visão Geral dos Módulos",
    description="Retorna informações gerais sobre os 7 módulos de indicadores.",
)
async def get_modules_overview() -> JSONResponse:
    """
    Retorna uma visão geral dos 7 módulos do sistema.

    **Inclui:**
    - Número de indicadores por módulo
    - Indicadores UNCTAD compliant
    - Fontes de dados
    """
    modules = [
        {
            "modulo": 1,
            "nome": "Operações de Navios",
            "total_indicadores": 12,
            "unctad_compliant": 10,
            "fonte_principal": "ANTAQ",
            "descricao": "Indicadores de tempos, características e operações de navios",
        },
        {
            "modulo": 2,
            "nome": "Operações de Carga",
            "total_indicadores": 13,
            "unctad_compliant": 11,
            "fonte_principal": "ANTAQ",
            "descricao": "Volume, produtividade e utilização de carga",
        },
        {
            "modulo": 3,
            "nome": "Recursos Humanos",
            "total_indicadores": 12,
            "unctad_compliant": 8,
            "fonte_principal": "RAIS",
            "descricao": "Emprego, salários e perfil dos trabalhadores portuários",
        },
        {
            "modulo": 4,
            "nome": "Comércio Exterior",
            "total_indicadores": 10,
            "unctad_compliant": 0,
            "fonte_principal": "Comex Stat",
            "descricao": "Exportações, importações e balança comercial",
        },
        {
            "modulo": 5,
            "nome": "Impacto Econômico Regional",
            "total_indicadores": 13,
            "unctad_compliant": 0,
            "fonte_principal": "IBGE + ANTAQ",
            "descricao": "PIB, população e correlações econômicas",
        },
        {
            "modulo": 6,
            "nome": "Finanças Públicas",
            "total_indicadores": 6,
            "unctad_compliant": 0,
            "fonte_principal": "FINBRA/STN",
            "descricao": "Arrecadação municipal e receitas",
        },
        {
            "modulo": 7,
            "nome": "Índices Sintéticos",
            "total_indicadores": 7,
            "unctad_compliant": 0,
            "fonte_principal": "Múltiplas",
            "descricao": "Índices compostos e rankings",
        },
    ]

    total = sum(m["total_indicadores"] for m in modules)
    unctad = sum(m["unctad_compliant"] for m in modules)

    return JSONResponse(content={
        "sistema": "SaaS Impacto Portuário",
        "versao": "1.0",
        "total_indicadores": total,
        "unctad_compliant": unctad,
        "total_modulos": 7,
        "modulos": modules,
    })
