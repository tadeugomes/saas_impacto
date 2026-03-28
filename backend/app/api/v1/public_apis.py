"""
Health/status das APIs públicas externas.

Endpoint opcional para monitoramento da disponibilidade
das APIs BACEN, IBGE etc.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

from app.clients.bacen import get_bacen_client
from app.clients.ibge import get_ibge_client
from app.clients.inpe import get_inpe_client
from app.clients.ana import get_ana_client

router = APIRouter(
    prefix="/public-apis",
    tags=["APIs Públicas"],
)


@router.get(
    "/status",
    summary="Status das APIs externas",
    response_model=Dict[str, Any],
)
async def public_apis_status():
    """Verifica conectividade com APIs externas (BACEN, IBGE)."""
    results: Dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "apis": {},
    }

    # BACEN
    try:
        bacen = get_bacen_client()
        data = await bacen.consultar_serie(432, "01/01/2025", "31/01/2025")
        results["apis"]["bacen"] = {
            "status": "connected" if data else "empty_response",
            "registros": len(data) if data else 0,
        }
    except Exception as e:
        results["apis"]["bacen"] = {
            "status": "disconnected",
            "error": str(e)[:200],
        }

    # IBGE
    try:
        ibge = get_ibge_client()
        data = await ibge.buscar_municipios("SP")
        results["apis"]["ibge"] = {
            "status": "connected" if data else "empty_response",
            "registros": len(data) if data else 0,
        }
    except Exception as e:
        results["apis"]["ibge"] = {
            "status": "disconnected",
            "error": str(e)[:200],
        }

    # INPE (Queimadas)
    try:
        inpe = get_inpe_client()
        # Teste com coordenadas de Santos
        data = await inpe.buscar_focos_incendio(-23.95, -46.33, raio_km=10, dias=1)
        results["apis"]["inpe"] = {
            "status": "connected",
            "focos_teste": len(data) if data else 0,
        }
    except Exception as e:
        results["apis"]["inpe"] = {
            "status": "disconnected",
            "error": str(e)[:200],
        }

    # ANA (Hidrologia)
    try:
        ana = get_ana_client()
        data = await ana.consultar_nivel_rio("14990000")  # Manaus
        results["apis"]["ana"] = {
            "status": "connected" if data else "empty_response",
            "registros": len(data) if data else 0,
        }
    except Exception as e:
        results["apis"]["ana"] = {
            "status": "disconnected",
            "error": str(e)[:200],
        }

    return results
