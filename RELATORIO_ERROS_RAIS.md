# Relatório de Erros - Análise RAIS (Módulo 3)

**Data:** 2026-01-16
**Branch:** claude/fix-rais-analysis-display-6edCB
**Foco:** Criação de análises RAIS e apresentação na tela

---

## 🔴 PROBLEMAS CRÍTICOS

### 1. **Indicadores Faltantes no Frontend** (CRÍTICO)
**Localização:** `/frontend/src/views/Dashboard/ModuleViews/Module3View.tsx:13-20`

**Problema:**
- Apenas **6 de 12** indicadores do Módulo 3 estão sendo exibidos no frontend
- Indicadores implementados no backend mas **ausentes** no frontend:
  - IND-3.03: Paridade por Categoria Profissional
  - IND-3.07: Produtividade (ton/empregado)
  - IND-3.08: Receita por Empregado
  - IND-3.09: Distribuição por Escolaridade
  - IND-3.10: Idade Média
  - IND-3.11: Variação Anual de Empregos

**Impacto:** Usuários não conseguem visualizar metade dos indicadores disponíveis

**Evidência:**
```typescript
// Module3View.tsx - linha 13
const INDICATORS_INFO = [
  { code: 'IND-3.01', ... },  // ✓ Exibido
  { code: 'IND-3.02', ... },  // ✓ Exibido
  // IND-3.03 AUSENTE ❌
  { code: 'IND-3.04', ... },  // ✓ Exibido
  { code: 'IND-3.05', ... },  // ✓ Exibido
  { code: 'IND-3.06', ... },  // ✓ Exibido
  // IND-3.07 a IND-3.11 AUSENTES ❌
  { code: 'IND-3.12', ... },  // ✓ Exibido
];
```

---

### 2. **Estrutura de Dados Incompatível para Indicadores Agrupados** (CRÍTICO)
**Localização:** Indicadores IND-3.03 e IND-3.09

**Problema:**
O frontend atual usa `BarChart` simples que espera **1 valor por município**, mas dois indicadores retornam **múltiplos valores agrupados**:

#### IND-3.03 (Paridade por Categoria Profissional)
Retorna 3 linhas por município (uma para cada categoria):
```sql
-- backend/app/db/bigquery/queries/module3_human_resources.py:214
SELECT
  id_municipio,
  nome_municipio,
  ano,
  categoria,           -- 'GESTAO_TECNICO', 'ADMINISTRATIVO', 'OPERACIONAL'
  total,
  feminino,
  percentual_feminino
```

#### IND-3.09 (Distribuição por Escolaridade)
Retorna N linhas por município (uma para cada nível de escolaridade):
```sql
-- module3_human_resources.py:542
SELECT
  id_municipio,
  nome_municipio,
  ano,
  grau_instrucao,      -- Múltiplos níveis de escolaridade
  qtd,
  percentual
```

**Impacto:**
- Se adicionados ao frontend atual, estes indicadores exibirão dados incorretos ou quebrarão
- Necessário implementar visualizações específicas (stacked bar chart ou grouped bar chart)

---

### 3. **Tratamento de Erros Silencioso** (ALTO)
**Localização:** `/frontend/src/views/Dashboard/ModuleViews/Module3View.tsx:48`

**Problema:**
```typescript
indicatorsService.queryIndicator({...})
  .catch(() => ({ data: [] }))  // ❌ Erro silenciosamente suprimido
```

**Consequências:**
- Erros de API não são logados no console
- Usuário vê apenas "Dados não disponíveis" sem saber a causa
- Dificulta debugging de problemas de backend/rede
- Não há distinção entre "sem dados" e "erro ao buscar dados"

**Evidência:**
```typescript
// Linha 48 - erro silencioso
.catch(() => ({ data: [] }))

// Linha 116 - mesma mensagem para erro e "sem dados"
<div className="h-64 flex items-center justify-center text-gray-400">
  Dados não disponíveis
</div>
```

---

### 4. **Comentário Indica Ausência de Dados** (MÉDIO)
**Localização:** `/frontend/src/views/Dashboard/ModuleViews/Module3View.tsx:12`

**Problema:**
```typescript
// Note: These indicators currently have NO DATA in the database
```

**Análise:**
- Backend possui queries completas e funcionais
- Queries usam dataset público: `basedosdados.br_me_rais.microdados_vinculos`
- **Possíveis causas:**
  1. Dataset RAIS não está populado no BigQuery do projeto
  2. Credenciais de acesso ao dataset Base dos Dados não configuradas
  3. Falta pipeline ETL para popular dados ANTAQ
  4. Queries executam mas retornam vazio por falta de dados filtrados

**Impacto:** Indicadores podem estar funcionais mas sem retornar dados reais

---

