"""Testes básicos de configuração do logging estruturado."""

from app.core.logging import configure_structlog, get_logger


def test_configure_structlog_and_get_logger():
    configure_structlog()
    logger = get_logger("test")
    logger.info("structlog smoke test", event="smoke")
