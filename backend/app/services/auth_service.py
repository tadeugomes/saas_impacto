"""
Serviço de Autenticação.

Lógica de negócio para login, registro e gerenciamento de tokens.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from typing import Optional
import uuid

from app.db.models.user import User
from app.db.models.tenant import Tenant
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
)
from app.schemas.auth import UserRegister


class AuthService:
    """Serviço para operações de autenticação."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate_user(
        self, email: str, password: str
    ) -> Optional[User]:
        """
        Autentica usuário com email e senha.

        Args:
            email: Email do usuário
            password: Senha em texto plano

        Returns:
            User se autenticado com sucesso, None caso contrário
        """
        # Buscar usuário por email (global, sem filtro de tenant)
        # Eager load tenant to avoid lazy loading in async context
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.tenant))
            .join(Tenant)
            .where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        if not user.ativo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        if not user.tenant.ativo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant account is inactive",
            )

        return user

    async def register_user(
        self, user_data: UserRegister
    ) -> User:
        """
        Registra um novo usuário.

        Args:
            user_data: Dados de registro

        Returns:
            User criado

        Raises:
            HTTPException: Se tenant não existe ou email já usado
        """
        # 1. Buscar tenant
        result = await self.db.execute(
            select(Tenant).where(
                Tenant.slug == user_data.tenant_slug,
                Tenant.ativo == True
            )
        )
        tenant = result.scalar_one_or_none()

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found or inactive",
            )

        # 2. Verificar se email já existe no tenant
        existing = await self.db.execute(
            select(User).where(
                User.tenant_id == tenant.id,
                User.email == user_data.email
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered in this tenant",
            )

        # 3. Criar usuário
        user = User(
            tenant_id=tenant.id,
            email=user_data.email,
            nome=user_data.nome,
            hashed_password=get_password_hash(user_data.password),
            roles=["viewer"],  # Role padrão
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def create_tokens(self, user: User) -> dict:
        """
        Cria tokens de acesso e refresh.

        Args:
            user: Usuário autenticado

        Returns:
            Dict com access_token e refresh_token
        """
        token_data = {
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id),
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