## 🟡 PROBLEMAS DE INCONSISTÊNCIA

### 5. **Descrição Incorreta no Frontend** (BAIXO)
**Localização:** `/frontend/src/views/Dashboard/ModuleViews/Module3View.tsx:81`

**Problema:**
```typescript
<p className="text-gray-500 mt-1">
  6 indicadores de recursos humanos  {/* ❌ Incorreto */}
</p>
```

**Correção:** Deve ser "12 indicadores" (ou 6 quando apenas 6 estiverem implementados)

---

### 6. **Falta de valueField para Indicadores Multivalor** (MÉDIO)

**Problema:**
O sistema atual usa `valueField` para extrair um único campo, mas IND-3.03 e IND-3.09 possuem estrutura complexa:

```typescript
// Atual (Module3View.tsx:22-24)
function getValueFromData(item: any, valueField: string): number {
  return item[valueField] ?? item.valor ?? item.total ?? 0;
}
```

**Campos esperados:**
| Indicador | valueField Necessário | Tipo de Visualização |
|-----------|----------------------|---------------------|
| IND-3.03 | `percentual_feminino` (por categoria) | Grouped/Stacked Bar |
| IND-3.07 | `ton_por_empregado` | Bar Chart (simples) ✓ |
| IND-3.08 | `pib_por_empregado_portuario` | Bar Chart (simples) ✓ |
| IND-3.09 | `percentual` (por escolaridade) | Grouped/Stacked Bar |
| IND-3.10 | `idade_media` | Bar Chart (simples) ✓ |
| IND-3.11 | `variacao_percentual` | Bar Chart (simples) ✓ |

---

## ✅ VERIFICAÇÕES REALIZADAS

### Mapeamento de Campos Backend ↔ Frontend

**Status:** ✓ CORRETO para os 6 indicadores exibidos

| Indicador | Campo Backend | valueField Frontend | Status |
|-----------|---------------|---------------------|--------|
| IND-3.01 | `empregos_portuarios` | `empregos_portuarios` | ✓ Match |
| IND-3.02 | `percentual_feminino` | `percentual_feminino` | ✓ Match |
| IND-3.04 | `taxa_temporario` | `taxa_temporario` | ✓ Match |
| IND-3.05 | `salario_medio` | `salario_medio` | ✓ Match |
| IND-3.06 | `massa_salarial_anual` | `massa_salarial_anual` | ✓ Match |
| IND-3.12 | `participacao_emprego_local` | `participacao_emprego_local` | ✓ Match |

---

## 📊 ESTRUTURA DE DADOS RETORNADA

### Indicadores Simples (1 valor por município)
```json
{
  "data": [
    {
      "id_municipio": "3304557",
      "nome_municipio": "Rio de Janeiro",
      "ano": 2023,
      "empregos_portuarios": 1500  // Exemplo IND-3.01
    }
  ]
}
```

### Indicadores Agrupados (N valores por município)

#### IND-3.03 - Por Categoria:
```json
{
  "data": [
    {
      "id_municipio": "3304557",
      "nome_municipio": "Rio de Janeiro",
      "ano": 2023,
      "categoria": "GESTAO_TECNICO",
      "total": 500,
      "feminino": 150,
      "percentual_feminino": 30.00
    },
    {
      "id_municipio": "3304557",
      "nome_municipio": "Rio de Janeiro",
      "ano": 2023,
      "categoria": "OPERACIONAL",
      "total": 800,
      "feminino": 80,
      "percentual_feminino": 10.00
    }
  ]
}
```

#### IND-3.09 - Por Escolaridade:
```json
{
  "data": [
    {
      "id_municipio": "3304557",
      "nome_municipio": "Rio de Janeiro",
      "ano": 2023,
      "grau_instrucao": "Superior Completo",
      "qtd": 300,
      "percentual": 20.00
    },
    {
      "id_municipio": "3304557",
      "nome_municipio": "Rio de Janeiro",
      "ano": 2023,
      "grau_instrucao": "Médio Completo",
      "qtd": 900,
      "percentual": 60.00
    }
  ]
}
```

---

## 🎯 RECOMENDAÇÕES DE CORREÇÃO

### Prioridade 1 (Imediata)
1. **Adicionar indicadores simples faltantes** (IND-3.07, 3.08, 3.10, 3.11)
   - Apenas adicionar ao array `INDICATORS_INFO`
   - Usar `BarChart` existente

2. **Melhorar tratamento de erros**
   - Logar erros no console
   - Diferenciar "sem dados" de "erro ao buscar"
   - Exibir mensagem de erro específica

3. **Corrigir descrição do número de indicadores**
   - Atualizar de "6" para "12" ou número real exibido

