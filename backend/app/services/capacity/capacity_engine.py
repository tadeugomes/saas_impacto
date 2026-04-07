"""
Motor de cálculo de capacidade portuária.

Implementa:
- Eq. 1b: C_cais = BOR_adm × H_ef × Lm / (Ta + a)
- Alocação por mix de carga
- BOR observado e BUR
- Flag de saturação

Referências:
- roteiro_capacidades_portuarias_v12.md, Passos 2-8
- Memoria_Calculo_Capacidade_Conteineres.ipynb, célula 8
- Memoria_Calculo_Capacidade_Sem_Conteineres.ipynb, célula 8
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from app.services.capacity.bor_adm_table import get_bor_adm
from app.services.capacity.constants import (
    DEFAULT_CLEARANCE_H,
    DEFAULT_FATOR_TEU,
    DEFAULT_H_EF,
    normalizar_perfil,
)


def compute_berth_capacity(
    indicators: List[dict],
    n_bercos: int = 1,
    h_ef: float = DEFAULT_H_EF,
    clearance_h: float = DEFAULT_CLEARANCE_H,
    fator_teu: float = DEFAULT_FATOR_TEU,
    bor_adm_override: Optional[float] = None,
    mov_realizada: Optional[Dict[str, float]] = None,
) -> List[dict]:
    """Calcula capacidade de cais para cada grupo de indicadores.

    Parameters
    ----------
    indicators : list[dict]
        Indicadores operacionais por grupo (output de compute_group_indicators).
        Campos esperados: ano, id_instalacao, berco, perfil_carga, sentido,
        is_container, n_atracacoes, mean_ta_h, mean_lm, ta_plus_a
    n_bercos : int
        Número de berços operacionais (da config do terminal).
    h_ef : float
        Horas efetivas de operação por ano.
    clearance_h : float
        Intervalo entre atracações (parâmetro 'a').
    fator_teu : float
        Fator de conversão TEU/contêiner.
    bor_adm_override : float | None
        BOR admissível customizado (None = usa Quadro 17).
    mov_realizada : dict | None
        Movimentação realizada por grupo-chave (para BUR). Se None, usa
        a soma de Lm × n_atracacoes como proxy.

    Returns
    -------
    list[dict]
        Resultados de capacidade por grupo com:
        - c_cais_bruta: capacidade bruta do berço
        - bor_adm: BOR admissível utilizado
        - bor_obs: BOR observado (%)
        - bur_obs: BUR observado (%)
        - saturado: True se BOR_obs > BOR_adm
    """
    if not indicators:
        return []

    results = []

    for ind in indicators:
        ta_plus_a = ind.get("ta_plus_a")
        mean_lm = ind.get("mean_lm")
        mean_ta = ind.get("mean_ta_h")
        n_atrac = ind.get("n_atracacoes", 0)
        is_container = ind.get("is_container", False)
        perfil = ind.get("perfil_carga", "")

        # Pular grupos sem dados suficientes
        if not ta_plus_a or ta_plus_a <= 0 or not mean_lm or mean_lm <= 0:
            continue

        # BOR admissível
        bor_adm = get_bor_adm(
            perfil=perfil,
            n_bercos=n_bercos,
            is_container=is_container,
            override=bor_adm_override,
        )

        # Eq. 1b: C_cais = BOR_adm × H_ef × Lm / (Ta + a)
        c_cais_bruta = (bor_adm * h_ef * mean_lm) / ta_plus_a

        # Para contêineres: também em toneladas
        c_cais_tons = None
        if is_container:
            c_cais_tons = c_cais_bruta * fator_teu

        # BOR observado (%)
        # BOR = (N_atracacoes × Ta) / (N_bercos × H_ef) × 100
        bor_obs = None
        if mean_ta and mean_ta > 0 and n_bercos > 0 and h_ef > 0:
            bor_obs = (n_atrac * mean_ta) / (n_bercos * h_ef) * 100

        # BUR observado (%)
        # BUR = Mov_realizada / C_cais × 100
        bur_obs = None
        group_key = f"{ind['ano']}_{ind['id_instalacao']}_{ind.get('berco', '')}_{perfil}_{ind.get('sentido', '')}"
        if mov_realizada and group_key in mov_realizada:
            mov = mov_realizada[group_key]
        else:
            # Proxy: Lm médio × número de atracações
            mov = mean_lm * n_atrac

        if c_cais_bruta > 0:
            bur_obs = (mov / c_cais_bruta) * 100

        # Flag de saturação
        saturado = False
        if bor_obs is not None:
            saturado = bor_obs > (bor_adm * 100)

        result = {
            # Chave
            "ano": ind["ano"],
            "id_instalacao": ind["id_instalacao"],
            "berco": ind.get("berco", ""),
            "perfil_carga": perfil,
            "sentido": ind.get("sentido"),
            "is_container": is_container,
            # Parâmetros utilizados
            "n_bercos": n_bercos,
            "h_ef": h_ef,
            "clearance_h": clearance_h,
            "bor_adm": bor_adm,
            "fator_teu": fator_teu if is_container else None,
            # Indicadores de entrada
            "mean_ta_h": mean_ta,
            "mean_lm": mean_lm,
            "ta_plus_a": ta_plus_a,
            "n_atracacoes": n_atrac,
            # Resultados de capacidade
            "c_cais_bruta": round(c_cais_bruta, 2),
            "c_cais_tons": round(c_cais_tons, 2) if c_cais_tons is not None else None,
            "unidade_capacidade": "TEU/ano" if is_container else "t/ano",
            # Indicadores de ocupação
            "bor_obs_pct": round(bor_obs, 2) if bor_obs is not None else None,
            "bur_obs_pct": round(bur_obs, 2) if bur_obs is not None else None,
            "mov_realizada": round(mov, 2),
            # Sinal de saturação
            "saturado": saturado,
            "folga_operacional": round(c_cais_bruta - mov, 2) if c_cais_bruta else None,
        }
        results.append(result)

    return results


def allocate_by_mix(
    capacity_results: List[dict],
) -> List[dict]:
    """Aloca a capacidade bruta do berço entre os perfis de carga por fração de tempo.

    Quando um berço opera múltiplos perfis de carga, a capacidade total é
    distribuída proporcionalmente ao tempo ocupado por cada perfil.

    f(j) = T_total(j) / T_total_berco
    C_alocada(j) = C_bruta_berco × f(j)

    Parameters
    ----------
    capacity_results : list[dict]
        Resultados de compute_berth_capacity().

    Returns
    -------
    list[dict]
        Mesma lista com campos adicionais:
        - fracao_tempo: fração do tempo total do berço ocupada por este perfil
        - c_alocada: capacidade alocada por mix
    """
    # Agrupar por (ano, id_instalacao, berco)
    BercoKey = Tuple[int, str, str]
    berco_groups: Dict[BercoKey, List[dict]] = defaultdict(list)

    for r in capacity_results:
        key: BercoKey = (r["ano"], r["id_instalacao"], r["berco"])
        berco_groups[key].append(r)

    results = []
    for key, group in berco_groups.items():
        # Tempo total por perfil: T(j) = n_atracacoes(j) × ta_plus_a(j)
        tempos = []
        for r in group:
            t = (r["n_atracacoes"] * r["ta_plus_a"]) if r["ta_plus_a"] else 0
            tempos.append(t)
        t_total = sum(tempos)

        for r, t_j in zip(group, tempos):
            fracao = t_j / t_total if t_total > 0 else 0
            c_alocada = r["c_cais_bruta"] * fracao if r["c_cais_bruta"] else 0

            r["fracao_tempo"] = round(fracao, 4)
            r["c_alocada"] = round(c_alocada, 2)
            results.append(r)

    return results


def consolidate_system(
    capacity_results: List[dict],
    c_armazenagem: Optional[float] = None,
    c_hinterland: Optional[float] = None,
) -> dict:
    """Consolidação sistêmica (Quadro 5 / Eq. 13).

    C_sistema = min(C_cais, C_armazenagem, C_hinterlândia)

    Parameters
    ----------
    capacity_results : list[dict]
        Resultados de capacidade (com alocação por mix).
    c_armazenagem : float | None
        Capacidade de armazenamento (Fase 2). None = não configurada.
    c_hinterland : float | None
        Capacidade de hinterlândia (Fase 2). None = não configurada.

    Returns
    -------
    dict
        Resumo sistêmico com c_cais_total, c_sistema, gargalo.
    """
    if not capacity_results:
        return {
            "c_cais_total": 0,
            "c_armazenagem": c_armazenagem,
            "c_hinterland": c_hinterland,
            "c_sistema": 0,
            "gargalo": "sem_dados",
        }

    c_cais_total = sum(
        r.get("c_alocada", r.get("c_cais_bruta", 0))
        for r in capacity_results
    )

    capacidades = {"cais": c_cais_total}
    if c_armazenagem is not None:
        capacidades["armazenagem"] = c_armazenagem
    if c_hinterland is not None:
        capacidades["hinterland"] = c_hinterland

    gargalo = min(capacidades, key=capacidades.get)
    c_sistema = capacidades[gargalo]

    return {
        "c_cais_total": round(c_cais_total, 2),
        "c_armazenagem": c_armazenagem,
        "c_hinterland": c_hinterland,
        "c_sistema": round(c_sistema, 2),
        "gargalo": gargalo,
        "n_perfis": len(capacity_results),
        "n_atracacoes_total": sum(r.get("n_atracacoes", 0) for r in capacity_results),
        "n_bercos_distintos": len({r.get("berco") for r in capacity_results if r.get("berco")}),
    }
