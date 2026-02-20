"""
Serviço Genérico de Indicadores.

Este serviço fornece uma interface unificada para consultar
qualquer indicador de qualquer módulo (1-7).
"""

import logging
import math
import time
import inspect
from decimal import Decimal
from typing import List, Dict, Any, Optional

from app.db.bigquery.client import BigQueryClient, get_bigquery_client
from app.db.bigquery.queries import ALL_QUERIES, get_query
from app.schemas.indicators import (
    GenericIndicatorRequest,
    GenericIndicatorResponse,
    DataQualityWarning,
    IndicatorMetadata,
    AllIndicatorsResponse,
)
from app.services.indicator_query_cache import IndicatorQueryCache


logger = logging.getLogger(__name__)

# Mapping between Port names (frontend) and IBGE 7-digit IDs
# This is essential for municipal-level indicators (RAIS, PIB, SICONFI)
# Comprehensive mapping covering all major Brazilian ports and installations
PORT_TO_IBGE_MAPPING = {
    # REGIÃO NORTE
    'Amapá': '1600306',
    'Belém': '1501402',
    'Itaqui': '2111300',
    'Itacoatiara': '1302103',
    'Manaus': '1302603',
    'Pecém': '2312403',
    'Porto Velho': '1100205',
    'Santarém': '1506807',
    'Vila do Conde': '1504139',

    # REGIÃO NORDESTE
    'Aratu': '2906501',
    'Cabedelo': '2504009',
    'Fortaleza': '2304400',
    'Mucuripe': '2304400',
    'Ilhéus': '2913350',
    'Imbui': '2901706',
    'Itaparica': '2910102',
    'Jacuípe': '2901706',
    'Maceió': '2704302',
    'Natal': '2408102',
    'Pecém (Ceará)': '2312403',
    'Porto de Aratu': '2906501',
    'Porto de Recife': '2611606',
    'Porto de Salvador': '2927408',
    'Porto de Suape': '2607208',
    'Recife': '2611606',
    'Salvador': '2927408',
    'Suape': '2607208',
    'São Luís': '2111300',

    # REGIÃO CENTRO-OESTE
    'Alvorada do Norte': '5201107',

    # REGIÃO SUDESTE
    'Angra dos Reis': '3300100',
    'Angra dos Reis (Ilha Grande)': '3300100',
    'Aracruz': '3201207',
    'Barra do Riacho': '3201207',
    'Caboto': '3301702',
    'Cabo Frio': '3301702',
    'Caraguatatuba': '3511305',
    'Guaíba Island': '3304557',
    'Ilha Guaíba': '3304557',
    'Ilha do Bom Jesus': '3304557',
    'Itaguaí': '3302000',
    'Itaguaí (Sepetiba)': '3302000',
    'Macaé': '3302403',
    'Niterói': '3303302',
    'Porto de Angra dos Reis': '3300100',
    'Porto de Cabo Frio': '3301702',
    'Porto de Ilha Guaíba': '3304557',
    'Porto de Itaguaí': '3302000',
    'Porto de Niterói': '3303302',
    'Porto do Rio de Janeiro': '3304557',
    'Porto de São Sebastião': '3550703',
    'Porto de Vitória': '3205309',
    'Rio de Janeiro': '3304557',
    'São Sebastião': '3550703',
    'Sepetiba': '3302000',
    'Tubarão': '3205309',
    'Tubarão (Vitória)': '3205309',
    'Vila Velha': '3205200',
    'Vitória': '3205309',
    'Voador': '3550703',

    # REGIÃO SUL
    'Antonina': '4101200',
    'Araquari': '4201406',
    'Balneário Camboriú': '4202105',
    'Barra do Sul': '4202400',
    'Braço do Norte': '4203508',
    'Capivari de Baixo': '4204607',
    'Garopaba': '4206105',
    'Imbituba': '4206805',
    'Itajaí': '4208203',
    'Itapoá': '4208302',
    'Laguna': '4210004',
    'Navegantes': '4211655',
    'Paranaguá': '4118204',
    'Penha': '4215304',
    'Porto de Balneário Camboriú': '4202105',
    'Porto de Braço do Norte': '4203508',
    'Porto de Capivari de Baixo': '4204607',
    'Porto de Garopaba': '4206105',
    'Porto de Imbituba': '4206805',
    'Porto de Itajaí': '4208203',
    'Porto de Itapoá': '4208302',
    'Porto de Laguna': '4210004',
    'Porto de Navegantes': '4211655',
    'Porto de Penha': '4215304',
    'Porto de São Francisco do Sul': '4220000',
    'Porto de Torres': '4221406',
    'Rio Grande': '4315602',
    'São Francisco do Sul': '4220000',
    'Torres': '4221406',

    # ESTADO DE SÃO PAULO (Múltiplas instalações)
    'Bertioga': '3506402',
    'Cubatão': '3513504',
    'Porto de Santos': '3548500',
    'Santos': '3548500',
    'São Vicente': '3551009',
    'São Sebastião (SP)': '3550703',

    # TERMINAIS ESPECÍFICOS (TUPs e outros)
    # Santos
    'DP World Santos': '3548500',
    'Portonave Santos': '3548500',
    'Brado Santos': '3548500',
    'Libra Santos': '3548500',
    'Santos Brasil': '3548500',
    'Valec Moçambique': '3548500',
    'Codesp': '3548500',
    'TGG Santos': '3548500',
    'T37 Santos': '3548500',

    # Paranaguá
    'TCP Paranaguá': '4118204',
    'TNG Paranaguá': '4118204',

    # Itajaí
    'Portonave Itajaí': '4208203',

    # Rio Grande
    'Terminais Riograndense': '4315602',

    # Itaguaí
    'CSN Itaguaí': '3302000',
    'Tecar Itaguaí': '3302000',
    'Valec Itaguaí': '3302000',

    # São Luís (Itaqui)
    'Valec Itaqui': '2111300',
    'Granel Itaqui': '2111300',
    'Alumar': '2111300',

    # Pecém
    'Porto do Pecém': '2312403',
    'SZP Pecém': '2312403',

    # Suape
    'TCU Suape': '2607208',
    'WPO Suape': '2607208',

    # Vitória
    'TVV Vitória': '3205309',
    'TGV Vitória': '3205309',
    'Valec Vitória': '3205309',
    'ArcelorMittal Tubarão': '3205309',
}


MODULE5_VALUE_FIELD_BY_CODE = {
    "IND-5.01": "pib_municipal",
    "IND-5.02": "pib_per_capita",
    "IND-5.03": "populacao",
    "IND-5.04": "pib_servicos_percentual",
    "IND-5.05": "pib_industria_percentual",
    "IND-5.06": "intensidade_portuaria",
    "IND-5.07": "intensidade_comercial",
    "IND-5.08": "concentracao_emprego_pct",
    "IND-5.09": "concentracao_salarial_pct",
    "IND-5.10": "crescimento_pib_percentual",
    "IND-5.11": "crescimento_tonelagem_pct",
    "IND-5.12": "crescimento_empregos_pct",
    "IND-5.13": "crescimento_comercio_pct",
    "IND-5.14": "correlacao",
    "IND-5.15": "correlacao",
    "IND-5.16": "correlacao",
    "IND-5.17": "elasticidade",
    "IND-5.18": "participacao_pib_regional_pct",
    "IND-5.19": "crescimento_relativo_uf_pp",
    "IND-5.20": "razao_emprego_total_portuario",
    "IND-5.21": "indice_concentracao_portuaria",
}

MODULE5_SUM_CODES = {"IND-5.01", "IND-5.03"}


class IndicatorAccessError(Exception):
    """Erro de autorizacao/regra de acesso para consulta de indicador."""


