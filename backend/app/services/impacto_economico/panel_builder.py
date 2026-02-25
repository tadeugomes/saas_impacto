"""Bridge BigQuery → pd.DataFrame para o engine causal de Impacto Econômico.

``EconomicImpactPanelBuilder`` é o ponto central de integração entre
o Data Warehouse (BigQuery) e as rotinas causais (DiD / IV / Panel IV).

Fluxo:
    1. Recebe parâmetros do painel (municípios, período, modo).
    2. Gera o SQL correto via ``app.db.bigquery.queries.impacto_economico_panel``.
    3. Executa via ``BigQueryClient.execute_query()`` (async, run_in_executor).
    4. Converte ``List[dict]`` → ``pd.DataFrame`` com tipos corretos.
    5. Aplica transformações de preparação:
       - ``prep.add_uf_from_municipio()`` — coluna ``uf`` a partir do código IBGE.
       - ``prep.build_did_panel()`` — colunas ``treated``, ``post``, ``did``
         (somente modo DiD).
    6. Valida colunas obrigatórias e retorna o DataFrame pronto para o engine.
"""
from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from app.db.bigquery.client import BigQueryClient, BigQueryError
from app.db.bigquery.queries.impacto_economico_panel import (
    query_causal_panel_from_mart,
    query_causal_panel_municipal,
    query_commodities_iv_panel,
    query_causal_panel_uf_year,
)
from app.services.impacto_economico.causal.prep import (
    add_uf_from_municipio,
    build_did_panel,
)

logger = logging.getLogger(__name__)

# ── Colunas mínimas que o engine causal exige ────────────────────────────────
REQUIRED_COLUMNS_BASE: list[str] = ["id_municipio", "ano"]
REQUIRED_COLUMNS_DID: list[str] = REQUIRED_COLUMNS_BASE + ["treated", "post", "did"]
REQUIRED_COLUMNS_IV: list[str] = REQUIRED_COLUMNS_BASE

# ── Tipos esperados após conversão ───────────────────────────────────────────
DTYPE_MAP: dict[str, str] = {
    "id_municipio": "str",
    "ano": "int64",
    "pib": "float64",
    "n_vinculos": "float64",
    "empregos_totais": "float64",
    "toneladas_antaq": "float64",
    "populacao": "float64",
    "pib_per_capita": "float64",
    "ipca_media": "float64",
    "receitas_total": "float64",
    "despesas_total": "float64",
    "remuneracao_media": "float64",
    "comercio_dolar": "float64",
    "exportacao_dolar": "float64",
    "importacao_dolar": "float64",
    "massa_salarial_portuaria": "float64",
    "massa_salarial_total": "float64",
    "vab_servicos": "float64",
    "vab_industria": "float64",
    # log-transformadas
    "pib_log": "float64",
    "n_vinculos_log": "float64",
    "pib_per_capita_log": "float64",
    "populacao_log": "float64",
    "toneladas_antaq_log": "float64",
    "comercio_dolar_log": "float64",
    # lags
    "pib_lag1": "float64",
    "n_vinculos_lag1": "float64",
    "empregos_portuarios_lag1": "float64",
}


class PanelValidationError(ValueError):
    """Painel retornado pelo BigQuery não atende requisitos mínimos."""


