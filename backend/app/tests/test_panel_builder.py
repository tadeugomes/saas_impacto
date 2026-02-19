"""Testes unitários de EconomicImpactPanelBuilder com BigQuery mockado.

Todos os testes usam ``unittest.mock.AsyncMock`` para substituir
``BigQueryClient.execute_query``, eliminando dependência de rede/credenciais.

Cobertura:
  - TestRowsToDataframe    — conversão List[dict] → pd.DataFrame
  - TestValidate           — PanelValidationError quando colunas faltam
  - TestBuildDidPanel      — fluxo principal DiD: colunas tratado/post/did
  - TestBuildDidPanelFallback — fallback mart-not-found → raw query
  - TestBuildIvPanel       — painel IV com commodities
  - TestBuildUfPanel       — painel agregado UF-ano
  - TestIngestScript       — parsing do Pink Sheet (sem BigQuery)
"""
from __future__ import annotations

import io
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Helpers para geração de dados sintéticos
# ---------------------------------------------------------------------------

def _make_rows(
    municipios: list[str],
    anos: list[int],
    extra_cols: dict | None = None,
) -> list[dict]:
    """Gera lista de dicionários no formato retornado por BigQueryClient."""
    rows: list[dict] = []
    for mun in municipios:
        for ano in anos:
            row: dict = {
                "id_municipio": mun,
                "ano": ano,
                "pib": float(np.random.randint(1_000_000, 50_000_000)),
                "n_vinculos": float(np.random.randint(50, 2000)),
                "empregos_totais": float(np.random.randint(500, 20000)),
                "toneladas_antaq": float(np.random.randint(10_000, 500_000)),
                "populacao": float(np.random.randint(20_000, 500_000)),
                "pib_per_capita": float(np.random.uniform(5_000, 40_000)),
                "ipca_media": float(np.random.uniform(95, 110)),
                "pib_log": float(np.log(1_000_000 + np.random.randint(0, 5_000_000))),
                "n_vinculos_log": float(np.log(100 + np.random.randint(0, 500))),
            }
            if extra_cols:
                row.update(extra_cols)
            rows.append(row)
    return rows


TREATED = ["2100055", "2100105"]
CONTROL = ["2100204", "2100303", "2100402"]
ALL_MUNS = TREATED + CONTROL
ANOS = list(range(2012, 2020))
TREATMENT_YEAR = 2015


# ---------------------------------------------------------------------------
# _rows_to_dataframe
# ---------------------------------------------------------------------------

class TestRowsToDataframe:
    def test_empty_returns_empty_df(self):
        from app.services.impacto_economico.panel_builder import (
            EconomicImpactPanelBuilder,
        )
        df = EconomicImpactPanelBuilder._rows_to_dataframe([])
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_basic_conversion(self):
        from app.services.impacto_economico.panel_builder import (
            EconomicImpactPanelBuilder,
        )
        rows = _make_rows(ALL_MUNS, ANOS)
        df = EconomicImpactPanelBuilder._rows_to_dataframe(rows)

        assert len(df) == len(ALL_MUNS) * len(ANOS)
        assert "id_municipio" in df.columns
        assert "ano" in df.columns
        assert df["ano"].dtype == np.int64
        assert df["id_municipio"].dtype == object  # str

    def test_removes_query_ts(self):
        from app.services.impacto_economico.panel_builder import (
            EconomicImpactPanelBuilder,
        )
        rows = _make_rows(["2100055"], [2015])
        rows[0]["_query_ts"] = "2024-01-01T00:00:00"

        df = EconomicImpactPanelBuilder._rows_to_dataframe(rows)
        assert "_query_ts" not in df.columns

    def test_sorted_by_municipio_ano(self):
        from app.services.impacto_economico.panel_builder import (
            EconomicImpactPanelBuilder,
        )
        rows = _make_rows(["2100303", "2100055"], [2014, 2012, 2013])
        df = EconomicImpactPanelBuilder._rows_to_dataframe(rows)

        # Deve estar ordenado por id_municipio, depois ano
        assert df["id_municipio"].iloc[0] <= df["id_municipio"].iloc[-1]
        for mun, grp in df.groupby("id_municipio"):
            assert grp["ano"].is_monotonic_increasing

    def test_numeric_cols_are_float64(self):
        from app.services.impacto_economico.panel_builder import (
            EconomicImpactPanelBuilder,
        )
        rows = _make_rows(["2100055"], [2015, 2016, 2017])
        df = EconomicImpactPanelBuilder._rows_to_dataframe(rows)

        for col in ["pib", "n_vinculos", "populacao"]:
            if col in df.columns:
                assert df[col].dtype == np.float64, f"{col} não é float64"


# ---------------------------------------------------------------------------
# _validate
# ---------------------------------------------------------------------------

