"""
Endpoints de Autenticação API v1.

Rotas para login, registro e refresh de tokens.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.schemas.auth import (
    PasswordResetConfirm,
    PasswordResetRequest,
    UserLogin,
    UserRegister,
    Token,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.api.deps import get_current_user
from app.db.models.user import User
router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post("/login", response_model=Token)
async def login(
    user_login: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """
    Autentica usuário e retorna tokens JWT.

    Args:
        user_login: Email e senha
        db: Sessão do banco

    Returns:
        Token com access_token e refresh_token
    """
    auth_service = AuthService(db)

    # Autenticar
    user = await auth_service.authenticate_user(
        user_login.email,
        user_login.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Criar tokens
    tokens = await auth_service.create_tokens(user)

    return tokens


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    """
    Registra novo usuário em um tenant existente.

    Args:
        user_data: Dados de registro
        db: Sessão do banco

    Returns:
        Usuário criado
    """
    auth_service = AuthService(db)

    user = await auth_service.register_user(user_data)

    return user


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    Retorna informações do usuário autenticado.

    Args:
        current_user: Usuário injetado pelo token

    Returns:
        Dados do usuário
    """
    return current_user


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Renova tokens de acesso.

    Args:
        current_user: Usuário autenticado
        db: Sessão do banco

    Returns:
        Novos tokens
    """
    auth_service = AuthService(db)
    tokens = await auth_service.create_tokens(current_user)

    return tokens


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """
    Faz logout do usuário e revoga token atual.
    """
    auth_service = AuthService(db)
    await auth_service.blacklist_access_token(credentials.credentials)
    return {"message": "Successfully logged out"}


@router.post("/password-reset/request")
async def password_reset_request(
    payload: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Gera token de recuperação e envia por email.
    """
    auth_service = AuthService(db)
    await auth_service.request_password_reset(payload.email)

    return {
        "message": (
            "Se o e-mail estiver cadastrado, enviaremos instruções de recuperação."
        )
    }


@router.post("/password-reset/confirm")
async def password_reset_confirm(
    payload: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
):
    """
    Redefine senha usando token temporário.
    """
    auth_service = AuthService(db)
    await auth_service.confirm_password_reset(payload.token, payload.new_password)

    return {"message": "Senha redefinida com sucesso."}
