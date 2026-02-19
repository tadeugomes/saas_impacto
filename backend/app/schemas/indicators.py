"""
Schemas Pydantic para indicadores do Módulo 1 - Operações de Navios.

Estes schemas definem a estrutura de dados para entrada e saída
dos indicadores de operações de navios segundo a especificação técnica.
"""

from datetime import date, datetime
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
        description="Inclui detalhamento por município quando aplicável (ex.: área de influência)",
    )


class AreaInfluenceMunicipio(BaseModel):
    """Municipio pertencente a uma area de influencia."""

    id_municipio: str = Field(..., description="Codigo IBGE do municipio")
    peso: float = Field(1.0, description="Peso de agregacao", gt=0)


class AreaInfluenceUpsertRequest(BaseModel):
    """Payload para criar/atualizar area de influencia."""

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


class AllIndicatorsResponse(BaseModel):
    """Resposta com metadados de todos os indicadores."""

    total_indicadores: int = Field(..., description="Total de indicadores disponíveis")
    unctad_compliant: int = Field(..., description="Indicadores UNCTAD compliant")
    technical_debt_indicators: List[str] = Field(
        default_factory=list,
        description="Indicadores em dívida técnica (sem implementação completa)",
    )
    indicadores: List[IndicatorMetadata] = Field(..., description="Lista de indicadores")
