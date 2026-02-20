"""Testes unitários do PR-07: interface SCM/Augmented SCM + feature flag.

Cobertura:
  TestSCMStub           — run_scm* levanta SCMNotAvailableError
  TestAugmentedSCMStub  — run_augmented_scm* levanta AugmentedSCMNotAvailableError
  TestErrorHierarchy    — ambas são subclasses de NotImplementedError
  TestFeatureFlag       — MethodNotAvailableError levantada quando flag=False
  TestFeatureFlagEnabled — quando flag=True, método avança (stub levanta igualmente)
  TestSchemaAcceptsScm  — "scm" e "augmented_scm" são aceitos pelo Pydantic
  TestValidMethods      — VALID_METHODS do modelo inclui novos métodos
  TestMigrationSQL      — migration expande a CHECK constraint corretamente
  TestRouterReturns501  — POST /analises com scm retorna 501 (flag=False)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace

import pytest
from .http_test_client import make_sync_asgi_client


# ── Fixtures ───────────────────────────────────────────────────────────────

TENANT_ID = uuid.uuid4()
USER_ID = uuid.uuid4()

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

SCM_REQUEST = {**BASE_REQUEST, "method": "scm"}
AUGMENTED_SCM_REQUEST = {**BASE_REQUEST, "method": "augmented_scm"}


# ---------------------------------------------------------------------------
# TestSCMStub
# ---------------------------------------------------------------------------


class TestSCMStub:
    """run_scm / run_scm_with_diagnostics levantam SCMNotAvailableError."""

    def test_run_scm_raises(self):
        from app.services.impacto_economico.causal.scm import run_scm, SCMNotAvailableError
        with pytest.raises(SCMNotAvailableError):
            run_scm(df=None, outcome="pib_log", treatment_year=2015)  # type: ignore

    def test_run_scm_with_diagnostics_raises(self):
        from app.services.impacto_economico.causal.scm import (
            run_scm_with_diagnostics,
            SCMNotAvailableError,
        )
        with pytest.raises(SCMNotAvailableError):
            run_scm_with_diagnostics(df=None, outcome="pib_log", treatment_year=2015)  # type: ignore

    def test_error_message_contains_enable_flag(self):
        from app.services.impacto_economico.causal.scm import SCMNotAvailableError
        msg = str(SCMNotAvailableError())
        assert "ENABLE_SCM" in msg

    def test_error_message_contains_module_name(self):
        from app.services.impacto_economico.causal.scm import SCMNotAvailableError
        msg = str(SCMNotAvailableError())
        assert "synthetic_control" in msg.lower() or "synthetic_control.py" in msg

    def test_error_message_suggests_alternatives(self):
        from app.services.impacto_economico.causal.scm import SCMNotAvailableError
        msg = str(SCMNotAvailableError())
        assert "did" in msg.lower()

    def test_scm_exported_from_causal_init(self):
        from app.services.impacto_economico.causal import (
            run_scm,
            run_scm_with_diagnostics,
            SCMNotAvailableError,
        )
        assert callable(run_scm)
        assert callable(run_scm_with_diagnostics)
        assert issubclass(SCMNotAvailableError, NotImplementedError)


# ---------------------------------------------------------------------------
# TestAugmentedSCMStub
# ---------------------------------------------------------------------------


class TestAugmentedSCMStub:
    """run_augmented_scm* levantam AugmentedSCMNotAvailableError."""

    def test_run_augmented_scm_raises(self):
        from app.services.impacto_economico.causal.augmented_scm import (
            run_augmented_scm,
            AugmentedSCMNotAvailableError,
        )
        with pytest.raises(AugmentedSCMNotAvailableError):
            run_augmented_scm(df=None, outcome="pib_log", treatment_year=2015)  # type: ignore

    def test_run_augmented_scm_with_diagnostics_raises(self):
        from app.services.impacto_economico.causal.augmented_scm import (
            run_augmented_scm_with_diagnostics,
            AugmentedSCMNotAvailableError,
        )
        with pytest.raises(AugmentedSCMNotAvailableError):
            run_augmented_scm_with_diagnostics(  # type: ignore
                df=None, outcome="pib_log", treatment_year=2015
            )

    def test_error_message_contains_enable_flag(self):
        from app.services.impacto_economico.causal.augmented_scm import (
            AugmentedSCMNotAvailableError,
        )
        msg = str(AugmentedSCMNotAvailableError())
        assert "ENABLE_AUGMENTED_SCM" in msg

    def test_error_message_contains_module_name(self):
        from app.services.impacto_economico.causal.augmented_scm import (
            AugmentedSCMNotAvailableError,
        )
        msg = str(AugmentedSCMNotAvailableError())
        assert "synthetic_augmented" in msg.lower()

    def test_error_message_references_paper(self):
        """Deve mencionar Ben-Michael ou referência ao método."""
        from app.services.impacto_economico.causal.augmented_scm import (
            AugmentedSCMNotAvailableError,
        )
        msg_or_doc = str(AugmentedSCMNotAvailableError()) + (
            __import__(
                "app.services.impacto_economico.causal.augmented_scm",
                fromlist=["run_augmented_scm_with_diagnostics"],
            ).__doc__
            or ""
        )
        assert "augmented" in msg_or_doc.lower() or "ben-michael" in msg_or_doc.lower()

    def test_augmented_scm_exported_from_causal_init(self):
        from app.services.impacto_economico.causal import (
            run_augmented_scm,
            run_augmented_scm_with_diagnostics,
            AugmentedSCMNotAvailableError,
        )
        assert callable(run_augmented_scm)
        assert callable(run_augmented_scm_with_diagnostics)
        assert issubclass(AugmentedSCMNotAvailableError, NotImplementedError)


# ---------------------------------------------------------------------------
# TestErrorHierarchy
# ---------------------------------------------------------------------------


class TestErrorHierarchy:
    """Ambas as exceções devem ser subclasses de NotImplementedError."""

    def test_scm_error_is_not_implemented_error(self):
        from app.services.impacto_economico.causal.scm import SCMNotAvailableError
        assert issubclass(SCMNotAvailableError, NotImplementedError)

    def test_augmented_scm_error_is_not_implemented_error(self):
        from app.services.impacto_economico.causal.augmented_scm import (
            AugmentedSCMNotAvailableError,
        )
        assert issubclass(AugmentedSCMNotAvailableError, NotImplementedError)

    def test_method_not_available_is_not_implemented_error(self):
        from app.services.impacto_economico.analysis_service import MethodNotAvailableError
        assert issubclass(MethodNotAvailableError, NotImplementedError)

    def test_scm_caught_as_not_implemented_error(self):
        from app.services.impacto_economico.causal.scm import run_scm
        with pytest.raises(NotImplementedError):
            run_scm(df=None, outcome="pib_log", treatment_year=2015)  # type: ignore


# ---------------------------------------------------------------------------
# TestFeatureFlag
# ---------------------------------------------------------------------------


class TestFeatureFlag:
    """_assert_method_available levanta MethodNotAvailableError quando flag=False."""

    def test_scm_flag_false_raises(self):
        from app.services.impacto_economico.analysis_service import (
            AnalysisService,
            MethodNotAvailableError,
        )
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value.enable_scm = False
            mock_settings.return_value.enable_augmented_scm = False
            with pytest.raises(MethodNotAvailableError):
                AnalysisService._assert_method_available("scm")

    def test_augmented_scm_flag_false_raises(self):
        from app.services.impacto_economico.analysis_service import (
            AnalysisService,
            MethodNotAvailableError,
        )
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value.enable_scm = False
            mock_settings.return_value.enable_augmented_scm = False
            with pytest.raises(MethodNotAvailableError):
                AnalysisService._assert_method_available("augmented_scm")

    def test_stable_methods_never_raise(self):
        """Métodos estáveis não devem levantar mesmo com flags desabilitadas."""
        from app.services.impacto_economico.analysis_service import AnalysisService
        for method in ("did", "iv", "panel_iv", "event_study", "compare"):
            AnalysisService._assert_method_available(method)  # deve ser silencioso

    def test_method_not_available_error_contains_scm_message(self):
        from app.services.impacto_economico.analysis_service import (
            AnalysisService,
            MethodNotAvailableError,
        )
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value.enable_scm = False
            mock_settings.return_value.enable_augmented_scm = False
            with pytest.raises(MethodNotAvailableError) as exc_info:
                AnalysisService._assert_method_available("scm")
            assert "scm" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# TestFeatureFlagEnabled
# ---------------------------------------------------------------------------


class TestFeatureFlagEnabled:
    """Quando flag=True, _assert_method_available passa; stub é chamado no pipeline."""

    def test_scm_flag_true_no_assertion_error(self):
        """Com flag habilitada, _assert_method_available não levanta."""
        from app.services.impacto_economico.analysis_service import AnalysisService
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value.enable_scm = True
            mock_settings.return_value.enable_augmented_scm = False
            # Não deve levantar
            AnalysisService._assert_method_available("scm")

    def test_augmented_scm_flag_true_no_assertion_error(self):
        from app.services.impacto_economico.analysis_service import AnalysisService
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value.enable_scm = False
            mock_settings.return_value.enable_augmented_scm = True
            AnalysisService._assert_method_available("augmented_scm")

    def test_scm_flag_true_pipeline_still_raises_stub(self):
        """Com flag habilitada, a execução do pipeline bate no stub e levanta."""
        from app.services.impacto_economico.causal.scm import SCMNotAvailableError
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value.enable_scm = True
            with pytest.raises(SCMNotAvailableError):
                from app.services.impacto_economico.causal.scm import run_scm_with_diagnostics
                run_scm_with_diagnostics(df=None, outcome="pib_log", treatment_year=2015)  # type: ignore


# ---------------------------------------------------------------------------
# TestSchemaAcceptsScm
# ---------------------------------------------------------------------------


class TestSchemaAcceptsScm:
    """'scm' e 'augmented_scm' são aceitos pelo schema Pydantic."""

    def test_scm_accepted_in_method_literal(self):
        from app.schemas.impacto_economico import EconomicImpactAnalysisCreateRequest
        req = EconomicImpactAnalysisCreateRequest(**SCM_REQUEST)
        assert req.method == "scm"

    def test_augmented_scm_accepted_in_method_literal(self):
        from app.schemas.impacto_economico import EconomicImpactAnalysisCreateRequest
        req = EconomicImpactAnalysisCreateRequest(**AUGMENTED_SCM_REQUEST)
        assert req.method == "augmented_scm"

    def test_invalid_method_rejected(self):
        from app.schemas.impacto_economico import EconomicImpactAnalysisCreateRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            EconomicImpactAnalysisCreateRequest(**{**BASE_REQUEST, "method": "synthetic_control"})

    def test_scm_model_dump_is_json_serialisable(self):
        import json
        from app.schemas.impacto_economico import EconomicImpactAnalysisCreateRequest
        req = EconomicImpactAnalysisCreateRequest(**SCM_REQUEST)
        payload = req.model_dump(mode="json")
        json.dumps(payload)  # não deve lançar


# ---------------------------------------------------------------------------
# TestValidMethods
# ---------------------------------------------------------------------------


class TestValidMethods:
    """VALID_METHODS do modelo de DB inclui 'scm' e 'augmented_scm'."""

    def test_scm_in_valid_methods(self):
        from app.db.models.economic_impact_analysis import VALID_METHODS
        assert "scm" in VALID_METHODS

    def test_augmented_scm_in_valid_methods(self):
        from app.db.models.economic_impact_analysis import VALID_METHODS
        assert "augmented_scm" in VALID_METHODS

    def test_stable_methods_still_present(self):
        from app.db.models.economic_impact_analysis import VALID_METHODS
        for m in ("did", "iv", "panel_iv", "event_study", "compare"):
            assert m in VALID_METHODS


# ---------------------------------------------------------------------------
# TestMigrationSQL
# ---------------------------------------------------------------------------


class TestMigrationSQL:
    """Migration d7e8f9a0b1c2 expande a CHECK constraint corretamente."""

    def _get_migration(self):
        import importlib
        return importlib.import_module(
            "app.alembic.versions"
            ".20260220_1000_d7e8f9a0b1c2_expand_method_check_scm"
        )

    def test_revision_id(self):
        m = self._get_migration()
        assert m.revision == "d7e8f9a0b1c2"

    def test_down_revision_is_rls_migration(self):
        m = self._get_migration()
        assert m.down_revision == "c8f3a1d92b47"

    def test_upgrade_adds_scm(self):
        m = self._get_migration()
        assert "scm" in m._ADD_CONSTRAINT_V2

    def test_upgrade_adds_augmented_scm(self):
        m = self._get_migration()
        assert "augmented_scm" in m._ADD_CONSTRAINT_V2

    def test_downgrade_removes_scm(self):
        m = self._get_migration()
        assert "scm" not in m._ADD_CONSTRAINT_V1

    def test_downgrade_removes_augmented_scm(self):
        m = self._get_migration()
        assert "augmented_scm" not in m._ADD_CONSTRAINT_V1

    def test_stable_methods_in_both_versions(self):
        m = self._get_migration()
        for method in ("did", "iv", "panel_iv", "event_study", "compare"):
            assert method in m._ADD_CONSTRAINT_V1
            assert method in m._ADD_CONSTRAINT_V2

    def test_drop_constraint_targets_correct_table(self):
        m = self._get_migration()
        assert "economic_impact_analyses" in m._DROP_CONSTRAINT


# ---------------------------------------------------------------------------
# TestRouterReturns501
# ---------------------------------------------------------------------------


class TestRouterReturns501:
    """POST /analises com scm retorna 501 quando feature flag está desabilitada."""

    PREFIX = "/impacto-economico"

    def _make_client(self, mock_service: MagicMock):
        from fastapi import FastAPI
        import app.api.v1.impacto_economico.router as router_module
        from app.api.deps import get_current_user
        from app.core.tenant import get_tenant_id
        from app.db.base import get_db

        test_app = FastAPI()
        test_app.include_router(router_module.router)

        mock_user = SimpleNamespace(
            id=USER_ID,
            tenant_id=TENANT_ID,
            roles=["analyst"],
            tenant=SimpleNamespace(plano="enterprise"),
        )

        async def _mock_db():
            yield AsyncMock()

        async def _mock_tenant():
            return TENANT_ID

        async def _mock_user():
            return mock_user

        def _mock_service_factory():
            return mock_service

        async def _mock_permission_service():
            class _PermissionService:
                async def list_permissions_by_roles(self, _db, _tenant_id, _roles):
                    return {}

            return _PermissionService()

        test_app.dependency_overrides[get_db] = _mock_db
        test_app.dependency_overrides[get_tenant_id] = _mock_tenant
        test_app.dependency_overrides[get_current_user] = _mock_user
        from app.api.deps import get_tenant_permission_service
        test_app.dependency_overrides[get_tenant_permission_service] = (
            _mock_permission_service
        )
        test_app.dependency_overrides[router_module._get_analysis_service] = (
            _mock_service_factory
        )
        return make_sync_asgi_client(test_app)

    def test_scm_returns_501_when_flag_disabled(self):
        """POST /analises com method=scm retorna 501 Not Implemented."""
        from app.services.impacto_economico.analysis_service import MethodNotAvailableError

        svc = MagicMock()
        svc.create_queued = AsyncMock(
            side_effect=MethodNotAvailableError(
                "O método 'scm' ainda não está disponível. ENABLE_SCM=true"
            )
        )

        client = self._make_client(svc)
        resp = client.post(f"{self.PREFIX}/analises", json=SCM_REQUEST)

        assert resp.status_code == 501
        assert "scm" in resp.json()["detail"].lower() or "501" in str(resp.status_code)

    def test_augmented_scm_returns_501_when_flag_disabled(self):
        from app.services.impacto_economico.analysis_service import MethodNotAvailableError

        svc = MagicMock()
        svc.create_queued = AsyncMock(
            side_effect=MethodNotAvailableError(
                "O método 'augmented_scm' ainda não está disponível. ENABLE_AUGMENTED_SCM=true"
            )
        )

        client = self._make_client(svc)
        resp = client.post(f"{self.PREFIX}/analises", json=AUGMENTED_SCM_REQUEST)

        assert resp.status_code == 501

    def test_501_detail_contains_enable_instruction(self):
        """Detail do 501 deve conter instrução para habilitar a flag."""
        from app.services.impacto_economico.analysis_service import MethodNotAvailableError

        svc = MagicMock()
        svc.create_queued = AsyncMock(
            side_effect=MethodNotAvailableError(
                "O método 'scm' não está disponível. Configure ENABLE_SCM=true no .env"
            )
        )

        client = self._make_client(svc)
        resp = client.post(f"{self.PREFIX}/analises", json=SCM_REQUEST)

        assert resp.status_code == 501
        assert "enable_scm" in resp.json()["detail"].lower() or "enable" in resp.json()["detail"].lower()

    def test_did_still_returns_202(self):
        """Métodos estáveis continuam retornando 202 Accepted."""
        from app.schemas.impacto_economico import EconomicImpactAnalysisResponse

        now = datetime.now(tz=timezone.utc)
        analysis = EconomicImpactAnalysisResponse(
            id=uuid.uuid4(), tenant_id=TENANT_ID, user_id=USER_ID,
            status="queued", method="did", created_at=now, updated_at=now,
        )
        svc = MagicMock()
        svc.create_queued = AsyncMock(return_value=analysis)

        with patch(
            "app.api.v1.impacto_economico.router.run_economic_impact_analysis"
        ) as mock_task:
            mock_task.delay = MagicMock()
            client = self._make_client(svc)
            resp = client.post(f"{self.PREFIX}/analises", json=BASE_REQUEST)

        assert resp.status_code == 202
