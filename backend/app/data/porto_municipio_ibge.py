"""Mapeamento porto (nome do Excel) → município no mart BigQuery.

IDs validados contra o mart `marts_impacto.mart_impacto_economico` em 2026-04-06.
Em alguns casos o ID do mart difere do IBGE oficial — usamos o ID do mart para
garantir o join com tonelagem.

Portos sem cobertura no mart (tonelagem = NULL):
  - Porto do Pecém (São Gonçalo do Amarante 2312403): mart não cobre CE além de Fortaleza
  - Porto de Parnaíba (2207702): porto pequeno, não presente no mart
  - Porto de Areia Branca (Guamaré/2404507): mart não tem histórico 2018-2024
  - Porto de Cabedelo (2503209): sem tonelagem no mart
  - Porto de Natal (2408102): sem tonelagem no mart
  - Porto de Manaus (1302603): ausente do mart

Consolidados: usam o município do porto de maior tonelagem da concessão.
"""
from __future__ import annotations

PORTO_MUNICIPIO_MAP: dict[str, dict] = {
    # ── Nordeste ─────────────────────────────────────────────────────────────
    "Porto do Itaqui":
        {"id_municipio": "2111300", "nome": "São Luís",                "uf": "MA", "no_mart": True},
    "Porto de Parnaíba (Porto Piauí)":
        {"id_municipio": "2207702", "nome": "Parnaíba",                "uf": "PI", "no_mart": False},
    "Porto do Pecém":
        {"id_municipio": "2312403", "nome": "São Gonçalo do Amarante", "uf": "CE", "no_mart": False},
    "Porto do Mucuripe (Porto de Fortaleza)":
        {"id_municipio": "2304400", "nome": "Fortaleza",               "uf": "CE", "no_mart": True},
    "Porto de Natal":
        {"id_municipio": "2408102", "nome": "Natal",                   "uf": "RN", "no_mart": True},
    "Porto de Areia Branca":
        # Mart usa Guamaré (2404507) onde fica o terminal de sal; IBGE oficial = 2401107
        {"id_municipio": "2404507", "nome": "Guamaré",                 "uf": "RN", "no_mart": True},
    "Porto de Cabedelo":
        {"id_municipio": "2503209", "nome": "Cabedelo",                "uf": "PB", "no_mart": True},
    "Porto de Suape":
        # Mart usa 2607208 para Ipojuca (IBGE oficial = 2607901)
        {"id_municipio": "2607208", "nome": "Ipojuca",                 "uf": "PE", "no_mart": True},
    "Porto do Recife":
        {"id_municipio": "2611606", "nome": "Recife",                  "uf": "PE", "no_mart": True},
    "Porto de Maceió":
        {"id_municipio": "2704302", "nome": "Maceió",                  "uf": "AL", "no_mart": True},
    "Porto de Aratu":
        # Aratu fica em Madre de Deus/BA no mart (2919926), não Simões Filho
        {"id_municipio": "2919926", "nome": "Madre de Deus",           "uf": "BA", "no_mart": True},
    "Porto de Salvador":
        {"id_municipio": "2927408", "nome": "Salvador",                "uf": "BA", "no_mart": True},
    "Porto de Ilhéus":
        {"id_municipio": "2913606", "nome": "Ilhéus",                  "uf": "BA", "no_mart": True},
    # ── Sudeste ──────────────────────────────────────────────────────────────
    "Porto de Santos":
        {"id_municipio": "3548500", "nome": "Santos",                  "uf": "SP", "no_mart": True},
    "PortosRio (Rio de Janeiro, Niterói, Angra dos Reis)":
        {"id_municipio": "3304557", "nome": "Rio de Janeiro",          "uf": "RJ", "no_mart": True},
    "Porto de Vitória / Capuaba":
        {"id_municipio": "3205309", "nome": "Vitória",                 "uf": "ES", "no_mart": True},
    # ── Sul ──────────────────────────────────────────────────────────────────
    "Portos do Paraná":
        {"id_municipio": "4118204", "nome": "Paranaguá",               "uf": "PR", "no_mart": True},
    "Portos RS (Rio Grande, Pelotas, Porto Alegre)":
        {"id_municipio": "4315602", "nome": "Rio Grande",              "uf": "RS", "no_mart": True},
    "Porto de São Francisco do Sul":
        # Mart usa 4216206 (IBGE oficial = 4216404 diverge do diretório basedosdados)
        {"id_municipio": "4216206", "nome": "São Francisco do Sul",    "uf": "SC", "no_mart": True},
    "Porto de Imbituba":
        # Mart usa 4207304 (IBGE oficial = 4207206 diverge do diretório basedosdados)
        {"id_municipio": "4207304", "nome": "Imbituba",                "uf": "SC", "no_mart": True},
    # ── Norte ────────────────────────────────────────────────────────────────
    "Portos do Pará (Belém, Santarém, Vila do Conde)":
        # Principal: Barcarena (Vila do Conde) com maior tonelagem
        {"id_municipio": "1501303", "nome": "Barcarena",               "uf": "PA", "no_mart": True},
    "Porto de Manaus":
        {"id_municipio": "1302603", "nome": "Manaus",                  "uf": "AM", "no_mart": False},
}
