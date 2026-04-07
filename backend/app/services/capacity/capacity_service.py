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
    H_CAL,
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
            MOTIVO_CATEGORIA,
            query_base_depurada_conteiner,
            query_base_depurada_nao_conteiner,
            query_paralisacoes_por_berco,
        )

        # 0. Buscar dados de paralisação para calcular H_ef real
        h_ef_breakdown = await self._compute_h_ef_breakdown(
            id_instalacao, ano, ano_inicio, ano_fim,
            query_paralisacoes_por_berco, MOTIVO_CATEGORIA,
        )
        if h_ef_breakdown:
            h_ef = h_ef_breakdown["h_ef_medio"]
            logger.info(
                "h_ef_from_paralisacoes",
                extra={
                    "id_instalacao": id_instalacao,
                    "h_ef_calculado": h_ef,
                    "h_cli": h_ef_breakdown["h_cli"],
                    "h_mnt": h_ef_breakdown["h_mnt"],
                    "h_nav": h_ef_breakdown["h_nav"],
                    "h_out": h_ef_breakdown["h_out"],
                    "n_bercos_com_dados": h_ef_breakdown["n_bercos"],
                },
            )

        # 1. Executar queries BQ
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
            "h_ef_breakdown": h_ef_breakdown,
        }

    async def _compute_h_ef_breakdown(
        self,
        id_instalacao: str,
        ano: Optional[int],
        ano_inicio: Optional[int],
        ano_fim: Optional[int],
        query_fn: Any,
        motivo_map: Dict[str, str],
    ) -> Optional[Dict[str, Any]]:
        """Calcula H_ef desagregado a partir de paralisações ANTAQ.

        H_ef = H_cal - H_cli - H_mnt - H_nav - H_out  (Eq. 1c)

        Retorna a média ponderada por berço. Se não houver dados
        de paralisação para a instalação, retorna None (fallback para default).
        """
        try:
            sql = query_fn(
                id_instalacao=id_instalacao,
                ano=ano, ano_inicio=ano_inicio, ano_fim=ano_fim,
            )
            raw = await self._bq.execute_query(sql, timeout_ms=60000)
        except Exception as exc:
            logger.warning("h_ef_paralisacao_query_failed: %s", exc)
            return None

        if not raw:
            logger.info("h_ef_paralisacao_sem_dados", extra={"id_instalacao": id_instalacao})
            return None

        logger.info("h_ef_paralisacao_raw_rows", extra={"n_rows": len(raw), "sample_motivo": raw[0].get("motivo", "") if raw else ""})

        # Agregar horas por berço e categoria
        berco_cats: Dict[str, Dict[str, float]] = {}
        for row in raw:
            berco = row.get("berco", "?")
            motivo = row.get("motivo", "")
            horas = float(row.get("horas", 0) or 0)
            cat = motivo_map.get(motivo)
            if cat is None:
                continue  # motivo operacional — não reduz H_ef
            if berco not in berco_cats:
                berco_cats[berco] = {"H_cli": 0, "H_mnt": 0, "H_nav": 0, "H_out": 0}
            berco_cats[berco][cat] += horas

        if not berco_cats:
            return None

        # Calcular H_ef por berço e média
        n = len(berco_cats)
        totals = {"H_cli": 0.0, "H_mnt": 0.0, "H_nav": 0.0, "H_out": 0.0}
        h_ef_per_berco: List[float] = []
        for cats in berco_cats.values():
            perda = sum(cats.values())
            h_ef_per_berco.append(max(H_CAL - perda, 0))
            for k in totals:
                totals[k] += cats[k]

        h_ef_medio = round(sum(h_ef_per_berco) / n, 1)

        return {
            "h_cal": H_CAL,
            "h_cli": round(totals["H_cli"] / n, 1),
            "h_mnt": round(totals["H_mnt"] / n, 1),
            "h_nav": round(totals["H_nav"] / n, 1),
            "h_out": round(totals["H_out"] / n, 1),
            "h_ef_medio": h_ef_medio,
            "n_bercos": n,
            "fonte": "ANTAQ paralisações",
        }
