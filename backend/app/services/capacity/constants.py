"""
Constantes para o módulo de capacidade portuária.

Referências:
- roteiro_capacidades_portuarias_v12.md (LabPortos/UFMA)
- BD_Modelo_Memoria_Calculo.xlsx, aba Parametros
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Horas
# ---------------------------------------------------------------------------
H_CAL: int = 8_760
"""Horas calendário por ano (365 × 24)."""

DEFAULT_H_EF: float = 8_000.0
"""Horas efetivas/ano padrão.  H_ef = H_cal − H_cli − H_mnt − H_nav − H_out.
O analista deve calibrar por terminal; 8 000 h é a referência genérica."""

DEFAULT_CLEARANCE_H: float = 3.0
"""Intervalo entre atracações consecutivas (parâmetro 'a' na Eq. 1b).
Faixa ANTAQ: 3.0–3.5 h  (Quadro 6)."""

# ---------------------------------------------------------------------------
# Contêineres
# ---------------------------------------------------------------------------
DEFAULT_FATOR_TEU: float = 1.55
"""Fator de conversão TEU/contêiner (Quadro 8). Faixa: 1.40–1.65."""

# ---------------------------------------------------------------------------
# Perfis de carga canônicos (usados como chave no mapa BOR_adm)
# ---------------------------------------------------------------------------
PERFIL_GRANEL_SOLIDO = "GRANEL_SOLIDO"
PERFIL_GRANEL_LIQUIDO = "GRANEL_LIQUIDO"
PERFIL_CARGA_GERAL = "CARGA_GERAL"
PERFIL_CONTEINER = "CONTEINER"
PERFIL_RORO = "RORO"

# Mapeamento de strings ANTAQ para perfis canônicos
ANTAQ_PERFIL_MAP: dict[str, str] = {
    # Granel sólido
    "Granel Sólido": PERFIL_GRANEL_SOLIDO,
    "GRANEL SÓLIDO": PERFIL_GRANEL_SOLIDO,
    "Granel Solido": PERFIL_GRANEL_SOLIDO,
    "GRANEL SOLIDO": PERFIL_GRANEL_SOLIDO,
    "granel sólido": PERFIL_GRANEL_SOLIDO,
    "granel solido": PERFIL_GRANEL_SOLIDO,
    # Granel líquido / gasoso
    "Granel Líquido e Gasoso": PERFIL_GRANEL_LIQUIDO,
    "Granel Líquido": PERFIL_GRANEL_LIQUIDO,
    "GRANEL LÍQUIDO": PERFIL_GRANEL_LIQUIDO,
    "GRANEL LIQUIDO": PERFIL_GRANEL_LIQUIDO,
    "Granel Liquido": PERFIL_GRANEL_LIQUIDO,
    "granel líquido": PERFIL_GRANEL_LIQUIDO,
    "granel liquido": PERFIL_GRANEL_LIQUIDO,
    # Carga geral
    "Carga Geral": PERFIL_CARGA_GERAL,
    "CARGA GERAL": PERFIL_CARGA_GERAL,
    "carga geral": PERFIL_CARGA_GERAL,
    # Contêiner
    "Carga Conteinerizada": PERFIL_CONTEINER,
    "CARGA CONTEINERIZADA": PERFIL_CONTEINER,
    "Conteinerizada": PERFIL_CONTEINER,
    "Contêiner": PERFIL_CONTEINER,
    "CONTÊINER": PERFIL_CONTEINER,
    "Container": PERFIL_CONTEINER,
    "CONTAINER": PERFIL_CONTEINER,
    # Ro-Ro / Veículos
    "Ro-Ro": PERFIL_RORO,
    "RO-RO": PERFIL_RORO,
    "Veículos": PERFIL_RORO,
    "VEÍCULOS": PERFIL_RORO,
}


def normalizar_perfil(perfil_antaq: str) -> str:
    """Normaliza string de perfil ANTAQ para chave canônica.

    Se não encontrar no mapa, retorna a string original em UPPER.
    """
    return ANTAQ_PERFIL_MAP.get(perfil_antaq, perfil_antaq.upper())
