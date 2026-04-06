"""Mapeamento porto (nome do Excel) → município IBGE.

Portos consolidados (PortosRio, Portos RS, Portos do Pará, Portos do Paraná)
usam o município do porto principal da concessão.
"""
from __future__ import annotations

PORTO_MUNICIPIO_MAP: dict[str, dict] = {
    "Porto do Itaqui":                                        {"id_municipio": "2111300", "nome": "São Luís",                   "uf": "MA"},
    "Porto de Parnaíba (Porto Piauí)":                        {"id_municipio": "2207702", "nome": "Parnaíba",                   "uf": "PI"},
    "Porto do Pecém":                                         {"id_municipio": "2303808", "nome": "São Gonçalo do Amarante",    "uf": "CE"},
    "Porto do Mucuripe (Porto de Fortaleza)":                 {"id_municipio": "2304400", "nome": "Fortaleza",                  "uf": "CE"},
    "Porto de Natal":                                         {"id_municipio": "2408102", "nome": "Natal",                     "uf": "RN"},
    "Porto de Areia Branca":                                  {"id_municipio": "2401602", "nome": "Areia Branca",              "uf": "RN"},
    "Porto de Cabedelo":                                      {"id_municipio": "2503209", "nome": "Cabedelo",                  "uf": "PB"},
    "Porto de Suape":                                         {"id_municipio": "2607901", "nome": "Ipojuca",                   "uf": "PE"},
    "Porto do Recife":                                        {"id_municipio": "2611606", "nome": "Recife",                    "uf": "PE"},
    "Porto de Maceió":                                        {"id_municipio": "2704302", "nome": "Maceió",                    "uf": "AL"},
    "Porto de Aratu":                                         {"id_municipio": "2930808", "nome": "Simões Filho",              "uf": "BA"},
    "Porto de Salvador":                                      {"id_municipio": "2927408", "nome": "Salvador",                  "uf": "BA"},
    "Porto de Ilhéus":                                        {"id_municipio": "2913606", "nome": "Ilhéus",                   "uf": "BA"},
    "Porto de Santos":                                        {"id_municipio": "3548500", "nome": "Santos",                   "uf": "SP"},
    "PortosRio (Rio de Janeiro, Niterói, Angra dos Reis)":    {"id_municipio": "3304557", "nome": "Rio de Janeiro",            "uf": "RJ"},
    "Porto de Vitória / Capuaba":                             {"id_municipio": "3205309", "nome": "Vitória",                  "uf": "ES"},
    "Portos do Paraná":                                       {"id_municipio": "4118204", "nome": "Paranaguá",                 "uf": "PR"},
    "Portos RS (Rio Grande, Pelotas, Porto Alegre)":          {"id_municipio": "4315602", "nome": "Rio Grande",               "uf": "RS"},
    "Porto de São Francisco do Sul":                          {"id_municipio": "4217204", "nome": "São Francisco do Sul",     "uf": "SC"},
    "Porto de Imbituba":                                      {"id_municipio": "4207206", "nome": "Imbituba",                  "uf": "SC"},
    "Portos do Pará (Belém, Santarém, Vila do Conde)":        {"id_municipio": "1501402", "nome": "Belém",                    "uf": "PA"},
    "Porto de Manaus":                                        {"id_municipio": "1302603", "nome": "Manaus",                   "uf": "AM"},
}