class TestValidate:
    def test_did_passes_with_all_cols(self):
        from app.services.impacto_economico.panel_builder import (
            EconomicImpactPanelBuilder,
        )
        df = pd.DataFrame(
            {"id_municipio": ["x"], "ano": [2015], "treated": [1], "post": [1], "did": [1]}
        )
        # Não deve lançar exceção
        EconomicImpactPanelBuilder._validate(df, mode="did")

    def test_did_fails_without_treated(self):
        from app.services.impacto_economico.panel_builder import (
            EconomicImpactPanelBuilder,
            PanelValidationError,
        )
        df = pd.DataFrame({"id_municipio": ["x"], "ano": [2015], "post": [1], "did": [1]})
        with pytest.raises(PanelValidationError, match="treated"):
            EconomicImpactPanelBuilder._validate(df, mode="did")

    def test_iv_passes_without_did_cols(self):
        from app.services.impacto_economico.panel_builder import (
            EconomicImpactPanelBuilder,
        )
        df = pd.DataFrame({"id_municipio": ["x"], "ano": [2015], "preco_soja": [350.0]})
        EconomicImpactPanelBuilder._validate(df, mode="iv")

    def test_fails_on_empty_df(self):
        from app.services.impacto_economico.panel_builder import (
            EconomicImpactPanelBuilder,
            PanelValidationError,
        )
        df = pd.DataFrame(columns=["id_municipio", "ano", "treated", "post", "did"])
        # DataFrame com as colunas certas mas vazio
        with pytest.raises(PanelValidationError, match="vazio"):
            EconomicImpactPanelBuilder._validate(df, mode="did")


# ---------------------------------------------------------------------------
# build_did_panel — caminho feliz
# ---------------------------------------------------------------------------

class TestBuildDidPanel:
    @pytest.fixture
    def builder_with_mock(self):
        """Retorna (builder, mock_execute_query)."""
        from app.services.impacto_economico.panel_builder import (
            EconomicImpactPanelBuilder,
        )
        mock_bq = MagicMock()
        rows = _make_rows(ALL_MUNS, ANOS)
        mock_bq.execute_query = AsyncMock(return_value=rows)
        builder = EconomicImpactPanelBuilder(bq_client=mock_bq)
        return builder, mock_bq.execute_query

    @pytest.mark.asyncio
    async def test_returns_dataframe(self, builder_with_mock):
        builder, _ = builder_with_mock
        df = await builder.build_did_panel(
            treated_municipios=TREATED,
            control_municipios=CONTROL,
            treatment_year=TREATMENT_YEAR,
        )
        assert isinstance(df, pd.DataFrame)
        assert not df.empty

    @pytest.mark.asyncio
    async def test_has_did_columns(self, builder_with_mock):
        builder, _ = builder_with_mock
        df = await builder.build_did_panel(
            treated_municipios=TREATED,
            control_municipios=CONTROL,
            treatment_year=TREATMENT_YEAR,
        )
        for col in ["treated", "post", "did"]:
            assert col in df.columns, f"Coluna '{col}' ausente"

    @pytest.mark.asyncio
    async def test_treated_flag_correct(self, builder_with_mock):
        builder, _ = builder_with_mock
        df = await builder.build_did_panel(
            treated_municipios=TREATED,
            control_municipios=CONTROL,
            treatment_year=TREATMENT_YEAR,
        )
        treated_muns = df[df["id_municipio"].isin(TREATED)]
        control_muns = df[df["id_municipio"].isin(CONTROL)]
        assert (treated_muns["treated"] == 1).all()
        assert (control_muns["treated"] == 0).all()

    @pytest.mark.asyncio
    async def test_post_flag_correct(self, builder_with_mock):
        builder, _ = builder_with_mock
        df = await builder.build_did_panel(
            treated_municipios=TREATED,
            control_municipios=CONTROL,
            treatment_year=TREATMENT_YEAR,
        )
        pre = df[df["ano"] < TREATMENT_YEAR]
        post = df[df["ano"] >= TREATMENT_YEAR]
        assert (pre["post"] == 0).all()
        assert (post["post"] == 1).all()

    @pytest.mark.asyncio
    async def test_did_is_treated_times_post(self, builder_with_mock):
        builder, _ = builder_with_mock
        df = await builder.build_did_panel(
            treated_municipios=TREATED,
            control_municipios=CONTROL,
            treatment_year=TREATMENT_YEAR,
        )
        expected_did = df["treated"] * df["post"]
        pd.testing.assert_series_equal(
            df["did"].astype(int),
            expected_did.astype(int),
            check_names=False,
        )

    @pytest.mark.asyncio
    async def test_correct_number_of_rows(self, builder_with_mock):
        builder, _ = builder_with_mock
        df = await builder.build_did_panel(
            treated_municipios=TREATED,
            control_municipios=CONTROL,
            treatment_year=TREATMENT_YEAR,
        )
        expected = len(ALL_MUNS) * len(ANOS)
        assert len(df) == expected

    @pytest.mark.asyncio
    async def test_log_cols_not_negative_inf(self, builder_with_mock):
        builder, _ = builder_with_mock
        df = await builder.build_did_panel(
            treated_municipios=TREATED,
            control_municipios=CONTROL,
            treatment_year=TREATMENT_YEAR,
        )
        log_cols = [c for c in df.columns if c.endswith("_log")]
        for col in log_cols:
            assert not (df[col] == -np.inf).any(), f"{col} contém -inf"


