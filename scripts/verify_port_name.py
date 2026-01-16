
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_query_full_name():
    # Login
    login_resp = requests.post(f"{BASE_URL}/auth/login", json={"email": "admin@example.com", "password": "admin123"})
    token = login_resp.json()["access_token"]

    # Query with "Porto de Santos"
    print("Querying with 'Porto de Santos'...")
    resp = requests.post(
        f"{BASE_URL}/indicators/query",
        json={"codigo_indicador": "IND-1.01", "id_instalacao": "Porto de Santos", "ano": 2023},
        headers={"Authorization": f"Bearer {token}"}
    )
    data = resp.json()
    print(f"Status: {resp.status_code}")
    print(f"Data count: {len(data.get('data', []))}")
    if len(data.get('data', [])) > 0:
        print("FOUND DATA with 'Porto de Santos'")
    else:
        print("NO DATA with 'Porto de Santos'")

if __name__ == "__main__":
    test_query_full_name()
