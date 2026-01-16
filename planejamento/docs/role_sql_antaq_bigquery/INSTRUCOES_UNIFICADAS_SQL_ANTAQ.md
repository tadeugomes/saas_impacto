# Instruções Unificadas (SQL BigQuery) — Dados ANTAQ

Este documento consolida, em um único lugar, as regras e templates necessários para **construir queries SQL corretas, consistentes e rápidas** usando os dados ANTAQ no **Google BigQuery**, com foco na **metodologia oficial** (alinhamento com o painel público da ANTAQ).

## 1) Regra de Ouro (correção)

**Sempre** consulte a view metodológica oficial:

```sql
FROM `antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial`
```

### Nunca faça

- Consultar tabelas brutas diretamente:
  - `...FROM ...atracacao`
  - `...FROM ...carga`
- Reaplicar manualmente filtros metodológicos (tipos, flags, autorização) já embutidos na view.
- Converter números “na unha” em toda query (ex.: `CAST(REPLACE(vlpesocargabruta, ',', '.') AS FLOAT64)`), a não ser que você esteja **construindo a view oficial**.
- Criar joins 1:N com tabelas auxiliares que multipliquem registros (isso foi a causa raiz de divergências históricas).

## 2) O que você deve “levar” para outro projeto

### 2.1 Artefatos obrigatórios (para manter a metodologia)

- `scripts/criar_view_metodologia_oficial.sql`
  - Define o contrato do dado analítico: **deduplicação por `idcarga`**, filtros oficiais e a referência temporal correta via **`data_referencia` = desatracação** (com fallback para atracação).
- (Opcional, recomendado) `scripts/update_views_cenario_a.sql`
  - Cria `vw_carga_enriched` a partir da view oficial e adiciona `is_publicado_oficialmente` (janela de 45 dias).

### 2.2 Documentação de regra/uso (para garantir construção correta de SQL)

- `PADRAO_BIGQUERY_ANTAQ.md` (templates + regras rápidas)
- `docs/PADRAO_CALCULO_ANTAQ.md` (checklist + “proibidos”)
- (Recomendado) `docs/CASO_ESTUDO_ANTAQ.md` (por que certas queries dão errado: duplicação, flags, joins)
- (Recomendado) `docs/TABELAS.md` e `docs/VIEWS.md` (dicionário operacional)
- `metadata_query_examples.sql` (exemplos reutilizáveis)

## 3) Implantação no BigQuery (no outro projeto)

### 3.1 Pré-requisito

Você precisa ter as tabelas base carregadas no dataset alvo (ex.: `...br_antaq_estatistico_aquaviario.carga` e `...br_antaq_estatistico_aquaviario.atracacao`) com os campos usados no script da view.

### 3.2 Criar/atualizar a view oficial

Execute o script no projeto/dataset alvo:

```bash
bq query --use_legacy_sql=false < scripts/criar_view_metodologia_oficial.sql
```

### 3.3 (Opcional) Criar views “enriched”

```bash
bq query --use_legacy_sql=false < scripts/update_views_cenario_a.sql
```

## 4) Contrato da View Oficial (o que você pode assumir)

A view `v_carga_metodologia_oficial` já entrega:

- **Deduplicação por `idcarga`** (evita dupla contagem).
- `vlpesocargabruta_oficial` e `qtcarga_oficial` como **FLOAT64** (conversão feita na view).
- Filtros metodológicos embutidos (autorização, tipos oficiais, peso positivo).
- Referência temporal oficial:
  - `data_referencia` (DATE) = **desatracação** (fallback: atracação)
  - `ano` e `mes` derivados de `data_referencia`

## 5) Padrão de filtro temporal (correção + performance)

### Use SEMPRE intervalo por `data_referencia` (recomendado)

```sql
WHERE data_referencia >= DATE '2024-01-01'
  AND data_referencia <  DATE '2025-01-01'
```

Evite usar apenas:

```sql
WHERE EXTRACT(YEAR FROM data_referencia) = 2024
```

