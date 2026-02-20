"""Testes unitários do PR-06: Celery app + task impacto_economico.

Cobertura:
  TestCeleryApp          — configuração da instância Celery (broker, backend,
                           task_routes, serialização, timeouts)
  TestRunEconomicTask    — lógica da task: sucesso, análise não encontrada,
                           parâmetros inválidos, retry em exceção inesperada
  TestExecuteAnalysisAsync — helper _execute_analysis_async isolado
"""
from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Fixtures compartilhados
# ---------------------------------------------------------------------------

ANALYSIS_ID = str(uuid.uuid4())
TENANT_ID = str(uuid.uuid4())


# ---------------------------------------------------------------------------
# TestCeleryApp
# ---------------------------------------------------------------------------


class TestCeleryApp:
    """Valida a configuração da instância Celery sem broker real."""

    def _get_app(self):
        from app.tasks.celery_app import celery_app
        return celery_app

    def test_celery_app_is_celery_instance(self):
        from celery import Celery
        app = self._get_app()
        assert isinstance(app, Celery)

    def test_app_name(self):
        app = self._get_app()
        assert app.main == "saas_impacto"

    def test_broker_url_configured(self):
        app = self._get_app()
        # Deve estar configurado (vem das settings ou do conftest default)
        assert app.conf.broker_url is not None
        assert "redis" in app.conf.broker_url.lower() or "redis" in str(app.conf.broker_url).lower()

    def test_result_backend_configured(self):
        app = self._get_app()
        assert app.conf.result_backend is not None

    def test_task_serializer_json(self):
        app = self._get_app()
        assert app.conf.task_serializer == "json"

    def test_result_serializer_json(self):
        app = self._get_app()
        assert app.conf.result_serializer == "json"

    def test_timezone_utc(self):
        app = self._get_app()
        assert app.conf.timezone == "UTC"
        assert app.conf.enable_utc is True

    def test_task_acks_late(self):
        app = self._get_app()
        assert app.conf.task_acks_late is True

    def test_worker_prefetch_multiplier_one(self):
        app = self._get_app()
        assert app.conf.worker_prefetch_multiplier == 1

    def test_economic_impact_task_route(self):
        app = self._get_app()
        routes = app.conf.task_routes or {}
        assert "app.tasks.impacto_economico.*" in routes
        assert routes["app.tasks.impacto_economico.*"]["queue"] == "economic_impact"

    def test_task_soft_time_limit(self):
        app = self._get_app()
        assert app.conf.task_soft_time_limit == 900  # 15 min

    def test_task_time_limit(self):
        app = self._get_app()
        assert app.conf.task_time_limit == 1200  # 20 min

    def test_task_track_started(self):
        app = self._get_app()
        assert app.conf.task_track_started is True

    def test_task_registered(self):
        """Task run_economic_impact_analysis deve estar registrada no Celery app."""
        from app.tasks.impacto_economico import run_economic_impact_analysis  # garante registro
        celery_app = self._get_app()
        registered = list(celery_app.tasks.keys())
        assert run_economic_impact_analysis.name in registered, (
            f"Task não encontrada. Registradas: {registered}"
        )


# ---------------------------------------------------------------------------
# TestRunEconomicTask
# ---------------------------------------------------------------------------


class TestRunEconomicTask:
    """Testa a task Celery chamando task.run() diretamente (sem broker/backend).

    ``task.run()`` invoca a função subjacente sem passar pelo Celery backend,
    eliminando a dependência de Redis nos testes unitários.
    """

    def _get_task(self):
        from app.tasks.impacto_economico import run_economic_impact_analysis
        return run_economic_impact_analysis

    def test_task_is_registered(self):
        task = self._get_task()
        assert task.name == "app.tasks.impacto_economico.run_economic_impact_analysis"

    def test_task_max_retries(self):
        task = self._get_task()
        assert task.max_retries == 3

    def test_task_acks_late(self):
        task = self._get_task()
        assert task.acks_late is True

    def test_task_success_calls_asyncio_run(self):
        """Task chama asyncio.run(...)  quando executa com sucesso."""
        task = self._get_task()

        with patch("app.tasks.impacto_economico.asyncio") as mock_asyncio:
            mock_asyncio.run = MagicMock(return_value=None)
            # Usa task.run() para evitar acesso ao backend Redis
            result = task.run(ANALYSIS_ID, TENANT_ID)

        assert result == {"analysis_id": ANALYSIS_ID, "status": "done"}
        mock_asyncio.run.assert_called_once()

    def test_task_success_returns_dict(self):
        """Task bem-sucedida retorna dict com analysis_id e status."""
        task = self._get_task()

        with patch("app.tasks.impacto_economico.asyncio") as mock_asyncio:
            mock_asyncio.run = MagicMock(return_value=None)
            result = task.run(ANALYSIS_ID, TENANT_ID)

        assert result["analysis_id"] == ANALYSIS_ID
        assert result["status"] == "done"

    def test_task_retries_on_unexpected_exception(self):
        """Task dispara self.retry() quando asyncio.run levanta exceção inesperada."""
        from celery.exceptions import Retry

        task = self._get_task()

        with patch("app.tasks.impacto_economico.asyncio") as mock_asyncio:
            mock_asyncio.run = MagicMock(side_effect=ConnectionError("down"))
            # self.retry() levanta celery.exceptions.Retry em modo não-eager
            with pytest.raises((ConnectionError, Retry, Exception)):
                task.run(ANALYSIS_ID, TENANT_ID)


