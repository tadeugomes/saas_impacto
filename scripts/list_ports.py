
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def list_ports():
    # Login
    login_resp = requests.post(f"{BASE_URL}/auth/login", json={"email": "admin@example.com", "password": "admin123"})
    token = login_resp.json()["access_token"]

    # Query ALL for 2023
    print("Querying ALL data for 2023 to find valid port names...")
    resp = requests.post(
        f"{BASE_URL}/indicators/query",
        json={"codigo_indicador": "IND-1.01", "ano": 2023},
        headers={"Authorization": f"Bearer {token}"}
    )
    data = resp.json()
    
    ports = set()
    for row in data.get("data", []):
        if "id_instalacao" in row:
            ports.add(row["id_instalacao"])
            
    print(f"Found {len(ports)} unique ports.")
    print(f"Examples: {list(ports)[:5]}")
    
    if "SANTOS" in ports:
        print("SANTOS is in the list!")
    elif "Porto de Santos" in ports:
        print("'Porto de Santos' is in the list!")
    else:
        print("NEITHER 'SANTOS' nor 'Porto de Santos' found in available data.")

if __name__ == "__main__":
    list_ports()
