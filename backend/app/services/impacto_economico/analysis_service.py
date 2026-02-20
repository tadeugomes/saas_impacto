"""
Orquestrador de Análises de Impacto Econômico.

``EconomicImpactAnalysisService`` é o único ponto de entrada para disparar
e recuperar análises causais. Ele coordena:

  1. Criação do registro ``EconomicImpactAnalysis`` no Postgres (status=queued)
  2. Busca e construção do painel via ``EconomicImpactPanelBuilder`` (BigQuery)
  3. Execução do engine causal adequado ao método solicitado
  4. Serialização do resultado via ``serialize_causal_result``
  5. Persistência do resultado e atualização de status (success/failed)
  6. Consulta de registros respeitando RLS por tenant

Estratégia de execução (MVP):
  A execução roda de forma síncrona inline (aguarda conclusão antes de
  responder). O PR-06 irá substituir este fluxo por um worker assíncrono
  (Celery/ARQ), mantendo a interface deste service inalterada.

RLS:
  Antes de qualquer operação na tabela ``economic_impact_analyses``,
  o serviço seta ``SET LOCAL app.current_tenant_id = '<uuid>'`` na sessão
  Postgres, ativando a policy de Row Level Security.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.economic_impact_analysis import EconomicImpactAnalysis
from app.schemas.impacto_economico import (
    EconomicImpactAnalysisCreateRequest,
    EconomicImpactAnalysisDetailResponse,
    EconomicImpactAnalysisListResponse,
    EconomicImpactAnalysisResponse,
)
from app.services.impacto_economico.causal.serialize import serialize_causal_result

logger = logging.getLogger(__name__)

# ── Tamanho máximo do payload inline (bytes JSON estimados) ──────────────────
_MAX_INLINE_BYTES = 512 * 1024  # 512 KB → acima disso, usar artifact_path


class AnalysisNotFoundError(LookupError):
    """Análise não encontrada (ou pertence a outro tenant)."""


class AnalysisService:
    """
    Orquestrador de análises causais de impacto econômico.

    Parameters
    ----------
    db:
        Sessão assíncrona do Postgres (injetada pelo FastAPI).
    tenant_id:
        UUID do tenant corrente; usado para setar o contexto RLS.
    """

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._db = db
        self._tenant_id = tenant_id

    # ──────────────────────────────────────────────────────────────────────────
    # Operações de escrita
    # ──────────────────────────────────────────────────────────────────────────

    async def create_and_run(
        self,
        request: EconomicImpactAnalysisCreateRequest,
        user_id: uuid.UUID | None = None,
    ) -> EconomicImpactAnalysisDetailResponse:
        """Cria, executa e persiste uma análise causal.

        Fluxo MVP (síncrono):
          queued → running → (success | failed)

        Returns
        -------
        EconomicImpactAnalysisDetailResponse com status final.
        """
        analysis = await self._create_queued(request, user_id)
        analysis = await self._execute(analysis, request)
        return EconomicImpactAnalysisDetailResponse.from_orm_instance(analysis)

    async def create_queued(
        self,
        request: EconomicImpactAnalysisCreateRequest,
        user_id: uuid.UUID | None = None,
    ) -> EconomicImpactAnalysisResponse:
        """Cria análise com status=queued sem executar (para workers).

        Usado quando PR-06 implementar execução assíncrona.

        Returns
        -------
        EconomicImpactAnalysisResponse com status='queued'.
        """
        analysis = await self._create_queued(request, user_id)
        return EconomicImpactAnalysisResponse.model_validate(analysis)

    # ──────────────────────────────────────────────────────────────────────────
    # Operações de leitura
    # ──────────────────────────────────────────────────────────────────────────

    async def get_status(self, analysis_id: uuid.UUID) -> EconomicImpactAnalysisResponse:
        """Retorna status da análise (sem resultado completo)."""
        analysis = await self._fetch(analysis_id)
        return EconomicImpactAnalysisResponse.model_validate(analysis)

    async def get_detail(
        self, analysis_id: uuid.UUID
    ) -> EconomicImpactAnalysisDetailResponse:
        """Retorna análise completa com resultado."""
        analysis = await self._fetch(analysis_id)
        return EconomicImpactAnalysisDetailResponse.from_orm_instance(analysis)

    async def list_analyses(
        self,
        page: int = 1,
        page_size: int = 20,
        status_filter: str | None = None,
        method_filter: str | None = None,
    ) -> EconomicImpactAnalysisListResponse:
        """Lista análises do tenant com paginação e filtros opcionais."""
        await self._set_rls_context()

        stmt = select(EconomicImpactAnalysis).where(
            EconomicImpactAnalysis.tenant_id == self._tenant_id
        )

        if status_filter:
            stmt = stmt.where(EconomicImpactAnalysis.status == status_filter)
        if method_filter:
            stmt = stmt.where(EconomicImpactAnalysis.method == method_filter)

        # Total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._db.execute(count_stmt)).scalar_one()

        # Página
        stmt = (
            stmt.order_by(EconomicImpactAnalysis.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self._db.execute(stmt)).scalars().all()

        return EconomicImpactAnalysisListResponse(
            total=total,
            items=[
                EconomicImpactAnalysisResponse.model_validate(r) for r in rows
            ],
            page=page,
            page_size=page_size,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers internos
    # ──────────────────────────────────────────────────────────────────────────

    async def _set_rls_context(self) -> None:
        """Ativa a policy RLS na sessão corrente.

        ``SET LOCAL`` garante que a variável seja resetada no fim da transação,
        sem vazar para outras sessões do pool.
        """
        await self._db.execute(
            text("SET LOCAL app.current_tenant_id = :tid"),
            {"tid": str(self._tenant_id)},
        )

    async def _create_queued(
        self,
        request: EconomicImpactAnalysisCreateRequest,
        user_id: uuid.UUID | None,
    ) -> EconomicImpactAnalysis:
        """Persiste registro inicial com status='queued'."""
        await self._set_rls_context()

        analysis = EconomicImpactAnalysis(
            id=uuid.uuid4(),
            tenant_id=self._tenant_id,
            user_id=user_id,
            method=request.method,
            status="queued",
            request_params=request.model_dump(mode="json"),
        )
        self._db.add(analysis)
        await self._db.commit()
        await self._db.refresh(analysis)

        logger.info(
            "Análise criada: id=%s method=%s tenant=%s",
            analysis.id,
            analysis.method,
            self._tenant_id,
        )
        return analysis

    async def _execute(
        self,
        analysis: EconomicImpactAnalysis,
        request: EconomicImpactAnalysisCreateRequest,
    ) -> EconomicImpactAnalysis:
        """Executa o pipeline causal e persiste o resultado."""
        await self._set_rls_context()
        analysis.mark_running()
        await self._db.commit()

        try:
            result_full = await self._run_causal_pipeline(request)
            result_summary = _extract_summary(result_full, request)

            # Decide persistência inline vs artifact
            import json
            payload_size = len(json.dumps(result_full, default=str).encode())
            if payload_size > _MAX_INLINE_BYTES:
                analysis.mark_success(
                    result_summary=result_summary,
                    result_full=None,
                    artifact_path=None,  # PR-06 implementa upload GCS
                )
                logger.warning(
                    "Resultado grande (%d bytes); result_full omitido inline. "
                    "artifact_path será preenchido pelo worker GCS no PR-06.",
                    payload_size,
                )
            else:
                analysis.mark_success(
                    result_summary=result_summary,
                    result_full=result_full,
                )

        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"
            logger.exception("Falha na análise %s: %s", analysis.id, error_msg)
            analysis.mark_failed(error_msg)

        await self._set_rls_context()
        await self._db.commit()
        await self._db.refresh(analysis)
        return analysis

    async def _fetch(self, analysis_id: uuid.UUID) -> EconomicImpactAnalysis:
        """Busca análise por ID. RLS garante isolamento por tenant."""
        await self._set_rls_context()

        stmt = select(EconomicImpactAnalysis).where(
            EconomicImpactAnalysis.id == analysis_id,
            EconomicImpactAnalysis.tenant_id == self._tenant_id,
        )
        result = await self._db.execute(stmt)
        analysis = result.scalar_one_or_none()

        if analysis is None:
            raise AnalysisNotFoundError(
                f"Análise {analysis_id} não encontrada para o tenant corrente."
            )
        return analysis

    async def _run_causal_pipeline(
        self, request: EconomicImpactAnalysisCreateRequest
    ) -> dict[str, Any]:
        """Orquestra panel builder → engine causal → serialização.

        Retorna o resultado serializado (JSON-safe) do engine causal.
        """
        from app.services.impacto_economico.panel_builder import EconomicImpactPanelBuilder

        builder = EconomicImpactPanelBuilder()

        results: dict[str, Any] = {}

        if request.method in ("did", "event_study", "compare"):
            df = await builder.build_did_panel(
                treated_municipios=request.treated_ids,
                control_municipios=request.control_ids or [],
                treatment_year=request.treatment_year,
                ano_inicio=request.ano_inicio,
                ano_fim=request.ano_fim,
                use_mart=request.use_mart,
                scope=request.scope,
            )

            if request.method in ("did", "event_study"):
                from app.services.impacto_economico.causal.did import (
                    run_did_with_diagnostics,
                )

                outcome_results = {}
                for outcome in request.outcomes:
                    outcome_results[outcome] = run_did_with_diagnostics(
                        df=df,
                        outcome=outcome,
                        treatment_year=request.treatment_year,
                        controls=request.controls,
                    )
                results = outcome_results

            elif request.method == "compare":
                from app.services.impacto_economico.causal.did import (
                    run_did_with_diagnostics,
                )
                from app.services.impacto_economico.causal.comparison import (
                    compare_method_results,
                )

                did_results = {}
                for outcome in request.outcomes:
                    did_r = run_did_with_diagnostics(
                        df=df,
                        outcome=outcome,
                        treatment_year=request.treatment_year,
                        controls=request.controls,
                    )
                    did_results[outcome] = did_r

                results["did"] = did_results
                results["comparison"] = {
                    outcome: compare_method_results(
                        did_result=did_results[outcome].get("main_result"),
                        outcome=outcome,
                    )
                    for outcome in request.outcomes
                }

        elif request.method == "iv":
            df = await builder.build_did_panel(
                treated_municipios=request.treated_ids,
                control_municipios=request.control_ids or [],
                treatment_year=request.treatment_year,
                ano_inicio=request.ano_inicio,
                ano_fim=request.ano_fim,
                use_mart=request.use_mart,
                scope=request.scope,
            )

            from app.services.impacto_economico.causal.iv import (
                run_iv_with_diagnostics,
            )

            outcome_results = {}
            for outcome in request.outcomes:
                outcome_results[outcome] = run_iv_with_diagnostics(
                    df=df,
                    outcome=outcome,
                    endog="toneladas_antaq_log",
                    instrument=request.instrument,
                    controls=request.controls,
                )
            results = outcome_results

        elif request.method == "panel_iv":
            df = await builder.build_iv_panel(
                id_municipios=request.treated_ids + (request.control_ids or []),
                ano_inicio=request.ano_inicio,
                ano_fim=request.ano_fim,
                commodity_cols=[request.instrument] if request.instrument else None,
            )

            from app.services.impacto_economico.causal.iv_panel import (
                run_panel_iv_with_diagnostics,
            )

            outcome_results = {}
            for outcome in request.outcomes:
                outcome_results[outcome] = run_panel_iv_with_diagnostics(
                    df=df,
                    outcome=outcome,
                    endog="toneladas_antaq_log",
                    instrument=request.instrument,
                    controls=request.controls,
                )
            results = outcome_results

        # Serializa tudo para JSON-safe antes de retornar
        return serialize_causal_result(results)


# ── Helpers de extração de resumo ─────────────────────────────────────────────

def _extract_summary(
    result_full: dict[str, Any],
    request: EconomicImpactAnalysisCreateRequest,
) -> dict[str, Any]:
    """Extrai métricas principais do resultado completo.

    Prioriza o primeiro outcome listado. Retorna um dict JSON-safe
    com coef, std_err, p_value, n_obs e warnings.
    """
    summary: dict[str, Any] = {
        "method": request.method,
        "outcomes": request.outcomes,
        "treatment_year": request.treatment_year,
        "treated_ids": request.treated_ids,
        "n_treated": len(request.treated_ids),
        "n_control": len(request.control_ids or []),
        "ano_inicio": request.ano_inicio,
        "ano_fim": request.ano_fim,
    }

    # Extrai métricas do primeiro outcome
    first_outcome = request.outcomes[0] if request.outcomes else None
    if first_outcome and first_outcome in result_full:
        outcome_data = result_full[first_outcome]

        main = outcome_data.get("main_result", outcome_data)
        summary["outcome"] = first_outcome
        summary["coef"] = main.get("coef") or main.get("att")
        summary["std_err"] = main.get("std_err")
        summary["p_value"] = main.get("p_value")
        summary["ci_lower"] = main.get("ci_lower")
        summary["ci_upper"] = main.get("ci_upper")
        summary["n_obs"] = main.get("n_obs")
        summary["r2"] = main.get("r2")

        # Agrega warnings de todas as chaves relevantes
        warnings: list[str] = []
        for key in ("warnings", "parallel_trends", "first_stage"):
            section = outcome_data.get(key)
            if isinstance(section, dict) and section.get("warning"):
                warnings.append(section["warning"])
            elif isinstance(section, list):
                warnings.extend(str(w) for w in section)
        summary["warnings"] = warnings

    return {k: v for k, v in summary.items() if v is not None}


# ── Dependency factory ────────────────────────────────────────────────────────

def get_analysis_service(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> AnalysisService:
    """Factory para uso como FastAPI Depends."""
    return AnalysisService(db=db, tenant_id=tenant_id)
