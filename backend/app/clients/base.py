"""
Cliente HTTP base assíncrono para APIs públicas brasileiras.

Fornece retry com backoff exponencial, cache Redis via IndicatorQueryCache,
rate-limiting e logging estruturado. Todas as subclasses (BacenClient,
IbgeClient etc.) herdam deste cliente.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

import httpx

from app.services.indicator_query_cache import IndicatorQueryCache

logger = logging.getLogger(__name__)


class PublicApiError(Exception):
    """Exceção base para erros de APIs externas (espelha BigQueryError)."""

    def __init__(
        self,
        message: str,
        api_name: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[str] = None,
    ):
        self.message = message
        self.api_name = api_name
        self.url = url
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class BasePublicApiClient:
    """
    Cliente HTTP assíncrono base com retry, cache e rate-limiting.

    Padrão idêntico ao BigQueryClient:
    - Lazy initialization do httpx.AsyncClient
    - Cache via IndicatorQueryCache (Redis)
    - Retry com backoff exponencial (1s, 2s, 4s)
    - Rate-limit handling (429 + Retry-After)
    """

    MAX_RETRIES = 3

    def __init__(self, base_url: str, api_name: str, timeout: float = 30.0):
        self.base_url = base_url
        self.api_name = api_name
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._cache = IndicatorQueryCache()

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazy init com connection pooling."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self._timeout,
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
                follow_redirects=True,
            )
        return self._client

    async def get_cached(
        self,
        cache_key: str,
        fetcher,
        *,
        ttl: int = 3600,
    ) -> Any:
        """Verifica cache -> executa fetcher se miss -> salva no cache."""
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return cached
        data = await fetcher()
        await self._cache.set(cache_key, data, ttl=ttl)
        return data

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> Any:
        """
        Request com retry (3x, backoff exponencial 1s->2s->4s).

        Trata 429 (rate-limit) e 5xx (server error) com retry.
        Demais erros HTTP levantam PublicApiError imediatamente.
        """
        client = await self._get_client()
        last_error: Optional[Exception] = None

        for attempt in range(self.MAX_RETRIES):
            try:
                resp = await client.request(
                    method, path, params=params, headers=headers
                )
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                last_error = e
                code = e.response.status_code
                if code == 429:
                    retry_after = int(
                        e.response.headers.get("Retry-After", 2**attempt)
                    )
                    logger.warning(
                        "public_api_rate_limited",
                        api=self.api_name,
                        path=path,
                        retry_after=retry_after,
                    )
                    await asyncio.sleep(retry_after)
                elif code >= 500:
                    logger.warning(
                        "public_api_server_error",
                        api=self.api_name,
                        path=path,
                        status=code,
                        attempt=attempt + 1,
                    )
                    await asyncio.sleep(2**attempt)
                else:
                    raise PublicApiError(
                        message=f"HTTP {code}: {e.response.text[:200]}",
                        api_name=self.api_name,
                        url=str(e.request.url),
                        status_code=code,
                    )
            except httpx.TransportError as e:
                last_error = e
                logger.warning(
                    "public_api_transport_error",
                    api=self.api_name,
                    path=path,
                    error=str(e),
                    attempt=attempt + 1,
                )
                await asyncio.sleep(2**attempt)

        raise PublicApiError(
            message=f"Falha após {self.MAX_RETRIES} tentativas: {last_error}",
            api_name=self.api_name,
        )

    async def get(self, path: str, *, params: Optional[dict] = None) -> Any:
        """Convenience wrapper para GET requests."""
        return await self._request("GET", path, params=params)

    async def close(self) -> None:
        """Fecha o cliente HTTP (chamado no shutdown da aplicação)."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
