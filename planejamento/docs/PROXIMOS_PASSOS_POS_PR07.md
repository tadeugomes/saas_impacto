# Próximos Passos — SaaS Impacto Portuário

> Atualizado: 2026-02-20 | Pós PR-07 (SCM/Augmented SCM Interface)

---

## Estado Atual (PR-01 a PR-07 concluídos)

| PR | Escopo | Testes |
|----|--------|--------|
| PR-01 | Módulo 5 — alinhamento de 21 indicadores (catálogo + BigQuery) | — |
| PR-02 | Engine causal portado (DiD, IV, Panel IV, prep, comparison, serialize) | 30 |
| PR-03 | Panel Builder BigQuery → DataFrame + script de ingestão | 28 |
| PR-04 | Persistência (EconomicImpactAnalysis + Alembic + RLS) | — |
| PR-05 | API endpoints (schemas, AnalysisService, router) | 32 |
| PR-06 | Celery worker assíncrono + docker-compose worker | 56 |
| PR-07 | Interface SCM/ASCM com NotImplementedError + feature flag + HTTP 501 | 42 |

**Status adicional:** PR-13 foi iniciado (`RBAC granular`) com proteção de endpoints de leitura de indicador e análises causais via roles (`viewer`, `analyst`, `admin`) e plano (`basic`/`pro`/`enterprise`).
**Status atual:** PR-14 foi implementado (audit log + endpoint administrativo + middleware).
**Próximo PR sugerido:** PR-18 (CI/CD com GitHub Actions).

**Total de testes:** ~262 (cobrindo engine causal, panel builder, API, worker, SCM, observabilidade e compliance)

**O que funciona hoje:**
- Backend FastAPI com auth JWT, multi-tenancy (RLS), 81 indicadores definidos
- Engine causal: DiD, IV, Panel IV, Compare (SCM/ASCM bloqueados por feature flag)
- Pipeline completo: POST → Celery → BigQuery → engine causal → resultado em JSONB
- Frontend React com 7 módulos (visualização), Module5View com formulário de análise
- Docker Compose: api + worker + postgres + redis

---

## Fase 2 — Robustez e Completude do Core

### PR-08 — Event Study: implementação real
**Prioridade:** Alta | **Esforço:** Médio

O `event_study.py` existe como placeholder no schema e dispatch, mas sem implementação real.

**Entregas:**
- `causal/event_study.py`: regressão two-way FE com leads/lags dinâmicos (referência: Sun & Abraham 2021)
- Retorno: coeficientes por período relativo, CIs, gráfico de event study
- Integração no `_run_causal_pipeline()` do `analysis_service.py`
- Serialização via `serialize.py`
- Testes: 20-25 (geração de dados sintéticos com efeito conhecido)

**Dependência:** Nenhuma

---

### PR-09 — Cache Redis para queries BigQuery
**Prioridade:** Alta | **Esforço:** Médio

Atualmente cada request de indicador (Módulos 1-7) bate diretamente no BigQuery. O Redis está configurado mas não integrado nas queries.

**Entregas:**
- Decorator `@bq_cached(ttl=3600)` no `indicator_service.py` e `generic_indicator_service.py`
- Cache key: `bq:{module}:{indicator}:{hash(params)}` com TTL configurável por módulo
- Invalidação: endpoint admin `DELETE /admin/cache/{module}` ou TTL natural
- Métricas: header `X-Cache-Hit: true/false` nas respostas
- `config.py`: `bq_cache_ttl_seconds: int = 3600`, `bq_cache_enabled: bool = True`
- Testes: 15-20 (hit/miss, invalidação, serialização Redis de DataFrames)

**Dependência:** Nenhuma

---

### PR-10 — Relatório DOCX automático para análises de impacto
**Prioridade:** Alta | **Esforço:** Médio-Alto

O `reports/` existe com `docx_generator.py` e `report_service.py`, mas a integração com os resultados do engine causal precisa ser completada.

**Entregas:**
- Template DOCX com: resumo executivo, tabela de coeficientes, gráficos de event study, diagnósticos
- Endpoint `GET /impacto-economico/analises/{id}/report` → gera e retorna .docx
- `ReportService.generate_impact_report(analysis_id)`: busca result_full, renderiza template
- Suporte a todos os métodos (DiD, IV, Panel IV, Compare)
- Upload para GCS (artifact_path) com URL temporária
- Testes: 10-15

**Dependência:** PR-08 (para incluir event study no template)

---

### PR-11 — Health checks reais + observabilidade básica
**Prioridade:** Média | **Esforço:** Baixo

O `/health` atual retorna hardcoded `"connected"`. Sem métricas ou logging estruturado.
**Status:** Concluído.

**Entregas:**
- `GET /health`: verifica PostgreSQL (SELECT 1), Redis (PING), BigQuery (dry run)
- `GET /health/ready`: readiness probe (aceita tráfego)
- `GET /health/live`: liveness probe (processo vivo)
- Logging estruturado (structlog): request_id, tenant_id, duration_ms em cada log
- Middleware de request timing com header `X-Request-Duration-Ms`
- Testes: 8-10

