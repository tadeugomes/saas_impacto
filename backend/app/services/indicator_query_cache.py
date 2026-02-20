"""Camada simples de cache para resultados de query.

Objetivo:
  - centralizar lógica de chave e fallback de conectividade
  - permitir cache em Redis quando disponível
  - retornar comportamento seguro (sem impacto) quando Redis estiver off-line
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Optional

import redis.asyncio as aioredis

from app.config import get_settings


class IndicatorQueryCache:
    """Cache assíncrono para resultados de consultas de indicadores."""

    def __init__(self, enabled: Optional[bool] = None, ttl_seconds: Optional[int] = None):
        settings = get_settings()
        self.enabled = settings.bq_cache_enabled if enabled is None else bool(enabled)
        self.ttl_seconds = (
            settings.bq_cache_ttl_seconds if ttl_seconds is None else int(ttl_seconds)
        )
        self._redis_url = settings.redis_url
        self._redis: Optional[aioredis.Redis] = None

    @staticmethod
    def make_key(module: int, codigo: str, tenant_id: Optional[str], payload: dict) -> str:
        """
        Monta chave determinística por módulo, indicador, tenant e payload.

        Exemplo: bq:5:ind-5.01:<hash>
        """
        normalized = json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()
        return f"bq:{module}:{codigo}:{tenant_id or 'public'}:{digest}"

    async def get(self, key: str) -> Optional[list[dict[str, Any]]]:
        """Busca resultado no cache; retorna None em falha."""
        if not self.enabled:
            return None

        try:
            client = await self._get_redis_client()
            cached = await client.get(key)
            if not cached:
                return None
            if isinstance(cached, (bytes, bytearray)):
                cached = cached.decode("utf-8")
            payload = json.loads(cached)
            if isinstance(payload, list):
                return payload
            return None
        except Exception:
            return None

    async def set(self, key: str, value: list[dict[str, Any]]) -> None:
        """Armazena valor no cache; falha silenciosa para não quebrar consultas."""
        if not self.enabled:
            return
        try:
            client = await self._get_redis_client()
            await client.set(key, json.dumps(value, ensure_ascii=False), ex=self.ttl_seconds)
        except Exception:
            return

    async def _get_redis_client(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

