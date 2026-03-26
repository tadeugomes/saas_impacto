# Infraestrutura — SaaS Impacto Portuário

## Estrutura

```
infra/
├── terraform/          # IaC — GCP (Cloud Run, Cloud SQL, Memorystore, GCS, IAM, VPC)
└── grafana/            # Dashboard e alertas Grafana (importáveis)
    ├── dashboard_saas_impacto.json
    └── alerts.yaml
```

---

## Terraform

Ver [`terraform/README.md`](terraform/README.md) para instruções completas de provisionamento de staging e produção.

---

## Grafana — Dashboard e Alertas

### Pré-requisitos

- Grafana ≥ 10.0 (Cloud, self-hosted ou Grafana Cloud)
- Datasource **Prometheus** configurado apontando para:
  - Prometheus do OpenTelemetry Collector, **ou**
  - Cloud Monitoring via plugin `grafana-googlecloud-monitoring-datasource`

As métricas são emitidas pelo backend via OpenTelemetry (PR-29) com os prefixos:
- `http_requests_total` — request rate e error rate
- `http_request_duration_seconds` — latência (histogram)
- `celery_tasks_total` — tasks do worker Celery por estado
- `bigquery_cache_hits_total` / `bigquery_cache_misses_total` — cache Redis do BigQuery
- `causal_analyses_total` — análises causais por método e status

### Importar o dashboard

1. Abra Grafana → **Dashboards → Import**
2. Faça upload de `grafana/dashboard_saas_impacto.json`
3. Na tela de importação, selecione o datasource Prometheus correto no campo `DS_PROMETHEUS`
4. Clique **Import**

O dashboard contém 4 seções:
| Seção | Painéis |
|-------|---------|
| Request Rate e Latência | Request rate por tenant, latência P50/P95/P99, error rate 5xx |
| Celery — Tasks Assíncronas | Tasks por status (queued/running/success/failed), stat de falhas e fila |
| BigQuery — Cache e Custo | Cache hit rate, bytes faturados por dia |
| Análises Causais | Análises por método (DiD/IV/Event Study/SCM), por status (running/completed/failed) |

### Provisionar alertas

```bash
# Via API do Grafana (substitua URL e API key)
curl -X POST \
  -H "Content-Type: application/yaml" \
  -H "Authorization: Bearer <grafana-api-key>" \
  --data-binary @infra/grafana/alerts.yaml \
  https://<grafana-host>/api/v1/provisioning/alert-rules/export
```

Ou copie `alerts.yaml` para o diretório de provisionamento do Grafana:
```
/etc/grafana/provisioning/alerting/saas_impacto_alerts.yaml
```
e reinicie o Grafana.

### Alertas configurados

| Alerta | Condição | Severidade | Prazo |
|--------|----------|------------|-------|
| API Error Rate > 1% | Taxa 5xx > 1% por 2 min | critical | 2 min |
| API Latência P95 > 2s | P95 > 2s por 5 min | warning | 5 min |
| Celery Failures > 5/min | Falhas > 5 por minuto | critical | 2 min |
| BigQuery Cache Hit < 30% | Hit rate < 30% por 10 min | warning | 10 min |

### Variáveis de ambiente necessárias no backend

Confirme que o `.env` de produção contém:
```
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_SERVICE_NAME=saas-impacto-api
```
(configurados em PR-29 — OpenTelemetry + Prometheus)
