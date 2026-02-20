"""Testes básicos de configuração do logging estruturado."""

from typing import Any

from app.core.logging import (
    bind_request_context,
    configure_structlog,
    get_logger,
    inject_request_context,
)


def test_configure_structlog_and_get_logger():
    configure_structlog()
    logger = get_logger("test")
    logger.info("structlog smoke test", event="smoke")


def test_inject_request_context_populates_event_fields() -> None:
    event: dict[str, Any] = {}
    with bind_request_context(
        request_id="req-1",
        tenant_id="tenant-1",
        user_id="user-1",
        task_id="task-1",
    ):
        enriched = inject_request_context(None, "info", event)

    assert enriched["request_id"] == "req-1"
    assert enriched["tenant_id"] == "tenant-1"
    assert enriched["user_id"] == "user-1"
    assert enriched["task_id"] == "task-1"


def test_bind_request_context_is_scoped() -> None:
    event: dict[str, Any] = {}
    assert inject_request_context(None, "info", event) == {}

    with bind_request_context(request_id="req-2"):
        in_context: dict[str, Any] = {}
        assert inject_request_context(None, "info", in_context)["request_id"] == "req-2"

    after_context: dict[str, Any] = {}
    assert inject_request_context(None, "info", after_context).get("request_id") is None
