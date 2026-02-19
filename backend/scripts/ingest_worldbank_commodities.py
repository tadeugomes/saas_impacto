#!/usr/bin/env python3
"""Ingestão do World Bank Pink Sheet para BigQuery.

Baixa o arquivo "Pink Sheet" de preços de commodities do World Bank
(``PINKSHEET_URL``), extrai as séries mensais de interesse,
agrega para periodicidade anual e carrega na tabela BigQuery
``marts_impacto.external.worldbank_commodities``.

A tabela resultante é usada como instrumento exógeno (IV) na análise
causal de impacto econômico dos portos:
  - ``preco_soja``   (SOYBEAN)  — relevante para municípios com exportação agrícola
  - ``preco_milho``  (MAIZE)    — idem
  - ``preco_trigo``  (WHEAT)    — grãos em geral
  - ``preco_aco``    (IRON_ORE) — minério / cargas a granel
  - ``preco_oleo``   (CRUDE_OIL, Brent) — petróleo e derivados
  - ``commodity_index`` — índice agregado (média normalizada z-score das 5 séries)

Uso:
    python scripts/ingest_worldbank_commodities.py \
        --project my-gcp-project \
        --dataset marts_impacto \
        --table worldbank_commodities \
        [--credentials /path/to/sa.json] \
        [--ano-inicio 2000] \
        [--ano-fim 2024] \
        [--dry-run]

Dependências (já listadas em requirements.txt):
    pandas, openpyxl, google-cloud-bigquery, httpx
"""
from __future__ import annotations

import argparse
import io
import logging
import sys
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("ingest_worldbank_commodities")


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

PINKSHEET_URL = (
    "https://thedocs.worldbank.org/en/doc/"
    "5d903e848db1d1b83e0ec8f744e55570-0350012021/related/"
    "CMO-Historical-Data-Monthly.xlsx"
)

# Mapeamento: nome da coluna no Pink Sheet → nome amigável no BQ
COMMODITY_COLUMNS: dict[str, str] = {
    "Soybeans": "preco_soja",
    "Maize": "preco_milho",
    "Wheat, US SRW": "preco_trigo",
    "Iron ore, cfr spot": "preco_minerio_ferro",
    "Crude oil, Brent": "preco_oleo_brent",
}

BQ_SCHEMA_FIELDS = [
    ("ano", "INTEGER"),
    ("preco_soja", "FLOAT"),
    ("preco_milho", "FLOAT"),
    ("preco_trigo", "FLOAT"),
    ("preco_minerio_ferro", "FLOAT"),
    ("preco_oleo_brent", "FLOAT"),
    ("commodity_index", "FLOAT"),
    ("_ingestao_ts", "TIMESTAMP"),
]

