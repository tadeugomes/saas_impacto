"""Middleware de rate limiting por tenant."""

from __future__ import annotations

import time

import redis.asyncio as aioredis
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import get_settings
from app.core.security import decode_access_token
from app.core.tenant import PUBLIC_PATHS

settings = get_settings()


def _normalize_plan(plan: str | None) -> str:
    normalized = (plan or "basic").lower().strip()
    if normalized not in {"basic", "pro", "enterprise"}:
        return "basic"
    return normalized


def _is_analysis_route(path: str) -> bool:
    return path.startswith("/api/v1/impacto-economico/analises")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Aplica limites por janela de tempo usando Redis."""

    def __init__(self, app):
        super().__init__(app)
        self._settings = settings
        self._default_tenant_id = "00000000-0000-0000-0000-000000000001"

    async def dispatch(self, request: Request, call_next):
        if not self._settings.rate_limiting_enabled:
            return await call_next(request)

        path = request.url.path
        if path in PUBLIC_PATHS:
            return await call_next(request)

        # Prefixos públicos adicionais
        if path.startswith("/docs") or path.startswith("/openapi"):
            return await call_next(request)

        tenant_id = str(getattr(request.state, "tenant_id", self._default_tenant_id))
        plan = self._tenant_plan_from_request(request)
        limit, window_seconds = self._resolve_limit(plan, path)

        # Se o endpoint foi configurado com limite <= 0, ignora.
        if limit <= 0:
            return await call_next(request)

        allowed, remaining, reset_ts = await self._consume(tenant_id, plan, path, limit, window_seconds)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": (
                        f"Rate limit exceeded for tenant {tenant_id} on {plan} "
                        f"plan, path {path}"
                    )
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_ts),
                    "Retry-After": str(max(1, reset_ts - int(time.time()))),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(reset_ts)
        return response

    async def _consume(
        self,
        tenant_id: str,
        plan: str,
        path: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int, int]:
        """Incrementa contador no Redis e decide se mantém dentro do teto."""
        bucket_key = f"{self._bucket(plan, path)}:{tenant_id}:{int(time.time() // window_seconds)}"
        reset_ts = int(time.time() // window_seconds * window_seconds + window_seconds)

        try:
            redis_client = aioredis.from_url(self._settings.redis_url, decode_responses=True)
            try:
                used = int(await redis_client.incr(bucket_key))
                if used == 1:
                    await redis_client.expire(bucket_key, window_seconds)
                if used > limit:
                    return False, max(0, limit - used), reset_ts
                return True, limit - used, reset_ts
            finally:
                await redis_client.aclose()
        except Exception:
            # Em falha de Redis, não bloqueia tráfego.
            return True, limit - 1, reset_ts

    @staticmethod
    def _bucket(plan: str, path: str) -> str:
        return (
            f"analises:{plan}"
            if _is_analysis_route(path)
            else f"general:{plan}"
        )

    @staticmethod
    def _tenant_plan_from_request(request: Request) -> str:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return "basic"
        payload = decode_access_token(auth_header[7:])
        if not isinstance(payload, dict):
            return "basic"
        return _normalize_plan(payload.get("tenant_plan", ""))

    def _resolve_limit(self, plan: str, path: str) -> tuple[int, int]:
        if _is_analysis_route(path):
            window_seconds = 3600
            if plan == "enterprise":
                return self._settings.rate_limit_enterprise_analyses_per_hour, window_seconds
            if plan == "pro":
                return self._settings.rate_limit_pro_analyses_per_hour, window_seconds
            return self._settings.rate_limit_basic_analyses_per_hour, window_seconds

        window_seconds = max(1, self._settings.rate_limit_window_seconds)
        if plan == "enterprise":
            return self._settings.rate_limit_enterprise_rpm, window_seconds
        if plan == "pro":
            return self._settings.rate_limit_pro_rpm, window_seconds
        return self._settings.rate_limit_basic_rpm, window_seconds
