"""
BigQuery Database Module.

Este módulo fornece acesso ao BigQuery Data Warehouse.
"""

from app.db.bigquery.client import (
    BigQueryClient,
    BigQueryError,
    get_bigquery_client,
    close_bigquery_client,
)

__all__ = [
    "BigQueryClient",
    "BigQueryError",
    "get_bigquery_client",
    "close_bigquery_client",
]
