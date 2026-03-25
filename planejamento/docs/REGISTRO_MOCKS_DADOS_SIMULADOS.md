# Registro Oficial — Mocks, Dados Simulados e Placeholders

> Criado: 2026-03-25 | Auditoria completa do código de produção
>
> **Escopo:** Apenas código de produção (`backend/app/` excluindo `tests/`, `frontend/src/` excluindo `*.test.*`).
> Dados de testes unitários (mocks em `unittest.mock`, `_FakeRedis`, `_DummyBigQueryClient`) são esperados e não estão listados aqui.

---

## Sumário

| Severidade | Quantidade | Descrição |
|-----------|-----------|-----------|
| 🔴 ALTO | 3 | Indicadores com dado incorreto (denominador errado) OU bypass de segurança em produção |
| 🟡 MÉDIO | 3 | Indicadores zero explícito + estimativa causal sintética com p-values fabricados |
| 🟢 BAIXO | 4 | Coeficientes acadêmicos hardcoded + fallback de gráfico em DOCX |

---

## 🔴 ALTA SEVERIDADE — Dado incorreto exibido ao usuário

### M2-PH-01 — IND-2.11: Toneladas por Hectare

| Campo | Valor |
|-------|-------|
| **Arquivo** | `backend/app/db/bigquery/queries/module2_cargo_operations.py` |
| **Linha** | 416–456 (função `query_toneladas_por_hectare`) |
| **Indicador** | IND-2.11 — Densidade Operacional por Área |
| **Comportamento real** | Retorna `tonelagem_total / 1` (denominador = 1 hectare) — equivale a retornar a tonelagem bruta sem normalização |
| **Comportamento esperado** | `SUM(tonelagem) / area_berco_hectares` por instalação |
| **Causa** | Dados de área dos berços (m²) não disponíveis nas tabelas ANTAQ do BigQuery |
| **Impacto** | Usuário vê valores na ordem de milhões de ton/ha, sem comparabilidade entre portos |
| **Workaround atual** | Nenhum — indicador está ativo na UI |
| **PR de correção** | PR-37 |

```python
# Linha 429 — comentário no código
"""Retorna tonelagem total como placeholder."""
```

---

### M2-PH-02 — IND-2.12: Toneladas por Metro de Cais

| Campo | Valor |
|-------|-------|
| **Arquivo** | `backend/app/db/bigquery/queries/module2_cargo_operations.py` |
| **Linha** | 460–500 (função `query_toneladas_por_metro_cais`) |
| **Indicador** | IND-2.12 — Densidade Operacional por Extensão de Cais |
| **Comportamento real** | Retorna `tonelagem_total / 1` (denominador = 1 metro) |
| **Comportamento esperado** | `SUM(tonelagem) / extensao_cais_metros` por instalação |
| **Causa** | Dados de extensão de cais (m) não disponíveis nas tabelas ANTAQ |
| **Impacto** | Mesmo problema do IND-2.11 — valor sem sentido físico |
| **Workaround atual** | Nenhum — indicador está ativo na UI |
| **PR de correção** | PR-37 |

```python
# Linha 473 — comentário no código
"""Retorna tonelagem total como placeholder."""
```

---

### FE-SEC-01 — Flag `VITE_DISABLE_AUTH`: bypass completo de autenticação JWT

