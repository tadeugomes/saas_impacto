"""
Templates e configurações para relatórios de cada módulo.

Define estrutura, indicadores e formatação para geração de DOCX.
"""

from typing import Any, Dict, List, Optional


# Configurações dos módulos
MODULE_TEMPLATES: Dict[str, Dict] = {
    "IND-1": {
        "name": "Módulo 1 - Operações de Navios",
        "description": "Indicadores de operações de navios seguindo padrão UNCTAD",
        "indicators": [
            {"code": "IND-1.01", "name": "Tempo Médio de Espera", "unit": "Horas", "description": "Tempo entre chegada e atracação"},
            {"code": "IND-1.02", "name": "Tempo Médio em Porto", "unit": "Horas", "description": "Tempo total no porto"},
            {"code": "IND-1.03", "name": "Tempo Bruto de Atracação", "unit": "Horas", "description": "Tempo de atracação até desatracação"},
            {"code": "IND-1.04", "name": "Tempo Líquido de Operação", "unit": "Horas", "description": "Tempo efetivo de operação"},
            {"code": "IND-1.05", "name": "Taxa de Ocupação de Berços", "unit": "%", "description": "Ocupação média dos berços"},
            {"code": "IND-1.06", "name": "Tempo Ocioso Médio", "unit": "Horas", "description": "Tempo de paralisação"},
            {"code": "IND-1.07", "name": "Arqueação Bruta Média", "unit": "GT", "description": "Tamanho médio dos navios"},
            {"code": "IND-1.08", "name": "Comprimento Médio", "unit": "Metros", "description": "Comprimento médio dos navios"},
            {"code": "IND-1.09", "name": "Calado Máximo", "unit": "Metros", "description": "Maior calado operacional"},
            {"code": "IND-1.10", "name": "Distribuição por Tipo", "unit": "%", "description": "Por tipo de navegação"},
            {"code": "IND-1.11", "name": "Número de Atracações", "unit": "Contagem", "description": "Total de atracações"},
            {"code": "IND-1.12", "name": "Índice de Paralisação", "unit": "%", "description": "Tempo ocioso / tempo atracado"},
        ],
        "table_headers": ["Indicador", "Descrição", "Unidade", "Valor"],
    },
    "IND-2": {
        "name": "Módulo 2 - Operações de Carga",
        "description": "Indicadores de operações de carga seguindo padrão UNCTAD",
        "indicators": [
            {"code": "IND-2.01", "name": "Carga Total Movimentada", "unit": "Toneladas", "description": "Soma de carga embarcada e desembarcada"},
            {"code": "IND-2.05", "name": "Carga Média por Atracação", "unit": "Toneladas", "description": "Carga média por atracação"},
            {"code": "IND-2.06", "name": "Produtividade de Berço", "unit": "Ton/hora", "description": "Toneladas por hora de operação"},
            {"code": "IND-2.10", "name": "Tonelagem Total (Ranking)", "unit": "Toneladas", "description": "Ranking por tonelagem"},
            {"code": "IND-2.11", "name": "Concentração de Carga", "unit": "Toneladas", "description": "Índice de concentração"},
            {"code": "IND-2.12", "name": "Mix de Carga", "unit": "%", "description": "Distribuição por tipo de carga"},
            {"code": "IND-2.13", "name": "Sazonalidade", "unit": "Índice", "description": "Variação mensal da carga"},
        ],
        "table_headers": ["Indicador", "Descrição", "Unidade", "Valor"],
    },
    "IND-3": {
        "name": "Módulo 3 - Recursos Humanos",
        "description": "Indicadores de recursos humanos seguindo padrão UNCTAD",
        "indicators": [
            {"code": "IND-3.01", "name": "Empregos Portuários", "unit": "Empregos", "description": "Total de empregos no setor portuário (RAIS)"},
            {"code": "IND-3.02", "name": "Paridade de Gênero", "unit": "%", "description": "Percentual de mulheres no setor portuário"},
            {"code": "IND-3.03", "name": "Paridade por Categoria", "unit": "%", "description": "Paridade por categoria profissional"},
            {"code": "IND-3.04", "name": "Taxa Emprego Temporário", "unit": "%", "description": "Percentual de contratos temporários"},
            {"code": "IND-3.05", "name": "Salário Médio", "unit": "R$", "description": "Remuneração média mensal"},
            {"code": "IND-3.06", "name": "Massa Salarial", "unit": "R$", "description": "Massa salarial anual estimada"},
            {"code": "IND-3.07", "name": "Produtividade", "unit": "ton/emp", "description": "Toneladas por empregado"},
            {"code": "IND-3.08", "name": "Receita por Empregado", "unit": "R$/emp", "description": "PIB por empregado portuário"},
            {"code": "IND-3.09", "name": "Distribuição Escolaridade", "unit": "%", "description": "Distribuição por nível de escolaridade"},
            {"code": "IND-3.10", "name": "Idade Média", "unit": "Anos", "description": "Idade média dos trabalhadores"},
            {"code": "IND-3.11", "name": "Variação Anual Empregos", "unit": "%", "description": "Variação anual de empregos"},
            {"code": "IND-3.12", "name": "Participação Emprego Local", "unit": "%", "description": "Participação no emprego total do município"},
        ],
        "table_headers": ["Indicador", "Descrição", "Unidade", "Valor"],
    },
    "IND-4": {
        "name": "Módulo 4 - Comércio Exterior",
        "description": "Indicadores de comércio exterior seguindo padrão UNCTAD",
        "indicators": [
            {"code": "IND-4.01", "name": "Valor FOB Exportações", "unit": "US$", "description": "Valor total das exportações"},
            {"code": "IND-4.02", "name": "Valor FOB Importações", "unit": "US$", "description": "Valor total das importações"},
            {"code": "IND-4.03", "name": "Balança Comercial", "unit": "US$", "description": "Saldo comercial (Exp - Imp)"},
            {"code": "IND-4.04", "name": "Peso Líquido Exportações", "unit": "kg", "description": "Peso líquido das exportações"},
            {"code": "IND-4.05", "name": "Peso Líquido Importações", "unit": "kg", "description": "Peso líquido das importações"},
            {"code": "IND-4.06", "name": "Valor Médio por kg", "unit": "US$/kg", "description": "Valor médio por kg exportado"},
            {"code": "IND-4.07", "name": "Concentração por País", "unit": "%", "description": "Concentração por país de destino"},
            {"code": "IND-4.08", "name": "Concentração por NCM", "unit": "%", "description": "Concentração por produto (NCM)"},
            {"code": "IND-4.09", "name": "Variação Anual", "unit": "%", "description": "Variação anual do comércio exterior"},
            {"code": "IND-4.10", "name": "Market Share", "unit": "%", "description": "Participação no mercado nacional"},
        ],
        "table_headers": ["Indicador", "Descrição", "Unidade", "Valor"],
    },
    "IND-5": {
        "name": "Módulo 5 - Impacto Econômico Regional",
        "description": "Indicadores de impacto econômico regional",
        "indicators": [
            {"code": "IND-5.01", "name": "PIB Municipal", "unit": "R$", "description": "PIB Total do Município"},
            {"code": "IND-5.02", "name": "PIB per Capita", "unit": "R$/hab", "description": "PIB per capita do município"},
            {"code": "IND-5.03", "name": "População Municipal", "unit": "Habitantes", "description": "População municipal estimada"},
            {"code": "IND-5.04", "name": "PIB Setorial - Serviços", "unit": "%", "description": "Participação do setor de serviços"},
            {"code": "IND-5.05", "name": "PIB Setorial - Indústria", "unit": "%", "description": "Participação do setor industrial"},
            {"code": "IND-5.06", "name": "Intensidade Portuária", "unit": "ton/R$", "description": "Razão Tonelada/PIB"},
            {"code": "IND-5.07", "name": "Intensidade Comercial", "unit": "US$/R$", "description": "Razão Comércio/PIB"},
            {"code": "IND-5.08", "name": "Concentração Emprego Portuário", "unit": "%", "description": "Participação do emprego portuário"},
            {"code": "IND-5.09", "name": "Concentração Salarial Portuária", "unit": "%", "description": "Participação da massa salarial"},
            {"code": "IND-5.10", "name": "Crescimento PIB", "unit": "%", "description": "Crescimento do PIB municipal"},
            {"code": "IND-5.11", "name": "Crescimento Tonelagem", "unit": "%", "description": "Variação anual da tonelagem"},
            {"code": "IND-5.12", "name": "Crescimento Empregos", "unit": "%", "description": "Variação anual de empregos"},
            {"code": "IND-5.13", "name": "Crescimento Comércio Exterior", "unit": "%", "description": "Variação do comércio exterior"},
            {"code": "IND-5.14", "name": "Correlação Tonelagem × PIB", "unit": "Coef", "description": "Correlação entre tonelagem e PIB"},
            {"code": "IND-5.15", "name": "Correlação Tonelagem × Empregos", "unit": "Coef", "description": "Correlação entre tonelagem e empregos"},
            {"code": "IND-5.16", "name": "Correlação Comércio × PIB", "unit": "Coef", "description": "Correlação entre comércio e PIB"},
            {"code": "IND-5.17", "name": "Elasticidade Tonelagem/PIB", "unit": "Elast", "description": "Elasticidade da tonelagem em relação ao PIB"},
            {"code": "IND-5.18", "name": "Participação PIB Regional", "unit": "%", "description": "Participação no PIB da microrregião"},
            {"code": "IND-5.19", "name": "Crescimento Relativo UF", "unit": "pp", "description": "Crescimento relativo ao estado"},
            {"code": "IND-5.20", "name": "Razão Emprego Total/Portuário", "unit": "Razão", "description": "Empregos totais por portuário"},
            {"code": "IND-5.21", "name": "Índice Concentração Portuária", "unit": "0-100", "description": "Índice composto de concentração"},
        ],
        "table_headers": ["Indicador", "Descrição", "Unidade", "Valor"],
    },
    "IND-6": {
        "name": "Módulo 6 - Finanças Públicas",
        "description": "6 indicadores de finanças públicas seguindo padrão UNCTAD",
        "indicators": [
            {"code": "IND-6.01", "name": "Arrecadação de ICMS", "unit": "R$", "description": "Total arrecadado de ICMS no município"},
            {"code": "IND-6.02", "name": "Arrecadação de ISS", "unit": "R$", "description": "Total arrecadado de ISS no município"},
            {"code": "IND-6.03", "name": "Receita Total Municipal", "unit": "R$", "description": "Receita total municipal (FINBRA)"},
            {"code": "IND-6.04", "name": "Receita per Capita", "unit": "R$/hab", "description": "Receita municipal por habitante"},
            {"code": "IND-6.05", "name": "Crescimento da Receita", "unit": "%", "description": "Variação anual da receita"},
            {"code": "IND-6.06", "name": "ICMS por Tonelada", "unit": "R$/ton", "description": "ICMS arrecadado por tonelada movimentada"},
        ],
        "table_headers": ["Indicador", "Descrição", "Unidade", "Valor"],
    },
    "IND-7": {
        "name": "Módulo 7 - Índices Sintéticos",
        "description": "Indicadores de índices sintéticos seguindo padrão UNCTAD",
        "indicators": [
            {"code": "IND-7.01", "name": "Índice de Eficiência Portuária", "unit": "0-100", "description": "Índice composto de eficiência"},
            {"code": "IND-7.02", "name": "Índice de Relevância", "unit": "0-100", "description": "Índice composto de relevância"},
            {"code": "IND-7.03", "name": "Índice de Integração", "unit": "0-100", "description": "Índice composto de integração"},
            {"code": "IND-7.04", "name": "Índice de Concentração", "unit": "0-100", "description": "Índice de concentração"},
            {"code": "IND-7.05", "name": "Índice de Sustentabilidade", "unit": "0-100", "description": "Índice composto de sustentabilidade"},
            {"code": "IND-7.06", "name": "Índice de Inovação", "unit": "0-100", "description": "Índice composto de inovação"},
            {"code": "IND-7.07", "name": "Índice de Desempenho Consolidado", "unit": "0-100", "description": "Índice geral consolidado"},
        ],
        "table_headers": ["Indicador", "Descrição", "Unidade", "Valor"],
    },
}