Ele é correto, mas o intervalo por data tende a ser mais amigável para otimização (e é mais fácil de parametrizar).

## 6) Padrão de agregação (evitar duplicação silenciosa)

### Contagens

- Para “quantas cargas”: `COUNT(DISTINCT idcarga)`
- Para “quantas atracações”: `COUNT(DISTINCT idatracacao)`
- Evite `COUNT(*)` como métrica “principal” (use como diagnóstico).

### Somatórios

- Volume oficial: `SUM(vlpesocargabruta_oficial)`

## 7) Templates prontos (copiar/colar)

### 7.1 Validação rápida do total anual

```sql
SELECT
  'VALIDACAO_PADRAO_ANTAQ' AS status,
  SUM(vlpesocargabruta_oficial) AS total_toneladas,
  COUNT(DISTINCT idcarga) AS cargas_unicas,
  COUNT(DISTINCT idatracacao) AS atracacoes_unicas,
  COUNT(DISTINCT porto_atracacao) AS portos_ativos
FROM `antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial`
WHERE data_referencia >= DATE '2024-01-01'
  AND data_referencia <  DATE '2025-01-01';
```

### 7.2 Top portos por volume (ano)

```sql
SELECT
  porto_atracacao,
  uf,
  SUM(vlpesocargabruta_oficial) AS toneladas,
  COUNT(DISTINCT idatracacao) AS atracacoes
FROM `antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial`
WHERE data_referencia >= DATE '2024-01-01'
  AND data_referencia <  DATE '2025-01-01'
GROUP BY porto_atracacao, uf
HAVING toneladas > 0
ORDER BY toneladas DESC
LIMIT 10;
```

### 7.3 Série mensal (correta por desatracação)

```sql
SELECT
  ano,
  mes,
  SUM(vlpesocargabruta_oficial) AS toneladas,
  COUNT(DISTINCT idcarga) AS cargas_unicas
FROM `antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial`
WHERE data_referencia >= DATE '2023-01-01'
  AND data_referencia <  DATE '2025-01-01'
GROUP BY ano, mes
ORDER BY ano, mes;
```

### 7.4 Por sentido (Embarcados/Desembarcados)

```sql
SELECT
  sentido,
  SUM(vlpesocargabruta_oficial) AS toneladas,
  COUNT(DISTINCT idcarga) AS cargas_unicas
FROM `antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial`
WHERE data_referencia >= DATE '2024-01-01'
  AND data_referencia <  DATE '2025-01-01'
GROUP BY sentido
ORDER BY toneladas DESC;
```

## 8) Janela de “publicação oficial” (45 dias)

Se você precisa **reproduzir apenas o que já está publicado/homologado** (janela de 45 dias), prefira a view:

```sql
FROM `antaqdados.br_antaq_estatistico_aquaviario.vw_carga_enriched`
WHERE is_publicado_oficialmente = 1
```

Observação: a recomendação do projeto é **não embutir** esse corte na `v_carga_metodologia_oficial`, e sim aplicá-lo quando necessário na query de consumo.

## 9) Checklist de revisão (antes de executar)

- Estou usando `v_carga_metodologia_oficial` (ou `vw_carga_enriched` quando fizer sentido)?
- Meu recorte temporal usa `data_referencia` (desatracação) com intervalo de datas?
- Minhas contagens usam `COUNT(DISTINCT ...)`?
- Eu evitei `JOIN` que multiplica linhas (1:N) sem pré-agregação/dedup?
- Eu não repliquei conversões/filtros que já são responsabilidade da view oficial?

## 10) Onde está a fonte de verdade (neste repositório)

- Metodologia/contrato: `scripts/criar_view_metodologia_oficial.sql`
- Atualização de views derivadas: `scripts/update_views_cenario_a.sql`
- Padrão de consultas: `PADRAO_BIGQUERY_ANTAQ.md` e `docs/PADRAO_CALCULO_ANTAQ.md`
- Exemplos: `metadata_query_examples.sql`
