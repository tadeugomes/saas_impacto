"""
Aplicação Principal FastAPI - SaaS Impacto Portuário

Entry point do servidor REST API com suporte a multi-tenancy.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.tenant import TenantContextMiddleware
from app.api.v1 import auth
from app.api.v1.indicators import module1_router, generic_router
from app.api.v1.reports import router as reports_router
from app.api.v1.impacto_economico.router import router as impacto_economico_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.

    Startup: Conexões, pools, etc.
    Shutdown: Limpeza de recursos
    """
    # Startup
    print(f"🚀 {settings.app_name} v{settings.app_version} starting...")
    print(f"📊 Environment: {settings.environment}")

    yield

    # Shutdown
    print("👋 Shutting down...")


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

# Multi-tenancy (deve ser registrado ANTES de rotas que usam get_tenant_id)
app.add_middleware(TenantContextMiddleware)


# =====================================================
# Rotas API v1
# =====================================================

from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")

# Incluir routers
api_router.include_router(auth.router)
api_router.include_router(module1_router)
api_router.include_router(generic_router)
api_router.include_router(reports_router)
api_router.include_router(impacto_economico_router)

app.include_router(api_router)


# =====================================================
# Health Check
# =====================================================

@app.get("/")
async def root():
    """Health check básico."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "healthy",
        "environment": settings.environment,
    }


@app.get("/health")
async def health():
    """Health check detalhado."""
    return {
        "status": "healthy",
        "database": "connected",  # TODO: Verificar conexão real
        "bigquery": "connected",  # TODO: Verificar conexão real
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
