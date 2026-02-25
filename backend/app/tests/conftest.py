"""Configuração global do pytest para testes unitários do backend.

Problema:
    ``app/db/base.py`` cria um engine SQLAlchemy assíncrono (asyncpg) no
    nível de módulo. Isso impede importar qualquer modelo (Tenant, User,
    EconomicImpactAnalysis…) em ambientes de CI sem Postgres/asyncpg.

Solução:
    Este conftest injeta stubs em ``sys.modules`` ANTES que qualquer módulo
    da aplicação seja importado, permitindo que os testes unitários inspecionem
    estruturas SQLAlchemy sem abrir conexões reais.

    Os testes de integração (``integration/``) e e2e (``e2e/``) devem rodar
    em ambientes com Postgres e asyncpg instalados, onde esses stubs serão
    substituídos pelos módulos reais.
"""
from __future__ import annotations

import os
import sys
import types
import unittest.mock as mock


# ---------------------------------------------------------------------------
# Stubs de módulos que requerem Postgres / credenciais GCP
# ---------------------------------------------------------------------------

def _inject_asyncpg_stub() -> None:
    """Injeta stub de asyncpg para evitar ImportError ao importar app.db.base."""
    if "asyncpg" in sys.modules:
        return  # já carregado (ambiente com asyncpg real)

    asyncpg_stub = types.ModuleType("asyncpg")
    asyncpg_stub.__version__ = "0.0.0-stub"
    sys.modules["asyncpg"] = asyncpg_stub

    # Sub-módulos referenciados internamente pelo SQLAlchemy asyncpg dialect
    for sub in (
        "asyncpg.connection",
        "asyncpg.exceptions",
        "asyncpg.pool",
        "asyncpg.protocol",
        "asyncpg.protocol.protocol",
    ):
        sys.modules[sub] = types.ModuleType(sub)


def _inject_google_cloud_stub() -> None:
    """Injeta stubs para google-cloud-bigquery (não instalado no CI unitário)."""
    for name in (
        "google",
        "google.cloud",
        "google.cloud.bigquery",
        "google.oauth2",
        "google.oauth2.service_account",
        "google.api_core",
        "google.api_core.exceptions",
    ):
        if name not in sys.modules:
            sys.modules[name] = types.ModuleType(name)

    # Exceções usadas pelo BigQueryClient
    import types as _t
    exc_mod = sys.modules["google.api_core.exceptions"]
    for exc_name in ("GoogleAPIError", "NotFound", "Forbidden", "BadRequest"):
        setattr(exc_mod, exc_name, type(exc_name, (Exception,), {}))

    # Mocks mínimos do bigquery
    bq_mod = sys.modules["google.cloud.bigquery"]
    bq_mod.Client = mock.MagicMock
    bq_mod.QueryJobConfig = mock.MagicMock
    bq_mod.ScalarQueryParameter = mock.MagicMock
    bq_mod.DatasetReference = mock.MagicMock
    bq_mod.TableReference = mock.MagicMock
    bq_mod.SchemaField = mock.MagicMock
    bq_mod.LoadJobConfig = mock.MagicMock
    bq_mod.WriteDisposition = mock.MagicMock
    bq_mod.Table = mock.MagicMock

    sa_stub = types.ModuleType("google.oauth2.service_account")
    sa_stub.Credentials = mock.MagicMock
    sys.modules["google.oauth2.service_account"] = sa_stub


def _set_env_defaults() -> None:
    """Seta variáveis de ambiente mínimas para que pydantic Settings não falhe."""
    defaults = {
        "POSTGRES_URL": "postgresql+asyncpg://user:pass@localhost/testdb",
        "SYNC_POSTGRES_URL": "postgresql+psycopg2://user:pass@localhost/testdb",
        "GCP_PROJECT_ID": "test-project",
        "GOOGLE_APPLICATION_CREDENTIALS": "",
        "BQ_LOCATION": "US",
        "BQ_DATASET_ANTAQ": "antaq",
        "BQ_DATASET_MARTS": "marts_impacto",
        "SECRET_KEY": "test-secret-key-32-chars-minimum!!",
        "JWT_SECRET_KEY": "test-jwt-secret-key-32chars-min!",
        "DEBUG": "false",
        "POSTGRES_POOL_SIZE": "1",
        "POSTGRES_MAX_OVERFLOW": "0",
        # Celery: usa sempre o modo "eager" em testes unitários
        # (executa a task inline, sem broker Redis real)
        "CELERY_BROKER_URL": "redis://localhost:6379/1",
        "CELERY_RESULT_BACKEND": "redis://localhost:6379/2",
    }
    for key, val in defaults.items():
        os.environ.setdefault(key, val)


def _configure_celery_eager() -> None:
    """Configura Celery para executar tasks de forma síncrona (sem broker/Redis).

    ``task_always_eager=True``: .delay() / .apply_async() executam inline.
    ``result_backend="cache+memory://"``: resultados em memória, sem Redis.
    ``task_eager_propagates=True``: exceções propagadas (útil para retry tests).
    """
    try:
        from app.tasks.celery_app import celery_app
        celery_app.conf.update(
            task_always_eager=True,
            task_eager_propagates=True,
            result_backend="cache+memory://",  # sem Redis no CI unitário
            broker_url="memory://",            # sem Redis no CI unitário
        )
    except Exception:
        pass  # Celery não disponível ou import circular → ignorar silenciosamente


# ---------------------------------------------------------------------------
# Executa os stubs antes de qualquer import de módulo da app
# ---------------------------------------------------------------------------
_inject_asyncpg_stub()
_inject_google_cloud_stub()
_set_env_defaults()
_configure_celery_eager()
