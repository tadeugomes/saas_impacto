"""Testes para os endpoints de health check e observabilidade."""

from __future__ import annotations

import json
import re
from unittest.mock import AsyncMock

from fastapi import FastAPI

from app.tests.http_test_client import make_sync_asgi_client


def _extract_log_payload(message: str) -> dict:
    regexes = {
        "request_id": re.compile(r"request_id=\'?\"?([^'\" ]+)\"?\'?"),
        "tenant_id": re.compile(r"tenant_id=\'?\"?([^'\" ]+)\"?\'?"),
    }

    try:
        return json.loads(message)
    except Exception:
        payload: dict[str, str] = {}
        for key, pattern in regexes.items():
            match = pattern.search(message)
            if match:
                payload[key] = match.group(1)
        return payload


def _build_client_with_health_checks(monkeypatched_checks) -> FastAPI:
    """Cria app de teste com checagens de health substituídas."""
    import app.main as app_module

    if "postgres" in monkeypatched_checks:
        app_module._check_postgres = AsyncMock(
            return_value=monkeypatched_checks["postgres"]
        )
    if "redis" in monkeypatched_checks:
        app_module._check_redis = AsyncMock(
            return_value=monkeypatched_checks["redis"]
        )
    if "bigquery" in monkeypatched_checks:
        app_module._check_bigquery = AsyncMock(
            return_value=monkeypatched_checks["bigquery"]
        )
    return app_module.app


def test_health_endpoint_returns_dependency_map():
    checks = {
        "postgres": {"status": "connected"},
        "redis": {"status": "connected"},
        "bigquery": {"status": "connected"},
    }
    app_main = _build_client_with_health_checks(checks)

    client = make_sync_asgi_client(app_main)
    resp = client.get("/health")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "healthy"
    assert payload["dependencies"]["postgres"]["status"] == "connected"
    assert payload["dependencies"]["redis"]["status"] == "connected"
    assert payload["dependencies"]["bigquery"]["status"] == "connected"


def test_ready_endpoint_returns_200_when_all_dependencies_ok():
    app_main = _build_client_with_health_checks(
        {
            "postgres": {"status": "connected"},
            "redis": {"status": "connected"},
            "bigquery": {"status": "connected"},
        }
    )

    client = make_sync_asgi_client(app_main)
    resp = client.get("/health/ready")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "ready"
    assert payload["dependencies"]["postgres"]["status"] == "connected"


def test_ready_endpoint_returns_503_when_dependency_fails():
    app_main = _build_client_with_health_checks(
        {
            "postgres": {"status": "disconnected", "error": "connection timeout"},
            "redis": {"status": "connected"},
            "bigquery": {"status": "connected"},
        }
    )

    client = make_sync_asgi_client(app_main)
    resp = client.get("/health/ready")

    assert resp.status_code == 503
    payload = resp.json()
    assert payload["detail"]["status"] == "unready"
    assert payload["detail"]["dependencies"]["postgres"]["status"] == "disconnected"


def test_live_endpoint_and_request_timing_header():
    app_main = _build_client_with_health_checks(
        {
            "postgres": {"status": "disconnected"},
            "redis": {"status": "disconnected"},
            "bigquery": {"status": "disconnected"},
        }
    )

    client = make_sync_asgi_client(app_main)
    resp = client.get("/health/live")

    assert resp.status_code == 200
    assert "X-Request-Duration-Ms" in resp.headers


def test_request_timing_preserves_header_request_id():
    app_main = _build_client_with_health_checks(
        {
            "postgres": {"status": "connected"},
            "redis": {"status": "connected"},
            "bigquery": {"status": "connected"},
        }
    )

    client = make_sync_asgi_client(app_main)
    resp = client.get("/health", headers={"X-Request-Id": "test-req-1"})

    assert resp.status_code == 200
    assert resp.headers["X-Request-Id"] == "test-req-1"


def test_request_timing_logs_request_context_in_json_payload(caplog):
    app_main = _build_client_with_health_checks(
        {
            "postgres": {"status": "connected"},
            "redis": {"status": "connected"},
            "bigquery": {"status": "connected"},
        }
    )

    client = make_sync_asgi_client(app_main)
    with caplog.at_level("INFO"):
        resp = client.get(
            "/health",
            headers={
                "X-Request-Id": "test-req-2",
                "X-Tenant-ID": "00000000-0000-0000-0000-000000000001",
            },
        )

    assert resp.status_code == 200
    records = [
        record
        for record in caplog.records
        if "http_request_complete" in record.getMessage()
    ]
    assert records, "esperado log de request com contexto"

    payload = _extract_log_payload(records[-1].getMessage())
    assert payload.get("request_id") == "test-req-2"
    assert payload.get("tenant_id") == "00000000-0000-0000-0000-000000000001"
