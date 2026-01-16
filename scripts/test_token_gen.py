
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.security import create_access_token
import uuid

def generate_token():
    tenant_id = "550e8400-e29b-41d4-a716-446655440000"
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    
    data = {
        "sub": user_id,
        "tenant_id": tenant_id
    }
    
    token = create_access_token(data)
    print(f"Token: {token}")

if __name__ == "__main__":
    generate_token()
