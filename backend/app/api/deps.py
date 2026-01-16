"""
Dependencies para endpoints FastAPI.

Funções reutilizáveis para injeção de dependências.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
import uuid

from app.db.base import get_db
from app.core.tenant import get_tenant_id
from app.core.security import decode_access_token
from app.db.models.user import User
from sqlalchemy import select


# Security scheme para swagger
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
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
    # 1. Decodificar token
    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    # 2. Extrair user_id e tenant_id do token
    user_id = payload.get("sub")
    token_tenant_id = payload.get("tenant_id")

    if not user_id or not token_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # 3. Validar que tenant_id do token bate com do header
    if uuid.UUID(token_tenant_id) != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant mismatch",
        )

    # 4. Buscar usuário no banco
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.tenant_id == tenant_id,
            User.ativo == True
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


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
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    return current_user
