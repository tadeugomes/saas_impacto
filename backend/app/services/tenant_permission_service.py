"""Serviços de permissão granular por tenant."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.models.tenant_module_permission import TenantModulePermission


class TenantPermissionService:
    """Gerencia regras de módulo/ação por tenant e role."""

    VALID_ACTIONS = {"read", "execute", "write"}
    MIN_MODULE = 1
    MAX_MODULE = 7

    def _validate_permission(self, module_number: int, action: str) -> None:
        if not isinstance(module_number, int) or not (
            self.MIN_MODULE <= module_number <= self.MAX_MODULE
        ):
            raise ValueError("module deve estar entre 1 e 7")

        if action not in self.VALID_ACTIONS:
            raise ValueError("action deve ser um dos: read, execute, write")

    @staticmethod
    def _normalize_role(role: str) -> str:
        return role.strip().lower()

    async def list_permissions_by_roles(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        roles: Iterable[str],
    ) -> dict[str, list[dict[str, str]]]:
        normalized_roles = [
            self._normalize_role(role)
            for role in roles
            if role and isinstance(role, str) and role.strip()
        ]
        if not normalized_roles:
            return {}

        result = await db.execute(
            select(TenantModulePermission).where(
                TenantModulePermission.tenant_id == tenant_id,
                TenantModulePermission.role.in_(normalized_roles),
            )
        )
        rows = result.scalars().all()

        permissions_by_role: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in rows:
            permissions_by_role[row.role].append(
                {
                    "module_number": row.module_number,
                    "action": row.action,
                }
            )
        return dict(permissions_by_role)

    async def list_permissions(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        role: str,
    ) -> list[dict[str, str]]:
        return (
            await self.list_permissions_by_roles(db=db, tenant_id=tenant_id, roles=[role])
        ).get(self._normalize_role(role), [])

    async def set_permissions_for_role(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        role: str,
        permissions: Iterable[tuple[int, str, bool]],
    ) -> list[dict[str, str]]:
        # Remove antigas permissões do role no tenant
        await db.execute(
            delete(TenantModulePermission).where(
                TenantModulePermission.tenant_id == tenant_id,
                TenantModulePermission.role == self._normalize_role(role),
            )
        )

        normalized_role = self._normalize_role(role)
        inserts = []
        seen: set[tuple[int, str]] = set()
        for module_number, action, allowed in permissions:
            self._validate_permission(module_number, action)
            if not allowed:
                continue

            key = (module_number, action)
            if key in seen:
                continue
            seen.add(key)
            inserts.append(
                TenantModulePermission(
                    tenant_id=tenant_id,
                    role=normalized_role,
                    module_number=module_number,
                    action=action,
                )
            )

        db.add_all(inserts)
        await db.commit()

        return await self.list_permissions(db, tenant_id, role)

    async def upsert_permissions_for_role(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        role: str,
        permissions: list[tuple[int, str, bool]],
    ) -> list[dict[str, str]]:
        normalized_role = self._normalize_role(role)
        # Mantém permissões existentes e adiciona/remover as informadas
        existing_result = await db.execute(
            select(TenantModulePermission).where(
                TenantModulePermission.tenant_id == tenant_id,
                TenantModulePermission.role == normalized_role,
            )
        )
        existing = list(existing_result.scalars())
        existing_by_key = {
            (row.module_number, row.action): row for row in existing
        }

        input_by_key = {
            (module_number, action): allowed
            for module_number, action, allowed in permissions
        }

        to_add: list[TenantModulePermission] = []
        for (module_number, action), allowed in input_by_key.items():
            self._validate_permission(module_number, action)
            if allowed:
                if (module_number, action) not in existing_by_key:
                    to_add.append(
                    TenantModulePermission(
                        tenant_id=tenant_id,
                        role=normalized_role,
                        module_number=module_number,
                        action=action,
                    )
                )
            else:
                if (module_number, action) in existing_by_key:
                    await db.delete(existing_by_key[(module_number, action)])

        if to_add:
            db.add_all(to_add)

        await db.commit()
        return await self.list_permissions(db, tenant_id, role)


def get_tenant_permission_service() -> TenantPermissionService:
    """Dependency provider."""

    return TenantPermissionService()
