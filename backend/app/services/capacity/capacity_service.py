"""
Serviço orquestrador de análise de capacidade portuária.

Coordena: BigQuery queries → IQR filter → indicadores → Eq. 1b → mix → BOR/BUR.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.services.capacity.capacity_engine import (
    allocate_by_mix,
    compute_berth_capacity,
    consolidate_system,
)
from app.services.capacity.constants import (
    DEFAULT_CLEARANCE_H,
    DEFAULT_FATOR_TEU,
    DEFAULT_H_EF,
)
from app.services.capacity.operational_indicators import compute_group_indicators

logger = logging.getLogger(__name__)


class CapacityAnalysisService:
    """Serviço de análise de capacidade de cais."""

    def __init__(self, bq_client: Any):
        self._bq = bq_client

    async def compute_capacity(
        self,
        id_instalacao: str,
        ano: Optional[int] = None,
        ano_inicio: Optional[int] = None,
        ano_fim: Optional[int] = None,
        n_bercos: int = 1,
        h_ef: float = DEFAULT_H_EF,
        clearance_h: float = DEFAULT_CLEARANCE_H,
        fator_teu: float = DEFAULT_FATOR_TEU,
        bor_adm_override: Optional[float] = None,
    ) -> dict:
        """Executa a análise completa de capacidade para uma instalação.

        Returns
        -------
        dict
            {
                "nao_conteiner": list[dict],  # resultados por perfil
                "conteiner": list[dict],       # resultados por perfil
                "consolidacao": dict,           # resumo sistêmico
                "parametros": dict,             # parâmetros utilizados
            }
        """
        from app.db.bigquery.queries.module12_capacity import (
            query_base_depurada_conteiner,
            query_base_depurada_nao_conteiner,
        )

        # 1. Executar queries BQ em paralelo
        sql_nao_cont = query_base_depurada_nao_conteiner(
            id_instalacao=id_instalacao,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )
        sql_cont = query_base_depurada_conteiner(
            id_instalacao=id_instalacao,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )

        logger.info(
            "capacity_analysis_started",
            extra={
                "id_instalacao": id_instalacao,
                "ano": ano,
                "n_bercos": n_bercos,
                "h_ef": h_ef,
            },
        )

        raw_nao_cont = await self._bq.execute_query(sql_nao_cont)
        raw_cont = await self._bq.execute_query(sql_cont)

        # 2. Calcular indicadores operacionais (IQR)
        ind_nao_cont = compute_group_indicators(
            raw_nao_cont, clearance_h=clearance_h, is_container=False
        )
        ind_cont = compute_group_indicators(
            raw_cont, clearance_h=clearance_h, is_container=True
        )

        # 3. Calcular capacidade (Eq. 1b)
        cap_nao_cont = compute_berth_capacity(
            ind_nao_cont,
            n_bercos=n_bercos,
            h_ef=h_ef,
            clearance_h=clearance_h,
            bor_adm_override=bor_adm_override,
        )
        cap_cont = compute_berth_capacity(
            ind_cont,
            n_bercos=n_bercos,
            h_ef=h_ef,
            clearance_h=clearance_h,
            fator_teu=fator_teu,
            bor_adm_override=bor_adm_override,
        )

        # 4. Alocação por mix
        all_results = allocate_by_mix(cap_nao_cont + cap_cont)

        # 5. Consolidação sistêmica
        consolidacao = consolidate_system(all_results)

        logger.info(
            "capacity_analysis_completed",
            extra={
                "id_instalacao": id_instalacao,
                "n_perfis": consolidacao["n_perfis"],
                "c_cais_total": consolidacao["c_cais_total"],
                "gargalo": consolidacao["gargalo"],
            },
        )

        nao_cont_results = [r for r in all_results if not r.get("is_container")]
        cont_results = [r for r in all_results if r.get("is_container")]

        return {
            "nao_conteiner": nao_cont_results,
            "conteiner": cont_results,
            "consolidacao": consolidacao,
            "parametros": {
                "id_instalacao": id_instalacao,
                "ano": ano,
                "ano_inicio": ano_inicio,
                "ano_fim": ano_fim,
                "n_bercos": n_bercos,
                "h_ef": h_ef,
                "clearance_h": clearance_h,
                "fator_teu": fator_teu,
                "bor_adm_override": bor_adm_override,
            },
        }
