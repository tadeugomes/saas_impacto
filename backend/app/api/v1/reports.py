"""
API Endpoints para Exportação de Relatórios em DOCX.

Este módulo fornece endpoints para gerar e baixar relatórios
em formato Microsoft Word (.docx) para cada módulo ou indicador.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from typing import Optional

from app.services.generic_indicator_service import (
    GenericIndicatorService,
    get_generic_indicator_service,
)
from app.schemas.indicators import GenericIndicatorRequest
from app.reports import ReportService


router = APIRouter(
    prefix="/reports",
    tags=["Relatórios - Exportação DOCX"],
)


@router.post(
    "/module/{module_code}",
    summary="Exportar Módulo Completo em DOCX",
    description="""
    Gera um relatório completo em formato DOCX para todos os indicadores de um módulo.

    **Módulos disponíveis:**
    - `1` ou `IND-1`: Operações de Navios
    - `2` ou `IND-2`: Operações de Carga
    - `3` ou `IND-3`: Recursos Humanos
    - `4` ou `IND-4`: Comércio Exterior
    - `5` ou `IND-5`: Impacto Econômico Regional
    - `6` ou `IND-6`: Finanças Públicas
    - `7` ou `IND-7`: Índices Sintéticos

    **Parâmetros:**
    - `id_instalacao`: ID da instalação/porto (opcional)
    - `id_municipio`: ID do município IBGE (opcional)
    - `ano`: Ano específico (opcional)
    - `ano_inicio` e `ano_fim`: Período de anos (opcional)

    **Retorna:** Arquivo .docx para download
    """,
)
async def export_module_report(
    module_code: str,
    id_instalacao: Optional[str] = Query(None, description="ID da instalação/porto"),
    id_municipio: Optional[str] = Query(None, description="ID do município IBGE"),
    ano: Optional[int] = Query(None, description="Ano específico"),
    ano_inicio: Optional[int] = Query(None, description="Ano inicial do período"),
    ano_fim: Optional[int] = Query(None, description="Ano final do período"),
    service: GenericIndicatorService = Depends(get_generic_indicator_service),
):
    """
    Gera e retorna um relatório DOCX completo para um módulo.

    O relatório inclui:
    - Cabeçalho com nome do módulo, porto e ano
    - Resumo executivo com totais
    - Tabela detalhada com todos os dados
    - Notas metodológicas
    """
    try:
        # Normaliza o código do módulo
        if not module_code.startswith("IND-"):
            module_code = f"IND-{module_code}"

        report_service = ReportService()

        # Busca dados de todos os indicadores do módulo
        data = {}
        porto_nome = id_instalacao or "Todos os portos"

        # Lista de indicadores por módulo
        module_indicators = _get_indicators_by_module(module_code)

        for indicator_code in module_indicators:
            request = GenericIndicatorRequest(
                codigo_indicador=indicator_code,
                id_instalacao=id_instalacao,
                id_municipio=id_municipio,
                ano=ano,
                ano_inicio=ano_inicio,
                ano_fim=ano_fim,
            )
            result = await service.execute_indicator(request)
            data[indicator_code] = result.data

        # Gera o DOCX
        doc_bytes, filename = report_service.generate_module_report(
            module_code=module_code,
            data=data,
            porto=porto_nome,
            ano=ano or (ano_inicio if ano_inicio else None),
        )

        # Retorna o arquivo para download
        return StreamingResponse(
            content=iter([doc_bytes.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar relatório: {str(e)}",
        )


@router.post(
    "/indicator/{indicator_code}",
    summary="Exportar Indicador Individual em DOCX",
    description="""
    Gera um relatório DOCX para um único indicador.

    **Exemplos de códigos:**
    - `IND-1.01`: Tempo Médio de Espera
    - `IND-2.06`: Produtividade de Berço
    - `IND-3.01`: Empregos Portuários
    - `IND-4.01`: Valor FOB Exportações
    - `IND-5.01`: PIB Municipal

    **Retorna:** Arquivo .docx para download
    """,
)
async def export_indicator_report(
    indicator_code: str,
    id_instalacao: Optional[str] = Query(None, description="ID da instalação/porto"),
    id_municipio: Optional[str] = Query(None, description="ID do município IBGE"),
    ano: Optional[int] = Query(None, description="Ano específico"),
    ano_inicio: Optional[int] = Query(None, description="Ano inicial do período"),
    ano_fim: Optional[int] = Query(None, description="Ano final do período"),
    service: GenericIndicatorService = Depends(get_generic_indicator_service),
):
    """
    Gera e retorna um relatório DOCX para um indicador específico.

    O relatório inclui:
    - Nome e descrição do indicador
    - Tabela com dados
    - Notas metodológicas
    """
    try:
        # Normaliza o código do indicador
        if not indicator_code.startswith("IND-"):
            # Assume formato curto como "1.01"
            indicator_code = f"IND-{indicator_code}"

        report_service = ReportService()

        # Busca dados do indicador
        request = GenericIndicatorRequest(
            codigo_indicador=indicator_code,
            id_instalacao=id_instalacao,
            id_municipio=id_municipio,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )
        result = await service.execute_indicator(request)

        # Determina o código do módulo
        module_code = f"IND-{indicator_code.split('.')[0].replace('IND-', '')}"

        # Gera o DOCX
        doc_bytes, filename = report_service.generate_single_indicator_report(
            module_code=module_code,
            indicator_code=indicator_code,
            data=result.data,
            porto=id_instalacao or "Todos",
            ano=ano or (ano_inicio if ano_inicio else None),
        )

        # Retorna o arquivo para download
        return StreamingResponse(
            content=iter([doc_bytes.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar relatório: {str(e)}",
        )


def _get_indicators_by_module(module_code: str) -> list[str]:
    """Retorna lista de códigos de indicadores por módulo."""
    module_num = module_code.replace("IND-", "").split(".")[0]

    indicators_by_module = {
        "1": [
            "IND-1.01", "IND-1.02", "IND-1.03", "IND-1.04", "IND-1.05",
            "IND-1.06", "IND-1.07", "IND-1.08", "IND-1.09", "IND-1.10",
            "IND-1.11", "IND-1.12",
        ],
        "2": [
            "IND-2.01", "IND-2.02", "IND-2.03", "IND-2.04", "IND-2.05",
            "IND-2.06", "IND-2.07", "IND-2.08", "IND-2.09", "IND-2.10",
            "IND-2.11", "IND-2.12", "IND-2.13",
        ],
        "3": [
            "IND-3.01", "IND-3.02", "IND-3.03", "IND-3.04", "IND-3.05",
            "IND-3.06", "IND-3.07", "IND-3.08", "IND-3.09", "IND-3.10",
            "IND-3.11", "IND-3.12",
        ],
        "4": [
            "IND-4.01", "IND-4.02", "IND-4.03", "IND-4.04", "IND-4.05",
            "IND-4.06", "IND-4.07", "IND-4.08", "IND-4.09", "IND-4.10",
        ],
        "5": [
            "IND-5.01", "IND-5.02", "IND-5.03", "IND-5.04", "IND-5.05",
            "IND-5.06", "IND-5.07", "IND-5.08", "IND-5.09", "IND-5.10",
            "IND-5.11", "IND-5.12", "IND-5.13", "IND-5.14", "IND-5.15",
            "IND-5.16", "IND-5.17", "IND-5.18", "IND-5.19", "IND-5.20",
            "IND-5.21",
        ],
        "6": [
            "IND-6.01", "IND-6.02", "IND-6.03", "IND-6.04", "IND-6.05", "IND-6.06",
        ],
        "7": [
            "IND-7.01", "IND-7.02", "IND-7.03", "IND-7.04", "IND-7.05",
            "IND-7.06", "IND-7.07",
        ],
    }

    return indicators_by_module.get(module_num, [])
