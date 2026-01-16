# 📊 Estrutura de Tabelas ERP ANTAQ

## 📋 Overview

Este documento descreve em detalhes todas as tabelas do ERP ANTAQ, incluindo schemas, relacionamentos, índices e casos de uso, com foco na **metodologia oficial ANTAQ** que garante **98,6% de precisão**.

## 🎯 **IMPORTANTE: Como Usar as Tabelas**

### **⚠️ NUNCA USE TABELAS BRUTAS DIRETAMENTE!**
- ❌ `FROM atracacao` - Resultados 76% maiores
- ❌ `FROM carga` - Sem validação ANTAQ
- ❌ `FROM v_carga_oficial_antaq` - Metodologia diferente

### **✅ USE SEMPRE A VIEW OFICIAL:**
```sql
-- Padro Obrigatorio
FROM antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial
WHERE isValidoMetodologiaANTAQ = 1
```

## 🗃️ Catálogo Completo de Tabelas

### **Tabelas Principais (Core Business)**

#### 1. `atracacao` - Atracações Portuárias

**Descrição**: Registro de todas as operações de atracação de embarcações nos portos brasileiros.

| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| `IDAtracacao` | STRING | ID único da atracação (PK) | `ATR0001234567` |
| `CDInstalacaoPortuaria` | STRING | Código da instalação portuária | `BRSSZ` |
| `CDTPInstalacaoPortuaria` | STRING | Tipo da instalação | `1` |
| `CDBerco` | STRING | Identificação do berço | `B001` |
| `CDPortoBase` | STRING | Código do porto base | `BRSSZ` |
| `TmInicioDaAtracacao` | DATETIME | Início da atracação | `2024-03-15 08:30:00` |
| `TSFimDaAtracacao` | DATETIME | Fim da atracação | `2024-03-15 14:45:00` |
| `TmInicioOperacao` | DATETIME | Início das operações | `2024-03-15 09:15:00` |
| `TSFimOperacao` | DATETIME | Fim das operações | `2024-03-15 13:30:00` |
| `CDTipoNavegacaoAtracacao` | STRING | Tipo de navegação | `1` |
| `NMTripulante` | STRING | Nome do tripulante responsável | `JOÃO SILVA` |
| `CDMandato` | STRING | Mandato da atracação | `2024` |

**Índices**: `IDAtracacao` (PK), `CDInstalacaoPortuaria`, `TSFimDaAtracacao`

**Volume**: 1,259,410 registros

#### 2. `carga` - Movimentação de Cargas

**Descrição**: Registro detalhado de todas as movimentações de carga nos portos.

| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| `IDCarga` | STRING | ID único da carga (PK) | `CAR00012345678` |
| `IDAtracacao` | STRING | FK para atracação | `ATR0001234567` |
| `CDMercadoria` | STRING | Código da mercadoria | `001234` |
| `CDTPCarga` | STRING | Tipo da carga | `1` |
| `CDNaturezaCarga` | STRING | Natureza da carga | `1` |
| `CDTPTipoOperacaoCarga` | STRING | Tipo de operação | `1` |
| `CDsentidoCarga` | STRING | Sentido da carga | `1` |
| `QTCarga` | FLOAT64 | Quantidade da carga | `1500.50` |
| `VLPesoCargaBruta` | FLOAT64 | Peso bruto em toneladas | `1250.75` |
| `CDTEUCarga` | STRING | TEU (se aplicável) | `NULL` |
| `origem` | STRING | Código de origem | `BR` |
| `destino` | STRING | Código de destino | `US` |

**Índices**: `IDCarga` (PK), `IDAtracacao` (FK), `CDMercadoria`

**Volume**: 60,786,676 registros

### **Tabelas Secundárias (Analytics)**

#### 3. `carga_hidrovia` - Cargas por Hidrovia

**Descrição**: Dados de movimentação agregados por hidrovia.

| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| `IDCarga` | STRING | FK para carga | `CAR00012345678` |
| `regiao_hidrografica` | STRING | Região hidrográfica | `Bacia do Amazonas` |
| `valormovimentado` | FLOAT64 | Valor movimentado | `150000.00` |

**Volume**: 8,313,600 registros

#### 4. `carga_rio` - Cargas por Rio

**Descrição**: Dados de movimentação específicos por rio.

| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| `IDCarga` | STRING | FK para carga | `CAR00012345678` |
| `nome_rio` | STRING | Nome do rio | `Rio Amazonas` |
| `trecho` | STRING | Trecho do rio | `Trecho 1` |
| `valormovimentado` | FLOAT64 | Valor movimentado | `75000.00` |

**Volume**: 5,836,455 registros

#### 5. `tempos_atracacao_paralisacao` - Tempos de Paralização

**Descrição**: Métricas de tempo de paralização de embarcações.

| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| `IDAtracacao` | STRING | FK para atracação | `ATR0001234567` |
| `tempos_paralisacao` | FLOAT64 | Horas de paralização | `12.5` |
| `motivo_paralisacao` | STRING | Código do motivo | `001` |
| `custo_paralisacao` | FLOAT64 | Custo estimado | `5000.00` |

**Volume**: 1,250,749 registros

#### 6. `taxa_ocupacao` - Taxa de Ocupação Portuária

**Descrição**: Índices de ocupação das instalações portuárias.

| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| `CDInstalacaoPortuaria` | STRING | Instalação portuária | `BRSSZ` |
| `ano` | INTEGER | Ano de referência | `2024` |
| `mes` | INTEGER | Mês de referência | `3` |
| `taxa_ocupacao` | FLOAT64 | Percentual de ocupação | `85.5` |
| `capacidade` | FLOAT64 | Capacidade máxima | `1000.0` |
| `utilizado` | FLOAT64 | Espaço utilizado | `855.0` |

**Volume**: 1,774,400 registros

#### 7. `taxa_ocupacao_com_carga` - Taxa com Carga

**Descrição**: Taxa de ocupação considerando cargas em processo.

| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| `CDInstalacaoPortuaria` | STRING | Instalação portuária | `BRSSZ` |
| `ano` | INTEGER | Ano de referência | `2024` |
| `mes` | INTEGER | Mês de referência | `3` |
| `taxa_com_carga` | FLOAT64 | Taxa com carga ativa | `92.3` |
| `taxa_sem_carga` | FLOAT64 | Taxa sem carga | `78.6` |

**Volume**: 1,774,400 registros

#### 8. `taxa_ocupacao_to_atracacao` - Taxa TO Atracação

**Descrição**: Taxa de ocupação por tempo de atracação.

| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| `CDInstalacaoPortuaria` | STRING | Instalação portuária | `BRSSZ` |
| `tempo_atracacao_medio` | FLOAT64 | Tempo médio (horas) | `24.5` |
| `taxa_ocupacao_tempo` | FLOAT64 | Taxa por tempo | `76.8` |
| `eficiencia_operacional` | FLOAT64 | Índice de eficiência | `0.85` |

**Volume**: 1,878,378 registros

### **Tabelas de Referência (Master Data)**

#### 9. `instalacao_origem` - Instalações de Origem

**Descrição**: Catálogo de instalações portuárias de origem.

| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| `origem` | STRING | Código (PK) | `BRSSZ` |
| `cd_tup_origem` | STRING | Código TUP | `BRSSZ001` |
| `nome` | STRING | Nome completo | `Porto de Santos` |
| `cidade` | STRING | Cidade | `Santos` |
| `uf` | STRING | Estado | `SP` |
| `pais` | STRING | País | `Brasil` |
| `regiao_hidrografica` | STRING | Região hidrográfica | `Sudeste` |
| `bloco_economico` | STRING | Bloco econômico | `América do Sul` |

**Volume**: 15 registros

#### 10. `instalacao_destino` - Instalações de Destino

**Descrição**: Catálogo de instalações portuárias de destino.

| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| `destino` | STRING | Código (PK) | `USNYC` |
| `cd_tup_destino` | STRING | Código TUP | `USNYC001` |
| `nome` | STRING | Nome completo | `Porto de Nova York` |
| `cidade` | STRING | Cidade | `Nova York` |
| `uf` | STRING | Estado | `NY` |
| `pais` | STRING | País | `Estados Unidos` |
| `regiao_hidrografica` | STRING | Região hidrográfica | `América do Norte` |
| `bloco_economico` | STRING | Bloco econômico | `América do Norte` |

**Volume**: 16 registros

#### 11. `mercadoria_carga` - Catálogo de Mercadorias

**Descrição**: Catálogo completo de mercadorias transportadas.

| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| `cd_mercadoria` | STRING | Código (PK) | `001234` |
| `nome_mercadoria` | STRING | Nome da mercadoria | `Minério de Ferro` |
| `grupo_mercadoria` | STRING | Grupo | `Minerais` |
| `subgrupo_mercadoria` | STRING | Subgrupo | `Minérios Metálicos` |
| `periculosidade` | STRING | Classe de periculosidade | `Não Perigoso` |
| `unidade_medida` | STRING | Unidade padrão | `TON` |

**Volume**: 1,403 registros

### **Tabelas Vazias (Configuradas para Futuro Uso)**

#### 12. `carga_conteinerizada` - Cargas Conteinerizadas

**Descrição**: Movimentação específica de conteineres.
- **Status**: Configurada para produção
- **Volume**: 0 registros (limpa)
- **Schema**: Pronto para carga de dados reais

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `idcarga` | STRING | FK para carga |
| `cdmercadoriaconteinerizada` | STRING | Código do conteiner |
| `vlpesocargaconteinerizada` | FLOAT64 | Peso do conteiner |

#### 13. `carga_regiao` - Cargas por Região

**Descrição**: Dados agregados por região geográfica.
- **Status**: Configurada para produção
- **Volume**: 0 registros (limpa)
- **Schema**: Pronto para carga de dados reais

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `idcarga` | STRING | FK para carga |
| `regiao_hidrografica` | STRING | Região |
| `valormovimentado` | FLOAT64 | Valor movimentado |

#### 14. `tempos_atracacao` - Tempos de Atracação

**Descrição**: Métricas detalhadas de tempo de atracação.
- **Status**: Configurada para produção
- **Volume**: 0 registros (limpa)
- **Schema**: Pronto para carga de dados reais

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `idatracacao` | STRING | FK para atracação |
| `tesperaatracacao` | FLOAT64 | Tempo de espera |
| `tesperainicioop` | FLOAT64 | Espera início operação |
| `toperacao` | FLOAT64 | Tempo operação |
| `tesperadesatracacao` | FLOAT64 | Espera desatracação |
| `tatracado` | FLOAT64 | Tempo atracado |
| `testadia` | FLOAT64 | Tempo total de estadia |

## 🔗 Relacionamentos e Chaves

### **Chaves Primárias (PK)**
- `atracacao.IDAtracacao`
- `carga.IDCarga`
- `instalacao_origem.origem`
- `instalacao_destino.destino`
- `mercadoria_carga.cd_mercadoria`

### **Chaves Estrangeiras (FK)**
- `carga.IDAtracacao` → `atracacao.IDAtracacao`
- `carga.CDMercadoria` → `mercadoria_carga.cd_mercadoria`
- `carga.origem` → `instalacao_origem.origem`
- `carga.destino` → `instalacao_destino.destino`

### **Integridade Referencial**
```sql
-- Verificação de integridade
SELECT
    'FK_Atracacao_Carga' as relationship,
    COUNT(*) as valid_relations,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM carga), 2) as integrity_percentage
FROM antaqdados.br_antaq_estatistico_aquaviario.carga c
JOIN antaqdados.br_antaq_estatistico_aquaviario.atracacao a
    ON c.IDAtracacao = a.IDAtracacao;
```

## 📊 Volume de Dados por Categoria

| Categoria | Tabelas | Registros | Percentual |
|-----------|---------|-----------|------------|
| **Principais** | 2 | 62,046,086 | 74.8% |
| **Secundárias** | 6 | 20,827,982 | 25.1% |
| **Referência** | 3 | 1,434 | 0.0% |
| **Vazias** | 3 | 0 | 0.0% |
| **Total** | **14** | **82,875,502** | **100%** |

## 🔄 Ciclo de Vida dos Dados

### **Atualizações**
- **Dados Históricos**: Não modificáveis (append-only)
- **Dados de Referência**: Atualizações mensais
- **Taxas de Ocupação**: Atualizações diárias
- **Dados em Tempo Real**: Streaming quando disponível

### **Retenção**
- **Dados Operacionais**: 10 anos
- **Dados Analíticos**: Permanente
- **Logs de Sistema**: 90 dias
- **Backups**: 7 anos

---

**Última atualização: Dezembro 2024**
*Versão: 1.0.0 - Produção Release*