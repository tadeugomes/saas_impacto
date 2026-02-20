"""
Middleware de auditoria para registrar operações mutantes.
"""

from __future__ import annotations

from time import perf_counter
from app.core.logging import get_logger

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.security import decode_access_token
from app.db.base import AsyncSessionLocal
from app.services.audit_service import AuditService

logger = get_logger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """Registra ações de escrita/remoção em `audit_logs`."""

    _MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    def __init__(self, app):
        super().__init__(app)
        self._service = AuditService()

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method not in self._MUTATING_METHODS:
            return await call_next(request)

        start = perf_counter()
        response = await call_next(request)
        duration_ms = int((perf_counter() - start) * 1000)

        try:
            tenant_id = self._extract_tenant_id(request)
            if tenant_id is None:
                return response
            if (
                request.url.path == "/"
                or request.url.path.startswith("/api/v1/health")
                or request.url.path.startswith("/health")
            ):
                return response

            action = self._derive_action(request)
            if not action:
                return response

            user_id = self._extract_user_id(request)
            request_id = request.headers.get("X-Request-Id") or request.headers.get(
                "X-Request-ID"
            )

            async with AsyncSessionLocal() as db:
                await self._service.record_action(
                    db=db,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    action=action,
                    resource=request.url.path,
                    status_code=getattr(response, "status_code", None),
                    duration_ms=duration_ms,
                    ip=self._extract_ip(request),
                    request_id=request_id,
                    details={
                        "method": request.method,
                        "query": dict(request.query_params),
                    },
                )
        except Exception:
            logger.debug("Falha ao registrar auditoria", exc_info=True)

        return response

    @staticmethod
    def _extract_tenant_id(request: Request) -> str | None:
        raw_tenant_id = getattr(request.state, "tenant_id", None)
        if raw_tenant_id is not None:
            return str(raw_tenant_id)

        header_tenant_id = request.headers.get("X-Tenant-ID")
        if header_tenant_id:
            return header_tenant_id

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            payload = decode_access_token(auth_header.removeprefix("Bearer "))
            if payload and payload.get("tenant_id"):
                return str(payload.get("tenant_id"))
        return None

    @staticmethod
    def _extract_user_id(request: Request) -> str | None:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None
        payload = decode_access_token(auth_header.removeprefix("Bearer "))
        if not payload:
            return None
        return payload.get("sub")

    @staticmethod
    def _extract_ip(request: Request) -> str | None:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else None

    @staticmethod
    def _derive_action(request: Request) -> str | None:
        path = request.url.path
        if path.startswith("/api/v1/impacto-economico/analises") and request.method == "POST":
            return "create_analysis"
        if path.startswith("/api/v1/indicators/permissions"):
            return f"{request.method.lower()}_role_permission"
        if path.startswith("/api/v1/admin/"):
            return f"{request.method.lower()}_admin_resource"
        if request.method == "DELETE":
            return "delete_resource"
        if request.method == "PUT":
            return "update_resource"
        if request.method == "POST":
            return "create_resource"
        if request.method == "PATCH":
            return "update_resource"
        return None
