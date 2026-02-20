"""Métricas leves de execução (Prometheus) com fallback para operação sem serviço."""

from __future__ import annotations

from collections.abc import Callable

try:
    from prometheus_client import CollectorRegistry, CONTENT_TYPE_LATEST, generate_latest, Histogram
    from prometheus_client import Counter
except ModuleNotFoundError:  # pragma: no cover - opcional em alguns ambientes
    Counter = None
    Histogram = None
    CollectorRegistry = None
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"

    def generate_latest(*args, **kwargs):  # noqa: D401
        return b""


from app.config import get_settings

settings = get_settings()

_registry = CollectorRegistry() if CollectorRegistry else None
_http_requests_total = None
_http_request_duration_seconds = None
_celery_tasks_total = None
_bq_cache_hits_total = None
_bq_cache_misses_total = None


def _build_metrics() -> None:
    if Counter is None or Histogram is None or _registry is None:
        return

    global _http_requests_total, _http_request_duration_seconds
    global _celery_tasks_total, _bq_cache_hits_total, _bq_cache_misses_total

    if _http_requests_total is not None:
        return

    _http_requests_total = Counter(
        "http_requests_total",
        "Total de requisições HTTP",
        ["method", "path", "status", "tenant"],
        registry=_registry,
    )
    _http_request_duration_seconds = Histogram(
        "http_request_duration_seconds",
        "Duração das requisições HTTP",
        ["method", "path", "status", "tenant"],
        registry=_registry,
        buckets=[0.05, 0.1, 0.5, 1, 3, 5, 10],
    )
    _celery_tasks_total = Counter(
        "celery_tasks_total",
        "Total de tarefas Celery executadas",
        ["task", "status"],
        registry=_registry,
    )
    _bq_cache_hits_total = Counter(
        "bq_cache_hits_total",
        "Cache hits em consultas BigQuery",
        ["tenant", "query_code"],
        registry=_registry,
    )
    _bq_cache_misses_total = Counter(
        "bq_cache_misses_total",
        "Cache misses em consultas BigQuery",
        ["tenant", "query_code"],
        registry=_registry,
    )


def is_enabled() -> bool:
    """Métricas habilitadas globalmente."""
    return bool(settings.metrics_enabled)


def _tenant_label(request_tenant: str | None) -> str:
    return request_tenant or "anonymous"


def record_http_request(
    method: str,
    path: str,
    status: int,
    duration_seconds: float,
    tenant_id: str | None = None,
) -> None:
    """Registra métrica de request HTTP."""
    if not is_enabled() or Counter is None:
        return
    _build_metrics()
    if _http_requests_total is None:
        return

    tenant = _tenant_label(tenant_id)
    _http_requests_total.labels(
        method=method.upper(),
        path=path,
        status=str(status),
        tenant=tenant,
    ).inc()
    _http_request_duration_seconds.labels(
        method=method.upper(),
        path=path,
        status=str(status),
        tenant=tenant,
    ).observe(duration_seconds)


def record_celery_task(task: str, status: str) -> None:
    """Registra sucesso/falha de tarefa Celery."""
    if not is_enabled() or Counter is None:
        return
    _build_metrics()
    if _celery_tasks_total is None:
        return
    _celery_tasks_total.labels(task=task, status=status).inc()


def record_bq_cache_hit(tenant_id: str | None, query_code: str) -> None:
    """Registra cache hit de BigQuery."""
    if not is_enabled() or Counter is None:
        return
    _build_metrics()
    if _bq_cache_hits_total is None:
        return
    _bq_cache_hits_total.labels(
        tenant=_tenant_label(tenant_id),
        query_code=query_code,
    ).inc()


def record_bq_cache_miss(tenant_id: str | None, query_code: str) -> None:
    """Registra cache miss de BigQuery."""
    if not is_enabled() or Counter is None:
        return
    _build_metrics()
    if _bq_cache_misses_total is None:
        return
    _bq_cache_misses_total.labels(
        tenant=_tenant_label(tenant_id),
        query_code=query_code,
    ).inc()


def get_metrics_payload() -> bytes:
    """Métricas no formato texto do Prometheus."""
    if not is_enabled():
        return b""
    return generate_latest(_registry) if _registry is not None else b""