| Campo | Valor |
|-------|-------|
| **Arquivo** | `frontend/src/api/client.ts` |
| **Linha** | 10 (`this.disableAuth = import.meta.env.VITE_DISABLE_AUTH === 'true'`) |
| **Componente** | `ApiClient` — interceptor de request |
| **Comportamento real** | Quando `VITE_DISABLE_AUTH=true`, o token JWT nunca é adicionado ao cabeçalho `Authorization`. O interceptor de resposta também ignora erros 401 sem tentar refresh. |
| **Comportamento esperado** | Autenticação sempre ativa em qualquer ambiente não-dev |
| **Causa** | Flag de desenvolvimento para facilitar testes sem backend de auth |
| **Impacto** | Se o build de produção for feito com `VITE_DISABLE_AUTH=true`, todos os usuários acessam como anônimos — todos os endpoints protegidos ficam acessíveis sem token |
| **Risco** | CRÍTICO em produção; aceitável apenas em ambiente local de dev |
| **Workaround atual** | Depende de variável de ambiente não ser definida em produção — sem proteção por código |
| **Ação recomendada** | Adicionar guard no `vite.config.ts` ou CI que falhe o build de produção se `VITE_DISABLE_AUTH=true` |

---

## 🟡 MÉDIA SEVERIDADE — Dado zero explícito (fonte indisponível)

### M2-PH-03 — IND-2.04: Passageiros Ferry

| Campo | Valor |
|-------|-------|
| **Arquivo** | `backend/app/db/bigquery/queries/module2_cargo_operations.py` |
| **Linha** | 110–132 (função `query_passageiros_ferry`) |
| **Indicador** | IND-2.04 — Movimentação de Passageiros Ferry |
| **Comportamento real** | Retorna `passageiros = 0` para qualquer consulta |
| **Comportamento esperado** | `COUNT(passageiros)` ou `SUM(volume_passageiros)` de tabela ANTAQ específica |
| **Causa** | Dados de passageiros ferry não existem na view `v_carga_metodologia_oficial`; requerem tabela separada não mapeada |
| **Impacto** | Gráfico sempre zerado — usuário pode interpretar como dado real (zero passageiros) |
| **Workaround atual** | Comentário no código; sem indicação visual na UI |
| **PR de correção** | PR-38 |

```python
# Linha 120 — comentário no código
"""Retorna 0 como placeholder - requer dados específicos de passageiros."""
```

---

### M2-PH-04 — IND-2.05: Passageiros Cruzeiro

| Campo | Valor |
|-------|-------|
| **Arquivo** | `backend/app/db/bigquery/queries/module2_cargo_operations.py` |
| **Linha** | 133–155 (função `query_passageiros_cruzeiro`) |
| **Indicador** | IND-2.05 — Movimentação de Passageiros Cruzeiro |
| **Comportamento real** | Retorna `passageiros = 0` para qualquer consulta |
| **Comportamento esperado** | Dado de temporada de cruzeiros (out–mar) por instalação |
| **Causa** | Mesma causa do IND-2.04 |
| **Impacto** | Idem — zero pode ser confundido com dado real em portos sem cruzeiros |
| **Workaround atual** | Comentário no código |
| **PR de correção** | PR-38 |

---

### M3-PH-05 — Estimativa causal sintética (`build_proxy_causal_multiplier`)

| Campo | Valor |
|-------|-------|
| **Arquivo** | `backend/app/services/employment_multiplier.py` |
| **Linhas** | 402–450 (método estático `build_proxy_causal_multiplier`) |
| **Indicador** | Módulo 3 — multiplicador de emprego com `use_causal=true` |
| **Comportamento real** | Gera `p_value`, `std_error`, `n_obs` e `method` sintéticos a partir de regras determinísticas sobre `direct_jobs` e sinais locais. P-values são sempre 0.045, 0.08 ou 0.10 dependendo de condições. `n_obs = max(24, min(240, direct_jobs / 20))`. Método declarado como `"panel_iv"` ou `"iv_2sls"`. |
| **Comportamento esperado** | Resultado de estimação econométrica real (DiD, IV, Panel IV) via pipeline causal do Módulo 5 |
| **Causa** | Pipeline causal completo (Módulo 5) não integrado ao Módulo 3; este helper foi criado como ponte temporária para habilitar o endpoint `use_causal=true` |
| **Impacto** | Usuário que solicita `use_causal=true` recebe coeficiente com aparência de estimativa causal (p-value, CIs, método), mas todos os valores de significância são fabricados. A resposta inclui aviso `correlacao_ou_proxy: true`, mas o campo `method: "panel_iv"` é enganoso. |
| **Workaround atual** | Campo `correlacao_ou_proxy: true` na resposta; docstring explica a natureza temporária |
| **Ação recomendada** | Remover `build_proxy_causal_multiplier` após integração real do pipeline causal M5 → M3. Até lá, considerar retornar apenas `literature` sem simular `p_value`/`n_obs`. |

