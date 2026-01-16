-- EXEMPLOS DE CONSULTAS ENRIQUECIDAS COM METADADOS
-- ANTAQ ERP - Sistema com Dicionários de Dados Integrados

-- =====================================================
-- 1. CONSULTAS BÁSICAS COM METADADOS
-- =====================================================

-- Exemplo 1: Consultar atracação com descrições das colunas
SELECT
    a.id_atracacao,
    'Código único de identificação da atracação no sistema' as desc_id_atracacao,
    a.cd_tup,
    'Código do porto informante conforme cadastro da ANTAQ' as desc_cd_tup,
    a.porto_atracacao,
    'Nome do porto onde ocorreu a atracação' as desc_porto_atracacao,
    a.data_atracacao,
    'Data e hora exata da atracação da embarcação' as desc_data_atracacao,
    a.vl_peso_carga_bruta,
    'Peso bruto total da carga movimentada em toneladas' as desc_peso_carga
FROM `br_antaq_estatistico_aquaviario.atracacao` a
WHERE a.ano = 2024
LIMIT 5;

-- Exemplo 2: Consulta de carga com metadados dinâmicos
WITH janela_publicacao AS (
  SELECT
    DATE_SUB(CURRENT_DATE(), INTERVAL 45 DAY) AS data_limite,
    EXTRACT(YEAR FROM DATE_SUB(CURRENT_DATE(), INTERVAL 45 DAY)) AS ano_limite,
    EXTRACT(MONTH FROM DATE_SUB(CURRENT_DATE(), INTERVAL 45 DAY)) AS mes_limite
)
SELECT
    c.idcarga AS id_carga,
    (SELECT descricao FROM `br_antaq_estatistico_aquaviario.dicionario_dados`
     WHERE tabela = 'V_CARGA_METODOLOGIA_OFICIAL' AND coluna = 'IDCARGA') AS desc_id_carga,
    c.cdmercadoria,
    (SELECT descricao FROM `br_antaq_estatistico_aquaviario.dicionario_dados`
     WHERE tabela = 'V_CARGA_METODOLOGIA_OFICIAL' AND coluna = 'CDMERCADORIA') AS desc_cd_mercadoria,
    c.vlpesocargabruta_oficial,
    (SELECT descricao FROM `br_antaq_estatistico_aquaviario.dicionario_dados`
     WHERE tabela = 'V_CARGA_METODOLOGIA_OFICIAL' AND coluna = 'VLPESOCARGABRUTA_OFICIAL') AS desc_peso_carga,
    c.teu,
    (SELECT descricao FROM `br_antaq_estatistico_aquaviario.dicionario_dados`
     WHERE tabela = 'V_CARGA_METODOLOGIA_OFICIAL' AND coluna = 'TEU') AS desc_teu
FROM `br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial` c
CROSS JOIN janela_publicacao j
WHERE LOWER(c.tipo_operacao_da_carga) IN ('apoio', 'abastecimento', 'safamento', 'remoção a bordo', 'operação intermediária', 'transferência interna', 'movimentação de carga', 'longo curso exportação', 'longo curso importação', 'longo curso exportação com baldeação de carga estrangeira', 'longo curso importação com baldeação de carga estrangeira', 'cabotagem', 'interior', 'baldeação de carga nacional', 'baldeação de carga estrangeira de passagem')
  AND c.vlpesocargabruta_oficial > 0
  AND (
        CAST(c.ano AS INT64) < j.ano_limite
        OR (CAST(c.ano AS INT64) = j.ano_limite AND CAST(c.mes AS INT64) <= j.mes_limite)
      )
  AND c.ano = '2024'
LIMIT 5;

-- =====================================================
-- 2. ANÁLISE COM CATEGORIAS DE METADADOS
-- =====================================================

-- Exemplo 3: Análise temporal (usando metadados de categoria temporal)
SELECT
    'Ano da desatracação' as desc_ano,
    a.ano,
    'Mês da desatracação' as desc_mes,
    a.mes,
    'Tipo de navegação da embarcação' as desc_tipo_navegacao,
    a.tipo_navegacao_atracacao,
    (SELECT descricao FROM `br_antaq_estatistico_aquaviario.dicionario_dados`
     WHERE tabela = 'ATRACACAO' AND coluna = 'TIPODENAVEGACAODATRACACAO') as desc_tipo_navegacao,
    COUNT(*) as total_atracacoes,
    'Número total de atracações no período' as desc_total_atracacoes
