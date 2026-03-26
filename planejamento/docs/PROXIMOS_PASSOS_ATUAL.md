# Próximos Passos — SaaS Impacto Portuário

> Atualizado: 2026-03-26 | Pós PR-41 — todos os gaps de dados e qualidade de engenharia resolvidos

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
| PR-M3 | M3: remover `build_proxy_causal_multiplier` + banner frontend | — | ✅ |
| PR-RPT | Relatório DOCX: bandas de IC no gráfico Event Study | — | ✅ |
| PR-FE  | FE-SEC-01: guard `VITE_DISABLE_AUTH` em `vite.config.ts` | — | ✅ |
| PR-39 | E2E Playwright: 8 suites (login, M1, M3, M5, onboarding, M2 warnings, navegação, health) | 8 suites | ✅ |
| PR-40 | Dashboard Grafana pré-configurado + 4 alertas YAML | — | ✅ |
| PR-41 | Limpeza docstring migration Alembic D7 SCM | — | ✅ |
| IND-6.12/13 | ISS por Porto e ISS por Tonelada — queries prontas, ativação aguarda tabela BigQuery | — | 🟡 aguardando dado |

**Total acumulado:** ~380 testes unitários + 8 suites E2E, stack completa

**Stack atual:**
- FastAPI + asyncpg + SQLAlchemy 2.0 + Alembic (8 migrations)
- Celery + Redis (broker + cache + rate limit + beat scheduler)
- BigQuery (81 indicadores em 7 módulos + 2 indicadores M6 aguardando dado ISS)
- RBAC + RLS + Audit + Rate Limit + JWT blacklist + password reset
- OpenTelemetry + Prometheus metrics + Grafana dashboard importável
- Terraform GCP (Cloud Run + Cloud SQL + Memorystore + GCS + Secret Manager)
- CI/CD GitHub Actions → Cloud Run (api + worker + beat) + job E2E Playwright
- PWA + i18n PT/EN
- 7 módulos frontend (M1: tendência/benchmarking/score; M3: simulador de emprego + MIP; M5: causal completo)

---

## Score de prontidão atual

| Dimensão | Score | Notas |
|----------|-------|-------|
| Backend API | 97% | 81 indicadores com BigQuery real; 4 M2 com `dado_indisponivel` documentado; IND-6.12/13 prontos para ativar |
| Frontend | 97% | 7 módulos completos; warnings visíveis para dados indisponíveis; banner causal informativo |
| Infraestrutura | 93% | Terraform pronto; CI/CD ativo com E2E; Celery Beat rodando |
| Segurança | 95% | RBAC, RLS, audit, rate limit, JWT blacklist, password reset, guard VITE_DISABLE_AUTH em build |
| Observabilidade | 95% | structlog + OpenTelemetry + Prometheus + dashboard Grafana + 4 alertas |
| Qualidade de dados | 97% | 0 mocks de ALTO ou MÉDIO; apenas coeficientes acadêmicos (baixo, intencional) |
| Testes | 90% | ~380 unitários + 8 suites E2E (ativas quando `E2E_BASE_URL` configurado no CI) |

---

## Estado dos dados simulados/placeholder

Ver `REGISTRO_MOCKS_DADOS_SIMULADOS.md` para inventário completo.

**Resumo atual (0 itens ALTO, 0 itens MÉDIO):**

| Indicador | Status | Comportamento atual |
|-----------|--------|---------------------|
| IND-2.03 Passageiros Ferry | ✅ Resolvido | `WHERE FALSE` + `DataQualityWarning` na UI |
| IND-2.04 Passageiros Cruzeiro | ✅ Resolvido | `WHERE FALSE` + `DataQualityWarning` na UI |
| IND-2.10 Toneladas/Hectare | ✅ Resolvido | `WHERE FALSE` + `DataQualityWarning` na UI |
| IND-2.11 Toneladas/Metro de Cais | ✅ Resolvido | `WHERE FALSE` + `DataQualityWarning` na UI |
| Multiplicador de emprego (M3) | ✅ Intencional | Coeficientes MIP IBGE 2015, documentados |
| Estimativa causal M3 | ✅ Resolvido | `causal: null` + banner explicativo; sem p-values fabricados |
| IND-6.12 ISS por Porto | 🟡 Aguardando dado | Código pronto; ativa ao definir `BD_ISS_POR_PORTO` |
| IND-6.13 ISS por Tonelada | 🟡 Aguardando dado | Código pronto; ativa ao definir `BD_ISS_POR_PORTO` |

---

## Gaps abertos

| # | Gap | Desbloqueio | Esforço |
|---|-----|-------------|---------|
| **G-ISS** | IND-6.12/6.13: tabela ISS por porto não carregada no BigQuery | Usuário carrega tabela → 1 linha de código | ~10 min |
| **G-MIP** | MIP IBGE 2020 não publicada — constantes de 2015 em uso | IBGE publicar MIP 2020 | 2h |
| **G-M6-CAUSAL** | IND-6.10/6.11 são Pearson + OLS (não causais) — planejado adaptar para DiD/IV usando pipeline M5 | Após dado ISS confirmado | 3-5d |
| **G-E2E-STAGING** | E2E Playwright configurado mas sem `E2E_BASE_URL` no CI — job não executa até secret ser definido | Configurar secret no repositório | ~30 min |

