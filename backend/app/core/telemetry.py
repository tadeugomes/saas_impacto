"""Inicialização opcional de OpenTelemetry."""

from __future__ import annotations

from typing import Any

from app.config import get_settings

settings = get_settings()


def init_telemetry(app: Any) -> None:
    """Ativa instrumentação OpenTelemetry se configurada.

    Falha de inicialização é tratada como operação não bloqueante para não
    impedir o boot da API.
    """
    if not settings.otel_enabled:
        return

    try:
        from opentelemetry import trace
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            ConsoleSpanExporter,
        )
    except Exception:
        # Dependências opcionais não instaladas/erro de importação.
        return

    exporter = settings.otel_exporter.lower().strip()
    if exporter == "console":
        exporter_instance = ConsoleSpanExporter()
    elif exporter == "otlp":
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )

            exporter_instance = OTLPSpanExporter(
                endpoint=settings.otel_exporter_otlp_endpoint,
            )
        except Exception:
            exporter_instance = ConsoleSpanExporter()
    else:
        exporter_instance = ConsoleSpanExporter()

    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": "saas-impacto-api",
                "service.version": settings.app_version,
                "deployment.environment": settings.environment,
            }
        )
    )
    processor = BatchSpanProcessor(exporter_instance)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    try:
        FastAPIInstrumentor().instrument(
            app=app,
            tracer_provider=provider,
            server_request_hook=_on_request_start,
            server_response_hook=_on_request_end,
        )
        SQLAlchemyInstrumentor().instrument()
        try:
            RedisInstrumentor().instrument()
        except Exception:
            pass
    except Exception:
        # Em caso de erro de instrumentação, mantém app funcional.
        return


def _on_request_start(span, scope, message, **kwargs):  # pragma: no cover
    del kwargs
    if span is None:
        return
    request = getattr(scope.get("extensions", {}), "request", None)
    if request is None:
        request = scope.get("state", {}).get("request") if isinstance(scope, dict) else None
    if request is None:
        return
    span.set_attribute("http.user_agent", str(getattr(request, "headers", {}).get("user-agent", "")))
    try:
        if tenant_id := getattr(request.state, "tenant_id", None):
            span.set_attribute("tenant_id", str(tenant_id))
    except Exception:
        pass


def _on_request_end(span, scope, message, response, **kwargs):  # pragma: no cover
    del kwargs
    if span is not None:
        span.set_attribute("http.status_code", getattr(response, "status_code", None))
    _ = scope
