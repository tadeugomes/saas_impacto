"""
API Endpoints Genéricos para Todos os Indicadores.

Este módulo fornece endpoints universais que podem ser usados
para consultar qualquer indicador de qualquer módulo (1-7).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Any
from app.services.generic_indicator_service import (
    GenericIndicatorService,
    get_generic_indicator_service,
    INDICATORS_METADATA,
    IndicatorAccessError,
    IndicatorQuotaError,
)
from app.services.audit_service import AuditService, get_audit_service
from app.services.tenant_policy_service import get_tenant_policy_service, TenantPolicyService
from app.services.tenant_permission_service import (
    TenantPermissionService,
    get_tenant_permission_service,
)
from app.schemas.indicators import (
    GenericIndicatorRequest,
    GenericIndicatorResponse,
    IndicatorMetadata,
    AllIndicatorsResponse,
    TenantModulePermissionsRequest,
    TenantModulePermissionsResponse,
    TenantModulePermissionItem,
    AreaInfluenceUpsertRequest,
    AllowlistPolicyUpdateRequest,
)
from app.core.tenant import get_tenant_id
from app.db.base import get_db
from app.api.deps import require_admin, require_indicator_permission
from app.db.models.user import User


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
    policy_service: TenantPolicyService = Depends(get_tenant_policy_service),
    audit_service: AuditService = Depends(get_audit_service),
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_indicator_permission("read")),
    http_response: Response = None,
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
        policy = await policy_service.get_policy(db, tenant_id)
        user_id = str(current_user.id) if current_user else None
        audit_context: dict[str, Any] = {}

        result = await service.execute_indicator(
            request,
            tenant_policy=policy,
            tenant_id=str(tenant_id),
            user_id=user_id,
            audit_context=audit_context,
        )
        await audit_service.record_action(
            db=db,
            tenant_id=tenant_id,
            user_id=current_user.id if current_user else None,
            action="query_indicator",
            resource="/api/v1/indicators/query",
            status_code=200,
            duration_ms=audit_context.get("duration_ms"),
            bytes_processed=audit_context.get("bytes_processed"),
            details={
                "codigo_indicador": request.codigo_indicador,
                "id_municipio": request.id_municipio,
                "id_instalacao": request.id_instalacao,
                "ano": request.ano,
                "ano_inicio": request.ano_inicio,
                "ano_fim": request.ano_fim,
                "cache_hit": audit_context.get("cache_hit", False),
            },
            request_id=None,
        )
        if http_response is not None:
            http_response.headers["X-Cache-Hit"] = "true" if result.cache_hit else "false"
        return result
    except IndicatorAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except IndicatorQuotaError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
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
    "/policies",
    summary="Políticas do Tenant para Indicadores",
    description="Retorna configuração de area de influencia, allowlist e quota do tenant.",
)
async def get_tenant_policies(
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    policy_service: TenantPolicyService = Depends(get_tenant_policy_service),
):
    policy = await policy_service.get_policy(db, tenant_id)
    return JSONResponse(
        content={
            "tenant_id": str(tenant_id),
            "allowed_installations": policy.get("allowed_installations", []),
            "allowed_municipios": policy.get("allowed_municipios", []),
            "area_influencia": policy.get("area_influencia", {}),
            "max_bytes_per_query": policy.get("max_bytes_per_query"),
        }
    )


def _normalize_role(role: str) -> str:
    return role.strip().lower()


@router.get(
    "/permissions/{role}",
    response_model=TenantModulePermissionsResponse,
    summary="Listar permissões de role do tenant",
    description="Lista permissões explícitas configuradas para um role no tenant atual.",
)
async def get_tenant_role_permissions(
    role: str,
    _: User = Depends(require_admin),
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    permission_service: TenantPermissionService = Depends(get_tenant_permission_service),
) -> TenantModulePermissionsResponse:
    role = _normalize_role(role)
    permissions = await permission_service.list_permissions(
        db=db,
        tenant_id=tenant_id,
        role=role,
    )
    items = [
        TenantModulePermissionItem(
            module_number=permission["module_number"],
            action=permission["action"],
            allowed=True,
        )
        for permission in permissions
    ]
    return TenantModulePermissionsResponse(role=role, permissions=items)


@router.put(
    "/permissions/{role}",
    response_model=TenantModulePermissionsResponse,
    summary="Configurar permissões de role do tenant",
    description=(
        "Substitui o conjunto explícito de permissões (módulo/ação) para o role."
    ),
)
async def replace_tenant_role_permissions(
    role: str,
    payload: TenantModulePermissionsRequest,
    _: User = Depends(require_admin),
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    permission_service: TenantPermissionService = Depends(get_tenant_permission_service),
) -> TenantModulePermissionsResponse:
    role = _normalize_role(role)
    try:
        permissions = await permission_service.set_permissions_for_role(
            db=db,
            tenant_id=tenant_id,
            role=role,
            permissions=[
                (item.module_number, item.action, item.allowed)
                for item in payload.permissions
            ],
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    items = [
        TenantModulePermissionItem(
            module_number=permission["module_number"],
            action=permission["action"],
            allowed=True,
        )
        for permission in permissions
    ]
    return TenantModulePermissionsResponse(role=role, permissions=items)


@router.put(
    "/policies/area-influence/{id_instalacao}",
    summary="Criar/Atualizar área de influência",
)
async def upsert_area_influence(
    id_instalacao: str,
    payload: AreaInfluenceUpsertRequest,
    _: User = Depends(require_admin),
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    policy_service: TenantPolicyService = Depends(get_tenant_policy_service),
):
    try:
        updated = await policy_service.set_area_influencia(
            db=db,
            tenant_id=tenant_id,
            id_instalacao=id_instalacao,
            municipios=[item.model_dump() for item in payload.municipios],
        )
        area = updated.get("area_influencia", {}).get(id_instalacao, [])
        return JSONResponse(
            content={
                "tenant_id": str(tenant_id),
                "id_instalacao": id_instalacao,
                "total_municipios": len(area),
                "municipios": area,
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/policies/area-influence/{id_instalacao}",
    summary="Remover área de influência",
)
async def delete_area_influence(
    id_instalacao: str,
    _: User = Depends(require_admin),
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    policy_service: TenantPolicyService = Depends(get_tenant_policy_service),
):
    updated = await policy_service.delete_area_influencia(
        db=db,
        tenant_id=tenant_id,
        id_instalacao=id_instalacao,
    )
    return JSONResponse(
        content={
            "tenant_id": str(tenant_id),
            "id_instalacao": id_instalacao,
            "area_influencia": updated.get("area_influencia", {}),
        }
    )


@router.put(
    "/policies/allowlist",
    summary="Atualizar allowlist de municípios/quota",
)
async def update_allowlist(
    payload: AllowlistPolicyUpdateRequest,
    _: User = Depends(require_admin),
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    policy_service: TenantPolicyService = Depends(get_tenant_policy_service),
):
    try:
        updated = await policy_service.set_allowlist_policy(
            db=db,
            tenant_id=tenant_id,
            allowed_municipios=payload.allowed_municipios,
            max_bytes_per_query=payload.max_bytes_per_query,
        )
        return JSONResponse(
            content={
                "tenant_id": str(tenant_id),
                "allowed_municipios": updated.get("allowed_municipios", []),
                "max_bytes_per_query": updated.get("max_bytes_per_query"),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/metadata",
    response_model=AllIndicatorsResponse,
    summary="Metadados de Todos os Indicadores",
    description="Retorna informações sobre todos os indicadores disponíveis no catálogo.",
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
    module_metadata = {
        1: {
            "nome": "Operações de Navios",
            "fonte_principal": "ANTAQ",
            "descricao": "Indicadores de tempos, características e operações de navios",
        },
        2: {
            "nome": "Operações de Carga",
            "fonte_principal": "ANTAQ",
            "descricao": "Volume, produtividade e utilização de carga",
        },
        3: {
            "nome": "Recursos Humanos",
            "fonte_principal": "RAIS",
            "descricao": "Emprego, salários e perfil dos trabalhadores portuários",
        },
        4: {
            "nome": "Comércio Exterior",
            "fonte_principal": "Comex Stat",
            "descricao": "Exportações, importações e balança comercial",
        },
        5: {
            "nome": "Impacto Econômico Regional",
            "fonte_principal": "IBGE + ANTAQ + RAIS + Comex",
            "descricao": "PIB, população e indicadores econômicos portuários",
        },
        6: {
            "nome": "Finanças Públicas",
            "fonte_principal": "FINBRA/STN",
            "descricao": "Arrecadação municipal e receitas",
        },
        7: {
            "nome": "Índices Sintéticos",
            "fonte_principal": "Múltiplas",
            "descricao": "Índices compostos e rankings",
        },
    }

    module_counts = {}
    for _code, meta in INDICATORS_METADATA.items():
        modulo = meta.get("modulo")
        if modulo not in module_counts:
            module_counts[modulo] = {"total_indicadores": 0, "unctad_compliant": 0}
        module_counts[modulo]["total_indicadores"] += 1
        if meta.get("unctad"):
            module_counts[modulo]["unctad_compliant"] += 1

    modules = []
    for modulo in range(1, 8):
        info = module_metadata.get(modulo, {})
        totals = module_counts.get(modulo, {"total_indicadores": 0, "unctad_compliant": 0})
        modules.append({
            "modulo": modulo,
            "nome": info.get("nome", f"Módulo {modulo}"),
            "total_indicadores": totals["total_indicadores"],
            "unctad_compliant": totals["unctad_compliant"],
            "fonte_principal": info.get("fonte_principal", "Não informada"),
            "descricao": info.get("descricao", ""),
        })

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