### Prioridade 2 (Curto Prazo)
4. **Implementar visualização para indicadores agrupados** (IND-3.03, IND-3.09)
   - Criar componente `GroupedBarChart` ou `StackedBarChart`
   - Adaptar lógica de extração de dados para múltiplos valores

5. **Investigar ausência de dados**
   - Verificar conexão com BigQuery
   - Validar credenciais para Base dos Dados
   - Testar queries manualmente no console BigQuery

### Prioridade 3 (Médio Prazo)
6. **Adicionar validação de schema**
   - Validar estrutura de resposta da API
   - Alertar se campos esperados estão ausentes

7. **Melhorar logging e monitoramento**
   - Adicionar métricas de sucesso/falha por indicador
   - Implementar retry logic para falhas de rede

---

## 📋 CHECKLIST DE CORREÇÃO

### Frontend (`Module3View.tsx`)
- [ ] Adicionar IND-3.07 ao `INDICATORS_INFO`
- [ ] Adicionar IND-3.08 ao `INDICATORS_INFO`
- [ ] Adicionar IND-3.10 ao `INDICATORS_INFO`
- [ ] Adicionar IND-3.11 ao `INDICATORS_INFO`
- [ ] Implementar tratamento de erro com logging
- [ ] Corrigir texto "6 indicadores" → "12 indicadores"
- [ ] Criar componente para indicadores agrupados
- [ ] Adicionar IND-3.03 com visualização agrupada
- [ ] Adicionar IND-3.09 com visualização agrupada

### Backend (Validações)
- [ ] Testar query IND-3.03 no BigQuery
- [ ] Testar query IND-3.07 no BigQuery (requer JOIN com ANTAQ)
- [ ] Testar query IND-3.08 no BigQuery (requer JOIN com PIB)
- [ ] Testar query IND-3.09 no BigQuery
- [ ] Validar acesso ao dataset `basedosdados.br_me_rais.microdados_vinculos`
- [ ] Validar acesso ao dataset ANTAQ para IND-3.07

### Formatação (`chartFormats.ts`)
- [ ] Adicionar formato para IND-3.07 (`ton_por_empregado`)
- [ ] Adicionar formato para IND-3.08 (`pib_por_empregado`)
- [ ] Adicionar formato para IND-3.10 (`idade_media`)
- [ ] Adicionar formato para IND-3.11 (`variacao_percentual`)

---

## 🔍 OBSERVAÇÕES SOBRE "DISCUSSÃO SOBRE TRABALHO"

**Busca realizada:** Procurei por termos relacionados a "discussão", "análise textual", "relatório narrativo" sobre trabalho/RAIS.

**Resultado:** Não foi encontrada nenhuma funcionalidade de "discussão sobre trabalho" no código atual.

**Possíveis interpretações:**
1. Pode se referir a uma **análise narrativa/relatório** que deveria ser gerada mas não foi implementada
2. Pode se referir aos **metadados/descrições** dos indicadores no arquivo `templates.py`
3. Pode ser uma funcionalidade planejada mas não desenvolvida

**Arquivos verificados:**
- `/backend/app/reports/templates.py` - Contém apenas metadados dos indicadores (nome, descrição, unidade)
- `/backend/app/reports/report_service.py` - Gera relatórios DOCX mas sem análise narrativa
- Nenhum arquivo contém "discussão" ou análise textual elaborada sobre trabalho

**Recomendação:** Esclarecer com stakeholders o que seria a "discussão sobre trabalho" esperada.

---

## 📁 ARQUIVOS ANALISADOS

```
/backend/app/db/bigquery/queries/module3_human_resources.py  # Queries SQL
/backend/app/services/generic_indicator_service.py           # Serviço de indicadores
/backend/app/reports/templates.py                            # Metadados
/frontend/src/views/Dashboard/ModuleViews/Module3View.tsx    # Interface frontend
/frontend/src/utils/chartFormats.ts                          # Formatação de valores
```

---

## 🏁 CONCLUSÃO

**Problemas Principais Identificados:**
1. ❌ 6 indicadores faltantes no frontend (IND-3.03, 3.07-3.11)
2. ❌ 2 indicadores (IND-3.03, 3.09) necessitam visualização especial para dados agrupados
3. ❌ Tratamento de erro inadequado (silencioso)
4. ⚠️ Possível ausência de dados reais no BigQuery

**Próximos Passos:**
1. Implementar indicadores simples faltantes (rápido)
2. Melhorar tratamento de erros (rápido)
3. Criar visualização para indicadores agrupados (médio)
4. Investigar disponibilidade de dados RAIS (crítico)

**Estimativa de Impacto:**
- Problemas identificados afetam **50% dos indicadores** do Módulo 3
- Correções prioritárias podem ser implementadas rapidamente
- Visualizações agrupadas requerem desenvolvimento de componente novo
