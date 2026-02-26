"""
Schemas Pydantic para multiplicadores e impacto de emprego (Módulo 3).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

ConfidenceLiteral = Literal["strong", "moderate", "weak"]
ImpactConfidenceLiteral = Literal["forte", "moderado", "baixo"]
MultiplierTypeLiteral = Literal["literature", "causal"]
CausalMethodLiteral = Literal["iv_2sls", "panel_iv"]


class LiteratureMultiplier(BaseModel):
    """Metadados do multiplicador de literatura."""

    coefficient: float = Field(..., ge=1)
    range_low: float = Field(..., gt=0)
    range_high: float = Field(..., gt=0)
    confidence: ConfidenceLiteral = "moderate"
    source: str
    year_published: int = Field(..., ge=2000)
    region: str = "Brasil"
    breakdown_indirect: float = Field(..., ge=0)
    breakdown_induced: float = Field(..., ge=0)


class CausalMultiplier(BaseModel):
    """Resultado de estimativa causal (quando disponível)."""

    coefficient: float
    std_error: Optional[float] = None
    p_value: Optional[float] = None
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None
    confidence: ConfidenceLiteral = "weak"
    n_obs: Optional[int] = None
    method: CausalMethodLiteral = "iv_2sls"


class IndirectJobsEstimate(BaseModel):
    """Estimativa no formato legado do frontend antigo."""

    municipality_id: str = ""
    municipality_name: Optional[str] = None
    year: Optional[int] = None
    direct_jobs: int = Field(..., ge=0)
    indirect_estimated: float = Field(..., ge=0)
    induced_estimated: float = Field(..., ge=0)
    total_impact: float = Field(..., ge=0)
    multiplier_used: float = Field(..., ge=1)
    multiplier_type: MultiplierTypeLiteral
    confidence: ConfidenceLiteral
    source: str


class EmploymentImpactResult(BaseModel):
    """Resultado central de impacto de emprego para leitura de negócio."""

    municipality_id: str = Field(..., description="id_municipio IBGE (7 dígitos)")
    municipality_name: Optional[str] = Field(default=None, description="nome do município")
    ano: int = Field(..., description="ano da estimativa")
    empregos_diretos: int = Field(..., ge=0, description="empregos diretos no setor portuário")
    empregos_totais: Optional[int] = Field(
        default=None,
        ge=0,
        description="empregos totais municipais",
    )
    participacao_emprego_local: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="% de participação do emprego portuário no total municipal",
    )
    tonelagem_antaq_milhoes: Optional[float] = Field(
        default=None,
        gt=0,
        description="tonelagem movimentada anual em milhões de toneladas",
    )
    empregos_por_milhao_toneladas: Optional[float] = Field(
        default=None,
        ge=0,
        description="empregos diretos por 1 milhão de toneladas",
    )
    empregos_indiretos_estimados: float = Field(..., ge=0, description="empregos indiretos estimados")
    empregos_induzidos_estimados: float = Field(..., ge=0, description="empregos induzidos estimados")
    emprego_total_estimado: float = Field(..., ge=0, description="total aproximado de empregos (diretos+indiretos+induzidos)")
    metodologia: str = Field(..., description="descrição do método")
    indicador_de_confianca: ImpactConfidenceLiteral = Field(
        ...,
        description="classificação qualitativa de confiança",
    )
    correlacao_ou_proxy: bool = Field(
        ...,
        description="true quando indicador não é causal",
    )
    metodo: str = Field(..., description="metodologia usada para o impacto")
    fonte: str = Field(..., description="fonte do dado base")
    scenario: Optional["EmploymentShockScenario"] = Field(
        default=None,
        description="simulação de choque de tonelagem",
    )

    @field_validator("municipality_id")
    @classmethod
    def _normalize_municipality_id(cls, value: str) -> str:
        if not value:
            return value
        return str(value).strip()

    @field_validator("ano")
    @classmethod
    def _validate_year(cls, value: int) -> int:
        if value < 2000:
            raise ValueError("ano precisa ser >= 2000")
        if value > datetime.now(timezone.utc).year + 1:
            raise ValueError("ano não pode estar no futuro")
        return value


class EmploymentShockScenario(BaseModel):
    """Estimativa de choque de carga para simulação."""

    delta_tonelagem_pct: float = Field(..., description="variação percentual da tonelagem")
    delta_empregos_diretos: float = Field(..., description="mudança esperada de empregos diretos")
    delta_empregos_indiretos: float = Field(..., description="mudança esperada de empregos indiretos")
    delta_empregos_induzidos: float = Field(..., description="mudança esperada de empregos induzidos")
    delta_emprego_total: float = Field(..., description="mudança total esperada de empregos")


class MultiplierMetadataItem(BaseModel):
    """Item de catálogo de multiplicador."""

    sector: str
    coefficient: float
    range_low: float
    range_high: float
    source: str
    year_published: int
    region: str
    confidence: ConfidenceLiteral
