
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

INDICATORS = [
    'IND-2.01', 'IND-2.02', 'IND-2.03', 'IND-2.04', 'IND-2.05',
    'IND-2.06', 'IND-2.07', 'IND-2.08', 'IND-2.09', 'IND-2.10',
    'IND-2.11', 'IND-2.12', 'IND-2.13'
]

def check_indicators():
    for ind in INDICATORS:
        try:
            resp = requests.post(
                f"{BASE_URL}/indicators/query",
                json={"codigo_indicador": ind, "ano": 2023},
                timeout=10
            )
            data = resp.json()
            count = len(data.get('data', []))
            if count > 0:
                fields = list(data['data'][0].keys())
                print(f"{ind}: {count} records, fields: {fields}")
            else:
                print(f"{ind}: NO DATA")
        except Exception as e:
            print(f"{ind}: ERROR - {e}")

if __name__ == "__main__":
    check_indicators()
