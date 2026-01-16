"""
Configurações centralizadas da aplicação usando Pydantic Settings.

Este módulo carrega e valida todas as variáveis de ambiente do arquivo .env
e fornece uma interface type-safe para acessá-las em toda a aplicação.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List

# Caminho base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / "backend" / ".env"


class Settings(BaseSettings):
    """Configurações da aplicação."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = "SaaS Impacto Portuário"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"
    secret_key: str
    allowed_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "saas_impacto"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_pool_size: int = 20
    postgres_max_overflow: int = 10

    @property
    def postgres_url(self) -> str:
        """URL de conexão PostgreSQL para SQLAlchemy."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_postgres_url(self) -> str:
        """URL de conexão síncrona para Alembic."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # BigQuery
    google_application_credentials: str
    gcp_project_id: str
    bq_location: str = "US"
    bq_dataset_antaq: str = "antaqdados.br_antaq_estatistico_aquaviario"
    bq_dataset_marts: str = "marts_impacto"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None
    redis_cache_ttl: int = 3600

    @property
    def redis_url(self) -> str:
        """URL de conexão Redis."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # JWT
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    jwt_algorithm: str = "HS256"
    jwt_secret_key: str

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Storage (S3/GCS)
    storage_backend: str = "gcs"
    gcs_bucket_name: str = "saas-impacto-reports"
    gcs_project_id: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_s3_bucket: str | None = None

    # Observability
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "saas-impacto-backend"
    otel_sampling_ratio: float = 1.0

    # Reports
    quarto_path: str = "/usr/bin/quarto"
    reports_output_path: str = "/tmp/reports"


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna instância cached de Settings.

    Usa lru_cache para garantir que as configurações sejam carregadas
    apenas uma vez e reutilizadas em toda a aplicação.

    Returns:
        Settings: Instância de configurações validadas
    """
    return Settings()
