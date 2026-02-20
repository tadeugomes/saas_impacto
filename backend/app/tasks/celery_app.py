"""
Instância Celery centralizada para o SaaS Impacto Portuário.

Configurações carregadas via ``app.config.Settings``:
  - ``celery_broker_url``  → Redis db=1 (fila de mensagens)
  - ``celery_result_backend`` → Redis db=2 (resultados de tasks)

Fila dedicada para análises causais: ``economic_impact``

Uso:
    # Iniciar worker em desenvolvimento:
    celery -A app.tasks.celery_app.celery_app worker \\
        --loglevel=info -Q economic_impact,celery -c 2

    # Monitorar tasks (requer Flower):
    celery -A app.tasks.celery_app.celery_app flower
"""
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

# ── Instância principal ────────────────────────────────────────────────────
celery_app = Celery(
    "saas_impacto",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    # Registro automático das tasks ao importar o pacote
    include=["app.tasks.impacto_economico", "app.tasks.maintenance", "app.tasks.notifications"],
)

# ── Configuração global ────────────────────────────────────────────────────
celery_app.conf.update(
    # Serialização
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Confiabilidade
    task_track_started=True,   # task.state == "STARTED" visível no broker
    task_acks_late=True,       # ack só após conclusão; previne perda em crash
    worker_prefetch_multiplier=1,  # 1 task por processo (análises são pesadas)
    # Timeout: análise causal pode levar vários minutos
    task_soft_time_limit=900,  # 15 min → SoftTimeLimitExceeded
    task_time_limit=1200,      # 20 min → processo encerrado forçosamente
    # Roteamento de filas
    task_routes={
        "app.tasks.impacto_economico.*": {"queue": "economic_impact"},
    },
    # Retentativas padrão (sobrescrito por task individualmente)
    task_default_retry_delay=60,   # 60 s entre tentativas
    task_max_retries=3,
)

celery_app.conf.beat_schedule = {
    "purge-expired-audit-logs": {
        "task": "app.tasks.maintenance.purge_expired_audit_logs",
        "schedule": crontab(hour=3, minute=0),
    }
}
