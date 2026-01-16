-- =====================================================
-- View Metodologia Oficial (alinhada ao critério ANTAQ)
-- =====================================================
-- Objetivo: incorporar na view oficial o critério temporal por
-- desatracação e garantir inclusão apenas de registros autorizados,
-- com pesos positivos e tipos de operação oficiais.
--
-- Execução recomendada:
--   bq query --use_legacy_sql=false < scripts/criar_view_metodologia_oficial.sql
--
-- Alvo:
--   antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial
-- =====================================================

CREATE OR REPLACE VIEW `antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial` AS
WITH carga_filtrada AS (
  SELECT *
  FROM `antaqdados.br_antaq_estatistico_aquaviario.carga`
  WHERE FlagAutorizacao = 'S'
    AND CAST(REPLACE(vlpesocargabruta, ',', '.') AS FLOAT64) > 0
    AND SAFE_CAST(FlagMCOperacaoCarga AS INT64) = 1
    AND LOWER(tipo_operacao_da_carga) IN (
      'movimentação de carga',
      'apoio',
      'longo curso exportação',
      'longo curso importação',
      'longo curso exportação com baldeação de carga estrangeira',
      'longo curso importação com baldeação de carga estrangeira',
      'cabotagem',
      'interior',
      'baldeação de carga nacional',
      'baldeação de carga estrangeira de passagem'
    )
),
carga_dedup AS (
  SELECT
    idcarga,
    ANY_VALUE(idatracacao) AS idatracacao,
    ANY_VALUE(cdmercadoria) AS cdmercadoria,
    ANY_VALUE(sentido) AS sentido,
    MAX(CAST(REPLACE(vlpesocargabruta, ',', '.') AS FLOAT64)) AS vlpesocargabruta_oficial,
    MAX(CAST(REPLACE(qtcarga, ',', '.') AS FLOAT64)) AS qtcarga_oficial,
    ANY_VALUE(teu) AS teu,
    ANY_VALUE(origem) AS origem,
    ANY_VALUE(destino) AS destino,
    ANY_VALUE(tipo_operacao_da_carga) AS tipo_operacao_da_carga,
    ANY_VALUE(FlagAutorizacao) AS FlagAutorizacao
  FROM carga_filtrada
  GROUP BY idcarga
)
SELECT
  -- Chaves e identificadores
  d.idcarga,
  d.idatracacao,
  d.cdmercadoria,
  d.sentido,

  -- Métricas oficiais deduplicadas
  d.vlpesocargabruta_oficial,
  d.qtcarga_oficial,
  d.teu,

  -- Rotas
  d.origem,
  d.destino,

  -- Atributos de atracação e localização
  a.porto_atracacao,
  a.municipio,
  a.sguf AS uf,
  a.regiao_geografica,
  a.tipo_de_navegacao_da_atracacao,
  a.data_atracacao,
  a.data_desatracacao,

  -- Critério temporal oficial: data de desatracação como referência
  COALESCE(
    DATE(SAFE_CAST(a.data_desatracacao AS TIMESTAMP)),
    DATE(SAFE_CAST(a.data_atracacao AS TIMESTAMP))
  ) AS data_referencia,
  EXTRACT(YEAR FROM COALESCE(
    DATE(SAFE_CAST(a.data_desatracacao AS TIMESTAMP)),
    DATE(SAFE_CAST(a.data_atracacao AS TIMESTAMP))
  )) AS ano,
  EXTRACT(MONTH FROM COALESCE(
    DATE(SAFE_CAST(a.data_desatracacao AS TIMESTAMP)),
    DATE(SAFE_CAST(a.data_atracacao AS TIMESTAMP))
  )) AS mes,

  -- Classificações de operação
  d.tipo_operacao_da_carga,
  d.FlagAutorizacao,

  -- Indicador de validade metodológica (alinhado ao painel)
  1 AS isValidoMetodologiaANTAQ

FROM carga_dedup d
JOIN `antaqdados.br_antaq_estatistico_aquaviario.atracacao` a
  ON d.idatracacao = a.idatracacao;

-- Notas:
-- 1) `ano` e `mes` passam a refletir a data de desatracação (critério oficial).
-- 2) `data_referencia` fica disponível para recortes temporais precisos.
-- 3) `FlagAutorizacao = 'S'` assegura integração apenas de dados validados pelo SDP.
-- 4) A lista de tipos de operação reproduz o conjunto utilizado pelo painel público da ANTAQ.
-- 5) Evitar filtros de janela de publicação (45 dias) diretamente na view; aplique-os nas consultas.
