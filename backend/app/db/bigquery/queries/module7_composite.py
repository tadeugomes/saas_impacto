"""
Índices Sintéticos Compostos — Módulo 7 (Fase 3).

Combina dados de BigQuery (operacionais) + APIs externas (macro, ambiental,
fiscal) para criar índices cross-module com transparência total via bloco
`composicao`.

IND-7.08: Índice de Desenvolvimento Portuário Municipal (IDPM)
IND-7.09: Índice de Risco Operacional (IRO)
IND-7.10: Índice de Governança Portuária (IGP)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


async def query_idpm(
    id_instalacao: Optional[str] = None,
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    IND-7.08: Índice de Desenvolvimento Portuário Municipal (IDPM).

    Combina 5 dimensões com pesos iguais (0.20 cada):
      1. PIB per capita municipal (IBGE)
      2. Emprego portuário relativo (RAIS via BigQuery)
      3. Eficiência operacional (Score Módulo 1 via BigQuery)
      4. Autonomia fiscal (TCE)
      5. Risco ambiental invertido (ANA + INPE)

    Retorna valor normalizado 0-100 + bloco `composicao`.
    """
    agora = datetime.now(timezone.utc).isoformat()
    componentes = []
    valores = []

    # 1. PIB per capita municipal
    pib_pc = await _fetch_pib_per_capita(id_municipio, ano)
    componentes.append({
        "nome": "PIB per Capita Municipal",
        "codigo_fonte": "IND-8.06",
        "valor_bruto": pib_pc,
        "valor_normalizado": _normalize_pib(pib_pc),
        "peso": 0.20,
        "fonte": "IBGE — Agregados 5938 + 6579",
        "periodo_dados": f"Ano {ano}" if ano else "último disponível",
        "ultima_atualizacao": agora,
        "descricao": "PIB do município / população estimada",
    })
    if _normalize_pib(pib_pc) is not None:
        valores.append(("pib_pc", _normalize_pib(pib_pc), 0.20))

    # 2. Emprego portuário relativo
    emprego = await _fetch_emprego_portuario(id_municipio, ano)
    norm_emprego = _normalize_ratio(emprego, max_val=0.15)  # 15%+ do emprego = score 1
    componentes.append({
        "nome": "Emprego Portuário Relativo",
        "codigo_fonte": "IND-3 (RAIS)",
        "valor_bruto": emprego,
        "valor_normalizado": norm_emprego,
        "peso": 0.20,
        "fonte": "RAIS via BigQuery (basedosdados)",
        "periodo_dados": f"Ano {ano}" if ano else "último disponível",
        "ultima_atualizacao": agora,
        "descricao": "Empregos portuários / empregos totais do município",
    })
    if norm_emprego is not None:
        valores.append(("emprego", norm_emprego, 0.20))

    # 3. Eficiência operacional
    eficiencia = await _fetch_eficiencia_operacional(id_instalacao, ano)
    norm_efic = eficiencia / 100.0 if eficiencia is not None else None
    componentes.append({
        "nome": "Eficiência Operacional",
        "codigo_fonte": "IND-7.01",
        "valor_bruto": eficiencia,
        "valor_normalizado": norm_efic,
        "peso": 0.20,
        "fonte": "ANTAQ via BigQuery",
        "periodo_dados": f"Ano {ano}" if ano else "último disponível",
        "ultima_atualizacao": agora,
        "descricao": "Índice de eficiência operacional (Módulo 7, escala 0-100)",
    })
    if norm_efic is not None:
        valores.append(("eficiencia", norm_efic, 0.20))

    # 4. Autonomia fiscal
    autonomia = await _fetch_autonomia_fiscal(id_instalacao, id_municipio, ano)
    componentes.append({
        "nome": "Autonomia Fiscal",
        "codigo_fonte": "IND-6.12",
        "valor_bruto": autonomia,
        "valor_normalizado": autonomia,  # já é 0-1
        "peso": 0.20,
        "fonte": "TCE Estadual",
        "periodo_dados": f"Ano {ano}" if ano else "último disponível",
        "ultima_atualizacao": agora,
        "descricao": "Receita própria / receita total do município",
    })
    if autonomia is not None:
        valores.append(("autonomia", autonomia, 0.20))

    # 5. Risco ambiental invertido (1 - risco = sustentabilidade)
    risco = await _fetch_risco_ambiental(id_instalacao)
    sustentabilidade = round(1.0 - risco, 3) if risco is not None else None
    componentes.append({
        "nome": "Sustentabilidade Ambiental",
        "codigo_fonte": "IND-9.03 (invertido)",
        "valor_bruto": risco,
        "valor_normalizado": sustentabilidade,
        "peso": 0.20,
        "fonte": "ANA + INPE",
        "periodo_dados": "últimos 7 dias (incêndio) + última leitura (hídrico)",
        "ultima_atualizacao": agora,
        "descricao": "1 - Índice de Risco Ambiental (quanto menor o risco, maior o score)",
    })
    if sustentabilidade is not None:
        valores.append(("sustentabilidade", sustentabilidade, 0.20))

    # Calcula IDPM
    if not valores:
        idpm = None
        classificacao = "sem_dados"
    else:
        peso_total = sum(v[2] for v in valores)
        idpm_raw = sum(v[1] * v[2] for v in valores) / peso_total
        idpm = round(idpm_raw * 100, 1)  # Escala 0-100
        classificacao = (
            "alto" if idpm >= 70
            else "medio" if idpm >= 40
            else "baixo"
        )

    # Monta formula dinâmica
    termos = [f"{v[2]/sum(x[2] for x in valores):.2f} × {v[0]}" for v in valores] if valores else []
    formula = f"IDPM = ({' + '.join(termos)}) × 100" if termos else "IDPM = sem dados"

    return [{
        "id_instalacao": id_instalacao,
        "id_municipio": id_municipio,
        "ano": ano,
        "valor": idpm,
        "classificacao": classificacao,
        "componentes_disponiveis": len(valores),
        "componentes_total": 5,
        "composicao": {
            "formula": formula,
            "componentes": componentes,
            "nota_metodologica": (
                "O IDPM combina 5 dimensões com pesos iguais (0.20 cada). "
                "Quando um componente não está disponível, os pesos dos demais "
                "são redistribuídos proporcionalmente. Valores normalizados 0-1, "
                "resultado final em escala 0-100. Classificação: Alto (≥70), "
                "Médio (40-69), Baixo (<40)."
            ),
        },
    }]


