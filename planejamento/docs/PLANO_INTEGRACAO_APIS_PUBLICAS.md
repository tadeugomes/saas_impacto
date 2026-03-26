# Plano de Integração — APIs Públicas Brasileiras

> Inspirado no [mcp-brasil](https://github.com/jxnxts/mcp-brasil). Acesso direto
> às APIs REST públicas, sem dependência do servidor MCP.

---

## Visão Geral

| Item | Valor |
|------|-------|
| **APIs integradas** | 6 (Fase 1-3) |
| **Novos indicadores** | ~18 |
| **Módulos impactados** | Todos (1-7) |
| **Padrão** | Mesmo padrão de `BigQueryClient` + `IndicatorQueryCache` |

---

## Arquitetura da Integração

```
backend/app/
├── clients/                         # NOVO — Clientes HTTP para APIs externas
│   ├── __init__.py
│   ├── base_http_client.py          # Cliente base async (httpx) com retry/cache
│   ├── bacen_client.py              # Banco Central (SGS API)
│   ├── ibge_client.py               # IBGE APIs (agregados, localidades)
│   ├── tabua_mares_client.py        # Marinha — Tábua de Marés
│   ├── tce_client.py                # TCEs (SP, RJ, RS)
│   ├── transparencia_client.py      # Portal da Transparência
│   ├── ana_client.py                # Agência Nacional de Águas
│   └── inpe_client.py               # INPE (focos de incêndio)
│
├── services/
│   ├── macro_economico_service.py   # NOVO — Indicadores macroeconômicos
│   ├── mares_service.py             # NOVO — Indicadores de marés
│   ├── ambiental_service.py         # NOVO — Índice ambiental
│   └── financas_publicas_service.py # NOVO — Complementa Módulo 6
│
├── api/v1/
│   ├── macro.py                     # NOVO — Endpoints macroeconômicos
│   ├── mares.py                     # NOVO — Endpoints de marés
│   └── ambiental.py                 # NOVO — Endpoints ambientais
│
├── schemas/
│   ├── macro.py                     # NOVO — Schemas BACEN/IBGE
│   ├── mares.py                     # NOVO — Schemas Tábua de Marés
│   └── ambiental.py                 # NOVO — Schemas ANA/INPE
│
├── tasks/
│   └── sync_external_data.py        # NOVO — Celery tasks para sync periódico
│
└── config.py                        # ATUALIZAR — Novas variáveis de ambiente

frontend/src/
├── api/
│   ├── macro.ts                     # NOVO — API client macro
│   ├── mares.ts                     # NOVO — API client marés
│   └── ambiental.ts                 # NOVO — API client ambiental
├── hooks/
│   ├── useMacro.ts                  # NOVO
│   ├── useMares.ts                  # NOVO
│   └── useAmbiental.ts              # NOVO
├── views/Dashboard/
│   ├── MacroContextView.tsx         # NOVO — Painel macroeconômico
│   └── components/
│       ├── MacroCard.tsx            # NOVO — Card de indicador macro
│       ├── TideChart.tsx            # NOVO — Gráfico de marés
│       └── EnvironmentalRiskGauge.tsx # NOVO
└── types/
    ├── macro.ts                     # NOVO
    ├── mares.ts                     # NOVO
    └── ambiental.ts                 # NOVO
```

---

## Fase 1 — Alta Prioridade (Semanas 1-3)

### 1.1 Cliente HTTP Base

**Arquivo:** `backend/app/clients/base_http_client.py`

Segue o mesmo padrão do `BigQueryClient`: lazy init, retry com backoff, cache Redis.

```python
class BaseHttpClient:
    """Cliente HTTP assíncrono base com retry, cache e rate-limiting."""

    BASE_URL: str  # Sobrescrito pelas subclasses
    CACHE_PREFIX: str = "api"
    DEFAULT_TTL: int = 3600  # 1 hora

    def __init__(self):
        self._client: httpx.AsyncClient | None = None
        self._cache = IndicatorQueryCache()

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=30.0,
                limits=httpx.Limits(max_connections=10),
            )
        return self._client

    async def _request(
        self, method: str, path: str, *,
        params: dict = None,
        cache_key: str = None,
        ttl: int = None,
    ) -> dict | list:
        # 1. Verificar cache
        if cache_key:
            cached = await self._cache.get(cache_key)
            if cached is not None:
                return cached

        # 2. Request com retry (3x, backoff exponencial)
        client = await self._get_client()
        for attempt in range(3):
            try:
                resp = await client.request(method, path, params=params)
                resp.raise_for_status()
                data = resp.json()
                break
            except (httpx.HTTPStatusError, httpx.TransportError):
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)

        # 3. Salvar no cache
        if cache_key:
            await self._cache.set(cache_key, data, ttl=ttl or self.DEFAULT_TTL)

        return data
```

### 1.2 Cliente BACEN (Banco Central)

**Arquivo:** `backend/app/clients/bacen_client.py`

**API Base:** `https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados`

**Séries prioritárias:**

| Código SGS | Indicador | Uso no SaaS Impacto |
|------------|-----------|---------------------|
| 432 | IPCA mensal | Deflacionar séries monetárias (todos os módulos) |
| 1 | Taxa Selic | Variável de controle (Módulo 5 causal) |
| 3698 | Câmbio (dólar PTAX venda) | Converter valores FOB (Módulo 4) |
| 4380 | PIB mensal (IBC-Br) | Covariável para modelos de painel |
| 27574 | Expectativa Focus IPCA | Projeção inflacionária |

**Ferramentas expostas:**
- `consultar_serie(codigo, data_inicio, data_fim)` → Lista de {data, valor}
- `indicadores_atuais()` → Selic, IPCA, câmbio, PIB atuais
- `deflacionar(valores, datas, serie_deflator=432)` → Valores em reais constantes

**Novos indicadores habilitados:**
- **IND-MACRO-01:** Selic atual e tendência (12 meses)
- **IND-MACRO-02:** IPCA acumulado 12 meses
- **IND-MACRO-03:** Câmbio USD/BRL (PTAX)
- **IND-MACRO-04:** IBC-Br (proxy PIB mensal)

**Impacto nos módulos existentes:**
- **Módulo 1-6:** Todas as séries monetárias passam a ter versão "real" (deflacionada)
- **Módulo 4:** Valores Comex convertidos para USD com PTAX do dia
- **Módulo 5:** Séries BACEN como covariáveis nos modelos DiD/IV/SCM

### 1.3 Cliente IBGE (Dados Municipais)

**Arquivo:** `backend/app/clients/ibge_client.py`

**APIs:**
- `https://servicodados.ibge.gov.br/api/v1/localidades/`
- `https://servicodados.ibge.gov.br/api/v3/agregados/`

**Dados prioritários:**

| Agregado | Descrição | Uso |
|----------|-----------|-----|
| 5938 | PIB municipal | Enriquecer Módulo 5 com dados recentes |
| 6579 | População estimada | Denominadores per capita |
| 1301 | IPCA por região | Deflator regional |

**Ferramentas expostas:**
- `buscar_municipios(uf)` → Lista de municípios com código IBGE
- `consultar_agregado(agregado, localidade, periodo)` → Dados estatísticos
- `populacao_municipio(cod_ibge, ano)` → População estimada

**Novos indicadores:**
- **IND-MACRO-05:** População do município portuário (atualizada)
- **IND-MACRO-06:** PIB per capita municipal
- Enriquece multiplicadores de emprego (Módulo 3) com denominadores atualizados

### 1.4 Cliente Tábua de Marés

**Arquivo:** `backend/app/clients/tabua_mares_client.py`

**API Base:** `https://www.marinha.mil.br/chm/tabuas-de-mare` (scraping estruturado ou API interna)

**Dados disponíveis:**
- Previsão de marés por porto (hora, altura)
- Marés de sizígia e quadratura
- Janelas de navegação por calado

**Ferramentas expostas:**
- `previsao_mares(porto, data_inicio, data_fim)` → Lista de {hora, altura_metros}
- `janelas_navegacao(porto, calado_minimo, data)` → Períodos navegáveis

**Novos indicadores (Módulo 1):**
- **IND-1.13:** Taxa de Aproveitamento de Maré — % de atracações dentro da janela ótima de maré
- **IND-1.14:** Tempo Médio de Espera por Maré — horas aguardando janela de maré
- **IND-1.15:** Janela Navegável Média — horas/dia com calado suficiente

**Correlação com indicadores existentes:**
- Cruzar IND-1.01 (Tempo Médio de Espera) com janelas de maré para isolar espera operacional vs. espera por maré

### 1.5 Serviço Macroeconômico

**Arquivo:** `backend/app/services/macro_economico_service.py`

```python
class MacroEconomicoService:
    """Serviço de indicadores macroeconômicos e deflação."""

    def __init__(self):
        self.bacen = BacenClient()
        self.ibge = IBGEClient()

    async def indicadores_atuais(self) -> MacroIndicadoresResponse:
        """Retorna snapshot atual de Selic, IPCA, câmbio, PIB."""

    async def serie_historica(
        self, codigo_sgs: int, anos: int = 5
    ) -> SerieHistoricaResponse:
        """Retorna série temporal de um indicador BACEN."""

    async def deflacionar_serie(
        self, valores: list[float], datas: list[str],
        deflator: int = 432
    ) -> list[float]:
        """Converte valores nominais para valores reais."""

    async def contexto_municipal(
        self, cod_ibge: int, ano: int
    ) -> ContextoMunicipalResponse:
        """PIB, população e dados socioeconômicos de um município."""
```

### 1.6 Configuração

**Arquivo:** `backend/app/config.py` — Adicionar:

```python
# APIs Externas
bacen_api_base_url: str = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"
ibge_api_base_url: str = "https://servicodados.ibge.gov.br/api/v3"
tabua_mares_api_base_url: str = "https://www.marinha.mil.br/chm/dados-de-mare"
transparencia_api_key: Optional[str] = None
datajud_api_key: Optional[str] = None

# Cache TTLs específicos
cache_ttl_bacen: int = 21600      # 6h (dados BACEN atualizam 1x/dia)
cache_ttl_ibge: int = 86400       # 24h (dados IBGE menos frequentes)
cache_ttl_mares: int = 43200      # 12h (previsões de maré)
cache_ttl_ambiental: int = 3600   # 1h (focos de incêndio em tempo real)
```

### 1.7 Endpoints REST (Fase 1)

**Arquivo:** `backend/app/api/v1/macro.py`

```
GET  /api/v1/macro/indicadores-atuais     → Selic, IPCA, câmbio, IBC-Br
GET  /api/v1/macro/serie/{codigo_sgs}     → Série histórica BACEN
POST /api/v1/macro/deflacionar            → Deflacionar lista de valores
GET  /api/v1/macro/contexto-municipal/{cod_ibge} → Dados municipais IBGE
```

**Arquivo:** `backend/app/api/v1/mares.py`

```
GET  /api/v1/mares/previsao/{porto}       → Previsão de marés
GET  /api/v1/mares/janelas/{porto}        → Janelas de navegação
GET  /api/v1/mares/indicadores/{id_instalacao} → IND-1.13, 1.14, 1.15
```

### 1.8 Frontend (Fase 1)

**Novo painel:** `MacroContextView.tsx` — Sidebar item "Contexto Macro"

Componentes:
- **MacroCard.tsx** — Card reutilizável (valor atual, variação %, sparkline)
- **SerieChart.tsx** — Gráfico de linha para séries BACEN
- **TideChart.tsx** — Gráfico de maré com janelas de navegação

Hooks:
- `useMacro()` — Fetch indicadores macroeconômicos
- `useMares()` — Fetch previsões de maré

---

## Fase 2 — Média Prioridade (Semanas 4-6)

### 2.1 Cliente TCEs

**Arquivo:** `backend/app/clients/tce_client.py`

**APIs por estado:**

| TCE | Base URL | Dados |
|-----|----------|-------|
| TCE-SP | `https://transparencia.tce.sp.gov.br/api/` | Receita/despesa de 645 municípios |
| TCE-RJ | `https://api-dados-abertos.tce.rj.gov.br/` | Licitações, contratos, obras |
| TCE-RS | `https://dados.tce.rs.gov.br/api/` | Educação, saúde, gestão fiscal |

**Novos indicadores (Módulo 6):**
- **IND-6.06:** Autonomia Fiscal — Receita própria / Receita total do município
- **IND-6.07:** Investimento per capita — Despesas de capital / População
- **IND-6.08:** Eficiência na Execução Orçamentária — Executado / Autorizado

### 2.2 Cliente Portal da Transparência

**Arquivo:** `backend/app/clients/transparencia_client.py`

**API Base:** `https://api.portaldatransparencia.gov.br/api-de-dados/`

**Requer:** `TRANSPARENCIA_API_KEY` (registro gratuito)

**Novos indicadores:**
- **IND-6.09:** Investimento Federal no Município Portuário — Soma de contratos federais
- **IND-6.10:** Emendas Parlamentares — Valor total de emendas no município
- **IND-6.11:** Servidores Federais — Quantidade no município (proxy presença federal)

### 2.3 Clientes ANA + INPE

**Arquivo:** `backend/app/clients/ana_client.py`

**API Base:** `https://www.snirh.gov.br/hidroweb/rest/api/`

**Dados:**
- Estações hidrológicas (nível, vazão, chuva)
- Monitoramento de reservatórios

**Arquivo:** `backend/app/clients/inpe_client.py`

**API Base:** `https://queimadas.dgi.inpe.br/api/focos/`

**Dados:**
- Focos de incêndio (lat/lon, data, satélite, município)

**Novos indicadores (cross-module):**
- **IND-AMB-01:** Índice de Risco Hídrico — Nível de rio vs. calado mínimo (portos fluviais)
- **IND-AMB-02:** Focos de Incêndio Próximos — Quantidade em raio de 50km do porto
- **IND-AMB-03:** Índice de Risco Ambiental Composto — Média ponderada de IND-AMB-01 + IND-AMB-02

### 2.4 Serviço de Finanças Públicas Expandido

**Arquivo:** `backend/app/services/financas_publicas_service.py`

Complementa o Módulo 6 existente (FINBRA via BigQuery) com dados em tempo real dos TCEs.

### 2.5 Celery Tasks para Sincronização

**Arquivo:** `backend/app/tasks/sync_external_data.py`

```python
@celery_app.task(name="sync_bacen_series")
def sync_bacen_series():
    """Roda diariamente — atualiza séries BACEN no cache Redis."""

@celery_app.task(name="sync_ibge_populacao")
def sync_ibge_populacao():
    """Roda mensalmente — atualiza dados demográficos IBGE."""

@celery_app.task(name="sync_mares")
def sync_mares():
    """Roda 2x/dia — atualiza previsões de maré para portos configurados."""

@celery_app.task(name="sync_focos_incendio")
def sync_focos_incendio():
    """Roda a cada 3h — atualiza focos de incêndio INPE."""
```

Registrar no Celery Beat (schedule periódico).

---

## Fase 3 — Baixa Prioridade (Semanas 7-10)

### 3.1 Novos Índices Sintéticos (Módulo 7)

Usando os dados das fases 1 e 2, criar índices compostos:

**IND-7.06: Índice de Desenvolvimento Portuário Municipal (IDPM)**

```
IDPM = 0.25 × PIB_normalizado
     + 0.20 × Emprego_portuário_normalizado
     + 0.20 × Eficiência_operacional (score existente)
     + 0.15 × Autonomia_fiscal
     + 0.10 × Infraestrutura_saude
     + 0.10 × Sustentabilidade_ambiental
```

**IND-7.07: Índice de Risco Operacional**

```
IRO = 0.40 × Risco_maré (janela navegável)
    + 0.30 × Risco_hídrico (nível do rio)
    + 0.30 × Risco_ambiental (incêndios)
```

**IND-7.08: Índice de Governança Portuária**

```
IGP = 0.35 × Transparência_fiscal (TCE)
    + 0.30 × Investimento_federal_per_capita
    + 0.35 × Execução_orçamentária
```

### 3.2 Integração com Modelos Causais (Módulo 5)

Adicionar covariáveis do BACEN/IBGE ao `panel_builder.py`:

```python
# Em panel_builder.py — novo método
async def _enrich_with_macro(self, panel: pd.DataFrame) -> pd.DataFrame:
    """Adiciona Selic, IPCA, câmbio como covariáveis ao painel."""
    bacen = BacenClient()
    selic = await bacen.consultar_serie(1, ...)
    ipca = await bacen.consultar_serie(432, ...)
    cambio = await bacen.consultar_serie(3698, ...)
    # Merge por ano/mês
    ...
```

### 3.3 Módulos Futuros (Planejamento)

| Módulo | Fonte | Escopo |
|--------|-------|--------|
| Compliance Portuário | PNCP + TCU + Querido Diário | Monitorar licitações e menções ao porto |
| Contexto Eleitoral | TSE | Correlação presença portuária × resultados eleitorais |
| Saúde Regional | DataSUS/CNES | Infraestrutura de saúde em municípios portuários |

---

## Dependências e Pacotes

**Adicionar ao `requirements.txt`:**

```
httpx>=0.27.0          # Cliente HTTP async (substitui requests)
```

> Nota: `httpx` é a única dependência nova necessária. O projeto já tem
> `redis`, `pydantic`, `celery`, e toda a infra de cache/tasks.

---

## Variáveis de Ambiente (.env)

```env
# APIs Externas (Fase 1)
BACEN_API_BASE_URL=https://api.bcb.gov.br/dados/serie/bcdata.sgs
IBGE_API_BASE_URL=https://servicodados.ibge.gov.br/api/v3
TABUA_MARES_API_BASE_URL=https://www.marinha.mil.br/chm/dados-de-mare

# Cache TTLs
CACHE_TTL_BACEN=21600
CACHE_TTL_IBGE=86400
CACHE_TTL_MARES=43200
CACHE_TTL_AMBIENTAL=3600

# APIs com chave (Fase 2 — opcional)
TRANSPARENCIA_API_KEY=
DATAJUD_API_KEY=
```

---

## Registro de Rotas

**Arquivo:** `backend/app/main.py` — Adicionar:

```python
from app.api.v1.macro import router as macro_router
from app.api.v1.mares import router as mares_router
from app.api.v1.ambiental import router as ambiental_router

app.include_router(macro_router, prefix="/api/v1")
app.include_router(mares_router, prefix="/api/v1")
app.include_router(ambiental_router, prefix="/api/v1")
```

---

## Resumo de Entregáveis por Fase

| Fase | Semanas | Arquivos Novos | Indicadores | APIs |
|------|---------|---------------|-------------|------|
| **1** | 1-3 | ~15 (backend) + ~8 (frontend) | 10 novos + deflação em todos | BACEN, IBGE, Tábua de Marés |
| **2** | 4-6 | ~8 (backend) + ~4 (frontend) | 9 novos | TCEs, Transparência, ANA, INPE |
| **3** | 7-10 | ~5 (backend) + ~3 (frontend) | 3 índices sintéticos + covariáveis causais | Compostos |

**Total:** ~43 arquivos novos, ~22 indicadores, 8 APIs integradas.

---

## Critérios de Aceite

- [ ] Todos os clientes HTTP seguem o padrão `BaseHttpClient` com retry e cache
- [ ] Cache Redis com TTL configurável por fonte de dados
- [ ] Testes unitários para cada cliente (mock de API)
- [ ] Testes de integração com APIs reais (marcados como `@pytest.mark.integration`)
- [ ] Indicadores aparecem no endpoint genérico `/api/v1/indicators/query`
- [ ] Frontend exibe dados no dashboard com filtros de período
- [ ] Celery tasks sincronizam dados periodicamente
- [ ] Documentação de cada novo indicador em `INDICATORS_METADATA`