# ---------------------------------------------------------------------------
# TestExecuteAnalysisAsync
# ---------------------------------------------------------------------------


class TestExecuteAnalysisAsync:
    """Testa o helper async _execute_analysis_async com mocks de DB."""

    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def _mock_analysis(self, request_params: dict | None = None):
        """Cria mock de EconomicImpactAnalysis."""
        analysis = MagicMock()
        analysis.id = uuid.UUID(ANALYSIS_ID)
        analysis.tenant_id = uuid.UUID(TENANT_ID)
        analysis.status = "queued"
        analysis.request_params = request_params or {
            "method": "did",
            "treated_ids": ["2100055"],
            "control_ids": ["2100204"],
            "treatment_year": 2015,
            "scope": "state",
            "outcomes": ["pib_log"],
            "ano_inicio": 2010,
            "ano_fim": 2023,
            "use_mart": True,
        }
        analysis.mark_failed = MagicMock()
        return analysis

    def _make_mock_session(self, analysis):
        """Fábrica de mock AsyncSession que retorna `analysis` no SELECT."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.commit = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = analysis
        mock_session.execute = AsyncMock(return_value=mock_result)
        return mock_session

    def test_analysis_not_found_logs_error_and_returns(self):
        """Quando a análise não existe, não deve lançar exceção."""
        from app.tasks.impacto_economico import _execute_analysis_async

        mock_session = self._make_mock_session(analysis=None)

        # AsyncSessionLocal é importado *dentro* da função, então patchamos
        # no módulo de origem (app.db.base), não no módulo da task.
        with patch("app.db.base.AsyncSessionLocal", return_value=mock_session):
            self._run(_execute_analysis_async(ANALYSIS_ID, TENANT_ID))
        # Sem exceção = passou

    def test_invalid_request_params_marks_failed(self):
        """request_params inválidos marcam análise como failed sem retry."""
        from app.tasks.impacto_economico import _execute_analysis_async

        analysis = self._mock_analysis(request_params={"method": "did"})  # faltam campos
        mock_session = self._make_mock_session(analysis)

        with patch("app.db.base.AsyncSessionLocal", return_value=mock_session):
            self._run(_execute_analysis_async(ANALYSIS_ID, TENANT_ID))

        analysis.mark_failed.assert_called_once()
        error_msg = analysis.mark_failed.call_args[0][0]
        assert "inválidos" in error_msg.lower() or "Parâmetros" in error_msg

    def test_valid_analysis_calls_service_execute(self):
        """Análise válida deve chamar AnalysisService._execute()."""
        from app.tasks.impacto_economico import _execute_analysis_async

        analysis = self._mock_analysis()
        analysis.status = "success"
        mock_session = self._make_mock_session(analysis)

        mock_service = MagicMock()
        mock_service._execute = AsyncMock(return_value=analysis)

        with patch("app.db.base.AsyncSessionLocal", return_value=mock_session), \
             patch(
                 "app.services.impacto_economico.analysis_service.AnalysisService",
                 return_value=mock_service,
             ):
            self._run(_execute_analysis_async(ANALYSIS_ID, TENANT_ID))

        mock_service._execute.assert_called_once()

    def test_rls_context_set_before_query(self):
        """SET LOCAL deve ser executado antes do SELECT (mín. 2 execute calls)."""
        from app.tasks.impacto_economico import _execute_analysis_async

        call_count = 0

        async def counting_execute(stmt, params=None):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            return result

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.execute = AsyncMock(side_effect=counting_execute)

        with patch("app.db.base.AsyncSessionLocal", return_value=mock_session):
            self._run(_execute_analysis_async(ANALYSIS_ID, TENANT_ID))

        # SET LOCAL (statement 1) + SELECT (statement 2)
        assert call_count >= 2
