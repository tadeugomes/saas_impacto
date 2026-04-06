"""
Cálculo de indicadores operacionais agregados por grupo (Passo 2).

Recebe os dados brutos por atracação (Planilha 1) e retorna indicadores
filtrados por IQR e agregados por grupo (Planilha 2).

Agrupamento: Ano × Instalação × Berço × Perfil × Sentido

Referências:
- Memoria_Calculo_Capacidade_Conteineres.ipynb, célula 6
- Memoria_Calculo_Capacidade_Sem_Conteineres.ipynb, célula 6
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from app.services.capacity.iqr_filter import iqr_filtered_mean, iqr_filter_stats


# Chave de agrupamento
GroupKey = Tuple[int, str, str, str, Optional[str]]  # (ano, id_instalacao, berco, perfil, sentido)


def _group_key(row: dict) -> GroupKey:
    return (
        row["ano"],
        row["id_instalacao"],
        row.get("berco", ""),
        row.get("perfil_carga", ""),
        row.get("sentido"),
    )


def compute_group_indicators(
    records: List[dict],
    clearance_h: float = 3.0,
    is_container: bool = False,
) -> List[dict]:
    """Agrupa registros e calcula indicadores operacionais com filtro IQR.

    Parameters
    ----------
    records : list[dict]
        Registros individuais por atracação (output da query base depurada).
        Campos esperados: ano, id_instalacao, berco, perfil_carga, sentido,
        inop_pre_h, t_op_h, inop_pos_h, ta_h, lm_tons/lm_teu,
        produtividade_t_h/produtividade_teu_h
    clearance_h : float
        Intervalo entre atracações (parâmetro 'a').
    is_container : bool
        Se True, usa campos TEU. Se False, usa campos de tonelagem.

    Returns
    -------
    list[dict]
        Indicadores agregados por grupo, com campos:
        - Chave: ano, id_instalacao, berco, perfil_carga, sentido
        - Indicadores: mean_inop_pre_h, mean_t_op_h, mean_inop_pos_h,
          mean_ta_h, mean_lm, mean_produtividade, ta_plus_a, n_atracacoes
        - IQR stats: iqr_inop_pre, iqr_produtividade, iqr_inop_pos
    """
    # Agrupar por chave
    groups: Dict[GroupKey, List[dict]] = defaultdict(list)
    for row in records:
        key = _group_key(row)
        groups[key].append(row)

    lm_field = "lm_teu" if is_container else "lm_tons"
    prod_field = "produtividade_teu_h" if is_container else "produtividade_t_h"

    results = []
    for key, rows in groups.items():
        ano, id_instalacao, berco, perfil, sentido = key
        n = len(rows)

        # Extrair vetores para IQR
        inop_pre_vals = [r["inop_pre_h"] for r in rows if r.get("inop_pre_h") is not None and r["inop_pre_h"] >= 0]
        prod_vals = [r[prod_field] for r in rows if r.get(prod_field) is not None and r[prod_field] > 0]
        inop_pos_vals = [r["inop_pos_h"] for r in rows if r.get("inop_pos_h") is not None and r["inop_pos_h"] >= 0]
        lm_vals = [r[lm_field] for r in rows if r.get(lm_field) is not None and r[lm_field] > 0]
        t_op_vals = [r["t_op_h"] for r in rows if r.get("t_op_h") is not None and r["t_op_h"] > 0]

        # Médias filtradas por IQR
        mean_inop_pre = iqr_filtered_mean(inop_pre_vals)
        mean_prod = iqr_filtered_mean(prod_vals)
        mean_inop_pos = iqr_filtered_mean(inop_pos_vals)
        mean_lm = iqr_filtered_mean(lm_vals)
        mean_t_op = iqr_filtered_mean(t_op_vals)

        # Ta recalculado = inop_pre + t_op + inop_pos (usando médias filtradas)
        if all(v is not None for v in [mean_inop_pre, mean_t_op, mean_inop_pos]):
            mean_ta = mean_inop_pre + mean_t_op + mean_inop_pos
        else:
            # Fallback: média IQR direta do Ta bruto
            ta_vals = [r["ta_h"] for r in rows if r.get("ta_h") is not None and r["ta_h"] > 0]
            mean_ta = iqr_filtered_mean(ta_vals)

        ta_plus_a = (mean_ta + clearance_h) if mean_ta is not None else None

        result = {
            # Chave
            "ano": ano,
            "id_instalacao": id_instalacao,
            "berco": berco,
            "perfil_carga": perfil,
            "sentido": sentido,
            "is_container": is_container,
            # Contagem
            "n_atracacoes": n,
            # Indicadores (médias IQR-filtradas)
            "mean_inop_pre_h": _round(mean_inop_pre),
            "mean_t_op_h": _round(mean_t_op),
            "mean_inop_pos_h": _round(mean_inop_pos),
            "mean_ta_h": _round(mean_ta),
            "mean_lm": _round(mean_lm),
            "mean_produtividade": _round(mean_prod),
            "ta_plus_a": _round(ta_plus_a),
            # Estatísticas IQR para auditoria
            "iqr_inop_pre": iqr_filter_stats(inop_pre_vals),
            "iqr_produtividade": iqr_filter_stats(prod_vals),
            "iqr_inop_pos": iqr_filter_stats(inop_pos_vals),
        }
        results.append(result)

    return results


def _round(value: Optional[float], digits: int = 4) -> Optional[float]:
    return round(value, digits) if value is not None else None
