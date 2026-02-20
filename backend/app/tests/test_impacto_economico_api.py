"""Testes unitários do PR-05: schemas, service e router de Impacto Econômico.

Cobertura:
  TestSchemas          — validação Pydantic (casos feliz + erros esperados)
  TestAnalysisService  — service com DB mockado (AsyncMock)
  TestRouter           — endpoints via TestClient (ASGI) com mocks de dependência
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# Fixtures compartilhados
# ---------------------------------------------------------------------------

TENANT_ID = uuid.uuid4()
USER_ID = uuid.uuid4()
ANALYSIS_ID = uuid.uuid4()

BASE_REQUEST = {
    "method": "did",
    "treated_ids": ["2100055", "2100105"],
    "control_ids": ["2100204", "2100303"],
    "treatment_year": 2015,
    "scope": "state",
    "outcomes": ["pib_log"],
    "ano_inicio": 2010,
    "ano_fim": 2023,
    "use_mart": True,
}


# ---------------------------------------------------------------------------
# TestSchemas
# ---------------------------------------------------------------------------

class TestSchemas:
    """Valida lógica de negócio dos schemas Pydantic."""

    def test_valid_did_request(self):
        from app.schemas.impacto_economico import EconomicImpactAnalysisCreateRequest
        req = EconomicImpactAnalysisCreateRequest(**BASE_REQUEST)
        assert req.method == "did"
        assert req.treatment_year == 2015
        assert req.instrument is None

    def test_valid_iv_request_requires_instrument(self):
        from app.schemas.impacto_economico import EconomicImpactAnalysisCreateRequest
        data = {**BASE_REQUEST, "method": "iv", "instrument": "commodity_index"}
        req = EconomicImpactAnalysisCreateRequest(**data)
        assert req.method == "iv"
        assert req.instrument == "commodity_index"

    def test_iv_without_instrument_raises(self):
        from app.schemas.impacto_economico import EconomicImpactAnalysisCreateRequest
        with pytest.raises(ValidationError, match="instrument"):
            EconomicImpactAnalysisCreateRequest(
                **{**BASE_REQUEST, "method": "iv", "instrument": None}
            )

    def test_panel_iv_without_instrument_raises(self):
        from app.schemas.impacto_economico import EconomicImpactAnalysisCreateRequest
        with pytest.raises(ValidationError, match="instrument"):
            EconomicImpactAnalysisCreateRequest(
                **{**BASE_REQUEST, "method": "panel_iv"}
            )

    def test_ano_fim_must_be_greater_than_ano_inicio(self):
        from app.schemas.impacto_economico import EconomicImpactAnalysisCreateRequest
        with pytest.raises(ValidationError, match="ano_fim"):
            EconomicImpactAnalysisCreateRequest(
                **{**BASE_REQUEST, "ano_inicio": 2018, "ano_fim": 2015}
            )

    def test_treatment_year_must_be_in_panel(self):
        from app.schemas.impacto_economico import EconomicImpactAnalysisCreateRequest
        # treatment_year before ano_inicio
        with pytest.raises(ValidationError, match="treatment_year"):
            EconomicImpactAnalysisCreateRequest(
                **{**BASE_REQUEST, "treatment_year": 2009}
            )

    def test_treatment_year_at_ano_inicio_raises(self):
        from app.schemas.impacto_economico import EconomicImpactAnalysisCreateRequest
        # treatment_year == ano_inicio is invalid (no pre-period)
        with pytest.raises(ValidationError, match="treatment_year"):
            EconomicImpactAnalysisCreateRequest(
                **{**BASE_REQUEST, "treatment_year": 2010}
            )

    def test_overlap_treated_control_raises(self):
        from app.schemas.impacto_economico import EconomicImpactAnalysisCreateRequest
        with pytest.raises(ValidationError, match="mesmo tempo"):
            EconomicImpactAnalysisCreateRequest(
                **{
                    **BASE_REQUEST,
                    "treated_ids": ["2100055"],
                    "control_ids": ["2100055", "2100204"],  # overlap
                }
            )

    def test_empty_treated_ids_raises(self):
        from app.schemas.impacto_economico import EconomicImpactAnalysisCreateRequest
        with pytest.raises(ValidationError):
            EconomicImpactAnalysisCreateRequest(**{**BASE_REQUEST, "treated_ids": []})

    def test_empty_outcomes_raises(self):
        from app.schemas.impacto_economico import EconomicImpactAnalysisCreateRequest
        with pytest.raises(ValidationError):
            EconomicImpactAnalysisCreateRequest(**{**BASE_REQUEST, "outcomes": []})

    def test_model_dump_is_json_serialisable(self):
        import json
        from app.schemas.impacto_economico import EconomicImpactAnalysisCreateRequest
        req = EconomicImpactAnalysisCreateRequest(**BASE_REQUEST)
        dumped = req.model_dump(mode="json")
        # Should not raise
        json.dumps(dumped)

    def test_all_valid_methods_accepted(self):
        from app.schemas.impacto_economico import EconomicImpactAnalysisCreateRequest
        for method in ("did", "event_study", "compare"):
            req = EconomicImpactAnalysisCreateRequest(**{**BASE_REQUEST, "method": method})
            assert req.method == method

    def test_response_model_from_attributes(self):
        from app.schemas.impacto_economico import EconomicImpactAnalysisResponse

        now = datetime.now(tz=timezone.utc)
        mock_obj = MagicMock()
        mock_obj.id = ANALYSIS_ID
        mock_obj.tenant_id = TENANT_ID
        mock_obj.user_id = USER_ID
        mock_obj.status = "success"
        mock_obj.method = "did"
        mock_obj.created_at = now
        mock_obj.updated_at = now

        resp = EconomicImpactAnalysisResponse.model_validate(mock_obj)
        assert resp.id == ANALYSIS_ID
        assert resp.status == "success"

    def test_detail_response_from_orm_instance(self):
        from app.schemas.impacto_economico import EconomicImpactAnalysisDetailResponse

        now = datetime.now(tz=timezone.utc)
        mock_orm = MagicMock()
        mock_orm.id = ANALYSIS_ID
        mock_orm.tenant_id = TENANT_ID
        mock_orm.user_id = USER_ID
        mock_orm.status = "success"
        mock_orm.method = "did"
        mock_orm.created_at = now
        mock_orm.updated_at = now
        mock_orm.started_at = now
        mock_orm.completed_at = now
        mock_orm.duration_seconds = 2.5
        mock_orm.request_params = BASE_REQUEST
        mock_orm.result_summary = {"coef": 0.15, "p_value": 0.02}
        mock_orm.result_full = None
        mock_orm.artifact_path = None
        mock_orm.error_message = None

        detail = EconomicImpactAnalysisDetailResponse.from_orm_instance(mock_orm)
        assert detail.result_summary["coef"] == 0.15
        assert detail.duration_seconds == 2.5

    def test_list_response_structure(self):
        from app.schemas.impacto_economico import (
            EconomicImpactAnalysisListResponse,
            EconomicImpactAnalysisResponse,
        )
        now = datetime.now(tz=timezone.utc)
        item = EconomicImpactAnalysisResponse(
            id=ANALYSIS_ID,
            tenant_id=TENANT_ID,
            user_id=None,
            status="queued",
            method="did",
            created_at=now,
            updated_at=now,
        )
        lst = EconomicImpactAnalysisListResponse(total=1, items=[item])
        assert lst.total == 1
        assert len(lst.items) == 1
        assert lst.page == 1
        assert lst.page_size == 20


# ---------------------------------------------------------------------------
# TestAnalysisService
# ---------------------------------------------------------------------------

class TestAnalysisService:
    """Testa o AnalysisService com DB mockado."""

    def _make_mock_analysis(self, status: str = "success") -> MagicMock:
        """Cria um mock de EconomicImpactAnalysis com campos mínimos."""
        now = datetime.now(tz=timezone.utc)
        obj = MagicMock()
        obj.id = ANALYSIS_ID
        obj.tenant_id = TENANT_ID
        obj.user_id = USER_ID
        obj.status = status
        obj.method = "did"
        obj.created_at = now
        obj.updated_at = now
        obj.started_at = now
        obj.completed_at = now
        obj.duration_seconds = 1.5
        obj.request_params = BASE_REQUEST
        obj.result_summary = {"coef": 0.15}
        obj.result_full = {"main_result": {"coef": 0.15}}
        obj.artifact_path = None
        obj.error_message = None
        obj.is_terminal = status in ("success", "failed")
        return obj

    def _make_service(self) -> "AnalysisService":
        from app.services.impacto_economico.analysis_service import AnalysisService
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return AnalysisService(db=db, tenant_id=TENANT_ID)

    @pytest.mark.asyncio
    async def test_get_status_returns_response(self):
        from app.schemas.impacto_economico import EconomicImpactAnalysisResponse

        service = self._make_service()
        mock_analysis = self._make_mock_analysis()

        with patch.object(service, "_fetch", AsyncMock(return_value=mock_analysis)):
            result = await service.get_status(ANALYSIS_ID)

        assert isinstance(result, EconomicImpactAnalysisResponse)
        assert result.id == ANALYSIS_ID
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_get_detail_returns_detail_response(self):
        from app.schemas.impacto_economico import EconomicImpactAnalysisDetailResponse

        service = self._make_service()
        mock_analysis = self._make_mock_analysis()

        with patch.object(service, "_fetch", AsyncMock(return_value=mock_analysis)):
            result = await service.get_detail(ANALYSIS_ID)

        assert isinstance(result, EconomicImpactAnalysisDetailResponse)
        assert result.result_summary == {"coef": 0.15}

    @pytest.mark.asyncio
    async def test_get_status_raises_not_found(self):
        from app.services.impacto_economico.analysis_service import AnalysisNotFoundError

        service = self._make_service()

        with patch.object(
            service,
            "_fetch",
            AsyncMock(side_effect=AnalysisNotFoundError("not found")),
        ):
            with pytest.raises(AnalysisNotFoundError):
                await service.get_status(ANALYSIS_ID)

    @pytest.mark.asyncio
    async def test_set_rls_context_executes_set_local(self):
        service = self._make_service()
        await service._set_rls_context()
        # Verifica que execute foi chamado
        service._db.execute.assert_called_once()
        call_args = service._db.execute.call_args
        # O texto SQL deve conter SET LOCAL
        sql_arg = str(call_args[0][0])
        assert "SET LOCAL" in sql_arg or "SET LOCAL" in sql_arg.upper()

    @pytest.mark.asyncio
    async def test_create_queued_adds_and_commits(self):
        from app.schemas.impacto_economico import EconomicImpactAnalysisCreateRequest

        service = self._make_service()
        mock_analysis = self._make_mock_analysis(status="queued")

        # refresh retorna o mock
        service._db.refresh = AsyncMock(
            side_effect=lambda obj: setattr(obj, "id", ANALYSIS_ID)
        )

        req = EconomicImpactAnalysisCreateRequest(**BASE_REQUEST)

        with patch(
            "app.services.impacto_economico.analysis_service.EconomicImpactAnalysis",
            return_value=mock_analysis,
        ):
            result = await service._create_queued(req, user_id=USER_ID)

        service._db.add.assert_called_once()
        service._db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_create_and_run_returns_detail(self):
        from app.schemas.impacto_economico import (
            EconomicImpactAnalysisCreateRequest,
            EconomicImpactAnalysisDetailResponse,
        )

        service = self._make_service()
        mock_analysis = self._make_mock_analysis()
        req = EconomicImpactAnalysisCreateRequest(**BASE_REQUEST)

        with patch.object(
            service, "_create_queued", AsyncMock(return_value=mock_analysis)
        ), patch.object(
            service, "_execute", AsyncMock(return_value=mock_analysis)
        ):
            result = await service.create_and_run(req, user_id=USER_ID)

        assert isinstance(result, EconomicImpactAnalysisDetailResponse)


# ---------------------------------------------------------------------------
# TestRouter
# ---------------------------------------------------------------------------

class TestRouter:
    """Testa os endpoints via httpx / TestClient com mocks de dependências.

    Estratégia:
      - Monta uma FastAPI mínima com apenas o router de impacto_economico.
      - Substitui `_get_analysis_service` (dependência interna do router)
        por uma factory que retorna um MagicMock pré-configurado.
      - Sobrescreve `get_current_user` e `get_tenant_id` com funções dummy.
      - Todas as chamadas HTTP usam o prefixo completo: /impacto-economico/...
    """

    # Prefixo definido no router
    PREFIX = "/impacto-economico"

    def _now(self) -> str:
        return datetime.now(tz=timezone.utc).isoformat()

    def _mock_detail(self, status: str = "success") -> dict:
        now = self._now()
        return {
            "id": str(ANALYSIS_ID),
            "tenant_id": str(TENANT_ID),
            "user_id": str(USER_ID),
            "status": status,
            "method": "did",
            "created_at": now,
            "updated_at": now,
            "started_at": now,
            "completed_at": now,
            "duration_seconds": 2.5,
            "request_params": BASE_REQUEST,
            "result_summary": {"coef": 0.15, "p_value": 0.02},
            "result_full": {"main_result": {"coef": 0.15}},
            "artifact_path": None,
            "error_message": None,
        }

    def _make_client(self, mock_service: MagicMock):
        """Cria TestClient com `_get_analysis_service` substituído."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        import app.api.v1.impacto_economico.router as router_module
        from app.api.deps import get_current_user
        from app.core.tenant import get_tenant_id
        from app.db.base import get_db

        test_app = FastAPI()
        test_app.include_router(router_module.router)

        mock_user = MagicMock()
        mock_user.id = USER_ID

        # Substituir todas as dependências por mocks
        async def _mock_db():
            yield AsyncMock()

        async def _mock_tenant():
            return TENANT_ID

        async def _mock_user():
            return mock_user

        def _mock_service_factory():
            return mock_service

        test_app.dependency_overrides[get_db] = _mock_db
        test_app.dependency_overrides[get_tenant_id] = _mock_tenant
        test_app.dependency_overrides[get_current_user] = _mock_user
        test_app.dependency_overrides[router_module._get_analysis_service] = (
            _mock_service_factory
        )

        return TestClient(test_app, raise_server_exceptions=False)

    def test_post_analises_returns_201(self):
        from app.schemas.impacto_economico import EconomicImpactAnalysisDetailResponse

        detail = EconomicImpactAnalysisDetailResponse(**self._mock_detail())
        svc = MagicMock()
        svc.create_and_run = AsyncMock(return_value=detail)

        client = self._make_client(svc)
        resp = client.post(f"{self.PREFIX}/analises", json=BASE_REQUEST)

        assert resp.status_code == 201
        body = resp.json()
        assert "id" in body
        assert body["status"] == "success"

    def test_post_analises_validation_error_422(self):
        svc = MagicMock()
        client = self._make_client(svc)

        bad = {**BASE_REQUEST, "treated_ids": []}
        resp = client.post(f"{self.PREFIX}/analises", json=bad)
        assert resp.status_code == 422

    def test_get_analises_returns_200(self):
        from app.schemas.impacto_economico import EconomicImpactAnalysisListResponse

        lst = EconomicImpactAnalysisListResponse(total=0, items=[], page=1, page_size=20)
        svc = MagicMock()
        svc.list_analyses = AsyncMock(return_value=lst)

        client = self._make_client(svc)
        resp = client.get(f"{self.PREFIX}/analises")

        assert resp.status_code == 200
        body = resp.json()
        assert "total" in body
        assert "items" in body

    def test_get_analise_status_returns_200(self):
        from app.schemas.impacto_economico import EconomicImpactAnalysisResponse

        now = self._now()
        resp_obj = EconomicImpactAnalysisResponse(
            id=ANALYSIS_ID,
            tenant_id=TENANT_ID,
            user_id=USER_ID,
            status="success",
            method="did",
            created_at=now,
            updated_at=now,
        )
        svc = MagicMock()
        svc.get_status = AsyncMock(return_value=resp_obj)

        client = self._make_client(svc)
        resp = client.get(f"{self.PREFIX}/analises/{ANALYSIS_ID}")

        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_get_analise_status_not_found_returns_404(self):
        from app.services.impacto_economico.analysis_service import AnalysisNotFoundError

        svc = MagicMock()
        svc.get_status = AsyncMock(side_effect=AnalysisNotFoundError("not found"))

        client = self._make_client(svc)
        resp = client.get(f"{self.PREFIX}/analises/{ANALYSIS_ID}")

        assert resp.status_code == 404

    def test_get_result_still_running_returns_409(self):
        from app.schemas.impacto_economico import EconomicImpactAnalysisDetailResponse

        running = EconomicImpactAnalysisDetailResponse(**self._mock_detail(status="running"))
        svc = MagicMock()
        svc.get_detail = AsyncMock(return_value=running)

        client = self._make_client(svc)
        resp = client.get(f"{self.PREFIX}/analises/{ANALYSIS_ID}/result")

        assert resp.status_code == 409
        assert "running" in resp.json()["detail"]

    def test_get_result_success_returns_200(self):
        from app.schemas.impacto_economico import EconomicImpactAnalysisDetailResponse

        detail = EconomicImpactAnalysisDetailResponse(**self._mock_detail(status="success"))
        svc = MagicMock()
        svc.get_detail = AsyncMock(return_value=detail)

        client = self._make_client(svc)
        resp = client.get(f"{self.PREFIX}/analises/{ANALYSIS_ID}/result")

        assert resp.status_code == 200
        body = resp.json()
        assert body["result_summary"]["coef"] == pytest.approx(0.15)

    def test_get_result_not_found_returns_404(self):
        from app.services.impacto_economico.analysis_service import AnalysisNotFoundError

        svc = MagicMock()
        svc.get_detail = AsyncMock(side_effect=AnalysisNotFoundError("not found"))

        client = self._make_client(svc)
        resp = client.get(f"{self.PREFIX}/analises/{ANALYSIS_ID}/result")

        assert resp.status_code == 404

    def test_router_openapi_has_analises_paths(self):
        """Verifica que o OpenAPI expõe os paths com o prefixo correto."""
        svc = MagicMock()
        client = self._make_client(svc)

        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        paths = resp.json().get("paths", {})

        assert f"{self.PREFIX}/analises" in paths, (
            f"Path '{self.PREFIX}/analises' não encontrado. Paths: {list(paths)}"
        )
        assert f"{self.PREFIX}/analises/{{analysis_id}}" in paths
        assert f"{self.PREFIX}/analises/{{analysis_id}}/result" in paths

    def test_router_openapi_methods_correct(self):
        """Verifica que POST e GET estão registrados nos paths corretos."""
        svc = MagicMock()
        client = self._make_client(svc)

        resp = client.get("/openapi.json")
        paths = resp.json()["paths"]

        analises_path = paths[f"{self.PREFIX}/analises"]
        assert "post" in analises_path, "POST /analises não encontrado"
        assert "get" in analises_path, "GET /analises não encontrado"

        detail_path = paths[f"{self.PREFIX}/analises/{{analysis_id}}"]
        assert "get" in detail_path

        result_path = paths[f"{self.PREFIX}/analises/{{analysis_id}}/result"]
        assert "get" in result_path

    def test_router_openapi_tag_present_in_operations(self):
        """Verifica que as operações têm a tag correta."""
        svc = MagicMock()
        client = self._make_client(svc)

        resp = client.get("/openapi.json")
        paths = resp.json()["paths"]

        post_op = paths[f"{self.PREFIX}/analises"]["post"]
        tags = post_op.get("tags", [])
        assert any("Impacto" in t or "Módulo 5" in t for t in tags), (
            f"Tag esperada não encontrada. Tags: {tags}"
        )
