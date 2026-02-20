"""
Alembic Environment Configuration.

Configuração para migrations assíncronas com SQLAlchemy e PostgreSQL.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Importar modelos para autogenerate
from app.db.base import Base
from app.db.models.tenant import Tenant
from app.db.models.user import User
from app.db.models.dashboard_view import DashboardView
from app.db.models.economic_impact_analysis import EconomicImpactAnalysis  # noqa: F401
from app.db.models.tenant_module_permission import TenantModulePermission  # noqa: F401
from app.db.models.audit_log import AuditLog  # noqa: F401
from app.db.models.notification_preference import NotificationPreference  # noqa: F401

# Importar configurações
from app.config import get_settings

settings = get_settings()

# Alembic Config object
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData para autogenerate
target_metadata = Base.metadata


def get_url():
    """Retorna URL de conexão síncrona para Alembic."""
    return settings.sync_postgres_url


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Configura a URL do banco e gera o script SQL sem conectar.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Executa migrations em modo online."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in 'online' mode assíncrono.

    Neste cenário, precisamos criar um engine e conectar
    de forma assíncrona.
    """
    configuration = config.get_section(config.config_ini_section)
    # Usar URL assíncrona com asyncpg para migrations
    configuration["sqlalchemy.url"] = settings.postgres_url

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
