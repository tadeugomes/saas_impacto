# Próximos Passos — SaaS Impacto Portuário

> Atualizado: 2026-02-20 | Auditoria pós-sprint de robustez/segurança

---

## Inventário completo de PRs concluídos

| PR | Escopo | Testes | Status |
|----|--------|--------|--------|
| PR-01 | Módulo 5 — alinhamento 21 indicadores | — | ✅ |
| PR-02 | Engine causal (DiD, IV, Panel IV, prep, comparison, serialize) | 30 | ✅ |
| PR-03 | Panel Builder BigQuery → DataFrame + ingestão | 28 | ✅ |
| PR-04 | Persistência (EconomicImpactAnalysis + Alembic + RLS) | — | ✅ |
| PR-05 | API endpoints (schemas, AnalysisService, router) | 32 | ✅ |
| PR-06 | Celery worker assíncrono + docker-compose | 56 | ✅ |
| PR-07 | Interface SCM/ASCM + feature flag + HTTP 501 | 42 | ✅ |
| PR-08 | Event Study real (TWFE + Sun & Abraham, statsmodels) | +30 | ✅ |
| PR-09 | Cache Redis para queries BigQuery (`IndicatorQueryCache`) | +20 | ✅ |
| PR-10 | Relatório DOCX (ReportService + DOCXGenerator para indicadores) | +12 | ✅ |
| PR-11 | Health checks reais + request timing middleware | +10 | ✅ |
| PR-12 | Rate limiting Redis (sliding window, por plano/tenant) | +18 | ✅ |
| PR-13 | RBAC granular (tabela permissions, decorators, endpoints protegidos) | +35 | ✅ |
| PR-14 | Audit log (tabela, AuditMiddleware, AuditService, admin endpoint) | +22 | ✅ |
| PR-18 | CI/CD GitHub Actions (lint, test, build, deploy GCP Cloud Run) | — | ✅ |

**Total acumulado:** ~305 testes, 5.082 linhas de teste, 20 arquivos

**Stack atual em produção:**
- FastAPI + asyncpg + SQLAlchemy 2.0 + Alembic (5 migrations)
- Celery + Redis (broker + cache + rate limit)
- BigQuery (81 indicadores, 7 módulos)
- RBAC + RLS + Audit + Rate Limit
- CI/CD → Cloud Run (api + worker)

---

## Gap analysis — o que ficou incompleto

### Lacunas descobertas na auditoria

| Item | Situação | Impacto |
|------|----------|---------|
| Rota `/dashboard/module5` ausente do `routes.tsx` | Componente `Module5View` existe mas está desconectado | Alto — feature invisível no frontend |
| Relatório DOCX para análise de impacto causal | `ReportService` cobre indicadores; `result_full` da análise causal não é exportado | Alto — entrega core do produto |
| Logging estruturado (structlog) | `logging` padrão, sem JSON fields; sem tenant_id/request_id no log | Médio — dificulta debugging em produção |
| Purge periódico de audit_logs | Método `purge_expired()` existe mas não é chamado automaticamente | Médio — acumulo ilimitado no Postgres |
| Terraform/IaC | CI/CD deploy existe mas infraestrutura criada manualmente | Médio — não reproduzível |
| Notificações (webhook/email) | Não iniciado | Baixo — UX melhor para análises longas |
| SCM/Augmented SCM port real | Stubs com NotImplementedError, aguardando `new_impacto` | Baixo — bloqueado por dependência externa |

---

## Próximos PRs planejados

---

### PR-19 — Frontend: conectar Module5View + polish de UX

**Prioridade:** Crítica | **Esforço:** Baixo
**Objetivo:** Tornar o módulo de análise causal acessível no produto — sem isso, todo o backend de impacto é invisível ao usuário.

**Entregas:**
- `router/routes.tsx`: adicionar rota `/dashboard/module5` → `Module5View` (lazy)
- `DashboardHome.tsx`: card do Módulo 5 com link funcional (remover `disabled` ou placeholder)
- Conectar `Module5View` ao hook de polling `useAnalysis(id)`:
  - Intervalo: 2s enquanto `queued`, 5s enquanto `running`, parar em `success`/`failed`
  - Status badge: queued (âmbar), running (azul), success (verde), failed (vermelho)
- Componente `AnalysisResultCard` integrado ao resultado real da API (`result_summary`)
- Componente `EventStudyChart` integrado quando `method = event_study`
- Componente `MethodComparisonTable` integrado quando `method = compare`
- Download: botão "Exportar CSV" (coeficientes) + "Exportar JSON" (result_full)
- Formulário de criação: validação client-side (ano ≥ 2000, pelo menos 1 treated + 1 control)
- Testes: React Testing Library para os 4 novos componentes + hook

**Dependência:** Nenhuma — componentes já existem, só falta conectar.

---

