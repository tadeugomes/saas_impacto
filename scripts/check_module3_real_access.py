"""Validação de acesso real ao BigQuery para o Módulo 3 (RAIS + ANTAQ)."""

import argparse
import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, List

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.db.bigquery.client import get_bigquery_client
from app.db.bigquery.queries.module3_human_resources import (
    query_empregos_diretos_portuarios,
    query_total_municipal_employment,
    query_produtividade_ton_empregado,
)


QueryBuilder = Callable[[str, int], str]


@dataclass
class CheckResult:
    """Resultado de uma checagem."""

    label: str
    rows: int
    columns: List[str]
    bytes_billed: int
    sample: Any
    query_error: str | None = None


async def run_check(
    label: str,
    build_query: QueryBuilder,
    id_municipio: str,
    ano: int,
    limit: int,
    client,
) -> CheckResult:
    """
    Executa uma consulta com limite e retorna contagem + schema da resposta.
    """
    query = build_query(id_municipio=id_municipio, ano=ano)
    if "LIMIT" not in query.upper():
        query = f"SELECT * FROM ({query}) LIMIT {limit}"

    try:
        stats = await client.get_dry_run_results(query)
        rows = await client.execute_query(query)
        columns = list(rows[0].keys()) if rows else []
        sample = rows[0] if rows else None
        return CheckResult(
            label=label,
            rows=len(rows),
            columns=columns,
            bytes_billed=stats.get("total_bytes_billed", 0) or 0,
            sample=sample,
        )
    except Exception as exc:  # pragma: no cover - operação externa
        return CheckResult(
            label=label,
            rows=0,
            columns=[],
            bytes_billed=0,
            sample=None,
            query_error=str(exc),
        )


def _build_antaq_tonelagem_query(id_municipio: str, ano: int) -> str:
    return f"""
    SELECT
      CAST(municipio AS STRING) AS id_municipio,
      CAST(SAFE_CAST(ano AS INT64) AS INT64) AS ano,
      SUM(vlpesocargabruta_oficial) AS tonelagem_oficial
    FROM `antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial`
    WHERE SAFE_CAST(ano AS INT64) = {ano}
      AND CAST(municipio AS STRING) = '{id_municipio}'
      AND vlpesocargabruta_oficial IS NOT NULL
    GROUP BY id_municipio, ano
    """


def _print_result(result: CheckResult) -> None:
    print("=" * 70)
    print(result.label)
    if result.query_error:
        print(f"ERRO: {result.query_error}")
        return

    print(f"rows_limitadas: {result.rows}")
    print(f"columns: {result.columns}")
    print(f"bytes_billed_est: {result.bytes_billed}")
    print(f"sample: {result.sample}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Checa acesso real do Módulo 3 no BigQuery")
    parser.add_argument("--municipio", default="3548500", help="id_municipio IBGE (7 dígitos)")
    parser.add_argument("--ano", type=int, default=2023, help="ano de referência")
    parser.add_argument("--limit", type=int, default=3, help="limite por consulta")
    args = parser.parse_args()

    client = get_bigquery_client()

    checks = [
        (
            "RAIS - Empregos diretos portuários",
            lambda id_municipio, ano: query_empregos_diretos_portuarios(
                id_municipio=id_municipio,
                ano=ano,
            ),
        ),
        (
            "RAIS - Empregos totais do município",
            lambda id_municipio, ano: query_total_municipal_employment(
                id_municipio=id_municipio,
                ano=ano,
            ),
        ),
        (
            "RAIS - Produtividade (ton/empregado)",
            lambda id_municipio, ano: query_produtividade_ton_empregado(
                id_municipio=id_municipio,
                ano=ano,
            ),
        ),
        (
            "ANTAQ - Tonelagem mensal agregada",
            _build_antaq_tonelagem_query,
        ),
    ]

    results = [
        await run_check(label, build_query, args.municipio, args.ano, args.limit, client)
        for label, build_query in checks
    ]

    print("\nValidação real de Módulo 3")
    print(f"Município: {args.municipio} | Ano: {args.ano}\n")
    for item in results:
        _print_result(item)

    failed = [r for r in results if r.query_error]
    if failed:
        raise SystemExit(2)
    return None


if __name__ == "__main__":
    asyncio.run(main())
