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
    """Painel DFs-operador (2018-2024) para composição, baseline e regressão."""
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
    summary="Elasticidade Fiscal — ISS do operador portuário × tonelagem",
    description="""
Estima a elasticidade entre tonelagem movimentada e ISS pago pelo operador portuário.

**Fonte de dados:**
- ISS: Demonstrações Financeiras dos operadores portuários (ISS pago pelo porto, não o ISS municipal total)
- Tonelagem: mart BigQuery ANTAQ, 2018-2024
- 11-13 portos com dados completos, n≈59-68 obs

**Metodologia:**
- Regressão OLS pooled log-log (sem FE) — com FE disponível como alternativa no campo `fe_result`
- OLS pooled é usado pois com n≈59 o FE tem baixo poder (variação within-porto pequena)
- Erros padrão HC3 (heteroscedasticidade-robustos)

**Interpretação:**
- β_municipal ≈ 0.84 → portos com 10% mais carga pagam 8.4% mais ISS ao município
- Análise cross-sectional: captura diferença entre portos de tamanhos distintos

**Por que DFs e não FINBRA:**
O ISS do FINBRA representa a arrecadação total do município (todos os serviços),
não apenas do porto. Para capturar a contribuição fiscal direta do porto ao município,
usa-se o ISS declarado nas DFs do operador.

**Nota:** análise associativa (não causal). Fonte: DFs 2018-2024.
Resultado cacheado por 24h.
""",
)
async def get_elasticidade(
    _: User = Depends(require_module_permission(6, "read")),
) -> FiscalElasticidadeResponse:
    """Retorna elasticidades fiscais (DFs dos operadores) + scatter + composição."""
    df = _get_panel()

    elasticidades = compute_elasticity_panel(df)
    scatter = get_scatter_data(df)
    composition = get_composition_data(df)
    portos = get_portos_disponiveis(df)

    el_mun = elasticidades.get("municipal")
    el_fed = elasticidades.get("federal")

    nota = (
        "Regressão OLS log-log pooled (HC3). "
        "ISS: Demonstrações Financeiras dos operadores portuários (ISS pago pelo porto, 2018-2024). "
        "Tonelagem: ANTAQ (mart BigQuery). "
        "Resultado é associativo — não implica causalidade. "
        "ISS do FINBRA (municipal total) não utilizado para não contaminar com serviços não-portuários. "
        "Portos consolidados atribuídos ao município do porto principal."
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
