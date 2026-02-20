# Fase 3 — Hardening, Produto e Escala

> Atualizado: 2026-02-20 | Pós conclusão de PRs 01-26

---

## Onde estamos

O SaaS Impacto Portuário completou dois ciclos de desenvolvimento:

**Ciclo 1 (PR-01 a PR-07):** Fundação — engine causal, panel builder, persistência, API, worker async, interface SCM com feature flag.

**Ciclo 2 (PR-08 a PR-26):** Robustez e completude — Event Study real, cache Redis, relatórios DOCX, health checks, rate limiting, RBAC, audit log, CI/CD, Terraform, notificações, SCM real, matching automático.

**Resultado atual:**
- 7 módulos com 81 indicadores, todos com queries BigQuery
- 7 métodos causais (DiD, IV, Panel IV, Event Study, Compare, SCM, Augmented SCM)
- Multi-tenant com RLS, RBAC granular, audit log, rate limiting
- Frontend React com 7 views, polling de análises, charts de event study
- CI/CD completo (GitHub Actions → Cloud Run) + Terraform para GCP
- ~194 testes coletados, 4.758 linhas de teste

**Score de prontidão:** Backend 90%, Frontend 95%, Infra 85%, Segurança 75%.

---

## Gap analysis — dívidas técnicas e riscos identificados

### Riscos críticos (bloqueiam demo/produção)

| # | Gap | Risco | Esforço |
|---|-----|-------|---------|
| G1 | `structlog` ausente do `requirements.txt` | RuntimeError em produção ao acessar logs estruturados | 5 min |
| G2 | Sem endpoint de reset de senha | Usuário travado se esquecer senha; bloqueio de onboarding | 2h |
| G3 | JWT sem blacklist no logout | Token continua válido até expirar (30 min); risco de sessão fantasma | 1h |

### Riscos operacionais

| # | Gap | Risco | Esforço |
|---|-----|-------|---------|
| G4 | Sem CRUD de tenant via API | Admin precisa de acesso ao banco para criar/editar tenants | 3h |
| G5 | Swagger/ReDoc desabilitado em produção | Integradores não conseguem explorar a API | 30 min |
| G6 | Sem monitoramento de métricas (Prometheus/OpenTelemetry) | Cego em produção — não sabe latência, throughput, error rate | 4h |
| G7 | Sem data refresh agendado do BigQuery | Dados podem ficar defasados se ANTAQ atualizar | 2h |

---

## PRs planejados — Ciclo 3

---

### PR-27 — Hotfixes de produção (structlog + segurança auth)

**Prioridade:** Bloqueante | **Esforço:** 3h
**Objetivo:** Corrigir os 3 gaps que impedem deploy seguro.

**Entregas:**

1. **structlog no requirements.txt**
   - Adicionar `structlog>=24.1.0` ao `requirements.txt`
   - Verificar que `configure_structlog()` funciona end-to-end
   - Testes: 3 (import, configure, log com campos)

2. **Password reset com token temporário**
   - Endpoint `POST /auth/password-reset/request` → gera token (UUID, 1h TTL, armazenado em Redis)
   - Endpoint `POST /auth/password-reset/confirm` → valida token, atualiza senha
   - Template de email via SendGrid (já configurado no PR-24)
   - Schema: `PasswordResetRequest(email)`, `PasswordResetConfirm(token, new_password)`
   - Testes: 8 (fluxo completo, token expirado, token inválido, senha fraca)

3. **JWT blacklist no Redis**
   - No logout (`POST /auth/logout`): `redis.setex(f"blacklist:{jti}", ttl, "1")` onde `jti` é o JWT ID
   - No `decode_access_token()`: verificar se `jti` está na blacklist
   - TTL = tempo restante até expiração do token (não polui Redis)
   - Testes: 5 (logout invalida, token expirado não verifica, blacklist sobrevive a requests)

**Dependência:** Nenhuma

---

### PR-28 — Admin: CRUD de tenants + gestão de usuários

**Prioridade:** Alta | **Esforço:** 4h
**Objetivo:** Permitir que administradores gerenciem tenants e usuários pela API sem acesso direto ao banco.

**Entregas:**

- `api/v1/admin_tenants.py`: novo router
  - `POST /admin/tenants` — criar tenant (nome, slug, plano, instalações permitidas)
  - `GET /admin/tenants` — listar tenants (paginado)
  - `GET /admin/tenants/{id}` — detalhe do tenant
  - `PATCH /admin/tenants/{id}` — atualizar (plano, nome, status)
  - `DELETE /admin/tenants/{id}` — desativar (soft delete, não cascata)

