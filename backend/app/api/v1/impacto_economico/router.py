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

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.security import decode_access_token
from app.core.tenant import get_tenant_id
from app.db.base import get_db
from app.db.models.user import User
from app.schemas.impacto_economico import (
    EconomicImpactAnalysisCreateRequest,
    EconomicImpactAnalysisDetailResponse,
    EconomicImpactAnalysisListResponse,
    EconomicImpactAnalysisResponse,
)
from app.services.impacto_economico.analysis_service import (
    AnalysisNotFoundError,
    AnalysisService,
)
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


def _extract_user_id(request: Request) -> uuid.UUID | None:
    """Extrai user_id do JWT, sem falhar se ausente."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        payload = decode_access_token(auth_header[7:])
        if payload and payload.get("sub"):
            try:
                return uuid.UUID(str(payload["sub"]))
            except (ValueError, AttributeError):
                pass
    return None


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
    http_request: Request,
    service: AnalysisService = Depends(_get_analysis_service),
    current_user: User = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
) -> EconomicImpactAnalysisResponse:
    """
    Registra a análise com status='queued' e despacha para o worker Celery.

    Retorna imediatamente com `status: queued` e o `id` da análise para
    polling posterior via GET /analises/{id}.
    """
    user_id = _extract_user_id(http_request)

    try:
        analysis = await service.create_queued(
            request=body,
            user_id=user_id or (current_user.id if current_user else None),
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
    _: User = Depends(get_current_user),
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
    _: User = Depends(get_current_user),
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
    _: User = Depends(get_current_user),
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