def get_module_template(module_code: str) -> Optional[Dict]:
    """Retorna o template de um módulo."""
    # Extrai o prefixo do módulo (IND-1, IND-2, etc.)
    for key in MODULE_TEMPLATES:
        if module_code.startswith(key.replace('IND-', '')):
            return MODULE_TEMPLATES[key]
    # Tenta match exato
    return MODULE_TEMPLATES.get(module_code)


def get_indicator_info(module_code: str, indicator_code: str) -> Optional[Dict]:
    """Retorna informações de um indicador específico."""
    template = get_module_template(module_code)
    if template:
        for ind in template.get("indicators", []):
            if ind["code"] == indicator_code:
                return ind
    return None


def format_value(value: Any, unit: str = "") -> str:
    """Formata um valor para exibição no relatório."""
    if value is None or value == "":
        return "N/A"

    # Formatação especial para diferentes unidades
    if unit in ["R$", "US$", "R$/hab", "US$/kg", "R$/ton", "R$/emp"]:
        try:
            num = float(value)
            if abs(num) >= 1_000_000:
                return f"{num/1_000_000:.2f} mi {unit}"
            elif abs(num) >= 1_000:
                return f"{num/1_000:.2f} mil {unit}"
            return f"{num:.2f} {unit}"
        except (ValueError, TypeError):
            return str(value)

    if unit == "%":
        try:
            return f"{float(value):.2f}%"
        except (ValueError, TypeError):
            return str(value)

    if unit == "Habitantes" or unit == "Hab" or unit == "Empregos" or unit == "Contagem" or unit == "Toneladas":
        try:
            return f"{int(value):,} {unit}".replace(",", ".")
        except (ValueError, TypeError):
            return str(value)

    if unit in ["Horas", "Metros", "GT", "ton/hora", "kg", "Anos", "ton/R$", "US$/R$"]:
        try:
            return f"{float(value):.2f} {unit}"
        except (ValueError, TypeError):
            return str(value)

    return str(value)
