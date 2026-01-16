
import asyncio
import sys
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.config import get_settings
from app.db.models.user import User
from app.db.models.tenant import Tenant

async def check_user():
    settings = get_settings()
    engine = create_async_engine(settings.postgres_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check Tenant
        result = await session.execute(select(Tenant))
        tenants = result.scalars().all()
        print(f"Tenants found: {[t.slug for t in tenants]}")

        # Check User
        result = await session.execute(select(User).where(User.email == "admin@example.com"))
        user = result.scalar_one_or_none()
        
        if user:
            print(f"User found: {user.email} (ID: {user.id})")
            print(f"Tenant ID: {user.tenant_id}")
            print(f"Active: {user.ativo}")
        else:
            print("User admin@example.com NOT found.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_user())
