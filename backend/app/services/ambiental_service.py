"""
Serviço de indicadores ambientais (Módulo 9).

Combina dados de ANA (risco hídrico) e INPE (focos de incêndio)
para criar o Índice de Risco Ambiental Composto.

Todo índice composto retorna um bloco `composicao` com fórmula, pesos,
fontes, períodos e última atualização — garantindo transparência ao usuário.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.clients.ana import AnaClient, get_ana_client
from app.clients.inpe import InpeClient, get_inpe_client

logger = logging.getLogger(__name__)


class AmbientalService:
    """Serviço de indicadores ambientais e índice composto."""

    def __init__(
        self,
        ana: Optional[AnaClient] = None,
        inpe: Optional[InpeClient] = None,
    ):
        self.ana = ana or get_ana_client()
        self.inpe = inpe or get_inpe_client()

    async def indice_risco_ambiental(
        self,
        id_instalacao: str,
        calado_minimo: float = 12.0,
        raio_incendio_km: int = 50,
        dias_incendio: int = 7,
    ) -> Dict[str, Any]:
        """
        IND-9.03: Índice de Risco Ambiental Composto.

        Combina risco hídrico (ANA) e risco de incêndio (INPE)
        com pesos iguais (0.50 cada).

        Returns:
            Dict com valor, classificação e bloco `composicao` detalhado.
        """
        agora = datetime.now(timezone.utc).isoformat()

        # Componente 1: Risco Hídrico (apenas para portos fluviais)
        estacao = self.ana.get_estacao_for_porto(id_instalacao)
        risco_hidrico = None
        hidrico_data = {}
        if estacao:
            hidrico_data = await self.ana.calcular_risco_hidrico(
                estacao["codigo"], calado_minimo
            )
            risco_hidrico = hidrico_data.get("risco_normalizado")

        # Componente 2: Risco de Incêndio
        incendio_data = await self.inpe.calcular_risco_incendio(
            id_instalacao, raio_incendio_km, dias_incendio
        )
        risco_incendio = incendio_data.get("risco_normalizado")

        # Calcula índice composto
        componentes_validos = []
        if risco_hidrico is not None:
            componentes_validos.append(("hidrico", risco_hidrico))
        if risco_incendio is not None:
            componentes_validos.append(("incendio", risco_incendio))

        if not componentes_validos:
            valor_composto = None
            classificacao = "sem_dados"
        elif len(componentes_validos) == 1:
            # Só um componente disponível — usa ele direto
            valor_composto = componentes_validos[0][1]
            classificacao = _classificar_risco(valor_composto)
        else:
            # Ambos disponíveis — média ponderada (pesos iguais)
            valor_composto = round(
                0.50 * risco_hidrico + 0.50 * risco_incendio, 3
            )
            classificacao = _classificar_risco(valor_composto)

        # Bloco composicao — transparência para o usuário
        composicao_componentes = []

        if estacao:
            composicao_componentes.append({
                "nome": "Risco Hídrico",
                "codigo_fonte": "IND-9.01",
                "valor_normalizado": risco_hidrico,
                "peso": 0.50,
                "fonte": "ANA — Agência Nacional de Águas",
                "estacao": f"{estacao['nome']} ({estacao['codigo']})",
                "rio": estacao.get("rio", ""),
                "periodo_dados": "últimos dados disponíveis",
                "ultima_atualizacao": agora,
                "descricao": f"Nível do rio vs. calado mínimo operacional ({calado_minimo}m)",
            })

        composicao_componentes.append({
            "nome": "Risco de Incêndio",
            "codigo_fonte": "IND-9.02",
            "valor_normalizado": risco_incendio,
            "peso": 0.50,
            "fonte": "INPE — Instituto Nacional de Pesquisas Espaciais",
            "raio_busca_km": raio_incendio_km,
            "focos_detectados": incendio_data.get("focos_detectados"),
            "periodo_dados": f"últimos {dias_incendio} dias",
            "ultima_atualizacao": agora,
            "descricao": f"Focos de incêndio em raio de {raio_incendio_km}km da instalação",
        })

        n_comp = len(componentes_validos)
        if n_comp == 2:
            formula = "IRAmb = 0.50 × Risco_Hídrico + 0.50 × Risco_Incêndio"
        elif n_comp == 1:
            nome = componentes_validos[0][0].replace("_", " ").title()
            formula = f"IRAmb = 1.00 × Risco_{nome} (único componente disponível)"
        else:
            formula = "IRAmb = sem dados disponíveis"

        return {
            "id_instalacao": id_instalacao,
            "valor": valor_composto,
            "classificacao": classificacao,
            "composicao": {
                "formula": formula,
                "componentes": composicao_componentes,
                "nota_metodologica": (
                    "Valores normalizados 0-1. Risco hídrico: margem entre nível do rio "
                    "e calado mínimo. Risco de incêndio: contagem de focos normalizada "
                    "(0 focos = 0, 50+ focos = 1). Pesos iguais quando ambos disponíveis. "
                    "Para portos marítimos sem rio, apenas o risco de incêndio é considerado."
                ),
            },
        }


def _classificar_risco(valor: float) -> str:
    if valor < 0.3:
        return "baixo"
    elif valor < 0.7:
        return "moderado"
    else:
        return "alto"


# Singleton
_ambiental_service: Optional[AmbientalService] = None


def get_ambiental_service() -> AmbientalService:
    global _ambiental_service
    if _ambiental_service is None:
        _ambiental_service = AmbientalService()
    return _ambiental_service
