"""
Módulo de Segurança - JWT e Password Hashing.

Funções para criar e validar tokens JWT e gerenciar senhas.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import bcrypt
from typing import Optional
from uuid import uuid4

import redis
from app.core.logging import get_logger

from app.config import get_settings

settings = get_settings()
logger = get_logger(__name__)


def _jwt_now() -> datetime:
    """Retorna timestamp atual em UTC."""
    return datetime.now(timezone.utc)


def _redis_sync_client() -> Optional[redis.Redis]:
    """Cria cliente Redis síncrono (sync) usado por validação de blacklist."""
    try:
        return redis.Redis.from_url(settings.redis_url, decode_responses=True)
    except Exception as exc:  # pragma: no cover - ambiente sem redis
        logger.warning(
            "Falha ao criar cliente Redis para validação de blacklist",
            extra={"error": str(exc)},
        )
        return None


def _seconds_until_exp(exp: object) -> int:
    """Calcula segundos até expiração do token."""
    if exp is None:
        return 0

    now = _jwt_now()
    if isinstance(exp, (int, float)):
        expires_at = datetime.fromtimestamp(int(exp), tz=timezone.utc)
    elif isinstance(exp, datetime):
        expires_at = exp
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
    else:
        return 0

    ttl = int((expires_at - now).total_seconds())
    return max(0, ttl)


def _is_jti_blacklisted(jti: str) -> bool:
    """
    Consulta Redis por jti de token invalidado.

    Em falha de infraestrutura, segue fluxo sem bloquear autenticação
    (melhor esforço para não degradar disponibilidade).
    """
    redis_client = _redis_sync_client()
    if redis_client is None:
        return False

    key = f"blacklist:{jti}"
    try:
        return bool(redis_client.get(key))
    except Exception as exc:  # pragma: no cover - falhas operacionais
        logger.warning(
            "Falha ao consultar blacklist no Redis",
            extra={"key": key, "error": str(exc)},
        )
        return False
    finally:
        redis_client.close()


def _add_jti_blacklist(jti: str, ttl_seconds: int) -> None:
    """Adiciona jti na blacklist com TTL em segundos."""
    if ttl_seconds <= 0:
        return

    redis_client = _redis_sync_client()
    if redis_client is None:
        return

    key = f"blacklist:{jti}"
    try:
        redis_client.setex(key, ttl_seconds, "1")
    except Exception as exc:  # pragma: no cover - falhas operacionais
        logger.warning(
            "Falha ao salvar jti na blacklist do Redis",
            extra={"key": key, "ttl_seconds": ttl_seconds, "error": str(exc)},
        )
    finally:
        redis_client.close()


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
        expire = _jwt_now() + expires_delta
    else:
        expire = _jwt_now() + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )

    to_encode.update(
        {
            "exp": int(expire.timestamp()),
            "iat": _jwt_now().timestamp(),
            "jti": str(uuid4()),
        }
    )
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )

    return encoded_jwt


def decode_access_token(
    token: str,
    *,
    verify_expiration: bool = True,
) -> Optional[dict]:
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
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": verify_expiration},
        )
        jti = payload.get("jti")
        if isinstance(jti, str) and _is_jti_blacklisted(jti):
            return None
        return payload
    except JWTError:
        return None


def blacklist_access_token(token: str) -> None:
    """Invalida token no Redis via jti."""
    payload = decode_access_token(token, verify_expiration=False)
    if not payload:
        return

    jti = payload.get("jti")
    if not isinstance(jti, str):
        return

    exp = payload.get("exp")
    ttl_seconds = _seconds_until_exp(exp)
    _add_jti_blacklist(jti, ttl_seconds)


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