### PR-20 — Relatório DOCX para análise de impacto causal

**Prioridade:** Alta | **Esforço:** Médio
**Objetivo:** Entregar um produto tangível ao usuário após a análise — relatório em Word com metodologia, resultados e diagnósticos.

**Entregas:**
- `reports/impact_report_service.py`: novo serviço específico para análise causal
  - `generate_impact_report(analysis: EconomicImpactAnalysis) → bytes`
  - Lê `result_full` (ou busca de `artifact_path` no GCS se payload grande)
  - Renderiza seções: capa, resumo executivo, especificação do método, tabela de coeficientes, diagnósticos (p-valores, n_obs, R²), event study chart como imagem (matplotlib), notas metodológicas
  - Suporte a todos os métodos: DiD, IV, Panel IV, Event Study, Compare
- `reports/templates/impact_report.py`: constantes de formatação ABNT-compatible
- Endpoint novo: `GET /impacto-economico/analises/{id}/report`
  - Retorna Content-Disposition: attachment; filename=relatorio_impacto_{id}.docx
  - Requer status = `success`; retorna 409 se ainda rodando, 404 se não encontrado
  - Requer permissão `module5:read`
- Upload para GCS (opcional): link temporário de 24h se habilitado
- Testes: 12-15 (mock de `result_full` para cada método, geração de bytes válidos)

**Dependência:** PR-19 (botão de download no frontend)

---

### PR-21 — Logging estruturado com structlog

**Prioridade:** Alta | **Esforço:** Baixo
**Objetivo:** Logs legíveis por máquina no Cloud Logging do GCP — indispensável para debugging em produção multi-tenant.

**Entregas:**
- `pip install structlog` adicionado ao `requirements.txt`
- `app/core/logging.py`: configuração do structlog
  - Renderer: JSON em produção, ConsoleRenderer colorido em dev
  - Processors padrão: add_log_level, add_timestamp, render_to_log_kwargs
  - Processadores customizados: `inject_request_context` (request_id, tenant_id, user_id via contextvars)
- `RequestTimingMiddleware` (atualizado): popula `structlog.contextvars` com request_id, tenant_id
- Substituição de `logger.info(...)` por `structlog.get_logger().info(...)` nos módulos principais:
  - `main.py`, `core/audit.py`, `services/impacto_economico/analysis_service.py`, `tasks/impacto_economico.py`
- Worker Celery: `structlog` configurado com task_id como campo padrão
- Testes: 5-8 (verificar que log contém campos obrigatórios)

**Dependência:** Nenhuma

---

### PR-22 — Purge automático de audit_logs + retenção configurável

**Prioridade:** Média | **Esforço:** Baixo
**Objetivo:** Evitar acúmulo ilimitado de logs no Postgres e garantir conformidade com políticas de retenção de dados.

**Entregas:**
- Celery beat schedule: task `purge_old_audit_logs` rodando diariamente (cron: `0 3 * * *`)
- `tasks/maintenance.py`: task Celery que chama `AuditService.purge_expired(db)`
- `celery_app.py`: adicionar `beat_schedule` com a task de purge
- `docker-compose.yml`: adicionar serviço `beat` (celery beat scheduler)
- `config.py`: `audit_log_retention_days: int = 90` (já existe, agora usado de verdade)
- Admin endpoint: `POST /admin/audit-logs/purge` (executa manualmente, requer admin)
- Testes: 5-8

**Dependência:** Nenhuma

---

### PR-23 — Terraform/IaC para GCP staging + production

**Prioridade:** Alta | **Esforço:** Alto
**Objetivo:** Infraestrutura como código — ambiente reproduzível, zero-manual-click para subir staging ou produção.

**Entregas:**
- `infra/terraform/`:
  - `modules/cloud_run/`: API + Worker (variáveis: image, cpu, memory, env_vars)
  - `modules/cloud_sql/`: Cloud SQL PostgreSQL 16 com private VPC
  - `modules/memorystore/`: Redis 7 Memorystore
  - `modules/storage/`: GCS bucket para relatórios/artifacts
  - `modules/secrets/`: Secret Manager (DATABASE_URL, REDIS_URL, JWT_SECRET, GCP_SA_KEY)
  - `modules/iam/`: Service accounts com least-privilege
  - `modules/vpc/`: VPC privada + Cloud NAT + Connector para Cloud Run
  - `environments/staging/main.tf`: módulos com configs de staging
  - `environments/production/main.tf`: módulos com configs de produção
  - `backend.tf`: estado remoto no GCS (bucket: `saas-impacto-tfstate`)
- `infra/README.md`: instruções de bootstrap do estado remoto
- `.github/workflows/terraform.yml`:
  - `terraform plan` em PRs (comentário automático no PR)
  - `terraform apply` automático em merge para staging
  - Apply manual (workflow_dispatch) para produção

