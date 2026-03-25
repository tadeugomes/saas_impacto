# Registro Oficial — Mocks, Dados Simulados e Placeholders

> Criado: 2026-03-25 | Auditoria completa do código de produção
>
> **Escopo:** Apenas código de produção (`backend/app/` excluindo `tests/`, `frontend/src/` excluindo `*.test.*`).
> Dados de testes unitários (mocks em `unittest.mock`, `_FakeRedis`, `_DummyBigQueryClient`) são esperados e não estão listados aqui.

---

## Sumário

| Severidade | Quantidade | Descrição |
|-----------|-----------|-----------|
| 🔴 ALTO | 2 | Indicadores retornam dado incorreto (denominador errado) — usuário vê valor sem sentido |
| 🟡 MÉDIO | 2 | Indicadores retornam zero explícito — fonte de dados inexistente |
| 🟢 BAIXO | 3 | Coeficientes hardcoded da literatura acadêmica — intencional e documentado |

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