# ---------------------------------------------------------------------------
# Fallback mart-not-found → raw query
# ---------------------------------------------------------------------------

class TestBuildDidPanelFallback:
    @pytest.mark.asyncio
    async def test_fallback_on_mart_not_found(self):
        from app.services.impacto_economico.panel_builder import (
            EconomicImpactPanelBuilder,
        )
        from app.db.bigquery.client import BigQueryError

        rows = _make_rows(ALL_MUNS, ANOS)
        call_count = 0

        async def mock_execute(query, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise BigQueryError("not found: mart_impacto_economico")
            return rows

        mock_bq = MagicMock()
        mock_bq.execute_query = mock_execute
        builder = EconomicImpactPanelBuilder(bq_client=mock_bq)

        df = await builder.build_did_panel(
            treated_municipios=TREATED,
            control_municipios=CONTROL,
            treatment_year=TREATMENT_YEAR,
            use_mart=True,
        )

        # A segunda chamada (fallback) deve ter sido feita
        assert call_count == 2
        assert not df.empty
        assert "did" in df.columns

    @pytest.mark.asyncio
    async def test_raises_on_non_notfound_error(self):
        from app.services.impacto_economico.panel_builder import (
            EconomicImpactPanelBuilder,
        )
        from app.db.bigquery.client import BigQueryError

        mock_bq = MagicMock()
        mock_bq.execute_query = AsyncMock(
            side_effect=BigQueryError("Forbidden: insufficient permissions")
        )
        builder = EconomicImpactPanelBuilder(bq_client=mock_bq)

        with pytest.raises(BigQueryError):
            await builder.build_did_panel(
                treated_municipios=TREATED,
                control_municipios=CONTROL,
                treatment_year=TREATMENT_YEAR,
            )


# ---------------------------------------------------------------------------
# build_iv_panel
# ---------------------------------------------------------------------------

class TestBuildIvPanel:
    @pytest.fixture
    def iv_builder(self):
        from app.services.impacto_economico.panel_builder import (
            EconomicImpactPanelBuilder,
        )
        rows = _make_rows(ALL_MUNS, ANOS, extra_cols={"preco_soja": 350.0, "commodity_index": 0.5})
        mock_bq = MagicMock()
        mock_bq.execute_query = AsyncMock(return_value=rows)
        return EconomicImpactPanelBuilder(bq_client=mock_bq)

    @pytest.mark.asyncio
    async def test_returns_dataframe_with_commodity_col(self, iv_builder):
        df = await iv_builder.build_iv_panel(id_municipios=ALL_MUNS)
        assert isinstance(df, pd.DataFrame)
        assert "preco_soja" in df.columns

    @pytest.mark.asyncio
    async def test_has_id_municipio_and_ano(self, iv_builder):
        df = await iv_builder.build_iv_panel(id_municipios=ALL_MUNS)
        assert "id_municipio" in df.columns
        assert "ano" in df.columns

    @pytest.mark.asyncio
    async def test_raises_if_empty(self):
        from app.services.impacto_economico.panel_builder import (
            EconomicImpactPanelBuilder,
            PanelValidationError,
        )
        mock_bq = MagicMock()
        mock_bq.execute_query = AsyncMock(return_value=[])
        builder = EconomicImpactPanelBuilder(bq_client=mock_bq)

        with pytest.raises(PanelValidationError, match="vazio"):
            await builder.build_iv_panel(id_municipios=ALL_MUNS)


# ---------------------------------------------------------------------------
# build_uf_panel
# ---------------------------------------------------------------------------

class TestBuildUfPanel:
    @pytest.fixture
    def uf_builder(self):
        from app.services.impacto_economico.panel_builder import (
            EconomicImpactPanelBuilder,
        )
        ufs = ["MA", "PA", "RJ"]
        rows = [
            {
                "uf": uf,
                "ano": ano,
                "pib": float(np.random.randint(1e9, 1e11)),
                "n_vinculos": float(np.random.randint(1000, 50000)),
                "toneladas_antaq": float(np.random.randint(1e6, 1e8)),
                "populacao": float(np.random.randint(1e6, 1e7)),
                "pib_log": np.log(1e9),
                "n_vinculos_log": np.log(5000),
                "toneladas_antaq_log": np.log(1e7),
                "pib_per_capita": float(np.random.uniform(5000, 30000)),
                "ipca_media": 103.5,
            }
            for uf in ufs
            for ano in ANOS
        ]
        mock_bq = MagicMock()
        mock_bq.execute_query = AsyncMock(return_value=rows)
        return EconomicImpactPanelBuilder(bq_client=mock_bq)

    @pytest.mark.asyncio
    async def test_has_uf_column(self, uf_builder):
        df = await uf_builder.build_uf_panel(ufs=["MA", "PA", "RJ"])
        assert "uf" in df.columns

    @pytest.mark.asyncio
    async def test_correct_uf_values(self, uf_builder):
        df = await uf_builder.build_uf_panel(ufs=["MA", "PA", "RJ"])
        assert set(df["uf"].unique()) == {"MA", "PA", "RJ"}

    @pytest.mark.asyncio
    async def test_raises_if_empty(self):
        from app.services.impacto_economico.panel_builder import (
            EconomicImpactPanelBuilder,
            PanelValidationError,
        )
        mock_bq = MagicMock()
        mock_bq.execute_query = AsyncMock(return_value=[])
        builder = EconomicImpactPanelBuilder(bq_client=mock_bq)

        with pytest.raises(PanelValidationError):
            await builder.build_uf_panel(ufs=["MA"])


# ---------------------------------------------------------------------------
# Script de ingestão — parsing (sem BigQuery)
# ---------------------------------------------------------------------------

class TestIngestScript:
    """Testa o parser do Pink Sheet com Excel sintético."""

    def _make_fake_pinksheet(self) -> bytes:
        """Gera um Excel mínimo no formato esperado pelo parser."""
        # Pink Sheet tem 4 linhas de header antes dos dados
        header_rows = [
            ["", "", "", "", ""],
            ["", "", "", "", ""],
            ["", "", "", "", ""],
            ["", "", "", "", ""],
            [
                "Date",
                "Soybeans",
                "Maize",
                "Wheat, US SRW",
                "Iron ore, cfr spot",
                "Crude oil, Brent",
            ],
        ]
        data_rows = []
        for year in range(2010, 2023):
            for month in range(1, 13):
                data_rows.append(
                    [
                        f"{year}M{month:02d}",
                        float(300 + year - 2010 + month),
                        float(150 + year - 2010 + month),
                        float(200 + year - 2010 + month),
                        float(80 + year - 2010 + month),
                        float(70 + year - 2010 + month),
                    ]
                )

        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            all_rows = header_rows + data_rows
            df = pd.DataFrame(all_rows)
            df.to_excel(writer, sheet_name="Monthly Prices", index=False, header=False)
        buf.seek(0)
        return buf.read()

    def test_parse_returns_annual_dataframe(self):
        try:
            import openpyxl  # noqa: F401
        except ImportError:
            pytest.skip("openpyxl não instalado")

        from scripts.ingest_worldbank_commodities import _parse_pinksheet

        content = self._make_fake_pinksheet()
        df = _parse_pinksheet(content, ano_inicio=2010, ano_fim=2022)

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert "ano" in df.columns
        # Anual: um por ano
        assert df["ano"].nunique() == 13  # 2010–2022

    def test_parse_has_commodity_index(self):
        try:
            import openpyxl  # noqa: F401
        except ImportError:
            pytest.skip("openpyxl não instalado")

        from scripts.ingest_worldbank_commodities import _parse_pinksheet

        content = self._make_fake_pinksheet()
        df = _parse_pinksheet(content, ano_inicio=2010, ano_fim=2022)

        assert "commodity_index" in df.columns
        # O índice deve ser um número real (não NaN puro, pode haver alguns NaN)
        assert df["commodity_index"].notna().any()

    def test_parse_filters_by_year_range(self):
        try:
            import openpyxl  # noqa: F401
        except ImportError:
            pytest.skip("openpyxl não instalado")

        from scripts.ingest_worldbank_commodities import _parse_pinksheet

        content = self._make_fake_pinksheet()
        df = _parse_pinksheet(content, ano_inicio=2015, ano_fim=2018)

        assert df["ano"].min() >= 2015
        assert df["ano"].max() <= 2018

    def test_parse_no_negative_prices(self):
        try:
            import openpyxl  # noqa: F401
        except ImportError:
            pytest.skip("openpyxl não instalado")

        from scripts.ingest_worldbank_commodities import _parse_pinksheet

        content = self._make_fake_pinksheet()
        df = _parse_pinksheet(content, ano_inicio=2010, ano_fim=2022)

        price_cols = [c for c in df.columns if c.startswith("preco_")]
        for col in price_cols:
            valid = df[col].dropna()
            assert (valid >= 0).all(), f"Preço negativo em {col}"
