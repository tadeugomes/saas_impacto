
import asyncio
import sys
import os
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.config import get_settings
from app.db.models.user import User
from app.core.security import get_password_hash

async def reset_password():
    settings = get_settings()
    engine = create_async_engine(settings.postgres_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Find User
        result = await session.execute(select(User).where(User.email == "admin@example.com"))
        user = result.scalar_one_or_none()
        
        if user:
            new_hash = get_password_hash("admin123")
            user.hashed_password = new_hash
            session.add(user)
            await session.commit()
            print("Password for admin@example.com reset to 'admin123'.")
        else:
            print("User admin@example.com NOT found.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(reset_password())
