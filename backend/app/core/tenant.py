"""
Middleware de Multi-tenancy.

Extrai e injeta o contexto de tenant em todas as requisições.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import uuid
from typing import Optional

from app.core.security import decode_access_token


# Public paths that don't require tenant identification
PUBLIC_PATHS = {
    "/",
    "/health",
    "/health/ready",
    "/health/live",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
}


def extract_tenant_id_from_token(auth_header: Optional[str]) -> Optional[str]:
    """
    Extrai tenant_id do token JWT.

    Args:
        auth_header: Header Authorization com Bearer token

    Returns:
        tenant_id como string se encontrado, None caso contrário
    """
    if not auth_header:
        return None

    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]  # Remove "Bearer " prefix
    payload = decode_access_token(token)

    if payload and "tenant_id" in payload:
        return payload["tenant_id"]

    return None


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware que extrai o tenant_id do token JWT e injeta no contexto.

    O token JWT deve conter o campo 'sub' com o user_id e 'tenant_id'.
    Este middleware garante que toda requisição tenha um tenant_id associado.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip tenant check for public paths
        if request.url.path in PUBLIC_PATHS or request.url.path.startswith("/static"):
            return await call_next(request)

        # 1. Extrair tenant_id do header X-Tenant-ID (prioridade)
        tenant_id = request.headers.get("X-Tenant-ID")

        # 2. Se não tiver, tenta extrair do JWT token
        if not tenant_id:
            auth_header = request.headers.get("Authorization")
            tenant_id = extract_tenant_id_from_token(auth_header)

        # 3. DEVELOPMENT MODE: Use default tenant if no auth provided
        if not tenant_id:
            # Default demo tenant for development
            tenant_id = "00000000-0000-0000-0000-000000000001"

        # 4. Validar formato UUID
        try:
            tenant_uuid = uuid.UUID(tenant_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid tenant ID format",
            )

        # 5. Adicionar ao state da requisição
        request.state.tenant_id = tenant_uuid
        request.state.tenant_id_str = tenant_id

        # 6. Processar request
        response = await call_next(request)

        return response


async def get_tenant_id(request: Request) -> uuid.UUID:
    """
    Dependency para injetar tenant_id nos endpoints.

    Args:
        request: Objeto de requisição FastAPI

    Returns:
        UUID do tenant

    Raises:
        HTTPException: Se tenant_id não estiver no contexto
    """
    tenant_id = getattr(request.state, "tenant_id", None)

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant context not found",
        )

    return tenant_id