async def query_indice_risco_operacional(
    id_instalacao: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    IND-7.09: Índice de Risco Operacional (IRO).

    Combina 3 componentes:
      1. Risco de maré — restrição por janela navegável (0.40)
      2. Risco hídrico — nível do rio para portos fluviais (0.30)
      3. Risco ambiental — focos de incêndio próximos (0.30)

    Para portos marítimos sem dados fluviais, os pesos são redistribuídos.
    """
    agora = datetime.now(timezone.utc).isoformat()
    componentes = []
    valores = []

    # 1. Risco de maré (inversão da taxa de aproveitamento)
    from app.clients.mares import get_mares_client
    mares = get_mares_client()
    estacao = mares.get_estacao_for_instalacao(id_instalacao) if id_instalacao else None

    if estacao:
        janela = await mares.janelas_navegacao(estacao["id"], calado_minimo=10.0)
        pct = janela.get("percentual_janela")
        risco_mare = round(1.0 - pct / 100, 3) if pct is not None else None
    else:
        risco_mare = None

    componentes.append({
        "nome": "Risco de Maré",
        "codigo_fonte": "IND-1.13 (invertido)",
        "valor_normalizado": risco_mare,
        "peso": 0.40,
        "fonte": "Marinha do Brasil — Tábua de Marés",
        "periodo_dados": "próximos 7 dias",
        "ultima_atualizacao": agora,
        "descricao": "1 - (% do tempo com maré suficiente). Maior restrição = maior risco.",
    })
    if risco_mare is not None:
        valores.append(("mare", risco_mare, 0.40))

    # 2. Risco hídrico
    from app.clients.ana import get_ana_client
    ana = get_ana_client()
    estacao_hidro = ana.get_estacao_for_porto(id_instalacao) if id_instalacao else None

    risco_hidrico = None
    if estacao_hidro:
        hidro = await ana.calcular_risco_hidrico(estacao_hidro["codigo"], 12.0)
        risco_hidrico = hidro.get("risco_normalizado")

    componentes.append({
        "nome": "Risco Hídrico",
        "codigo_fonte": "IND-9.01",
        "valor_normalizado": risco_hidrico,
        "peso": 0.30,
        "fonte": "ANA — Agência Nacional de Águas",
        "estacao": f"{estacao_hidro['nome']} ({estacao_hidro['codigo']})" if estacao_hidro else "N/A (porto marítimo)",
        "periodo_dados": "última leitura disponível",
        "ultima_atualizacao": agora,
        "descricao": "Nível do rio vs. calado mínimo. Portos marítimos: N/A.",
    })
    if risco_hidrico is not None:
        valores.append(("hidrico", risco_hidrico, 0.30))

    # 3. Risco de incêndio
    from app.clients.inpe import get_inpe_client
    inpe = get_inpe_client()
    incendio = await inpe.calcular_risco_incendio(id_instalacao, raio_km=50, dias=7)
    risco_incendio = incendio.get("risco_normalizado")

    componentes.append({
        "nome": "Risco de Incêndio",
        "codigo_fonte": "IND-9.02",
        "valor_normalizado": risco_incendio,
        "peso": 0.30,
        "fonte": "INPE — Queimadas",
        "focos_detectados": incendio.get("focos_detectados"),
        "periodo_dados": "últimos 7 dias",
        "ultima_atualizacao": agora,
        "descricao": f"Focos de incêndio em raio de 50km: {incendio.get('focos_detectados', 'N/A')}",
    })
    if risco_incendio is not None:
        valores.append(("incendio", risco_incendio, 0.30))

    # Calcula IRO
    if not valores:
        iro = None
        classificacao = "sem_dados"
    else:
        peso_total = sum(v[2] for v in valores)
        iro = round(sum(v[1] * v[2] for v in valores) / peso_total, 3)
        classificacao = "baixo" if iro < 0.3 else "moderado" if iro < 0.7 else "alto"

    termos = [f"{v[2]/sum(x[2] for x in valores):.2f} × {v[0]}" for v in valores] if valores else []
    formula = f"IRO = {' + '.join(termos)}" if termos else "IRO = sem dados"

    return [{
        "id_instalacao": id_instalacao,
        "valor": iro,
        "classificacao": classificacao,
        "componentes_disponiveis": len(valores),
        "componentes_total": 3,
        "composicao": {
            "formula": formula,
            "componentes": componentes,
            "nota_metodologica": (
                "O IRO combina riscos de maré (peso 0.40), hídrico (0.30) e "
                "incêndio (0.30). Portos marítimos sem dados fluviais: peso "
                "redistribuído entre maré e incêndio. Escala 0-1. "
                "Classificação: Baixo (<0.3), Moderado (0.3-0.7), Alto (>0.7)."
            ),
        },
    }]


async def query_indice_governanca(
    id_instalacao: Optional[str] = None,
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    IND-7.10: Índice de Governança Portuária (IGP).

    Combina 3 componentes:
      1. Transparência fiscal — execução orçamentária (0.35)
      2. Investimento federal per capita (0.30)
      3. Autonomia fiscal (0.35)
    """
    agora = datetime.now(timezone.utc).isoformat()
    componentes = []
    valores = []

    # 1. Execução orçamentária
    execucao = await _fetch_execucao_orcamentaria(id_instalacao, id_municipio, ano)
    componentes.append({
        "nome": "Execução Orçamentária",
        "codigo_fonte": "IND-6.14",
        "valor_normalizado": execucao,
        "peso": 0.35,
        "fonte": "TCE Estadual",
        "periodo_dados": f"Ano {ano}" if ano else "último disponível",
        "ultima_atualizacao": agora,
        "descricao": "Despesa executada / despesa autorizada (ideal próximo de 1.0)",
    })
    if execucao is not None:
        valores.append(("execucao", min(execucao, 1.0), 0.35))

    # 2. Investimento federal per capita (normalizado)
    inv_pc = await _fetch_investimento_federal_pc(id_municipio, ano)
    norm_inv = _normalize_ratio(inv_pc, max_val=5000)  # R$5000/hab = score 1
    componentes.append({
        "nome": "Investimento Federal per Capita",
        "codigo_fonte": "IND-6.15",
        "valor_bruto_reais": inv_pc,
        "valor_normalizado": norm_inv,
        "peso": 0.30,
        "fonte": "Portal da Transparência",
        "periodo_dados": f"Ano {ano}" if ano else "último disponível",
        "ultima_atualizacao": agora,
        "descricao": "Contratos + emendas federais / população",
    })
    if norm_inv is not None:
        valores.append(("investimento", norm_inv, 0.30))

    # 3. Autonomia fiscal
    autonomia = await _fetch_autonomia_fiscal(id_instalacao, id_municipio, ano)
    componentes.append({
        "nome": "Autonomia Fiscal",
        "codigo_fonte": "IND-6.12",
        "valor_normalizado": autonomia,
        "peso": 0.35,
        "fonte": "TCE Estadual",
        "periodo_dados": f"Ano {ano}" if ano else "último disponível",
        "ultima_atualizacao": agora,
        "descricao": "Receita própria / receita total (maior = menos dependente de transferências)",
    })
    if autonomia is not None:
        valores.append(("autonomia", autonomia, 0.35))

    # Calcula IGP
    if not valores:
        igp = None
        classificacao = "sem_dados"
    else:
        peso_total = sum(v[2] for v in valores)
        igp_raw = sum(v[1] * v[2] for v in valores) / peso_total
        igp = round(igp_raw * 100, 1)  # Escala 0-100
        classificacao = (
            "alto" if igp >= 70
            else "medio" if igp >= 40
            else "baixo"
        )

    termos = [f"{v[2]/sum(x[2] for x in valores):.2f} × {v[0]}" for v in valores] if valores else []
    formula = f"IGP = ({' + '.join(termos)}) × 100" if termos else "IGP = sem dados"

    return [{
        "id_instalacao": id_instalacao,
        "id_municipio": id_municipio,
        "ano": ano,
        "valor": igp,
        "classificacao": classificacao,
        "componentes_disponiveis": len(valores),
        "componentes_total": 3,
        "composicao": {
            "formula": formula,
            "componentes": componentes,
            "nota_metodologica": (
                "O IGP combina execução orçamentária (peso 0.35), investimento "
                "federal per capita (0.30) e autonomia fiscal (0.35). Valores "
                "normalizados 0-1, resultado em escala 0-100. Classificação: "
                "Alto (≥70), Médio (40-69), Baixo (<40). Dados dependem de "
                "disponibilidade da API do TCE estadual e Portal da Transparência."
            ),
        },
    }]


# ============================================================================
# Helpers — buscam dados dos serviços existentes
# ============================================================================

def _normalize_pib(pib_pc: Optional[float]) -> Optional[float]:
    """Normaliza PIB per capita: R$100k+ = 1.0."""
    if pib_pc is None:
        return None
    return round(min(pib_pc / 100_000, 1.0), 3)


def _normalize_ratio(val: Optional[float], max_val: float) -> Optional[float]:
    """Normaliza um valor para 0-1 com teto em max_val."""
    if val is None:
        return None
    return round(min(val / max_val, 1.0), 3)


async def _fetch_pib_per_capita(
    id_municipio: Optional[str], ano: Optional[int]
) -> Optional[float]:
    """Busca PIB per capita via IBGE."""
    if not id_municipio:
        return None
    try:
        from app.clients.ibge import get_ibge_client
        ibge = get_ibge_client()
        pib = await ibge.consultar_agregado(5938, 37, f"N6[{id_municipio}]", str(ano or 2021))
        pop = await ibge.populacao_municipio(id_municipio, ano or 2021)
        if pib and pop and pop.get("valor"):
            pib_val = float(pib[0].get("valor", 0)) if pib else 0
            pop_val = float(pop["valor"])
            return round(pib_val / pop_val, 2) if pop_val > 0 else None
    except Exception as e:
        logger.warning("idpm_pib_error", error=str(e))
    return None


async def _fetch_emprego_portuario(
    id_municipio: Optional[str], ano: Optional[int]
) -> Optional[float]:
    """Busca ratio emprego portuário / total via BigQuery."""
    if not id_municipio:
        return None
    try:
        from app.db.bigquery.client import get_bigquery_client
        bq = get_bigquery_client()
        sql = f"""
        SELECT
            SAFE_DIVIDE(
                COUNTIF(cnae_2_subclasse IN ('5231101','5231102','5232000','5239701','5239799')),
                COUNT(*)
            ) AS ratio_portuario
        FROM `basedosdados.br_me_rais.microdados_vinculos`
        WHERE id_municipio = '{id_municipio}'
          AND ano = {ano or 2022}
        """
        rows = await bq.execute_query(sql, timeout_ms=30000)
        if rows:
            return float(rows[0].get("ratio_portuario", 0))
    except Exception as e:
        logger.warning("idpm_emprego_error", error=str(e))
    return None


async def _fetch_eficiencia_operacional(
    id_instalacao: Optional[str], ano: Optional[int]
) -> Optional[float]:
    """Busca score de eficiência via BigQuery (IND-7.01)."""
    if not id_instalacao:
        return None
    try:
        from app.db.bigquery.queries.module7_synthetic_indices import query_indice_eficiencia_operacional
        from app.db.bigquery.client import get_bigquery_client
        bq = get_bigquery_client()
        sql = query_indice_eficiencia_operacional(id_instalacao, ano)
        rows = await bq.execute_query(sql, timeout_ms=30000)
        if rows:
            return float(rows[0].get("indice_eficiencia", 0))
    except Exception as e:
        logger.warning("idpm_eficiencia_error", error=str(e))
    return None


async def _fetch_autonomia_fiscal(
    id_instalacao: Optional[str], id_municipio: Optional[str], ano: Optional[int]
) -> Optional[float]:
    """Busca autonomia fiscal via TCE."""
    try:
        from app.clients.tce import get_uf_for_porto, get_tce_client, TCE_REGISTRY
        uf = get_uf_for_porto(id_instalacao) if id_instalacao else None
        if not uf or uf not in TCE_REGISTRY or not id_municipio or not ano:
            return None
        tce = get_tce_client(uf)
        result = await tce.calcular_autonomia_fiscal(id_municipio, ano)
        return result.get("autonomia_fiscal")
    except Exception as e:
        logger.warning("autonomia_fiscal_error", error=str(e))
    return None


async def _fetch_risco_ambiental(id_instalacao: Optional[str]) -> Optional[float]:
    """Busca risco ambiental composto (IND-9.03)."""
    if not id_instalacao:
        return None
    try:
        from app.services.ambiental_service import get_ambiental_service
        service = get_ambiental_service()
        result = await service.indice_risco_ambiental(id_instalacao)
        return result.get("valor")
    except Exception as e:
        logger.warning("risco_ambiental_error", error=str(e))
    return None


async def _fetch_execucao_orcamentaria(
    id_instalacao: Optional[str], id_municipio: Optional[str], ano: Optional[int]
) -> Optional[float]:
    """Busca eficiência de execução orçamentária via TCE."""
    try:
        from app.clients.tce import get_uf_for_porto, get_tce_client, TCE_REGISTRY
        uf = get_uf_for_porto(id_instalacao) if id_instalacao else None
        if not uf or uf not in TCE_REGISTRY or not id_municipio or not ano:
            return None
        tce = get_tce_client(uf)
        result = await tce.calcular_execucao_orcamentaria(id_municipio, ano)
        return result.get("eficiencia_execucao")
    except Exception as e:
        logger.warning("execucao_orc_error", error=str(e))
    return None


async def _fetch_investimento_federal_pc(
    id_municipio: Optional[str], ano: Optional[int]
) -> Optional[float]:
    """Busca investimento federal per capita via Portal da Transparência."""
    if not id_municipio or not ano:
        return None
    try:
        from app.clients.transparencia import get_transparencia_client
        from app.clients.ibge import get_ibge_client
        transp = get_transparencia_client()
        ibge = get_ibge_client()
        pop_data = await ibge.populacao_municipio(id_municipio, ano)
        populacao = int(pop_data.get("valor", 0)) if pop_data and pop_data.get("valor") else None
        result = await transp.calcular_investimento_federal(id_municipio, ano, populacao)
        return result.get("investimento_per_capita")
    except Exception as e:
        logger.warning("inv_federal_error", error=str(e))
    return None


QUERIES_MODULE_7_COMPOSITE = {
    "IND-7.08": query_idpm,
    "IND-7.09": query_indice_risco_operacional,
    "IND-7.10": query_indice_governanca,
}
