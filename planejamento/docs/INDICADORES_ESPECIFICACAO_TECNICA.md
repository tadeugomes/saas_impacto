# Especificação Técnica de Indicadores
## Sistema de Análise do Impacto Econômico do Setor Portuário Brasileiro

**Versão:** 3.0  
**Data:** Dezembro 2025  
**Padrão:** UNCTAD Port Performance Scorecard (PPS)

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Fontes de Dados](#2-fontes-de-dados)
3. [Módulo 1: Operações de Navios](#3-módulo-1-operações-de-navios)
4. [Módulo 2: Operações de Carga](#4-módulo-2-operações-de-carga)
5. [Módulo 3: Recursos Humanos](#5-módulo-3-recursos-humanos)
6. [Módulo 4: Comércio Exterior](#6-módulo-4-comércio-exterior)
7. [Módulo 5: Impacto Econômico Regional](#7-módulo-5-impacto-econômico-regional)
8. [Módulo 6: Finanças Públicas](#8-módulo-6-finanças-públicas)
9. [Módulo 7: Índices Sintéticos](#9-módulo-7-índices-sintéticos)
10. [CNAEs do Setor Portuário](#10-cnaes-do-setor-portuário)
11. [Estrutura de Marts no BigQuery](#11-estrutura-de-marts-no-bigquery)

---

## 1. Visão Geral

### 1.1 Escopo

Este documento especifica **78 indicadores** organizados em 7 módulos para implementação no BigQuery e exposição via API FastAPI.

### 1.2 Padrão UNCTAD

Indicadores marcados com `[UNCTAD]` seguem a metodologia do Port Performance Scorecard, permitindo benchmarking internacional.

| Módulo | Total | UNCTAD | Específico BR |
|--------|-------|--------|---------------|
| Operações de Navios | 12 | 10 | 2 |
| Operações de Carga | 13 | 11 | 2 |
| Recursos Humanos | 12 | 8 | 4 |
| Comércio Exterior | 10 | 0 | 10 |
| Impacto Econômico | 18 | 0 | 18 |
| Finanças Públicas | 6 | 0 | 6 |
| Índices Sintéticos | 7 | 0 | 7 |
| **TOTAL** | **78** | **29** | **49** |

### 1.3 Abordagem Metodológica

> ⚠️ **IMPORTANTE**: Esta especificação adota abordagem **descritiva e correlacional**.
> 
> **NÃO estão incluídos:**
> - Multiplicadores Input-Output (requerem matrizes regionais inexistentes)
> - Análise DEA/SFA (requer validação acadêmica)
> - Modelos ARIMA/Forecasting (escopo diferente)
> - Efeitos induzidos (sem dados de consumo)

---

## 2. Fontes de Dados

### 2.1 BigQuery - Caminhos Completos

```sql
-- ANTAQ (Dados Portuários)
antaqdados.br_antaq_estatistico_aquaviario.v_atracacao_validada
antaqdados.br_antaq_estatistico_aquaviario.v_carga_validada
antaqdados.br_antaq_estatistico_aquaviario.tempos_atracacao
antaqdados.br_antaq_estatistico_aquaviario.tempos_atracacao_paralisacao
antaqdados.br_antaq_estatistico_aquaviario.taxa_ocupacao
antaqdados.br_antaq_estatistico_aquaviario.carga_conteinerizada
antaqdados.br_antaq_estatistico_aquaviario.instalacao_origem

-- RAIS (Emprego Formal)
basedosdados.br_me_rais.microdados_vinculos

-- IBGE (PIB e População)
basedosdados.br_ibge_pib.municipio
basedosdados.br_ibge_populacao.municipio

-- Comex Stat (Comércio Exterior)
basedosdados.br_me_comex_stat.municipio_exportacao
basedosdados.br_me_comex_stat.municipio_importacao

-- FINBRA (Arrecadação)
basedosdados.br_tesouro_finbra.receitas

-- IPCA (Deflacionamento)
basedosdados.br_ibge_ipca.mes_brasil
```

### 2.2 Chaves de Junção

| Campo | Descrição | Formato |
|-------|-----------|---------|
| `id_municipio` | Código IBGE município | 7 dígitos |
| `sigla_uf` | Unidade Federativa | 2 caracteres |
| `ano` | Ano de referência | YYYY |
| `mes` | Mês de referência | 1-12 |
| `id_instalacao` | Código instalação ANTAQ | Alfanumérico |

---

## 3. Módulo 1: Operações de Navios

**Fonte Principal:** `antaqdados.br_antaq_estatistico_aquaviario`

### 3.1 Indicadores de Tempo

#### IND-1.01: Tempo Médio de Espera `[UNCTAD]`

```sql
SELECT 
  id_instalacao,
  ano,
  AVG(tempo_espera) AS tempo_medio_espera_horas
FROM tempos_atracacao
GROUP BY id_instalacao, ano
```

**Unidade:** Horas  
**Granularidade:** Instalação/Ano

---

#### IND-1.02: Tempo Médio em Porto `[UNCTAD]`

```sql
SELECT 
  id_instalacao,
  ano,
  AVG(tempo_atracado + tempo_espera) AS tempo_medio_porto_horas
FROM tempos_atracacao
GROUP BY id_instalacao, ano
```

**Unidade:** Horas  
**Granularidade:** Instalação/Ano

---

#### IND-1.03: Tempo Bruto de Atracação `[UNCTAD]`

```sql
SELECT 
  id_instalacao,
  ano,
  AVG(tempo_atracado) AS tempo_bruto_atracacao_horas
FROM tempos_atracacao
GROUP BY id_instalacao, ano
```

**Unidade:** Horas  
**Granularidade:** Instalação/Ano

---

#### IND-1.04: Tempo Líquido de Operação `[UNCTAD]`

```sql
SELECT 
  id_instalacao,
  ano,
  AVG(tempo_operacao) AS tempo_liquido_operacao_horas
FROM tempos_atracacao
GROUP BY id_instalacao, ano
```

**Unidade:** Horas  
**Granularidade:** Instalação/Ano

---

#### IND-1.05: Taxa de Ocupação de Berços `[UNCTAD]`

```sql
SELECT 
  id_instalacao,
  ano,
  AVG(taxa_ocupacao) AS taxa_ocupacao_percentual
FROM taxa_ocupacao
GROUP BY id_instalacao, ano
```

**Unidade:** Percentual (0-100)  
**Granularidade:** Instalação/Ano

---

#### IND-1.06: Tempo Ocioso Médio por Turno `[UNCTAD]`

```sql
SELECT 
  id_instalacao,
  ano,
  AVG(tempo_paralisado) AS tempo_ocioso_medio_horas
FROM tempos_atracacao_paralisacao
GROUP BY id_instalacao, ano
```

**Unidade:** Horas  
**Granularidade:** Instalação/Ano

---

### 3.2 Indicadores de Características de Navios

#### IND-1.07: Arqueação Bruta Média (GT) `[UNCTAD]`

```sql
SELECT 
  id_instalacao,
  ano,
  AVG(arqueacao_bruta) AS arqueacao_bruta_media
FROM v_atracacao_validada
GROUP BY id_instalacao, ano
```

**Unidade:** GT (Gross Tonnage)  
**Granularidade:** Instalação/Ano

---

#### IND-1.08: Comprimento Médio de Navios `[UNCTAD]`

```sql
SELECT 
  id_instalacao,
  ano,
  AVG(comprimento) AS comprimento_medio_metros
FROM v_atracacao_validada
GROUP BY id_instalacao, ano
```

**Unidade:** Metros  
**Granularidade:** Instalação/Ano

---

#### IND-1.09: Calado Máximo Operacional `[UNCTAD]`

```sql
SELECT 
  id_instalacao,
  MAX(calado) AS calado_maximo_metros
FROM v_atracacao_validada
GROUP BY id_instalacao
```

**Unidade:** Metros  
**Granularidade:** Instalação

---

#### IND-1.10: Distribuição por Tipo de Navio `[UNCTAD]`

```sql
SELECT 
  id_instalacao,
  ano,
  tipo_navegacao,
  COUNT(*) AS qtd_atracacoes,
  COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY id_instalacao, ano) AS percentual
FROM v_atracacao_validada
GROUP BY id_instalacao, ano, tipo_navegacao
```

**Unidade:** Percentual por tipo  
**Granularidade:** Instalação/Ano/Tipo

---

#### IND-1.11: Número de Atracações

```sql
SELECT 
  id_instalacao,
  ano,
  COUNT(DISTINCT id_atracacao) AS total_atracacoes
FROM v_atracacao_validada
GROUP BY id_instalacao, ano
```

**Unidade:** Contagem  
**Granularidade:** Instalação/Ano

---

#### IND-1.12: Índice de Paralisação

```sql
SELECT 
  id_instalacao,
  ano,
  SUM(tempo_paralisado) * 100.0 / NULLIF(SUM(tempo_atracado), 0) AS indice_paralisacao
FROM tempos_atracacao t
LEFT JOIN tempos_atracacao_paralisacao p USING (id_atracacao)
GROUP BY id_instalacao, ano
```

**Unidade:** Percentual  
**Granularidade:** Instalação/Ano

---

## 4. Módulo 2: Operações de Carga

**Fonte Principal:** `antaqdados.br_antaq_estatistico_aquaviario`

### 4.1 Indicadores de Volume

#### IND-2.01: Total Carga Movimentada `[UNCTAD]`

```sql
SELECT 
  id_instalacao,
  ano,
  SUM(peso_carga_bruta) AS tonelagem_total
FROM v_carga_validada
GROUP BY id_instalacao, ano
```

**Unidade:** Toneladas  
**Granularidade:** Instalação/Ano

---

#### IND-2.02: TEUs Movimentados `[UNCTAD]`

```sql
SELECT 
  id_instalacao,
  ano,
  SUM(teus) AS total_teus
FROM carga_conteinerizada
GROUP BY id_instalacao, ano
```

**Unidade:** TEUs  
**Granularidade:** Instalação/Ano

---

#### IND-2.03: Total Passageiros Ferry `[UNCTAD]`

```sql
SELECT 
  id_instalacao,
  ano,
  SUM(CASE WHEN tipo_navegacao = 'TRAVESSIA' THEN qtd_passageiros ELSE 0 END) AS passageiros_ferry
FROM v_atracacao_validada
GROUP BY id_instalacao, ano
```

**Unidade:** Contagem  
**Granularidade:** Instalação/Ano

---

#### IND-2.04: Total Passageiros Cruzeiro `[UNCTAD]`

```sql
SELECT 
  id_instalacao,
  ano,
  SUM(CASE WHEN tipo_navegacao = 'CRUZEIRO' THEN qtd_passageiros ELSE 0 END) AS passageiros_cruzeiro
FROM v_atracacao_validada
GROUP BY id_instalacao, ano
```

**Unidade:** Contagem  
**Granularidade:** Instalação/Ano

---

#### IND-2.05: Carga Média por Atracação `[UNCTAD]`

```sql
SELECT 
  id_instalacao,
  ano,
  SUM(peso_carga_bruta) / NULLIF(COUNT(DISTINCT id_atracacao), 0) AS carga_media_atracacao
FROM v_carga_validada
GROUP BY id_instalacao, ano
```

**Unidade:** Toneladas/Atracação  
**Granularidade:** Instalação/Ano

---

### 4.2 Indicadores de Produtividade

#### IND-2.06: Produtividade Bruta (ton/h) `[UNCTAD]`

```sql
SELECT 
  c.id_instalacao,
  c.ano,
  SUM(c.peso_carga_bruta) / NULLIF(SUM(t.tempo_operacao), 0) AS produtividade_ton_hora
FROM v_carga_validada c
JOIN tempos_atracacao t USING (id_atracacao)
GROUP BY c.id_instalacao, c.ano
```

**Unidade:** Toneladas/Hora  
**Granularidade:** Instalação/Ano

---

#### IND-2.07: Produtividade Granel Sólido `[UNCTAD]`

```sql
SELECT 
  c.id_instalacao,
  c.ano,
  SUM(c.peso_carga_bruta) / NULLIF(SUM(t.tempo_operacao), 0) AS produtividade_granel_solido
FROM v_carga_validada c
JOIN tempos_atracacao t USING (id_atracacao)
WHERE c.tipo_carga = 'GRANEL SOLIDO'
GROUP BY c.id_instalacao, c.ano
```

**Unidade:** Toneladas/Hora  
**Granularidade:** Instalação/Ano

---

#### IND-2.08: Produtividade Granel Líquido `[UNCTAD]`

```sql
SELECT 
  c.id_instalacao,
  c.ano,
  SUM(c.peso_carga_bruta) / NULLIF(SUM(t.tempo_operacao), 0) AS produtividade_granel_liquido
FROM v_carga_validada c
JOIN tempos_atracacao t USING (id_atracacao)
WHERE c.tipo_carga = 'GRANEL LIQUIDO'
GROUP BY c.id_instalacao, c.ano
```

**Unidade:** Toneladas/Hora  
**Granularidade:** Instalação/Ano

---

#### IND-2.09: Movimentos/Hora Contêiner (LPSPH) `[UNCTAD]`

```sql
SELECT 
  c.id_instalacao,
  c.ano,
  SUM(c.qtd_movimentacoes) / NULLIF(SUM(t.tempo_operacao), 0) AS lifts_per_ship_hour
FROM carga_conteinerizada c
JOIN tempos_atracacao t USING (id_atracacao)
GROUP BY c.id_instalacao, c.ano
```

**Unidade:** Movimentos/Hora  
**Granularidade:** Instalação/Ano

---

### 4.3 Indicadores de Utilização

#### IND-2.10: Toneladas por Hectare `[UNCTAD]`

```sql
SELECT 
  c.id_instalacao,
  c.ano,
  SUM(c.peso_carga_bruta) / NULLIF(i.area_total_m2 / 10000, 0) AS ton_por_hectare
FROM v_carga_validada c
JOIN instalacao_origem i USING (id_instalacao)
GROUP BY c.id_instalacao, c.ano, i.area_total_m2
```

**Unidade:** Toneladas/Hectare  
**Granularidade:** Instalação/Ano

---

#### IND-2.11: Toneladas por Metro de Cais `[UNCTAD]`

```sql
SELECT 
  c.id_instalacao,
  c.ano,
  SUM(c.peso_carga_bruta) / NULLIF(i.extensao_cais_m, 0) AS ton_por_metro_cais
FROM v_carga_validada c
JOIN instalacao_origem i USING (id_instalacao)
GROUP BY c.id_instalacao, c.ano, i.extensao_cais_m
```

**Unidade:** Toneladas/Metro  
**Granularidade:** Instalação/Ano

---

#### IND-2.12: Mix de Carga

```sql
SELECT 
  id_instalacao,
  ano,
  tipo_carga,
  SUM(peso_carga_bruta) AS tonelagem,
  SUM(peso_carga_bruta) * 100.0 / SUM(SUM(peso_carga_bruta)) OVER (PARTITION BY id_instalacao, ano) AS percentual
FROM v_carga_validada
GROUP BY id_instalacao, ano, tipo_carga
```

**Unidade:** Percentual por tipo  
**Granularidade:** Instalação/Ano/Tipo

---

#### IND-2.13: Sazonalidade Mensal

```sql
WITH media_anual AS (
  SELECT id_instalacao, ano, AVG(tonelagem_mes) AS media
  FROM (
    SELECT id_instalacao, ano, mes, SUM(peso_carga_bruta) AS tonelagem_mes
    FROM v_carga_validada
    GROUP BY id_instalacao, ano, mes
  )
  GROUP BY id_instalacao, ano
)
SELECT 
  c.id_instalacao,
  c.ano,
  c.mes,
  SUM(c.peso_carga_bruta) / NULLIF(m.media, 0) * 100 AS indice_sazonalidade
FROM v_carga_validada c
JOIN media_anual m USING (id_instalacao, ano)
GROUP BY c.id_instalacao, c.ano, c.mes, m.media
```

**Unidade:** Índice (100 = média)  
**Granularidade:** Instalação/Ano/Mês

---

## 5. Módulo 3: Recursos Humanos

**Fonte Principal:** `basedosdados.br_me_rais.microdados_vinculos`

### 5.1 Filtro Base - CNAEs Portuários

```sql
-- Usar em todas as queries deste módulo
WHERE cnae_2_subclasse IN (
  '5231101', '5231102', '5231103', '5011401', '5011402',
  '5012201', '5012202', '5021101', '5021102', '5022001',
  '5022002', '5030101', '5030102', '5030103', '5091201',
  '5091202', '5099801', '5099899', '5232000', '5239701',
  '5239799', '5250801', '5250802', '5250804'
)
```

---

#### IND-3.01: Empregos Diretos Portuários `[UNCTAD]`

```sql
SELECT 
  id_municipio,
  ano,
  COUNT(*) AS empregos_portuarios
FROM basedosdados.br_me_rais.microdados_vinculos
WHERE cnae_2_subclasse IN (/* CNAEs portuários */)
  AND vinculo_ativo_3112 = 1
GROUP BY id_municipio, ano
```

**Unidade:** Contagem  
**Granularidade:** Município/Ano

---

#### IND-3.02: Paridade de Gênero Geral `[UNCTAD]`

```sql
SELECT 
  id_municipio,
  ano,
  SUM(CASE WHEN sexo = 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS percentual_feminino
FROM basedosdados.br_me_rais.microdados_vinculos
WHERE cnae_2_subclasse IN (/* CNAEs portuários */)
  AND vinculo_ativo_3112 = 1
GROUP BY id_municipio, ano
```

**Unidade:** Percentual  
**Granularidade:** Município/Ano

---

#### IND-3.03: Paridade por Categoria Profissional `[UNCTAD]`

```sql
SELECT 
  id_municipio,
  ano,
  CASE 
    WHEN SUBSTR(cbo_2002, 1, 1) IN ('1', '2') THEN 'GESTAO_TECNICO'
    WHEN SUBSTR(cbo_2002, 1, 1) IN ('3', '4') THEN 'ADMINISTRATIVO'
    ELSE 'OPERACIONAL'
  END AS categoria,
  SUM(CASE WHEN sexo = 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS percentual_feminino
FROM basedosdados.br_me_rais.microdados_vinculos
WHERE cnae_2_subclasse IN (/* CNAEs portuários */)
  AND vinculo_ativo_3112 = 1
GROUP BY id_municipio, ano, categoria
```

**Unidade:** Percentual por categoria  
**Granularidade:** Município/Ano/Categoria

---

#### IND-3.04: Taxa de Emprego Temporário `[UNCTAD]`

```sql
SELECT 
  id_municipio,
  ano,
  SUM(CASE WHEN tipo_vinculo IN (/* códigos temporários */) THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS taxa_temporario
FROM basedosdados.br_me_rais.microdados_vinculos
WHERE cnae_2_subclasse IN (/* CNAEs portuários */)
  AND vinculo_ativo_3112 = 1
GROUP BY id_municipio, ano
```

**Unidade:** Percentual  
**Granularidade:** Município/Ano

---

#### IND-3.05: Salário Médio Setor Portuário `[UNCTAD]`

```sql
SELECT 
  id_municipio,
  ano,
  AVG(valor_remuneracao_media) AS salario_medio
FROM basedosdados.br_me_rais.microdados_vinculos
WHERE cnae_2_subclasse IN (/* CNAEs portuários */)
  AND vinculo_ativo_3112 = 1
GROUP BY id_municipio, ano
```

**Unidade:** R$ (valores nominais - deflacionar)  
**Granularidade:** Município/Ano

---

#### IND-3.06: Massa Salarial Portuária `[UNCTAD]`

```sql
SELECT 
  id_municipio,
  ano,
  SUM(valor_remuneracao_media * 12) AS massa_salarial_anual
FROM basedosdados.br_me_rais.microdados_vinculos
WHERE cnae_2_subclasse IN (/* CNAEs portuários */)
  AND vinculo_ativo_3112 = 1
GROUP BY id_municipio, ano
```

**Unidade:** R$/ano  
**Granularidade:** Município/Ano

---

#### IND-3.07: Produtividade (ton/empregado) `[UNCTAD]`

```sql
-- Requer JOIN com dados ANTAQ via id_municipio
SELECT 
  r.id_municipio,
  r.ano,
  a.tonelagem_total / NULLIF(r.empregos_portuarios, 0) AS ton_por_empregado
FROM (
  SELECT id_municipio, ano, COUNT(*) AS empregos_portuarios
  FROM basedosdados.br_me_rais.microdados_vinculos
  WHERE cnae_2_subclasse IN (/* CNAEs portuários */)
  GROUP BY id_municipio, ano
) r
JOIN (
  SELECT id_municipio, ano, SUM(peso_carga_bruta) AS tonelagem_total
  FROM v_carga_validada
  GROUP BY id_municipio, ano
) a USING (id_municipio, ano)
```

**Unidade:** Toneladas/Empregado  
**Granularidade:** Município/Ano

---

#### IND-3.08: Receita por Empregado (proxy) `[UNCTAD]`

```sql
SELECT 
  r.id_municipio,
  r.ano,
  p.pib / NULLIF(r.empregos_portuarios, 0) AS pib_por_empregado_portuario
FROM (
  SELECT id_municipio, ano, COUNT(*) AS empregos_portuarios
  FROM basedosdados.br_me_rais.microdados_vinculos
  WHERE cnae_2_subclasse IN (/* CNAEs portuários */)
  GROUP BY id_municipio, ano
) r
JOIN basedosdados.br_ibge_pib.municipio p USING (id_municipio, ano)
```

**Unidade:** R$/Empregado  
**Granularidade:** Município/Ano

---

#### IND-3.09: Distribuição por Escolaridade

```sql
SELECT 
  id_municipio,
  ano,
  grau_instrucao,
  COUNT(*) AS qtd,
  COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY id_municipio, ano) AS percentual
FROM basedosdados.br_me_rais.microdados_vinculos
WHERE cnae_2_subclasse IN (/* CNAEs portuários */)
  AND vinculo_ativo_3112 = 1
GROUP BY id_municipio, ano, grau_instrucao
```

**Unidade:** Percentual por faixa  
**Granularidade:** Município/Ano/Escolaridade

---

#### IND-3.10: Idade Média

```sql
SELECT 
  id_municipio,
  ano,
  AVG(idade) AS idade_media
FROM basedosdados.br_me_rais.microdados_vinculos
WHERE cnae_2_subclasse IN (/* CNAEs portuários */)
  AND vinculo_ativo_3112 = 1
GROUP BY id_municipio, ano
```

**Unidade:** Anos  
**Granularidade:** Município/Ano

---

#### IND-3.11: Variação Anual de Empregos

```sql
WITH empregos_ano AS (
  SELECT id_municipio, ano, COUNT(*) AS empregos
  FROM basedosdados.br_me_rais.microdados_vinculos
  WHERE cnae_2_subclasse IN (/* CNAEs portuários */)
  GROUP BY id_municipio, ano
)
SELECT 
  a.id_municipio,
  a.ano,
  (a.empregos - b.empregos) * 100.0 / NULLIF(b.empregos, 0) AS variacao_percentual
FROM empregos_ano a
JOIN empregos_ano b ON a.id_municipio = b.id_municipio AND a.ano = b.ano + 1
```

**Unidade:** Percentual  
**Granularidade:** Município/Ano

---

#### IND-3.12: Participação no Emprego Local

```sql
SELECT 
  p.id_municipio,
  p.ano,
  p.empregos_portuarios * 100.0 / NULLIF(t.empregos_totais, 0) AS participacao_emprego_local
FROM (
  SELECT id_municipio, ano, COUNT(*) AS empregos_portuarios
  FROM basedosdados.br_me_rais.microdados_vinculos
  WHERE cnae_2_subclasse IN (/* CNAEs portuários */)
  GROUP BY id_municipio, ano
) p
JOIN (
  SELECT id_municipio, ano, COUNT(*) AS empregos_totais
  FROM basedosdados.br_me_rais.microdados_vinculos
  GROUP BY id_municipio, ano
) t USING (id_municipio, ano)
```

**Unidade:** Percentual  
**Granularidade:** Município/Ano

---

## 6. Módulo 4: Comércio Exterior

**Fonte Principal:** `basedosdados.br_me_comex_stat`

> ⚠️ **AVISO**: A SECEX não valida oficialmente estatísticas por porto. Usar como estimativa técnica.

---

#### IND-4.01: Valor FOB Exportações (US$)

```sql
SELECT 
  id_municipio,
  ano,
  SUM(valor_fob_dolar) AS valor_exportacoes_usd
FROM basedosdados.br_me_comex_stat.municipio_exportacao
GROUP BY id_municipio, ano
```

**Unidade:** US$  
**Granularidade:** Município/Ano

---

#### IND-4.02: Valor FOB Importações (US$)

```sql
SELECT 
  id_municipio,
  ano,
  SUM(valor_fob_dolar) AS valor_importacoes_usd
FROM basedosdados.br_me_comex_stat.municipio_importacao
GROUP BY id_municipio, ano
```

**Unidade:** US$  
**Granularidade:** Município/Ano

---

#### IND-4.03: Balança Comercial do Porto

```sql
SELECT 
  COALESCE(e.id_municipio, i.id_municipio) AS id_municipio,
  COALESCE(e.ano, i.ano) AS ano,
  COALESCE(e.exportacoes, 0) - COALESCE(i.importacoes, 0) AS balanca_comercial_usd
FROM (
  SELECT id_municipio, ano, SUM(valor_fob_dolar) AS exportacoes
  FROM basedosdados.br_me_comex_stat.municipio_exportacao
  GROUP BY id_municipio, ano
) e
FULL OUTER JOIN (
  SELECT id_municipio, ano, SUM(valor_fob_dolar) AS importacoes
  FROM basedosdados.br_me_comex_stat.municipio_importacao
  GROUP BY id_municipio, ano
) i USING (id_municipio, ano)
```

**Unidade:** US$  
**Granularidade:** Município/Ano

---

#### IND-4.04 a IND-4.10

*(Queries similares para peso líquido, valor médio/kg, concentração por país/NCM, variação anual e market share)*

---

## 7. Módulo 5: Impacto Econômico Regional

**Fontes:** IBGE + ANTAQ + RAIS + Comex

> 📊 **METODOLOGIA**: Indicadores descritivos e correlacionais apenas. Não são calculados multiplicadores I-O.

### 7.1 Indicadores Estruturais

#### IND-5.01: PIB Municipal

```sql
SELECT 
  id_municipio,
  ano,
  pib AS pib_municipal
FROM basedosdados.br_ibge_pib.municipio
```

**Unidade:** R$ (preços correntes)  
**Granularidade:** Município/Ano

---

#### IND-5.02: PIB per Capita

```sql
SELECT 
  p.id_municipio,
  p.ano,
  p.pib / NULLIF(pop.populacao, 0) AS pib_per_capita
FROM basedosdados.br_ibge_pib.municipio p
JOIN basedosdados.br_ibge_populacao.municipio pop USING (id_municipio, ano)
```

**Unidade:** R$/habitante  
**Granularidade:** Município/Ano

---

#### IND-5.03: População Municipal

```sql
SELECT 
  id_municipio,
  ano,
  populacao
FROM basedosdados.br_ibge_populacao.municipio
```

**Unidade:** Habitantes  
**Granularidade:** Município/Ano

---

#### IND-5.04: PIB Setorial - Serviços (%)

```sql
SELECT 
  id_municipio,
  ano,
  vab_servicos * 100.0 / NULLIF(pib, 0) AS pib_servicos_percentual
FROM basedosdados.br_ibge_pib.municipio
```

**Unidade:** Percentual  
**Granularidade:** Município/Ano

---

#### IND-5.05: PIB Setorial - Indústria (%)

```sql
SELECT 
  id_municipio,
  ano,
  vab_industria * 100.0 / NULLIF(pib, 0) AS pib_industria_percentual
FROM basedosdados.br_ibge_pib.municipio
```

**Unidade:** Percentual  
**Granularidade:** Município/Ano

---

### 7.2 Indicadores de Intensidade Portuária

#### IND-5.06: Intensidade Portuária (ton/PIB)

```sql
SELECT 
  a.id_municipio,
  a.ano,
  a.tonelagem / NULLIF(p.pib, 0) AS intensidade_portuaria
FROM (
  SELECT id_municipio, ano, SUM(peso_carga_bruta) AS tonelagem
  FROM v_carga_validada
  GROUP BY id_municipio, ano
) a
JOIN basedosdados.br_ibge_pib.municipio p USING (id_municipio, ano)
```

**Unidade:** Toneladas/R$  
**Granularidade:** Município/Ano

---

#### IND-5.07: Intensidade Comercial

```sql
SELECT 
  c.id_municipio,
  c.ano,
  (c.exportacoes + c.importacoes) / NULLIF(p.pib, 0) AS intensidade_comercial
FROM (
  SELECT 
    COALESCE(e.id_municipio, i.id_municipio) AS id_municipio,
    COALESCE(e.ano, i.ano) AS ano,
    COALESCE(e.valor, 0) AS exportacoes,
    COALESCE(i.valor, 0) AS importacoes
  FROM (SELECT id_municipio, ano, SUM(valor_fob_dolar) AS valor FROM municipio_exportacao GROUP BY 1,2) e
  FULL JOIN (SELECT id_municipio, ano, SUM(valor_fob_dolar) AS valor FROM municipio_importacao GROUP BY 1,2) i USING (id_municipio, ano)
) c
JOIN basedosdados.br_ibge_pib.municipio p USING (id_municipio, ano)
```

**Unidade:** Razão (US$/R$)  
**Granularidade:** Município/Ano

---

#### IND-5.08: Concentração de Emprego Portuário

```sql
-- Ver IND-3.12
```

**Unidade:** Percentual  
**Granularidade:** Município/Ano

---

#### IND-5.09: Concentração Salarial Portuária

```sql
SELECT 
  p.id_municipio,
  p.ano,
  p.massa_salarial_port * 100.0 / NULLIF(t.massa_salarial_total, 0) AS concentracao_salarial
FROM (
  SELECT id_municipio, ano, SUM(valor_remuneracao_media * 12) AS massa_salarial_port
  FROM basedosdados.br_me_rais.microdados_vinculos
  WHERE cnae_2_subclasse IN (/* CNAEs portuários */)
  GROUP BY id_municipio, ano
) p
JOIN (
  SELECT id_municipio, ano, SUM(valor_remuneracao_media * 12) AS massa_salarial_total
  FROM basedosdados.br_me_rais.microdados_vinculos
  GROUP BY id_municipio, ano
) t USING (id_municipio, ano)
```

**Unidade:** Percentual  
**Granularidade:** Município/Ano

---

### 7.3 Indicadores de Variação Temporal

#### IND-5.10: Crescimento PIB Municipal (%)

```sql
WITH pib_ano AS (
  SELECT id_municipio, ano, pib
  FROM basedosdados.br_ibge_pib.municipio
)
SELECT 
  a.id_municipio,
  a.ano,
  (a.pib - b.pib) * 100.0 / NULLIF(b.pib, 0) AS crescimento_pib_percentual
FROM pib_ano a
JOIN pib_ano b ON a.id_municipio = b.id_municipio AND a.ano = b.ano + 1
```

**Unidade:** Percentual  
**Granularidade:** Município/Ano

---

#### IND-5.11 a IND-5.13

*(Queries similares para crescimento de tonelagem, empregos e comércio exterior)*

---

### 7.4 Indicadores Correlacionais

> ⚠️ **NOTA**: Correlações não implicam causalidade. Calcular apenas com séries de 5+ anos.

#### IND-5.14: Correlação Tonelagem × PIB

```sql
-- Usar função CORR() do BigQuery
SELECT 
  id_municipio,
  CORR(tonelagem, pib) AS correlacao_tonelagem_pib
FROM (
  SELECT 
    a.id_municipio,
    a.ano,
    a.tonelagem,
    p.pib
  FROM (
    SELECT id_municipio, ano, SUM(peso_carga_bruta) AS tonelagem
    FROM v_carga_validada
    GROUP BY id_municipio, ano
  ) a
  JOIN basedosdados.br_ibge_pib.municipio p USING (id_municipio, ano)
)
GROUP BY id_municipio
HAVING COUNT(*) >= 5  -- Mínimo 5 anos
```

**Unidade:** Coeficiente (-1 a +1)  
**Granularidade:** Município

---

#### IND-5.15: Correlação Tonelagem × Empregos

```sql
SELECT 
  id_municipio,
  CORR(tonelagem, empregos) AS correlacao_tonelagem_empregos
FROM (/* join tonelagem ANTAQ + empregos RAIS */)
GROUP BY id_municipio
HAVING COUNT(*) >= 5
```

**Unidade:** Coeficiente (-1 a +1)  
**Granularidade:** Município

---

#### IND-5.16: Correlação Comércio × PIB

```sql
SELECT 
  id_municipio,
  CORR(comercio_total, pib) AS correlacao_comercio_pib
FROM (/* join comex + pib */)
GROUP BY id_municipio
HAVING COUNT(*) >= 5
```

**Unidade:** Coeficiente (-1 a +1)  
**Granularidade:** Município

---

#### IND-5.17: Elasticidade Tonelagem/PIB

```sql
-- Regressão log-log simples: ln(tonelagem) = α + β·ln(PIB)
-- β é a elasticidade
SELECT 
  id_municipio,
  (COUNT(*) * SUM(ln_ton * ln_pib) - SUM(ln_ton) * SUM(ln_pib)) /
  NULLIF(COUNT(*) * SUM(ln_pib * ln_pib) - SUM(ln_pib) * SUM(ln_pib), 0) AS elasticidade
FROM (
  SELECT 
    id_municipio,
    LN(tonelagem) AS ln_ton,
    LN(pib) AS ln_pib
  FROM (/* join tonelagem + pib */)
  WHERE tonelagem > 0 AND pib > 0
)
GROUP BY id_municipio
HAVING COUNT(*) >= 5
```

**Unidade:** Elasticidade  
**Granularidade:** Município  
**Interpretação:** Variação % na tonelagem para cada 1% de variação no PIB

---

### 7.5 Indicadores Comparativos

#### IND-5.18: Participação no PIB Regional

```sql
SELECT 
  m.id_municipio,
  m.ano,
  m.pib * 100.0 / NULLIF(r.pib_regiao, 0) AS participacao_pib_regional
FROM basedosdados.br_ibge_pib.municipio m
JOIN (
  SELECT id_microrregiao, ano, SUM(pib) AS pib_regiao
  FROM basedosdados.br_ibge_pib.municipio
  GROUP BY id_microrregiao, ano
) r ON m.id_microrregiao = r.id_microrregiao AND m.ano = r.ano
```

**Unidade:** Percentual  
**Granularidade:** Município/Ano

---

#### IND-5.19: Crescimento Relativo ao Estado

```sql
WITH cresc_mun AS (/* crescimento PIB municipal */),
     cresc_uf AS (/* crescimento PIB estadual */)
SELECT 
  m.id_municipio,
  m.ano,
  m.crescimento - u.crescimento AS crescimento_relativo_uf
FROM cresc_mun m
JOIN cresc_uf u ON m.sigla_uf = u.sigla_uf AND m.ano = u.ano
```

**Unidade:** Pontos percentuais  
**Granularidade:** Município/Ano

---

#### IND-5.20: Razão Emprego Total/Portuário

```sql
SELECT 
  id_municipio,
  ano,
  empregos_totais / NULLIF(empregos_portuarios, 0) AS razao_emprego
FROM (/* join empregos totais + portuários */)
```

**Unidade:** Razão  
**Granularidade:** Município/Ano  
**Interpretação:** Quantos empregos totais existem para cada emprego portuário

---

#### IND-5.21: Índice de Concentração Portuária

```sql
-- Score composto normalizado (0-100)
WITH indicadores AS (
  SELECT 
    id_municipio,
    ano,
    participacao_emprego,
    intensidade_portuaria,
    participacao_pib_regional
  FROM (/* queries anteriores */)
),
normalizado AS (
  SELECT 
    id_municipio,
    ano,
    (participacao_emprego - MIN(participacao_emprego) OVER()) / 
      NULLIF(MAX(participacao_emprego) OVER() - MIN(participacao_emprego) OVER(), 0) AS norm_emprego,
    (intensidade_portuaria - MIN(intensidade_portuaria) OVER()) / 
      NULLIF(MAX(intensidade_portuaria) OVER() - MIN(intensidade_portuaria) OVER(), 0) AS norm_intensidade,
    (participacao_pib_regional - MIN(participacao_pib_regional) OVER()) / 
      NULLIF(MAX(participacao_pib_regional) OVER() - MIN(participacao_pib_regional) OVER(), 0) AS norm_pib
  FROM indicadores
)
SELECT 
  id_municipio,
  ano,
  (norm_emprego + norm_intensidade + norm_pib) / 3 * 100 AS indice_concentracao_portuaria
FROM normalizado
```

**Unidade:** Índice (0-100)  
**Granularidade:** Município/Ano

---

## 8. Módulo 6: Finanças Públicas

**Fonte Principal:** `basedosdados.br_tesouro_finbra.receitas`

> ⚠️ **LIMITAÇÃO**: Não há desagregação por setor econômico. Indicadores são contextuais.

#### IND-6.01 a IND-6.06

*(Queries para ICMS, ISS, receita total, per capita, crescimento e ICMS/tonelada)*

---

## 9. Módulo 7: Índices Sintéticos

### Metodologia de Normalização

Todos os índices usam **min-max scaling**:

```sql
valor_normalizado = (valor - MIN(valor)) / (MAX(valor) - MIN(valor)) * 100
```

#### IND-7.01: Índice de Eficiência Operacional

```sql
-- Componentes: produtividade (+), ocupação (+), ociosidade (-)
SELECT 
  id_instalacao,
  ano,
  (norm_produtividade + norm_ocupacao + (100 - norm_ociosidade)) / 3 AS indice_eficiencia
FROM (/* normalização dos componentes */)
```

---

#### IND-7.02 a IND-7.07

*(Índices de relevância, integração, concentração, ranking, benchmark e variação)*

---

## 10. CNAEs do Setor Portuário

```python
CNAES_PORTUARIOS = [
    '5231101',  # Administração da infraestrutura portuária
    '5231102',  # Atividades do operador portuário
    '5231103',  # Gestão de terminais aquaviários
    '5011401',  # Transporte marítimo de cabotagem - carga
    '5011402',  # Transporte marítimo de cabotagem - passageiros
    '5012201',  # Transporte marítimo de longo curso - carga
    '5012202',  # Transporte marítimo de longo curso - passageiros
    '5021101',  # Transporte por navegação interior de carga, municipal
    '5021102',  # Transporte por navegação interior de carga, intermunicipal
    '5022001',  # Transporte por navegação interior de passageiros, municipal
    '5022002',  # Transporte por navegação interior de passageiros, intermunicipal
    '5030101',  # Navegação de apoio marítimo
    '5030102',  # Navegação de apoio portuário
    '5030103',  # Serviço de rebocadores e empurradores
    '5091201',  # Transporte por navegação de travessia, municipal
    '5091202',  # Transporte por navegação de travessia, intermunicipal
    '5099801',  # Transporte aquaviário para passeios turísticos
    '5099899',  # Outros transportes aquaviários
    '5232000',  # Atividades de agenciamento marítimo
    '5239701',  # Serviços de praticagem
    '5239799',  # Atividades auxiliares dos transportes aquaviários
    '5250801',  # Comissaria de despachos
    '5250802',  # Atividades de despachantes aduaneiros
    '5250804',  # Organização logística do transporte de carga
]
```

---

## 11. Estrutura de Marts no BigQuery

### 11.1 Estrutura de Diretórios

```
projeto_portos/
├── marts/
│   ├── operacoes_navios/
│   │   └── mart_operacoes_navios.sql
│   ├── operacoes_carga/
│   │   └── mart_operacoes_carga.sql
│   ├── recursos_humanos/
│   │   └── mart_recursos_humanos.sql
│   ├── comercio_exterior/
│   │   └── mart_comercio_exterior.sql
│   ├── impacto_economico/
│   │   └── mart_impacto_economico.sql
│   ├── financas_publicas/
│   │   └── mart_financas_publicas.sql
│   ├── indices_sinteticos/
│   │   └── mart_indices_sinteticos.sql
│   └── unctad/
│       └── mart_unctad_port_performance.sql  # Indicadores UNCTAD consolidados
```

### 11.2 Configuração de Particionamento

```sql
-- Exemplo para mart de operações
CREATE OR REPLACE TABLE marts.operacoes_navios
PARTITION BY DATE_TRUNC(data_referencia, YEAR)
CLUSTER BY id_instalacao, id_municipio
AS (
  -- Query do mart
)
```

### 11.3 Metadados

```sql
-- Tabela de metadados dos indicadores
CREATE TABLE marts.indicadores_metadata (
  codigo_indicador STRING,
  nome STRING,
  modulo STRING,
  formula STRING,
  unidade STRING,
  granularidade STRING,
  fonte_dados STRING,
  unctad BOOL,
  data_atualizacao TIMESTAMP
)
```

---

## Changelog

| Versão | Data | Alterações |
|--------|------|------------|
| 1.0 | Dez/2025 | Versão inicial |
| 2.0 | Dez/2025 | Integração UNCTAD |
| 3.0 | Dez/2025 | Revisão Módulo 5 (metodologia descritiva-correlacional) |

---

*Documento gerado para equipe de desenvolvimento. Para dúvidas metodológicas, consultar documentação de planejamento.*
