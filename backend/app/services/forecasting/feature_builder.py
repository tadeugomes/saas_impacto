"""
FeatureBuilder — Monta o painel de variáveis para forecast de tonelagem.

Organizado em 5 blocos seguindo a literatura de throughput portuário:

  Bloco 1: Histórico da série (lags, médias móveis, sazonalidade)
  Bloco 2: Macroeconomia e comércio exterior (PIB, câmbio, IBC-Br)
  Bloco 3: Operação do porto (navios, espera, ocupação, produtividade)
  Bloco 4: Safra e logística (CONAB, tipo de carga)
  Bloco 5: Clima e ambiente (precipitação, El Niño, nível de rio)

Referências:
  - Throughput forecasting: séries históricas + PIB + comércio + operação
  - Variáveis climáticas: precipitação + ENSO com lag de 1-6 meses
  - Safra: estimativa CONAB como leading indicator de carga graneleira
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class FeatureBuilder:
    """Constrói painel de features para forecast de tonelagem."""

    def __init__(self):
        self._features_built: List[str] = []

    async def build_panel(
        self,
        id_instalacao: str,
        id_municipio: Optional[str] = None,
        ano_inicio: int = 2014,
        ano_fim: int = 2024,
    ) -> pd.DataFrame:
        """
        Monta painel completo de features para um porto.

        Returns:
            DataFrame com index=date (mensal), colunas de features
        """
        # Bloco 1: Histórico (tonelagem + lags)
        df = await self._build_historical(id_instalacao, ano_inicio, ano_fim)

        if df.empty:
            logger.warning("feature_builder: sem dados históricos para %s", id_instalacao)
            return df

        # Bloco 2: Macro
        df = await self._add_macro_features(df, ano_inicio, ano_fim)

        # Bloco 3: Operação
        df = await self._add_operational_features(df, id_instalacao, ano_inicio, ano_fim)

        # Bloco 4: Safra
        df = await self._add_crop_features(df, id_instalacao)

        # Bloco 5: Clima
        df = await self._add_climate_features(df, id_instalacao, ano_inicio, ano_fim)

        # Remove linhas sem target
        df = df.dropna(subset=["tonelagem"])

        self._features_built = [c for c in df.columns if c != "tonelagem"]
        logger.info(
            "feature_builder: %d features, %d meses, porto=%s",
            len(self._features_built), len(df), id_instalacao,
        )

        return df

    @property
    def feature_names(self) -> List[str]:
        return self._features_built

    # ── Bloco 1: Histórico ──────────────────────────────────────────────

    async def _build_historical(
        self, id_instalacao: str, ano_inicio: int, ano_fim: int,
    ) -> pd.DataFrame:
        """
        Tonelagem mensal + lags (1,3,6,12) + médias móveis + sazonalidade.
        Fonte: ANTAQ via BigQuery.
        """
        from app.db.bigquery.client import get_bigquery_client

        bq = get_bigquery_client()
        sql = f"""
        SELECT
            CAST(ano AS INT64) AS ano,
            CAST(mes AS INT64) AS mes,
            SUM(vlpesocargabruta_oficial) AS tonelagem,
            COUNT(DISTINCT idatracacao) AS atracoes
        FROM
            `antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial`
        WHERE
            porto_atracacao = '{id_instalacao}'
            AND CAST(ano AS INT64) BETWEEN {ano_inicio} AND {ano_fim}
            AND vlpesocargabruta_oficial IS NOT NULL
        GROUP BY ano, mes
        ORDER BY ano, mes
        """

        try:
            rows = await bq.execute_query(sql, timeout_ms=30000)
        except Exception as e:
            logger.warning("feature_builder_bq_error: %s", e)
            return pd.DataFrame()

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(
            df["ano"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2) + "-01"
        )
        df = df.set_index("date").sort_index()
        df["tonelagem"] = pd.to_numeric(df["tonelagem"], errors="coerce")
        df["atracoes"] = pd.to_numeric(df["atracoes"], errors="coerce")

        # Lags
        for lag in [1, 3, 6, 12]:
            df[f"ton_lag_{lag}"] = df["tonelagem"].shift(lag)

        # Médias móveis
        df["ton_ma_3"] = df["tonelagem"].rolling(3).mean()
        df["ton_ma_6"] = df["tonelagem"].rolling(6).mean()
        df["ton_ma_12"] = df["tonelagem"].rolling(12).mean()

        # Crescimento MoM e YoY
        df["ton_mom"] = df["tonelagem"].pct_change(1)
        df["ton_yoy"] = df["tonelagem"].pct_change(12)

        # Sazonalidade
        df["mes_num"] = df.index.month
        df["trimestre"] = df.index.quarter
        df["sin_mes"] = np.sin(2 * np.pi * df.index.month / 12)
        df["cos_mes"] = np.cos(2 * np.pi * df.index.month / 12)

        return df

    # ── Bloco 2: Macroeconomia ──────────────────────────────────────────

    async def _add_macro_features(
        self, df: pd.DataFrame, ano_inicio: int, ano_fim: int,
    ) -> pd.DataFrame:
        """
        Câmbio PTAX, IBC-Br, Selic, IPCA via BACEN.
        Aplicados com lags típicos da literatura.
        """
        from app.clients.bacen import get_bacen_client

        bacen = get_bacen_client()
        inicio = f"01/01/{ano_inicio}"
        fim = f"31/12/{ano_fim}"

        series_config = {
            "cambio": (3698, 1),     # PTAX, lag 1
            "ibc_br": (24364, 1),    # IBC-Br, lag 1
            "selic": (432, 3),       # Selic, lag 3
            "ipca": (433, 0),        # IPCA, lag 0
        }

        for nome, (codigo, lag) in series_config.items():
            try:
                data = await bacen.consultar_serie(codigo, inicio, fim)
                if data:
                    serie_df = self._bcb_to_monthly(data, nome)
                    df = df.join(serie_df, how="left")
                    if lag > 0:
                        df[f"{nome}_lag{lag}"] = df[nome].shift(lag)
            except Exception as e:
                logger.warning("feature_macro_%s_error: %s", nome, e)

        return df

    # ── Bloco 3: Operação ───────────────────────────────────────────────

    async def _add_operational_features(
        self, df: pd.DataFrame, id_instalacao: str, ano_inicio: int, ano_fim: int,
    ) -> pd.DataFrame:
        """
        Navios atendidos, tempo de espera, ocupação de berço, produtividade.
        Fonte: ANTAQ via BigQuery.
        """
        from app.db.bigquery.client import get_bigquery_client

        bq = get_bigquery_client()
        sql = f"""
        SELECT
            CAST(ano AS INT64) AS ano,
            CAST(mes AS INT64) AS mes,
            COUNT(DISTINCT idatracacao) AS navios_atendidos,
            AVG(DATETIME_DIFF(
                PARSE_DATETIME('%Y-%m-%d %H:%M:%S', CONCAT(data_atracacao, ' ', hora_atracacao)),
                PARSE_DATETIME('%Y-%m-%d %H:%M:%S', CONCAT(data_chegada, ' ', hora_chegada)),
                MINUTE
            )) / 60.0 AS tempo_espera_horas,
            AVG(DATETIME_DIFF(
                PARSE_DATETIME('%Y-%m-%d %H:%M:%S', CONCAT(data_desatracacao, ' ', hora_desatracacao)),
                PARSE_DATETIME('%Y-%m-%d %H:%M:%S', CONCAT(data_atracacao, ' ', hora_atracacao)),
                MINUTE
            )) / 60.0 AS tempo_atracacao_horas,
            AVG(SAFE_CAST(calado_saida AS FLOAT64)) AS calado_medio
        FROM
            `antaqdados.br_antaq_estatistico_aquaviario.v_atracacao_validada`
        WHERE
            porto_atracacao = '{id_instalacao}'
            AND CAST(ano AS INT64) BETWEEN {ano_inicio} AND {ano_fim}
        GROUP BY ano, mes
        ORDER BY ano, mes
        """

        try:
            rows = await bq.execute_query(sql, timeout_ms=30000)
            if rows:
                ops_df = pd.DataFrame(rows)
                ops_df["date"] = pd.to_datetime(
                    ops_df["ano"].astype(str) + "-" + ops_df["mes"].astype(str).str.zfill(2) + "-01"
                )
                ops_df = ops_df.set_index("date")
                for col in ["navios_atendidos", "tempo_espera_horas", "tempo_atracacao_horas", "calado_medio"]:
                    if col in ops_df.columns:
                        ops_df[col] = pd.to_numeric(ops_df[col], errors="coerce")
                df = df.join(ops_df[["navios_atendidos", "tempo_espera_horas", "tempo_atracacao_horas", "calado_medio"]], how="left")
        except Exception as e:
            logger.warning("feature_ops_error: %s", e)

        return df

    # ── Bloco 4: Safra ──────────────────────────────────────────────────

    async def _add_crop_features(
        self, df: pd.DataFrame, id_instalacao: str,
    ) -> pd.DataFrame:
        """
        Estimativa de safra CONAB para produtos relevantes ao porto.
        """
        try:
            from app.clients.conab import get_conab_client

            conab = get_conab_client()
            produtos = conab.get_produtos_porto(id_instalacao)

            for produto in produtos[:2]:  # Top 2 produtos
                try:
                    prod_data = await conab.producao_por_uf(produto)
                    total = sum(prod_data.values())
                    # Como CONAB é anual, replica para todos os meses do ano
                    if total > 0:
                        df[f"safra_{produto}_mil_ton"] = total
                except Exception:
                    pass
        except Exception as e:
            logger.warning("feature_crop_error: %s", e)

        return df

    # ── Bloco 5: Clima ──────────────────────────────────────────────────

    async def _add_climate_features(
        self, df: pd.DataFrame, id_instalacao: str, ano_inicio: int, ano_fim: int,
    ) -> pd.DataFrame:
        """
        Precipitação (INMET), El Niño/La Niña (NOAA ONI), nível de rio (ANA).
        """
        # 5a. Precipitação regional (INMET)
        try:
            from app.clients.inmet import get_inmet_client

            inmet = get_inmet_client()
            estacoes = inmet.get_estacoes_porto(id_instalacao)

            for estacao in estacoes[:1]:  # Estação principal
                precip_all = []
                for ano in range(ano_inicio, ano_fim + 1):
                    try:
                        dados = await inmet.precipitacao_acumulada_mensal(
                            estacao["codigo"], ano
                        )
                        precip_all.extend(dados)
                    except Exception:
                        continue

                if precip_all:
                    precip_df = pd.DataFrame(precip_all)
                    precip_df["date"] = pd.to_datetime(
                        precip_df["ano"].astype(str) + "-" + precip_df["mes"].astype(str).str.zfill(2) + "-01"
                    )
                    precip_df = precip_df.set_index("date")
                    df = df.join(precip_df[["precipitacao_acumulada_mm"]], how="left")
                    # Lag de 1-2 meses (chuva → colheita → transporte → porto)
                    df["precip_lag1"] = df.get("precipitacao_acumulada_mm", pd.Series(dtype=float)).shift(1)
                    df["precip_lag2"] = df.get("precipitacao_acumulada_mm", pd.Series(dtype=float)).shift(2)
        except Exception as e:
            logger.warning("feature_inmet_error: %s", e)

        # 5b. El Niño / La Niña (NOAA ONI)
        try:
            from app.clients.noaa_enso import get_noaa_enso_client

            noaa = get_noaa_enso_client()
            oni_data = await noaa.get_oni_por_periodo(ano_inicio, ano_fim)

            if oni_data:
                oni_df = pd.DataFrame(oni_data)
                oni_df["date"] = pd.to_datetime(
                    oni_df["ano"].astype(str) + "-" + oni_df["mes"].astype(str).str.zfill(2) + "-01"
                )
                oni_df = oni_df.set_index("date")
                df = df.join(oni_df[["oni"]], how="left")
                # ONI com lag longo (3-6 meses para afetar safra)
                df["oni_lag3"] = df.get("oni", pd.Series(dtype=float)).shift(3)
                df["oni_lag6"] = df.get("oni", pd.Series(dtype=float)).shift(6)
        except Exception as e:
            logger.warning("feature_enso_error: %s", e)

        # 5c. Nível do rio (ANA) — apenas para portos fluviais
        try:
            from app.clients.ana import get_ana_client

            ana = get_ana_client()
            estacao = ana.get_estacao_for_porto(id_instalacao)

            if estacao:
                dados = await ana.consultar_nivel_rio(estacao["codigo"])
                if dados:
                    nivel_df = pd.DataFrame(dados)
                    nivel_df["date"] = pd.to_datetime(nivel_df["data"], errors="coerce")
                    nivel_df = nivel_df.dropna(subset=["date"])
                    nivel_df = nivel_df.set_index("date").resample("MS").mean()
                    df = df.join(nivel_df[["nivel_metros"]], how="left")
        except Exception as e:
            logger.warning("feature_ana_error: %s", e)

        return df

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _bcb_to_monthly(data: List[Dict], col_name: str) -> pd.DataFrame:
        """Converte série BCB (dd/MM/yyyy) para DataFrame mensal."""
        records = []
        for item in data:
            try:
                parts = item["data"].split("/")
                dt = pd.Timestamp(int(parts[2]), int(parts[1]), 1)
                records.append({"date": dt, col_name: float(item["valor"])})
            except (ValueError, KeyError, IndexError):
                continue

        if not records:
            return pd.DataFrame(columns=[col_name])

        df = pd.DataFrame(records).set_index("date")
        return df.resample("MS").last()
