"""
Schemas Pydantic para indicadores macroeconômicos (Módulo 8).
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MacroIndicadoresResponse(BaseModel):
    """Snapshot dos indicadores macroeconômicos atuais."""

    selic_meta_aa: Optional[float] = Field(None, description="Taxa Selic Meta (% a.a.)")
    ipca_mensal: Optional[float] = Field(None, description="IPCA variação mensal (%)")
    ipca_acumulado_12m: Optional[float] = Field(
        None, description="IPCA acumulado 12 meses (%)"
    )
    cambio_ptax_venda: Optional[float] = Field(
        None, description="Câmbio USD/BRL PTAX venda"
    )
    ibc_br: Optional[float] = Field(None, description="IBC-Br dessazonalizado")
    data_referencia: Optional[str] = Field(None, description="Data de referência ISO")


class SerieTemporalItem(BaseModel):
    """Um ponto de uma série temporal BACEN."""

    data: str = Field(..., description="Data no formato dd/MM/yyyy")
    valor: Optional[float] = Field(None, description="Valor da série")


class SerieHistoricaResponse(BaseModel):
    """Série temporal de um indicador BACEN."""

    codigo_sgs: int
    nome: str
    dados: List[SerieTemporalItem] = []


class ContextoMunicipalResponse(BaseModel):
    """Dados socioeconômicos de um município (IBGE)."""

    cod_ibge: str
    nome_municipio: str = ""
    ano: Optional[int] = None
    populacao: Optional[int] = None
    pib_mil_reais: Optional[float] = None
    pib_per_capita_reais: Optional[float] = None


class DeflacionarRequest(BaseModel):
    """Request para deflacionar uma série de valores."""

    valores: List[Dict[str, Any]] = Field(
        ..., description="Lista de registros com valor nominal"
    )
    campo_valor: str = Field(..., description="Nome do campo com valor nominal")
    campo_ano: str = Field(..., description="Nome do campo com o ano")
    ano_base: Optional[int] = Field(
        None, description="Ano base (default: mais recente)"
    )


class ComposicaoComponente(BaseModel):
    """Um componente de um índice composto — garante transparência ao usuário."""

    nome: str
    codigo_fonte: str = Field(..., description="Código do indicador fonte")
    valor_normalizado: Optional[float] = None
    peso: float
    fonte: str = Field(..., description="Nome da API/fonte de dados")
    periodo_dados: Optional[str] = None
    ultima_atualizacao: Optional[str] = None
    descricao: Optional[str] = None


class ComposicaoIndice(BaseModel):
    """Bloco de transparência que todo índice composto deve retornar."""

    formula: str
    componentes: List[ComposicaoComponente]
    nota_metodologica: Optional[str] = None
