#!/usr/bin/env python3
"""
Script diagnóstico para descobrir os códigos corretos de produto
na API SIDRA/IBGE para as tabelas 1612 (c81) e 5457 (c782).

Uso: python discover_sidra_codes.py
"""

import requests
import json

PRODUTOS_BUSCA = ["soja", "milho", "cana", "café", "algodão"]

TABELAS = [
    ("1612", "c81", "Lavoura temporária"),
    ("5457", "c782", "Lavoura temp. + permanente"),
]


def buscar_produtos(tabela: str, classif: str, label: str):
    """Busca todos os produtos de uma tabela/classificação no SIDRA."""
    # Pega 1 UF (SP=35), 1 ano, TODOS os produtos (allxt = all except total)
    url = (
        f"https://apisidra.ibge.gov.br/values"
        f"/t/{tabela}"
        f"/n3/35"               # São Paulo
        f"/v/214"               # Quantidade produzida
        f"/p/last%201"          # Último período
        f"/{classif}/allxt"     # Todos os produtos, sem total
    )
    print(f"\n{'='*60}")
    print(f"Tabela {tabela} / {classif} ({label})")
    print(f"URL: {url}")
    print(f"{'='*60}")

    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"ERRO: {e}")
        return

    if not isinstance(data, list) or len(data) < 2:
        print(f"Resposta inesperada: {str(data)[:200]}")
        return

    # Header
    header = data[0]
    print(f"Header keys: {list(header.keys())}")
    print(f"Total de produtos: {len(data) - 1}")

    # Identifica qual campo D contém o nome e código do produto
    # Tipicamente D4N=nome do produto, D4C=código
    first = data[1]
    print(f"\nPrimeira linha completa:")
    for k, v in first.items():
        print(f"  {k} = {v}")

    # Procura produtos de interesse
    print(f"\nProdutos encontrados (filtro: {PRODUTOS_BUSCA}):")
    print(f"{'Código':<10} {'Nome':<40} {'Valor':>15}")
    print("-" * 70)

    encontrados = {}
    for row in data[1:]:
        # Tenta encontrar nome do produto em todos os campos DxN
        nome_produto = ""
        cod_produto = ""
        for i in range(1, 6):
            dn = row.get(f"D{i}N", "")
            dc = row.get(f"D{i}C", "")
            # O campo do produto geralmente tem nomes como "Soja (em grão)"
            if dn and ("(" in dn or len(dn) > 10):
                # Pode ser nome de produto ou "Quantidade produzida"
                if "produzida" not in dn.lower() and "plantada" not in dn.lower():
                    nome_produto = dn
                    cod_produto = dc
                    break

        valor = row.get("V", "")

        # Filtra pelos produtos de interesse
        nome_lower = nome_produto.lower()
        for busca in PRODUTOS_BUSCA:
            if busca in nome_lower:
                print(f"{cod_produto:<10} {nome_produto:<40} {valor:>15}")
                encontrados[busca] = cod_produto
                break

    print(f"\n--- Resumo códigos encontrados ---")
    for produto, codigo in encontrados.items():
        print(f'    "{produto}": "{codigo}",')

    # Também mostra os primeiros 5 produtos para referência
    print(f"\nPrimeiros 10 produtos (para referência):")
    for row in data[1:11]:
        nomes = []
        for i in range(1, 6):
            dn = row.get(f"D{i}N", "")
            dc = row.get(f"D{i}C", "")
            if dn and "produzida" not in dn.lower() and len(dn) > 3:
                nomes.append(f"{dc}={dn}")
        valor = row.get("V", "")
        print(f"  {' | '.join(nomes)} => V={valor}")


if __name__ == "__main__":
    for tabela, classif, label in TABELAS:
        buscar_produtos(tabela, classif, label)

    print("\n\nDone. Use os códigos acima para atualizar SIDRA_TABELAS em conab.py")
