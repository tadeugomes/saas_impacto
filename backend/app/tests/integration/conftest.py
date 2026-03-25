"""
Configuração para testes de integração com BigQuery real.

Estes testes requerem:
- GOOGLE_APPLICATION_CREDENTIALS apontando para service account válida
- GCP_PROJECT_ID configurado
- Acesso às tabelas basedosdados.br_me_rais e basedosdados.br_ibge_pib

Execução:
    cd backend
    python3 -m pytest app/tests/integration/ -v -m integration

Para pular em CI (sem credenciais):
    python3 -m pytest app/tests/ -m "not integration"
"""
from __future__ import annotations

import os
import pytest

from app.db.bigquery.client import BigQueryClient


def _has_bq_credentials() -> bool:
    """Verifica se há credenciais BigQuery disponíveis."""
    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    return bool(cred_path) and os.path.isfile(cred_path)


# Pula todos os testes do diretório se não houver credenciais
pytestmark = pytest.mark.integration

# Skip automático quando não há credenciais BQ
if not _has_bq_credentials():
    pytestmark = [
        pytest.mark.integration,
        pytest.mark.skip(reason="BigQuery credentials not available"),
    ]


@pytest.fixture(scope="module")
def bq_client():
    """BigQuery client real (não mockado)."""
    return BigQueryClient()
