"""Router — Módulo 6: Contribuição Fiscal Direta dos Portos."""
from __future__ import annotations

import functools
import time
import logging
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.deps import require_module_permission
from app.db.models.user import User
from app.services.fiscal_elasticity_service import (
    build_panel_df,
    compute_elasticity_panel,
    get_scatter_data,
    get_composition_data,
    get_portos_disponiveis,
    simulate_fiscal_impact,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/indicators/module6/fiscal",
    tags=["Módulo 6 — Contribuição Fiscal Direta"],
)

# Cache simples em memória (dados estáticos, TTL 24h)
_cache: dict[str, Any] = {}
_cache_ts: dict[str, float] = {}
_CACHE_TTL = 86400  # 24 horas


def _cached(key: str):
    """Decorator de cache simples com TTL."""
    def decorator(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            now = time.time()
            if key in _cache and (now - _cache_ts.get(key, 0)) < _CACHE_TTL:
                return _cache[key]
            result = await fn(*args, **kwargs)
            _cache[key] = result
            _cache_ts[key] = now
            return result
        return wrapper
    return decorator


def _get_panel():
    """Carrega painel com BigQuery quando disponível, caso contrário usa fixture."""
    try:
        from app.db.bigquery.client import get_bigquery_client
        bq = get_bigquery_client()
        return build_panel_df(bq_client=bq)
    except Exception as exc:
        logger.warning("module6_fiscal: BigQuery indisponível, usando fixture: %s", exc)
        return build_panel_df(bq_client=None)


# ── Schemas ───────────────────────────────────────────────────────────────────

class ElasticidadeResult(BaseModel):
    beta: float
    ci_lower: float
    ci_upper: float
    r2: float
    p_value: float
    n_obs: int
    n_portos: int
    especificacao: Optional[str] = "pooled_ols"
    fe_result: Optional[dict] = None


class ScatterPoint(BaseModel):
    porto: str
    uf: str
    ano: int
    tonelagem_m_ton: float
    iss_r_mi: float
    trib_federais_r_mi: Optional[float] = None


class CompositionItem(BaseModel):
    porto: str
    uf: str
    municipal_r_mi: float
    federal_r_mi: float
    total_r_mi: float
    pct_municipal: float
    pct_federal: float


class FiscalElasticidadeResponse(BaseModel):
    elasticidade_municipal: Optional[ElasticidadeResult] = None
    elasticidade_federal: Optional[ElasticidadeResult] = None
    scatter_points: list[ScatterPoint]
    composition: list[CompositionItem]
    portos_disponiveis: list[str]
    nota_metodologica: str


class SimulacaoFiscalRequest(BaseModel):
    porto: Optional[str] = None
    shock_pct: float = 20.0


class SimulacaoFiscalResponse(BaseModel):
    porto: str
    ano_referencia: Optional[int] = None
    shock_pct: float
    baseline_municipal_r_mi: Optional[float] = None
    baseline_federal_r_mi: Optional[float] = None
    delta_municipal_r_mi: Optional[float] = None
    delta_federal_r_mi: Optional[float] = None
    delta_municipal_ci: Optional[list[float]] = None
    delta_federal_ci: Optional[list[float]] = None
    elasticidade_usada: str
    nota: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/elasticidade",
    response_model=FiscalElasticidadeResponse,
    summary="Elasticidade Fiscal — Regressão OLS log-log (média do setor)",
    description="""
Estima a elasticidade entre tonelagem movimentada e tributos pagos pelos portos.

**Metodologia:**
- Regressão OLS log-log com efeitos fixos de porto (dummies)
- Erros padrão HC3 (heteroscedasticidade-robustos)
- Amostra: 22 portos, 2018-2024
- Outliers filtrados (trib > R$ 500M)

**Interpretação:**
- beta_municipal = 0.68 → +10% tonelagem → +6.8% ISS municipal
- beta_federal = 0.52 → +10% tonelagem → +5.2% tributos federais

**Nota:** análise associativa (não causal). Fonte: DFs dos operadores portuários.

Resultado cacheado por 24h (dados estáticos).
""",
)
async def get_elasticidade(
    _: User = Depends(require_module_permission(6, "read")),
) -> FiscalElasticidadeResponse:
    """Retorna elasticidades fiscais + dados para scatter + composição municipal/federal."""
    df = _get_panel()

    elasticidades = compute_elasticity_panel(df)
    scatter = get_scatter_data(df)
    composition = get_composition_data(df)
    portos = get_portos_disponiveis(df)

    el_mun = elasticidades.get("municipal")
    el_fed = elasticidades.get("federal")

    nota = (
        "Regressão OLS log-log com efeitos fixos de porto (HC3). "
        "Tonelagem proveniente de ANTAQ (mart interno). "
        "Tributos de Demonstrações Financeiras dos operadores, 2018-2024. "
        "Resultado é associativo — não implica causalidade. "
        "Outliers filtrados (>R$ 500M). "
        "Portos consolidados (PortosRio, Portos RS, Portos do Pará, Portos do Paraná) "
        "atribuídos ao município do porto principal."
    )

    return FiscalElasticidadeResponse(
        elasticidade_municipal=ElasticidadeResult(**el_mun) if el_mun else None,
        elasticidade_federal=ElasticidadeResult(**el_fed) if el_fed else None,
        scatter_points=[ScatterPoint(**p) for p in scatter],
        composition=[CompositionItem(**c) for c in composition],
        portos_disponiveis=portos,
        nota_metodologica=nota,
    )


@router.post(
    "/simulacao",
    response_model=SimulacaoFiscalResponse,
    summary="Simular impacto fiscal de variação de tonelagem",
    description="""
Projeta variação em ISS municipal e tributos federais dado um choque de tonelagem.

**Se porto informado:** usa ISS/tributos reais do ano mais recente do porto como baseline.
**Se porto=null:** usa médias do setor.

Elasticidade usada: média do setor (painel de todos os portos).
""",
)
async def simulacao_fiscal(
    body: SimulacaoFiscalRequest,
    _: User = Depends(require_module_permission(6, "read")),
) -> SimulacaoFiscalResponse:
    """Projeta impacto fiscal de crescimento de tonelagem."""
    if abs(body.shock_pct) > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="shock_pct deve estar entre -200% e +200%.",
        )

    df = _get_panel()
    elasticidades = compute_elasticity_panel(df)

    result = simulate_fiscal_impact(
        porto=body.porto,
        shock_pct=body.shock_pct,
        elasticidades=elasticidades,
        df=df,
    )

    return SimulacaoFiscalResponse(**result)
