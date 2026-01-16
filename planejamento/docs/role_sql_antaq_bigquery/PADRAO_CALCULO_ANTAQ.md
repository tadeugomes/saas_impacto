# 📋 Padrão Oficial de Cálculo ANTAQ

## 🎯 **Objetivo**
Este documento estabelece o padrão obrigatório para cálculos e análises utilizando dados da ANTAQ, garantindo consistência, qualidade e alinhamento com os dados oficiais publicados.

## 🚨 **REGRA FUNDAMENTAL**

### **Use SEMPRE a View Oficial**
```sql
-- ✅ FORMA CORRETA - Usar view oficial
SELECT
    ano,
    mes,
    sentido,
    SUM(vlpesocargabruta_oficial) as volume_toneladas
FROM antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial
WHERE EXTRACT(YEAR FROM data_referencia) = 2024
GROUP BY ano, mes, sentido;

-- ❌ NUNCA FAÇA ISSO - Acessar tabela bruta diretamente
SELECT
    SUM(CAST(REPLACE(vlpesocargabruta, ',', '.') AS FLOAT64))
FROM antaqdados.br_antaq_estatistico_aquaviario.carga;  -- ERRADO!
```

## 📊 **View Oficial Disponível**

### **`v_carga_metodologia_oficial`**
Campos disponíveis:
- `idcarga` - ID único da carga
- `sentido` - Embarcados/Desembarcados/Não Informado
- `vlpesocargabruta_oficial` - Peso já convertido para FLOAT64
- `qtcarga_oficial` - Quantidade já convertida
- `ano`, `mes` - Período derivado
- `tipo_operacao_da_carga` - Tipo de operação
- 
## 🔧 **Padrões Obrigatórios**

### **1. Filtro de Validação**
— Já embutido na view (tipos oficiais, peso positivo, autorização). Nas consultas, filtre apenas por período usando `data_referencia`.

### **Referência Temporal**
- Utilize a **data de desatracação** como referência oficial de período.
- Exemplo de filtro por janela mensal/anual:
  ```sql
  WHERE SAFE_CAST(data_referencia AS DATE) BETWEEN DATE '2024-01-01' AND DATE '2024-12-31'
  ```
- Esse critério impede dupla contagem entre meses e reproduz o total divulgado pela ANTAQ.

### **2. Tratamento de Duplicação**
```sql
-- A view já aplica DISTINCT, mas use COUNT(DISTINCT) para agregações
SELECT
    COUNT(DISTINCT idcarga) as cargas_unicas,
    SUM(vlpesocargabruta_oficial) as volume_toneladas
FROM v_carga_metodologia_oficial
```

### **3. Agrupamento Temporal**
```sql
-- Padrão para análise mensal
SELECT
    FORMAT_DATE('%Y-%m', DATE_TRUNC(data_referencia, MONTH)) as ano_mes,
    SUM(vlpesocargabruta_oficial) as volume_toneladas
FROM v_carga_metodologia_oficial
GROUP BY ano_mes
ORDER BY ano_mes;
```

### **4. Análise por Sentido**
```sql
-- Padrão para análise por sentido
SELECT
    sentido,
    COUNT(DISTINCT idcarga) as operacoes,
    SUM(vlpesocargabruta_oficial) as volume_toneladas
FROM v_carga_metodologia_oficial
GROUP BY sentido;
```

## 📈 **Templates de Consulta**

### **Template 1: Volume Mensal Completo**
```sql
-- Volume mensal completo com validação
SELECT
    ano,
    mes,
    COUNT(DISTINCT idcarga) as cargas_unicas,
    COUNT(DISTINCT idatracacao) as atracoes_unicas,
    SUM(vlpesocargabruta_oficial) as volume_toneladas,
    ROUND(SUM(vlpesocargabruta_oficial) / 1000000, 2) as volume_mil_toneladas,
    COUNT(DISTINCT porto_atracacao) as portos_unicos
FROM antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial
GROUP BY ano, mes
ORDER BY ano, mes;
```

