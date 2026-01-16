
import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.config import get_settings

async def list_ports():
    settings = get_settings()
    engine = create_async_engine(settings.postgres_url.replace('+asyncpg', '')) # Hack for simple query, actually nvm use correct driver
    engine = create_async_engine(settings.postgres_url)
    
    # We need to query BigQuery, not Postgres for indicators!
    # The indicators are in BigQuery.
    
    # But wait, generic_indicator_service uses BigQueryClient.
    print('Checking Backend config for BigQuery...')
    if not settings.google_application_credentials:
        print('No GCP Creds? Local mock?')

if __name__ == '__main__':
    asyncio.run(list_ports())

