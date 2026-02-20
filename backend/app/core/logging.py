"""Configuração de logging estruturado padrão da aplicação."""

from __future__ import annotations

import logging
import logging as _stdlib_logging

try:  # pragma: no cover - fallback quando dependência opcional não estiver instalada
    import structlog
except ModuleNotFoundError:  # pragma: no cover
    structlog = None


_LOG_FORMAT = "%(levelname)s %(name)s %(message)s"


def configure_structlog() -> None:
    """Configura structlog com saída JSON em ambientes de produção."""
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(message)s" if structlog is not None else _LOG_FORMAT
        ),
    )
    if structlog is None:
        _stdlib_logging.info("structlog não encontrado; usando logger stdlib fallback")
        return

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Retorna logger estruturado para o módulo informado."""
    if structlog is None:
        return _stdlib_logging.getLogger(name)

    return structlog.get_logger(name)
