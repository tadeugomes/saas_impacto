# Plano de Integração — APIs Públicas Brasileiras

> Inspirado no [mcp-brasil](https://github.com/jxnxts/mcp-brasil). Acesso direto
> às APIs REST públicas, sem dependência do servidor MCP.
>
> **Perspectiva:** Investidor no setor portuário brasileiro.
> Priorização orientada por relevância para decisão de investimento.

---

## Visão Geral

| Item | Valor |
|------|-------|
| **APIs integradas** | 7 (Fase 1-3) |
| **Novos indicadores** | ~22 |
| **Módulos impactados** | Todos (1-7) + Módulo 8 (Macro) + Módulo 9 (Ambiental) |
| **Padrão** | Mesmo pipeline de `GenericIndicatorService` + `IndicatorQueryCache` |
| **Nova dependência** | `httpx>=0.27.0` (única adição ao requirements.txt) |

### Decisões Arquiteturais

1. **Reutilizar `GenericIndicatorService`** — novos indicadores fluem pelo mesmo
   endpoint `/api/v1/indicators/query`, herdando cache, permissões, audit e tenant
   isolation automaticamente.
2. **Dispatch via `inspect.iscoroutinefunction`** — mudança mínima em
   `execute_indicator()` para suportar funções async (APIs externas) ao lado das
   funções SQL (BigQuery). Sem reestruturação.
3. **Sem novas tabelas no PostgreSQL** — dados de API ficam em Redis cache;
   séries deflacionadas são computadas on-the-fly a partir de BigQuery + cache.
4. **Celery pre-fetch** — dados macro mudam lentamente (Selic a cada 45 dias,
   IPCA mensal), então pre-fetch no Redis garante resposta <10ms nas consultas.
5. **Transparência nos índices compostos** — todo índice composto inclui na
   resposta da API um bloco `composicao` com: fórmula, pesos, fonte de cada
   componente, período dos dados e data da última atualização.

---

## Arquitetura da Integração

```
backend/app/
├── clients/                         # NOVO — Clientes HTTP para APIs externas
│   ├── __init__.py
│   ├── base.py                      # Cliente base async (httpx) com retry/cache
│   ├── bacen.py                     # Banco Central (SGS API)
│   ├── ibge.py                      # IBGE APIs (agregados, localidades)
│   ├── tce.py                       # TCEs (SP, RJ, RS)
│   ├── transparencia.py             # Portal da Transparência
│   ├── ana.py                       # Agência Nacional de Águas
│   ├── inpe.py                      # INPE (focos de incêndio)
│   └── mares.py                     # Marinha — Tábua de Marés
│
├── services/
│   ├── deflation_service.py         # NOVO — Deflação IPCA + conversão cambial
│   ├── macro_economico_service.py   # NOVO — Indicadores macroeconômicos
│   ├── ambiental_service.py         # NOVO — Índice ambiental composto
│   └── financas_publicas_service.py # NOVO — Complementa Módulo 6
│
├── db/bigquery/queries/
│   └── composite_indicators.py      # NOVO — Indicadores que combinam BQ + API
│
├── api/v1/
│   └── public_apis.py               # NOVO — Health/status das APIs externas
│
├── schemas/
│   ├── macro.py                     # NOVO — Schemas BACEN/IBGE
│   └── ambiental.py                 # NOVO — Schemas ANA/INPE
│
├── tasks/
│   └── public_api_sync.py           # NOVO — Celery tasks para sync periódico
│
└── config.py                        # ATUALIZAR — Novas variáveis de ambiente

frontend/src/
├── views/Dashboard/ModuleViews/
│   ├── Module8View.tsx              # NOVO — Contexto Macroeconômico
│   └── Module9View.tsx              # NOVO — Risco Ambiental (Fase 2)
├── components/
│   ├── MacroCard.tsx                # NOVO — Card macro (valor, variação, sparkline)
│   ├── CompositeIndexCard.tsx       # NOVO — Card com nota de composição
│   └── EnvironmentalRiskGauge.tsx   # NOVO — Gauge de risco ambiental (Fase 2)
└── types/
    └── macro.ts                     # NOVO — Tipos para indicadores macro
```

---

## Fase 1 — Contexto do Investidor (Semanas 1-3)

> **Foco:** Dados macroeconômicos que contextualizam a decisão de investimento —
> custo de oportunidade (Selic), erosão de retorno (IPCA), competitividade
> cambial (PTAX), atividade econômica (IBC-Br), e dados municipais (PIB, população).

### 1.1 Cliente HTTP Base

**Arquivo:** `backend/app/clients/base.py`

Segue o mesmo padrão do `BigQueryClient`: lazy init, retry com backoff, cache Redis.
Usado por `PublicApiError` (espelha `BigQueryError`).

```python
class PublicApiError(Exception):
    """Exceção base para erros de APIs externas."""
    def __init__(self, message: str, api_name: str, url: str = None,
                 status_code: int = None, details: str = None):
        ...

class BasePublicApiClient:
    """Cliente HTTP assíncrono base com retry, cache e rate-limiting."""

    def __init__(self, base_url: str, api_name: str):
        self.base_url = base_url
        self.api_name = api_name
        self._client: httpx.AsyncClient | None = None
        self._cache = IndicatorQueryCache()

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazy init com connection pooling e HTTP/2."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=30.0,
                limits=httpx.Limits(max_connections=10),
                http2=True,
            )
        return self._client

    async def get_cached(self, cache_key: str, fetcher, *, ttl: int = 3600):
        """Verifica cache → executa fetcher se miss → salva no cache."""
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return cached
        data = await fetcher()
        await self._cache.set(cache_key, data, ttl=ttl)
        return data

    async def _request(self, method: str, path: str, *,
                       params: dict = None) -> dict | list:
        """Request com retry (3x, backoff exponencial 1s→2s→4s)."""
        client = await self._get_client()
        last_error = None
        for attempt in range(3):
            try:
                resp = await client.request(method, path, params=params)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    retry_after = int(e.response.headers.get("Retry-After", 2 ** attempt))
                    await asyncio.sleep(retry_after)
                elif e.response.status_code >= 500:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise PublicApiError(str(e), self.api_name, status_code=e.response.status_code)
                last_error = e
            except httpx.TransportError as e:
                await asyncio.sleep(2 ** attempt)
                last_error = e
        raise PublicApiError(f"Falha após 3 tentativas: {last_error}", self.api_name)

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
```

### 1.2 Cliente BACEN (Banco Central)

**Arquivo:** `backend/app/clients/bacen.py`

**API Base:** `https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados`

**Séries prioritárias para o investidor:**

| Código SGS | Indicador | Relevância para Investimento |
|------------|-----------|------------------------------|
| 432 | IPCA mensal | Deflacionar séries → retorno real do ativo |
| 1 | Taxa Selic | Custo de oportunidade (CDI como benchmark) |
| 3698 | Câmbio PTAX venda | Competitividade exportadora / receita em USD |
| 4380 | IBC-Br | Proxy de PIB mensal → atividade econômica |
| 27574 | Expectativa Focus IPCA | Projeção de cenário inflacionário |

**Métodos do cliente:**
- `consultar_serie(codigo, data_inicio, data_fim)` → Lista de {data, valor}
- `indicadores_atuais()` → Selic, IPCA, câmbio, IBC-Br atuais
- `get_deflator_ipca(ano_base, ano_inicio, ano_fim)` → Fatores de deflação por ano

**Novos indicadores (Módulo 8 — Contexto Macro):**
- **IND-8.01:** Taxa Selic Meta — valor atual + série 12 meses
- **IND-8.02:** IPCA Acumulado 12 meses — inflação corrente
- **IND-8.03:** Câmbio USD/BRL (PTAX) — série diária
- **IND-8.04:** IBC-Br — proxy PIB mensal, dessazonalizado

**Impacto nos módulos existentes:**
- **Módulos 1-6:** Todas as séries monetárias ganham versão "real" (deflacionada pelo IPCA)
- **Módulo 4:** Valores Comex convertidos para USD com PTAX do período
- **Módulo 5:** Séries BACEN como covariáveis nos modelos DiD/IV/SCM

### 1.3 Cliente IBGE (Dados Municipais)

**Arquivo:** `backend/app/clients/ibge.py`

**APIs:**
- `https://servicodados.ibge.gov.br/api/v1/localidades/`
- `https://servicodados.ibge.gov.br/api/v3/agregados/`

**Dados prioritários:**

| Agregado | Descrição | Relevância para Investimento |
|----------|-----------|------------------------------|
| 5938 | PIB municipal | Tamanho da economia local do porto |
| 6579 | População estimada | Denominadores per capita (receita/habitante) |
| 1301 | IPCA por região metropolitana | Deflator regionalizado |

**Métodos do cliente:**
- `buscar_municipios(uf)` → Lista de municípios com código IBGE
- `consultar_agregado(agregado, localidade, periodo)` → Dados estatísticos
- `populacao_municipio(cod_ibge, ano)` → População estimada

**Novos indicadores (Módulo 8):**
- **IND-8.05:** População do município portuário (atualizada)
- **IND-8.06:** PIB per capita municipal
- Enriquece multiplicadores de emprego (Módulo 3) com denominadores atualizados

### 1.4 Serviço de Deflação

**Arquivo:** `backend/app/services/deflation_service.py`

Serviço transversal que todos os módulos podem usar para deflacionar séries
monetárias e converter câmbio.

```python
class DeflationService:
    """Deflação IPCA e conversão cambial para análise em termos reais."""

    def __init__(self, bacen: BacenClient):
        self.bacen = bacen

    async def deflacionar_serie(
        self, valores: list[dict], campo_valor: str, campo_ano: str,
        ano_base: int = None
    ) -> list[dict]:
        """Retorna a série com campo '{campo_valor}_real' adicionado."""

    async def converter_para_usd(
        self, valores: list[dict], campo_valor_brl: str, campo_data: str
    ) -> list[dict]:
        """Adiciona campo '{campo_valor}_usd' usando PTAX do período."""
```

### 1.5 Serviço Macroeconômico

**Arquivo:** `backend/app/services/macro_economico_service.py`

```python
class MacroEconomicoService:
    """Indicadores macroeconômicos para contexto de investimento."""

    def __init__(self):
        self.bacen = BacenClient()
        self.ibge = IBGEClient()

    async def indicadores_atuais(self) -> MacroIndicadoresResponse:
        """Snapshot atual: Selic, IPCA, câmbio, IBC-Br."""

    async def serie_historica(
        self, codigo_sgs: int, anos: int = 5
    ) -> SerieHistoricaResponse:
        """Série temporal de um indicador BACEN."""

    async def contexto_municipal(
        self, cod_ibge: int, ano: int
    ) -> ContextoMunicipalResponse:
        """PIB, população e dados socioeconômicos de um município."""
```

### 1.6 Indicadores Compostos (BigQuery + API)

**Arquivo:** `backend/app/db/bigquery/queries/composite_indicators.py`

Funções async que combinam dados BigQuery com dados de APIs externas.
Registradas em `ALL_QUERIES` e detectadas via `inspect.iscoroutinefunction`.

```python
async def query_receita_real_por_tonelada(
    bq_client, deflation_service, **params
) -> list[dict]:
    """IND-2.14: Receita por tonelada deflacionada pelo IPCA."""
    raw = await bq_client.execute_query(query_receita_nominal(**params))
    return await deflation_service.deflacionar_serie(raw, "receita", "ano")

async def query_fob_ajustado_cambio(
    bq_client, deflation_service, **params
) -> list[dict]:
    """IND-4.08: Valor FOB/TEU convertido para USD via PTAX."""
    raw = await bq_client.execute_query(query_fob_nominal(**params))
    return await deflation_service.converter_para_usd(raw, "valor_fob", "data")
```

### 1.7 Configuração

**Arquivo:** `backend/app/config.py` — Adicionar:

```python
# APIs Externas
bacen_api_base_url: str = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"
ibge_api_base_url: str = "https://servicodados.ibge.gov.br/api/v3"
transparencia_api_key: Optional[str] = None

# Cache TTLs específicos por fonte
cache_ttl_bacen: int = 21600      # 6h (BACEN atualiza 1x/dia)
cache_ttl_ibge: int = 86400       # 24h (IBGE menos frequente)
cache_ttl_ambiental: int = 3600   # 1h (dados em tempo real — Fase 2)

# Rate limits para APIs externas (requests/minuto)
public_api_timeout_seconds: int = 30
public_api_max_retries: int = 3
```

### 1.8 Integração no GenericIndicatorService

**Arquivo:** `backend/app/services/generic_indicator_service.py` — Modificar:

```python
# Em execute_indicator():
import inspect

if inspect.iscoroutinefunction(query_func):
    # Indicador composto (BigQuery + API externa)
    rows = await query_func(bq_client=self.bq_client, **params)
else:
    # Indicador BigQuery puro (padrão existente)
    sql = query_func(**params)
    rows = await self.bq_client.execute_query(sql)
```

Registrar novos indicadores em `INDICATORS_METADATA`:
```python
INDICATORS_METADATA["IND-8.01"] = IndicatorMeta(modulo=8, nome="Taxa Selic Meta", ...)
INDICATORS_METADATA["IND-8.02"] = IndicatorMeta(modulo=8, nome="IPCA Acumulado 12m", ...)
# ...
```

**Arquivo:** `backend/app/api/deps.py` — Estender planos:
```python
MODULE_PLAN_LIMITS = {
    "basic": {1, 2, 3, 4},
    "pro": {1, 2, 3, 4, 5, 6, 7, 8},          # +Módulo 8
    "enterprise": {1, 2, 3, 4, 5, 6, 7, 8, 9}, # +Módulo 9
}
```

### 1.9 Frontend (Fase 1)

**Novo painel:** `Module8View.tsx` — Sidebar item "Contexto Macro"

Segue o padrão idêntico de `Module1View.tsx`: declara `INDICATORS_INFO`,
usa `indicatorsService.queryIndicator()`, renderiza `IndicatorDashboardCard`.

Componentes:
- **MacroCard.tsx** — Card reutilizável (valor atual, variação %, sparkline 12 meses)

Sem necessidade de hooks ou API clients separados — tudo flui pelo
`indicatorsService.queryIndicator({ codigo_indicador: 'IND-8.01', params })`.

---

## Fase 2 — Operacional e Ambiental (Semanas 4-6)

> **Foco:** Dados operacionais (marés), ambientais (hidrologia, incêndios),
> fiscais (TCEs, Transparência) e Celery tasks para sincronização.

### 2.1 Cliente Tábua de Marés

**Arquivo:** `backend/app/clients/mares.py`

**API Base:** API de marés da Marinha do Brasil

**Dados disponíveis:**
- Previsão de marés por porto (hora, altura)
- Marés de sizígia e quadratura
- Janelas de navegação por calado

**Novos indicadores (Módulo 1):**
- **IND-1.13:** Taxa de Aproveitamento de Maré — % de atracações na janela ótima
- **IND-1.14:** Tempo Médio de Espera por Maré — horas aguardando janela
- **IND-1.15:** Janela Navegável Média — horas/dia com calado suficiente

### 2.2 Clientes ANA + INPE

**Arquivo:** `backend/app/clients/ana.py`

**API Base:** `https://telemetriaws1.ana.gov.br/ServiceANA.asmx`

**Dados:**
- Estações hidrológicas (nível, vazão, chuva)
- Monitoramento de reservatórios
- Relevante para portos fluviais (Manaus, Porto Velho, Santarém)

**Arquivo:** `backend/app/clients/inpe.py`

**API Base:** `https://terrabrasilis.dpi.inpe.br/queimadas/bdqueimadas`

**Dados:**
- Focos de incêndio (lat/lon, data, satélite, município)

**Novos indicadores (Módulo 9 — Risco Ambiental):**
- **IND-9.01:** Índice de Risco Hídrico — Nível de rio vs. calado mínimo
- **IND-9.02:** Focos de Incêndio Próximos — Quantidade em raio de 50km do porto
- **IND-9.03:** Índice de Risco Ambiental Composto

#### Transparência nos Índices Compostos

> **Requisito:** Todo índice composto DEVE incluir na resposta da API um bloco
> `composicao` que torna explícito ao usuário quais dados geraram o índice.

Exemplo de resposta para IND-9.03:
```json
{
  "codigo": "IND-9.03",
  "nome": "Índice de Risco Ambiental Composto",
  "valor": 0.42,
  "classificacao": "moderado",
  "composicao": {
    "formula": "IRAmb = 0.50 × Risco_Hídrico + 0.50 × Risco_Incêndio",
    "componentes": [
      {
        "nome": "Risco Hídrico",
        "codigo_fonte": "IND-9.01",
        "valor_normalizado": 0.35,
        "peso": 0.50,
        "fonte": "ANA — Agência Nacional de Águas",
        "estacao": "Manaus (14990000)",
        "periodo_dados": "2026-03-01 a 2026-03-27",
        "ultima_atualizacao": "2026-03-27T08:00:00Z",
        "descricao": "Nível do rio vs. calado mínimo operacional (12m)"
      },
      {
        "nome": "Risco de Incêndio",
        "codigo_fonte": "IND-9.02",
        "valor_normalizado": 0.49,
        "peso": 0.50,
        "fonte": "INPE — Instituto Nacional de Pesquisas Espaciais",
        "raio_busca_km": 50,
        "focos_detectados": 23,
        "periodo_dados": "últimos 7 dias",
        "ultima_atualizacao": "2026-03-27T06:30:00Z",
        "descricao": "Focos de incêndio em raio de 50km da instalação"
      }
    ],
    "nota_metodologica": "Valores normalizados 0-1 via min-max sobre histórico de 5 anos. Pesos definidos por relevância operacional para a instalação portuária."
  }
}
```

Este padrão de `composicao` será utilizado em **todos** os índices compostos
(IND-7.06 IDPM, IND-7.07 Risco Operacional, IND-7.08 Governança, IND-9.03 Ambiental).

### 2.3 Cliente TCEs

**Arquivo:** `backend/app/clients/tce.py`

**APIs por estado:**

| TCE | Base URL | Dados |
|-----|----------|-------|
| TCE-SP | `https://transparencia.tce.sp.gov.br/api/` | Receita/despesa de 645 municípios |
| TCE-RJ | `https://api-dados-abertos.tce.rj.gov.br/` | Licitações, contratos, obras |
| TCE-RS | `https://dados.tce.rs.gov.br/api/` | Educação, saúde, gestão fiscal |

**Novos indicadores (Módulo 6):**
- **IND-6.06:** Autonomia Fiscal — Receita própria / Receita total
- **IND-6.07:** Investimento per capita — Despesas de capital / População
- **IND-6.08:** Eficiência na Execução Orçamentária — Executado / Autorizado

### 2.4 Cliente Portal da Transparência

**Arquivo:** `backend/app/clients/transparencia.py`

**API Base:** `https://api.portaldatransparencia.gov.br/api-de-dados/`

**Requer:** `TRANSPARENCIA_API_KEY` (registro gratuito)

**Novos indicadores (Módulo 6):**
- **IND-6.09:** Investimento Federal no Município Portuário
- **IND-6.10:** Emendas Parlamentares no município
- **IND-6.11:** Servidores Federais (proxy presença federal)

### 2.5 Celery Tasks para Sincronização

**Arquivo:** `backend/app/tasks/public_api_sync.py`

```python
@celery_app.task(name="sync_bacen_series")
def sync_bacen_series():
    """Roda diariamente — atualiza séries BACEN no cache Redis."""

@celery_app.task(name="sync_ibge_dados")
def sync_ibge_dados():
    """Roda mensalmente — atualiza PIB e população IBGE."""

@celery_app.task(name="sync_focos_incendio")
def sync_focos_incendio():
    """Roda a cada 3h — atualiza focos de incêndio INPE."""

@celery_app.task(name="sync_nivel_rios")
def sync_nivel_rios():
    """Roda a cada 6h — atualiza nível de rios para portos fluviais."""
```

Registrar no Celery Beat (schedule periódico).

---

## Fase 3 — Baixa Prioridade (Semanas 7-10)

### 3.1 Novos Índices Sintéticos (Módulo 7)

Usando os dados das fases 1 e 2, criar índices compostos.
**Todos incluem o bloco `composicao` na resposta da API** (ver padrão na seção 2.2).

**IND-7.06: Índice de Desenvolvimento Portuário Municipal (IDPM)**

```
IDPM = 0.25 × PIB_normalizado           (IBGE — Agregado 5938)
     + 0.20 × Emprego_portuário_norm     (RAIS via BigQuery)
     + 0.20 × Eficiência_operacional     (Score existente — Módulo 1)
     + 0.15 × Autonomia_fiscal           (TCE — IND-6.06)
     + 0.10 × Infraestrutura_saude       (DataSUS/CNES — futuro)
     + 0.10 × Sustentabilidade_ambiental (ANA+INPE — IND-9.03)
```

**IND-7.07: Índice de Risco Operacional**

```
IRO = 0.40 × Risco_maré       (Tábua de Marés — IND-1.15)
    + 0.30 × Risco_hídrico    (ANA — IND-9.01)
    + 0.30 × Risco_ambiental  (INPE — IND-9.02)
```

**IND-7.08: Índice de Governança Portuária**

```
IGP = 0.35 × Transparência_fiscal        (TCE — IND-6.06)
    + 0.30 × Investimento_federal_per_cap (Portal Transparência — IND-6.09)
    + 0.35 × Execução_orçamentária        (TCE — IND-6.08)
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

# Cache TTLs por fonte
CACHE_TTL_BACEN=21600       # 6h — BACEN atualiza 1x/dia
CACHE_TTL_IBGE=86400        # 24h — IBGE menos frequente
CACHE_TTL_AMBIENTAL=3600    # 1h — dados em tempo real (Fase 2)

# Rate limits e timeout
PUBLIC_API_TIMEOUT_SECONDS=30
PUBLIC_API_MAX_RETRIES=3

# APIs com chave (Fase 2 — registro gratuito)
TRANSPARENCIA_API_KEY=
```

---

## Registro no Pipeline Existente

**Novos indicadores NÃO precisam de rotas separadas.** Todos são servidos pelo
endpoint universal `/api/v1/indicators/query` já existente.

**Arquivo:** `backend/app/main.py` — Adicionar apenas:

```python
# Health/status das APIs externas (opcional, para monitoramento)
from app.api.v1.public_apis import router as public_apis_router
app.include_router(public_apis_router, prefix="/api/v1")
```

**Arquivo:** `backend/app/main.py` (lifespan) — Adicionar cleanup:

```python
# No shutdown do lifespan
from app.clients.bacen import get_bacen_client
from app.clients.ibge import get_ibge_client
await get_bacen_client().close()
await get_ibge_client().close()
```

---

## Resumo de Entregáveis por Fase

| Fase | Semanas | Foco | Arquivos Novos | Indicadores | APIs |
|------|---------|------|---------------|-------------|------|
| **1** | 1-3 | Contexto do Investidor | ~12 (backend) + ~3 (frontend) | 8 novos (IND-8.xx) + deflação em todos | BACEN, IBGE |
| **2** | 4-6 | Operacional e Ambiental | ~10 (backend) + ~3 (frontend) | 11 novos (IND-1.13-15, IND-6.06-11, IND-9.01-03) | Tábua de Marés, ANA, INPE, TCEs, Transparência |
| **3** | 7-10 | Índices Sintéticos | ~5 (backend) + ~2 (frontend) | 3 índices compostos + covariáveis causais | Compostos |

**Total:** ~35 arquivos novos, ~22 indicadores, 7 APIs integradas.

---

## Critérios de Aceite

- [ ] Todos os clientes HTTP herdam de `BasePublicApiClient` com retry e cache
- [ ] Cache Redis com TTL configurável por fonte de dados
- [ ] Testes unitários para cada cliente (mock de API via httpx transport)
- [ ] Testes de integração com APIs reais (`@pytest.mark.integration`)
- [ ] Indicadores servidos pelo endpoint genérico `/api/v1/indicators/query`
- [ ] Frontend Module8View exibe indicadores macro com filtros de período
- [ ] Celery tasks sincronizam dados periodicamente (Beat schedule)
- [ ] Cada novo indicador registrado em `INDICATORS_METADATA`
- [ ] **Índices compostos incluem bloco `composicao`** na resposta, com: fórmula,
  pesos, fonte de cada componente, período dos dados e última atualização
- [ ] Fallback gracioso: quando API externa indisponível, retorna dados
  cacheados (stale) com warning, ou dados não-deflacionados com aviso