**Dependência:** PR-18 (CI/CD já configurado)

---

### PR-24 — Notificações: webhook + email ao fim de análise

**Prioridade:** Média | **Esforço:** Médio
**Objetivo:** UX — análises casuais demoram minutos; usuário não deve ficar com aba aberta esperando.

**Entregas:**
- Tabela `notification_preferences` (tenant_id, user_id, channel: email|webhook, endpoint, enabled)
- Migration Alembic correspondente
- `tasks/notifications.py`: task Celery `notify_analysis_complete(analysis_id, tenant_id)`
  - Chamada no final de `run_economic_impact_analysis` (success + failed)
  - Canal email: SendGrid SDK (ou SMTP se configurado)
  - Canal webhook: HTTP POST com payload `{analysis_id, status, method, tenant_id}`
  - Retry: 3x com backoff de 60s
- `services/notification_service.py`: CRUD de preferências
- Endpoints:
  - `GET /users/me/notifications` — listar preferências
  - `PUT /users/me/notifications` — atualizar preferências
- `config.py`: `sendgrid_api_key`, `notifications_enabled: bool = False`
- Testes: 10-12

**Dependência:** PR-22 (celery beat configurado; reutiliza infraestrutura de tasks)

---

### PR-25 — SCM port real (synthetic_control.py de `new_impacto`)

**Prioridade:** Média | **Esforço:** Alto (bloqueado por dependência externa)
**Objetivo:** Substituir stubs por implementação real quando `synthetic_control.py` for disponibilizado.

**Entregas:**
- `causal/scm.py`: implementação real de `run_scm()` e `run_scm_with_diagnostics()`
  - Placebos de espaço (donors) e tempo (pre-treatment)
  - Retorno compatível com `comparison.py` (`scm_result` key)
- `causal/augmented_scm.py`: implementação real (Ben-Michael et al. 2021)
  - Ridge regression + SCM
  - Retorno: `augmented_result`
- Habilitar flags `ENABLE_SCM=true`, `ENABLE_AUGMENTED_SCM=true` em produção
- Testes de regressão: 25-30 (dados sintéticos com efeito conhecido)
- Remoção da migration `d7e8f9a0b1c2` de "NotImplementedError stubs" do changelog

**Dependência:** Recuperação dos arquivos do repositório `new_impacto`

---

### PR-26 — Matching automático de controles (PSM/CEM)

**Prioridade:** Baixa | **Esforço:** Alto
**Objetivo:** Remover a necessidade de o usuário especificar `control_ids` manualmente — sugere controles estatisticamente comparáveis.

**Entregas:**
- `causal/matching.py`: Propensity Score Matching (scikit-learn LogisticRegression) ou Coarsened Exact Matching
  - Covariáveis de balanceamento: PIB per capita, população, emprego portuário, volume de comércio
  - Retorno: lista ordenada de `control_ids` com score de similaridade
- Endpoint: `POST /impacto-economico/matching`
  - Input: `{treated_ids, treatment_year, scope, n_controls?}`
  - Output: `{suggested_controls: [{id, similarity_score}], balance_table: {...}}`
- Integração opcional: form de criação no Module5View com botão "Sugerir controles"
- Testes: 15

**Dependência:** PR-25 (SCM real se beneficia de matching para seleção de donors)

---

## Sequência de execução recomendada

```
Imediato (visibilidade e completude):
  PR-19 → PR-20 → PR-21
     │        │
     └────────┴──→ PR-22 (operações / beat)

Infraestrutura:
  PR-23 (Terraform)

Funcionalidades avançadas (quando desbloqueadas):
  PR-24 → PR-25 → PR-26
```

**Caminho crítico para produto pronto para demo:** PR-19 → PR-20

Com apenas esses 2 PRs, o produto passa de "API funcional" para "produto demonstrável" — um usuário consegue criar uma análise, ver o progresso em tempo real na UI e baixar um relatório Word com os resultados.

---

## Métricas de progresso atualizado

| Métrica | Agora | Pós PR-19/20 | Pós PR-23 | Completo |
|---------|-------|--------------|-----------|---------|
| Testes | ~305 | ~340 | ~340 | ~400 |
| Métodos causais ativos | 5 (sem SCM) | 5 | 5 | 7 |
| Endpoints API | ~20 | ~23 | ~23 | ~28 |
| Módulos visíveis no frontend | 6 de 7 | 7 de 7 | 7 de 7 | 7 de 7 |
| Relatório DOCX para impacto | ❌ | ✅ | ✅ | ✅ |
| Terraform/IaC | ❌ | ❌ | ✅ | ✅ |
| Notificações | ❌ | ❌ | ❌ | ✅ |
| SCM real | ❌ | ❌ | ❌ | ✅ |
| Logs estruturados (GCP) | ❌ | ✅ | ✅ | ✅ |
