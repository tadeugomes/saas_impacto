"""
Endpoints de exportação de relatórios em DOCX, PDF e XLSX.
"""

from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.reports import ReportService, PDFGenerator, XLSXGenerator
from app.reports.templates import get_indicators_by_module
from app.schemas.indicators import GenericIndicatorRequest
from app.services.generic_indicator_service import (
    GenericIndicatorService,
    get_generic_indicator_service,
)


router = APIRouter(
    prefix="/reports",
    tags=["Relatórios - Exportação DOCX"],
)


def _build_media_type(format_type: str) -> str:
    if format_type == "pdf":
        return "application/pdf"
    if format_type == "xlsx":
        return (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    return (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


def _content_disposition(filename: str) -> str:
    return f'attachment; filename="{filename}"'


@router.post(
    "/module/{module_code}",
    summary="Exportar Módulo Completo",
)
async def export_module_report(
    module_code: str,
    id_instalacao: Optional[str] = Query(None, description="ID da instalação/porto"),
    id_municipio: Optional[str] = Query(None, description="ID do município IBGE"),
    ano: Optional[int] = Query(None, description="Ano específico"),
    ano_inicio: Optional[int] = Query(None, description="Ano inicial do período"),
    ano_fim: Optional[int] = Query(None, description="Ano final do período"),
    format: Literal["docx", "pdf", "xlsx"] = Query("docx"),
    service: GenericIndicatorService = Depends(get_generic_indicator_service),
):
    """Exporta relatório consolidado de módulo em múltiplos formatos."""
    try:
        if not module_code.startswith("IND-"):
            module_code = f"IND-{module_code}"

        data: dict[str, list[dict]] = {}
        porto_nome = id_instalacao or "Todos os portos"
        module_indicators = get_indicators_by_module(module_code)

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

        if format == "docx":
            report_service = ReportService()
            report_bytes, filename = report_service.generate_module_report(
                module_code=module_code,
                data=data,
                porto=porto_nome,
                ano=ano or (ano_inicio if ano_inicio else None),
            )
        elif format == "pdf":
            report_bytes, filename = PDFGenerator().build(
                title=f"Relatório do {module_code}",
                subtitle=f"Filtro: {porto_nome}",
                rows=[item for rows in data.values() for item in rows],
                output_name=f"{module_code}_{ano or 'todos'}.pdf",
            )
        else:
            report_bytes, filename = XLSXGenerator().build_module(
                module_code=module_code,
                dataset=data,
                output_name=f"{module_code}_{ano or 'todos'}.xlsx",
            )

        return StreamingResponse(
            content=iter([report_bytes.getvalue()]),
            media_type=_build_media_type(format),
            headers={"Content-Disposition": _content_disposition(filename)},
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
    summary="Exportar Indicador Individual",
)
async def export_indicator_report(
    indicator_code: str,
    id_instalacao: Optional[str] = Query(None, description="ID da instalação/porto"),
    id_municipio: Optional[str] = Query(None, description="ID do município IBGE"),
    ano: Optional[int] = Query(None, description="Ano específico"),
    ano_inicio: Optional[int] = Query(None, description="Ano inicial do período"),
    ano_fim: Optional[int] = Query(None, description="Ano final do período"),
    format: Literal["docx", "pdf", "xlsx"] = Query("docx"),
    service: GenericIndicatorService = Depends(get_generic_indicator_service),
):
    """Exporta relatório de indicador individual em DOCX/PDF/XLSX."""
    try:
        if not indicator_code.startswith("IND-"):
            indicator_code = f"IND-{indicator_code}"

        request = GenericIndicatorRequest(
            codigo_indicador=indicator_code,
            id_instalacao=id_instalacao,
            id_municipio=id_municipio,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )
        result = await service.execute_indicator(request)
        module_code = f"IND-{indicator_code.split('.')[0].replace('IND-', '')}"

        if format == "docx":
            report_service = ReportService()
            report_bytes, filename = report_service.generate_single_indicator_report(
                module_code=module_code,
                indicator_code=indicator_code,
                data=result.data,
                porto=id_instalacao or "Todos",
                ano=ano or (ano_inicio if ano_inicio else None),
            )
        elif format == "pdf":
            report_bytes, filename = PDFGenerator().build(
                title=indicator_code,
                subtitle=module_code,
                rows=result.data,
                output_name=f"{indicator_code}_{ano or 'todos'}.pdf",
            )
        else:
            report_bytes, filename = XLSXGenerator().build_single_indicator(
                code=indicator_code,
                rows=result.data,
                output_name=f"{indicator_code}_{ano or 'todos'}.xlsx",
            )

        return StreamingResponse(
            content=iter([report_bytes.getvalue()]),
            media_type=_build_media_type(format),
            headers={"Content-Disposition": _content_disposition(filename)},
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
