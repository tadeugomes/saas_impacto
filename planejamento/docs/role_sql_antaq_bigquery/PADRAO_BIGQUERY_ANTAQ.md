# 📋 Padrão Obrigatório BigQuery - ANTAQ

## 🎯 REGRA FUNDAMENTAL

**SEMPRE** use a view metodológica oficial para qualquer análise de movimentação de cargas no BigQuery.

## ✅ Padrão Ouro (OBRIGATÓRIO)

```sql
-- Estrutura padrão para TODAS as consultas
SELECT
    porto_atracacao,
    SUM(vlpesocargabruta_oficial) as toneladas,
    COUNT(DISTINCT idatracacao) as atracacoes,
    COUNT(*) as registros
FROM antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial
WHERE EXTRACT(YEAR FROM data_referencia) = 2024                  -- Período desejado
  -- [outros filtros específicos]
GROUP BY porto_atracacao
ORDER BY toneladas DESC;
```

## 🚨 Tabelas que NUNCA devem ser usadas diretamente

| Tabela | Motivo | Problema |
|--------|--------|----------|
| `atracao` | Sem tratamento de duplicação | Resultados 76% maiores |
| `carga` | Sem validação ANTAQ | Inclui dados inválidos |
| `v_carga_oficial_antaq` | Metodologia diferente | Resultados inconsistentes |

## 🎯 Exemplos Práticos

### 1. Análise por Porto
```sql
-- Top 10 portos por movimentação
SELECT
    porto_atracacao,
    uf,
    regiao_geografica,
    FORMAT('%.2f', SUM(vlpesocargabruta_oficial)) as toneladas,
    COUNT(DISTINCT idatracacao) as atracacoes
FROM antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial
WHERE EXTRACT(YEAR FROM data_referencia) = 2024
GROUP BY porto_atracacao, uf, regiao_geografica
HAVING SUM(vlpesocargabruta_oficial) > 0
ORDER BY SUM(vlpesocargabruta_oficial) DESC
LIMIT 10;
```

### 2. Análise Temporal
```sql
-- Evolução mensal da movimentação
SELECT
    ano,
    mes,
    FORMAT('%.2f', SUM(vlpesocargabruta_oficial)) as toneladas_mensais,
    COUNT(DISTINCT porto_atracacao) as portos_ativos,
    COUNT(DISTINCT idatracacao) as total_atracacoes
FROM antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial
WHERE EXTRACT(YEAR FROM data_referencia) BETWEEN 2022 AND 2024
GROUP BY ano, mes
ORDER BY ano, mes;
```

### 3. Análise por Tipo de Navegação
```sql
-- Movimentação por tipo de navegação
SELECT
    tipo_de_navegacao_da_atracacao,
    FORMAT('%.2f', SUM(vlpesocargabruta_oficial)) as toneladas,
    COUNT(DISTINCT porto_atracacao) as portos_utilizados,
    COUNT(DISTINCT idatracacao) as total_atracacoes
FROM antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial
WHERE EXTRACT(YEAR FROM data_referencia) = 2024
GROUP BY tipo_de_navegacao_da_atracacao
ORDER BY SUM(vlpesocargabruta_oficial) DESC;
```

### 4. Análise por Mercadoria
```sql
-- Top 15 mercadorias movimentadas
SELECT
    cdmercadoria,
    FORMAT('%.2f', SUM(vlpesocargabruta_oficial)) as toneladas,
    COUNT(*) as registros,
    COUNT(DISTINCT porto_atracacao) as portos_envolvidos
FROM antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial
WHERE EXTRACT(YEAR FROM data_referencia) = 2024
  AND cdmercadoria IS NOT NULL
GROUP BY cdmercadoria
HAVING SUM(vlpesocargabruta_oficial) > 0
ORDER BY SUM(vlpesocargabruta_oficial) DESC
LIMIT 15;
```

