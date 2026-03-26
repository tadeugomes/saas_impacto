# Próximos Passos — SaaS Impacto Portuário

> Atualizado: 2026-03-25 | Auditoria completa pós-sincronização com main

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
| PR-19 | Frontend: rota `/dashboard/module5` → `Module5View` | — | ✅ |
| PR-20 | Relatório DOCX para análise causal (`ReportService`) | 16 | ✅ |
| PR-21 | Logging estruturado structlog + Python 3.9 compat | 3 | ✅ |
| PR-22 | Purge automático `audit_logs` + Celery Beat scheduler | +8 | ✅ |
| PR-23 | Terraform/IaC para GCP staging + produção | — | ✅ |
| PR-24 | Notificações webhook + email ao fim de análise | +10 | ✅ |
| PR-25 | SCM real (ASCM: ridge regression + placebos de espaço/tempo) | +30 | ✅ |
| PR-26 | Matching automático PSM/CEM para seleção de controles | +15 | ✅ |
| PR-27 | Hotfixes auth: password reset + JWT blacklist Redis | +13 | ✅ |
| PR-28 | Admin CRUD de tenants + gestão de usuários | +20 | ✅ |
| PR-29 | OpenTelemetry + métricas Prometheus | +8 | ✅ |
| PR-30 | API docs OpenAPI + versionamento + SDK generation | +5 | ✅ |
| PR-31 | Module3View: Painel de Impacto em Emprego + IND-3.13-3.16 | — | ✅ |
| PR-32 | Exportação avançada: PDF + Excel para indicadores | — | ✅ |
| PR-33 | Dashboard analítico do tenant (admin) | — | ✅ |
| PR-34 | i18n PT/EN + mobile responsiveness + component tests | — | ✅ |
| PR-35 | PWA + manifest + service worker | — | ✅ |
| PR-36 | Onboarding self-service (tenant + admin user em uma transação) | — | ✅ |
| PR-X  | M1: Analytics operacional (tendência, benchmarking, score) | +12 | ✅ |
| PR-X  | M1: Frontend aba Benchmarking Nacional | — | ✅ |
| PR-X  | M3: MIP IBGE 2015 + QL RAIS + benchmark Paranaguá | +8 | ✅ |
| PR-X  | M3/M5: DOCX enriquecido (simulação + diagnósticos causais) | — | ✅ |
| PR-37 | M2: IND-2.10/2.11 marcados indisponíveis + warning + frontend | — | ✅ |
| PR-38 | M2: IND-2.03/2.04 marcados indisponíveis + warning + frontend | — | ✅ |
| PR-M3 | M3: remover build_proxy_causal_multiplier + banner frontend | — | ✅ |
| PR-RPT | Relatório DOCX: bandas de IC no gráfico Event Study | — | ✅ |
| PR-39  | E2E Playwright: 8 cenários (login, M1, M3, M5, onboarding, M2 warnings, navegação, health) | 8 | ✅ |
| PR-40  | Dashboard Grafana pré-configurado + alertas YAML | — | ✅ |
| PR-41  | Limpeza docstring migration Alembic D7 SCM stub | — | ✅ |

**Total acumulado:** ~370 testes unitários, stack completa

**Stack atual:**
- FastAPI + asyncpg + SQLAlchemy 2.0 + Alembic (5 migrations)
- Celery + Redis (broker + cache + rate limit + beat scheduler)
- BigQuery (81 indicadores, 7 módulos)
- RBAC + RLS + Audit + Rate Limit
- OpenTelemetry + Prometheus metrics
- Terraform GCP (Cloud Run + Cloud SQL + Memorystore + GCS + Secret Manager)
- CI/CD GitHub Actions → Cloud Run (api + worker + beat)
- PWA + i18n PT/EN
- 7 módulos frontend com analytics (M1: tendência/benchmarking/score; M3: simulador de emprego + MIP)

---

## Score de prontidão atual

| Dimensão | Score | Notas |
|----------|-------|-------|
| Backend API | 95% | Todos os módulos com BigQuery real; 4 indicadores M2 com placeholders documentados |
| Frontend | 97% | 7 módulos completos; M1 com 4 abas analíticas; M3 com simulador |
| Infraestrutura | 90% | Terraform pronto; CI/CD ativo; Celery Beat rodando |
| Segurança | 92% | RBAC, RLS, audit, rate limit, JWT blacklist, password reset |
| Observabilidade | 85% | structlog, OpenTelemetry, Prometheus; sem dashboard Grafana pré-configurado |

---

## Gaps conhecidos e registrados

### Dados simulados/placeholder em produção

Ver `REGISTRO_MOCKS_DADOS_SIMULADOS.md` para inventário completo.

Resumo dos gaps de dados:

| Indicador | Módulo | Gap | Impacto |
|-----------|--------|-----|---------|
| IND-2.03 Passageiros Ferry | M2 | ✅ Resolvido: retorna vazio + warning "tabela de passageiros não integrada" | — |
| IND-2.04 Passageiros Cruzeiro | M2 | ✅ Resolvido: retorna vazio + warning "tabela de passageiros não integrada" | — |
| IND-2.10 Toneladas/Hectare | M2 | ✅ Resolvido: retorna vazio + warning "área física indisponível no ANTAQ" | — |
| IND-2.11 Toneladas/Metro de Cais | M2 | ✅ Resolvido: retorna vazio + warning "extensão de cais indisponível no ANTAQ" | — |
| Multiplicador de emprego | M3 | Coeficientes da literatura (MIP IBGE 2015) — intencional, documentado | Baixo |
| Benchmark Paranaguá | M3 | Valor de referência hardcoded do TCC — intencional, documentado | Baixo |