class IndicatorQuotaError(Exception):
    """Erro de quota/custo de consulta."""


# ============================================================================
# Metadados de Todos os Indicadores
# ============================================================================

INDICATORS_METADATA: Dict[str, Dict[str, Any]] = {
    # Module 1 - Ship Operations
    "IND-1.01": {
        "codigo": "IND-1.01",
        "nome": "Tempo Médio de Espera",
        "modulo": 1,
        "unidade": "Horas",
        "unctad": True,
        "descricao": "Tempo médio entre a chegada e o início da atracação",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - tempos_atracacao",
    },
    "IND-1.02": {
        "codigo": "IND-1.02",
        "nome": "Tempo Médio em Porto",
        "modulo": 1,
        "unidade": "Horas",
        "unctad": True,
        "descricao": "Tempo médio total no porto (atracado + espera)",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - tempos_atracacao",
    },
    "IND-1.03": {
        "codigo": "IND-1.03",
        "nome": "Tempo Bruto de Atracação",
        "modulo": 1,
        "unidade": "Horas",
        "unctad": True,
        "descricao": "Tempo médio desde atracação até desatracação",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - tempos_atracacao",
    },
    "IND-1.04": {
        "codigo": "IND-1.04",
        "nome": "Tempo Líquido de Operação",
        "modulo": 1,
        "unidade": "Horas",
        "unctad": True,
        "descricao": "Tempo efetivo de operação com carga",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - tempos_atracacao",
    },
    "IND-1.05": {
        "codigo": "IND-1.05",
        "nome": "Taxa de Ocupação de Berços",
        "modulo": 1,
        "unidade": "%",
        "unctad": True,
        "descricao": "Percentual médio de ocupação dos berços",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - taxa_ocupacao",
    },
    "IND-1.06": {
        "codigo": "IND-1.06",
        "nome": "Tempo Ocioso Médio por Turno",
        "modulo": 1,
        "unidade": "Horas",
        "unctad": True,
        "descricao": "Tempo médio de paralisação durante operação",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - tempos_atracacao_paralisacao",
    },
    "IND-1.07": {
        "codigo": "IND-1.07",
        "nome": "Arqueação Bruta Média",
        "modulo": 1,
        "unidade": "GT",
        "unctad": True,
        "descricao": "Tamanho médio dos navios em Gross Tonnage",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - v_atracacao_validada",
    },
    "IND-1.08": {
        "codigo": "IND-1.08",
        "nome": "Comprimento Médio de Navios",
        "modulo": 1,
        "unidade": "Metros",
        "unctad": True,
        "descricao": "Comprimento médio dos navios atracados",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - v_atracacao_validada",
    },
    "IND-1.09": {
        "codigo": "IND-1.09",
        "nome": "Calado Máximo Operacional",
        "modulo": 1,
        "unidade": "Metros",
        "unctad": True,
        "descricao": "Maior calado já registrado na instalação",
        "granularidade": "Instalação",
        "fonte_dados": "ANTAQ - v_atracacao_validada",
    },
    "IND-1.10": {
        "codigo": "IND-1.10",
        "nome": "Distribuição por Tipo de Navio",
        "modulo": 1,
        "unidade": "%",
        "unctad": True,
        "descricao": "Distribuição de atracações por tipo de navegação",
        "granularidade": "Instalação/Ano/Tipo",
        "fonte_dados": "ANTAQ - v_atracacao_validada",
    },
    "IND-1.11": {
        "codigo": "IND-1.11",
        "nome": "Número de Atracações",
        "modulo": 1,
        "unidade": "Contagem",
        "unctad": False,
        "descricao": "Total de atracações no período",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - v_atracacao_validada",
    },
    "IND-1.12": {
        "codigo": "IND-1.12",
        "nome": "Índice de Paralisação",
        "modulo": 1,
        "unidade": "%",
        "unctad": False,
        "descricao": "Percentual do tempo de paralisação sobre tempo atracado",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - tempos_atracacao",
    },
    # Module 2 - Cargo Operations
    "IND-2.01": {
        "codigo": "IND-2.01",
        "nome": "Total Carga Movimentada",
        "modulo": 2,
        "unidade": "Toneladas",
        "unctad": True,
        "descricao": "Somatório do peso de todas as cargas",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - v_carga_validada",
    },
    "IND-2.02": {
        "codigo": "IND-2.02",
        "nome": "TEUs Movimentados",
        "modulo": 2,
        "unidade": "TEUs",
        "unctad": True,
        "descricao": "Total de contêineres em TEUs",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - carga_conteinerizada",
    },
    "IND-2.03": {
        "codigo": "IND-2.03",
        "nome": "Total Passageiros Ferry",
        "modulo": 2,
        "unidade": "Contagem",
        "unctad": True,
        "descricao": "Total de passageiros em travessias",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - v_atracacao_validada",
    },
    "IND-2.04": {
        "codigo": "IND-2.04",
        "nome": "Total Passageiros Cruzeiro",
        "modulo": 2,
        "unidade": "Contagem",
        "unctad": True,
        "descricao": "Total de passageiros de cruzeiro",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - v_atracacao_validada",
    },
    "IND-2.05": {
        "codigo": "IND-2.05",
        "nome": "Carga Média por Atracação",
        "modulo": 2,
        "unidade": "Toneladas/Atracação",
        "unctad": True,
        "descricao": "Média de carga por operação de atracação",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - v_carga_validada",
    },
    "IND-2.06": {
        "codigo": "IND-2.06",
        "nome": "Produtividade Bruta",
        "modulo": 2,
        "unidade": "Toneladas/Hora",
        "unctad": True,
        "descricao": "Toneladas movimentadas por hora de operação",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - v_carga_validada + tempos_atracacao",
    },
    "IND-2.07": {
        "codigo": "IND-2.07",
        "nome": "Produtividade Granel Sólido",
        "modulo": 2,
        "unidade": "Toneladas/Hora",
        "unctad": True,
        "descricao": "Produtividade para carga de granel sólido",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - v_carga_validada + tempos_atracacao",
    },
    "IND-2.08": {
        "codigo": "IND-2.08",
        "nome": "Produtividade Granel Líquido",
        "modulo": 2,
        "unidade": "Toneladas/Hora",
        "unctad": True,
        "descricao": "Produtividade para carga de granel líquido",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - v_carga_validada + tempos_atracacao",
    },
    "IND-2.09": {
        "codigo": "IND-2.09",
        "nome": "Movimentos/Hora Contêiner",
        "modulo": 2,
        "unidade": "Movimentos/Hora",
        "unctad": True,
        "descricao": "LPSPH - Lifts per ship hour",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - carga_conteinerizada + tempos_atracacao",
    },
    "IND-2.10": {
        "codigo": "IND-2.10",
        "nome": "Toneladas por Hectare",
        "modulo": 2,
        "unidade": "Toneladas/Hectare",
        "unctad": True,
        "descricao": "Densidade de carga por área do terminal",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - v_carga_validada + instalacao_origem",
    },
    "IND-2.11": {
        "codigo": "IND-2.11",
        "nome": "Toneladas por Metro de Cais",
        "modulo": 2,
        "unidade": "Toneladas/Metro",
        "unctad": True,
        "descricao": "Densidade de carga por extensão de cais",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - v_carga_validada + instalacao_origem",
    },
    "IND-2.12": {
        "codigo": "IND-2.12",
        "nome": "Mix de Carga",
        "modulo": 2,
        "unidade": "%",
        "unctad": False,
        "descricao": "Distribuição percentual por tipo de carga",
        "granularidade": "Instalação/Ano/Tipo",
        "fonte_dados": "ANTAQ - v_carga_validada",
    },
    "IND-2.13": {
        "codigo": "IND-2.13",
        "nome": "Sazonalidade Mensal",
        "modulo": 2,
        "unidade": "Índice",
        "unctad": False,
        "descricao": "Índice de sazonalidade da movimentação de carga",
        "granularidade": "Instalação/Ano/Mês",
        "fonte_dados": "ANTAQ - v_carga_validada",
    },
    # Module 3 - Human Resources
    "IND-3.01": {
        "codigo": "IND-3.01",
        "nome": "Empregos Diretos Portuários",
        "modulo": 3,
        "unidade": "Contagem",
        "unctad": True,
        "descricao": "Número de empregos formais no setor portuário",
        "granularidade": "Município/Ano",
        "fonte_dados": "RAIS - microdados_vinculos",
    },
    "IND-3.02": {
        "codigo": "IND-3.02",
        "nome": "Paridade de Gênero Geral",
        "modulo": 3,
        "unidade": "%",
        "unctad": True,
        "descricao": "Percentual de mulheres no setor portuário",
        "granularidade": "Município/Ano",
        "fonte_dados": "RAIS - microdados_vinculos",
    },
    "IND-3.03": {
        "codigo": "IND-3.03",
        "nome": "Paridade por Categoria Profissional",
        "modulo": 3,
        "unidade": "%",
        "unctad": True,
        "descricao": "Percentual de mulheres por categoria profissional",
        "granularidade": "Município/Ano/Categoria",
        "fonte_dados": "RAIS - microdados_vinculos",
    },
    "IND-3.04": {
        "codigo": "IND-3.04",
        "nome": "Taxa de Emprego Temporário",
        "modulo": 3,
        "unidade": "%",
        "unctad": True,
        "descricao": "Percentual de vínculos temporários",
        "granularidade": "Município/Ano",
        "fonte_dados": "RAIS - microdados_vinculos",
    },
    "IND-3.05": {
        "codigo": "IND-3.05",
        "nome": "Salário Médio Setor Portuário",
        "modulo": 3,
        "unidade": "R$",
        "unctad": True,
        "descricao": "Remuneração média no setor portuário",
        "granularidade": "Município/Ano",
        "fonte_dados": "RAIS - microdados_vinculos",
    },
    "IND-3.06": {
        "codigo": "IND-3.06",
        "nome": "Massa Salarial Portuária",
        "modulo": 3,
        "unidade": "R$/ano",
        "unctad": True,
        "descricao": "Somatório da remuneração anual do setor",
        "granularidade": "Município/Ano",
        "fonte_dados": "RAIS - microdados_vinculos",
    },
    "IND-3.07": {
        "codigo": "IND-3.07",
        "nome": "Produtividade (ton/empregado)",
        "modulo": 3,
        "unidade": "Toneladas/Empregado",
        "unctad": True,
        "descricao": "Toneladas movimentadas por empregado portuário",
        "granularidade": "Município/Ano",
        "fonte_dados": "ANTAQ + RAIS",
    },
    "IND-3.08": {
        "codigo": "IND-3.08",
        "nome": "Receita por Empregado",
        "modulo": 3,
        "unidade": "R$/Empregado",
        "unctad": True,
        "descricao": "PIB por empregado portuário (proxy)",
        "granularidade": "Município/Ano",
        "fonte_dados": "RAIS + IBGE PIB",
    },
    "IND-3.09": {
        "codigo": "IND-3.09",
        "nome": "Distribuição por Escolaridade",
        "modulo": 3,
        "unidade": "%",
        "unctad": False,
        "descricao": "Distribuição por grau de instrução",
        "granularidade": "Município/Ano/Escolaridade",
        "fonte_dados": "RAIS - microdados_vinculos",
    },
    "IND-3.10": {
        "codigo": "IND-3.10",
        "nome": "Idade Média",
        "modulo": 3,
        "unidade": "Anos",
        "unctad": False,
        "descricao": "Idade média dos trabalhadores portuários",
        "granularidade": "Município/Ano",
        "fonte_dados": "RAIS - microdados_vinculos",
    },
    "IND-3.11": {
        "codigo": "IND-3.11",
        "nome": "Variação Anual de Empregos",
        "modulo": 3,
        "unidade": "%",
        "unctad": False,
        "descricao": "Variação percentual anual de empregos",
        "granularidade": "Município/Ano",
        "fonte_dados": "RAIS - microdados_vinculos",
    },
    "IND-3.12": {
        "codigo": "IND-3.12",
        "nome": "Participação no Emprego Local",
        "modulo": 3,
        "unidade": "%",
        "unctad": False,
        "descricao": "Participação do setor portuário no emprego total",
        "granularidade": "Município/Ano",
        "fonte_dados": "RAIS - microdados_vinculos",
    },
    # Module 4 - Foreign Trade
    "IND-4.01": {
        "codigo": "IND-4.01",
        "nome": "Valor FOB Exportações",
        "modulo": 4,
        "unidade": "US$",
        "unctad": False,
        "descricao": "Valor total das exportações FOB",
        "granularidade": "Município/Ano",
        "fonte_dados": "Comex Stat - municipio_exportacao",
    },
    "IND-4.02": {
        "codigo": "IND-4.02",
        "nome": "Valor FOB Importações",
        "modulo": 4,
        "unidade": "US$",
        "unctad": False,
        "descricao": "Valor total das importações FOB",
        "granularidade": "Município/Ano",
        "fonte_dados": "Comex Stat - municipio_importacao",
    },
    "IND-4.03": {
        "codigo": "IND-4.03",
        "nome": "Balança Comercial do Porto",
        "modulo": 4,
        "unidade": "US$",
        "unctad": False,
        "descricao": "Exportações menos Importações",
        "granularidade": "Município/Ano",
        "fonte_dados": "Comex Stat",
    },
    "IND-4.04": {
        "codigo": "IND-4.04",
        "nome": "Peso Líquido Exportações",
        "modulo": 4,
        "unidade": "kg",
        "unctad": False,
        "descricao": "Peso total das exportações",
        "granularidade": "Município/Ano",
        "fonte_dados": "Comex Stat - municipio_exportacao",
    },
    "IND-4.05": {
        "codigo": "IND-4.05",
        "nome": "Peso Líquido Importações",
        "modulo": 4,
        "unidade": "kg",
        "unctad": False,
        "descricao": "Peso total das importações",
        "granularidade": "Município/Ano",
        "fonte_dados": "Comex Stat - municipio_importacao",
    },
    "IND-4.06": {
        "codigo": "IND-4.06",
        "nome": "Valor Médio por kg Exportação",
        "modulo": 4,
        "unidade": "US$/kg",
        "unctad": False,
        "descricao": "Valor médio por quilograma exportado",
        "granularidade": "Município/Ano",
        "fonte_dados": "Comex Stat - municipio_exportacao",
    },
    "IND-4.07": {
        "codigo": "IND-4.07",
        "nome": "Concentração por País",
        "modulo": 4,
        "unidade": "%",
        "unctad": False,
        "descricao": "Distribuição de exportações por país de destino",
        "granularidade": "Município/Ano/País",
        "fonte_dados": "Comex Stat - municipio_exportacao",
    },
    "IND-4.08": {
        "codigo": "IND-4.08",
        "nome": "Concentração por NCM",
        "modulo": 4,
        "unidade": "%",
        "unctad": False,
        "descricao": "Distribuição por capítulo NCM",
        "granularidade": "Município/Ano/NCM",
        "fonte_dados": "Comex Stat - municipio_exportacao",
    },
    "IND-4.09": {
        "codigo": "IND-4.09",
        "nome": "Variação Anual do Comércio",
        "modulo": 4,
        "unidade": "%",
        "unctad": False,
        "descricao": "Variação percentual anual do comércio exterior",
        "granularidade": "Município/Ano",
        "fonte_dados": "Comex Stat - municipio_exportacao",
    },
    "IND-4.10": {
        "codigo": "IND-4.10",
        "nome": "Market Share entre Portos",
        "modulo": 4,
        "unidade": "%",
        "unctad": False,
        "descricao": "Participação no total nacional",
        "granularidade": "Município/Ano",
        "fonte_dados": "Comex Stat - municipio_exportacao",
    },
    # Module 5 - Economic Impact
    "IND-5.01": {
        "codigo": "IND-5.01",
        "nome": "PIB Municipal",
        "modulo": 5,
        "unidade": "R$",
        "unctad": False,
        "descricao": "Nível de PIB municipal em valores correntes: mede o tamanho econômico local no ano de referência.",
        "granularidade": "Município/Ano",
        "fonte_dados": "IBGE - PIB municipal",
    },
    "IND-5.02": {
        "codigo": "IND-5.02",
        "nome": "PIB per Capita",
        "modulo": 5,
        "unidade": "R$/habitante",
        "unctad": False,
        "descricao": "PIB per capita: PIB municipal dividido pela população residente, para comparar níveis econômicos entre municípios.",
        "granularidade": "Município/Ano",
        "fonte_dados": "IBGE - PIB municipal + IBGE - População municipal",
    },
    "IND-5.03": {
        "codigo": "IND-5.03",
        "nome": "População Municipal",
        "modulo": 5,
        "unidade": "Habitantes",
        "unctad": False,
        "descricao": "População residente no município, usada como base para indicadores per capita.",
        "granularidade": "Município/Ano",
        "fonte_dados": "IBGE - População municipal",
    },
    "IND-5.04": {
        "codigo": "IND-5.04",
        "nome": "PIB Setorial - Serviços",
        "modulo": 5,
        "unidade": "%",
        "unctad": False,
        "descricao": "Participação do setor de serviços no PIB municipal; quanto maior, maior o peso do setor de serviços.",
        "granularidade": "Município/Ano",
        "fonte_dados": "IBGE - PIB municipal",
    },
    "IND-5.05": {
        "codigo": "IND-5.05",
        "nome": "PIB Setorial - Indústria",
        "modulo": 5,
        "unidade": "%",
        "unctad": False,
        "descricao": "Participação do setor industrial no PIB municipal; mede peso relativo da indústria local.",
        "granularidade": "Município/Ano",
        "fonte_dados": "IBGE - PIB municipal",
    },
    "IND-5.06": {
        "codigo": "IND-5.06",
        "nome": "Intensidade Portuária",
        "modulo": 5,
        "unidade": "Toneladas/R$",
        "unctad": False,
        "descricao": "Razão entre tonelagem movimentada e PIB municipal: intensidade de atividade logística por unidade econômica.",
        "granularidade": "Município/Ano",
        "fonte_dados": "ANTAQ - v_carga_metodologia_oficial + IBGE - PIB municipal",
    },
    "IND-5.07": {
        "codigo": "IND-5.07",
        "nome": "Intensidade Comercial",
        "modulo": 5,
        "unidade": "US$/R$",
        "unctad": False,
        "descricao": "Razão entre comércio exterior (exportação+importação) e PIB municipal: indica exposição do comércio no contexto econômico local.",
        "granularidade": "Município/Ano",
        "fonte_dados": "ComexStat + IBGE - PIB municipal",
    },
    "IND-5.08": {
        "codigo": "IND-5.08",
        "nome": "Concentração de Emprego Portuário",
        "modulo": 5,
        "unidade": "%",
        "unctad": False,
        "descricao": "Participação percentual dos empregos de CNAEs portuários sobre o total de empregos do município.",
        "granularidade": "Município/Ano",
        "fonte_dados": "RAIS - microdados_vinculos",
    },
    "IND-5.09": {
        "codigo": "IND-5.09",
        "nome": "Concentração Salarial Portuária",
        "modulo": 5,
        "unidade": "%",
        "unctad": False,
        "descricao": "Participação da massa salarial dos vínculos portuários sobre a massa salarial municipal total.",
        "granularidade": "Município/Ano",
        "fonte_dados": "RAIS - microdados_vinculos",
    },
    "IND-5.10": {
        "codigo": "IND-5.10",
        "nome": "Crescimento PIB Municipal",
        "modulo": 5,
        "unidade": "%",
        "unctad": False,
        "descricao": "Variação percentual anual do PIB municipal em relação ao ano anterior.",
        "granularidade": "Município/Ano",
        "fonte_dados": "IBGE - PIB municipal",
    },
    "IND-5.11": {
        "codigo": "IND-5.11",
        "nome": "Crescimento de Tonelagem",
        "modulo": 5,
        "unidade": "%",
        "unctad": False,
        "descricao": "Variação percentual anual da tonelagem movimentada por município.",
        "granularidade": "Município/Ano",
        "fonte_dados": "ANTAQ - v_carga_metodologia_oficial",
    },
    "IND-5.12": {
        "codigo": "IND-5.12",
        "nome": "Crescimento de Empregos",
        "modulo": 5,
        "unidade": "%",
        "unctad": False,
        "descricao": "Variação percentual anual dos empregos portuários ativos do município.",
        "granularidade": "Município/Ano",
        "fonte_dados": "RAIS - microdados_vinculos",
    },
    "IND-5.13": {
        "codigo": "IND-5.13",
        "nome": "Crescimento de Comércio Exterior",
        "modulo": 5,
        "unidade": "%",
        "unctad": False,
        "descricao": "Variação percentual anual do comércio exterior (exportação + importação) por município.",
        "granularidade": "Município/Ano",
        "fonte_dados": "ComexStat - municipio_exportacao/importacao",
    },
    "IND-5.14": {
        "codigo": "IND-5.14",
        "nome": "Correlação Tonelagem × PIB",
        "modulo": 5,
        "unidade": "Coeficiente",
        "unctad": False,
        "descricao": "Coeficiente de correlação entre evolução de tonelagem e PIB municipal (mínimo 5 anos úteis). Correlação não implica causalidade; trata-se apenas de associação.",
        "granularidade": "Município",
        "fonte_dados": "ANTAQ - v_carga_metodologia_oficial + IBGE - PIB municipal",
    },
    "IND-5.15": {
        "codigo": "IND-5.15",
        "nome": "Correlação Tonelagem × Empregos",
        "modulo": 5,
        "unidade": "Coeficiente",
        "unctad": False,
        "descricao": "Coeficiente de correlação entre tonelagem e empregos portuários (mínimo 5 anos úteis). Correlação não implica causalidade; trata-se apenas de associação.",
        "granularidade": "Município",
        "fonte_dados": "ANTAQ - v_carga_metodologia_oficial + RAIS - microdados_vinculos",
    },
    "IND-5.16": {
        "codigo": "IND-5.16",
        "nome": "Correlação Comércio × PIB",
        "modulo": 5,
        "unidade": "Coeficiente",
        "unctad": False,
        "descricao": "Coeficiente de correlação entre comércio exterior e PIB municipal (mínimo 5 anos úteis). Correlação não implica causalidade; trata-se apenas de associação.",
        "granularidade": "Município",
        "fonte_dados": "ComexStat + IBGE - PIB municipal",
    },
    "IND-5.17": {
        "codigo": "IND-5.17",
        "nome": "Elasticidade Tonelagem/PIB",
        "modulo": 5,
        "unidade": "Elasticidade",
        "unctad": False,
        "descricao": "Elasticidade da tonelagem em relação ao PIB municipal (regressão log-log). Não representa causalidade direta. Correlação não implica causalidade; trata-se apenas de associação.",
        "granularidade": "Município",
        "fonte_dados": "ANTAQ - v_carga_metodologia_oficial + IBGE - PIB municipal",
    },
    "IND-5.18": {
        "codigo": "IND-5.18",
        "nome": "Participação no PIB Regional",
        "modulo": 5,
        "unidade": "%",
        "unctad": False,
        "descricao": "Participação do município no PIB da sua microrregião no ano, para comparar concentração territorial.",
        "granularidade": "Município/Ano",
        "fonte_dados": "IBGE - PIB municipal",
    },
    "IND-5.19": {
        "codigo": "IND-5.19",
        "nome": "Crescimento Relativo ao Estado",
        "modulo": 5,
        "unidade": "Pontos percentuais",
        "unctad": False,
        "descricao": "Diferença entre crescimento do PIB municipal e crescimento médio do estado no mesmo ano.",
        "granularidade": "Município/Ano",
        "fonte_dados": "IBGE - PIB municipal + IBGE - PIB estadual",
    },
    "IND-5.20": {
        "codigo": "IND-5.20",
        "nome": "Razão Emprego Total/Portuário",
        "modulo": 5,
        "unidade": "Razão",
        "unctad": False,
        "descricao": "Relação entre empregos totais e empregos portuários; dimensão da dependência local do ciclo portuário.",
        "granularidade": "Município/Ano",
        "fonte_dados": "RAIS - microdados_vinculos",
    },
    "IND-5.21": {
        "codigo": "IND-5.21",
        "nome": "Índice de Concentração Portuária",
        "modulo": 5,
        "unidade": "Índice (0-100)",
        "unctad": False,
        "descricao": "Índice composto da intensidade econômica portuária (emprego, tonelagem e participação no PIB regional).",
        "granularidade": "Município/Ano",
        "fonte_dados": "RAIS - microdados_vinculos + ANTAQ - v_carga_metodologia_oficial + IBGE - PIB municipal",
    },
    # Module 6 - Public Finance
    "IND-6.01": {
        "codigo": "IND-6.01",
        "nome": "Arrecadação de ICMS",
        "modulo": 6,
        "unidade": "R$",
        "unctad": False,
        "descricao": "Total arrecadado de ICMS",
        "granularidade": "Município/Ano",
        "fonte_dados": "FINBRA/STN - receitas",
    },
    "IND-6.02": {
        "codigo": "IND-6.02",
        "nome": "Arrecadação de ISS",
        "modulo": 6,
        "unidade": "R$",
        "unctad": False,
        "descricao": "Total arrecadado de ISS",
        "granularidade": "Município/Ano",
        "fonte_dados": "FINBRA/STN - receitas",
    },
    "IND-6.03": {
        "codigo": "IND-6.03",
        "nome": "Receita Total Municipal",
        "modulo": 6,
        "unidade": "R$",
        "unctad": False,
        "descricao": "Total de receitas do município",
        "granularidade": "Município/Ano",
        "fonte_dados": "FINBRA/STN - receitas",
    },
    "IND-6.04": {
        "codigo": "IND-6.04",
        "nome": "Receita per Capita",
        "modulo": 6,
        "unidade": "R$/habitante",
        "unctad": False,
        "descricao": "Receita total dividida pela população",
        "granularidade": "Município/Ano",
        "fonte_dados": "FINBRA/STN + IBGE População",
    },
    "IND-6.05": {
        "codigo": "IND-6.05",
        "nome": "Crescimento da Receita",
        "modulo": 6,
        "unidade": "%",
        "unctad": False,
        "descricao": "Variação percentual anual da receita",
        "granularidade": "Município/Ano",
        "fonte_dados": "FINBRA/STN - receitas",
    },
    "IND-6.06": {
        "codigo": "IND-6.06",
        "nome": "ICMS por Tonelada",
        "modulo": 6,
        "unidade": "R$/ton",
        "unctad": False,
        "descricao": "ICMS arrecadado por tonelada movimentada",
        "granularidade": "Município/Ano",
        "fonte_dados": "FINBRA/STN + ANTAQ",
    },
    # Module 7 - Synthetic Indices
    "IND-7.01": {
        "codigo": "IND-7.01",
        "nome": "Índice de Eficiência Operacional",
        "modulo": 7,
        "unidade": "Índice (0-100)",
        "unctad": False,
        "descricao": "Score composto de produtividade, ocupação e ociosidade",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - múltiplas views",
    },
    "IND-7.02": {
        "codigo": "IND-7.02",
        "nome": "Índice de Relevância Portuária",
        "modulo": 7,
        "unidade": "Índice (0-100)",
        "unctad": False,
        "descricao": "Score baseado em tonelagem e número de atracações",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - v_carga_validada",
    },
    "IND-7.03": {
        "codigo": "IND-7.03",
        "nome": "Índice de Integração Multimodal",
        "modulo": 7,
        "unidade": "Índice (0-100)",
        "unctad": False,
        "descricao": "Diversificação de modais e tipos de carga",
        "granularidade": "Município/Ano",
        "fonte_dados": "ANTAQ - múltiplas views",
    },
    "IND-7.04": {
        "codigo": "IND-7.04",
        "nome": "Índice de Concentração Portuária",
        "modulo": 7,
        "unidade": "Índice (0-100)",
        "unctad": False,
        "descricao": "Participação do setor portuário na economia local",
        "granularidade": "Município/Ano",
        "fonte_dados": "RAIS - microdados_vinculos",
    },
    "IND-7.05": {
        "codigo": "IND-7.05",
        "nome": "Ranking de Portos",
        "modulo": 7,
        "unidade": "Posição",
        "unctad": False,
        "descricao": "Ranking por eficiência operacional",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - v_carga_validada",
    },
    "IND-7.06": {
        "codigo": "IND-7.06",
        "nome": "Índice de Benchmark",
        "modulo": 7,
        "unidade": "Índice (0-200)",
        "unctad": False,
        "descricao": "Posição relativa ao top 10 (100 = média do top 10)",
        "granularidade": "Instalação/Ano",
        "fonte_dados": "ANTAQ - v_carga_validada",
    },
    "IND-7.07": {
        "codigo": "IND-7.07",
        "nome": "Índice de Variação Anual",
        "modulo": 7,
        "unidade": "%",
        "unctad": False,
        "descricao": "Média da variação percentual dos últimos anos",
        "granularidade": "Instalação",
        "fonte_dados": "ANTAQ - v_carga_validada",
    },
}


