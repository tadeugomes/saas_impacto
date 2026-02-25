"""Construção de painéis para análise causal.

Portado de new_impacto/src/causal/prep.py — sem alterações funcionais,
apenas ajuste de path de imports.
"""
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

UF_CODE_MAP: dict[str, str] = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA",
    "16": "AP", "17": "TO", "21": "MA", "22": "PI", "23": "CE",
    "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE",
    "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT",
    "52": "GO", "53": "DF",
}


def add_uf_from_municipio(
    df: pd.DataFrame,
    col: str = "id_municipio",
) -> pd.DataFrame:
    """Infere a UF a partir dos dois primeiros dígitos do código IBGE do município."""
    out = df.copy()
    out[col] = out[col].astype(str)
    out["uf"] = out[col].str[:2].map(UF_CODE_MAP)
    return out


def build_did_panel(
    df: pd.DataFrame,
    treated_ids: Iterable[str],
    post_year: int,
    scope: str = "state",
) -> pd.DataFrame:
    """Constrói painel pronto para DiD com indicadores treated/post/did.

    Parameters
    ----------
    df:
        Painel com colunas [id_municipio, ano, ...].
    treated_ids:
        IDs IBGE dos municípios tratados.
    post_year:
        Primeiro ano do período pós-tratamento.
    scope:
        ``"state"`` mantém apenas as UFs com municípios tratados;
        ``"all"`` usa todo o país.

    Returns
    -------
    pd.DataFrame
        Painel enriquecido com colunas: ``uf``, ``treated``, ``post``, ``did``.
    """
    panel = add_uf_from_municipio(df)
    treated_ids_set = {str(x) for x in treated_ids}
    panel["treated"] = panel["id_municipio"].astype(str).isin(treated_ids_set).astype(int)
    panel["post"] = (panel["ano"] >= post_year).astype(int)
    panel["did"] = panel["treated"] * panel["post"]

    if scope == "state":
        treated_ufs = panel.loc[panel["treated"] == 1, "uf"].dropna().unique()
        panel = panel[panel["uf"].isin(treated_ufs)].copy()

    return panel


def aggregate_panel_by_uf_year(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega painel municipal para nível UF-ano com features em log."""
    panel = add_uf_from_municipio(df)
    group = panel.groupby(["uf", "ano"], as_index=False).agg(
        n_vinculos=("n_vinculos", "sum"),
        receitas_total=("receitas_total", "sum"),
        despesas_total=("despesas_total", "sum"),
        pib=("pib", "sum"),
        remuneracao_media=("remuneracao_media", "mean"),
        ipca_media=("ipca_media", "mean"),
    )
    for col in ["n_vinculos", "receitas_total", "despesas_total", "pib", "remuneracao_media"]:
        group[f"{col}_log"] = np.log(group[col].replace(0, np.nan))
    return group


def aggregate_antaq_by_uf_year(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega painel ANTAQ para nível UF-ano com features em log."""
    group = df.groupby(["uf", "ano"], as_index=False).agg(
        toneladas=("toneladas", "sum"),
        n_registros=("n_registros", "sum"),
        n_atracacao=("n_atracacao", "sum"),
        tempo_medio_atracado=("tempo_medio_atracado", "mean"),
        tempo_medio_operacao=("tempo_medio_operacao", "mean"),
        vista_rs=("vista_rs", "mean"),
        vista_usd=("vista_usd", "mean"),
    )
    for col in ["toneladas", "n_registros", "n_atracacao", "vista_rs", "vista_usd"]:
        group[f"{col}_log"] = np.log(group[col].replace(0, np.nan))
    return group