FROM `br_antaq_estatistico_aquaviario.atracacao` a
WHERE a.ano = 2024
GROUP BY a.ano, a.mes, a.tipo_navegacao_atracacao
ORDER BY a.ano, a.mes;

-- Exemplo 4: Análise de métricas (usando metadados de categoria métrica)
WITH janela_publicacao AS (
  SELECT
    DATE_SUB(CURRENT_DATE(), INTERVAL 45 DAY) AS data_limite,
    EXTRACT(YEAR FROM DATE_SUB(CURRENT_DATE(), INTERVAL 45 DAY)) AS ano_limite,
    EXTRACT(MONTH FROM DATE_SUB(CURRENT_DATE(), INTERVAL 45 DAY)) AS mes_limite
)
SELECT
    'Identificador da carga' AS desc_id_carga,
    c.idcarga AS id_carga,
    'Peso bruto da carga em toneladas' AS desc_peso,
    c.vlpesocargabruta_oficial AS vl_peso_carga_bruta,
    'Natureza da carga' AS desc_natureza,
    c.natureza_carga,
    'Sentido da operação' AS desc_sentido,
    CASE WHEN LOWER(c.sentido) = 'desembarcados' THEN 'Desembarque' ELSE 'Embarque' END AS sentido_desc,
    'Tipo de navegação' AS desc_navegacao,
    c.tipo_de_navegacao_da_atracacao AS tipo_navegacao
FROM `br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial` c
CROSS JOIN janela_publicacao j
WHERE LOWER(c.tipo_operacao_da_carga) IN ('apoio', 'abastecimento', 'safamento', 'remoção a bordo', 'operação intermediária', 'transferência interna', 'movimentação de carga', 'longo curso exportação', 'longo curso importação', 'longo curso exportação com baldeação de carga estrangeira', 'longo curso importação com baldeação de carga estrangeira', 'cabotagem', 'interior', 'baldeação de carga nacional', 'baldeação de carga estrangeira de passagem')
  AND c.vlpesocargabruta_oficial > 0
  AND (
        CAST(c.ano AS INT64) < j.ano_limite
        OR (CAST(c.ano AS INT64) = j.ano_limite AND CAST(c.mes AS INT64) <= j.mes_limite)
      )
  AND c.ano = '2024'
ORDER BY c.vlpesocargabruta_oficial DESC
LIMIT 10;

-- =====================================================
-- 3. DOCUMENTAÇÃO AUTOMÁTICA
-- =====================================================

-- Exemplo 5: Gerar dicionário de dados automaticamente
SELECT
    'Tabela: ' || d.tabela as tabela_info,
    'Coluna: ' || d.coluna as coluna_info,
    'Tipo: ' || d.tipo_dado as tipo_info,
    'Descrição: ' || d.descricao as desc_completa,
    CASE
        WHEN d.valores_possiveis IS NOT NULL
        THEN 'Valores possíveis: ' || d.valores_possiveis
        ELSE 'Sem restrições de valores'
    END as valores_info,
    'Categoria: ' || d.categoria as categoria_info,
    ARRAY_TO_STRING(d.tags, ', ') as tags_info
FROM `br_antaq_estatistico_aquaviario.dicionario_dados` d
WHERE d.tabela IN ('ATRACACAO', 'CARGA')
ORDER BY d.tabela, d.coluna;

-- Exemplo 6: Relatório de qualidade de dados por categoria
SELECT
    d.categoria,
    'Categoria de metadados' as desc_categoria,
    COUNT(*) as total_colunas,
    'Total de colunas nesta categoria' as desc_total,
    STRING_AGG(DISTINCT d.tabela, ', ') as tabelas_envolvidas,
    'Tabelas que possuem colunas nesta categoria' as desc_tabelas
FROM `br_antaq_estatistico_aquaviario.dicionario_dados` d
GROUP BY d.categoria
ORDER BY total_colunas DESC;

-- =====================================================
-- 4. CONSULTAS COM VALIDAÇÃO USANDO METADADOS
-- =====================================================

