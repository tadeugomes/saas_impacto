
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

MODULES = {
    3: ['IND-3.01', 'IND-3.02', 'IND-3.03', 'IND-3.04', 'IND-3.05', 'IND-3.06', 'IND-3.07', 'IND-3.08', 'IND-3.09', 'IND-3.10'],
    5: ['IND-5.01', 'IND-5.02', 'IND-5.03', 'IND-5.04', 'IND-5.05', 'IND-5.06', 'IND-5.07', 'IND-5.08', 'IND-5.09', 'IND-5.10'],
    6: ['IND-6.01', 'IND-6.02', 'IND-6.03', 'IND-6.04', 'IND-6.05', 'IND-6.06', 'IND-6.07', 'IND-6.08', 'IND-6.09', 'IND-6.10'],
}

def check_modules():
    for module, indicators in MODULES.items():
        print(f"\n=== MODULE {module} ===")
        for ind in indicators:
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
                    numeric_fields = [f for f in fields if f not in ['id_instalacao', 'ano', 'mes', 'tipo_carga', 'porto', 'id_municipio']]
                    print(f"  {ind}: {count} records, value fields: {numeric_fields}")
                else:
                    print(f"  {ind}: NO DATA")
            except Exception as e:
                print(f"  {ind}: ERROR - {e}")

if __name__ == "__main__":
    check_modules()
