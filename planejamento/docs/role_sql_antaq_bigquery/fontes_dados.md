# Fontes de Dados

## 1) Arrecadação Estadual/Municipal — SICONFI (Tesouro Nacional)

**Dataset BD**

SICONFI – Sistema de Informações Contábeis e Fiscais do Setor Público Brasileiro
https://basedosdados.org/dataset/5a3dec52-8740-460e-b31d-0e0347979da0?table=1d2d5e1c-45c7-4f86-9362-821086917a79

**Caminho BigQuery**

```
basedosdados.br_tesouro_finbra.receitas
```

> A Base dos Dados usa nomenclatura diferente dependendo da versão da tabela. O conjunto FINBRA/SICONFI costuma aparecer como:
> - `basedosdados.br_tesouro_finbra.despesa`
> - `basedosdados.br_tesouro_finbra.receita`
> - `basedosdados.br_tesouro_finbra.municipio_receitas` (exemplo)
>
> A tabela específica referenciada (código UUID) corresponde ao painel de receitas/ingressos, portanto o caminho correto é: `basedosdados.br_tesouro_finbra.receitas`

**Escopo (conforme BD)**

Arrecadação informada pelos estados e municípios no SICONFI.

Inclui ICMS, IPVA, ISS municipal, taxas, transferências, etc.

Periodicidade: anual (às vezes trimestral, dependendo da tabela).

**Observações técnicas**

- Falhas de reporte são comuns; BD sinaliza com `isna`/`is_valid` em algumas versões.
- Não existe granularidade "por setor", apenas por natureza da receita.

---

## 2) IPCA — Índice de Preços (deflacionamento)

**Dataset BD**

IPCA – Índice Nacional de Preços ao Consumidor Amplo (IBGE)
https://basedosdados.org/dataset/ea4d07ca-e779-4d77-bcfa-b0fd5ebea828?table=1d103367-51c7-4db4-95c5-d0c0de4c8a88

**Caminho BigQuery**

```
basedosdados.br_ibge_ipca.mes_brasil
```

**Escopo**

IPCA geral mensal — Brasil.

Possui também recortes por região metropolitana, dependendo da tabela.

**Uso esperado na aplicação**

- Construção de deflator para salários da RAIS.
- Deflação de valores monetários (PIB, arrecadação, movimentações econômicas).
- Cálculo de preços reais ao longo do tempo.

---

## 3) Censo Demográfico — IBGE

**Dataset BD**

Censo Demográfico (2010 e 2022)
https://basedosdados.org/dataset/08a1546e-251f-4546-9fe0-b1e6ab2b203d?table=cf9537b5-6198-455f-a8b0-7c762e94d79c

**Caminhos BigQuery (exemplos reais da BD)**

A BD organiza o censo em várias tabelas — exemplos típicos:

```
basedosdados.br_ibge_censo_2022.microdados
basedosdados.br_ibge_censo_2010.microdados
basedosdados.br_ibge_censo_2022.agregado_municipio
basedosdados.br_ibge_censo_2010.agregado_municipio
```

**Escopo**

Informações sociodemográficas por município e por setor censitário.

Variáveis típicas: população, escolaridade, idade, densidade, domicílios etc.

**Observações**

- Para análises socioeconômicas municipais, usar agregados por município.
- Microdados são gigantescos (bilhões de linhas) — devem ficar fora do app SAAS, servindo apenas para preprocessamentos ou análises internas.

---

## 4) PNAD Contínua (PNAD-C) — IBGE

**Dataset BD**

Pesquisa Nacional por Amostra de Domicílios Contínua
https://basedosdados.org/dataset/9fa532fb-5681-4903-b99d-01dc45fd527a?table=a04fc85d-908a-4393-b51d-1bd517a40210

**Caminhos BigQuery (exemplos reais)**

A PNAD-C é dividida em diversos módulos:

```
basedosdados.br_ibge_pnadc.microdados
basedosdados.br_ibge_pnadc.agregado_brasil
basedosdados.br_ibge_pnadc.agregado_uf
basedosdados.br_ibge_pnadc.agregado_municipio (quando disponível)
```

**Escopo**

Indicadores sobre força de trabalho: ocupação, rendimento, informalidade.

Podem complementar RAIS para análises sociais não cobertas por vínculos formais.

**Observações**

- PNAD é amostral → não confundir com RAIS (censo administrativo).
- Útil para indicadores sociais gerais, não para números absolutos de emprego formal.

---

## 5) Transporte Aquaviário — ANTAQ

**Dataset**

ANTAQ – Agência Nacional de Transportes Aquaviários (Estatístico Aquaviário)

**Caminho BigQuery**

```
antaqdados.br_antaq_estatistico_aquaviario
```

**Tabelas (origem direta)**

- `atracacao`
- `carga`
- `carga_conteinerizada`
- `carga_hidrovia`
- `carga_regiao`
- `carga_rio`
- `instalacao_origem`
- `instalacao_destino`
- `tempos_atracacao`
- `tempos_atracacao_paralisacao`
- `taxa_ocupacao`
- `taxa_ocupacao_com_carga`
- `taxa_ocupacao_to_atracacao`
- `mercadoria_carga`
- `mercadoria_carga_conteiner`
- `dicionario_dados`
- `log_validacao_mensal`

**Views curadas (preferenciais para consumo)**

- `v_atracacao_validada`
- `v_carga_validada`
- `v_carga_oficial_antaq`
- `v_carga_metodologia_oficial`
- `v_resumo_instalacoes`
- `v_resumo_integridade_referencial`
- `v_resumo_mercadorias`
- `vw_atracacao_enriched`
- `vw_carga_enriched`
- `v_analise_portuaria_1semestre_2025`
- `vw_metadados_consulta`

