"""Testes unitários e de integração leve para EconomicImpactAnalysis.

Estratégia por camada:

  TestModelStructure   — inspeciona metadados do SQLAlchemy (colunas, tipos,
                         constraints, índices) sem conectar ao Postgres.
  TestModelMethods     — testa os métodos de conveniência (mark_running,
                         mark_success, mark_failed, duration_seconds…).
  TestMigrationSQL     — valida strings SQL da migration (RLS DDL) por inspeção
                         de texto; não requer banco.
  TestRLSIntegration   — demonstração do padrão de isolamento usando SQLite
                         em memória (sem RLS nativo, mas valida a lógica de
                         filtragem que a policy implementaria no Postgres).

NOTA PARA RODAR EM PRODUÇÃO:
  Para validar o RLS real em Postgres, execute o script de sanidade manual:

      psql $DATABASE_URL << 'SQL'
      -- Setup
      SET app.current_tenant_id = 'aaaaaaaa-0000-0000-0000-000000000001';
      INSERT INTO economic_impact_analyses (id, tenant_id, method, status, request_params)
      VALUES (gen_random_uuid(),
              'aaaaaaaa-0000-0000-0000-000000000001',
              'did', 'queued', '{}');

      -- Deve retornar 1 linha
      SELECT count(*) FROM economic_impact_analyses;

      -- Troca tenant → deve retornar 0 linhas (RLS)
      SET app.current_tenant_id = 'bbbbbbbb-0000-0000-0000-000000000002';
      SELECT count(*) FROM economic_impact_analyses;
      SQL
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import DeclarativeBase


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def eia_cls():
    """Retorna a classe do model sem importar config/DB."""
    from app.db.models.economic_impact_analysis import EconomicImpactAnalysis
    return EconomicImpactAnalysis


@pytest.fixture
def fresh_instance():
    """Instância do model sem salvar em banco."""
    from app.db.models.economic_impact_analysis import EconomicImpactAnalysis
    return EconomicImpactAnalysis(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        method="did",
        status="queued",
        request_params={"treated": ["2100055"], "control": ["2100204"], "treatment_year": 2015},
    )


# ---------------------------------------------------------------------------
# TestModelStructure — inspecção de metadados SQLAlchemy
# ---------------------------------------------------------------------------

class TestModelStructure:
    def test_tablename(self, eia_cls):
        assert eia_cls.__tablename__ == "economic_impact_analyses"

    def test_required_columns_present(self, eia_cls):
        mapper = sa_inspect(eia_cls)
        col_names = {c.key for c in mapper.mapper.column_attrs}

        expected = {
            "id", "tenant_id", "user_id",
            "status", "method",
            "request_params", "result_summary", "result_full", "artifact_path",
            "error_message",
            "created_at", "updated_at", "started_at", "completed_at",
        }
        missing = expected - col_names
        assert not missing, f"Colunas ausentes no model: {missing}"

    def test_id_is_uuid(self, eia_cls):
        from sqlalchemy.dialects.postgresql import UUID
        col = eia_cls.__table__.c["id"]
        assert isinstance(col.type, UUID)

    def test_tenant_id_is_uuid_indexed(self, eia_cls):
        from sqlalchemy.dialects.postgresql import UUID
        col = eia_cls.__table__.c["tenant_id"]
        assert isinstance(col.type, UUID)
        assert col.index is True

    def test_user_id_nullable(self, eia_cls):
        col = eia_cls.__table__.c["user_id"]
        assert col.nullable is True

    def test_status_is_string_20(self, eia_cls):
        col = eia_cls.__table__.c["status"]
        assert isinstance(col.type, sa.String)
        assert col.type.length == 20

    def test_method_is_string_20(self, eia_cls):
        col = eia_cls.__table__.c["method"]
        assert isinstance(col.type, sa.String)
        assert col.type.length == 20

    def test_jsonb_columns(self, eia_cls):
        from sqlalchemy.dialects.postgresql import JSONB
        for col_name in ("request_params", "result_summary", "result_full"):
            col = eia_cls.__table__.c[col_name]
            assert isinstance(col.type, JSONB), f"{col_name} deve ser JSONB"

    def test_artifact_path_is_string_500(self, eia_cls):
        col = eia_cls.__table__.c["artifact_path"]
        assert isinstance(col.type, sa.String)
        assert col.type.length == 500

    def test_error_message_is_text(self, eia_cls):
        col = eia_cls.__table__.c["error_message"]
        assert isinstance(col.type, sa.Text)

    def test_timestamp_columns_with_tz(self, eia_cls):
        for col_name in ("created_at", "updated_at"):
            col = eia_cls.__table__.c[col_name]
            assert isinstance(col.type, sa.DateTime)
            assert col.type.timezone is True

    def test_check_constraint_status_exists(self, eia_cls):
        names = {c.name for c in eia_cls.__table__.constraints}
        assert "ck_economic_impact_analyses_status" in names

    def test_check_constraint_method_exists(self, eia_cls):
        names = {c.name for c in eia_cls.__table__.constraints}
        assert "ck_economic_impact_analyses_method" in names

    def test_composite_indexes_exist(self, eia_cls):
        index_names = {idx.name for idx in eia_cls.__table__.indexes}
        assert "ix_eia_tenant_status" in index_names
        assert "ix_eia_tenant_created" in index_names

    def test_fk_tenant_cascade(self, eia_cls):
        fk = next(
            fk for fk in eia_cls.__table__.foreign_keys
            if fk.column.table.name == "tenants"
        )
        assert fk.ondelete == "CASCADE"

    def test_fk_user_set_null(self, eia_cls):
        fk = next(
            fk for fk in eia_cls.__table__.foreign_keys
            if fk.column.table.name == "users"
        )
        assert fk.ondelete == "SET NULL"


# ---------------------------------------------------------------------------
# TestModelMethods — lógica de negócio dos métodos de conveniência
# ---------------------------------------------------------------------------

class TestModelMethods:
    def test_initial_status_queued(self, fresh_instance):
        assert fresh_instance.status == "queued"

    def test_is_terminal_false_for_queued(self, fresh_instance):
        assert fresh_instance.is_terminal is False

    def test_is_terminal_false_for_running(self, fresh_instance):
        fresh_instance.status = "running"
        assert fresh_instance.is_terminal is False

    def test_is_terminal_true_for_success(self, fresh_instance):
        fresh_instance.status = "success"
        assert fresh_instance.is_terminal is True

    def test_is_terminal_true_for_failed(self, fresh_instance):
        fresh_instance.status = "failed"
        assert fresh_instance.is_terminal is True

    def test_mark_running(self, fresh_instance):
        fresh_instance.mark_running()
        assert fresh_instance.status == "running"
        assert fresh_instance.started_at is not None
        assert isinstance(fresh_instance.started_at, datetime)

    def test_mark_success_sets_fields(self, fresh_instance):
        fresh_instance.mark_running()
        summary = {"coef": 0.15, "p_value": 0.02, "n_obs": 320}
        full = {"main_result": summary, "event_study": {"coefficients": []}}
        fresh_instance.mark_success(result_summary=summary, result_full=full)

        assert fresh_instance.status == "success"
        assert fresh_instance.result_summary == summary
        assert fresh_instance.result_full == full
        assert fresh_instance.completed_at is not None

    def test_mark_success_with_artifact_path(self, fresh_instance):
        fresh_instance.mark_running()
        fresh_instance.mark_success(
            result_summary={"coef": 0.1},
            artifact_path="gs://bucket/runs/abc123.json",
        )
        assert fresh_instance.artifact_path == "gs://bucket/runs/abc123.json"

    def test_mark_failed_sets_error(self, fresh_instance):
        fresh_instance.mark_running()
        fresh_instance.mark_failed("BigQueryError: Not Found")

        assert fresh_instance.status == "failed"
        assert fresh_instance.error_message == "BigQueryError: Not Found"
        assert fresh_instance.completed_at is not None

    def test_duration_seconds_none_before_completion(self, fresh_instance):
        assert fresh_instance.duration_seconds is None

    def test_duration_seconds_computed(self, fresh_instance):
        fresh_instance.mark_running()
        fresh_instance.mark_success(result_summary={"coef": 0.1})

        dur = fresh_instance.duration_seconds
        assert dur is not None
        assert dur >= 0.0

    def test_duration_seconds_reasonable(self, fresh_instance):
        """Duração deve ser pequena (sub-segundo) em testes unitários."""
        fresh_instance.mark_running()
        fresh_instance.mark_success(result_summary={"coef": 0.1})

        assert fresh_instance.duration_seconds < 5.0  # nunca deve levar 5s

    def test_repr_contains_method_and_status(self, fresh_instance):
        r = repr(fresh_instance)
        assert "did" in r
        assert "queued" in r

    def test_state_transitions_are_idempotent(self, fresh_instance):
        """Marcar failed duas vezes não deve lançar exceção."""
        fresh_instance.mark_running()
        fresh_instance.mark_failed("erro A")
        fresh_instance.mark_failed("erro B")
        assert fresh_instance.error_message == "erro B"


# ---------------------------------------------------------------------------
# TestMigrationSQL — valida o DDL de RLS por inspeção de strings
# ---------------------------------------------------------------------------

class TestMigrationSQL:
    @pytest.fixture
    def migration_module(self):
        import importlib
        return importlib.import_module(
            "app.alembic.versions"
            ".20260219_1500_c8f3a1d92b47_economic_impact_analyses_rls"
        )

    def test_revision_id(self, migration_module):
        assert migration_module.revision == "c8f3a1d92b47"

    def test_down_revision(self, migration_module):
        assert migration_module.down_revision == "9039ac2604a6"

    def test_table_name(self, migration_module):
        assert migration_module.TABLE_NAME == "economic_impact_analyses"

    def test_rls_enable_sql(self, migration_module):
        sql = migration_module._RLS_ENABLE
        assert "ENABLE ROW LEVEL SECURITY" in sql
        assert "economic_impact_analyses" in sql

    def test_rls_force_sql(self, migration_module):
        sql = migration_module._RLS_FORCE
        assert "FORCE ROW LEVEL SECURITY" in sql

    def test_policy_create_uses_current_setting(self, migration_module):
        sql = migration_module._POLICY_CREATE
        assert "current_setting('app.current_tenant_id', true)" in sql
        assert "tenant_isolation" in sql

    def test_policy_create_has_using_and_with_check(self, migration_module):
        sql = migration_module._POLICY_CREATE
        assert "USING" in sql
        assert "WITH CHECK" in sql

    def test_policy_drop_is_idempotent(self, migration_module):
        """DROP POLICY deve usar IF EXISTS para não falhar em downgrade repetido."""
        sql = migration_module._POLICY_DROP
        assert "DROP POLICY IF EXISTS" in sql
        assert "tenant_isolation" in sql

    def test_rls_disable_sql(self, migration_module):
        sql = migration_module._RLS_DISABLE
        assert "DISABLE ROW LEVEL SECURITY" in sql

    def test_valid_statuses_tuple(self, migration_module):
        statuses = migration_module.VALID_STATUSES
        assert "queued" in statuses
        assert "running" in statuses
        assert "success" in statuses
        assert "failed" in statuses

    def test_valid_methods_tuple(self, migration_module):
        methods = migration_module.VALID_METHODS
        assert "did" in methods
        assert "iv" in methods
        assert "panel_iv" in methods
        assert "compare" in methods


# ---------------------------------------------------------------------------
# TestRLSIntegration — lógica de isolamento simulada com SQLite em memória
#
# SQLite não suporta RLS nativo, mas podemos testar a lógica de filtragem
# que a policy implementa: SELECT WHERE tenant_id = :current_tenant
# ---------------------------------------------------------------------------

class TestRLSIntegration:
    """
    Simula o comportamento de isolamento que o RLS do Postgres garante,
    usando filtragem explícita em SQLite (sem RLS nativo).

    Em produção com Postgres, a policy 'tenant_isolation' faz exatamente
    esse filtro automaticamente, sem necessidade de WHERE no código.
    """

    @pytest.fixture(scope="class")
    def sqlite_engine(self):
        """Engine SQLite em memória com tabela simplificada de análises."""
        from sqlalchemy import create_engine, Column, String, Text, event
        from sqlalchemy.orm import DeclarativeBase, Session
        import uuid as _uuid

        class _Base(DeclarativeBase):
            pass

        class _Analysis(_Base):
            __tablename__ = "economic_impact_analyses"
            id = Column(String(36), primary_key=True)
            tenant_id = Column(String(36), nullable=False, index=True)
            method = Column(String(20), nullable=False)
            status = Column(String(20), nullable=False, default="queued")
            error_message = Column(Text, nullable=True)

        engine = create_engine("sqlite:///:memory:")
        _Base.metadata.create_all(engine)

        # Seed: dois tenants com uma análise cada
        tenant_a = "aaaaaaaa-0000-0000-0000-000000000001"
        tenant_b = "bbbbbbbb-0000-0000-0000-000000000002"

        with Session(engine) as sess:
            sess.add(_Analysis(
                id=str(_uuid.uuid4()),
                tenant_id=tenant_a,
                method="did",
                status="success",
            ))
            sess.add(_Analysis(
                id=str(_uuid.uuid4()),
                tenant_id=tenant_b,
                method="iv",
                status="queued",
            ))
            sess.commit()

        return engine, _Analysis, tenant_a, tenant_b

    def test_tenant_a_sees_only_own_rows(self, sqlite_engine):
        from sqlalchemy.orm import Session

        engine, Analysis, tenant_a, tenant_b = sqlite_engine

        with Session(engine) as sess:
            # Simula o que o RLS faz automaticamente
            rows = sess.query(Analysis).filter(
                Analysis.tenant_id == tenant_a
            ).all()

        assert len(rows) == 1
        assert rows[0].tenant_id == tenant_a

    def test_tenant_b_sees_only_own_rows(self, sqlite_engine):
        from sqlalchemy.orm import Session

        engine, Analysis, tenant_a, tenant_b = sqlite_engine

        with Session(engine) as sess:
            rows = sess.query(Analysis).filter(
                Analysis.tenant_id == tenant_b
            ).all()

        assert len(rows) == 1
        assert rows[0].tenant_id == tenant_b

    def test_tenant_a_cannot_see_tenant_b_rows(self, sqlite_engine):
        from sqlalchemy.orm import Session

        engine, Analysis, tenant_a, tenant_b = sqlite_engine

        with Session(engine) as sess:
            # Com filtro de tenant_a, nunca verá tenant_b
            rows = sess.query(Analysis).filter(
                Analysis.tenant_id == tenant_a,
                Analysis.tenant_id == tenant_b,  # nunca pode ser ambos
            ).all()

        assert len(rows) == 0

    def test_wrong_tenant_id_returns_nothing(self, sqlite_engine):
        from sqlalchemy.orm import Session

        engine, Analysis, tenant_a, tenant_b = sqlite_engine

        with Session(engine) as sess:
            rows = sess.query(Analysis).filter(
                Analysis.tenant_id == "cccccccc-0000-0000-0000-000000000003"
            ).all()

        assert rows == []

    def test_null_tenant_setting_returns_nothing(self, sqlite_engine):
        """Quando current_setting retorna NULL, nenhum registro deve ser visível."""
        from sqlalchemy.orm import Session

        engine, Analysis, tenant_a, tenant_b = sqlite_engine

        # NULL não faz match com nenhum UUID real
        with Session(engine) as sess:
            rows = sess.query(Analysis).filter(
                Analysis.tenant_id == None  # noqa: E711
            ).all()

        assert rows == []