### **Template 2: Análise por Porto**
```sql
-- Análise detalhada por porto
SELECT
    porto_atracacao,
    uf,
    sentido,
    COUNT(DISTINCT idcarga) as operacoes,
    SUM(vlpesocargabruta_oficial) as volume_toneladas,
    ROUND(SUM(vlpesocargabruta_oficial) / 1000000, 2) as volume_mil_toneladas
FROM antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial
WHERE SUBSTR(CAST(data_referencia AS STRING), 1, 7) = '2025-04'  -- Ajustar período
GROUP BY porto_atracacao, uf, sentido
ORDER BY volume_toneladas DESC;
```

### **Template 3: Validação vs Dados Oficiais**
```sql
-- Validação automática vs dados oficiais
DECLARE volume_oficial INT64 DEFAULT 107600000; -- Ajustar conforme mês

WITH dados_bigquery AS (
    SELECT SUM(vlpesocargabruta_oficial) as volume
    FROM antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial
    WHERE SUBSTR(CAST(data_referencia AS STRING), 1, 7) = '2025-04'
)
SELECT
    volume as volume_bigquery,
    volume_oficial,
    ROUND((volume - volume_oficial) * 100.0 / volume_oficial, 2) as divergencia_percentual,
    CASE
        WHEN ABS((volume - volume_oficial) * 100.0 / volume_oficial) <= 5 THEN '✅ OK'
        ELSE '❌ REVISAR'
    END as status;
FROM dados_bigquery;
```

## 🚫 **Operações Proibidas**

### **NUNCA acesse as tabelas brutas diretamente:**
```sql
-- ❌ ERRADO
SELECT * FROM antaqdados.br_antaq_estatistico_aquaviario.carga;
SELECT * FROM antaqdados.br_antaq_estatistico_aquaviario.atracacao;
```

### **NUNCA aplique filtros manuais:**
```sql
-- ❌ ERRADO - Não repita lógica de filtro
WHERE tipo_operacao_da_carga NOT IN ('Apoio', 'Transbordo', ...)
```

### **NUNCA faça conversão manual de dados:**
```sql
-- ❌ ERRADO - Não converta dados manualmente
CAST(REPLACE(vlpesocargabruta, ',', '.') AS FLOAT64)
```

## ✅ **Boas Práticas**

### **1. Use SEMPRE a view oficial**
- Garante aplicação correta da metodologia
- Mantém consistência entre análises
- Evita erros de duplicação

### **2. Valide seus resultados**
- Compare sempre com dados oficiais quando disponíveis
- Use o template de validação
- Documente qualquer discrepância > 5%

### **3. Documente suas análises**
- Inclua período e filtros utilizados
- Anote qualquer tratamento especial
- Registre fontes de dados oficiais para comparação

### **4. Use COUNT(DISTINCT) para contagens**
- Evita duplicação em operações de agregação
- Garante contagem precisa de operações únicas

## 📋 **Checklist de Qualidade**

### **Antes de Executar:**
- [ ] Estou usando `v_carga_metodologia_oficial`?
- [ ] Estou filtrando por `data_referencia` (desatracação)?
- [ ] Evitei filtros manuais de tipos/peso (já embutidos na view)?
- [ ] Usei COUNT(DISTINCT) para contagens?
- [ ] Validei o período de análise?

### **Após Executar:**
- [ ] Validei volume total vs dados oficiais?
- [ ] A divergência está < 5%?
- [ ] Documentei os resultados?
- [ ] Salvei a query para reutilização?

## 🔔 **Suporte e Manutenção**

### **Contato em caso de problemas:**
- Time de Engenharia de Dados
- Documentação adicional: [docs/](./)
- Padrões de qualidade: [PADRAO_CALCULO_ANTAQ.md](./PADRAO_CALCULO_ANTAQ.md)

### **Atualizações do padrão:**
- Qualquer alteração na metodologia deve ser discutida com o time
- Versão atual: 1.0
- Data de atualização: Outubro 2024

---

**Este padrão é OBRIGATÓRIO para todas as análises com dados ANTAQ.**
