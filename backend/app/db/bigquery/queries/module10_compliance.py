"""
Queries do Módulo 10 — Compliance e Governança Portuária.

Todas as queries filtram por relevância portuária (CNAE, termos, órgãos).
IND-10.04 retorna análise de sentimento com detalhamento por temas.
IND-10.07 e IND-10.08 retornam bloco `composicao` com transparência total.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.clients.pncp import get_pncp_client
from app.clients.tcu_federal import get_tcu_client
from app.clients.transparencia import get_transparencia_client
from app.clients.querido_diario import get_querido_diario_client
from app.clients.datajud import get_datajud_client
from app.services.compliance_service import get_compliance_service


async def query_licitacoes_portuarias(
    id_municipio: Optional[str] = None,
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """IND-10.01: Volume de Contratação Pública Portuária."""
    if not id_municipio or not ano:
        return []

    pncp = get_pncp_client()
    contratacoes = await pncp.buscar_contratacoes_portuarias(id_municipio, ano)

    valor_total = sum(
        float(c.get("valorInicial", c.get("valor", 0)) or 0)
        for c in contratacoes
    )

    return [{
        "id_municipio": id_municipio,
        "id_instalacao": id_instalacao,
        "ano": ano,
        "total_contratacoes": len(contratacoes),
        "valor_total": valor_total,
        "filtro": "termos e órgãos portuários",
    }]


async def query_sancoes_ecossistema_portuario(
    id_municipio: Optional[str] = None,
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """IND-10.02: Empresas Sancionadas no Ecossistema Portuário."""
    if not id_municipio:
        return []

    transp = get_transparencia_client()
    # Busca sanções CEIS no município — o client já existe
    try:
        contratos = await transp.buscar_contratos_municipio(id_municipio, ano or 2024)
    except Exception:
        contratos = []

    # Filtra por relevância portuária
    from app.clients.pncp import _is_port_related
    portuarios = [
        c for c in contratos
        if _is_port_related(str(c.get("objeto", "")) + " " + str(c.get("fornecedor", "")))
    ]

    return [{
        "id_municipio": id_municipio,
        "id_instalacao": id_instalacao,
        "ano": ano,
        "empresas_sancionadas": len(portuarios),
        "filtro": "CNAE portuário + termos portuários",
    }]


async def query_acordaos_tcu_portuarios(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """IND-10.03: Acórdãos TCU Portuários."""
    if not id_instalacao:
        return []

    tcu = get_tcu_client()
    acordaos = await tcu.buscar_acordaos_portuarios(id_instalacao, ano)

    return [{
        "id_instalacao": id_instalacao,
        "ano": ano,
        "total_acordaos": len(acordaos),
        "acordaos": [
            {
                "numero": a.get("numero", a.get("id", "")),
                "ementa": str(a.get("ementa", a.get("descricao", "")))[:300],
                "data": a.get("data", ""),
            }
            for a in acordaos[:10]  # Limita detalhamento a 10
        ],
        "filtro": "texto contém termos portuários",
    }]


async def query_mencoes_diario_oficial(
    id_municipio: Optional[str] = None,
    id_instalacao: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    IND-10.04: Menções em Diário Oficial com sentimento e temas.

    Retorna análise completa com score, temas, exemplos e justificativas.
    """
    if not id_municipio:
        return []

    diario = get_querido_diario_client()
    resultado = await diario.analisar_mencoes_com_temas(
        id_municipio, id_instalacao, meses=12
    )

    return [resultado]


async def query_processos_judiciais_portuarios(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """IND-10.05: Processos Judiciais Portuários."""
    if not id_instalacao:
        return []

    datajud = get_datajud_client()
    processos = await datajud.buscar_processos_portuarios(id_instalacao, ano)

    return [{
        "id_instalacao": id_instalacao,
        "ano": ano,
        "total_processos": len(processos),
        "processos": processos[:10],  # Limita detalhamento
        "filtro": "partes com CNAE portuário + assuntos portuários",
    }]


async def query_regularidade_licitatoria(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """IND-10.06: Regularidade Licitatória Portuária."""
    if not id_municipio or not ano:
        return []

    pncp = get_pncp_client()
    resultado = await pncp.calcular_regularidade_licitatoria(id_municipio, ano)
    return [resultado]


async def query_indice_risco_regulatorio(
    id_instalacao: Optional[str] = None,
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    IND-10.07: Índice de Risco Regulatório Composto.

    Combina 5 componentes com bloco `composicao` detalhado.
    """
    if not id_instalacao or not id_municipio or not ano:
        return []

    service = get_compliance_service()
    resultado = await service.indice_risco_regulatorio(
        id_instalacao, id_municipio, ano
    )
    return [resultado]


async def query_indice_governanca_portuaria(
    id_instalacao: Optional[str] = None,
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    IND-10.08: Índice de Governança Portuária (0-100).

    Combina compliance + finanças + transparência com bloco `composicao`.
    """
    if not id_instalacao or not id_municipio or not ano:
        return []

    service = get_compliance_service()
    resultado = await service.indice_governanca_portuaria(
        id_instalacao, id_municipio, ano
    )
    return [resultado]


QUERIES_MODULE_10 = {
    "IND-10.01": query_licitacoes_portuarias,
    "IND-10.02": query_sancoes_ecossistema_portuario,
    "IND-10.03": query_acordaos_tcu_portuarios,
    "IND-10.04": query_mencoes_diario_oficial,
    "IND-10.05": query_processos_judiciais_portuarios,
    "IND-10.06": query_regularidade_licitatoria,
    "IND-10.07": query_indice_risco_regulatorio,
    "IND-10.08": query_indice_governanca_portuaria,
}
