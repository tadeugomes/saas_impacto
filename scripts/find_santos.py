
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def find_santos():
    # Login
    login_resp = requests.post(f"{BASE_URL}/auth/login", json={"email": "admin@example.com", "password": "admin123"})
    token = login_resp.json()["access_token"]

    # Query ALL for 2023
    print("Finding all ports containing 'Santos'...")
    resp = requests.post(
        f"{BASE_URL}/indicators/query",
        json={"codigo_indicador": "IND-1.01", "ano": 2023},
        headers={"Authorization": f"Bearer {token}"}
    )
    data = resp.json()
    
    santos_ports = set()
    for row in data.get("data", []):
        name = row.get("id_instalacao", "")
        if "santos" in name.lower():
            santos_ports.add(name)
            
    print(f"Ports containing 'Santos': {list(santos_ports)}")
    
    # Also show first 20 ports alphabetically
    all_ports = set()
    for row in data.get("data", []):
        all_ports.add(row.get("id_instalacao", ""))
    
    print(f"\nFirst 20 ports alphabetically:")
    for p in sorted(list(all_ports))[:20]:
        print(f"  - {p}")

if __name__ == "__main__":
    find_santos()
