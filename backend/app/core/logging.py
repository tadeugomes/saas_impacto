"""Configuração de logging estruturado padrão da aplicação."""

from __future__ import annotations

from contextvars import ContextVar
import logging
import logging as _stdlib_logging
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from contextlib import contextmanager

from app.config import get_settings

try:  # pragma: no cover - fallback quando dependência opcional não estiver instalada
    import structlog
except ModuleNotFoundError:  # pragma: no cover
    structlog = None


_REQUEST_ID_VAR: ContextVar[str | None] = ContextVar("request_id", default=None)
_TENANT_ID_VAR: ContextVar[str | None] = ContextVar("tenant_id", default=None)
_USER_ID_VAR: ContextVar[str | None] = ContextVar("user_id", default=None)
_TASK_ID_VAR: ContextVar[str | None] = ContextVar("task_id", default=None)


_RESERVED_LOG_KWARGS = {
    "exc_info",
    "stack_info",
    "stacklevel",
    "extra",
}


@dataclass(slots=True)
class _StdlibLoggerAdapter:
    """Compatibilidade de API ``logger.*`` quando ``structlog`` não está disponível."""

    _logger: logging.Logger

    @staticmethod
    def _format_structured_fields(fields: dict[str, Any]) -> str:
        if not fields:
            return ""

        return " ".join(f"{key}={value!r}" for key, value in fields.items())

    def _log(self, level_method: str, msg: str, *args: Any, **kwargs: Any) -> None:
        log_kwargs = {
            key: kwargs.pop(key) for key in list(kwargs.keys()) if key in _RESERVED_LOG_KWARGS
        }
        payload = self._format_structured_fields(kwargs)
        message = msg if payload == "" else f"{msg} {payload}"
        logger = getattr(self._logger, level_method)
        logger(message, *args, **log_kwargs)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log("debug", msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log("info", msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log("warning", msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log("error", msg, *args, **kwargs)

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("exc_info", True)
        self._log("error", msg, *args, **kwargs)


def _to_str(value: Any) -> str | None:
    """Converte valor de contexto para string quando aplicável."""
    if value is None:
        return None
    return str(value)


_LOG_FORMAT = "%(levelname)s %(name)s %(message)s"


def _render_to_log_kwargs() -> Any:
    """Resolve ``render_to_log_kwargs`` com fallback seguro."""
    if structlog is None:
        return None

    stdlib = getattr(structlog, "stdlib", None)
    if stdlib is None:
        return None

    render_to_log_kwargs = getattr(stdlib, "render_to_log_kwargs", None)
    if render_to_log_kwargs is not None:
        return render_to_log_kwargs

    return lambda logger, method_name, event_dict: event_dict


def _console_renderer() -> Any:
    if structlog is None:
        return None

    dev_module = getattr(structlog, "dev", None)
    if dev_module is not None:
        console = getattr(dev_module, "ConsoleRenderer", None)
        if console is not None:
            return console()

    return None


def _is_production(settings) -> bool:
    environment = settings.environment.lower()
    return not settings.debug and environment not in {"development", "dev", "local"}


@contextmanager
def bind_request_context(
    *,
    request_id: str | None = None,
    tenant_id: str | None = None,
    user_id: str | None = None,
    task_id: str | None = None,
) -> Iterator[None]:
    """Adiciona contexto de request/execução aos logs via contextvars."""
    tokens = []
    if request_id is not None:
        tokens.append((_REQUEST_ID_VAR, _REQUEST_ID_VAR.set(_to_str(request_id))))
    if tenant_id is not None:
        tokens.append((_TENANT_ID_VAR, _TENANT_ID_VAR.set(_to_str(tenant_id))))
    if user_id is not None:
        tokens.append((_USER_ID_VAR, _USER_ID_VAR.set(_to_str(user_id))))
    if task_id is not None:
        tokens.append((_TASK_ID_VAR, _TASK_ID_VAR.set(_to_str(task_id))))

    try:
        yield
    finally:
        for var, token in reversed(tokens):
            var.reset(token)


def inject_request_context(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Injecta contexto atual (request/tenant/user/task) no evento de log."""
    del logger, method_name

    request_id = _REQUEST_ID_VAR.get()
    tenant_id = _TENANT_ID_VAR.get()
    user_id = _USER_ID_VAR.get()
    task_id = _TASK_ID_VAR.get()

    if request_id is not None:
        event_dict["request_id"] = request_id
    if tenant_id is not None:
        event_dict["tenant_id"] = tenant_id
    if user_id is not None:
        event_dict["user_id"] = user_id
    if task_id is not None:
        event_dict["task_id"] = task_id

    return event_dict


def configure_structlog() -> None:
    """Configura structlog com saída estruturada para observabilidade."""
    settings = get_settings()
    is_production = _is_production(settings)

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(message)s" if structlog is not None else _LOG_FORMAT
        ),
        force=True,
    )
    if structlog is None:
        _stdlib_logging.info("structlog não encontrado; usando logger stdlib fallback")
        return

    logger_processors = [
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.add_log_level,
        inject_request_context,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        _render_to_log_kwargs(),
    ]

    renderer = (
        structlog.processors.JSONRenderer()
        if is_production
        else _console_renderer() or structlog.processors.JSONRenderer()
    )
    logger_processors.append(renderer)

    structlog.configure(
        processors=logger_processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    """Retorna logger estruturado para o módulo informado."""
    if structlog is None:
        return _StdlibLoggerAdapter(_stdlib_logging.getLogger(name))

    return structlog.get_logger(name)
