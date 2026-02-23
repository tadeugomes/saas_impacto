# Backlog de Implementação — Módulo 3 (Impacto em Emprego)

**Meta:** consolidar o Módulo 3 para responder perguntas de impacto econômico com base em RAIS + ANTAQ reais.

**Data:** 22/02/2026

---

## PR-28 — Contrato de API para Impacto de Emprego (M3)

**Prioridade:** P0  
**Objetivo:** expor resposta explícita de impacto (não só “métricas descritivas de RH”).

### User Stories

- **M3-US-28.01**  
  Como analista, quero que o endpoint de impacto de emprego (`/employment/multipliers/{id_municipio}`) retorne:
  `empregos_diretos`, `empregos_totais`, `participacao_emprego_local`, `empregos_por_milhao_toneladas`, `empregos_indiretos_estimados`, `empregos_induzidos_estimados`, `emprego_total_estimado`, `metodologia`, `indicador_de_confianca`.
  - **ACEITE:** resposta HTTP 200 com `data` estruturado para municipio válido; para período sem dados, `data=[]`.

- **M3-US-28.02**  
  Como frontend, quero receber metadados de interpretação (descrição + limitação causal).
  - **ACEITE:** metadado `correlacao_ou_proxy=true` e `metodo` explícito.

### Implementação

- `backend/app/schemas/employment_multiplier.py`:
  - adicionar campos derivados de impacto no schema de retorno.
- `backend/app/services/employment_multiplier.py`:
  - incluir método de composição de retorno com `emprego_total_estimado`.
- `backend/app/api/v1/employment.py`:
  - substituir placeholder por chamada do `EmploymentMultiplierService`.
- `backend/app/tests/test_employment_multiplier.py`:
  - ajustar e ampliar cenários para campos de impacto.

---

## PR-29 — Pipeline de indicadores de base Módulo 3 (RAIS + ANTAQ)

**Prioridade:** P0  
**Objetivo:** substituir cálculos não validados por consultas reais e rastreáveis.

### User Stories

- **M3-US-29.01**  
  Como serviço, quero calcular `empregos_diretos_portuarios` por `id_municipio`/`ano` via RAIS real.
- **M3-US-29.02**  
  Como serviço, quero calcular `empregos_totais` municipais via RAIS real.
- **M3-US-29.03**  
  Como serviço, quero calcular `tonelagem` municipal via ANTAQ real para ligar com produtividade/choques.

### Aceite

- A consulta de testes com município real não pode retornar `Query inválida` para 2015+.
- Divergência estrutural deve cair em `warning` com detalhe e não quebrar o fluxo.
- Valores vazios resultam em `data=[]` (sem 500).

### Implementação

- `backend/app/db/bigquery/queries/module3_human_resources.py`:
  - manter/ajustar `query_produtividade_ton_empregado` com join robusto ANTAQ.
- `scripts/check_module3_real_access.py`:
  - incluir no runbook de validação e registrar taxa de sucesso por consulta.

---

## PR-30 — Impacto por tonelada e cenários de choque

**Prioridade:** P1  
**Objetivo:** responder “quanto o emprego responde a variação de carga”.

### User Stories

- **M3-US-30.01**  
  Como analista, quero `empregos_por_milhao_toneladas` para comparar eficiência entre municípios.
- **M3-US-30.02**  
  Como analista, quero simular choque de carga (`delta_tonelagem_pct`) e retornar `delta_empregos`.
- **M3-US-30.03**  
  Como dashboard, quero exibir se o resultado é linear por hipótese simplificada e o intervalo de validade.

### Implementação

- `backend/app/services/employment_multiplier.py`:
  - adicionar cálculo de choque:
    - `delta_empregos = empregos_diretos * elasticidade_estimada * (delta_tonelagem_pct / 100)`
  - incluir `scenario` na resposta.
- `backend/app/api/v1/employment.py`:
  - adicionar query param opcional `delta_tonelagem_pct`.
- `backend/app/tests/test_employment_multiplier.py`:
  - testes de cenário e limites de sinal/entrada.

---

## PR-31 — Frontend Módulo 3 com linguagem de impacto

**Prioridade:** P1  
**Objetivo:** substituir leitura operacional por painel de impacto com interpretação.

### User Stories

- **M3-US-31.01**  
  Como usuário, quero ver cards:
  - Emprego local total associado ao porto
  - Emprego por 1.000 t
  - Cenário de choque (`+10%`) com ganho/perda estimada
- **M3-US-31.02**  
  Como usuário, quero ver indicação `não causal` quando for proxy literário.
- **M3-US-31.03**  
  Como usuário, quero comparar municípios por retorno por tonelada.

### Implementação

- `frontend/src/views/Dashboard/ModuleViews/Module3View.tsx`:
  - incluir painel de impacto e cards por indicadores novos.
- `frontend/src/api/employmentMultiplier.ts`:
  - refletir novos campos de retorno/entrada de cenário.
- `frontend/src/types/api.ts`:
  - tipagem de payload atualizada.

---

## PR-32 — Qualidade/Observabilidade para indicadores de impacto

**Prioridade:** P1  
**Objetivo:** garantir confiança mínima e rastreabilidade.

### User Stories

- **M3-US-32.01**  
  Como operador, quero warnings estruturados para dados negativos/ausentes/atípicos.
- **M3-US-32.02**  
  Como operação, quero executar `scripts/check_module3_real_access.py` no pipeline de validação semanal.

### Implementação

- Reusar `DataQualityWarning` em `GenericIndicatorService` para casos de proxy.
- Registrar no log quando `data=[]` por ausência de cobertura anual.
- `backend/app/tests`:
  - testes de warning para valores negativos e `n_obs` baixo.

---

## Ordem recomendada

1. PR-28 (contrato de API)  
2. PR-29 (queries reais de base)  
3. PR-30 (cenários de choque)  
4. PR-31 (frontend explicativo)  
5. PR-32 (qualidade e runbook de validação)

---

## Entregáveis mínimos de pronto para negócio

- endpoint `/employment/multipliers/{id_municipio}` com:
  - impacto mensal/anuais derivados,
  - resposta estruturada de empregos diretos/indiretos/induzidos e custo de tonelagem,
  - mensagem de método/proxy explicitamente não causal.
- dashboard Módulo 3 mostrando impacto em português de negócio.
- validação real com RAIS/ANTAQ passando no `scripts/check_module3_real_access.py`.

