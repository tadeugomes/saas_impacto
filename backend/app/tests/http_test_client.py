"""Utilitários de cliente HTTP para testes de rota FastAPI.

Usa httpx + ASGITransport com wrapper síncrono para evitar dependência
direta de ``fastapi.testclient.TestClient`` em ambientes de versões
recentes de httpx/starlette.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

import httpx


class _SyncASGIClient:
    """Cliente HTTP síncrono mínimo para requests em apps ASGI."""

    def __init__(self, async_client: httpx.AsyncClient):
        self._async_client = async_client

    def _run(self, method: str, path: str, **kwargs: Dict[str, Any]):
        return asyncio.run(self._async_client.request(method=method, url=path, **kwargs))

    def get(self, path: str, **kwargs: Dict[str, Any]):
        return self._run("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Dict[str, Any]):
        return self._run("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Dict[str, Any]):
        return self._run("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs: Dict[str, Any]):
        return self._run("DELETE", path, **kwargs)

    def close(self):
        asyncio.run(self._async_client.aclose())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


def make_sync_asgi_client(app):
    """Cria cliente HTTP síncrono para uma app FastAPI usando ASGITransport."""
    transport = httpx.ASGITransport(app=app)
    async_client = httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        follow_redirects=True,
    )
    return _SyncASGIClient(async_client)