# Aba do Excel que contém séries mensais em USD
EXCEL_SHEET = "Monthly Prices"
# Linha de cabeçalho real (0-indexed), o Pink Sheet tem algumas linhas de título antes
HEADER_ROW = 4


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def _download_pinksheet(url: str = PINKSHEET_URL) -> bytes:
    """Baixa o Pink Sheet como bytes."""
    try:
        import httpx
    except ImportError as exc:
        raise SystemExit("httpx não instalado. Execute: pip install httpx") from exc

    logger.info("Baixando Pink Sheet: %s", url)
    with httpx.Client(timeout=120, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()

    logger.info("Download concluído: %.1f KB", len(resp.content) / 1024)
    return resp.content


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _parse_pinksheet(content: bytes, ano_inicio: int, ano_fim: int) -> "pd.DataFrame":
    """Parseia o Excel e retorna DataFrame anual com as colunas de interest."""
    try:
        import pandas as pd
    except ImportError as exc:
        raise SystemExit("pandas não instalado.") from exc

    logger.info("Parseando Excel (aba '%s', header row=%d) ...", EXCEL_SHEET, HEADER_ROW)

    df_raw = pd.read_excel(
        io.BytesIO(content),
        sheet_name=EXCEL_SHEET,
        header=HEADER_ROW,
        engine="openpyxl",
    )

    # Primeira coluna contém datas no formato "YYYYMNN" ou similar; normaliza
    date_col = df_raw.columns[0]
    df_raw = df_raw.rename(columns={date_col: "periodo"})
    df_raw["periodo"] = df_raw["periodo"].astype(str).str.strip()

    # Remove linhas sem data válida (notas de rodapé, cabeçalhos extras)
    df_raw = df_raw[df_raw["periodo"].str.match(r"^\d{4}M\d{2}$", na=False)].copy()

    if df_raw.empty:
        raise ValueError(
            "Nenhuma linha com formato 'YYYYMNN' encontrada. "
            "Verifique se o formato do Pink Sheet mudou."
        )

    # Extrai ano e mês
    df_raw["ano"] = df_raw["periodo"].str[:4].astype(int)
    df_raw["mes"] = df_raw["periodo"].str[5:].astype(int)

    # Seleciona apenas colunas de interesse
    available_cols = df_raw.columns.tolist()
    rename_map: dict[str, str] = {}
    for src, dst in COMMODITY_COLUMNS.items():
        # Busca correspondência parcial (o Pink Sheet usa nomes ligeiramente diferentes)
        matched = [c for c in available_cols if str(c).strip().lower().startswith(src.lower()[:8])]
        if matched:
            rename_map[matched[0]] = dst
        else:
            logger.warning("Coluna '%s' não encontrada no Pink Sheet.", src)

    keep_cols = ["ano", "mes"] + list(rename_map.keys())
    df_sel = df_raw[[c for c in keep_cols if c in df_raw.columns]].rename(columns=rename_map)

    # Converte tudo para numérico (células com "..." ou "-" viram NaN)
    commodity_final = [c for c in COMMODITY_COLUMNS.values() if c in df_sel.columns]
    for col in commodity_final:
        df_sel[col] = pd.to_numeric(df_sel[col], errors="coerce")

    # Filtra por ano
    df_sel = df_sel[(df_sel["ano"] >= ano_inicio) & (df_sel["ano"] <= ano_fim)]

    if df_sel.empty:
        raise ValueError(
            f"Nenhum dado encontrado para o período {ano_inicio}–{ano_fim}."
        )

    # Agrega para anual (média dos meses)
    df_anual = (
        df_sel.drop(columns=["mes"])
        .groupby("ano")
        .mean()
        .reset_index()
    )

    # Calcula índice composto (z-score médio das séries disponíveis)
    valid_series = [c for c in commodity_final if c in df_anual.columns]
    if valid_series:
        from scipy.stats import zscore as _zscore  # noqa: PLC0415

        z_matrix = df_anual[valid_series].apply(
            lambda col: _zscore(col.dropna(), ddof=1) if col.dropna().shape[0] > 1 else col * 0,
        )
        df_anual["commodity_index"] = z_matrix.mean(axis=1)
    else:
        df_anual["commodity_index"] = float("nan")

    df_anual["_ingestao_ts"] = datetime.utcnow().isoformat()

    logger.info(
        "Painel anual de commodities: %d linhas, colunas=%s",
        len(df_anual),
        df_anual.columns.tolist(),
    )
    return df_anual


# ---------------------------------------------------------------------------
# BigQuery Upload
# ---------------------------------------------------------------------------

def _upload_to_bigquery(
    df: "pd.DataFrame",
    project: str,
    dataset: str,
    table: str,
    credentials_path: Optional[str],
    dry_run: bool,
) -> None:
    """Faz upload do DataFrame para o BigQuery (replace total)."""
    try:
        from google.cloud import bigquery
        from google.oauth2 import service_account
        import json
    except ImportError as exc:
        raise SystemExit("google-cloud-bigquery não instalado.") from exc

    fqtn = f"{project}.{dataset}.{table}"

    if dry_run:
        logger.info("[DRY-RUN] Não fará upload. DataFrame a carregar:")
        logger.info(df.to_string(max_rows=10))
        logger.info("[DRY-RUN] Destino seria: %s", fqtn)
        return

    # Credenciais
    credentials = None
    if credentials_path:
        with open(credentials_path, "r") as f:
            cred_info = json.load(f)
        credentials = service_account.Credentials.from_service_account_info(
            cred_info,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )

    client = bigquery.Client(project=project, credentials=credentials)

    # Schema explícito
    schema = [
        bigquery.SchemaField(name, bq_type)
        for name, bq_type in BQ_SCHEMA_FIELDS
        if name in df.columns
    ]

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    logger.info("Fazendo upload de %d linhas para %s ...", len(df), fqtn)

    # Garante que _ingestao_ts seja datetime
    if "_ingestao_ts" in df.columns:
        import pandas as pd
        df["_ingestao_ts"] = pd.to_datetime(df["_ingestao_ts"])

    job = client.load_table_from_dataframe(df, fqtn, job_config=job_config)
    job.result()  # Aguarda conclusão

    table_ref = client.get_table(fqtn)
    logger.info(
        "Upload concluído: %d linhas em %s",
        table_ref.num_rows,
        fqtn,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingere Pink Sheet do World Bank no BigQuery."
    )
    parser.add_argument(
        "--project",
        required=True,
        help="ID do projeto GCP (ex.: my-gcp-project)",
    )
    parser.add_argument(
        "--dataset",
        default="marts_impacto",
        help="Dataset BigQuery de destino (default: marts_impacto)",
    )
    parser.add_argument(
        "--table",
        default="worldbank_commodities",
        help="Tabela de destino dentro do dataset (default: worldbank_commodities)",
    )
    parser.add_argument(
        "--credentials",
        default=None,
        metavar="PATH",
        help="Caminho para service account JSON (usa ADC se não fornecido)",
    )
    parser.add_argument(
        "--ano-inicio",
        type=int,
        default=2000,
        help="Ano de início da série (default: 2000)",
    )
    parser.add_argument(
        "--ano-fim",
        type=int,
        default=datetime.utcnow().year,
        help="Ano de fim da série (default: ano corrente)",
    )
    parser.add_argument(
        "--url",
        default=PINKSHEET_URL,
        help="URL do arquivo Excel do Pink Sheet",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas parseia e exibe os dados; não faz upload.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    try:
        content = _download_pinksheet(args.url)
        df = _parse_pinksheet(content, args.ano_inicio, args.ano_fim)
        _upload_to_bigquery(
            df=df,
            project=args.project,
            dataset=args.dataset,
            table=args.table,
            credentials_path=args.credentials,
            dry_run=args.dry_run,
        )
    except Exception:
        logger.exception("Falha na ingestão do Pink Sheet.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