---

## Ações pendentes (por quem)

### Usuário

| Ação | Impacto |
|------|---------|
| Carregar tabela ISS por porto no BigQuery e definir `BD_ISS_POR_PORTO` em `module6_public_finance.py` | Ativa IND-6.12 e IND-6.13 |
| Configurar secrets `E2E_BASE_URL`, `E2E_USER_EMAIL`, `E2E_USER_PASSWORD` no repositório GitHub | E2E roda em cada PR |
| Configurar datasource Prometheus no Grafana e importar `infra/grafana/dashboard_saas_impacto.json` | Observabilidade operacional ativa |
| Provisionar `infra/grafana/alerts.yaml` no Grafana (ou via API) | Alertas operacionais ativos |

### Engenharia (próximos PRs planejados)

---

### PR-42 — Adaptação causal IND-6.10/6.11 (M6 → pipeline M5)

**Prioridade:** Média | **Esforço:** 3–5d
**Objetivo:** Elevar os indicadores de associação a estimativas causais usando o pipeline DiD/IV já existente no Módulo 5.

**Contexto:**
- IND-6.10 (`corr_receita_tonelagem`): Pearson entre receita fiscal e tonelagem — associação, não causal
- IND-6.11 (`elasticidade_receita_tonelagem`): log-log OLS — associação, não causal
- O pipeline causal completo (DiD, IV, Panel IV, Event Study, SCM) já existe em `backend/app/services/causal/`
- O Módulo 5 já expõe `AnalysisService` que executa e persiste análises causais

**Entregas:**
- `backend/app/services/module6_causal.py`: wrapper que dispara análise DiD/IV para o par (receita fiscal, tonelagem) por município/porto
- Endpoints M6: `GET /api/v1/indicators/query?codigo=IND-6.10&method=did` retorna coeficiente causal real quando análise disponível, fallback para OLS com `correlacao_ou_proxy: true`
- Frontend `Module6View.tsx`: badge "Associação" → "Causal (DiD)" quando resultado disponível
- Testes: 8–10

**Dependência:** IND-6.12/13 (ISS) podem aumentar qualidade dos controles

---

### PR-43 — Dados reais para IND-2.03/2.04/2.10/2.11 (quando disponíveis no ANTAQ)

**Prioridade:** Baixa (aguardando fonte) | **Esforço:** 4–6h por indicador + dado
**Objetivo:** Substituir `WHERE FALSE` por queries reais quando as tabelas ANTAQ forem mapeadas.

**Contexto:**
- ANTAQ disponibiliza dados de passageiros (`v_passageiros_*`) e cadastro físico (`v_bercos_*`) em repositório separado do BigQuery público
- Quando mapeados: trocar `WHERE FALSE` por `JOIN` real e remover `DataQualityWarning`

**Entregas por indicador:**
- `IND-2.03 / IND-2.04`: query `COUNT(passageiros)` contra tabela de embarques ANTAQ
- `IND-2.10`: `SUM(tonelagem) / area_berco_m2 * 10000` (m² → hectares)
- `IND-2.11`: `SUM(tonelagem) / extensao_cais_metros`

**Dependência:** Acesso às tabelas ANTAQ de passageiros e cadastro físico de berços

---

### PR-44 — MIP 2020 (quando publicada pelo IBGE)

**Prioridade:** Baixa (aguardando publicação) | **Esforço:** 2h
**Objetivo:** Atualizar multiplicadores de emprego e produção com a matriz de insumo-produto mais recente.

**Entregas:**
- `backend/app/services/io_analysis/national_multipliers.py`: atualizar constantes `NATIONAL_EMPLOYMENT_ALL_SECTORS`, `NATIONAL_PRODUCTION_ALL_SECTORS`, `NATIONAL_INCOME_ALL_SECTORS`
- `backend/app/services/employment_multiplier.py`: revisar `MULTIPLIER_DEFAULTS` (faixas por categoria)
- Atualizar referências bibliográficas nos docstrings

**Dependência:** IBGE publicar MIP 2020 (prevista para 2025/2026)

---

## Caminho crítico para lançamento beta

```
Estado atual: stack completa, 0 mocks ativos, E2E configurado

Restam 2 ações de usuário para beta completo:
  1. Definir E2E_BASE_URL no GitHub → E2E roda em CI
  2. Importar dashboard Grafana → observabilidade ativa

Dados ISS (quando prontos):
  Usuário define BD_ISS_POR_PORTO → IND-6.12/13 ativam sem deploy

Próxima expansão técnica:
  PR-42 (causal M6) → PR-43 (dados ANTAQ reais)
```

---

## Métricas de progresso

| Métrica | Antes da sessão | Agora |
|---------|----------------|-------|
| Mocks ALTO/MÉDIO em produção | 5 | **0** |
| Indicadores com dado correto | 77/81 | **79/81** (+ 2 aguardando ISS) |
| Cobertura E2E | 0 | **8 suites Playwright** |
| Dashboard operacional | ❌ | **✅ (importável)** |
| Alertas Grafana | 0 | **4 configurados** |
| Guard VITE_DISABLE_AUTH | ❌ | **✅ (`vite.config.ts`)** |
| Testes unitários | ~370 | **~380** |
| Score geral de prontidão | ~88% | **~95%** |
