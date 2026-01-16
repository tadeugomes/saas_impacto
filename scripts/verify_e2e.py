
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_login_and_query():
    # 1. Login
    print("Attempting login...")
    try:
        login_resp = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "admin@example.com",
            "password": "admin123"
        })
        login_resp.raise_for_status()
        token_data = login_resp.json()
        access_token = token_data["access_token"]
        print("Login successful! Token obtained.")
    except Exception as e:
        print(f"Login failed: {e}")
        try:
            print(f"Response: {login_resp.text}")
        except:
            pass
        sys.exit(1)

    # 2. Query Indicator
    print("Attempting indicator query with port filter...")
    try:
        query_resp = requests.post(
            f"{BASE_URL}/indicators/query",
            json={
                "codigo_indicador": "IND-1.01",
                "id_instalacao": "SANTOS",
                "ano": 2023
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )
        query_resp.raise_for_status()
        data = query_resp.json()
        print(f"Query successful! Response status: {query_resp.status_code}")
        print(f"Data received: {json.dumps(data, indent=2)}")
        
        if data.get("data") == []:
            print("WARNING: Data array is empty (expected if no data for Santos/2023).")
        
    except Exception as e:
        print(f"Query failed: {e}")
        try:
            print(f"Response: {query_resp.text}")
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    test_login_and_query()