### 5. Análise Comparativa Períodos
```sql
-- Comparativo mesmo mês anos diferentes
SELECT
    EXTRACT(MONTH FROM data_referencia) as mes,
    EXTRACT(YEAR FROM data_referencia) as ano,
    FORMAT('%.2f', SUM(vlpesocargabruta_oficial)) as toneladas,
    LAG(SUM(vlpesocargabruta_oficial)) OVER (ORDER BY EXTRACT(YEAR FROM data_atracacao), EXTRACT(MONTH FROM data_atracacao)) as toneladas_ano_anterior,
    FORMAT('%.1f%%',
      (SUM(vlpesocargabruta_oficial) - LAG(SUM(vlpesocargabruta_oficial)) OVER (ORDER BY EXTRACT(YEAR FROM data_atracacao), EXTRACT(MONTH FROM data_atracacao))) * 100.0 /
      LAG(SUM(vlpesocargabruta_oficial)) OVER (ORDER BY EXTRACT(YEAR FROM data_atracacao), EXTRACT(MONTH FROM data_atracacao))
    ) as variacao_percentual
FROM antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial
WHERE EXTRACT(YEAR FROM data_referencia) IN (2023, 2024)
GROUP BY EXTRACT(YEAR FROM data_referencia), EXTRACT(MONTH FROM data_referencia)
ORDER BY ano, mes;
```

## 🔧 Filtros Comuns

### Por Período
```sql
WHERE EXTRACT(YEAR FROM data_referencia) = 2024
  -- OU período específico por desatracação:
  AND SAFE_CAST(data_referencia AS DATE) BETWEEN DATE '2024-01-01' AND DATE '2024-12-31'
```

### Por Estado/Região
```sql
WHERE EXTRACT(YEAR FROM data_referencia) = 2024
  AND uf IN ('SP', 'RJ', 'ES')  -- Sudeste
  -- OU
  AND regiao_geografica = 'Sudeste'
```

### Por Tipo de Operação
```sql
WHERE EXTRACT(YEAR FROM data_referencia) = 2024
  AND sentido = 'Embarcados'  -- Ou 'Desembarcados'
```

### Por Porto Específico
```sql
WHERE EXTRACT(YEAR FROM data_referencia) = 2024
  AND porto_atracacao = 'Santos'
```

## ⚡ Dicas de Performance

### 1. Particionamento por Data
```sql
-- Use sempre filtros de data na cláusula WHERE
WHERE SAFE_CAST(data_referencia AS DATE) >= DATE '2024-01-01'
  AND SAFE_CAST(data_referencia AS DATE) < DATE '2025-01-01'
```

### 2. Colunas para Agrupamento Eficiente
```sql
-- Prefira estas colunas para GROUP BY
GROUP BY porto_atracacao, uf, ano, mes
```

### 3. Filtros Seletivos
```sql
-- Aplique filtros o mais específico possível
WHERE LOWER(tipo_operacao_da_carga) IN ('apoio', 'abastecimento', 'safamento', 'remoção a bordo', 'operação intermediária', 'transferência interna', 'movimentação de carga', 'longo curso exportação', 'longo curso importação', 'longo curso exportação com baldeação de carga estrangeira', 'longo curso importação com baldeação de carga estrangeira', 'cabotagem', 'interior', 'baldeação de carga nacional', 'baldeação de carga estrangeira de passagem')
  AND vlpesocargabruta_oficial > 0
  AND ano = '2024'
  AND uf = 'SP'
  AND vlpesocargabruta_oficial > 1000
```

## 🎯 Resultados Esperados

Usando este padrão, você obterá:
- ✅ **98,6% de precisão** vs dados oficiais ANTAQ
- ✅ **Eliminação de dupla contagem**
- ✅ **Dados validados** conforme metodologia oficial
- ✅ **Comparabilidade** com relatórios oficiais
- ✅ **Consistência** em todas as análises

## 🚀 Validação

Para validar que está usando o padrão correto:

```sql
-- Query de validação rápida
SELECT
    'VALIDAÇÃO PADRÃO ANTAQ' as status,
    FORMAT('%.2f', SUM(vlpesocargabruta_oficial)) as total_toneladas,
    COUNT(*) as total_registros,
    COUNT(DISTINCT porto_atracacao) as portos_ativos
FROM antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial
WHERE EXTRACT(YEAR FROM data_referencia) = 2024;

-- Resultado esperado: ~1.302.009.479,02 toneladas
```

---

**REGRA FINAL**: Use **SEMPRE** `v_carga_metodologia_oficial` com `tipos de operação oficiais + peso > 0` no BigQuery! 🎯