---

## 🟢 BAIXA SEVERIDADE — Coeficientes acadêmicos hardcoded (intencional)

### M3-LIT-01 — Multiplicadores de Emprego (MIP IBGE 2015)

| Campo | Valor |
|-------|-------|
| **Arquivo** | `backend/app/services/io_analysis/national_multipliers.py` |
| **Linhas** | 80–150 (constantes `NATIONAL_EMPLOYMENT_ALL_SECTORS`, `NATIONAL_PRODUCTION_ALL_SECTORS`, `NATIONAL_INCOME_ALL_SECTORS`) |
| **Componente** | Multiplicadores nacionais do setor "Transp" (MIP IBGE 2015, 12 setores) |
| **Fonte** | Vale & Perobelli (2020), *Análise de Insumo-Produto no R*, tabelas de multiplicadores |
| **Comportamento** | Valores hardcoded de ME=17.07, MEI=1.83, MEII=3.43, MP=1.84, MR=0.44, etc. |
| **Justificativa** | Dados da MIP nacional são publicados e estáveis — não mudam a cada consulta. Atualizar requer nova edição do IBGE (último: MIP 2015, próximo previsto: MIP 2020) |
| **Ajuste regional** | QL (Quociente Locacional) calculado dinamicamente via RAIS no BigQuery |
| **Documentação** | 6 referências acadêmicas no docstring do módulo |
| **Impacto** | Baixo — limitação metodológica documentada na UI com flag `correlacao_ou_proxy: true` |

---

### M3-LIT-02 — Multiplicador de Emprego por Literatura (MULTIPLIER_DEFAULTS)

| Campo | Valor |
|-------|-------|
| **Arquivo** | `backend/app/services/employment_multiplier.py` |
| **Linhas** | 111–155 (dicionário `MULTIPLIER_DEFAULTS`) |
| **Componente** | Faixas de multiplicadores para categorias: standard (2.5–4.5×), indirect_only (1.4–2.3×), specialized (3.43–6.0×) |
| **Fonte** | MEII da MIP IBGE 2015 via Vale & Perobelli (2020); faixa "specialized" referencia o TCC Paranaguá |
| **Comportamento** | Retornados como campo `literature` na resposta do endpoint `/employment/multipliers/{id_municipio}` com metadado `source` explícito |
| **Justificativa** | Multiplicadores literários são a proxy padrão antes de estimativa causal por IV/DiD |
| **Impacto** | Baixo — claramente identificados na UI como "Multiplicador da literatura" com range e fonte |

---

### M3-LIT-03 — Benchmark de Referência Paranaguá (TCC)

| Campo | Valor |
|-------|-------|
| **Arquivo** | `backend/app/services/employment_multiplier.py` |
| **Linhas** | 107–155 (categoria `"paranagua_specialized"` em `MULTIPLIER_DEFAULTS`) |
| **Componente** | Multiplicador upper-bound: coefficient=4.46, range=[3.43, 6.0] |
| **Fonte** | Wozniak & Andrade Junior (2023), TCC — MIP regional Paranaguá (52 setores, balanceamento RAS) |
| **Comportamento** | Usado como teto de referência para portos especializados em granéis/contêineres |
| **Justificativa** | TCC com MIP regional completa (não disponível como dado aberto) — usado apenas como referência interpretativa |
| **Impacto** | Baixo — não afeta cálculos por padrão; aparece apenas se `multiplier_type="paranagua_specialized"` for solicitado |

