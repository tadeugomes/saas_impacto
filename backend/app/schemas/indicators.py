"""
Schemas Pydantic para indicadores do Módulo 1 - Operações de Navios.

Estes schemas definem a estrutura de dados para entrada e saída
dos indicadores de operações de navios segundo a especificação técnica.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Schemas Base
# ============================================================================

class IndicatorFilter(BaseModel):
    """Filtros comuns para consultas de indicadores."""

    id_instalacao: Optional[str] = Field(
        None,
        description="ID da instalação portuária (filtro específico)",
    )
    ano: Optional[int] = Field(
        None,
        description="Ano de referência (YYYY)",
        ge=2000,
        le=2100,
    )
    ano_inicio: Optional[int] = Field(
        None,
        description="Ano inicial para período",
        ge=2000,
        le=2100,
    )
    ano_fim: Optional[int] = Field(
        None,
        description="Ano final para período",
        ge=2000,
        le=2100,
    )
    mes: Optional[int] = Field(
        None,
        description="Mês de referência (1-12)",
        ge=1,
        le=12,
    )

    @field_validator("ano_fim")
    @classmethod
    def validate_periodo(cls, v: Optional[int], info) -> Optional[int]:
        """Valida que ano_fim >= ano_inicio."""
        if v is not None and "ano_inicio" in info.data:
            ano_inicio = info.data["ano_inicio"]
            if ano_inicio is not None and v < ano_inicio:
                raise ValueError("ano_fim deve ser maior ou igual a ano_inicio")
        return v


class IndicatorResponse(BaseModel):
    """Resposta base para indicadores."""

    codigo_indicador: str = Field(..., description="Código do indicador (ex: IND-1.01)")
    nome: str = Field(..., description="Nome do indicador")
    unidade: str = Field(..., description="Unidade de medida")
    unctad: bool = Field(..., description="Segue padrão UNCTAD")
    data_referencia: datetime = Field(
        default_factory=datetime.utcnow,
        description="Data/hora da geração dos dados",
    )


# ============================================================================
# Módulo 1: Indicadores de Tempo
# ============================================================================

class TempoMedioEsperaResponse(IndicatorResponse):
    """IND-1.01: Tempo Médio de Espera [UNCTAD]."""

    id_instalacao: str = Field(..., description="ID da instalação")
    ano: int = Field(..., description="Ano de referência")
    tempo_medio_espera_horas: float = Field(
        ...,
        description="Tempo médio de espera em horas",
        ge=0,
    )


class TempoMedioPortoResponse(IndicatorResponse):
    """IND-1.02: Tempo Médio em Porto [UNCTAD]."""

    id_instalacao: str = Field(..., description="ID da instalação")
    ano: int = Field(..., description="Ano de referência")
    tempo_medio_porto_horas: float = Field(
        ...,
        description="Tempo médio em porto (atracado + espera) em horas",
        ge=0,
    )


class TempoBrutoAtracacaoResponse(IndicatorResponse):
    """IND-1.03: Tempo Bruto de Atracação [UNCTAD]."""

    id_instalacao: str = Field(..., description="ID da instalação")
    ano: int = Field(..., description="Ano de referência")
    tempo_bruto_atracacao_horas: float = Field(
        ...,
        description="Tempo bruto de atracação em horas",
        ge=0,
    )


class TempoLiquidoOperacaoResponse(IndicatorResponse):
    """IND-1.04: Tempo Líquido de Operação [UNCTAD]."""

    id_instalacao: str = Field(..., description="ID da instalação")
    ano: int = Field(..., description="Ano de referência")
    tempo_liquido_operacao_horas: float = Field(
        ...,
        description="Tempo líquido de operação em horas",
        ge=0,
    )


class TaxaOcupacaoBercoesResponse(IndicatorResponse):
    """IND-1.05: Taxa de Ocupação de Berços [UNCTAD]."""

    id_instalacao: str = Field(..., description="ID da instalação")
    ano: int = Field(..., description="Ano de referência")
    taxa_ocupacao_percentual: float = Field(
        ...,
        description="Taxa de ocupação de berços (0-100)",
        ge=0,
        le=100,
    )


class TempoOciosoTurnoResponse(IndicatorResponse):
    """IND-1.06: Tempo Ocioso Médio por Turno [UNCTAD]."""

    id_instalacao: str = Field(..., description="ID da instalação")
    ano: int = Field(..., description="Ano de referência")
    tempo_ocioso_medio_horas: float = Field(
        ...,
        description="Tempo ocioso médio em horas",
        ge=0,
    )


# ============================================================================
# Módulo 1: Indicadores de Características de Navios
# ============================================================================

class ArqueacaoBrutaMediaResponse(IndicatorResponse):
    """IND-1.07: Arqueação Bruta Média (GT) [UNCTAD]."""

    id_instalacao: str = Field(..., description="ID da instalação")
    ano: int = Field(..., description="Ano de referência")
    arqueacao_bruta_media: float = Field(
        ...,
        description="Arqueação bruta média em GT (Gross Tonnage)",
        ge=0,
    )


class ComprimentoMedioNavioResponse(IndicatorResponse):
    """IND-1.08: Comprimento Médio de Navios [UNCTAD]."""

    id_instalacao: str = Field(..., description="ID da instalação")
    ano: int = Field(..., description="Ano de referência")
    comprimento_medio_metros: float = Field(
        ...,
        description="Comprimento médio dos navios em metros",
        ge=0,
    )


class CaladoMaximoOperacionalResponse(IndicatorResponse):
    """IND-1.09: Calado Máximo Operacional [UNCTAD]."""

    id_instalacao: str = Field(..., description="ID da instalação")
    calado_maximo_metros: float = Field(
        ...,
        description="Calado máximo operacional em metros",
        ge=0,
    )


class TipoNavioDistributionItem(BaseModel):
    """Item da distribuição por tipo de navio."""

    tipo_navegacao: str = Field(..., description="Tipo de navegação")
    qtd_atracacoes: int = Field(..., description="Quantidade de atracações", ge=0)
    percentual: float = Field(..., description="Percentual do total", ge=0, le=100)


class DistribuicaoTipoNavioResponse(IndicatorResponse):
    """IND-1.10: Distribuição por Tipo de Navio [UNCTAD]."""

    id_instalacao: str = Field(..., description="ID da instalação")
    ano: int = Field(..., description="Ano de referência")
    distribuicao: List[TipoNavioDistributionItem] = Field(
        ...,
        description="Distribuição por tipo de navegação",
    )


class NumeroAtracacoesResponse(IndicatorResponse):
    """IND-1.11: Número de Atracações."""

    id_instalacao: str = Field(..., description="ID da instalação")
    ano: int = Field(..., description="Ano de referência")
    total_atracacoes: int = Field(
        ...,
        description="Total de atracações no período",
        ge=0,
    )


class IndiceParalisacaoResponse(IndicatorResponse):
    """IND-1.12: Índice de Paralisação."""

    id_instalacao: str = Field(..., description="ID da instalação")
    ano: int = Field(..., description="Ano de referência")
    indice_paralisacao_percentual: Optional[float] = Field(
        None,
        description="Índice de paralisação (0-100), null se sem dados",
        ge=0,
        le=100,
    )


# ============================================================================
# Módulo 1: Resumo Consolidado
# ============================================================================

class OperacoesNaviosResumoItem(BaseModel):
    """Item do resumo de operações de navios."""

    codigo_indicador: str = Field(..., description="Código do indicador")
    nome: str = Field(..., description="Nome do indicador")
    valor: float = Field(..., description="Valor do indicador")
    unidade: str = Field(..., description="Unidade de medida")


class OperacoesNaviosResumoResponse(IndicatorResponse):
    """Resumo consolidado dos indicadores do Módulo 1."""

    id_instalacao: str = Field(..., description="ID da instalação")
    ano: int = Field(..., description="Ano de referência")
    indicadores: List[OperacoesNaviosResumoItem] = Field(
        ...,
        description="Lista de indicadores calculados",
    )


# ============================================================================
# Requests para Consulta
# ============================================================================

class OperacoesNaviosRequest(IndicatorFilter):
    """Request para consulta de indicadores de operações de navios."""

    include_detalhes: bool = Field(
        False,
        description="Incluir distribuição por tipo de navio",
    )
    consolidate: bool = Field(
        False,
        description="Retornar todos os indicadores consolidados",
    )


# ============================================================================
# Paginação
# ============================================================================

class PaginatedResponse(BaseModel):
    """Resposta paginada genérica."""

    items: List[dict] = Field(..., description="Itens da página atual")
    total: int = Field(..., description="Total de itens", ge=0)
    page: int = Field(..., description="Página atual (1-indexed)", ge=1)
    page_size: int = Field(..., description="Itens por página", ge=1, le=1000)
    total_pages: int = Field(..., description="Total de páginas", ge=0)


class IndicatorListRequest(IndicatorFilter):
    """Request para lista de indicadores com paginação."""

    page: int = Field(1, description="Página atual (1-indexed)", ge=1)
    page_size: int = Field(50, description="Itens por página", ge=1, le=1000)
    order_by: Optional[str] = Field(None, description="Campo de ordenação")
    order_desc: bool = Field(False, description="Ordenação descendente")


# ============================================================================
# Schemas Genéricos para Todos os Módulos
# ============================================================================

class GenericIndicatorRequest(BaseModel):
    """Request genérico para consulta de qualquer indicador."""

    codigo_indicador: str = Field(
        ...,
        description="Código do indicador (ex: IND-1.01, IND-2.05, etc.)",
    )
    id_instalacao: Optional[str] = Field(None, description="ID da instalação/município")
    id_municipio: Optional[str] = Field(None, description="ID do município (IBGE)")
    ano: Optional[int] = Field(None, description="Ano de referência", ge=2000, le=2100)
    ano_inicio: Optional[int] = Field(None, description="Ano inicial do período", ge=2000, le=2100)
    ano_fim: Optional[int] = Field(None, description="Ano final do período", ge=2000, le=2100)
    mes: Optional[int] = Field(None, description="Mês de referência (1-12)", ge=1, le=12)
    include_breakdown: bool = Field(
        default=False,
        description="Inclui detalhamento por município quando aplicável (ex.: município de influência).",
    )
    deflacionar: bool = Field(
        default=False,
        description=(
            "Aplica deflação IPCA aos valores monetários (R$), convertendo para "
            "valores reais. Adiciona campos *_real, deflator_ipca e ano_base_deflacao."
        ),
    )
    ano_base_deflacao: Optional[int] = Field(
        default=None,
        description="Ano base para deflação IPCA (default: ano mais recente da série). Ex: 2023",
        ge=2000,
        le=2100,
    )


class TenantModulePermissionItem(BaseModel):
    """Linha de permissão por módulo/ação para um role/tenant."""

    module_number: int = Field(..., ge=1, le=7)
    action: Literal["read", "execute", "write"]
    allowed: bool = True


class TenantModulePermissionsRequest(BaseModel):
    """Payload para definir permissões de um role em um tenant."""

    permissions: list[TenantModulePermissionItem] = Field(
        default_factory=list,
        description="Lista de combinações módulo/ação",
    )


class TenantModulePermissionsResponse(BaseModel):
    """Permissões retornadas por role (tenant)."""

    role: str = Field(..., description="Role alvo")
    permissions: list[TenantModulePermissionItem] = Field(
        default_factory=list,
        description="Permissões permitidas no escopo do role",
    )


class MunicipioLookupItem(BaseModel):
    """Item com identificador e nome de município."""

    id_municipio: str = Field(..., description="ID IBGE do município")
    nome_municipio: str = Field(..., description="Nome do município")


class MunicipioLookupResponse(BaseModel):
    """Resposta para consulta de nomes de municípios por código IBGE."""

    municipios: list[MunicipioLookupItem] = Field(
        default_factory=list,
        description="Pares ID e nome encontrados",
    )


class InstallationMunicipioResolutionResponse(BaseModel):
    """Resposta de resolução de instalação/porto para município IBGE."""

    id_instalacao: str = Field(..., description="Instalação/porto solicitado")
    id_municipio: Optional[str] = Field(
        None,
        description="ID IBGE do município associado (se encontrado)",
    )
    municipio_found: bool = Field(
        ...,
        description="Indica se foi encontrado município associado",
    )
    message: str = Field(..., description="Resumo de validação da resolução")


class AreaInfluenceMunicipio(BaseModel):
    """Municipio pertencente ao município de influência."""

    id_municipio: str = Field(..., description="Codigo IBGE do municipio")
    peso: float = Field(1.0, description="Peso de agregacao", gt=0)


class AreaInfluenceUpsertRequest(BaseModel):
    """Payload para criar/atualizar município de influência."""

    municipios: List[AreaInfluenceMunicipio] = Field(..., min_length=1)


class AllowlistPolicyUpdateRequest(BaseModel):
    """Payload de atualizacao de allowlist/quota do tenant."""

    allowed_municipios: List[str] = Field(default_factory=list)
    max_bytes_per_query: Optional[int] = Field(
        default=None,
        gt=0,
        description="Limite de bytes por consulta para modulo 5",
    )


class DataQualityWarning(BaseModel):
    """Advertência de qualidade de dado retornada junto com o resultado."""

    tipo: str = Field(..., description="Tipo da verificação de qualidade")
    codigo_indicador: str = Field(..., description="Indicador com problema potencial")
    campo: Optional[str] = Field(
        None,
        description="Campo numérico validado",
    )
    id_municipio: Optional[str] = Field(
        None,
        description="Município relacionado",
    )
    ano: Optional[int] = Field(None, description="Ano relacionado à observação")
    valor: Optional[float] = Field(None, description="Valor avaliado")
    mensagem: str = Field(..., description="Descrição da inconsistência")


class GenericIndicatorResponse(BaseModel):
    """Resposta genérica para qualquer indicador."""

    codigo_indicador: str = Field(..., description="Código do indicador")
    nome: str = Field(..., description="Nome do indicador")
    unidade: str = Field(..., description="Unidade de medida")
    unctad: bool = Field(..., description="Segue padrão UNCTAD")
    modulo: int = Field(..., description="Número do módulo (1-7)")
    data: List[dict] = Field(..., description="Dados do indicador")
    warnings: List[DataQualityWarning] = Field(
        default_factory=list,
        description="Advertências de qualidade de dados"
    )
    cache_hit: bool = Field(
        default=False,
        description="Indica se o resultado veio do cache de consulta",
    )
    data_referencia: datetime = Field(
        default_factory=datetime.utcnow,
        description="Data/hora da geração dos dados",
    )


class IndicatorMetadata(BaseModel):
    """Metadados de um indicador."""

    codigo: str = Field(..., description="Código do indicador")
    nome: str = Field(..., description="Nome do indicador")
    modulo: int = Field(..., description="Número do módulo")
    unidade: str = Field(..., description="Unidade de medida")
    unctad: bool = Field(..., description="Segue padrão UNCTAD")
    implementation_status: Literal["implemented", "technical_debt"] = Field(
        ...,
        description="Status de implementação do indicador",
    )
    descricao: Optional[str] = Field(None, description="Descrição do indicador")
    granularidade: str = Field(..., description="Granularidade dos dados")
    fonte_dados: str = Field(..., description="Fonte de dados")


# ============================================================================
# Módulo 1 — Analíticos: Tendência, Benchmarking, Score Eficiência
# ============================================================================

class ClassificacaoTendencia(str, Enum):
    """Classificação da tendência operacional."""
    IMPROVING = "IMPROVING"
    STABLE = "STABLE"
    DETERIORATING = "DETERIORATING"
    SEM_DADOS = "SEM_DADOS"


class TendenciaItem(BaseModel):
    """Tendência de um indicador operacional."""

    indicador_codigo: str = Field(..., description="Código do indicador (ex: IND-1.01)")
    indicador_nome: str = Field(..., description="Nome do indicador")
    unidade: str = Field(..., description="Unidade de medida")
    valor_atual: Optional[float] = Field(None, description="Valor no ano atual")
    valor_anterior: Optional[float] = Field(None, description="Valor no ano anterior")
    variacao_yoy_pct: Optional[float] = Field(None, description="Variação ano a ano (%)")
    cagr_3y_pct: Optional[float] = Field(None, description="CAGR 3 anos (%)")
    classificacao: ClassificacaoTendencia = Field(
        ClassificacaoTendencia.SEM_DADOS,
        description="IMPROVING / STABLE / DETERIORATING / SEM_DADOS",
    )
    polaridade_inversa: bool = Field(
        True,
        description="Se True, queda no valor = melhoria (tempos). Se False, crescimento = melhoria (atracações).",
    )


class TendenciaOperacionalResponse(BaseModel):
    """Análise de tendência operacional de uma instalação."""

    id_instalacao: str = Field(..., description="ID da instalação portuária")
    ano: int = Field(..., description="Ano de referência (mais recente)")
    indicadores: List[TendenciaItem] = Field(
        ...,
        description="Tendência para cada indicador temporal",
    )


class ClassificacaoBenchmark(str, Enum):
    """Classificação de benchmarking."""
    ACIMA_MEDIA = "ACIMA_MEDIA"
    NA_MEDIA = "NA_MEDIA"
    ABAIXO_MEDIA = "ABAIXO_MEDIA"


class BenchmarkItem(BaseModel):
    """Posição de uma instalação em um indicador relativo ao universo nacional."""

    indicador_codigo: str = Field(..., description="Código do indicador")
    indicador_nome: str = Field(..., description="Nome do indicador")
    unidade: str = Field(..., description="Unidade de medida")
    valor_instalacao: Optional[float] = Field(None, description="Valor da instalação")
    mediana_nacional: Optional[float] = Field(None, description="Mediana de todos os portos no ano")
    p75_nacional: Optional[float] = Field(None, description="Percentil 75 nacional")
    percentil_rank: Optional[float] = Field(
        None, description="Posição percentil da instalação (0-100)", ge=0, le=100,
    )
    classificacao: ClassificacaoBenchmark = Field(
        ClassificacaoBenchmark.NA_MEDIA,
        description="ACIMA_MEDIA / NA_MEDIA / ABAIXO_MEDIA",
    )
    polaridade_inversa: bool = Field(
        True,
        description="Se True, percentil baixo (menos tempo) = melhor",
    )


class BenchmarkingResponse(BaseModel):
    """Benchmarking de uma instalação contra pares nacionais."""

    id_instalacao: str = Field(..., description="ID da instalação portuária")
    ano: int = Field(..., description="Ano de referência")
    total_portos: int = Field(..., description="Total de portos no universo comparativo")
    indicadores: List[BenchmarkItem] = Field(
        ...,
        description="Posição relativa em cada indicador",
    )


class ComponenteScore(BaseModel):
    """Componente de um score de eficiência decomposto."""

    indicador_codigo: str = Field(..., description="Código do indicador")
    indicador_nome: str = Field(..., description="Nome do indicador")
    valor_bruto: Optional[float] = Field(None, description="Valor bruto do indicador")
    valor_normalizado: Optional[float] = Field(
        None, description="Valor normalizado (0-100)", ge=0, le=100,
    )
    peso: float = Field(..., description="Peso no score total (0-1)")
    contribuicao: Optional[float] = Field(
        None, description="Contribuição ao score total (normalizado × peso)",
    )


class ScoreEficienciaResponse(BaseModel):
    """Score de eficiência operacional decomposto."""

    id_instalacao: str = Field(..., description="ID da instalação portuária")
    ano: int = Field(..., description="Ano de referência")
    score_total: float = Field(
        ..., description="Score total de eficiência (0-100)", ge=0, le=100,
    )
    ranking_posicao: int = Field(..., description="Posição no ranking (1 = melhor)", ge=1)
    total_portos: int = Field(..., description="Total de portos avaliados")
    componentes: List[ComponenteScore] = Field(
        ...,
        description="Decomposição do score por indicador",
    )
    nota_metodologica: str = Field(
        default=(
            "Score baseado em 6 indicadores temporais com normalização min-max "
            "entre todos os portos no ano. Pesos: espera 20%, bruto 15%, "
            "operação 15%, ocioso 20%, atracações 15%, paralisação 15%. "
            "Diferente do IND-7.01 (Módulo 7) que usa volume (tonelagem)."
        ),
        description="Nota metodológica explicando o score",
    )


class AllIndicatorsResponse(BaseModel):
    """Resposta com metadados de todos os indicadores."""

    total_indicadores: int = Field(..., description="Total de indicadores disponíveis")
    unctad_compliant: int = Field(..., description="Indicadores UNCTAD compliant")
    technical_debt_indicators: List[str] = Field(
        default_factory=list,
        description="Indicadores em dívida técnica (sem implementação completa)",
    )
    indicadores: List[IndicatorMetadata] = Field(..., description="Lista de indicadores")