**Escopo**

Dados estatísticos do transporte aquaviário brasileiro: atracações, cargas (conteinerizadas, hidrovia), tempos, taxas de ocupação e mercadorias.

**Observações técnicas**

- **⚠️ OBRIGATÓRIO:** Para consultas de movimentação de carga, usar SEMPRE a view `v_carga_metodologia_oficial` com o filtro `isValidoMetodologiaANTAQ = 1`
  - Exemplo: `SELECT * FROM antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial WHERE isValidoMetodologiaANTAQ = 1`
  - Esta view aplica a metodologia oficial da ANTAQ e garante dados consistentes e validados
  - Usar o campo `vlpesocargabruta_oficial` para valores de peso
  - **NÃO usar** a tabela de origem `carga` diretamente, pois os valores não seguem a metodologia oficial

- **Aviso metodológico:** a view `v_carga_metodologia_oficial` já aplica:
  - Tipos oficiais (`FlagMCOperacaoCarga = 1`)
  - `FlagAutorizacao = 'S'`
  - `vlpesocargabruta_oficial > 0`
  - Define `data_referencia` pela desatracação
  - **Nas consultas, priorize sempre recortes por `data_referencia` em vez de `data_atracacao` ou listas de operações**

- Priorizar as views `v_*` e `vw_*` — já incorporam regras/metodologia oficial da ANTAQ
- Manter leitura read-only
- As views enriquecidas (`*_enriched`) podem conter dados adicionais para análise

---

## Resumo Consolidado

| Tema | Fonte BD (dataset) | Caminho BigQuery (US) | Uso |
|------|-------------------|------------------------|-----|
| População | IBGE | `basedosdados.br_ibge_populacao.municipio` | base demográfica municipal |
| Emprego formal | RAIS | `basedosdados.br_me_rais.microdados_vinculos` | estoque + salários anual |
| Comércio exterior | ComexStat | `basedosdados.br_me_comex_stat.municipio_exportacao` e `municipio_importacao` | FOB/peso agregados; recorte por UF/município/URF |
| → Observação porto | — | campos de unidade alfandegária (URF) | usar com cautela (não validado pela Secex) |
| Arrecadação estadual/municipal | SICONFI / FINBRA | `basedosdados.br_tesouro_finbra.receitas` | ICMS, ISS, taxas |
| IPCA | IBGE | `basedosdados.br_ibge_ipca.mes_brasil` | deflação geral |
| Censo 2010/2022 | IBGE | `basedosdados.br_ibge_censo_20xx.*` | perfil sociodemográfico |
| PNAD-C | IBGE | `basedosdados.br_ibge_pnadc.*` | renda e ocupação (amostral) |
| Transporte aquaviário | ANTAQ | `antaqdados.br_antaq_estatistico_aquaviario` | atracações, cargas, taxas de ocupação portuária |

---

## Testes de Conexão BigQuery

Data dos testes: 2025-12-26

### Resultados

| Fonte | Tabela | Status | Observações |
|-------|--------|--------|-------------|
| IPCA | `basedosdados.br_ibge_ipca.mes_brasil` | ✅ OK | Dados atualizados até 2025 |
| RAIS | `basedosdados.br_me_rais.microdados_vinculos` | ✅ OK | ~78M vínculos em 2022 |
| FINBRA Receitas | `basedosdados.br_tesouro_finbra.receitas` | ❌ **Erro 403** | Acesso negado - verificar permissões ou usar tabela alternativa |
| ANTAQ | `antaqdados.br_antaq_estatistico_aquaviario.v_carga_validada` | ✅ OK | Dados de cargas validados |
| ANTAQ | `antaqdados.br_antaq_estatistico_aquaviario.vw_atracacao_enriched` | ✅ OK | Dados de atracações enriquecidos |

### Detalhes dos Testes

**IPCA** - amostra dos dados:
```sql
SELECT * FROM `basedosdados.br_ibge_ipca.mes_brasil`
ORDER BY ano DESC, mes DESC LIMIT 10
```
Campos disponíveis: `ano`, `mes`, `indice`, `variacao_anual`, `variacao_doze_meses`, `variacao_mensal`, `variacao_semestral`, `variacao_trimestral`

**RAIS** - contagem de vínculos:
```sql
SELECT count(*) as total_vinculos
FROM `basedosdados.br_me_rais.microdados_vinculos`
WHERE ano = 2022
```
Resultado: **78.488.470 vínculos formais**

**ANTAQ** - views curadas:

Cargas validadas:
```sql
SELECT * FROM `antaqdados.br_antaq_estatistico_aquaviario.v_carga_validada` LIMIT 5
```
Campos principais: `idcarga`, `idatracacao`, `natureza_da_carga`, `vlpesocargabruta`, `qtcarga`, `teu`, `sentido`, `tipo_navegacao`, `tipo_operacao_da_carga`, `validation_status`

Atracações enriquecidas:
```sql
SELECT * FROM `antaqdados.br_antaq_estatistico_aquaviario.vw_atracacao_enriched` LIMIT 3
```
Campos principais: `idatracacao`, `data_atracacao`, `data_desatracacao`, `porto_atracacao`, `municipio`, `uf`, `regiao_geografica`, `tipo_de_operacao`, `tipo_de_navegacao_da_atracacao`, `coordenadas`

### Ações Necessárias

- [ ] Verificar permissões de acesso para `br_tesouro_finbra.receitas`
- [ ] Testar tabelas alternativas: `br_tesouro_finbra.receita`, `br_tesouro_finbra.municipio_receitas`
- [ ] Validar acesso às demais fontes ainda não testadas (ComexStat, Censo, PNAD-C)
