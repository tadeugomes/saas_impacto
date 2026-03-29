"""
FeatureBuilder — Monta o painel de variáveis para forecast de tonelagem.

Organizado em 5 blocos seguindo a literatura de throughput portuário:

  Bloco 1: Histórico da série (lags, médias móveis, sazonalidade)
  Bloco 2: Macroeconomia e comércio exterior (PIB, câmbio, IBC-Br)
  Bloco 3: Operação do porto (navios, espera, ocupação, produtividade)
  Bloco 4: Safra e logística (CONAB, tipo de carga)
  Bloco 5: Clima e ambiente (precipitação, El Niño, nível de rio)

Cada feature é categorizada como:
  - "exogena": variável real de fonte externa (BACEN, INMET, CONAB, etc.),
    projetável via cenários para forecast out-of-sample
  - "derivada": variável derivada do próprio target (lags, MA, MoM, YoY),
    útil no ajuste mas não projetável em horizonte longo

O SarimaxEngine usa essa categorização para priorizar exógenas reais na
seleção de features e gerar projeções corretas para forecast.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Prefixos de features derivadas do target (não projetáveis)
_TARGET_DERIVED_PREFIXES = (
    "ton_lag_", "ton_ma_", "ton_mom", "ton_yoy",
    "mes_num", "trimestre", "sin_mes", "cos_mes",
    "atracoes", "ano",
)

# ── Pesos mensais de escoamento portuário por produto ──────────────
# Distribuição típica de exportação ao longo do ano para os principais
# grãos em portos brasileiros (Santos, Paranaguá, Rio Grande).
# Fonte: perfil mensal médio 2018-2023, MDIC/Comex Stat.
# Soma = 1.0 para cada produto.
_SAFRA_PESO_MENSAL = {
    #                  jan   fev   mar   abr   mai   jun   jul   ago   set   out   nov   dez
    "soja": {
        1: 0.02, 2: 0.04, 3: 0.12, 4: 0.16, 5: 0.16, 6: 0.14,
        7: 0.10, 8: 0.08, 9: 0.06, 10: 0.05, 11: 0.04, 12: 0.03,
    },
    "milho": {
        1: 0.02, 2: 0.02, 3: 0.02, 4: 0.03, 5: 0.04, 6: 0.06,
        7: 0.12, 8: 0.16, 9: 0.16, 10: 0.14, 11: 0.12, 12: 0.11,
    },
    "açúcar": {
        1: 0.03, 2: 0.03, 3: 0.04, 4: 0.06, 5: 0.08, 6: 0.10,
        7: 0.12, 8: 0.13, 9: 0.12, 10: 0.11, 11: 0.10, 12: 0.08,
    },
    "café": {
        1: 0.05, 2: 0.05, 3: 0.06, 4: 0.06, 5: 0.07, 6: 0.08,
        7: 0.10, 8: 0.11, 9: 0.11, 10: 0.10, 11: 0.11, 12: 0.10,
    },
}
_PESO_UNIFORME = {m: 1.0 / 12 for m in range(1, 13)}


class FeatureBuilder:
    """Constrói painel de features para forecast de tonelagem."""

    def __init__(self):
        self._features_built: List[str] = []
        self._feature_blocks: Dict[str, List[str]] = {}
        self._blocks_status: Dict[str, str] = {}

    async def build_panel(
        self,
        id_instalacao: str,
        id_municipio: Optional[str] = None,
        ano_inicio: int = 2014,
        ano_fim: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Monta painel completo de features para um porto.

        Returns:
            DataFrame com index=date (mensal, freq=MS), colunas de features
        """
        self._feature_blocks = {}
        self._blocks_status = {}

        if ano_fim is None:
            from datetime import datetime
            ano_fim = datetime.now().year

        # Bloco 1: Histórico (tonelagem + lags)
        df = await self._build_historical(id_instalacao, ano_inicio, ano_fim)

        if df.empty:
            logger.warning("feature_builder: sem dados históricos para %s", id_instalacao)
            return df

        cols_before = set(df.columns)

        # Bloco 2: Macro
        df = await self._add_macro_features(df, ano_inicio, ano_fim)
        self._register_block("macro", df, cols_before)
        cols_before = set(df.columns)

        # Bloco 3: Operação
        df = await self._add_operational_features(df, id_instalacao, ano_inicio, ano_fim)
        self._register_block("operacao", df, cols_before)
        cols_before = set(df.columns)

        # Bloco 4: Safra
        df = await self._add_crop_features(df, id_instalacao)
        self._register_block("safra", df, cols_before)
        cols_before = set(df.columns)

        # Bloco 5: Clima
        df = await self._add_climate_features(df, id_instalacao, ano_inicio, ano_fim)
        self._register_block("clima", df, cols_before)

        # Frequência explícita para evitar warnings do statsmodels
        df = df.asfreq("MS")

        # Remove linhas sem target
        df = df.dropna(subset=["tonelagem"])

        self._features_built = [c for c in df.columns if c != "tonelagem"]

        # Registra bloco 1 (histórico = tudo que não é dos blocos 2-5)
        exog_features = set()
        for feats in self._feature_blocks.values():
            exog_features.update(feats)
        self._feature_blocks["historico"] = [
            f for f in self._features_built if f not in exog_features
        ]

        n_exog = sum(
            len(v) for k, v in self._feature_blocks.items() if k != "historico"
        )
        n_hist = len(self._feature_blocks.get("historico", []))

        logger.info(
            "feature_builder: %d features (%d exógenas reais + %d históricas), "
            "%d meses, porto=%s, blocos=%s",
            len(self._features_built), n_exog, n_hist,
            len(df), id_instalacao, self._blocks_status,
        )

        return df

    @property
    def feature_names(self) -> List[str]:
        return self._features_built

    @property
    def feature_blocks(self) -> Dict[str, List[str]]:
        """Mapeamento bloco → lista de features daquele bloco."""
        return self._feature_blocks

    @property
    def exogenous_features(self) -> List[str]:
        """Features de fontes externas (projetáveis para forecast)."""
        exog = []
        for block, feats in self._feature_blocks.items():
            if block != "historico":
                exog.extend(feats)
        return exog

    @property
    def derived_features(self) -> List[str]:
        """Features derivadas do target (não projetáveis)."""
        return self._feature_blocks.get("historico", [])

    @property
    def blocks_status(self) -> Dict[str, str]:
        """Status de cada bloco externo: 'ok' ou 'sem_dados'."""
        return self._blocks_status

    def classify_feature(self, col: str) -> str:
        """Retorna 'exogena' ou 'derivada' para uma feature."""
        for prefix in _TARGET_DERIVED_PREFIXES:
            if col.startswith(prefix) or col == prefix:
                return "derivada"
        for block, feats in self._feature_blocks.items():
            if block != "historico" and col in feats:
                return "exogena"
        return "derivada"

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
            "selic": (4189, 3),      # Selic meta mensal, lag 3
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
        # Coluna `mes` em v_atracacao_validada é texto ("jan","fev",...).
        # Extraímos ano e mês diretamente de data_atracacao.
        # ANTAQ mistura formatos de data entre anos: algumas colunas vêm
        # como 'YYYY-MM-DD HH:MM:SS', outras como 'DD/MM/YYYY HH:MM:SS'.
        # Usamos COALESCE + SAFE.PARSE_DATETIME para aceitar ambos.
        sql = f"""
        SELECT
            EXTRACT(YEAR FROM dt_atracacao) AS ano,
            EXTRACT(MONTH FROM dt_atracacao) AS mes,
            COUNT(DISTINCT idatracacao) AS navios_atendidos,
            AVG(DATETIME_DIFF(dt_atracacao, dt_chegada, MINUTE)) / 60.0 AS tempo_espera_horas,
            AVG(DATETIME_DIFF(dt_desatracacao, dt_atracacao, MINUTE)) / 60.0 AS tempo_atracacao_horas
        FROM (
            SELECT
                idatracacao,
                COALESCE(
                    SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_atracacao),
                    SAFE.PARSE_DATETIME('%d/%m/%Y %H:%M:%S', data_atracacao)
                ) AS dt_atracacao,
                COALESCE(
                    SAFE.PARSE_DATETIME('%d/%m/%Y %H:%M:%S', data_chegada),
                    SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_chegada)
                ) AS dt_chegada,
                COALESCE(
                    SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_desatracacao),
                    SAFE.PARSE_DATETIME('%d/%m/%Y %H:%M:%S', data_desatracacao)
                ) AS dt_desatracacao
            FROM
                `antaqdados.br_antaq_estatistico_aquaviario.v_atracacao_validada`
            WHERE
                porto_atracacao = '{id_instalacao}'
                AND CAST(ano AS INT64) BETWEEN {ano_inicio} AND {ano_fim}
                AND data_atracacao IS NOT NULL
                AND data_chegada IS NOT NULL
                AND data_desatracacao IS NOT NULL
        )
        WHERE dt_atracacao IS NOT NULL AND dt_chegada IS NOT NULL AND dt_desatracacao IS NOT NULL
        GROUP BY ano, mes
        ORDER BY ano, mes
        """

        try:
            rows = await bq.execute_query(sql, timeout_ms=30000)
            if rows:
                ops_df = pd.DataFrame(rows)
                ops_df["date"] = pd.to_datetime(
                    ops_df["ano"].astype(int).astype(str) + "-" + ops_df["mes"].astype(int).astype(str).str.zfill(2) + "-01"
                )
                ops_df = ops_df.set_index("date")
                op_cols = ["navios_atendidos", "tempo_espera_horas", "tempo_atracacao_horas"]
                for col in op_cols:
                    if col in ops_df.columns:
                        ops_df[col] = pd.to_numeric(ops_df[col], errors="coerce")
                available = [c for c in op_cols if c in ops_df.columns]
                df = df.join(ops_df[available], how="left")
        except Exception as e:
            logger.warning("feature_ops_error: %s", e)

        return df

    # ── Bloco 4: Safra ──────────────────────────────────────────────────
    # Pesos mensais de escoamento portuário por produto.
    # Fonte: perfil de exportação mensal de Santos/Paranaguá (ANTAQ/MDIC).
    # Soma dos 12 pesos = 1.0 para cada produto.

    async def _add_crop_features(
        self, df: pd.DataFrame, id_instalacao: str,
    ) -> pd.DataFrame:
        """
        Features de safra com variação mensal real.

        Em vez de replicar a produção anual em todos os 12 meses (valor
        constante intra-anual, eliminado pela diferenciação d=1 + D=1
        do SARIMAX), distribui a produção anual por mês usando pesos
        de sazonalidade de escoamento portuário.

        Features geradas por produto:
          - safra_{produto}_mil_ton: produção mensal estimada (anual × peso_mes)
          - safra_{produto}_yoy: variação % ano a ano da produção anual
        """
        try:
            from app.clients.conab import get_conab_client

            conab = get_conab_client()
            produtos = conab.get_produtos_porto(id_instalacao)

            for produto in produtos[:2]:  # Top 2 produtos
                try:
                    serie = await conab.serie_producao_anual(produto, n_anos=15)
                    if not serie:
                        continue
                    ano_prod = {item["ano"]: item["producao_mil_ton"] for item in serie}
                    if not ano_prod:
                        continue

                    # Pesos de sazonalidade de escoamento por produto.
                    # Baseado no perfil mensal de exportação em Santos/Paranaguá.
                    pesos = _SAFRA_PESO_MENSAL.get(produto, _PESO_UNIFORME)

                    col_prod = f"safra_{produto}_mil_ton"
                    col_yoy = f"safra_{produto}_yoy"

                    # Produção mensal = produção_anual × peso do mês
                    df[col_prod] = [
                        ano_prod.get(y, np.nan) * pesos.get(m, 1 / 12)
                        for y, m in zip(df.index.year, df.index.month)
                    ]

                    # Variação % ano a ano (mesmo mês, valor diferente pelo peso)
                    anos_sorted = sorted(ano_prod.keys())
                    yoy_map = {}
                    for i, ano in enumerate(anos_sorted):
                        if i == 0:
                            yoy_map[ano] = 0.0
                        else:
                            prev = ano_prod.get(anos_sorted[i - 1], 0)
                            curr = ano_prod[ano]
                            yoy_map[ano] = ((curr - prev) / prev * 100) if prev else 0.0
                    df[col_yoy] = df.index.year.map(
                        lambda y, ym=yoy_map: ym.get(y, np.nan)
                    )

                    logger.info(
                        "feature_crop_%s: %d anos, range=%s-%s, pesos=%s",
                        produto, len(ano_prod), min(ano_prod), max(ano_prod),
                        "sazonais" if produto in _SAFRA_PESO_MENSAL else "uniformes",
                    )
                except Exception as e:
                    logger.warning("feature_crop_%s_error: %s", produto, e)
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
                    # Lag de 1-2 meses (chuva -> colheita -> transporte -> porto)
                    df["precip_lag1"] = df.get("precipitacao_acumulada_mm", pd.Series(dtype=float)).shift(1)
                    df["precip_lag2"] = df.get("precipitacao_acumulada_mm", pd.Series(dtype=float)).shift(2)
        except Exception as e:
            logger.warning("feature_inmet_error: %s", e)

        # 5b. El Niño / La Niña (NOAA ONI)
        try:
            from app.clients.noaa_enso import get_noaa_enso_client

            noaa = get_noaa_enso_client()
            oni_data = await noaa.get_oni_por_periodo(ano_inicio, ano_fim)
            logger.info("feature_enso: %d registros ONI recebidos", len(oni_data) if oni_data else 0)

            if oni_data:
                oni_df = pd.DataFrame(oni_data)
                oni_df["date"] = pd.to_datetime(
                    oni_df["ano"].astype(str) + "-" + oni_df["mes"].astype(str).str.zfill(2) + "-01"
                )
                # Remove duplicatas (manter último valor por mês)
                oni_df = oni_df.drop_duplicates(subset=["date"], keep="last")
                oni_df = oni_df.set_index("date").sort_index()
                oni_df["oni"] = pd.to_numeric(oni_df["oni"], errors="coerce")
                df = df.join(oni_df[["oni"]], how="left")
                # ONI com lag longo (3-6 meses para afetar safra)
                if "oni" in df.columns:
                    df["oni_lag3"] = df["oni"].shift(3)
                    df["oni_lag6"] = df["oni"].shift(6)
                    n_valid = df["oni"].notna().sum()
                    logger.info("feature_enso: oni joined, %d valores não-nulos de %d", n_valid, len(df))
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

    def _register_block(
        self, block_name: str, df: pd.DataFrame, cols_before: set
    ) -> None:
        """Registra as features adicionadas por um bloco externo."""
        new_cols = [c for c in df.columns if c not in cols_before]
        self._feature_blocks[block_name] = new_cols
        self._blocks_status[block_name] = "ok" if new_cols else "sem_dados"

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
