"""
Módulo de Segurança - JWT e Password Hashing.

Funções para criar e validar tokens JWT e gerenciar senhas.
"""

from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
from typing import Optional

from app.config import get_settings

settings = get_settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se a senha plain corresponde ao hash fornecido.

    Args:
        plain_password: Senha em texto plano
        hashed_password: Hash bcrypt da senha

    Returns:
        True se a senha está correta, False caso contrário
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """
    Gera hash bcrypt para a senha fornecida.

    Args:
        password: Senha em texto plano

    Returns:
        Hash bcrypt da senha
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token JWT de acesso.

    Args:
        data: Payload do token (geralmente {"sub": user_id})
        expires_delta: Tempo de expiração opcional

    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodifica e valida um token JWT.

    Args:
        token: Token JWT codificado

    Returns:
        Payload do token se válido, None se inválido
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


def create_refresh_token(data: dict) -> str:
    """
    Cria um token JWT de refresh (longo prazo).

    Args:
        data: Payload do token

    Returns:
        Token JWT codificado com expiração estendida
    """
    expires_delta = timedelta(days=settings.jwt_refresh_token_expire_days)
    return create_access_token(data, expires_delta)
