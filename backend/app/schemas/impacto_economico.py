"""
Schemas Pydantic para a API de Impacto Econômico (Módulo 5).

Cobrem criação, consulta de status e leitura de resultados
de análises causais (DiD, IV, Panel IV, Event Study, Compare).
"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


# ── Literais de domínio ───────────────────────────────────────────────────────

MethodLiteral = Literal["did", "iv", "panel_iv", "event_study", "compare"]
ScopeLiteral = Literal["state", "municipal"]
StatusLiteral = Literal["queued", "running", "success", "failed"]

# Colunas de outcome e controle válidas (subset — lista não exaustiva)
_VALID_OUTCOMES = frozenset(
    {
        "pib_log", "pib_per_capita_log", "n_vinculos_log",
        "empregos_totais_log", "toneladas_antaq_log",
        "comercio_dolar_log", "exportacao_dolar_log",
        "importacao_dolar_log", "massa_salarial_total_log",
        "massa_salarial_portuaria_log", "populacao_log",
        "receitas_total_log", "despesas_total_log",
        # sem transformação log
        "pib", "n_vinculos", "empregos_totais", "toneladas_antaq",
        "comercio_dolar", "exportacao_dolar", "importacao_dolar",
    }
)

_VALID_INSTRUMENTS = frozenset(
    {
        "preco_soja", "preco_milho", "preco_trigo",
        "preco_minerio_ferro", "preco_oleo_brent",
        "commodity_index",
    }
)


# ── Request ───────────────────────────────────────────────────────────────────

class EconomicImpactAnalysisCreateRequest(BaseModel):
    """Corpo do POST /api/v1/impacto-economico/analises."""

    method: MethodLiteral = Field(
        ...,
        description=(
            "Método causal a executar:\n"
            "- `did`: Difference-in-Differences (TWFE com diagnósticos)\n"
            "- `iv`: Variáveis Instrumentais (2SLS)\n"
            "- `panel_iv`: Panel IV com efeitos fixos\n"
            "- `event_study`: Event study (sem DiD completo)\n"
            "- `compare`: Executa did + iv e compara consistência"
        ),
    )

    treated_ids: Annotated[
        list[str],
        Field(
            ...,
            min_length=1,
            max_length=200,
            description="Códigos IBGE dos municípios tratados (mínimo 1).",
            examples=[["2100055", "2100105"]],
        ),
    ]

    control_ids: list[str] | None = Field(
        default=None,
        max_length=500,
        description=(
            "Códigos IBGE dos municípios de controle. "
            "Se None, usa todos os municípios disponíveis que não são tratados."
        ),
    )

    treatment_year: int = Field(
        ...,
        ge=2000,
        le=2030,
        description="Ano em que o tratamento ocorreu (define a coluna `post`).",
        examples=[2015],
    )

    scope: ScopeLiteral = Field(
        default="state",
        description=(
            "Escopo geográfico para construção do painel:\n"
            "- `state`: agrupa municípios por UF (tratado = UF com porto)\n"
            "- `municipal`: nível de município individual"
        ),
    )

    outcomes: Annotated[
        list[str],
        Field(
            ...,
            min_length=1,
            max_length=10,
            description=(
                "Variáveis de resultado a estimar. "
                "Use sufixo `_log` para versão log-transformada."
            ),
            examples=[["pib_log", "n_vinculos_log"]],
        ),
    ]

    controls: list[str] | None = Field(
        default=None,
        max_length=10,
        description=(
            "Covariáveis de controle (além dos efeitos fixos). "
            "Se None, usa apenas fixed effects."
        ),
    )

    instrument: str | None = Field(
        default=None,
        description=(
            "Instrumento exógeno para métodos IV e panel_iv. "
            "Obrigatório quando method ∈ {iv, panel_iv}. "
            "Exemplos: `commodity_index`, `preco_soja`."
        ),
    )

    ano_inicio: int = Field(
        default=2010,
        ge=2000,
        le=2030,
        description="Primeiro ano do painel (inclusive).",
    )

    ano_fim: int = Field(
        default=2023,
        ge=2000,
        le=2030,
        description="Último ano do painel (inclusive).",
    )

    use_mart: bool = Field(
        default=True,
        description=(
            "Se True (padrão), usa o mart pré-calculado (mais rápido). "
            "Se False, constrói painel a partir das fontes brutas."
        ),
    )

    # ── Validators ────────────────────────────────────────────────────────────

    @field_validator("ano_fim")
    @classmethod
    def validate_periodo(cls, v: int, info) -> int:
        ano_inicio = info.data.get("ano_inicio", 2010)
        if v <= ano_inicio:
            raise ValueError(
                f"ano_fim ({v}) deve ser maior que ano_inicio ({ano_inicio})."
            )
        return v

    @field_validator("treatment_year")
    @classmethod
    def validate_treatment_year_in_panel(cls, v: int, info) -> int:
        ano_inicio = info.data.get("ano_inicio", 2010)
        ano_fim = info.data.get("ano_fim", 2023)
        if not (ano_inicio < v <= ano_fim):
            raise ValueError(
                f"treatment_year ({v}) deve estar dentro do período "
                f"({ano_inicio}, {ano_fim}] para haver variação pre/post."
            )
        return v

    @model_validator(mode="after")
    def validate_instrument_required_for_iv(self) -> "EconomicImpactAnalysisCreateRequest":
        if self.method in ("iv", "panel_iv") and not self.instrument:
            raise ValueError(
                f"O campo `instrument` é obrigatório para method='{self.method}'. "
                f"Opções: {sorted(_VALID_INSTRUMENTS)}"
            )
        return self

    @model_validator(mode="after")
    def validate_no_overlap_treated_control(self) -> "EconomicImpactAnalysisCreateRequest":
        if self.control_ids:
            overlap = set(self.treated_ids) & set(self.control_ids)
            if overlap:
                raise ValueError(
                    f"Os seguintes municípios estão em treated_ids e control_ids: {overlap}. "
                    "Um município não pode ser tratado e controle ao mesmo tempo."
                )
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "method": "did",
                    "treated_ids": ["2100055", "2100105"],
                    "control_ids": ["2100204", "2100303", "2100402"],
                    "treatment_year": 2015,
                    "scope": "state",
                    "outcomes": ["pib_log", "n_vinculos_log"],
                    "controls": None,
                    "instrument": None,
                    "ano_inicio": 2010,
                    "ano_fim": 2023,
                    "use_mart": True,
                },
            ]
        }
    }


# ── Responses ─────────────────────────────────────────────────────────────────

class EconomicImpactAnalysisResponse(BaseModel):
    """Resposta leve: criação ou consulta de status."""

    id: UUID = Field(..., description="UUID da análise.")
    tenant_id: UUID = Field(..., description="UUID do tenant dono da análise.")
    user_id: UUID | None = Field(None, description="UUID do usuário que disparou.")
    status: StatusLiteral = Field(..., description="queued | running | success | failed")
    method: str = Field(..., description="Método causal utilizado.")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EconomicImpactResultSummary(BaseModel):
    """Resumo executivo dos resultados (populado quando status=success)."""

    outcome: str | None = None
    coef: float | None = Field(None, description="Coeficiente ATT estimado.")
    std_err: float | None = Field(None, description="Erro padrão.")
    p_value: float | None = Field(None, description="P-valor.")
    ci_lower: float | None = Field(None, description="Limite inferior IC 95%.")
    ci_upper: float | None = Field(None, description="Limite superior IC 95%.")
    n_obs: int | None = Field(None, description="Número de observações.")
    r2: float | None = Field(None, description="R² do modelo.")
    warnings: list[str] = Field(default_factory=list, description="Alertas metodológicos.")

    model_config = {"from_attributes": True}


class EconomicImpactAnalysisDetailResponse(EconomicImpactAnalysisResponse):
    """Resposta detalhada: inclui parâmetros, resumo e diagnósticos."""

    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    request_params: dict[str, Any] = Field(default_factory=dict)
    result_summary: dict[str, Any] | None = None
    result_full: dict[str, Any] | None = None
    artifact_path: str | None = None
    error_message: str | None = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_instance(
        cls, obj: Any
    ) -> "EconomicImpactAnalysisDetailResponse":
        """Constrói a resposta a partir de uma instância ORM."""
        return cls(
            id=obj.id,
            tenant_id=obj.tenant_id,
            user_id=obj.user_id,
            status=obj.status,
            method=obj.method,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            started_at=obj.started_at,
            completed_at=obj.completed_at,
            duration_seconds=obj.duration_seconds,
            request_params=obj.request_params or {},
            result_summary=obj.result_summary,
            result_full=obj.result_full,
            artifact_path=obj.artifact_path,
            error_message=obj.error_message,
        )


# ── Listagem ──────────────────────────────────────────────────────────────────

class EconomicImpactAnalysisListResponse(BaseModel):
    """Resposta paginada para listagem de análises."""

    total: int = Field(..., description="Total de análises (do tenant).")
    items: list[EconomicImpactAnalysisResponse]
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    model_config = {"from_attributes": True}