**Dependência:** Nenhuma

---

## Fase 3 — Segurança e Multi-Tenancy Avançado

### PR-12 — Rate limiting + quotas por tenant
**Prioridade:** Alta | **Esforço:** Médio

SaaS sem rate limiting é vulnerável a abuso. Cada plano (basic, pro, enterprise) deve ter limites diferentes.

**Entregas:**
- Middleware `RateLimitMiddleware` usando Redis (sliding window)
- Limites padrão: basic=100 req/min, pro=500, enterprise=2000
- Limite específico para `/analises` (CPU-heavy): basic=5/hora, pro=20, enterprise=100
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- HTTP 429 Too Many Requests quando excedido
- `config.py`: rate limits configuráveis por plano
- Testes: 15-20

**Dependência:** Nenhuma

---

### PR-13 — RBAC granular + permissões por módulo
**Prioridade:** Média | **Esforço:** Médio

Atualmente roles são strings (`admin`, `analyst`, `viewer`) sem enforcement granular. Analyst e viewer acessam tudo.

**Entregas:**
- Tabela `permissions` (role, module, action: read/write/execute)
- Decorator `@require_permission("module5", "execute")` nos endpoints
- Admin pode configurar permissões via API
- Viewer: apenas leitura de indicadores; Analyst: leitura + criar análises; Admin: tudo
- Plano basic: Módulos 1-4 apenas; Pro: 1-7; Enterprise: 1-7 + métodos experimentais
- Testes: 20-25

**Dependência:** PR-12 (quotas informam enforcement)

---

### PR-14 — Audit log + compliance
**Prioridade:** Média | **Esforço:** Baixo-Médio

**Status:** Concluído

Para SaaS B2B/governo, auditoria é essencial.

**Entregas:**
- Tabela `audit_logs` (tenant_id, user_id, action, resource, details, ip, timestamp)
- Middleware que registra: criação/atualização/deleção de recursos
- `AuditService.log(action, resource, details)`
- Retenção configurável por tenant (padrão: 90 dias)
- Endpoint `GET /admin/audit-logs?page=1&action=create_analysis`
- Testes: 10-12

**Dependência:** Nenhuma

---

## Fase 4 — Frontend Production-Ready

### PR-15 — Refatoração de rotas + lazy loading
**Prioridade:** Média | **Esforço:** Baixo

Routes definidas inline em `App.tsx`. Sem code splitting.

**Entregas:**
- `router/routes.tsx`: definição centralizada de rotas com React.lazy()
- Cada ModuleView carrega sob demanda (reduce initial bundle ~40%)
- ProtectedRoute wrapper com redirect para login
- Breadcrumbs component baseado na rota atual
- Testes: E2E básico de navegação

**Dependência:** Nenhuma

---

### PR-16 — Module5View: polling + visualização de resultados
**Prioridade:** Alta | **Esforço:** Médio

O Module5View existe mas a integração com o backend (polling de status, display de resultados) precisa ser completada.

**Entregas:**
- Hook `useAnalysis(id)`: polling automático (2s queued, 5s running, stop on success/failed)
- Componente `AnalysisResultCard`: tabela de coeficientes, significância, diagnósticos
- Componente `EventStudyChart`: gráfico de coeficientes por período (Chart.js)
- Componente `MethodComparisonTable`: quando method=compare, mostra lado a lado
- Status badges: queued (amarelo), running (azul), success (verde), failed (vermelho)
- Download: JSON bruto + CSV dos coeficientes
- Testes: Component tests com React Testing Library

**Dependência:** PR-08 (event study chart precisa dos dados reais)

---

### PR-17 — Dashboard de indicadores (Módulos 1-4)
**Prioridade:** Média | **Esforço:** Médio-Alto

ModuleViews 1-4 existem mas com visualização básica. Precisa de charts reais, comparações, exports.

**Entregas:**
- Cada módulo: gráficos de série temporal (LineChart) + ranking de instalações (BarChart)
- FilterBar funcional: seleção de instalação, range de anos, granularidade (anual/mensal)
- Tabela de dados com ordenação e filtro local
- ExportButton: CSV e PDF do indicador selecionado
- Indicador selector: dropdown com os N indicadores do módulo
- Integração com cache Redis (headers X-Cache-Hit)
- Testes: Component tests

**Dependência:** PR-09 (cache para não sobrecarregar BigQuery)

---

## Fase 5 — Infraestrutura e Deploy

### PR-18 — CI/CD com GitHub Actions
**Prioridade:** Alta | **Esforço:** Médio

Sem CI/CD atualmente.
**Status:** Implementado (pipeline de qualidade melhorada: validação de arquivos alterados para `ruff`, `mypy` com execução incremental por PR, lint completo de `frontend/src` sem fallback; regras de lint em modo progressivamente rigoroso e já aplicadas para `no-explicit-any`, `no-unused-vars`, `no-useless-catch`, `no-empty-pattern` e `react-hooks/exhaustive-deps` em todo o `src`; deploy para GCP condicionado à conclusão com sucesso do workflow `CI`).

