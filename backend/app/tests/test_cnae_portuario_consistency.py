"""Validação da cadeia de códigos CNAE para indicadores portuários."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from app.db.bigquery.queries.module3_human_resources import CNAES_PORTUARIOS as MODULE3_CNAES
from app.db.bigquery.queries.module5_economic_impact import CNAES_PORTUARIOS as MODULE5_CNAES
from app.db.bigquery.sector_codes import CNAES_PORTUARIOS as CANONICAL_CNAES
from app.db.bigquery.marts.module5 import CNAES_PORTUARIOS as MART_CNAES


def _read_cnaes_from_technical_documentation() -> list[str]:
    repo_root = Path(__file__).resolve()
    docs_path = None
    for parent in repo_root.parents:
        candidate = parent / "planejamento/docs/INDICADORES_ESPECIFICACAO_TECNICA.md"
        if candidate.exists():
            docs_path = candidate
            break
    if docs_path is None:
        raise AssertionError("Não foi possível localizar o documento técnico no workspace.")

    raw = docs_path.read_text(encoding="utf-8")

    match = re.search(r"CNAES_PORTUARIOS\s*=\s*\[(.*?)\]", raw, re.S)
    if not match:
        raise AssertionError("Seção CNAES_PORTUARIOS não encontrada na especificação técnica.")

    cnaes: list[str] = []
    block = match.group(1)
    for line in block.splitlines():
        line = line.split("#", 1)[0].strip().rstrip(",")
        if not line:
            continue
        cnaes.append(ast.literal_eval(line))

    if not cnaes:
        raise AssertionError("Não foi possível extrair lista de CNAEs do documento técnico.")

    return cnaes


def test_cnae_portuarios_doc_list_is_single_source_and_matches_docs():
    doc_cnaes = _read_cnaes_from_technical_documentation()

    assert MODULE3_CNAES == CANONICAL_CNAES == MART_CNAES == MODULE5_CNAES
    assert doc_cnaes == CANONICAL_CNAES