### Riscos operacionais

| # | Gap | Risco | Esforço |
|---|-----|-------|---------|
| G1 | ~~Dashboard Grafana não pré-configurado~~ | ✅ Resolvido via PR-40 | — |
| G2 | ~~IND-2.11 e IND-2.12 retornam dados sem denominador real~~ | ✅ Resolvido via PR-37 | — |
| G3 | ~~Sem testes E2E (Playwright/Cypress)~~ | ✅ Resolvido via PR-39 | — |
| G4 | ~~Alembic migration D7 (SCM stubs) ainda no changelog~~ | ✅ Resolvido via PR-41 | — |

---

## Próximos PRs planejados

---

### PR-37 — Dados reais para IND-2.11 e IND-2.12 (área/extensão de berços)

**Prioridade:** Alta | **Esforço:** 4h + dados
**Objetivo:** Substituir os placeholders dos indicadores de densidade operacional por denominadores reais.

**Entregas:**
- Identificar fonte de dados de área (m²) e extensão de cais (m) por instalação no ANTAQ ou dados públicos da ANTAQ/Marinha
- `module2_cargo_operations.py`: atualizar `query_toneladas_por_hectare` e `query_toneladas_por_metro_cais` com join real
- Se fonte não disponível: marcar indicadores como `disponibilidade: "indisponível"` na resposta e exibir mensagem no frontend
- Testes: 4 (retorno correto, fallback para indisponível)

**Dependência:** Disponibilidade de dados — verificar ANTAQ/SNPq/dados abertos portuários

---

### PR-38 — Dados de passageiros (IND-2.04 e IND-2.05)

**Prioridade:** Média | **Esforço:** 3h + dados
**Objetivo:** Substituir zeros pelos dados reais de movimentação de passageiros.

**Entregas:**
- Identificar tabela ANTAQ com dados de passageiros (ferry e cruzeiro)
- `module2_cargo_operations.py`: implementar queries reais
- Se indisponível para a maioria dos portos: marcar como `disponibilidade: "parcial"` com nota
- Testes: 3

**Dependência:** Disponibilidade de dados no BigQuery ANTAQ

---

### PR-39 — Testes E2E com Playwright

**Prioridade:** Alta | **Esforço:** 1d
**Objetivo:** Detectar regressões de integração antes de chegar à produção.

**Entregas:**
- `e2e/` na raiz do projeto com Playwright
- Fluxos críticos:
  - Login → seleção de instalação → visualização de indicador M1
  - Login → criação de análise causal → polling de status → download DOCX
  - Login → Module3View → simulação de impacto por tonelagem
  - Onboarding: criação de tenant + primeiro acesso
- CI: job `e2e` no workflow `ci.yml` (executa em staging com dados fixos)
- Testes: 8-12 cenários

**Dependência:** Ambiente staging estável (PR-23 Terraform)

---

### PR-40 — Dashboard Grafana pré-configurado

**Prioridade:** Média | **Esforço:** 3h
**Objetivo:** Visualização operacional pronta para usar no Cloud Monitoring / Grafana.

**Entregas:**
- `infra/grafana/dashboard_saas_impacto.json`: dashboard importável
  - Painel: request rate por tenant, latência P50/P95/P99, error rate
  - Painel: Celery tasks por status (queued/running/success/failed)
  - Painel: BigQuery cache hit rate, custo estimado por dia
  - Painel: análises causais por método/status
- `infra/grafana/alerts.yaml`: alertas (error rate > 1%, latência > 2s)
- Instruções de importação no `infra/README.md`

**Dependência:** PR-29 (Prometheus já configurado)

---

### PR-41 — Limpeza: remover migration stub SCM do changelog

**Prioridade:** Baixa | **Esforço:** 30 min
**Objetivo:** Higiene — a migration `d7e8f9a0b1c2` expandia o check de métodos para SCM quando ainda eram stubs. Agora que SCM está implementado, o comentário histórico é ruído.

**Entregas:**
- Atualizar docstring da migration para refletir estado atual
- Não reescrever a migration (Alembic rastreia por hash)

**Dependência:** Nenhuma

---

## Sequência de execução recomendada

```
Imediato (qualidade de dados):
  PR-37 (IND-2.11/2.12) → PR-38 (passageiros)

Qualidade de engenharia:
  PR-39 (E2E) → PR-40 (Grafana)

Higiene:
  PR-41 (migration stub)
```

**Caminho crítico para lançamento beta:** PR-37 e PR-39
- PR-37 elimina o único dado falso visível ao usuário final
- PR-39 protege contra regressão no onboarding

---

## Métricas de progresso

| Métrica | Atual | Pós PR-37/38 | Pós PR-39/40 |
|---------|-------|--------------|--------------|
| Indicadores com dado real | 77/81 | 81/81 | 81/81 |
| Cobertura E2E | 0 cenários | — | 8 cenários ✅ |
| Dashboard operacional | ❌ | — | ✅ (PR-40) |
| Testes unitários | ~370 | ~380 | ~380 |