**Entregas:**
- `.github/workflows/ci.yml`:
  - Trigger: push/PR para main
  - Jobs: lint (ruff/mypy), test (pytest com PostgreSQL service container), build (Docker)
  - Matrix: Python 3.11, Node 20
  - Frontend: lint (eslint), build (vite build), type-check (tsc)
  - Qualidade progressiva concluída para `frontend/src`: regra `@typescript-eslint/no-explicit-any`, `@typescript-eslint/no-unused-vars`, `no-useless-catch`, `no-empty-pattern` e `react-hooks/exhaustive-deps` já ativas em lint completo.
- `.github/workflows/deploy.yml`:
  - Trigger: merge em main
  - Build multi-arch Docker images
  - Push para GCR/Artifact Registry
  - Deploy para Cloud Run (api) + Cloud Run Jobs (worker)
- Secrets: GCP_SA_KEY, DATABASE_URL, REDIS_URL

**Dependência:** Nenhuma

---

### PR-19 — Terraform/IaC para GCP
**Prioridade:** Média | **Esforço:** Alto

Infraestrutura como código para ambientes staging/production.

**Entregas:**
- `infra/terraform/`:
  - Cloud SQL (PostgreSQL 16) com private VPC
  - Memorystore (Redis 7)
  - Cloud Run (api + worker)
  - Cloud Storage (relatórios/artifacts)
  - Secret Manager (env vars)
  - VPC + Cloud NAT
  - IAM (service accounts com least privilege)
- Ambientes: staging, production (workspaces ou directories)
- Estado remoto: GCS backend

**Dependência:** PR-18 (CI/CD para executar terraform plan/apply)

---

## Fase 6 — Funcionalidades Avançadas

### PR-20 — Port do SCM real (synthetic_control.py)
**Prioridade:** Média | **Esforço:** Alto

Quando os arquivos `synthetic_control.py` e `synthetic_augmented.py` forem recuperados do `new_impacto`.

**Entregas:**
- Substituir stubs em `scm.py` e `augmented_scm.py` por implementação real
- Habilitar flags `ENABLE_SCM=true`, `ENABLE_AUGMENTED_SCM=true`
- Validação com dados reais de Santos
- Testes de regressão: 25-30

**Dependência:** Recuperação dos arquivos do repositório `new_impacto`

---

### PR-21 — Comparação automatizada de municípios (matching)
**Prioridade:** Baixa | **Esforço:** Alto

Automatizar a seleção do grupo de controle (hoje manual: control_ids).

**Entregas:**
- `causal/matching.py`: Propensity Score Matching ou Coarsened Exact Matching
- Endpoint: `POST /impacto-economico/matching` → sugere control_ids dado treated_ids
- Covariáveis: PIB, população, emprego portuário, comércio exterior
- Integração opcional no fluxo de criação de análise

**Dependência:** PR-20 (SCM real se beneficia de matching)

---

### PR-22 — Notificações (webhook + email)
**Prioridade:** Baixa | **Esforço:** Médio

Análises de impacto demoram minutos. O usuário precisa ser notificado quando terminar.

**Entregas:**
- Tabela `notification_preferences` (tenant_id, user_id, channel, enabled)
- Celery task `send_notification` ao final de cada análise
- Canais: email (SendGrid/SES), webhook (POST para URL configurada)
- Endpoint: `PUT /users/me/notifications` para configurar preferências
- Testes: 10-12

**Dependência:** PR-18 (CI/CD para secrets de email)

---

## Sequência Sugerida de Execução

```
Fase 2 (Robustez):    PR-08 → PR-09 → PR-10 → PR-11
                         │                │
Fase 3 (Segurança):     │    PR-12 → PR-13 → PR-14
                         │
Fase 4 (Frontend):       └─→ PR-15 → PR-16 → PR-17
                                        │
Fase 5 (Infra):         PR-18 ────────→ PR-19
                           │
Fase 6 (Avançado):        └─→ PR-20 → PR-21 → PR-22
```

**Caminho crítico para MVP SaaS:** PR-08 → PR-09 → PR-12 → PR-16 → PR-18

Esses 5 PRs transformam o projeto de "engine causal com API" em "SaaS funcional e deployável".

---

## Métricas de Progresso

| Métrica | Atual | Pós-Fase 2 | Pós-Fase 4 | Pós-Fase 5 |
|---------|-------|------------|------------|------------|
| Testes | ~188 | ~260 | ~340 | ~360 |
| Métodos causais ativos | 4 | 5 | 5 | 5-7 |
| Endpoints API | ~15 | ~20 | ~20 | ~25 |
| Cache hit rate | 0% | ~70% | ~70% | ~70% |
| CI/CD | ❌ | ❌ | ❌ | ✅ |
| Rate limiting | ❌ | ❌ | ✅ | ✅ |
| Audit trail | ❌ | ❌ | ✅ | ✅ |
