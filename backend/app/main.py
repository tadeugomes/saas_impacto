"""
Aplicação Principal FastAPI - SaaS Impacto Portuário

Entry point do servidor REST API com suporte a multi-tenancy.
"""

from app.core.logging import configure_structlog, get_logger
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from time import perf_counter
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import get_settings
from app.core.audit import AuditMiddleware
from app.core.rate_limit import RateLimitMiddleware
from app.core.tenant import TenantContextMiddleware
from app.api.v1 import auth
from app.api.v1.indicators import module1_router, generic_router
from app.api.v1.admin import router as admin_router
from app.api.v1.reports import router as reports_router
from app.api.v1.users import router as users_router
from app.api.v1.impacto_economico.router import router as impacto_economico_router
from app.db.base import engine
from app.db.bigquery.client import BigQueryError, BigQueryClient, get_bigquery_client
import redis.asyncio as aioredis
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

settings = get_settings()
configure_structlog()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.

    Startup: Conexões, pools, etc.
    Shutdown: Limpeza de recursos
    """
    # Startup
    logger.info(
        "startup_started",
        event="app_start",
        app_name=settings.app_name,
        app_version=settings.app_version,
        environment=settings.environment,
    )

    yield

    # Shutdown
    logger.info("shutdown", event="app_shutdown")


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Middleware de observabilidade básica com duração de request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-Id") or request.headers.get(
            "X-Request-ID"
        ) or str(uuid4())
        request.state.request_id = request_id
        start = perf_counter()

        response = await call_next(request)

        elapsed_ms = (perf_counter() - start) * 1000
        response.headers["X-Request-Id"] = request_id
        response.headers["X-Request-Duration-Ms"] = f"{elapsed_ms:.2f}"

        logger.info(
            "request_completed",
            event="http_request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": getattr(response, "status_code", None),
                "duration_ms": round(elapsed_ms, 2),
                "tenant_id": str(getattr(request.state, "tenant_id", "")),
            },
        )
        return response


# Criar aplicação FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Sistema de Análise do Impacto Econômico do Setor Portuário Brasileiro",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)


# =====================================================
# Middlewares
# =====================================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestTimingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuditMiddleware)

# Multi-tenancy (deve ser registrado ANTES de rotas que usam get_tenant_id)
app.add_middleware(TenantContextMiddleware)


def _build_health_result() -> dict[str, Any]:
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


async def _check_postgres() -> dict[str, Any]:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "connected"}
    except (Exception, SQLAlchemyError) as exc:
        return {"status": "disconnected", "error": str(exc)}


async def _check_bigquery() -> dict[str, Any]:
    try:
        client: BigQueryClient = get_bigquery_client()
        await client.get_dry_run_results("SELECT 1 AS value")
        return {"status": "connected"}
    except Exception as exc:
        if isinstance(exc, BigQueryError):
            return {"status": "disconnected", "error": exc.message}
        return {"status": "disconnected", "error": str(exc)}


async def _check_redis() -> dict[str, Any]:
    redis_client = aioredis.from_url(settings.redis_url)
    try:
        ping_result = await redis_client.ping()
        if ping_result is True:
            return {"status": "connected"}
        return {"status": "disconnected", "error": f"ping={ping_result!r}"}
    except Exception as exc:
        return {"status": "disconnected", "error": str(exc)}
    finally:
        await redis_client.aclose()


async def _collect_dependency_checks() -> dict[str, Any]:
    postgres = await _check_postgres()
    redis_check = await _check_redis()
    bigquery = await _check_bigquery()

    return {
        "dependencies": {
            "postgres": postgres,
            "redis": redis_check,
            "bigquery": bigquery,
        },
    }


# =====================================================
# Rotas API v1
# =====================================================

from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")

# Incluir routers
api_router.include_router(auth.router)
api_router.include_router(admin_router)
api_router.include_router(module1_router)
api_router.include_router(generic_router)
api_router.include_router(reports_router)
api_router.include_router(users_router)
api_router.include_router(impacto_economico_router)

app.include_router(api_router)


# =====================================================
# Health Check
# =====================================================

@app.get("/")
async def root():
    """Health check básico."""
    payload = _build_health_result()
    payload["status"] = "healthy"
    return payload


@app.get("/health")
async def health():
    """Health check simples: sempre retorna resumo consolidado."""
    payload = _build_health_result()
    payload["status"] = "healthy"
    checks = await _collect_dependency_checks()
    payload.update(checks)
    return payload


@app.get("/health/ready")
async def ready():
    """Readiness para orquestradores (carregamento de tráfego)."""
    payload = _build_health_result()
    checks = await _collect_dependency_checks()
    payload.update(checks)

    all_connected = all(
        dependency.get("status") == "connected"
        for dependency in checks["dependencies"].values()
    )

    if all_connected:
        payload["status"] = "ready"
        return payload

    payload["status"] = "unready"
    payload["status_code"] = 503
    from fastapi import HTTPException
    raise HTTPException(status_code=503, detail=payload)


@app.get("/health/live")
async def live():
    """Liveness: verifica se o processo está vivo."""
    payload = _build_health_result()
    payload["status"] = "alive"
    return payload


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