class GenericIndicatorService:
    """Serviço genérico para consulta de qualquer indicador."""

    def __init__(
        self,
        bq_client: Optional[BigQueryClient] = None,
        query_cache: Optional[IndicatorQueryCache] = None,
    ):
        """Inicializa o serviço."""
        self.bq_client = bq_client or get_bigquery_client()
        self._query_cache = query_cache if query_cache is not None else IndicatorQueryCache()

    async def execute_indicator(
        self,
        request: GenericIndicatorRequest,
        tenant_policy: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        audit_context: Optional[Dict[str, Any]] = None,
    ) -> GenericIndicatorResponse:
        """
        Executa a query de um indicador específico.

        Args:
            request: Parâmetros da consulta

        Returns:
            GenericIndicatorResponse com os dados do indicador
        """
        started_at = time.perf_counter()
        codigo = request.codigo_indicador.upper()

        if codigo not in INDICATORS_METADATA:
            raise ValueError(f"Indicador {codigo} não encontrado")

        meta = INDICATORS_METADATA[codigo]
        if codigo not in ALL_QUERIES:
            raise ValueError(
                f"Indicador {codigo} está em dívida técnica e ainda não possui query ativa"
            )

        # Obtém a função de query
        query_func = get_query(codigo)
        module_num = meta.get("modulo", 0)

        # Monta parâmetros da query
        raw_params = {}
        if request.id_instalacao:
            raw_params["id_instalacao"] = request.id_instalacao
        if request.id_municipio:
            raw_params["id_municipio"] = request.id_municipio
        if request.ano:
            raw_params["ano"] = request.ano
        if request.ano_inicio:
            raw_params["ano_inicio"] = request.ano_inicio
        if request.ano_fim:
            raw_params["ano_fim"] = request.ano_fim
        if request.mes:
            raw_params["mes"] = request.mes

        request_cache_key = self._build_request_cache_key(
            modulo=module_num,
            codigo=codigo,
            tenant_id=tenant_id,
            request=request,
            extra_params=raw_params,
        )

        # Controle E5: allowlist por municipio direto
        self._enforce_municipio_access(
            codigo=codigo,
            id_municipio=request.id_municipio,
            tenant_policy=tenant_policy,
        )

        can_use_cache = self._query_cache is not None and tenant_id is not None
        if can_use_cache:
            cached = await self._query_cache.get(request_cache_key)
            if cached is not None:
                if isinstance(cached, dict):
                    cached_data = cached.get("data", [])
                    cached_warnings_payload = cached.get("warnings", [])
                    if not isinstance(cached_data, list):
                        cached_data = []
                    if not isinstance(cached_warnings_payload, list):
                        cached_warnings_payload = []
                else:
                    cached_data = cached if isinstance(cached, list) else []
                    cached_warnings_payload = []

                cached_warnings: List[DataQualityWarning] = []
                for item in cached_warnings_payload:
                    if isinstance(item, DataQualityWarning):
                        cached_warnings.append(item)
                    elif isinstance(item, dict):
                        try:
                            cached_warnings.append(DataQualityWarning(**item))
                        except Exception:
                            continue

                if (
                    request.id_instalacao
                    and not request.id_municipio
                    and request.include_breakdown
                    and all(w.tipo != "area_influencia_agregada" for w in cached_warnings)
                ):
                    self._append_warning(
                        cached_warnings,
                        codigo,
                        "area_influencia_agregada",
                        "Resultado agregado por area de influência com breakdown municipal.",
                        campo="area_influencia",
                    )
                response = GenericIndicatorResponse(
                    codigo_indicador=meta["codigo"],
                    nome=meta["nome"],
                    unidade=meta["unidade"],
                    unctad=meta["unctad"],
                    modulo=meta["modulo"],
                    data=cached_data,
                    warnings=cached_warnings if cached_warnings else self._validate_module5_quality(codigo, cached_data),
                    cache_hit=True,
                )
                if audit_context is not None:
                    audit_context["bytes_processed"] = None
                    audit_context["cache_hit"] = True
                    audit_context["duration_ms"] = int((time.perf_counter() - started_at) * 1000)
                return response

        # Filtra apenas os parâmetros aceitos pela função de query
        sig = inspect.signature(query_func)
        params = {
            k: v for k, v in raw_params.items()
            if k in sig.parameters
        }

        # E4: area de influencia por instalacao para Modulo 5
        if (
            codigo.startswith("IND-5.")
            and request.id_instalacao
            and not request.id_municipio
            and "id_municipio" in sig.parameters
        ):
            area = self._resolve_area_influencia(
                id_instalacao=request.id_instalacao,
                tenant_policy=tenant_policy,
            )
            if area:
                allowed = set((tenant_policy or {}).get("allowed_municipios", []))
                if allowed:
                    blocked = [item["id_municipio"] for item in area if item["id_municipio"] not in allowed]
                    if blocked:
                        raise IndicatorAccessError(
                            f"Municipios da area de influencia nao autorizados para o tenant: {', '.join(blocked)}"
                        )
                if len(area) == 1:
                    params["id_municipio"] = area[0]["id_municipio"]
                else:
                    results, bytes_processed = await self._execute_area_influencia_module5(
                        codigo=codigo,
                        query_func=query_func,
                        request=request,
                        area=area,
                        tenant_policy=tenant_policy,
                    )
                    warnings = self._validate_module5_quality(codigo, results)
                    if request.include_breakdown:
                        self._append_warning(
                            warnings,
                            codigo,
                            "area_influencia_agregada",
                            "Resultado agregado por area de influencia com breakdown municipal.",
                            campo="area_influencia",
                        )
                    if can_use_cache:
                        await self._query_cache.set(
                            request_cache_key,
                            {
                                "data": results,
                                "warnings": [w.model_dump(mode="json") for w in warnings],
                            },
                        )
                    self._log_query_audit(
                        tenant_id=tenant_id,
                        user_id=user_id,
                        codigo=codigo,
                        request=request,
                        duration_ms=(time.perf_counter() - started_at) * 1000.0,
                        bytes_processed=None,
                    )
                    response = GenericIndicatorResponse(
                        codigo_indicador=meta["codigo"],
                        nome=meta["nome"],
                        unidade=meta["unidade"],
                        unctad=meta["unctad"],
                        modulo=meta["modulo"],
                        data=results,
                        warnings=warnings,
                        cache_hit=False,
                    )
                    if audit_context is not None:
                        audit_context["bytes_processed"] = bytes_processed
                        audit_context["cache_hit"] = False
                        audit_context["duration_ms"] = int((time.perf_counter() - started_at) * 1000)
                    return response

        # Caso especial legado: se for indicador municipal (3,4,5,6) e recebemos id_instalacao,
        # traduzimos para id_municipio via mapa fixo.
        if (
            module_num in [3, 4, 5, 6]
            and "id_municipio" in sig.parameters
            and not params.get("id_municipio")
            and "id_instalacao" in raw_params
        ):
            port_name = raw_params["id_instalacao"]
            if port_name in PORT_TO_IBGE_MAPPING:
                params["id_municipio"] = PORT_TO_IBGE_MAPPING[port_name]
            else:
                params["id_municipio"] = port_name

        # Executa a query regular
        query = query_func(**params)
        bytes_estimated = await self._estimate_query_bytes(query)
        self._enforce_bytes_quota(
            codigo=codigo,
            bytes_estimated=bytes_estimated,
            tenant_policy=tenant_policy,
        )
        results = await self.bq_client.execute_query(query)
        warnings = self._validate_module5_quality(codigo, results)
        if can_use_cache:
            await self._query_cache.set(
                request_cache_key,
                {
                    "data": results,
                    "warnings": [w.model_dump(mode="json") for w in warnings],
                },
            )
        if audit_context is not None:
            audit_context["bytes_processed"] = bytes_estimated
            audit_context["cache_hit"] = False
            audit_context["duration_ms"] = int((time.perf_counter() - started_at) * 1000)
        self._log_query_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            codigo=codigo,
            request=request,
            duration_ms=(time.perf_counter() - started_at) * 1000.0,
            bytes_processed=bytes_estimated,
        )

        return GenericIndicatorResponse(
            codigo_indicador=meta["codigo"],
            nome=meta["nome"],
            unidade=meta["unidade"],
            unctad=meta["unctad"],
            modulo=meta["modulo"],
            data=results,
            warnings=warnings,
            cache_hit=False,
        )

    @staticmethod
    def _resolve_area_influencia(
        id_instalacao: str,
        tenant_policy: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Resolve lista de municipios para uma instalacao (E4)."""
        policy = tenant_policy or {}
        area_map = policy.get("area_influencia") or {}
        mapped = area_map.get(id_instalacao)
        if isinstance(mapped, list) and mapped:
            cleaned = []
            for item in mapped:
                if not isinstance(item, dict):
                    continue
                id_municipio = str(item.get("id_municipio", "")).strip()
                if not id_municipio:
                    continue
                peso = GenericIndicatorService._to_float(item.get("peso"))
                cleaned.append(
                    {
                        "id_municipio": id_municipio,
                        "peso": peso if peso is not None and peso > 0 else 1.0,
                    }
                )
            if cleaned:
                return cleaned

        fallback_municipio = PORT_TO_IBGE_MAPPING.get(id_instalacao)
        if fallback_municipio:
            return [{"id_municipio": fallback_municipio, "peso": 1.0}]

        return []

    @staticmethod
    def _build_request_cache_key(
        modulo: int,
        codigo: str,
        tenant_id: Optional[str],
        request: GenericIndicatorRequest,
        extra_params: Dict[str, Any],
    ) -> str:
        """Constrói chave canônica para cache de consulta genérica."""
        payload = {
            "codigo_indicador": codigo.upper(),
            "modulo": modulo,
            "tenant_id": tenant_id or "public",
            "id_instalacao": request.id_instalacao,
            "id_municipio": request.id_municipio,
            "ano": request.ano,
            "ano_inicio": request.ano_inicio,
            "ano_fim": request.ano_fim,
            "mes": request.mes,
            "include_breakdown": request.include_breakdown,
            "extra_params": extra_params,
        }
        return IndicatorQueryCache.make_key(
            module=modulo,
            codigo=codigo.upper(),
            tenant_id=tenant_id,
            payload=payload,
        )

    @staticmethod
    def _enforce_municipio_access(
        codigo: str,
        id_municipio: Optional[str],
        tenant_policy: Optional[Dict[str, Any]],
    ) -> None:
        """Aplica allowlist por municipio quando configurada (E5)."""
        if not codigo.startswith("IND-5."):
            return
        if not id_municipio:
            return

        policy = tenant_policy or {}
        allowed = set(policy.get("allowed_municipios", []))
        if allowed and str(id_municipio) not in allowed:
            raise IndicatorAccessError(f"id_municipio {id_municipio} nao autorizado para o tenant")

    async def _estimate_query_bytes(self, query: str) -> Optional[int]:
        """Estimativa de bytes via dry run quando suportado pelo cliente."""
        dry_run_fn = getattr(self.bq_client, "get_dry_run_results", None)
        if dry_run_fn is None:
            return None
        try:
            stats = await dry_run_fn(query)
        except Exception:
            return None
        bytes_processed = stats.get("total_bytes_processed")
        try:
            return int(bytes_processed) if bytes_processed is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _enforce_bytes_quota(
        codigo: str,
        bytes_estimated: Optional[int],
        tenant_policy: Optional[Dict[str, Any]],
    ) -> None:
        """Enforce de limite de bytes por consulta (E5)."""
        if not codigo.startswith("IND-5."):
            return
        if bytes_estimated is None:
            return
        max_bytes = (tenant_policy or {}).get("max_bytes_per_query")
        if max_bytes is None:
            return
        try:
            max_bytes_int = int(max_bytes)
        except (TypeError, ValueError):
            return
        if max_bytes_int > 0 and bytes_estimated > max_bytes_int:
            raise IndicatorQuotaError(
                f"Consulta excede limite de bytes do tenant: estimado={bytes_estimated}, limite={max_bytes_int}"
            )

    @staticmethod
    def _log_query_audit(
        tenant_id: Optional[str],
        user_id: Optional[str],
        codigo: str,
        request: GenericIndicatorRequest,
        duration_ms: float,
        bytes_processed: Optional[int],
    ) -> None:
        """Log estruturado para auditoria de consultas (E5)."""
        logger.info(
            "indicator_query_audit",
            extra={
                "tenant_id": tenant_id,
                "user_id": user_id,
                "indicator_code": codigo,
                "filters": {
                    "id_instalacao": request.id_instalacao,
                    "id_municipio": request.id_municipio,
                    "ano": request.ano,
                    "ano_inicio": request.ano_inicio,
                    "ano_fim": request.ano_fim,
                },
                "duration_ms": round(duration_ms, 2),
                "bytes_processed": bytes_processed,
            },
        )

    async def _execute_area_influencia_module5(
        self,
        codigo: str,
        query_func: Any,
        request: GenericIndicatorRequest,
        area: List[Dict[str, Any]],
        tenant_policy: Optional[Dict[str, Any]],
    ) -> tuple[List[Dict[str, Any]], Optional[int]]:
        """
        Executa agregacao por area de influencia (E4) para indicadores do modulo 5.

        Estrategia:
        - roda query por municipio da area
        - agrega no backend por ano (ou linha unica para correlacionais)
        """
        signature = inspect.signature(query_func)
        all_rows: List[Dict[str, Any]] = []
        total_bytes_processed: Optional[int] = None
        breakdown_map: Dict[str, List[Dict[str, Any]]] = {}

        for item in area:
            id_municipio = item["id_municipio"]
            peso = self._to_float(item.get("peso")) or 1.0
            params = self._build_params_for_signature(signature, request, id_municipio=id_municipio)
            query = query_func(**params)
            bytes_estimated = await self._estimate_query_bytes(query)
            self._enforce_bytes_quota(codigo, bytes_estimated, tenant_policy)
            rows = await self.bq_client.execute_query(query)
            for row in rows:
                if not isinstance(row, dict):
                    continue
                row_copy = dict(row)
                row_copy["_peso_area"] = peso
                row_copy["_id_municipio_area"] = id_municipio
                all_rows.append(row_copy)
            if request.include_breakdown:
                breakdown_map[id_municipio] = rows
            if bytes_estimated is not None:
                if total_bytes_processed is None:
                    total_bytes_processed = 0
                total_bytes_processed += bytes_estimated

        return self._aggregate_area_rows(
            codigo=codigo,
            rows=all_rows,
            id_instalacao=request.id_instalacao,
            include_breakdown=request.include_breakdown,
            breakdown_map=breakdown_map,
        ), total_bytes_processed

    @staticmethod
    def _build_params_for_signature(
        signature: inspect.Signature,
        request: GenericIndicatorRequest,
        id_municipio: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Monta parametros aceitos por uma assinatura de query."""
        raw_params: Dict[str, Any] = {}
        if request.ano is not None:
            raw_params["ano"] = request.ano
        if request.ano_inicio is not None:
            raw_params["ano_inicio"] = request.ano_inicio
        if request.ano_fim is not None:
            raw_params["ano_fim"] = request.ano_fim
        if request.mes is not None:
            raw_params["mes"] = request.mes
        if id_municipio is not None:
            raw_params["id_municipio"] = id_municipio
        return {k: v for k, v in raw_params.items() if k in signature.parameters}

    @classmethod
    def _aggregate_area_rows(
        cls,
        codigo: str,
        rows: List[Dict[str, Any]],
        id_instalacao: Optional[str],
        include_breakdown: bool = False,
        breakdown_map: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> List[Dict[str, Any]]:
        """Agrega resultados por area de influencia por ano ou em linha unica."""
        if not rows:
            return []

        value_field = MODULE5_VALUE_FIELD_BY_CODE.get(codigo)
        if not value_field:
            return []

        strategy = "sum" if codigo in MODULE5_SUM_CODES else "weighted_avg"
        has_year = any(isinstance(row, dict) and row.get("ano") is not None for row in rows)
        grouped: Dict[Any, List[Dict[str, Any]]] = {}

        for row in rows:
            key = row.get("ano") if has_year else "single"
            grouped.setdefault(key, []).append(row)

        aggregated_rows: List[Dict[str, Any]] = []
        for group_key, group_rows in sorted(grouped.items(), key=lambda x: x[0], reverse=True):
            value_weighted_sum = 0.0
            weight_sum = 0.0
            values_sum = 0.0
            n_values = 0

            for row in group_rows:
                value = cls._to_float(row.get(value_field))
                if value is None:
                    continue
                weight = cls._to_float(row.get("_peso_area")) or 1.0
                values_sum += value
                value_weighted_sum += value * weight
                weight_sum += weight
                n_values += 1

            if n_values == 0:
                continue

            if strategy == "sum":
                agg_value = values_sum
            else:
                agg_value = value_weighted_sum / weight_sum if weight_sum > 0 else None

            if agg_value is None:
                continue

            row_out: Dict[str, Any] = {
                "id_instalacao": id_instalacao,
                value_field: round(agg_value, 4),
                "municipios_agregados": len({str(r.get("_id_municipio_area")) for r in group_rows}),
            }
            if has_year and group_key != "single":
                row_out["ano"] = group_key

            if codigo in {"IND-5.14", "IND-5.15", "IND-5.16", "IND-5.17"}:
                n_obs = 0
                for row in group_rows:
                    n_current = cls._to_float(row.get("n_observacoes"))
                    if n_current is not None:
                        n_obs += int(n_current)
                row_out["n_observacoes"] = n_obs

            if include_breakdown and breakdown_map:
                breakdown = []
                for id_municipio, municipio_rows in breakdown_map.items():
                    selected = None
                    for candidate in municipio_rows:
                        if not isinstance(candidate, dict):
                            continue
                        if has_year and group_key != "single" and candidate.get("ano") != group_key:
                            continue
                        if cls._to_float(candidate.get(value_field)) is not None:
                            selected = candidate
                            break
                    if selected is None:
                        continue
                    breakdown.append(
                        {
                            "id_municipio": id_municipio,
                            "ano": selected.get("ano"),
                            value_field: selected.get(value_field),
                            "peso": next(
                                (
                                    row.get("_peso_area")
                                    for row in group_rows
                                    if str(row.get("_id_municipio_area")) == id_municipio
                                ),
                                1.0,
                            ),
                        }
                    )
                row_out["breakdown"] = breakdown[:10]

            aggregated_rows.append(row_out)

        return aggregated_rows[:20]

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        """Converte valores do BigQuery para float com segurança."""
        if value is None:
            return None
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, Decimal):
            return float(value)
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _append_warning(
        warnings: List[DataQualityWarning],
        codigo: str,
        tipo: str,
        mensagem: str,
        campo: Optional[str] = None,
        row: Optional[dict] = None,
        valor: Optional[float] = None,
    ) -> None:
        """Adiciona alerta padronizado de qualidade."""
        row_id = row.get("id_municipio") if isinstance(row, dict) else None
        row_ano = row.get("ano") if isinstance(row, dict) else None
        warnings.append(
            DataQualityWarning(
                tipo=tipo,
                codigo_indicador=codigo,
                campo=campo,
                id_municipio=str(row_id) if row_id is not None else None,
                ano=int(row_ano) if row_ano is not None else None,
                valor=valor,
                mensagem=mensagem,
            )
        )

    @classmethod
    def _validate_module5_quality(
        cls,
        codigo: str,
        results: List[Dict[str, Any]],
    ) -> List[DataQualityWarning]:
        """Executa verificações mínimas de qualidade para o Módulo 5."""
        if not codigo.startswith("IND-5."):
            return []
        if not results:
            return []

        warnings: List[DataQualityWarning] = []
        percentage_fields_by_code = {
            "IND-5.04": {"pib_servicos_percentual"},
            "IND-5.05": {"pib_industria_percentual"},
            "IND-5.08": {"concentracao_emprego_pct"},
            "IND-5.09": {"concentracao_salarial_pct"},
            "IND-5.18": {"participacao_pib_regional_pct"},
            "IND-5.21": {"indice_concentracao_portuaria"},
        }
        non_negative_fields_by_code = {
            "IND-5.01": {"pib_municipal", "pib"},
            "IND-5.02": {"pib_per_capita"},
            "IND-5.03": {"populacao"},
            "IND-5.06": {"intensidade_portuaria"},
            "IND-5.07": {"intensidade_comercial"},
            "IND-5.20": {"empregos_portuarios", "empregos_totais", "razao_emprego_total_portuario"},
            "IND-5.21": {"indice_concentracao_portuaria"},
        }

        correlation_fields = {"IND-5.14", "IND-5.15", "IND-5.16"}
        correlation_aliases = (
            "correlacao",
            "correlacao_tonelagem_pib",
            "correlacao_tonelagem_empregos",
            "correlacao_comercio_pib",
        )

        for row in results:
            if not isinstance(row, dict):
                continue

            for field in percentage_fields_by_code.get(codigo, set()):
                value = cls._to_float(row.get(field))
                if value is None:
                    continue
                if not (0.0 <= value <= 100.0):
                    cls._append_warning(
                        warnings,
                        codigo,
                        "percentual_fora_intervalo",
                        f"{field} fora do intervalo 0-100",
                        campo=field,
                        valor=value,
                        row=row,
                    )

            for field in non_negative_fields_by_code.get(codigo, set()):
                value = cls._to_float(row.get(field))
                if value is None:
                    continue
                if value < 0:
                    cls._append_warning(
                        warnings,
                        codigo,
                        "valor_negativo",
                        f"{field} com valor negativo",
                        campo=field,
                        valor=value,
                        row=row,
                    )

            if codigo in correlation_fields:
                for field in correlation_aliases:
                    value = cls._to_float(row.get(field))
                    if value is None:
                        continue
                    if math.isinf(value) or math.isnan(value) or value < -1.0 or value > 1.0:
                        cls._append_warning(
                            warnings,
                            codigo,
                            "correlacao_fora_intervalo",
                            f"{field} fora do intervalo [-1,1]",
                            campo=field,
                            valor=value,
                            row=row,
                        )

            if codigo == "IND-5.17":
                for field in ("elasticidade", "elasticidade_tonelagem_pib"):
                    value = cls._to_float(row.get(field))
                    if value is None:
                        continue
                    if math.isinf(value) or math.isnan(value):
                        cls._append_warning(
                            warnings,
                            codigo,
                            "elasticidade_invalida",
                            f"{field} inválida (NaN/Inf)",
                            campo=field,
                            valor=value,
                            row=row,
                        )

        return warnings

    def get_all_metadata(self) -> AllIndicatorsResponse:
        """Retorna metadados de todos os indicadores."""
        technical_debt_indicators = set()
        indicadores = []

        for codigo, meta in INDICATORS_METADATA.items():
            meta_with_status = dict(meta)
            if codigo in ALL_QUERIES:
                meta_with_status["implementation_status"] = "implemented"
            else:
                meta_with_status["implementation_status"] = "technical_debt"
                technical_debt_indicators.add(codigo)

            indicadores.append(IndicatorMetadata(**meta_with_status))

        orphans = set(ALL_QUERIES) - set(INDICATORS_METADATA)
        technical_debt_indicators.update(orphans)

        unctad_count = sum(
            1 for item in indicadores
            if item.implementation_status == "implemented" and item.unctad
        )

        return AllIndicatorsResponse(
            total_indicadores=len(indicadores),
            unctad_compliant=unctad_count,
            technical_debt_indicators=sorted(technical_debt_indicators),
            indicadores=indicadores,
        )

    def get_indicator_metadata(self, codigo: str) -> IndicatorMetadata:
        """Retorna metadados de um indicador específico."""
        codigo = codigo.upper()
        if codigo not in INDICATORS_METADATA:
            raise ValueError(f"Indicador {codigo} não encontrado")

        meta = dict(INDICATORS_METADATA[codigo])
        meta["implementation_status"] = (
            "implemented" if codigo in ALL_QUERIES else "technical_debt"
        )
        return IndicatorMetadata(**meta)


# Singleton do serviço
_service_instance: Optional[GenericIndicatorService] = None


def get_generic_indicator_service() -> GenericIndicatorService:
    """Retorna instância singleton do serviço genérico."""
    global _service_instance
    if _service_instance is None:
        _service_instance = GenericIndicatorService()
    return _service_instance
