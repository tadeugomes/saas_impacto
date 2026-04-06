"""Schemas Pydantic para o Módulo 12 — Capacidade Portuária."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Configuração de Terminal
# ---------------------------------------------------------------------------

class TerminalCapacityConfigBase(BaseModel):
    """Campos comuns para criação e atualização."""

    id_instalacao: str = Field(
        ...,
        min_length=2,
        max_length=30,
        description="Código da instalação portuária ANTAQ",
    )
    nome_terminal: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Nome do terminal",
    )
    n_bercos: int = Field(
        1,
        ge=1,
        le=50,
        description="Número de berços operacionais",
    )
    h_ef: float = Field(
        8000.0,
        gt=0,
        le=8760,
        description="Horas efetivas de operação por ano",
    )
    clearance_h: float = Field(
        3.0,
        gt=0,
        le=24,
        description="Intervalo entre atracações (horas)",
    )
    bor_adm_override: Optional[float] = Field(
        None,
        gt=0,
        le=1.0,
        description="BOR admissível customizado (null = Quadro 17)",
    )
    fator_teu: float = Field(
        1.55,
        gt=0,
        le=3.0,
        description="Fator de conversão TEU/contêiner",
    )
    h_cli: Optional[float] = Field(
        None,
        ge=0,
        description="Horas de indisponibilidade climática/ano",
    )
    h_mnt: Optional[float] = Field(
        None,
        ge=0,
        description="Horas de manutenção/ano",
    )
    notas: Optional[str] = Field(None, max_length=2000)


class TerminalCapacityConfigCreate(TerminalCapacityConfigBase):
    """Payload para criação de configuração de terminal."""

    pass


class TerminalCapacityConfigUpdate(BaseModel):
    """Payload para atualização parcial de configuração."""

    nome_terminal: Optional[str] = Field(None, min_length=1, max_length=255)
    n_bercos: Optional[int] = Field(None, ge=1, le=50)
    h_ef: Optional[float] = Field(None, gt=0, le=8760)
    clearance_h: Optional[float] = Field(None, gt=0, le=24)
    bor_adm_override: Optional[float] = Field(None, gt=0, le=1.0)
    fator_teu: Optional[float] = Field(None, gt=0, le=3.0)
    h_cli: Optional[float] = Field(None, ge=0)
    h_mnt: Optional[float] = Field(None, ge=0)
    notas: Optional[str] = Field(None, max_length=2000)


class TerminalCapacityConfigResponse(TerminalCapacityConfigBase):
    """Resposta com configuração de terminal."""

    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TerminalCapacityConfigListResponse(BaseModel):
    """Lista de configurações de terminal."""

    items: List[TerminalCapacityConfigResponse]
    total: int


# ---------------------------------------------------------------------------
# BOR Quadro 17
# ---------------------------------------------------------------------------

class Quadro17Item(BaseModel):
    """Uma entrada do Quadro 17 UNCTAD."""

    perfil: str = Field(..., description="Perfil de carga canônico")
    faixa_bercos: str = Field(..., description="Faixa de berços (ex: '2-3 berços')")
    n_bercos_min: int = Field(..., description="Número mínimo de berços da faixa")
    bor_adm: float = Field(..., description="BOR admissível (adimensional)")


class Quadro17Response(BaseModel):
    """Quadro 17 completo."""

    items: List[Quadro17Item]
    fallback: float = Field(..., description="BOR admissível padrão (perfil não mapeado)")