- `api/v1/admin_users.py`: novo router
  - `GET /admin/tenants/{tenant_id}/users` — listar usuários do tenant
  - `PATCH /admin/users/{id}` — atualizar roles, status
  - `DELETE /admin/users/{id}` — desativar usuário

- Todos protegidos por `@require_admin()`
- Schemas: `TenantCreate`, `TenantUpdate`, `TenantDetail`, `UserAdminUpdate`
- Audit log: todas as ações de admin registradas automaticamente pelo middleware
- Testes: 15

**Dependência:** PR-27 (auth completo)

---

### PR-29 — Observabilidade: OpenTelemetry + métricas Prometheus

**Prioridade:** Alta | **Esforço:** 5h
**Objetivo:** Visibilidade operacional — saber o que acontece em produção antes de receber reclamações.

**Entregas:**

- `pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi opentelemetry-exporter-gcp-trace`
- `app/core/telemetry.py`: configuração do OpenTelemetry
  - Traces: cada request gera span com tenant_id, user_id, method, path, duration
  - Export: Google Cloud Trace (produção), ConsoleSpanExporter (dev)
  - Auto-instrumentação: FastAPI, SQLAlchemy, Redis, httpx
- `app/core/metrics.py`: métricas Prometheus (opcional)
  - `http_requests_total` (counter, labels: method, path, status, tenant)
  - `http_request_duration_seconds` (histogram)
  - `celery_tasks_total` (counter, labels: task, status)
  - `bq_cache_hits_total` / `bq_cache_misses_total`
  - Endpoint: `GET /metrics` (se habilitado)
- Dashboard pré-configurado (JSON para importar no Cloud Monitoring ou Grafana)
- `config.py`: `otel_enabled: bool`, `otel_exporter: str = "gcp"`, `metrics_enabled: bool`
- Testes: 8

**Dependência:** Nenhuma

---

### PR-30 — API pública: documentação OpenAPI + versionamento

**Prioridade:** Alta | **Esforço:** 3h
**Objetivo:** Tornar a API consumível por integradores externos (outras secretarias, consultorias, pesquisadores).

**Entregas:**

- Habilitar Swagger em produção com autenticação (Basic ou token)
  - `docs_url="/docs"` sempre; proteção via middleware que requer header
- OpenAPI metadata: título, descrição, versão, contato, licença, tags por módulo
- Schemas com `json_schema_extra` em todos os modelos Pydantic:
  - `example` para request/response (facilita "Try it" no Swagger)
- Geração automática de SDK:
  - `scripts/generate_sdk.py`: gera client Python via `openapi-python-client`
  - Instruções para gerar client TypeScript via `openapi-typescript-codegen`
- `docs/API_GUIDE.md`: guia de integração com exemplos curl/Python/JS
- Testes: 5 (schema examples válidos, docs endpoint acessível)

**Dependência:** PR-28 (endpoints de admin documentados)

---

### PR-31 — Tenant onboarding flow (self-service)

**Prioridade:** Média | **Esforço:** 6h
**Objetivo:** Permitir que novos clientes criem conta e comecem a usar o produto sem intervenção manual.

**Entregas:**

- **Backend:**
  - `POST /onboarding/register` — cria tenant + admin user em uma transação
    - Input: empresa, CNPJ, email, senha, plano selecionado
    - Output: tenant_id, user_id, access_token (já logado)
  - Seeding automático: ao criar tenant, insere permissões padrão por plano
  - Email de boas-vindas via SendGrid com instruções iniciais
  - `services/onboarding_service.py`: lógica de criação + setup

- **Frontend:**
  - `views/Onboarding/RegisterView.tsx`: formulário multi-step
    - Step 1: dados da empresa (nome, CNPJ)
    - Step 2: plano (basic, pro, enterprise) com comparativo
    - Step 3: conta admin (nome, email, senha)
    - Step 4: confirmação → redirect para dashboard
  - Rota `/register` no router (pública)

- Testes: 12 (backend) + component tests (frontend)

**Dependência:** PR-28 (tenant CRUD)

---

### PR-32 — Exportação avançada: PDF + Excel para indicadores

**Prioridade:** Média | **Esforço:** 4h
**Objetivo:** Além do DOCX que já existe, oferecer exportação em PDF e Excel para indicadores e análises.

**Entregas:**

- `reports/pdf_generator.py`: geração de PDF via ReportLab ou WeasyPrint
  - Capa com logo, título, data
  - Tabelas de indicadores formatadas
  - Gráficos embutidos como imagens (matplotlib → PNG → PDF)
  - Rodapé com "Gerado por SaaS Impacto Portuário" + timestamp