-- Exemplo 7: Validar dados usando metadados de valores possíveis
WITH validacoes AS (
  SELECT
    a.cd_tup,
    d.coluna,
    d.descricao,
    d.valores_possiveis,
    CASE
      WHEN d.valores_possiveis IS NOT NULL THEN
        CASE
          WHEN REGEXP_CONTAINS(a.cd_tup, d.valores_possiveis) THEN 'Válido'
          ELSE 'Inválido'
        END
      ELSE 'Não aplicável'
    END as status_validacao
  FROM `br_antaq_estatistico_aquaviario.atracacao` a
  JOIN `br_antaq_estatistico_aquaviario.dicionario_dados` d
    ON a.cd_tup IS NOT NULL
    AND d.tabela = 'ATRACACAO'
    AND d.coluna = 'CDTUP'
  WHERE a.ano = 2024
  LIMIT 100
)
SELECT
    'Validação de dados' as desc_validacao,
    coluna,
    descricao,
    valores_possiveis,
    status_validacao,
    CASE
      WHEN status_validacao = 'Válido' THEN 'Dado conforme especificação'
      WHEN status_validacao = 'Inválido' THEN 'Dado fora do padrão esperado'
      ELSE 'Validação não aplicável a este campo'
    END as desc_status
FROM validacoes;

-- =====================================================
-- 5. ASSISTENTE DE CONSULTAS INTELIGENTE
-- =====================================================

-- Exemplo 8: Buscar colunas por palavras-chave
SELECT
    d.tabela,
    d.coluna,
    d.descricao,
    d.tipo_dado,
    'Use esta coluna para analisar ' ||
    CASE
      WHEN d.categoria = 'Temporal' THEN 'dados ao longo do tempo'
      WHEN d.categoria = 'Métrica' THEN 'medidas e quantidades'
      WHEN d.categoria = 'Identificador' THEN 'chaves de relacionamento'
      WHEN d.categoria = 'Localização' THEN 'informações geográficas'
      ELSE 'descrições e classificações'
    END as sugestao_uso,
    'Exemplo: ' || d.exemplo_consulta as exemplo_pratico
FROM `br_antaq_estatistico_aquaviario.dicionario_dados` d
WHERE LOWER(d.descricao) LIKE '%porto%'
   OR LOWER(d.descricao) LIKE '%carga%'
   OR LOWER(d.descricao) LIKE '%navega%'
ORDER BY d.tabela, d.categoria;

-- Exemplo 9: Gerar consultas automaticamente
SELECT
    '-- Consulta gerada automaticamente para ' || d.tabela as cabecalho,
    'SELECT ' || d.coluna || ' FROM `' || d.tabela || '` -- ' || d.descricao as consulta_sugerida,
    d.tipo_dado,
    d.categoria,
    CASE
      WHEN d.tipo_dado = 'TIMESTAMP' THEN 'Filtre com WHERE coluna BETWEEN "2024-01-01" AND "2024-12-31"'
      WHEN d.tipo_dado IN ('INTEGER', 'FLOAT64') THEN 'Filtre com WHERE coluna > 0 ou coluna < valor_limite'
      WHEN d.valores_possiveis IS NOT NULL THEN 'Filtre com WHERE coluna IN (' || d.valores_possiveis || ')'
      ELSE 'Filtre com WHERE coluna = "valor_desejado"'
    END as dica_filtro
FROM `br_antaq_estatistico_aquaviario.dicionario_dados` d
WHERE d.tabela = 'ATRACACAO'
  AND d.categoria IN ('Métrica', 'Temporal')
ORDER BY d.categoria, d.coluna
LIMIT 10;

-- =====================================================
-- 6. RELATÓRIOS DE GOVERNANÇA DE DADOS
-- =====================================================

-- Exemplo 10: Relatório de completude de metadados
SELECT
    d.tabela,
    COUNT(*) as total_colunas,
    COUNT(CASE WHEN d.descricao IS NOT NULL AND d.descricao != '' THEN 1 END) as colunas_com_descricao,
    COUNT(CASE WHEN d.tipo_dado IS NOT NULL THEN 1 END) as colunas_com_tipo,
    COUNT(CASE WHEN d.categoria IS NOT NULL THEN 1 END) as colunas_com_categoria,
    COUNT(CASE WHEN ARRAY_LENGTH(d.tags) > 0 THEN 1 END) as colunas_com_tags,
    ROUND(
      COUNT(CASE WHEN d.descricao IS NOT NULL AND d.descricao != '' THEN 1 END) * 100.0 / COUNT(*),
      2
    ) as pct_descricao,
    ROUND(
      COUNT(CASE WHEN d.tipo_dado IS NOT NULL THEN 1 END) * 100.0 / COUNT(*),
      2
    ) as pct_tipo,
    'Qualidade dos metadados por tabela' as desc_relatorio
FROM `br_antaq_estatistico_aquaviario.dicionario_dados` d
GROUP BY d.tabela
ORDER BY total_colunas DESC;
