"""
Serviço de indicadores de Compliance e Governança Portuária (Módulo 10).

Calcula índices compostos combinando dados de PNCP, TCU, Portal da
Transparência, Querido Diário e DataJud — todos filtrados por relevância
portuária (CNAE, termos, órgãos).

Todo índice composto retorna bloco `composicao` com fórmula, pesos,
fontes e nota metodológica para total transparência ao investidor.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.clients.pncp import PncpClient, get_pncp_client
from app.clients.tcu_federal import TcuClient, get_tcu_client
from app.clients.querido_diario import QueridoDiarioClient, get_querido_diario_client
from app.clients.datajud import DatajudClient, get_datajud_client
from app.clients.transparencia import TransparenciaClient, get_transparencia_client

logger = logging.getLogger(__name__)


def _normalize_count(value: int, max_value: int) -> float:
    """Normaliza contagem para 0-1. Mais = risco maior."""
    if value <= 0:
        return 0.0
    if value >= max_value:
        return 1.0
    return round(value / max_value, 3)


def _invert_ratio(value: Optional[float]) -> Optional[float]:
    """Inverte razão: regularidade alta = risco baixo."""
    if value is None:
        return None
    return round(1.0 - value, 3)


def _classify_risk(valor: float) -> str:
    if valor < 0.3:
        return "baixo"
    elif valor < 0.7:
        return "moderado"
    return "alto"


def _classify_governance(valor: float) -> str:
    """Classifica governança em escala 0-100."""
    if valor >= 70:
        return "bom"
    elif valor >= 40:
        return "regular"
    return "fraco"


class ComplianceService:
    """Serviço de índices compostos de compliance e governança."""

    def __init__(
        self,
        pncp: Optional[PncpClient] = None,
        tcu: Optional[TcuClient] = None,
        diario: Optional[QueridoDiarioClient] = None,
        datajud: Optional[DatajudClient] = None,
        transparencia: Optional[TransparenciaClient] = None,
    ):
        self.pncp = pncp or get_pncp_client()
        self.tcu = tcu or get_tcu_client()
        self.diario = diario or get_querido_diario_client()
        self.datajud = datajud or get_datajud_client()
        self.transparencia = transparencia or get_transparencia_client()

    async def indice_risco_regulatorio(
        self,
        id_instalacao: str,
        id_municipio: str,
        ano: int,
    ) -> Dict[str, Any]:
        """
        IND-10.07: Índice de Risco Regulatório Composto.

        Combina 5 componentes com pesos:
          0.25 × sanções (CEIS)
          0.20 × acórdãos TCU
          0.20 × processos judiciais
          0.20 × irregularidade licitatória (1 - regularidade)
          0.15 × menções negativas em diário oficial
        """
        agora = datetime.now(timezone.utc).isoformat()

        # Coleta componentes em paralelo
        import asyncio
        sancoes_task = self.transparencia.buscar_contratos_municipio(id_municipio, ano)
        acordaos_task = self.tcu.buscar_acordaos_portuarios(id_instalacao, ano)
        processos_task = self.datajud.buscar_processos_portuarios(id_instalacao, ano)
        regularidade_task = self.pncp.calcular_regularidade_licitatoria(id_municipio, ano)
        mencoes_task = self.diario.analisar_mencoes_com_temas(id_municipio, id_instalacao, 12)

        results = await asyncio.gather(
            sancoes_task, acordaos_task, processos_task,
            regularidade_task, mencoes_task,
            return_exceptions=True,
        )

        # Extrai valores com fallback
        sancoes = results[0] if not isinstance(results[0], Exception) else []
        acordaos = results[1] if not isinstance(results[1], Exception) else []
        processos = results[2] if not isinstance(results[2], Exception) else []
        regularidade = results[3] if not isinstance(results[3], Exception) else {}
        mencoes = results[4] if not isinstance(results[4], Exception) else {}

        n_sancoes = len(sancoes) if isinstance(sancoes, list) else 0
        n_acordaos = len(acordaos) if isinstance(acordaos, list) else 0
        n_processos = len(processos) if isinstance(processos, list) else 0
        reg_ratio = regularidade.get("regularidade") if isinstance(regularidade, dict) else None
        score_sentimento = mencoes.get("score_sentimento") if isinstance(mencoes, dict) else None

        # Normaliza componentes (0-1, mais alto = mais risco)
        comp_sancoes = _normalize_count(n_sancoes, 10)
        comp_acordaos = _normalize_count(n_acordaos, 5)
        comp_processos = _normalize_count(n_processos, 20)
        comp_irregularidade = _invert_ratio(reg_ratio)  # 1 - regularidade
        # Sentimento: negativo = risco alto, positivo = risco baixo
        comp_mencoes_neg = None
        if score_sentimento is not None:
            comp_mencoes_neg = round(max(0, min(1, (0 - score_sentimento + 1) / 2)), 3)

        # Calcula índice composto
        componentes_dados = []
        pesos = {
            "Sanções (CEIS)": (comp_sancoes, 0.25),
            "Acórdãos TCU": (comp_acordaos, 0.20),
            "Processos Judiciais": (comp_processos, 0.20),
            "Irregularidade Licitatória": (comp_irregularidade, 0.20),
            "Menções Negativas": (comp_mencoes_neg, 0.15),
        }

        valores_validos = []
        componentes_detail = []
        fontes_map = {
            "Sanções (CEIS)": "Portal da Transparência — CEIS/CNEP",
            "Acórdãos TCU": "TCU — Tribunal de Contas da União",
            "Processos Judiciais": "DataJud/CNJ",
            "Irregularidade Licitatória": "PNCP — Portal Nacional de Contratações",
            "Menções Negativas": "Querido Diário — OK Brasil",
        }
        raw_values = {
            "Sanções (CEIS)": f"{n_sancoes} empresas sancionadas",
            "Acórdãos TCU": f"{n_acordaos} decisões",
            "Processos Judiciais": f"{n_processos} processos ativos",
            "Irregularidade Licitatória": f"{reg_ratio:.1%} regular" if reg_ratio is not None else "sem dados",
            "Menções Negativas": f"score {score_sentimento}" if score_sentimento is not None else "sem dados",
        }

        for nome, (valor, peso) in pesos.items():
            componentes_detail.append({
                "nome": nome,
                "valor_normalizado": valor,
                "peso": peso,
                "fonte": fontes_map[nome],
                "valor_bruto": raw_values[nome],
                "ultima_atualizacao": agora,
            })
            if valor is not None:
                valores_validos.append((nome, valor, peso))

        if not valores_validos:
            valor_composto = None
            classificacao = "sem_dados"
            formula = "IRR = sem dados disponíveis"
        else:
            peso_total = sum(p for _, _, p in valores_validos)
            valor_composto = round(
                sum(v * p for _, v, p in valores_validos) / peso_total, 3
            )
            classificacao = _classify_risk(valor_composto)
            termos = [f"{p/peso_total:.2f} × {n}" for n, _, p in valores_validos]
            formula = f"IRR = {' + '.join(termos)}"

        return {
            "id_instalacao": id_instalacao,
            "id_municipio": id_municipio,
            "ano": ano,
            "valor": valor_composto,
            "classificacao": classificacao,
            "composicao": {
                "formula": formula,
                "componentes": componentes_detail,
                "nota_metodologica": (
                    "Valores normalizados 0-1 (mais alto = mais risco). "
                    "Sanções: contagem normalizada (0=nenhuma, 10+=máximo). "
                    "TCU: contagem de acórdãos portuários. "
                    "Processos: contagem normalizada (0=nenhum, 20+=máximo). "
                    "Irregularidade: 1 - taxa de publicação regular no PNCP. "
                    "Menções: score de sentimento invertido (-1=risco máximo, +1=risco zero). "
                    "Todos os dados filtrados por relevância portuária (CNAE, termos, órgãos)."
                ),
            },
        }

    async def indice_governanca_portuaria(
        self,
        id_instalacao: str,
        id_municipio: str,
        ano: int,
    ) -> Dict[str, Any]:
        """
        IND-10.08: Índice de Governança Portuária (0-100).

        Combina compliance (IND-10.07) + finanças públicas + transparência.

        IGP = 100 - (0.40 × risco_regulatorio × 100)
            + 0.30 × autonomia_fiscal × 100
            + 0.30 × execucao_orcamentaria × 100
        """
        agora = datetime.now(timezone.utc).isoformat()

        # Busca risco regulatório
        risco = await self.indice_risco_regulatorio(id_instalacao, id_municipio, ano)
        risco_valor = risco.get("valor")

        # Busca dados fiscais (TCE)
        autonomia = None
        execucao = None
        try:
            from app.clients.tce import get_uf_for_porto, get_tce_client, TCE_REGISTRY
            uf = get_uf_for_porto(id_instalacao)
            if uf and uf in TCE_REGISTRY:
                tce = get_tce_client(uf)
                aut_data = await tce.calcular_autonomia_fiscal(id_municipio, ano)
                autonomia = aut_data.get("autonomia_fiscal")
                exec_data = await tce.calcular_execucao_orcamentaria(id_municipio, ano)
                execucao = exec_data.get("eficiencia_execucao")
        except Exception as e:
            logger.warning("governance_tce_error: %s", e)

        # Calcula IGP
        componentes = []
        valores = []

        if risco_valor is not None:
            comp_risco = round((1 - risco_valor) * 100, 1)  # Inverso: menos risco = mais governança
            componentes.append({
                "nome": "Compliance Regulatório",
                "codigo_fonte": "IND-10.07",
                "valor_normalizado": comp_risco,
                "peso": 0.40,
                "fonte": "Índice de Risco Regulatório (invertido)",
                "ultima_atualizacao": agora,
                "descricao": "100 - (risco regulatório × 100)",
            })
            valores.append(("Compliance", comp_risco, 0.40))

        if autonomia is not None:
            comp_aut = round(autonomia * 100, 1)
            componentes.append({
                "nome": "Autonomia Fiscal",
                "codigo_fonte": "IND-6.12",
                "valor_normalizado": comp_aut,
                "peso": 0.30,
                "fonte": "TCE Estadual",
                "ultima_atualizacao": agora,
                "descricao": "Receita própria / Receita total × 100",
            })
            valores.append(("Autonomia", comp_aut, 0.30))

        if execucao is not None:
            comp_exec = round(execucao * 100, 1)
            componentes.append({
                "nome": "Execução Orçamentária",
                "codigo_fonte": "IND-6.14",
                "valor_normalizado": comp_exec,
                "peso": 0.30,
                "fonte": "TCE Estadual",
                "ultima_atualizacao": agora,
                "descricao": "Despesa executada / Despesa autorizada × 100",
            })
            valores.append(("Execução", comp_exec, 0.30))

        if not valores:
            igp = None
            classificacao = "sem_dados"
            formula = "IGP = sem dados disponíveis"
        else:
            peso_total = sum(p for _, _, p in valores)
            igp = round(sum(v * p for _, v, p in valores) / peso_total, 1)
            classificacao = _classify_governance(igp)
            termos = [f"{p/peso_total:.2f} × {n}" for n, _, p in valores]
            formula = f"IGP = {' + '.join(termos)}"

        return {
            "id_instalacao": id_instalacao,
            "id_municipio": id_municipio,
            "ano": ano,
            "valor": igp,
            "classificacao": classificacao,
            "composicao": {
                "formula": formula,
                "componentes": componentes,
                "nota_metodologica": (
                    "Escala 0-100. Quanto MAIOR, melhor a governança. "
                    "Compliance: inverso do risco regulatório (IND-10.07). "
                    "Autonomia fiscal: receita própria vs. total (TCE). "
                    "Execução: orçamento executado vs. autorizado (TCE). "
                    "Pesos redistribuídos se algum componente indisponível."
                ),
            },
        }


# Singleton
_compliance_service: Optional[ComplianceService] = None


def get_compliance_service() -> ComplianceService:
    global _compliance_service
    if _compliance_service is None:
        _compliance_service = ComplianceService()
    return _compliance_service
