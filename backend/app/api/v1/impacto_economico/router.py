"""
API Endpoints — Módulo Impacto Econômico (Análises Causais).

Expõe operações CRUD para análises causais de impacto econômico portuário:

  POST   /api/v1/impacto-economico/analises
      Cria e executa uma análise (MVP: síncrono). Retorna análise completa.

  GET    /api/v1/impacto-economico/analises
      Lista análises do tenant com paginação e filtros opcionais.

  GET    /api/v1/impacto-economico/analises/{id}
      Retorna status + metadados da análise (sem result_full).

  GET    /api/v1/impacto-economico/analises/{id}/result
      Retorna análise completa incluindo result_full e result_summary.

Isolamento por tenant:
  Todos os endpoints recebem o tenant_id do middleware ``TenantContextMiddleware``
  via ``Depends(get_tenant_id)``. O service propaga esse valor para o Postgres
  (``SET LOCAL app.current_tenant_id``) ativando a policy RLS.

Autenticação:
  Os endpoints protegidos exigem token JWT via ``Depends(get_current_user)``.
  Em modo desenvolvimento (sem token), o middleware usa o tenant default.
"""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_module_permission
from app.core.tenant import get_tenant_id
from app.db.base import get_db
from app.db.models.user import User
from app.schemas.impacto_economico import (
    EconomicImpactAnalysisCreateRequest,
    EconomicImpactAnalysisDetailResponse,
    EconomicImpactAnalysisListResponse,
    EconomicImpactAnalysisResponse,
    MatchingRequest,
    MatchingResponse,
)
from app.services.impacto_economico.analysis_service import (
    AnalysisNotFoundError,
    AnalysisService,
    MethodNotAvailableError,
)
from app.services.audit_service import AuditService, get_audit_service
from app.reports import ReportService
from app.tasks.impacto_economico import run_economic_impact_analysis

router = APIRouter(
    prefix="/impacto-economico",
    tags=["Módulo 5 — Impacto Econômico (Análises Causais)"],
)

# ── Dependency helpers ────────────────────────────────────────────────────────


def _get_analysis_service(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
) -> AnalysisService:
    """Injeta AnalysisService com db + tenant_id do request."""
    return AnalysisService(db=db, tenant_id=tenant_id)


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post(
    "/analises",
    response_model=EconomicImpactAnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Criar Análise Causal (Execução Assíncrona)",
    description="""
Registra uma análise causal de impacto econômico portuário e a enfileira
para execução assíncrona pelo worker Celery.

**Métodos disponíveis:**
- `did` — Difference-in-Differences (Two-Way Fixed Effects com diagnósticos)
- `iv` — Variáveis Instrumentais (2SLS)
- `panel_iv` — Panel IV com within-transformation + efeitos de tempo
- `event_study` — Event study com janela pre/post
- `compare` — Executa DiD + IV e compara consistência dos resultados

**Métodos experimentais (retornam 501 até habilitação):**
- `scm` — Synthetic Control Method (requer `ENABLE_SCM=true` + módulo portado)
- `augmented_scm` — Augmented SCM/Ben-Michael 2021 (requer `ENABLE_AUGMENTED_SCM=true`)

**Fluxo assíncrono (PR-06):**
A resposta retorna imediatamente com `status: queued`.
O worker processa a análise em background e atualiza o status para
`running → success | failed`.
Consulte o progresso via `GET /analises/{id}` e o resultado via
`GET /analises/{id}/result`.

**Isolamento:** cada análise fica vinculada ao tenant do token JWT.
""",
    responses={
        202: {"description": "Análise aceita para processamento (status=queued)."},
        400: {"description": "Parâmetros inválidos."},
        422: {"description": "Erro de validação nos dados de entrada."},
        500: {"description": "Erro ao persistir análise ou enfileirar task."},
    },
)
async def create_analysis(
    body: EconomicImpactAnalysisCreateRequest,
    service: AnalysisService = Depends(_get_analysis_service),
    audit_service: AuditService = Depends(get_audit_service),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_module_permission(5, "execute")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
) -> EconomicImpactAnalysisResponse:
    """
    Registra a análise com status='queued' e despacha para o worker Celery.

    Retorna imediatamente com `status: queued` e o `id` da análise para
    polling posterior via GET /analises/{id}.
    """
    try:
        analysis = await service.create_queued(
            request=body,
            user_id=current_user.id,
        )
        await audit_service.record_action(
            db=db,
            tenant_id=tenant_id,
            user_id=current_user.id,
            action="create_analysis",
            resource="/api/v1/impacto-economico/analises",
            status_code=202,
            details={
                "method": body.method,
                "analysis_id": str(analysis.id),
                "tenant_id": str(tenant_id),
            },
        )
    except MethodNotAvailableError as exc:
        # Método experimental com feature flag desabilitada → 501 Not Implemented
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar análise: {exc}",
        )

    # Despacha execução para o worker Celery (não bloqueante)
    run_economic_impact_analysis.delay(str(analysis.id), str(tenant_id))

    return analysis


@router.post(
    "/matching",
    response_model=MatchingResponse,
    status_code=status.HTTP_200_OK,
    summary="Sugerir controles por matching",
    description="""
    Gera sugestão de controles estatisticamente comparáveis para SCM/ASCM.

    O matching usa distância no pré-tratamento considerando features
    econômicas do painel de impacto em nível municipal.
    """,
)
async def suggest_controls(
    body: MatchingRequest,
    _: User = Depends(require_module_permission(5, "execute")),
) -> MatchingResponse:
    """Endpoint de apoio ao frontend para preencher control_ids automaticamente."""
    from app.services.impacto_economico.causal.matching import suggest_control_matches

    result = await suggest_control_matches(
        treated_ids=body.treated_ids,
        treatment_year=body.treatment_year,
        scope=body.scope,
        n_controls=body.n_controls,
        ano_inicio=body.ano_inicio,
        ano_fim=body.ano_fim,
        features=body.features,
    )

    return MatchingResponse.model_validate(result)


