"""
Serviço de Autenticação.

Lógica de negócio para login, registro e gerenciamento de tokens.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from typing import Optional
import uuid
import httpx
import redis.asyncio as aioredis

from app.config import get_settings
from app.core.logging import get_logger
from app.db.models.user import User
from app.db.models.tenant import Tenant
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    blacklist_access_token,
)
from app.schemas.auth import UserRegister


settings = get_settings()
logger = get_logger(__name__)


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
                Tenant.ativo.is_(True),
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

    async def request_password_reset(self, email: str) -> None:
        """
        Inicia o fluxo de recuperação de senha por e-mail.

        Sempre retorna silenciosamente sem distinção para evitar enumeração de usuários.
        """
        token = await self._generate_password_reset_token(email)
        if not token:
            return

        await self._send_reset_email(email=email, token=token)

    async def confirm_password_reset(self, token: str, new_password: str) -> None:
        """
        Atualiza a senha após validação de token de recuperação.
        """
        user_id = await self._consume_password_reset_token(token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido ou expirado.",
            )

        user = await self._get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido ou expirado.",
            )

        if not user.ativo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuário inativo.",
            )

        if not user.tenant or not user.tenant.ativo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant inativo.",
            )

        user.hashed_password = get_password_hash(new_password)
        await self.db.commit()

    async def blacklist_access_token(self, token: str) -> None:
        """Requisita invalidação do token na camada de segurança."""
        blacklist_access_token(token)

    async def _generate_password_reset_token(self, email: str) -> Optional[str]:
        user = await self._find_active_user_by_email(email)
        if not user or not user.ativo or not user.tenant or not user.tenant.ativo:
            return None

        token = str(uuid.uuid4())
        await self._store_password_reset_token(token, user.id)
        return token

    async def _consume_password_reset_token(self, token: str) -> Optional[uuid.UUID]:
        redis_key = f"password-reset:{token}"
        redis_client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
        try:
            user_id = await redis_client.get(redis_key)
            if not user_id:
                return None

            await redis_client.delete(redis_key)
            return uuid.UUID(user_id)
        except Exception as exc:
            logger.error(
                "Falha ao ler token de reset no Redis",
                extra={"token": token, "error": str(exc)},
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Recurso de recuperação indisponível no momento.",
            )
        finally:
            await redis_client.aclose()

    async def _store_password_reset_token(self, token: str, user_id: uuid.UUID) -> None:
        redis_key = f"password-reset:{token}"
        redis_client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
        try:
            await redis_client.setex(
                redis_key,
                settings.password_reset_token_ttl_seconds,
                str(user_id),
            )
        except Exception as exc:
            logger.error(
                "Falha ao persistir token de reset no Redis",
                extra={"email": str(user_id), "error": str(exc)},
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Recurso de recuperação indisponível no momento.",
            )
        finally:
            await redis_client.aclose()

    async def _find_active_user_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.tenant))
            .join(Tenant)
            .where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def _get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.tenant))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def _send_reset_email(self, email: str, token: str) -> None:
        if not settings.sendgrid_api_key:
            logger.warning(
                "SendGrid não configurado; e-mail de reset não foi enviado.",
                extra={"email": email},
            )
            return

        message = (
            "Foi solicitada uma redefinição de senha.\n\n"
            f"Token: {token}\n\n"
            f"Este token expira em {settings.password_reset_token_ttl_seconds // 60} minutos.\n"
            "Se você não solicitou, ignore esta mensagem."
        )
        payload = {
            "personalizations": [{"to": [{"email": email}]}],
            "from": {"email": settings.sendgrid_from_email},
            "subject": "Redefinição de senha",
            "content": [{"type": "text/plain", "value": message}],
        }
        headers = {
            "Authorization": f"Bearer {settings.sendgrid_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
