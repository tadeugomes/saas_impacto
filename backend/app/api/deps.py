"""
Dependencies para endpoints FastAPI.

Funções reutilizáveis para injeção de dependências.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from collections.abc import Callable
from typing import Annotated, List, Optional, Union
import os
import uuid

from app.schemas.indicators import GenericIndicatorRequest
from app.db.base import get_db
from app.core.tenant import get_tenant_id
from app.core.security import decode_access_token
from app.db.models.user import User
from app.config import get_settings
from app.services.tenant_permission_service import (
    TenantPermissionService,
    get_tenant_permission_service,
)


# Security schemes para autenticação (obrigatória/opcional).
security_optional = HTTPBearer(auto_error=False)

MODULE_PLAN_LIMITS = {
    "basic": {1, 2, 3, 4},
    "pro": {1, 2, 3, 4, 5, 6, 7},
    "enterprise": {1, 2, 3, 4, 5, 6, 7},
}

ROLE_PERMISSIONS = {
    "viewer": {"read"},
    "analyst": {"read", "execute"},
    "admin": {"read", "execute", "write"},
}


def _is_auth_disabled() -> bool:
    """Retorna True quando a autenticação foi explicitamente desabilitada."""
    if os.getenv("PYTEST_CURRENT_TEST"):
        return False
    return get_settings().skip_auth


def _fallback_test_user(tenant_id: uuid.UUID) -> User:
    """
    Gera usuário sintético para fases de testes locais.

    Mantém atributos mínimos esperados pela aplicação para evitar quebra em
    validações de permissão e exibição de usuário.
    """
    return User(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email="teste_local@impacto.local",
        nome="Usuário de Teste",
        hashed_password="",
        ativo=True,
        roles=["admin"],
    )


def _normalize_plan(plan: Optional[str]) -> str:
    normalized = (plan or "basic").lower().strip()
    if normalized not in {"basic", "pro", "enterprise"}:
        return "basic"
    return normalized


def _indicator_module_from_code(codigo: str) -> Optional[int]:
    if not codigo:
        return None

    parts = codigo.split("-")
    if len(parts) < 2:
        return None

    module_part = parts[1].split(".")[0]
    try:
        return int(module_part)
    except (TypeError, ValueError):
        return None


def _tenant_plan(current_user: User) -> str:
    tenant = getattr(current_user, "tenant", None)
    if tenant is None:
        return "basic"
    return _normalize_plan(getattr(tenant, "plano", None))


def _normalize_roles(roles: Union[List[str], str, None]) -> List[str]:
    if not roles:
        return []
    if isinstance(roles, str):
        roles = [roles]
    return [str(role).strip().lower() for role in roles if str(role).strip()]


def _role_has_action(
    permissions: Optional[List[dict]],
    module_number: int,
    action: str,
) -> bool:
    if not permissions:
        return False
    return any(
        row.get("module_number") == module_number and row.get("action") == action
        for row in permissions
    )


def _role_static_allows(role: str, action: str) -> bool:
    return action in ROLE_PERMISSIONS.get(role, set())


async def _has_module_access(
    current_user: User,
    db: AsyncSession,
    permission_service: TenantPermissionService,
    module_number: int,
    action: str,
) -> bool:
    tenant_plan = _tenant_plan(current_user)
    allowed_modules = MODULE_PLAN_LIMITS.get(tenant_plan, MODULE_PLAN_LIMITS["basic"])
    if module_number not in allowed_modules:
        return False

    roles = _normalize_roles(current_user.roles)
    if not roles:
        return False

    try:
        explicit_permissions = await permission_service.list_permissions_by_roles(
            db=db,
            tenant_id=current_user.tenant_id,
            roles=roles,
        )
    except Exception:
        explicit_permissions = {}

    for role in roles:
        permissions = explicit_permissions.get(role)
        if permissions is not None:
            if _role_has_action(permissions, module_number, action):
                return True
            continue

        if _role_static_allows(role, action):
            return True

    return False


async def _get_user_from_token(
    credentials: HTTPAuthorizationCredentials,
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user_id = payload.get("sub")
    token_tenant_id = payload.get("tenant_id")
    if not user_id or not token_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    try:
        if uuid.UUID(token_tenant_id) != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tenant mismatch",
            )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid tenant identifier",
        )

    result = await db.execute(
        select(User)
        .options(selectinload(User.tenant))
        .where(
            User.id == user_id,
            User.tenant_id == tenant_id,
            User.ativo == True,
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
    )
    return user


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
) -> User:
    """
    Obtém o usuário atual a partir do token JWT.

    Args:
        credentials: Credenciais Bearer do header
        db: Sessão assíncrona do banco
        tenant_id: UUID do tenant (injetado pelo middleware)

    Returns:
        User: Usuário autenticado

    Raises:
        HTTPException: Se token inválido ou usuário não encontrado
    """
    if _is_auth_disabled():
        result = await db.execute(
            select(User)
            .options(selectinload(User.tenant))
            .where(
                User.tenant_id == tenant_id,
                User.ativo == True,
            )
            .order_by(User.email.asc())
            .limit(1)
        )
        existing_user = result.scalar_one_or_none()
        if existing_user:
            return existing_user
        return _fallback_test_user(tenant_id)

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await _get_user_from_token(credentials, db, tenant_id)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
) -> Optional[User]:
    """
    Retorna o usuário autenticado quando houver token válido. Caso não haja token,
    retorna None.
    """
    if _is_auth_disabled():
        result = await db.execute(
            select(User)
            .options(selectinload(User.tenant))
            .where(User.tenant_id == tenant_id, User.ativo == True)
            .order_by(User.email.asc())
            .limit(1)
        )
        existing_user = result.scalar_one_or_none()
        if existing_user:
            return existing_user
        return _fallback_test_user(tenant_id)

    if not credentials:
        return None
    return await _get_user_from_token(credentials, db, tenant_id)


def require_permission(module_number: Optional[int], action: str) -> Callable:
    """
    Dependency factory para validação de permissão de módulo+ação.
    """
    if module_number is None:
        raise ValueError("module_number must be provided for permission checks")

    async def _checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
        permission_service: TenantPermissionService = Depends(
            get_tenant_permission_service
        ),
    ) -> User:
        if _is_auth_disabled():
            return current_user

        if action not in {"read", "execute", "write"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Unsupported action: {action}",
            )

        if not await _has_module_access(
            current_user=current_user,
            db=db,
            permission_service=permission_service,
            module_number=module_number,
            action=action,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: insufficient permissions",
            )

        return current_user

    return _checker


def require_indicator_permission(
    action: str = "read",
) -> Callable:
    """
    Valida permissão para o indicador a partir do código da requisição.
    """
    if action not in {"read", "execute", "write"}:
        raise ValueError("Invalid action")

    async def _checker(
        request: GenericIndicatorRequest,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
        permission_service: TenantPermissionService = Depends(
            get_tenant_permission_service
        ),
    ) -> User:
        if _is_auth_disabled():
            return current_user

        module_number = _indicator_module_from_code(request.codigo_indicador)
        if module_number is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid indicator code",
            )

        if not await _has_module_access(
            current_user=current_user,
            db=db,
            permission_service=permission_service,
            module_number=module_number,
            action=action,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: insufficient permissions",
            )
        return current_user

    return _checker


def require_module_permission(
    module: int | str,
    action: str = "read",
) -> Callable:
    """
    Valida permissão para um módulo (ex.: módulo 5) em ações não ligadas a
    código de indicador específico.
    """
    if action not in {"read", "execute", "write"}:
        raise ValueError("Invalid action")

    module_number = int(module)

    async def _checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
        permission_service: TenantPermissionService = Depends(
            get_tenant_permission_service
        ),
    ) -> User:
        if _is_auth_disabled():
            return current_user

        if not await _has_module_access(
            current_user=current_user,
            db=db,
            permission_service=permission_service,
            module_number=module_number,
            action=action,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: insufficient permissions",
            )
        return current_user

    return _checker


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Verifica se o usuário tem role de admin.

    Args:
        current_user: Usuário autenticado

    Returns:
        User: Usuário admin

    Raises:
        HTTPException: Se usuário não for admin
    """
    if _is_auth_disabled():
        return current_user

    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    return current_user
