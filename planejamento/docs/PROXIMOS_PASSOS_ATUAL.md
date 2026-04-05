# Próximos Passos — SaaS Impacto Portuário

> Atualizado: 2026-04-05 | Estado real auditado após PRs 01-33 + módulos extras implementados.

---

## Inventário completo de PRs/features concluídos

| PR/Feature | Escopo | Testes | Status |
|------------|--------|--------|--------|
| PR-01 | Módulo 5 — alinhamento 21 indicadores | — | ✅ |
| PR-02 | Engine causal (DiD, IV, Panel IV, prep, comparison, serialize) | 30 | ✅ |
| PR-03 | Panel Builder BigQuery → DataFrame + ingestão | 28 | ✅ |
| PR-04 | Persistência (EconomicImpactAnalysis + Alembic + RLS) | — | ✅ |
| PR-05 | API endpoints (schemas, AnalysisService, router) | 32 | ✅ |
| PR-06 | Celery worker assíncrono + docker-compose | 56 | ✅ |
| PR-07 | Interface SCM/ASCM + feature flag | 42 | ✅ |
| PR-08 | Event Study real (TWFE + Sun & Abraham) | +30 | ✅ |
| PR-09 | Cache Redis para queries BigQuery | +20 | ✅ |
| PR-10 | Relatório DOCX (ReportService + DOCXGenerator) | +12 | ✅ |
| PR-11 | Health checks reais + request timing middleware | +10 | ✅ |
| PR-12 | Rate limiting Redis (sliding window) | +18 | ✅ |
| PR-13 | RBAC granular (permissions, decorators, endpoints) | +35 | ✅ |
| PR-14 | Audit log (tabela, AuditMiddleware, AuditService) | +22 | ✅ |
| PR-18 | CI/CD GitHub Actions (lint, test, build, deploy GCP) | — | ✅ |
| PR-19 | Frontend: rota `/dashboard/module5` → Module5View | — | ✅ |
| PR-20 | Relatório DOCX para análise causal | 16 | ✅ |
| PR-21 | Logging estruturado structlog + compat. Python 3.9 | 3 | ✅ |
| PR-22 | Purge automático de audit_logs (Celery beat) | 5 | ✅ |
| PR-23 | Terraform/IaC para GCP (staging + prod) | — | ✅ |
| PR-24 | Notificações webhook/email ao fim de análise | 10 | ✅ |
| PR-25 | SCM real (synthetic_control.py, placebos) | 25 | ✅ |
| PR-26 | Matching automático de controles (PSM/CEM) | 15 | ✅ |
| PR-27 | Hotfixes: password reset, JWT blacklist, structlog | 8 | ✅ |
| PR-28 | Admin CRUD tenants/usuários | — | ✅ |
| PR-29 | OpenTelemetry + Prometheus | — | ✅ |
| PR-30 | API pública + OpenAPI | — | ✅ |
| PR-31 | Module3View: Painel de Impacto em Emprego | — | ✅ |
| PR-32 | Export PDF + Excel (PDFGenerator, XLSXGenerator) | — | ✅ |
| PR-33 | Admin dashboard (AdminDashboard.tsx) | — | ✅ |
| Módulo 8 | Contexto Macro (BACEN, IBGE) + Module8View | — | ✅ |
| Módulo 9 | Risco Ambiental (ANA, INPE) + Module9View | — | ✅ |
| Módulo 10 | Compliance Portuário (TCU, PNCP, Querido Diário) + Module10View | — | ✅ |
| Módulo 11 | Forecasting SARIMAX + cenários + Module11View | — | ✅ |
| i18n | pt-BR + en-US (I18nContext, translations.ts) | — | ✅ |
| Self-service | Onboarding/registro (RegisterView, onboarding_service) | — | ✅ |
| APIs públicas | 12 clientes: BACEN, IBGE, ANA, INPE, CONAB, DATAJUD, INMET, MARES, NOAA, TCE, Transparência + sync periódico | — | ✅ |
| Simulador M5 | Endpoint `/analises/{id}/simulacao` (modo movimentação) | — | ✅ |

**Total:** ~350+ testes unitários passando, 0 falhas

**Stack em produção:**
- FastAPI + asyncpg + SQLAlchemy 2.0 + Alembic
- Celery + Redis (broker + cache + rate limit + beat)
- BigQuery (81 indicadores, 11 módulos)
- RBAC + RLS + Audit + Rate Limit + OpenTelemetry
- CI/CD → Cloud Run (api + worker + beat)
- Terraform/IaC staging + prod

---

## Pendências ativas

### Sprint 2 — Módulo 5: Robustez do Simulador

| Item | Status | Bloqueador |
|------|--------|-----------|
| Migrar exportações DOCX → Excel (unificar em XLSX) | 🔄 Em andamento | — |
| Fallback amigável para `artifact_path` ausente | ✅ Implementado no router | — |
| Card "Resumo para Gestor" + Painel de Risco | 🔄 Em andamento | — |
| Documentar limitação modo investimento na UI | 🔄 Em andamento | — |
| Exportação da simulação para Excel (M5-305) | ⏳ Pendente | — |

### Sprint 3 — UX Executiva (Módulo 5)

| Item | Descrição |
|------|-----------|
| Card "Resumo para Gestor" | Topo do simulador com mensagem executiva principal |
| Painel de Risco | Distribuição forte/moderada/fraca com linguagem de negócio |
| Alertas de premissa | Mensagens visíveis para premissas críticas da simulação |

### Infraestrutura e qualidade

| Item | Prioridade | Esforço |
|------|-----------|---------|
| Cobertura de testes no CI (coverage.py ≥ 80%) | Alta | 2h |
| Script `check_module3_real_access.py` (validação RAIS/ANTAQ) | Média | 1h |
| Drift detection / MAPE tracking no SARIMAX | Alta | Médio |
| Health endpoint unificado para clientes de API pública | Média | Baixo |

---

## Limitações documentadas (sem implementação por ausência de dados)

### Modo Investimento do Simulador (M5-E1)

O simulador opera apenas no modo **choque de movimentação** (`shock_mode: movement`).

O modo investimento (`shock_mode: investment`) requer uma base de dados histórica de **investimentos portuários por município/ano** para estimar o modelo de Estágio 1:

```
Δln(toneladas) ~ Δln(investimento)   [estimação FE municipal]
```

Essa base não existe em fontes públicas estruturadas (ANTAQ, SEP/MT, PAC). Até sua disponibilização:
- A UI exibe nota explicativa sobre a limitação
- O usuário pode informar manualmente a elasticidade como aproximação
- Resultados no modo investimento têm incerteza substancialmente maior

### Módulo de Impostos (Carga Tributária Portuária)

Análise de carga tributária portuária por município requer dados da Receita Federal desagregados por setor/município em série histórica. Esses dados não estão disponíveis via API pública estruturada.

A feature fica documentada como limitação permanente até integração com fontes privadas ou publicação oficial.

### Matriz I-O Regional (Módulo 3 — Leontief Regionalizado)

Multiplicadores de Leontief com regionalização estadual/municipal requerem a Matriz de Insumo-Produto regional do IBGE, publicada apenas para anos de Censo (última: 2015). A análise de emprego usa multiplicadores nacionais como aproximação.

---

## Baixa prioridade (roadmap futuro)

- PR-34: Refatorar i18n para `react-i18next` com namespaces (infraestrutura custom já funciona)
- PR-35: PWA offline com IndexedDB (service worker + vite-plugin-pwa)
- Módulo 10 avançado: Compliance/TCU expandido com scoring automático
- Testes E2E frontend (Playwright ponta-a-ponta para fluxo de simulação)