- `reports/xlsx_generator.py`: geração de Excel via openpyxl
  - Aba "Resumo" com métricas-chave
  - Aba por outcome/indicador com dados brutos
  - Formatação: cabeçalho colorido, bordas, colunas auto-ajustadas
  - Fórmulas: totais, médias onde aplicável
- Endpoints:
  - `GET /impacto-economico/analises/{id}/report?format=pdf|docx|xlsx`
  - `GET /indicators/{code}/export?format=pdf|xlsx`
- Frontend: dropdown de formato no botão "Exportar"
- Testes: 10

**Dependência:** Nenhuma

---

### PR-33 — Dashboard analítico do tenant (admin)

**Prioridade:** Média | **Esforço:** 6h
**Objetivo:** Painel para o admin do tenant ver uso, consumo e resultados.

**Entregas:**

- **Backend:**
  - `GET /admin/dashboard/usage` — métricas agregadas:
    - Total de análises (por status, por método, por mês)
    - Usuários ativos (últimos 7/30 dias)
    - Indicadores mais consultados (top 10)
    - Consumo BigQuery estimado (bytes processados, via audit_log)
    - Rate limit utilization (% do plano)
  - `services/dashboard_service.py`: queries agregadas no PostgreSQL

- **Frontend:**
  - `views/Admin/AdminDashboard.tsx`:
    - Cards: total de análises, usuários, indicadores consultados
    - Gráfico de uso por mês (LineChart — análises criadas)
    - Tabela de usuários ativos com last_login
    - Gráfico de métodos mais usados (PieChart)
  - Rota `/admin` (requer role admin)

- Testes: 8 (backend) + component tests (frontend)

**Dependência:** PR-28 (admin endpoints), PR-29 (métricas)

---

### PR-34 — Internacionalização (i18n) — Português + Inglês

**Prioridade:** Baixa | **Esforço:** 8h
**Objetivo:** Preparar o produto para mercado internacional (portos de outros países).

**Entregas:**

- **Frontend:**
  - `react-i18next` + namespace por módulo
  - `locales/pt-BR/`, `locales/en-US/` com JSON de traduções
  - Hook `useTranslation()` em todos os componentes
  - Seletor de idioma no header
  - Datas e números formatados por locale (date-fns locale)

- **Backend:**
  - Header `Accept-Language` processado no middleware
  - Mensagens de erro traduzidas (dict de mensagens)
  - Relatórios DOCX/PDF com template por idioma
  - `config.py`: `default_language: str = "pt-BR"`

- Testes: 10 (frontend snapshots + backend message lookup)

**Dependência:** Nenhuma

---

### PR-35 — Modo offline / PWA + cache local

**Prioridade:** Baixa | **Esforço:** 6h
**Objetivo:** Permitir consulta de indicadores sem internet (útil para gestores em campo).

**Entregas:**

- `vite-plugin-pwa`: service worker + manifest
- Cache strategy: network-first para API, cache-first para assets
- IndexedDB para cache local de indicadores consultados recentemente
- Banner "Modo offline — dados podem estar desatualizados"
- Sync automático quando reconectar
- Testes: E2E com simulação de offline

**Dependência:** PR-34 (i18n para mensagens de offline)

---

## Sequência de execução recomendada

```
Semana 1 (Bloqueante):
  PR-27 (hotfixes: structlog + password reset + token blacklist)

Semana 2-3 (Admin + Observabilidade):
  PR-28 (tenant CRUD) ──→ PR-30 (API pública)
  PR-29 (OpenTelemetry)     │
                             └──→ PR-31 (onboarding self-service)

Semana 4-5 (Produto):
  PR-32 (export PDF/Excel) ──→ PR-33 (admin dashboard)

Futuro (quando houver demanda):
  PR-34 (i18n) → PR-35 (PWA offline)
```

**Caminho crítico para lançamento beta:** PR-27 → PR-28 → PR-30 → PR-31

Com esses 4 PRs, o produto estará pronto para receber seus primeiros clientes via self-service com segurança, documentação e gestão.

---

## Métricas alvo para o fim do Ciclo 3

| Métrica | Agora | Alvo |
|---------|-------|------|
| Testes | ~194 | ~280 |
| Endpoints API | ~25 | ~40 |
| Cobertura de código | Não medida | > 80% |
| Tempo médio de resposta (p95) | Desconhecido | < 500ms (indicadores), < 200ms (auth) |
| Uptime (staging) | Não monitorado | > 99.5% |
| Tenants ativos | 1 (demo) | 3-5 (beta) |
| Formatos de exportação | 1 (DOCX) | 3 (DOCX, PDF, XLSX) |
| Idiomas | 1 (pt-BR) | 2 (pt-BR, en-US) |