---

### RPT-PH-01 — Placeholder de gráfico em relatório DOCX

| Campo | Valor |
|-------|-------|
| **Arquivos** | `backend/app/reports/docx_generator.py` (linhas 154–173) e `backend/app/reports/report_service.py` (linha 1358) |
| **Componente** | `DOCXGenerator.add_chart_placeholder()` — fallback de renderização |
| **Comportamento real** | Quando `chart_bytes` é `None` ou a inserção de imagem falha, o DOCX recebe um parágrafo com texto `[Gráfico: <título>]` em itálico cinza com borda. Não há gráfico real. |
| **Comportamento esperado** | Gráfico de Event Study renderizado como imagem PNG/SVG no documento |
| **Causa** | Geração de gráfico (matplotlib/plotly) como bytes não está implementada no path de geração de relatório; `chart_bytes` chega como `None` |
| **Impacto** | Relatório DOCX gerado para análises com Event Study mostra placeholder de texto no lugar do gráfico. Dado numérico (coeficientes, tabelas) está correto — apenas a visualização é ausente. |
| **Workaround atual** | Texto deixa claro que é um placeholder; não é dado falso |
| **Impacto** | Baixo — afeta apenas apresentação do relatório, não os dados |

---

## Dados hardcoded que NÃO são problema

Os seguintes hardcodings são esperados e corretos:

| Local | Dado | Justificativa |
|-------|------|---------------|
| `module3_human_resources.py` | Lista de 24 CNAEs portuários | Classificação oficial IBGE/ANTAQ — estável |
| `employment_multiplier.py` | `PORT_TO_IBGE_MAPPING` | Mapeamento porto→município oficial da ANTAQ |
| Todos os módulos | Nomes de tabelas BigQuery (`antaqdados.*`, `basedosdados.*`) | Paths de dados públicos — só mudam se ANTAQ renomear |
| `config.py` | Valores default de configuração | Padrões documentados, sobrescritos por `.env` em produção |
| `national_multipliers.py` | Coeficientes MIP IBGE 2015 | Dados acadêmicos publicados — ver M3-LIT-01 acima |

---

## Checklist de resolução

- [ ] **PR-37**: Implementar IND-2.11 e IND-2.12 com dado real ou marcar como `disponibilidade: "indisponível"` na resposta + mensagem na UI
- [ ] **PR-38**: Implementar IND-2.04 e IND-2.05 com dado real ou marcar como `disponibilidade: "indisponível"`
- [ ] **FE-SEC-01**: Adicionar guard de build que proíbe `VITE_DISABLE_AUTH=true` em `NODE_ENV=production` (vite.config.ts ou step de CI)
- [ ] **M3-PH-05**: Após integração do pipeline causal M5→M3, remover `build_proxy_causal_multiplier` e usar resultado real
- [ ] **RPT-PH-01**: Implementar geração de gráfico como bytes (matplotlib) no `report_service.py` para substituir o placeholder de Event Study
- [ ] **Atualização futura**: quando IBGE publicar MIP 2020, atualizar constantes em `national_multipliers.py` e `employment_multiplier.py`

---

## Como identificar novos mocks no futuro

Antes de criar uma nova função de query, verificar se:
1. A fonte de dados (tabela BigQuery) existe e tem o campo necessário
2. Se não existir: usar `disponibilidade: "indisponível"` no schema e retornar `data: []` com `warning`
3. Não usar `return 0` ou `return tonelagem_total` como denominador de índice — isso cria dados incorretos sem aviso

```python
# Padrão correto para indicador sem dado:
async def query_sem_dados(id_instalacao, ano):
    return IndicatorResponse(
        data=[],
        warnings=[Warning(mensagem="Dados não disponíveis para este indicador neste período")],
        disponibilidade="indisponível",
    )
```
