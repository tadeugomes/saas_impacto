
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

MODULES = {
    4: [f"IND-4.{i:02d}" for i in range(1, 11)],
    5: [f"IND-5.{i:02d}" for i in range(1, 22)],
    6: [f"IND-6.{i:02d}" for i in range(1, 12)],
    7: [f"IND-7.{i:02d}" for i in range(1, 8)],
}

def check_all_modules():
    for module, indicators in MODULES.items():
        print(f"\n=== MODULE {module} ===")
        for ind in indicators:
            try:
                resp = requests.post(
                    f"{BASE_URL}/indicators/query",
                    json={"codigo_indicador": ind, "ano": 2023},
                    timeout=10
                )
                if resp.status_code != 200:
                    error_msg = resp.json().get("detail", resp.text)
                    print(f"  {ind}: ERROR - HTTP {resp.status_code}: {error_msg}")
                    continue
                data = resp.json()
                count = len(data.get('data', []))
                if count > 0:
                    fields = list(data['data'][0].keys())
                    # Get numeric fields (potential value fields)
                    numeric_fields = [f for f in fields if f not in ['id_instalacao', 'ano', 'mes', 'tipo_carga', 'porto']]
                    print(f"  {ind}: {count} records, value fields: {numeric_fields}")
                else:
                    print(f"  {ind}: NO DATA")
            except Exception as e:
                print(f"  {ind}: ERROR - {e}")

if __name__ == "__main__":
    check_all_modules()
