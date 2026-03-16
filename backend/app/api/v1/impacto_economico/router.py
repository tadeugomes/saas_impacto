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

import math
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Annotated, Any, Literal, Optional

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
    ImpactSimulationRequest,
    ImpactSimulationResponse,
    ImpactSimulationProjection,
    MatchingRequest,
    MatchingResponse,
)
from app.services.impacto_economico.analysis_service import (
    AnalysisNotFoundError,
    AnalysisService,
)
from app.services.audit_service import AuditService, get_audit_service
from app.reports import ReportService
from app.reports import PDFGenerator, XLSXGenerator
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

- `scm` — Synthetic Control Method (implementação local)
- `augmented_scm` — Augmented SCM/Ben-Michael 2021 (implementação local)

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
        Optional[str],
        Query(
            alias="status",
            description="Filtrar por status: queued | running | success | failed",
        ),
    ] = None,
    method_filter: Annotated[
        Optional[str],
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

    result_full, result_warnings = _resolve_simulation_result_payload(detail)
    result_summary = dict(detail.result_summary or {})
    if result_warnings:
        warnings = result_summary.get("warnings")
        if isinstance(warnings, list):
            merged_warnings = [str(item) for item in warnings if isinstance(item, str)]
        else:
            merged_warnings = []

        for warning in result_warnings:
            warning_text = str(warning)
            if warning_text and warning_text not in merged_warnings:
                merged_warnings.append(warning_text)

        if merged_warnings:
            result_summary["warnings"] = merged_warnings

    return EconomicImpactAnalysisDetailResponse(
        id=detail.id,
        tenant_id=detail.tenant_id,
        user_id=detail.user_id,
        status=detail.status,
        method=detail.method,
        created_at=detail.created_at,
        updated_at=detail.updated_at,
        started_at=detail.started_at,
        completed_at=detail.completed_at,
        duration_seconds=detail.duration_seconds,
        request_params=detail.request_params,
        result_summary=result_summary if result_summary else None,
        result_full=result_full if isinstance(result_full, dict) and result_full else None,
        artifact_path=detail.artifact_path,
        error_message=detail.error_message,
    )


@router.post(
    "/analises/{analysis_id}/simulacao",
    response_model=ImpactSimulationResponse,
    summary="Simular impacto de cenário a partir da análise causal",
    description="""
Transforma um resultado causal executado em simulação gerencial.

Fluxo:
- O parâmetro `shock_intensity_pct` define a intensidade do choque (em %).
- O impacto de referência (ex.: `toneladas_antaq_log`) é usado para converter o choque.
- Os demais outcomes projetados usam a elasticidade implícita em relação à referência.
""",
    responses={
        200: {"description": "Simulação calculada com sucesso."},
        400: {"description": "Parâmetros inválidos para simulação."},
        404: {"description": "Análise não encontrada ou pertence a outro tenant."},
        409: {"description": "Análise ainda não concluída."},
    },
)
async def simulate_impact(
    analysis_id: uuid.UUID,
    body: ImpactSimulationRequest,
    service: AnalysisService = Depends(_get_analysis_service),
    _: User = Depends(require_module_permission(5, "read")),
) -> ImpactSimulationResponse:
    """Executa simulação de impacto com base nos coeficientes da análise."""
    try:
        detail = await service.get_detail(analysis_id)
    except AnalysisNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    if detail.status in ("queued", "running"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Análise ainda em execução (status='{detail.status}'). "
                "Execute a simulação após a conclusão."
            ),
        )

    result_full, simulation_warnings = _resolve_simulation_result_payload(detail)
    if not isinstance(result_full, dict) or not result_full:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A análise não possui resultado causal disponível para simulação.",
        )

    if detail.method == "compare":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Simulação não suportada para o método 'compare'.",
        )

    result_outcomes = [
        key
        for key, value in result_full.items()
        if isinstance(value, dict) and key not in {"comparison", "metadata"}
    ]

    requested = body.target_outcomes or result_outcomes
    normalized_requested = [str(v).strip() for v in requested if isinstance(v, str)]
    if not normalized_requested:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="target_outcomes vazio e análise sem outcomes disponíveis.",
        )

    reference_outcome = (body.reference_outcome or "toneladas_antaq_log").strip()
    if reference_outcome not in result_full:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Outcome de referência '{reference_outcome}' não encontrado na análise.",
        )

    applied_shock_intensity_pct = body.shock_intensity_pct
    if body.shock_mode == "investment":
        if body.investment_to_movement_elasticity is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "investment_to_movement_elasticity é obrigatório "
                    "quando shock_mode='investment'."
                ),
            )
        applied_shock_intensity_pct *= body.investment_to_movement_elasticity

    shock_ratio = applied_shock_intensity_pct / 100.0

    reference_payload = _extract_outcome_payload(result_full.get(reference_outcome))
    reference_effect = _to_percentage(reference_payload["coef"], reference_outcome)
    reference_ci_lower = _to_percentage(
        reference_payload["ci_lower"],
        reference_outcome,
    )
    reference_ci_upper = _to_percentage(
        reference_payload["ci_upper"],
        reference_outcome,
    )

    if reference_effect is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Não foi possível extrair o coeficiente do outcome de referência "
                f"'{reference_outcome}'."
            ),
        )

    if body.shock_mode == "investment":
        assumptions = [
            "Modo selecionado: investimento (duas etapas).",
            "Modelo causal usado como aproximação de efeito médio no recorte escolhido.",
            "Assume proporcionalidade entre impacto de investimento em movimentação e o efeito estimado (escala linear).",
            "A simulação usa a relação implícita entre outcome de referência e outcome projetado.",
        ]
    else:
        assumptions = [
            "Modo selecionado: movimentação.",
            "Modelo causal usado como aproximação de efeito médio no recorte escolhido.",
            "Assume proporcionalidade entre intensidade do choque e o efeito estimado (escala linear).",
            "A simulação usa a relação implícita entre outcome de referência e outcome projetado.",
        ]

    mode_description = (
        f"{body.shock_intensity_pct:.1f}% de investimento "
        f"({applied_shock_intensity_pct:.1f}% equivalente em movimentação)"
        if body.shock_mode == "investment"
        else f"{body.shock_intensity_pct:.1f}% de movimentação"
    )
    projections: list[ImpactSimulationProjection] = []
    metadata_notes = list(simulation_warnings)
    if detail.method:
        metadata_notes.append(f"Método causal de origem: {detail.method}.")
    if detail.status:
        metadata_notes.append(f"Status da análise origem: {detail.status}.")
    if detail.request_params:
        metadata_notes.append(
            "Parâmetros de modelagem do tratamento carregados a partir da análise."
        )
    if not metadata_notes:
        metadata_notes = ["Resultado de simulação derivado diretamente do output causal."]

    for outcome in normalized_requested:
        if outcome not in result_full:
            projections.append(
                ImpactSimulationProjection(
                    outcome=outcome,
                    outcome_label=_pretty_outcome_label(outcome),
                    treatment_effect_100pct=None,
                    projected_delta_pct=None,
                    method_used="sem dado",
                    confidence="fraca",
                    warning="Outcome não encontrado no result_full.",
                ),
            )
            continue

        payload = _extract_outcome_payload(result_full.get(outcome))
        coef = payload["coef"]
        p_value = payload["p_value"]
        n_obs = payload["n_obs"]
        std_err = payload["std_err"]
        ci_lower = payload["ci_lower"]
        ci_upper = payload["ci_upper"]
        outcome_notes = list(payload.get("notes", []))
        effect_100pct = _to_percentage(coef, outcome)
        effect_100pct_ci_lower = _to_percentage(ci_lower, outcome)
        effect_100pct_ci_upper = _to_percentage(ci_upper, outcome)

        if effect_100pct is None:
            projections.append(
                ImpactSimulationProjection(
                    outcome=outcome,
                    outcome_label=_pretty_outcome_label(outcome),
                    treatment_effect_100pct=None,
                    projected_delta_pct=None,
                    method_used="sem dado",
                    std_err=std_err,
                    p_value=p_value,
                    confidence=_impact_confidence(p_value, n_obs),
                    treatment_effect_100pct_ci_lower=None,
                    treatment_effect_100pct_ci_upper=None,
                    projected_delta_pct_conservative=None,
                    projected_delta_pct_optimistic=None,
                    notes=(
                        outcome_notes
                        if outcome_notes
                        else ["Sem intervalo de confiança disponível para este outcome."]
                    ),
                    warning="Coeficiente sem mapeamento para projeção percentual.",
                ),
            )
            continue

        if outcome == reference_outcome:
            projected = effect_100pct * shock_ratio
            method = f"escala direta ({reference_outcome})"
            warning = None
            projected_delta_pct_conservative, projected_delta_pct_optimistic = (
                _bound_from_interval(
                    effect_100pct_ci_lower,
                    effect_100pct_ci_upper,
                    shock_ratio,
                )
                if effect_100pct_ci_lower is not None
                and effect_100pct_ci_upper is not None
                else (None, None)
            )
        else:
            method = "encadeamento relativo"
            if reference_effect == 0:
                projected = None
                projected_delta_pct_conservative = None
                projected_delta_pct_optimistic = None
                warning = "Outcome de referência com efeito 0: impossibilidade de cadeia proporcional."
            else:
                ratio = effect_100pct / reference_effect
                projected = reference_effect * shock_ratio * ratio
                warning = None
                if (
                    effect_100pct_ci_lower is not None
                    and effect_100pct_ci_upper is not None
                    and reference_ci_lower is not None
                    and reference_ci_upper is not None
                ):
                    candidate_values: list[float] = []
                    for outcome_candidate in (
                        effect_100pct_ci_lower,
                        effect_100pct_ci_upper,
                    ):
                        for reference_candidate in (reference_ci_lower, reference_ci_upper):
                            if reference_candidate == 0:
                                continue
                            candidate_values.append(
                                reference_effect
                                * shock_ratio
                                * (outcome_candidate / reference_candidate)
                            )
                    if candidate_values:
                        projected_delta_pct_conservative = min(candidate_values)
                        projected_delta_pct_optimistic = max(candidate_values)
                    else:
                        projected_delta_pct_conservative = None
                        projected_delta_pct_optimistic = None
                else:
                    projected_delta_pct_conservative = None
                    projected_delta_pct_optimistic = None

        if not outcome_notes and std_err is None:
            outcome_notes = ["Simulação baseada em coeficiente com ci não informado."]

        projection = ImpactSimulationProjection(
            outcome=outcome,
            outcome_label=_pretty_outcome_label(outcome),
            treatment_effect_100pct=round(effect_100pct, 6),
            projected_delta_pct=round(projected, 6) if projected is not None else None,
            method_used=method,
            coef=coef,
            std_err=std_err,
            p_value=p_value,
            confidence=_impact_confidence(p_value, n_obs),
            treatment_effect_100pct_ci_lower=(
                round(effect_100pct_ci_lower, 6)
                if effect_100pct_ci_lower is not None
                else None
            ),
            treatment_effect_100pct_ci_upper=(
                round(effect_100pct_ci_upper, 6)
                if effect_100pct_ci_upper is not None
                else None
            ),
            projected_delta_pct_conservative=(
                round(projected_delta_pct_conservative, 6)
                if projected_delta_pct_conservative is not None
                else None
            ),
            projected_delta_pct_optimistic=(
                round(projected_delta_pct_optimistic, 6)
                if projected_delta_pct_optimistic is not None
                else None
            ),
            notes=outcome_notes,
            warning=warning,
        )
        projections.append(projection)

    executive_summary: list[str] = []
    for projection in projections:
        if projection.projected_delta_pct is None:
            executive_summary.append(
                f"{projection.outcome_label}: não foi possível simular por ausência de coeficiente compatível."
            )
            continue

        delta = projection.projected_delta_pct
        direction = "aumenta" if delta >= 0 else "reduz"
        abs_delta = abs(delta)
        if projection.projected_delta_pct_conservative is not None:
            conf_range = (
                f"({projection.projected_delta_pct_conservative:.4f}% "
                f"a {projection.projected_delta_pct_optimistic:.4f}%)"
            )
        else:
            conf_range = "sem faixa de incerteza disponível."
        executive_summary.append(
            f"Com {mode_description}, {projection.outcome_label} "
            f"tem variação estimada de {abs_delta:.4f}% {direction} no mesmo sentido do coeficiente "
            f"estimado. Faixa conservador/otimista: {conf_range}"
        )

    model_version = "simulador_impacto_v1"
    metadata_payload = result_full.get("metadata")
    if isinstance(metadata_payload, dict):
        candidate_version = metadata_payload.get("model_version")
        if isinstance(candidate_version, str) and candidate_version.strip():
            model_version = candidate_version.strip()

    return ImpactSimulationResponse(
        analysis_id=analysis_id,
        method=detail.method,
        shock_intensity_pct=body.shock_intensity_pct,
        shock_mode=body.shock_mode,
        applied_shock_intensity_pct=applied_shock_intensity_pct,
        investment_to_movement_elasticity=body.investment_to_movement_elasticity,
        reference_outcome=reference_outcome,
        reference_effect_100pct=round(reference_effect, 6),
        projected_outcomes=projections,
        simulation_metadata={
            "as_of": datetime.utcnow(),
            "model_version": model_version,
            "generated_by": "impacto_economico_router",
            "notes": metadata_notes,
        },
        assumptions=assumptions,
        executive_summary=executive_summary,
    )


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
    format: Literal["docx", "pdf", "xlsx"] = Query(default="docx"),
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
        if format == "docx":
            report_service = ReportService()
            report_bytes, filename = report_service.generate_impact_analysis_report(detail)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif format == "pdf":
            impact_data: list[dict[str, Any]] = _normalize_impact_rows(detail)
            report_bytes, filename = PDFGenerator().build(
                title=f"Relatório de Impacto Econômico - {analysis_id}",
                subtitle=f"Método: {detail.method}",
                rows=impact_data,
                output_name=f"relatorio_impacto_{analysis_id}.pdf",
            )
            media_type = "application/pdf"
        elif format == "xlsx":
            impact_data: list[dict[str, Any]] = _normalize_impact_rows(detail)
            report_bytes, filename = XLSXGenerator().build_single_indicator(
                code=f"impacto_economico_{detail.method}",
                rows=impact_data,
                output_name=f"relatorio_impacto_{analysis_id}.xlsx",
            )
            media_type = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato inválido: {format}",
            )
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
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


