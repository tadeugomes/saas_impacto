#!/usr/bin/env python3
"""
Runbook de validação de acesso real às fontes de dados do Módulo 3
(Impacto em Emprego: RAIS/ANTAQ via BigQuery).

Uso:
    cd backend && python scripts/check_module3_real_access.py [--municipio ID] [--ano ANO]

Retorna código de saída 0 se todas as verificações passarem, 1 se alguma falhar.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime


async def _check_bigquery_connection() -> tuple[bool, str]:
    """Verifica conexão básica com BigQuery."""
    try:
        from app.db.bigquery.client import get_bigquery_client
        client = get_bigquery_client()
        # Query mínima para validar credenciais
        result = client.query("SELECT 1 AS ok")
        rows = list(result)
        if rows and rows[0]["ok"] == 1:
            return True, "BigQuery: conexão OK"
        return False, "BigQuery: query retornou resultado inesperado"
    except ImportError as e:
        return False, f"BigQuery: dependência ausente — {e}"
    except Exception as e:
        return False, f"BigQuery: erro de conexão — {e}"


async def _check_rais_data(id_municipio: str, ano: int) -> tuple[bool, str]:
    """Verifica se dados RAIS estão disponíveis para o município/ano."""
    try:
        from app.db.bigquery.client import get_bigquery_client
        from app.db.bigquery.queries.module3_human_resources import (
            query_empregos_diretos_portuarios,
        )
        client = get_bigquery_client()
        query = query_empregos_diretos_portuarios(
            id_municipio=id_municipio,
            ano_inicio=ano,
            ano_fim=ano,
        )
        rows = list(client.query(query))
        if rows:
            return True, f"RAIS: {len(rows)} registro(s) encontrado(s) para município {id_municipio}, ano {ano}"
        return False, f"RAIS: nenhum dado para município {id_municipio}, ano {ano} (tabela pode estar vazia)"
    except Exception as e:
        return False, f"RAIS: erro na consulta — {e}"


async def _check_antaq_data(id_municipio: str, ano: int) -> tuple[bool, str]:
    """Verifica se dados ANTAQ estão disponíveis para o município/ano."""
    try:
        from app.db.bigquery.client import get_bigquery_client
        from app.db.bigquery.queries.module3_human_resources import (
            query_produtividade_ton_empregado,
        )
        client = get_bigquery_client()
        query = query_produtividade_ton_empregado(
            id_municipio=id_municipio,
            ano_inicio=ano,
            ano_fim=ano,
        )
        rows = list(client.query(query))
        if rows:
            return True, f"ANTAQ: {len(rows)} registro(s) encontrado(s) para município {id_municipio}, ano {ano}"
        return False, f"ANTAQ: nenhum dado para município {id_municipio}, ano {ano}"
    except Exception as e:
        return False, f"ANTAQ: erro na consulta — {e}"


async def _check_employment_service(id_municipio: str, ano: int) -> tuple[bool, str]:
    """Valida o fluxo completo do EmploymentMultiplierService."""
    try:
        from app.db.bigquery.client import get_bigquery_client
        from app.services.employment_multiplier import EmploymentMultiplierService

        client = get_bigquery_client()
        service = EmploymentMultiplierService(bigquery_client=client)
        result = await service.compute_impact(
            id_municipio=id_municipio,
            ano=ano,
        )
        direto = result.empregos_diretos if result else None
        if direto is not None:
            return True, f"EmploymentMultiplierService: OK — empregos_diretos={direto}"
        return False, "EmploymentMultiplierService: resultado retornou sem empregos_diretos"
    except Exception as e:
        return False, f"EmploymentMultiplierService: erro — {e}"


async def _check_national_multipliers() -> tuple[bool, str]:
    """Verifica que os multiplicadores nacionais I-O estão carregados."""
    try:
        from app.services.io_analysis.national_multipliers import (
            TRANSPORT_EMPLOYMENT,
            TRANSPORT_PRODUCTION,
            TRANSPORT_INCOME,
        )
        all_ok = (
            TRANSPORT_EMPLOYMENT is not None and TRANSPORT_EMPLOYMENT > 0
            and TRANSPORT_PRODUCTION is not None and TRANSPORT_PRODUCTION > 0
            and TRANSPORT_INCOME is not None and TRANSPORT_INCOME > 0
        )
        if all_ok:
            return True, (
                f"Multiplicadores I-O nacionais: OK — "
                f"emprego={TRANSPORT_EMPLOYMENT:.3f}, "
                f"produção={TRANSPORT_PRODUCTION:.3f}, "
                f"renda={TRANSPORT_INCOME:.3f}"
            )
        return False, "Multiplicadores I-O nacionais: valores zero ou None"
    except Exception as e:
        return False, f"Multiplicadores I-O: erro — {e}"


async def main(id_municipio: str, ano: int) -> int:
    print(f"\n{'='*60}")
    print(f"  Validação Módulo 3 — RAIS/ANTAQ")
    print(f"  Executado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Município: {id_municipio} | Ano: {ano}")
    print(f"{'='*60}\n")

    checks = [
        _check_bigquery_connection(),
        _check_national_multipliers(),
        _check_rais_data(id_municipio, ano),
        _check_antaq_data(id_municipio, ano),
        _check_employment_service(id_municipio, ano),
    ]

    results = await asyncio.gather(*checks)
    all_ok = True

    for ok, msg in results:
        icon = "✅" if ok else "❌"
        print(f"  {icon}  {msg}")
        if not ok:
            all_ok = False

    print(f"\n{'='*60}")
    if all_ok:
        print("  RESULTADO: todas as verificações passaram.\n")
        return 0
    else:
        print("  RESULTADO: uma ou mais verificações falharam. Verifique os erros acima.\n")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Valida acesso às fontes de dados do Módulo 3 (RAIS/ANTAQ)."
    )
    parser.add_argument(
        "--municipio",
        default="3304557",  # Rio de Janeiro como padrão
        help="ID do município IBGE (padrão: 3304557 = Rio de Janeiro)",
    )
    parser.add_argument(
        "--ano",
        type=int,
        default=2022,
        help="Ano de referência (padrão: 2022)",
    )
    args = parser.parse_args()

    exit_code = asyncio.run(main(id_municipio=args.municipio, ano=args.ano))
    sys.exit(exit_code)