class EconomicImpactPanelBuilder:
    """Constrói DataFrames para o engine causal de impacto econômico.

    Parameters
    ----------
    bq_client:
        Instância de ``BigQueryClient``. Se não fornecida, será criada
        internamente (útil em testes com mock).
    timeout_ms:
        Timeout para execução das queries no BigQuery (milissegundos).
    """

    def __init__(
        self,
        bq_client: BigQueryClient | None = None,
        timeout_ms: int = 60_000,
    ) -> None:
        if bq_client is None:
            from app.db.bigquery.client import get_bigquery_client
            bq_client = get_bigquery_client()
        self._bq = bq_client
        self._timeout_ms = timeout_ms

    # ──────────────────────────────────────────────────────────────────────────
    # Método principal — DiD municipal
    # ──────────────────────────────────────────────────────────────────────────

    async def build_did_panel(
        self,
        treated_municipios: list[str],
        control_municipios: list[str],
        treatment_year: int,
        ano_inicio: int = 2010,
        ano_fim: int = 2023,
        use_mart: bool = True,
        include_siconfi: bool = False,
        include_lags: bool = True,
        scope: str = "state",
    ) -> pd.DataFrame:
        """Monta painel DiD completo (treated/control × pre/post).

        Parameters
        ----------
        treated_municipios:
            Códigos IBGE dos municípios tratados.
        control_municipios:
            Códigos IBGE dos municípios de controle.
        treatment_year:
            Ano de tratamento (define a coluna ``post``).
        ano_inicio / ano_fim:
            Intervalo de anos do painel.
        use_mart:
            Se True, usa o mart pré-calculado (recomendado). Se False,
            usa fontes brutas (RAIS, PIB, SICONFI, ANTAQ).
        include_siconfi:
            Incluir dados SICONFI (só usado quando ``use_mart=False``).
        include_lags:
            Incluir variáveis defasadas.
        scope:
            Escopo para ``prep.build_did_panel()`` (``"state"`` ou ``"municipal"``).

        Returns
        -------
        pd.DataFrame com colunas ``treated``, ``post``, ``did`` adicionadas.
        """
        all_municipios = list(dict.fromkeys(treated_municipios + control_municipios))

        logger.info(
            "Buscando painel DiD: %d tratados, %d controles, %d–%d",
            len(treated_municipios),
            len(control_municipios),
            ano_inicio,
            ano_fim,
        )

        df = await self._fetch_panel(
            id_municipios=all_municipios,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
            use_mart=use_mart,
            include_siconfi=include_siconfi,
            include_lags=include_lags,
        )

        if df.empty:
            raise PanelValidationError(
                f"Painel vazio para municípios={all_municipios}, "
                f"período={ano_inicio}–{ano_fim}."
            )

        # Infere UF (se não vier do mart)
        if "uf" not in df.columns:
            df = add_uf_from_municipio(df, col="id_municipio")

        # Cria colunas DiD: treated / post / did
        df = build_did_panel(
            df=df,
            treated_ids=treated_municipios,
            post_year=treatment_year,
            scope=scope,
        )

        self._validate(df, mode="did")
        return df

    # ──────────────────────────────────────────────────────────────────────────
    # Painel IV (municípios + commodities como instrumento)
    # ──────────────────────────────────────────────────────────────────────────

    async def build_iv_panel(
        self,
        id_municipios: list[str],
        ano_inicio: int = 2010,
        ano_fim: int = 2023,
        commodity_cols: list[str] | None = None,
    ) -> pd.DataFrame:
        """Monta painel para Panel IV com preços de commodities como instrumento.

        Requer que ``marts_impacto.external.worldbank_commodities`` exista
        (via ``scripts/ingest_worldbank_commodities.py``).

        Parameters
        ----------
        commodity_cols:
            Colunas de commodities a incluir. Se None, todas.

        Returns
        -------
        pd.DataFrame com painel municipal + preços de commodities.
        """
        logger.info(
            "Buscando painel IV: %d municípios, %d–%d, commodities=%s",
            len(id_municipios),
            ano_inicio,
            ano_fim,
            commodity_cols or "all",
        )

        sql = query_commodities_iv_panel(
            id_municipios=id_municipios,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
            commodity_cols=commodity_cols,
        )
        rows = await self._bq.execute_query(sql, timeout_ms=self._timeout_ms)
        df = self._rows_to_dataframe(rows)

        if df.empty:
            raise PanelValidationError(
                "Painel IV vazio. Verifique se worldbank_commodities foi ingerida."
            )

        if "uf" not in df.columns:
            df = add_uf_from_municipio(df, col="id_municipio")

        self._validate(df, mode="iv")
        return df

    # ──────────────────────────────────────────────────────────────────────────
    # Painel UF-ano (DiD / SCM estadual)
    # ──────────────────────────────────────────────────────────────────────────

    async def build_uf_panel(
        self,
        ufs: list[str],
        ano_inicio: int = 2010,
        ano_fim: int = 2023,
    ) -> pd.DataFrame:
        """Monta painel agregado por UF-ano.

        Parameters
        ----------
        ufs:
            Lista de siglas UF (ex.: ['MA', 'PA', 'RJ']).

        Returns
        -------
        pd.DataFrame com granularidade UF-ano.
        """
        logger.info("Buscando painel UF-ano: %s, %d–%d", ufs, ano_inicio, ano_fim)

        sql = query_causal_panel_uf_year(
            ufs=ufs,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )
        rows = await self._bq.execute_query(sql, timeout_ms=self._timeout_ms)
        df = self._rows_to_dataframe(rows)

        if df.empty:
            raise PanelValidationError(f"Painel UF-ano vazio para ufs={ufs}.")

        # Painel UF usa "uf" como identificador de entidade, não id_municipio
        required = ["uf", "ano"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise PanelValidationError(f"Colunas ausentes no painel UF: {missing}")

        return df

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers internos
    # ──────────────────────────────────────────────────────────────────────────

    async def _fetch_panel(
        self,
        id_municipios: list[str],
        ano_inicio: int,
        ano_fim: int,
        use_mart: bool,
        include_siconfi: bool,
        include_lags: bool,
    ) -> pd.DataFrame:
        """Executa a query apropriada e retorna DataFrame."""
        if use_mart:
            sql = query_causal_panel_from_mart(
                id_municipios=id_municipios,
                ano_inicio=ano_inicio,
                ano_fim=ano_fim,
                include_lags=include_lags,
            )
        else:
            sql = query_causal_panel_municipal(
                id_municipios=id_municipios,
                ano_inicio=ano_inicio,
                ano_fim=ano_fim,
                include_siconfi=include_siconfi,
                include_antaq=True,
                include_lags=include_lags,
            )

        try:
            rows = await self._bq.execute_query(sql, timeout_ms=self._timeout_ms)
        except BigQueryError as exc:
            if "not found" in str(exc).lower() and use_mart:
                logger.warning(
                    "Mart não encontrado; fazendo fallback para fontes brutas. "
                    "Detalhe: %s",
                    exc,
                )
                sql = query_causal_panel_municipal(
                    id_municipios=id_municipios,
                    ano_inicio=ano_inicio,
                    ano_fim=ano_fim,
                    include_siconfi=include_siconfi,
                    include_antaq=True,
                    include_lags=include_lags,
                )
                rows = await self._bq.execute_query(sql, timeout_ms=self._timeout_ms)
            else:
                raise

        return self._rows_to_dataframe(rows)

    @staticmethod
    def _rows_to_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
        """Converte ``List[dict]`` → ``pd.DataFrame`` com tipos corretos.

        - Remove coluna interna ``_query_ts``.
        - Aplica ``DTYPE_MAP`` a colunas presentes.
        - Garante ``id_municipio`` como string.
        """
        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)

        # Remove metadado interno
        df = df.drop(columns=["_query_ts"], errors="ignore")

        # Converte tipos
        for col, dtype in DTYPE_MAP.items():
            if col in df.columns:
                try:
                    df[col] = df[col].astype(dtype)
                except (ValueError, TypeError) as exc:
                    logger.debug("Não foi possível converter %s para %s: %s", col, dtype, exc)

        # Garante ordenação canônica
        sort_cols = [c for c in ["id_municipio", "ano"] if c in df.columns]
        if sort_cols:
            df = df.sort_values(sort_cols).reset_index(drop=True)

        return df

    @staticmethod
    def _validate(df: pd.DataFrame, mode: str = "did") -> None:
        """Valida colunas obrigatórias para o modo solicitado.

        Raises
        ------
        PanelValidationError
            Se alguma coluna obrigatória estiver ausente.
        """
        if mode == "did":
            required = REQUIRED_COLUMNS_DID
        else:
            required = REQUIRED_COLUMNS_IV

        missing = [c for c in required if c not in df.columns]
        if missing:
            raise PanelValidationError(
                f"Painel modo='{mode}' faltando colunas: {missing}. "
                f"Colunas disponíveis: {sorted(df.columns.tolist())}"
            )

        if df.empty:
            raise PanelValidationError("Painel retornado está vazio.")

        logger.info(
            "Painel validado: %d linhas, %d colunas, modo=%s",
            len(df),
            len(df.columns),
            mode,
        )