def _normalize_impact_rows(detail: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    summary = getattr(detail, "result_summary", None) or {}
    if summary:
        rows.append(
            {
                "outcome": summary.get("outcome", "N/A"),
                "coef": summary.get("coef"),
                "std_err": summary.get("std_err"),
                "p_value": summary.get("p_value"),
                "n_obs": summary.get("n_obs"),
                "metodo": detail.method,
            }
        )

    if summary.get("outcome") is None:
        rows.append(
            {
                "metodo": detail.method,
                "status": detail.status,
            }
        )

    return rows


def _to_float(value: Any) -> float | None:
    """Converte valores JSON/string em float, ignorando inválidos."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            parsed = float(value.replace(",", "."))
        except ValueError:
            return None
        return parsed
    return None


def _to_percentage(coef: float | None, outcome: str) -> float | None:
    """
    Normaliza coeficiente para efeito percentual associado ao cenário de 100%.

    Para outcomes log (sufixo _log), usa transformação semi-elástica:
    (exp(coef) - 1)*100.
    Para outcomes não log, assume variação aproximada em % por unidade de tratamento.
    """
    if coef is None:
        return None
    if not isinstance(coef, (int, float)):
        return None
    if not math.isfinite(float(coef)):
        return None

    if outcome.endswith("_log"):
        return (math.exp(float(coef)) - 1.0) * 100.0
    return float(coef) * 100.0


def _to_float_or_none(value: Any) -> float | None:
    """Tenta converter diferentes tipos numéricos para float, ignorando inválidos."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        parsed = float(value)
        return parsed if math.isfinite(parsed) else None
    if isinstance(value, str):
        parsed = _to_float(value)
        return parsed
    return None


def _load_simulation_artifact_result(payload_path: str) -> tuple[dict[str, Any], list[str]]:
    """Carrega JSON de artifact de resultado causal para simulação."""
    path = (payload_path or "").strip()
    if not path:
        return {}, ["artifact_path vazio; sem payload inline disponível."]

    if path.startswith("file://"):
        path = path[7:]

    if path.startswith("gs://"):
        try:
            from google.cloud import storage  # type: ignore
        except Exception:
            return {}, [
                "Dependência google-cloud-storage não instalada: "
                "resultado causal completo não carregado para simulação."
            ]

        try:
            _, bucket_and_blob = path.split("gs://", 1)
            bucket_name, blob_name = bucket_and_blob.split("/", 1)
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            content = blob.download_as_text()
            payload = json.loads(content)
        except Exception as exc:  # noqa: BLE001
            return {}, [f"Falha ao carregar artifact_path GCS {path}: {exc}"]

        if isinstance(payload, dict):
            return payload, []
        return {}, [f"artifact_path GCS com formato inválido (não é JSON object): {path}"]

    local_path = Path(path)
    if not local_path.is_absolute():
        local_path = local_path.resolve()

    if not local_path.exists():
        return {}, [f"artifact_path não encontrado: {path}"]

    try:
        payload = json.loads(local_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {}, [f"Falha ao ler artifact_path {path}: {exc}"]

    if isinstance(payload, dict):
        return payload, []
    return {}, [f"artifact_path com formato inválido (não é JSON object): {path}"]


def _resolve_simulation_result_payload(
    detail: Any,
) -> tuple[dict[str, Any], list[str]]:
    """Resolve `result_full`, com fallback para `artifact_path` quando necessário."""
    result_full = getattr(detail, "result_full", None)
    if isinstance(result_full, dict) and result_full:
        return result_full, []

    artifact_path = getattr(detail, "artifact_path", None)
    if not artifact_path:
        return {}, []

    payload, warnings = _load_simulation_artifact_result(str(artifact_path))
    if payload:
        warnings = [*warnings, "Resultado causal carregado via artifact_path para simulação."]
    return payload, warnings


def _bound_from_interval(
    lower: float | None,
    upper: float | None,
    scale: float,
) -> tuple[float | None, float | None]:
    if lower is None or upper is None:
        return None, None
    candidate_low = lower * scale
    candidate_high = upper * scale
    return (
        candidate_low if candidate_low <= candidate_high else candidate_high,
        candidate_high if candidate_low <= candidate_high else candidate_low,
    )


def _impact_confidence(p_value: float | None, n_obs: int | None) -> str:
    if p_value is not None and p_value < 0.05 and (n_obs is None or n_obs >= 30):
        return "forte"
    if p_value is not None and p_value < 0.10:
        return "moderada"
    return "fraca"


def _pretty_outcome_label(outcome: str) -> str:
    names = {
        "pib_log": "PIB Municipal",
        "pib_per_capita_log": "Renda per Capita",
        "n_vinculos_log": "Empregos no Setor Portuário",
        "empregos_totais_log": "Empregos Totais do Município",
        "toneladas_antaq_log": "Movimentação de Carga",
        "comercio_dolar_log": "Comércio Exterior",
        "exportacao_dolar_log": "Exportações",
        "importacao_dolar_log": "Importações",
        "massa_salarial_total_log": "Massa Salarial Total",
        "massa_salarial_portuaria_log": "Massa Salarial Portuária",
        "populacao_log": "População",
    }
    return names.get(outcome, outcome.replace("_", " ").title())


def _extract_outcome_payload(
    section: Any,
) -> dict[str, float | None | list[str]]:
    """
    Extrai coeficiente principal e diagnósticos de uma seção de outcome.
    Compatível com did/iv/event_study/iv_panel/scm/augmented_scm.
    """
    if not isinstance(section, dict):
        return {
            "coef": None,
            "std_err": None,
            "p_value": None,
            "ci_lower": None,
            "ci_upper": None,
            "n_obs": None,
            "method": "outros",
            "notes": [],
        }

    main = section.get("main_result")
    if isinstance(main, dict):
        candidate = main
        method = "main_result"
    else:
        candidate = section
        method = "outcome_dict"

    coef = _to_float(candidate.get("coef", candidate.get("att")))
    std_err = _to_float(candidate.get("std_err"))
    p_value = _to_float(candidate.get("p_value", candidate.get("pvalue")))
    ci_lower = _to_float(candidate.get("ci_lower"))
    ci_upper = _to_float(candidate.get("ci_upper"))
    n_obs = candidate.get("n_obs")
    if n_obs is not None and isinstance(n_obs, (int, float)):
        n_obs = int(n_obs)

    # fallback: event study pode expor coeficientes por período
    if coef is None:
        coefficients = candidate.get("coefficients", section.get("coefficients"))
        if isinstance(coefficients, list) and coefficients:
            event_point = next(
                (point for point in coefficients if isinstance(point, dict) and point.get("rel_time") == 0),
                None,
            )
            if isinstance(event_point, dict):
                coef = _to_float(event_point.get("coef"))
                p_value = _to_float(
                    event_point.get("pvalue", event_point.get("p_value"))
                )
                std_err = _to_float(event_point.get("std_err", event_point.get("se")))
                ci_lower = _to_float(
                    event_point.get("ci_lower", event_point.get("ciLower"))
                )
                ci_upper = _to_float(
                    event_point.get("ci_upper", event_point.get("ciUpper"))
                )
                method = "event_study_rel0"

    notes = []
    section_notes = section.get("notes")
    if isinstance(section_notes, list):
        notes.extend([str(note) for note in section_notes if str(note).strip()])

    if isinstance(main, dict):
        main_notes = main.get("notes")
        if isinstance(main_notes, list):
            notes.extend([str(note) for note in main_notes if str(note).strip()])

    return {
        "coef": coef,
        "std_err": std_err,
        "p_value": p_value,
        "n_obs": int(n_obs) if isinstance(n_obs, int) else None,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "method": method,
        "notes": notes,
    }
