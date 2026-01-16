"""
Base de dados SQLAlchemy.

Configuração assíncrona e sessão para o PostgreSQL.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# Engine assíncrono
engine = create_async_engine(
    settings.postgres_url,
    echo=settings.debug,
    pool_size=settings.postgres_pool_size,
    max_overflow=settings.postgres_max_overflow,
)

# Session factory assíncrono
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Classe base para todos os modelos SQLAlchemy."""

    pass


async def get_db() -> AsyncSession:
    """
    Dependency para injetar sessão de banco nos endpoints.

    Yields:
        AsyncSession: Sessão assíncrona do PostgreSQL
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
