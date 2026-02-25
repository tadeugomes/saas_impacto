"""
Servicos de politica por tenant (E4/E5).

Centraliza leitura/escrita de configuracoes de:
- municipio de influencia por instalacao
- allowlist de municipios
- limite de bytes por consulta
"""

import json
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.bigquery.client import BigQueryClient, get_bigquery_client
from app.db.models.tenant import Tenant

BD_DADOS_DIRETORIO_MUNICIPIO = "basedosdados.br_bd_diretorios_brasil.municipio"


def _as_float(value: Any, default: float = 1.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class TenantPolicyService:
    """Gerencia politica de acesso/configuracao por tenant."""

    _INFLUENCE_MAP_KEYS = ("municipio_influencia", "area_influencia")

    def __init__(self, bq_client: Optional[BigQueryClient] = None):
        self.bq_client = bq_client or get_bigquery_client()

    @staticmethod
    def _default_policy() -> dict[str, Any]:
        return {
            "allowed_installations": [],
            "allowed_municipios": [],
            "municipio_influencia": {},
            "area_influencia": {},
            "max_bytes_per_query": None,
        }

    @classmethod
    def _normalize_influence_entry(cls, item: Any) -> Optional[dict[str, Any]]:
        """Normaliza um municipio de influencia."""
        if not isinstance(item, dict):
            return None
        id_municipio = str(item.get("id_municipio", "")).strip()
        if not id_municipio:
            return None
        return {
            "id_municipio": id_municipio,
            "peso": _as_float(item.get("peso"), default=1.0),
        }

    @classmethod
    def _normalize_influence_map(cls, raw_value: Any) -> dict[str, list[dict[str, Any]]]:
        """Normaliza mapa {'instalacao': [{'id_municipio', ...}]}."""
        if not isinstance(raw_value, dict):
            return {}
        normalized: dict[str, list[dict[str, Any]]] = {}
        for instalacao, municipios in raw_value.items():
            if not isinstance(municipios, list):
                continue
            cleaned = []
            seen: set[str] = set()
            for item in municipios:
                normalized_item = cls._normalize_influence_entry(item)
                if normalized_item is None:
                    continue
                id_municipio = normalized_item["id_municipio"]
                if id_municipio in seen:
                    continue
                seen.add(id_municipio)
                cleaned.append(normalized_item)
            normalized[str(instalacao)] = cleaned
        return normalized

    @classmethod
    def _read_influence_map(cls, payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        """Carrega municipio_de_influencia com fallback de area_influencia (legado)."""
        merged: dict[str, list[dict[str, Any]]] = {}
        for key in cls._INFLUENCE_MAP_KEYS:
            raw_map = cls._normalize_influence_map(payload.get(key, {}))
            for instalacao, municipios in raw_map.items():
                merged.setdefault(str(instalacao), [])
                existing_ids = {item["id_municipio"] for item in merged[str(instalacao)]}
                for item in municipios:
                    if item["id_municipio"] in existing_ids:
                        continue
                    merged[str(instalacao)].append(item)
                    existing_ids.add(item["id_municipio"])
        return merged

    @classmethod
    def parse_policy(cls, raw_value: Optional[str]) -> dict[str, Any]:
        """
        Parse de `tenants.instalacoes_permitidas` com backward compatibility.

        Formatos suportados:
        - lista JSON: ["Porto A", "Porto B"]  (legacy)
        - objeto JSON:
          {
            "allowed_installations": [...],
            "allowed_municipios": [...],
            "municipio_influencia": {
              "Porto A": [{"id_municipio":"3550308","peso":1.0}]
            },
            "max_bytes_per_query": 1000000000
          }
        """
        policy = cls._default_policy()

        if not raw_value:
            return policy

        try:
            payload = json.loads(raw_value)
        except (TypeError, ValueError):
            return policy

        if isinstance(payload, list):
            policy["allowed_installations"] = [str(item) for item in payload]
            return policy

        if not isinstance(payload, dict):
            return policy

        allowed_installations = payload.get("allowed_installations", [])
        if isinstance(allowed_installations, list):
            policy["allowed_installations"] = [str(item) for item in allowed_installations]

        allowed_municipios = payload.get("allowed_municipios", [])
        if isinstance(allowed_municipios, list):
            policy["allowed_municipios"] = [str(item) for item in allowed_municipios]

        max_bytes = payload.get("max_bytes_per_query")
        if max_bytes is not None:
            try:
                policy["max_bytes_per_query"] = int(max_bytes)
            except (TypeError, ValueError):
                policy["max_bytes_per_query"] = None

        influence_map = cls._read_influence_map(payload)
        policy["municipio_influencia"] = influence_map
        policy["area_influencia"] = influence_map
        return policy

    @classmethod
    def serialize_policy(cls, policy: dict[str, Any]) -> str:
        """Serializa politica para persistencia em `tenants.instalacoes_permitidas`."""
        normalized = cls._default_policy()
        normalized["allowed_installations"] = list(policy.get("allowed_installations", []))
        normalized["allowed_municipios"] = list(policy.get("allowed_municipios", []))
        municipal_map = dict(policy.get("municipio_influencia", {}))
        normalized["municipio_influencia"] = municipal_map
        normalized["area_influencia"] = municipal_map
        normalized["max_bytes_per_query"] = policy.get("max_bytes_per_query")
        return json.dumps(normalized, ensure_ascii=False)

    async def get_policy(self, db: AsyncSession, tenant_id: UUID) -> dict[str, Any]:
        """Busca politica atual do tenant."""
        result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if tenant is None:
            return self._default_policy()
        return self.parse_policy(tenant.instalacoes_permitidas)

    async def save_policy(self, db: AsyncSession, tenant_id: UUID, policy: dict[str, Any]) -> dict[str, Any]:
        """Persiste politica atualizada para o tenant."""
        result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if tenant is None:
            raise ValueError(f"Tenant {tenant_id} nao encontrado")

        tenant.instalacoes_permitidas = self.serialize_policy(policy)
        await db.commit()
        await db.refresh(tenant)
        return self.parse_policy(tenant.instalacoes_permitidas)

    async def set_area_influencia(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        id_instalacao: str,
        municipios: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Cria/atualiza municipio de influencia para uma instalacao."""
        if not id_instalacao:
            raise ValueError("id_instalacao e obrigatorio")
        if not municipios:
            raise ValueError("lista de municipios nao pode ser vazia")

        cleaned = []
        seen = set()
        for item in municipios:
            id_municipio = str(item.get("id_municipio", "")).strip()
            if not id_municipio:
                raise ValueError("id_municipio e obrigatorio")
            if (not id_municipio.isdigit()) or len(id_municipio) != 7:
                raise ValueError(
                    f"id_municipio invalido (esperado codigo IBGE de 7 digitos): {id_municipio}"
                )
            if id_municipio in seen:
                raise ValueError(f"municipio duplicado no municipio de influencia: {id_municipio}")
            seen.add(id_municipio)
            cleaned.append(
                {
                    "id_municipio": id_municipio,
                    "peso": _as_float(item.get("peso"), default=1.0),
                }
            )

        await self._validate_municipios_exist_in_ibge([item["id_municipio"] for item in cleaned])

        policy = await self.get_policy(db, tenant_id)
        area = dict(policy.get("municipio_influencia", {}))
        area[id_instalacao] = cleaned
        policy["municipio_influencia"] = area
        policy["area_influencia"] = area
        return await self.save_policy(db, tenant_id, policy)

    async def delete_area_influencia(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        id_instalacao: str,
    ) -> dict[str, Any]:
        """Remove municipio de influencia de uma instalacao."""
        policy = await self.get_policy(db, tenant_id)
        area = dict(policy.get("municipio_influencia", {}))
        area.pop(id_instalacao, None)
        policy["municipio_influencia"] = area
        policy["area_influencia"] = area
        return await self.save_policy(db, tenant_id, policy)

    async def set_allowlist_policy(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        allowed_municipios: list[str],
        max_bytes_per_query: Optional[int] = None,
    ) -> dict[str, Any]:
        """Atualiza allowlist de municipios e quota do tenant."""
        cleaned = self._normalize_allowed_municipios(allowed_municipios)
        await self._validate_municipios_exist_in_ibge(cleaned)

        policy = await self.get_policy(db, tenant_id)
        policy["allowed_municipios"] = cleaned
        policy["max_bytes_per_query"] = max_bytes_per_query
        return await self.save_policy(db, tenant_id, policy)

    @staticmethod
    def _normalize_allowed_municipios(allowed_municipios: list[str]) -> list[str]:
        """Normaliza e valida codigos IBGE da allowlist."""
        seen = set()
        cleaned: list[str] = []
        for raw_item in allowed_municipios or []:
            id_municipio = str(raw_item).strip()
            if not id_municipio:
                continue
            if (not id_municipio.isdigit()) or len(id_municipio) != 7:
                raise ValueError(
                    f"id_municipio invalido na allowlist (esperado codigo IBGE de 7 digitos): {id_municipio}"
                )
            if id_municipio in seen:
                continue
            seen.add(id_municipio)
            cleaned.append(id_municipio)
        return cleaned

    async def lookup_municipio_nomes(self, municipios: list[str]) -> dict[str, str]:
        """
        Retorna dicionário {id_municipio: nome_municipio} para os ids válidos.

        IDs inválidos ou não encontrados são ignorados.
        """
        unique_ids = sorted(
            {
                str(item).strip()
                for item in municipios or []
                if str(item).strip().isdigit() and len(str(item).strip()) == 7
            }
        )
        if not unique_ids:
            return {}

        ids_sql = ", ".join(f"'{item}'" for item in unique_ids)
        query = f"""
        SELECT
            CAST(id_municipio AS STRING) AS id_municipio,
            ANY_VALUE(nome) AS nome_municipio
        FROM `{BD_DADOS_DIRETORIO_MUNICIPIO}`
        WHERE CAST(id_municipio AS STRING) IN ({ids_sql})
        GROUP BY id_municipio
        """

        rows = await self.bq_client.execute_query(query)
        out = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            id_municipio = str(row.get("id_municipio", "")).strip()
            nome = row.get("nome_municipio")
            if id_municipio and nome:
                out[id_municipio] = str(nome).strip()
        return out

    async def _validate_municipios_exist_in_ibge(self, municipios: list[str]) -> None:
        """
        Valida que os municipios existem no diretorio IBGE.

        Se algum codigo nao for encontrado, bloqueia o cadastro com erro claro.
        """
        if not municipios:
            return

        unique_ids = sorted(set(municipios))
        ids_sql = ", ".join(f"'{item}'" for item in unique_ids)
        query = f"""
        SELECT CAST(id_municipio AS STRING) AS id_municipio
        FROM `{BD_DADOS_DIRETORIO_MUNICIPIO}`
        WHERE CAST(id_municipio AS STRING) IN ({ids_sql})
        """

        rows = await self.bq_client.execute_query(query)
        found = {
            str(row.get("id_municipio"))
            for row in rows
            if isinstance(row, dict) and row.get("id_municipio")
        }

        missing = [item for item in unique_ids if item not in found]
        if missing:
            raise ValueError(
                "municipios nao encontrados no diretorio IBGE: " + ", ".join(missing)
            )


_policy_service: Optional[TenantPolicyService] = None


def get_tenant_policy_service() -> TenantPolicyService:
    """Singleton do servico de politica de tenant."""
    global _policy_service
    if _policy_service is None:
        _policy_service = TenantPolicyService()
    return _policy_service
