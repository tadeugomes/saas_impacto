"""
Serviço Genérico de Indicadores.

Este serviço fornece uma interface unificada para consultar
qualquer indicador de qualquer módulo (1-7).
"""

from typing import List, Dict, Any, Optional
import logging

from app.db.bigquery.client import BigQueryClient, get_bigquery_client
from app.db.bigquery.queries import ALL_QUERIES, get_query
from app.schemas.indicators import (
    GenericIndicatorRequest,
    GenericIndicatorResponse,
    IndicatorMetadata,
    AllIndicatorsResponse,
)


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
        "descricao": "Produto Interno Bruto municipal",
        "granularidade": "Município/Ano",
        "fonte_dados": "IBGE - PIB municipal",
    },
    "IND-5.02": {
        "codigo": "IND-5.02",
        "nome": "PIB per Capita",
        "modulo": 5,
        "unidade": "R$/habitante",
        "unctad": False,
        "descricao": "PIB dividido pela população",
        "granularidade": "Município/Ano",
        "fonte_dados": "IBGE - PIB + População",
    },
    "IND-5.03": {
        "codigo": "IND-5.03",
        "nome": "População Municipal",
        "modulo": 5,
        "unidade": "Habitantes",
        "unctad": False,
        "descricao": "População residente no município",
        "granularidade": "Município/Ano",
        "fonte_dados": "IBGE - População municipal",
    },
    "IND-5.04": {
        "codigo": "IND-5.04",
        "nome": "PIB Setorial - Serviços",
        "modulo": 5,
        "unidade": "%",
        "unctad": False,
        "descricao": "Participação do setor serviços no PIB",
        "granularidade": "Município/Ano",
        "fonte_dados": "IBGE - PIB municipal",
    },
    "IND-5.05": {
        "codigo": "IND-5.05",
        "nome": "PIB Setorial - Indústria",
        "modulo": 5,
        "unidade": "%",
        "unctad": False,
        "descricao": "Participação do setor indústria no PIB",
        "granularidade": "Município/Ano",
        "fonte_dados": "IBGE - PIB municipal",
    },
    "IND-5.06": {
        "codigo": "IND-5.06",
        "nome": "Intensidade Portuária",
        "modulo": 5,
        "unidade": "Toneladas/R$",
        "unctad": False,
        "descricao": "Tonelagem movimentada por unidade de PIB",
        "granularidade": "Município/Ano",
        "fonte_dados": "ANTAQ + IBGE PIB",
    },
    "IND-5.07": {
        "codigo": "IND-5.07",
        "nome": "Intensidade Comercial",
        "modulo": 5,
        "unidade": "US$/R$",
        "unctad": False,
        "descricao": "Comércio exterior por unidade de PIB",
        "granularidade": "Município/Ano",
        "fonte_dados": "Comex Stat + IBGE PIB",
    },
    "IND-5.08": {
        "codigo": "IND-5.08",
        "nome": "Concentração de Emprego Portuário",
        "modulo": 5,
        "unidade": "%",
        "unctad": False,
        "descricao": "Participação do setor portuário no emprego",
        "granularidade": "Município/Ano",
        "fonte_dados": "RAIS - microdados_vinculos",
    },
    "IND-5.09": {
        "codigo": "IND-5.09",
        "nome": "Concentração Salarial Portuária",
        "modulo": 5,
        "unidade": "%",
        "unctad": False,
        "descricao": "Participação da massa salarial portuária",
        "granularidade": "Município/Ano",
        "fonte_dados": "RAIS - microdados_vinculos",
    },
    "IND-5.10": {
        "codigo": "IND-5.10",
        "nome": "Crescimento PIB Municipal",
        "modulo": 5,
        "unidade": "%",
        "unctad": False,
        "descricao": "Variação percentual anual do PIB",
        "granularidade": "Município/Ano",
        "fonte_dados": "IBGE - PIB municipal",
    },
    "IND-5.11": {
        "codigo": "IND-5.11",
        "nome": "Crescimento de Tonelagem",
        "modulo": 5,
        "unidade": "%",
        "unctad": False,
        "descricao": "Variação percentual anual da tonelagem",
        "granularidade": "Município/Ano",
        "fonte_dados": "ANTAQ - v_carga_validada",
    },
    "IND-5.14": {
        "codigo": "IND-5.14",
        "nome": "Correlação Tonelagem × PIB",
        "modulo": 5,
        "unidade": "Coeficiente",
        "unctad": False,
        "descricao": "Coeficiente de correlação (mínimo 5 anos)",
        "granularidade": "Município",
        "fonte_dados": "ANTAQ + IBGE PIB",
    },
    "IND-5.18": {
        "codigo": "IND-5.18",
        "nome": "Participação no PIB Regional",
        "modulo": 5,
        "unidade": "%",
        "unctad": False,
        "descricao": "Participação do município no PIB da microrregião",
        "granularidade": "Município/Ano",
        "fonte_dados": "IBGE - PIB municipal",
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

    def __init__(self, bq_client: Optional[BigQueryClient] = None):
        """Inicializa o serviço."""
        self.bq_client = bq_client or get_bigquery_client()

    async def execute_indicator(
        self,
        request: GenericIndicatorRequest,
    ) -> GenericIndicatorResponse:
        """
        Executa a query de um indicador específico.

        Args:
            request: Parâmetros da consulta

        Returns:
            GenericIndicatorResponse com os dados do indicador
        """
        codigo = request.codigo_indicador.upper()

        if codigo not in INDICATORS_METADATA:
            raise ValueError(f"Indicador {codigo} não encontrado")

        meta = INDICATORS_METADATA[codigo]

        # Obtém a função de query
        query_func = get_query(codigo)

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

        # Filtra apenas os parâmetros aceitos pela função de query
        import inspect
        sig = inspect.signature(query_func)
        params = {
            k: v for k, v in raw_params.items()
            if k in sig.parameters
        }

        # Caso especial: se for um indicador municipal (Módulos 3, 4, 5, 6) e recebemos id_instalacao (Porto),
        # traduzimos para o id_municipio (IBGE) correspondente usando o mapping.
        # Módulos 1 e 2 são por porto/instalação e NÃO devem ter essa tradução.
        module_num = meta.get("modulo", 0)
        if (module_num in [3, 4, 5, 6] and
            "id_municipio" in sig.parameters and
            not params.get("id_municipio") and
            "id_instalacao" in raw_params):
            port_name = raw_params["id_instalacao"]
            if port_name in PORT_TO_IBGE_MAPPING:
                params["id_municipio"] = PORT_TO_IBGE_MAPPING[port_name]
            else:
                # Fallback p/ o comportamento anterior se não houver no mapping
                params["id_municipio"] = port_name

        # Executa a query
        query = query_func(**params)
        results = await self.bq_client.execute_query(query)

        return GenericIndicatorResponse(
            codigo_indicador=meta["codigo"],
            nome=meta["nome"],
            unidade=meta["unidade"],
            unctad=meta["unctad"],
            modulo=meta["modulo"],
            data=results,
        )

    def get_all_metadata(self) -> AllIndicatorsResponse:
        """Retorna metadados de todos os indicadores."""
        indicadores = [
            IndicatorMetadata(**v)
            for v in INDICATORS_METADATA.values()
        ]

        unctad_count = sum(1 for v in INDICATORS_METADATA.values() if v["unctad"])

        return AllIndicatorsResponse(
            total_indicadores=len(indicadores),
            unctad_compliant=unctad_count,
            indicadores=indicadores,
        )

    def get_indicator_metadata(self, codigo: str) -> IndicatorMetadata:
        """Retorna metadados de um indicador específico."""
        codigo = codigo.upper()
        if codigo not in INDICATORS_METADATA:
            raise ValueError(f"Indicador {codigo} não encontrado")
        return IndicatorMetadata(**INDICATORS_METADATA[codigo])


# Singleton do serviço
_service_instance: Optional[GenericIndicatorService] = None


def get_generic_indicator_service() -> GenericIndicatorService:
    """Retorna instância singleton do serviço genérico."""
    global _service_instance
    if _service_instance is None:
        _service_instance = GenericIndicatorService()
    return _service_instance