@router.get(
    "/analises",
    response_model=EconomicImpactAnalysisListResponse,
    summary="Listar Análises do Tenant",
    description="""
Lista todas as análises causais do tenant corrente com paginação.

**Filtros opcionais:**
- `status`: queued | running | success | failed
- `method`: did | iv | panel_iv | event_study | compare
- `page` / `page_size`: paginação (default 1 / 20)

**Isolamento:** retorna apenas análises do tenant do token JWT.
""",
)
async def list_analyses(
    page: Annotated[int, Query(ge=1, description="Página (base 1)")] = 1,
    page_size: Annotated[
        int, Query(ge=1, le=100, description="Itens por página")
    ] = 20,
    status_filter: Annotated[
        str | None,
        Query(
            alias="status",
            description="Filtrar por status: queued | running | success | failed",
        ),
    ] = None,
    method_filter: Annotated[
        str | None,
        Query(
            alias="method",
            description="Filtrar por método: did | iv | panel_iv | event_study | compare",
        ),
    ] = None,
    service: AnalysisService = Depends(_get_analysis_service),
    _: User = Depends(require_module_permission(5, "read")),
) -> EconomicImpactAnalysisListResponse:
    """Lista análises do tenant com paginação e filtros opcionais."""
    return await service.list_analyses(
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        method_filter=method_filter,
    )


@router.get(
    "/analises/{analysis_id}",
    response_model=EconomicImpactAnalysisResponse,
    summary="Consultar Status da Análise",
    description="""
Retorna o status atual e metadados de uma análise.

**Não inclui** `result_full` (use `/result` para o resultado completo).

Útil para polling de progresso em implementações futuras com worker assíncrono.
""",
    responses={
        200: {"description": "Análise encontrada."},
        404: {"description": "Análise não encontrada ou pertence a outro tenant."},
    },
)
async def get_analysis_status(
    analysis_id: uuid.UUID,
    service: AnalysisService = Depends(_get_analysis_service),
    _: User = Depends(require_module_permission(5, "read")),
) -> EconomicImpactAnalysisResponse:
    """Retorna status e metadados básicos da análise (sem resultado completo)."""
    try:
        return await service.get_status(analysis_id)
    except AnalysisNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get(
    "/analises/{analysis_id}/result",
    response_model=EconomicImpactAnalysisDetailResponse,
    summary="Resultado Completo da Análise",
    description="""
Retorna a análise completa incluindo:
- `result_summary`: métricas principais (coef ATT, p-value, IC, n_obs)
- `result_full`: payload completo do engine causal (event study, placebo,
  sensitivity, specifications, warnings)
- `artifact_path`: URI GCS quando resultado foi salvo externamente (> 512 KB)
- `duration_seconds`: tempo de execução

**Nota:** `result_full` pode ser omitido para análises grandes
(consulte `artifact_path` nesse caso).
""",
    responses={
        200: {"description": "Resultado da análise."},
        404: {"description": "Análise não encontrada ou pertence a outro tenant."},
        409: {"description": "Análise ainda não concluída."},
    },
)
async def get_analysis_result(
    analysis_id: uuid.UUID,
    service: AnalysisService = Depends(_get_analysis_service),
    _: User = Depends(require_module_permission(5, "read")),
) -> EconomicImpactAnalysisDetailResponse:
    """Retorna análise completa com resultado do engine causal."""
    try:
        detail = await service.get_detail(analysis_id)
    except AnalysisNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if detail.status in ("queued", "running"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Análise ainda em execução (status='{detail.status}'). "
                "Aguarde a conclusão antes de consultar o resultado."
            ),
        )

    return detail


@router.get(
    "/analises/{analysis_id}/report",
    summary="Gerar Relatório DOCX da Análise",
    description="""
Gera e retorna um relatório DOCX consolidado para uma análise causal.

O relatório inclui:
- Metadados da análise (método, status, período, escopo)
- Resultado principal e detalhamento por outcome
- Diagnósticos principais (parallel trends, first-stage, comparação metodológica)
""",
    responses={
        200: {"description": "Relatório DOCX gerado com sucesso."},
        404: {"description": "Análise não encontrada ou pertence a outro tenant."},
        409: {"description": "Relatório disponível apenas para análises com status=success."},
        500: {"description": "Falha ao gerar o relatório."},
    },
)
async def get_analysis_report(
    analysis_id: uuid.UUID,
    service: AnalysisService = Depends(_get_analysis_service),
    _: User = Depends(require_module_permission(5, "read")),
) -> StreamingResponse:
    """Gera e retorna o relatório DOCX de uma análise causal."""
    try:
        detail = await service.get_detail(analysis_id)
    except AnalysisNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao carregar análise: {exc}",
        )

    if detail.status != "success":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Relatório disponível apenas para análises concluídas com sucesso. "
                f"Status atual: {detail.status}"
            ),
        )

    try:
        report_service = ReportService()
        report_bytes, filename = report_service.generate_impact_analysis_report(detail)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Não foi possível gerar relatório: {exc}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar relatório: {exc}",
        )

    return StreamingResponse(
        content=iter([report_bytes.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
