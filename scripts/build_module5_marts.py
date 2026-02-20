"""Materializa os marts do Módulo 5 no BigQuery.

Este script gera:
- mart_impacto_economico
- dim_municipio_antaq
- relatório de cobertura da crosswalk

Uso:
    python scripts/build_module5_marts.py --project seuprojeto --versao-pipeline v1.0.0
"""

import argparse
import asyncio
from dataclasses import dataclass

from app.db.bigquery.client import get_bigquery_client
from app.db.bigquery.marts.module5 import (
    build_crosswalk_coverage_query,
    build_dim_municipio_antaq_sql,
    build_impacto_economico_mart_sql,
    build_indicator_metadata_sql,
)


@dataclass(frozen=True)
class PipelineResult:
    """Resultado de uma etapa da orquestração."""
    step: str
    ok: bool
    message: str


async def _execute(client, query: str, step: str) -> PipelineResult:
    try:
        loop = asyncio.get_event_loop()
        query_job = await loop.run_in_executor(None, lambda: client.client.query(query))
        await loop.run_in_executor(None, query_job.result)
        return PipelineResult(step=step, ok=True, message="executado")
    except Exception as exc:  # pragma: no cover - erro operacional externo
        return PipelineResult(step=step, ok=False, message=str(exc))


async def run_pipeline(versao_pipeline: str, dry_run: bool = False) -> list[PipelineResult]:
    """
    Executa ou imprime as queries de criação do mart e da crosswalk.

    Args:
        versao_pipeline: tag usada para controle de versionamento no mart
        dry_run: se True imprime as queries sem executar
    """
    client = get_bigquery_client()

    crosswalk_sql = build_dim_municipio_antaq_sql()
    mart_sql = build_impacto_economico_mart_sql(versao_pipeline=versao_pipeline)
    coverage_sql = build_crosswalk_coverage_query()

    if dry_run:
        print("-- crosswalk")
        print(crosswalk_sql)
        print("-- mart impacto economico")
        print(mart_sql)
        print("-- metadata de cobertura")
        print(coverage_sql)
        return [
            PipelineResult(step="crosswalk", ok=True, message="dry_run"),
            PipelineResult(step="mart", ok=True, message="dry_run"),
            PipelineResult(step="coverage", ok=True, message="dry_run"),
        ]

    steps = [
        ("crosswalk", crosswalk_sql),
        ("mart", mart_sql),
        ("metadata", build_indicator_metadata_sql()),
        ("coverage", coverage_sql),
    ]

    results: list[PipelineResult] = []
    for step_name, sql in steps:
        result = await _execute(client, sql, step_name)
        results.append(result)
        if not result.ok:
            break

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Materializa o mart do Módulo 5")
    parser.add_argument("--versao-pipeline", default="v1.0.0", help="Tag da versão do pipeline")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas imprime SQL sem executar",
    )
    args = parser.parse_args()

    results = asyncio.run(run_pipeline(args.versao_pipeline, dry_run=args.dry_run))

    for item in results:
        print(f"[{item.step}] {item.ok} - {item.message}")

    if not all(item.ok for item in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
