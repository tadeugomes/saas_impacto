"""
Serviço de Indicadores do Módulo 1 - Operações de Navios.

Este serviço encapsula a lógica de negócio para consulta e cálculo
dos indicadores de operações de navios via BigQuery.
"""

from typing import Optional, List
from datetime import datetime
import logging

from app.db.bigquery.client import (
    BigQueryClient,
    BigQueryError,
    get_bigquery_client,
)
from app.db.bigquery.queries import (
    query_tempo_medio_espera,
    query_tempo_medio_porto,
    query_tempo_bruto_atracacao,
    query_tempo_liquido_operacao,
    query_taxa_ocupacao_bercos,
    query_tempo_ocioso_turno,
    query_arqueacao_bruta_media,
    query_comprimento_medio_navios,
    query_calado_maximo_operacional,
    query_distribuicao_tipo_navio,
    query_numero_atracacoes,
    query_indice_paralisacao,
    query_resumo_operacoes_navios,
)
from app.schemas.indicators import (
    TempoMedioEsperaResponse,
    TempoMedioPortoResponse,
    TempoBrutoAtracacaoResponse,
    TempoLiquidoOperacaoResponse,
    TaxaOcupacaoBercoesResponse,
    TempoOciosoTurnoResponse,
    ArqueacaoBrutaMediaResponse,
    ComprimentoMedioNavioResponse,
    CaladoMaximoOperacionalResponse,
    DistribuicaoTipoNavioResponse,
    TipoNavioDistributionItem,
    NumeroAtracacoesResponse,
    IndiceParalisacaoResponse,
    OperacoesNaviosResumoResponse,
    OperacoesNaviosResumoItem,
    OperacoesNaviosRequest,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Metadados dos Indicadores
# ============================================================================

INDICATOR_METADATA = {
    "IND-1.01": {
        "codigo": "IND-1.01",
        "nome": "Tempo Médio de Espera",
        "unidade": "Horas",
        "unctad": True,
        "descricao": "Tempo médio entre a chegada e o início da atracação",
    },
    "IND-1.02": {
        "codigo": "IND-1.02",
        "nome": "Tempo Médio em Porto",
        "unidade": "Horas",
        "unctad": True,
        "descricao": "Tempo médio total no porto (atracado + espera)",
    },
    "IND-1.03": {
        "codigo": "IND-1.03",
        "nome": "Tempo Bruto de Atracação",
        "unidade": "Horas",
        "unctad": True,
        "descricao": "Tempo médio desde atracação até desatracação",
    },
    "IND-1.04": {
        "codigo": "IND-1.04",
        "nome": "Tempo Líquido de Operação",
        "unidade": "Horas",
        "unctad": True,
        "descricao": "Tempo efetivo de operação com carga",
    },
    "IND-1.05": {
        "codigo": "IND-1.05",
        "nome": "Taxa de Ocupação de Berços",
        "unidade": "%",
        "unctad": True,
        "descricao": "Percentual médio de ocupação dos berços",
    },
    "IND-1.06": {
        "codigo": "IND-1.06",
        "nome": "Tempo Ocioso Médio por Turno",
        "unidade": "Horas",
        "unctad": True,
        "descricao": "Tempo médio de paralisação durante operação",
    },
    "IND-1.07": {
        "codigo": "IND-1.07",
        "nome": "Arqueação Bruta Média",
        "unidade": "GT",
        "unctad": True,
        "descricao": "Tamanho médio dos navios em Gross Tonnage",
    },
    "IND-1.08": {
        "codigo": "IND-1.08",
        "nome": "Comprimento Médio de Navios",
        "unidade": "Metros",
        "unctad": True,
        "descricao": "Comprimento médio dos navios atracados",
    },
    "IND-1.09": {
        "codigo": "IND-1.09",
        "nome": "Calado Máximo Operacional",
        "unidade": "Metros",
        "unctad": True,
        "descricao": "Maior calado já registrado na instalação",
    },
    "IND-1.10": {
        "codigo": "IND-1.10",
        "nome": "Distribuição por Tipo de Navio",
        "unidade": "%",
        "unctad": True,
        "descricao": "Distribuição de atracações por tipo de navegação",
    },
    "IND-1.11": {
        "codigo": "IND-1.11",
        "nome": "Número de Atracações",
        "unidade": "Contagem",
        "unctad": False,
        "descricao": "Total de atracações no período",
    },
    "IND-1.12": {
        "codigo": "IND-1.12",
        "nome": "Índice de Paralisação",
        "unidade": "%",
        "unctad": False,
        "descricao": "Percentual do tempo de paralisação sobre tempo atracado",
    },
}


# ============================================================================
# Serviço de Indicadores
# ============================================================================

class ShipOperationsIndicatorService:
    """
    Serviço para consultas de indicadores de operações de navios.

    Este serviço fornece métodos para consultar cada indicador do Módulo 1,
    com suporte a filtros por instalação e período.
    """

    def __init__(self, bq_client: Optional[BigQueryClient] = None):
        """
        Inicializa o serviço.

        Args:
            bq_client: Cliente BigQuery (usa singleton se não informado)
        """
        self.bq_client = bq_client or get_bigquery_client()

    async def _execute_query(
        self,
        query_func: callable,
        **kwargs
    ) -> List[dict]:
        """
        Executa uma query e retorna os resultados.

        Args:
            query_func: Função que gera a query SQL
            **kwargs: Parâmetros para a função de query

        Returns:
            Lista de dicionários com os resultados
        """
        query = query_func(**kwargs)

        try:
            results = await self.bq_client.execute_query(query)
            logger.info(f"Query executada com sucesso: {len(results)} registros")
            return results
        except BigQueryError as e:
            logger.error(f"Erro na query BigQuery: {e.message}")
            raise

    # ========================================================================
    # IND-1.01: Tempo Médio de Espera
    # ========================================================================

    async def get_tempo_medio_espera(
        self,
        id_instalacao: Optional[str] = None,
        ano: Optional[int] = None,
        ano_inicio: Optional[int] = None,
        ano_fim: Optional[int] = None,
    ) -> List[TempoMedioEsperaResponse]:
        """
        Consulta o IND-1.01: Tempo Médio de Espera.

        Args:
            id_instalacao: Filtro por ID da instalação
            ano: Ano específico
            ano_inicio: Ano inicial do período
            ano_fim: Ano final do período

        Returns:
            Lista de resultados com tempos médios de espera
        """
        results = await self._execute_query(
            query_tempo_medio_espera,
            id_instalacao=id_instalacao,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )

        meta = INDICATOR_METADATA["IND-1.01"]
        return [
            TempoMedioEsperaResponse(
                codigo_indicador=meta["codigo"],
                nome=meta["nome"],
                unidade=meta["unidade"],
                unctad=meta["unctad"],
                id_instalacao=row["id_instalacao"],
                ano=row["ano"],
                tempo_medio_espera_horas=float(row["tempo_medio_espera_horas"]),
            )
            for row in results
        ]

    # ========================================================================
    # IND-1.02: Tempo Médio em Porto
    # ========================================================================

    async def get_tempo_medio_porto(
        self,
        id_instalacao: Optional[str] = None,
        ano: Optional[int] = None,
        ano_inicio: Optional[int] = None,
        ano_fim: Optional[int] = None,
    ) -> List[TempoMedioPortoResponse]:
        """Consulta o IND-1.02: Tempo Médio em Porto."""
        results = await self._execute_query(
            query_tempo_medio_porto,
            id_instalacao=id_instalacao,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )

        meta = INDICATOR_METADATA["IND-1.02"]
        return [
            TempoMedioPortoResponse(
                codigo_indicador=meta["codigo"],
                nome=meta["nome"],
                unidade=meta["unidade"],
                unctad=meta["unctad"],
                id_instalacao=row["id_instalacao"],
                ano=row["ano"],
                tempo_medio_porto_horas=float(row["tempo_medio_porto_horas"]),
            )
            for row in results
        ]

    # ========================================================================
    # IND-1.03: Tempo Bruto de Atracação
    # ========================================================================

    async def get_tempo_bruto_atracacao(
        self,
        id_instalacao: Optional[str] = None,
        ano: Optional[int] = None,
        ano_inicio: Optional[int] = None,
        ano_fim: Optional[int] = None,
    ) -> List[TempoBrutoAtracacaoResponse]:
        """Consulta o IND-1.03: Tempo Bruto de Atracação."""
        results = await self._execute_query(
            query_tempo_bruto_atracacao,
            id_instalacao=id_instalacao,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )

        meta = INDICATOR_METADATA["IND-1.03"]
        return [
            TempoBrutoAtracacaoResponse(
                codigo_indicador=meta["codigo"],
                nome=meta["nome"],
                unidade=meta["unidade"],
                unctad=meta["unctad"],
                id_instalacao=row["id_instalacao"],
                ano=row["ano"],
                tempo_bruto_atracacao_horas=float(row["tempo_bruto_atracacao_horas"]),
            )
            for row in results
        ]

    # ========================================================================
    # IND-1.04: Tempo Líquido de Operação
    # ========================================================================

    async def get_tempo_liquido_operacao(
        self,
        id_instalacao: Optional[str] = None,
        ano: Optional[int] = None,
        ano_inicio: Optional[int] = None,
        ano_fim: Optional[int] = None,
    ) -> List[TempoLiquidoOperacaoResponse]:
        """Consulta o IND-1.04: Tempo Líquido de Operação."""
        results = await self._execute_query(
            query_tempo_liquido_operacao,
            id_instalacao=id_instalacao,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )

        meta = INDICATOR_METADATA["IND-1.04"]
        return [
            TempoLiquidoOperacaoResponse(
                codigo_indicador=meta["codigo"],
                nome=meta["nome"],
                unidade=meta["unidade"],
                unctad=meta["unctad"],
                id_instalacao=row["id_instalacao"],
                ano=row["ano"],
                tempo_liquido_operacao_horas=float(row["tempo_liquido_operacao_horas"]),
            )
            for row in results
        ]

    # ========================================================================
    # IND-1.05: Taxa de Ocupação de Berços
    # ========================================================================

    async def get_taxa_ocupacao_bercos(
        self,
        id_instalacao: Optional[str] = None,
        ano: Optional[int] = None,
        ano_inicio: Optional[int] = None,
        ano_fim: Optional[int] = None,
    ) -> List[TaxaOcupacaoBercoesResponse]:
        """Consulta o IND-1.05: Taxa de Ocupação de Berços."""
        results = await self._execute_query(
            query_taxa_ocupacao_bercos,
            id_instalacao=id_instalacao,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )

        meta = INDICATOR_METADATA["IND-1.05"]
        return [
            TaxaOcupacaoBercoesResponse(
                codigo_indicador=meta["codigo"],
                nome=meta["nome"],
                unidade=meta["unidade"],
                unctad=meta["unctad"],
                id_instalacao=row["id_instalacao"],
                ano=row["ano"],
                taxa_ocupacao_percentual=float(row["taxa_ocupacao_percentual"]),
            )
            for row in results
        ]

    # ========================================================================
    # IND-1.06: Tempo Ocioso Médio por Turno
    # ========================================================================

    async def get_tempo_ocioso_turno(
        self,
        id_instalacao: Optional[str] = None,
        ano: Optional[int] = None,
        ano_inicio: Optional[int] = None,
        ano_fim: Optional[int] = None,
    ) -> List[TempoOciosoTurnoResponse]:
        """Consulta o IND-1.06: Tempo Ocioso Médio por Turno."""
        results = await self._execute_query(
            query_tempo_ocioso_turno,
            id_instalacao=id_instalacao,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )

        meta = INDICATOR_METADATA["IND-1.06"]
        return [
            TempoOciosoTurnoResponse(
                codigo_indicador=meta["codigo"],
                nome=meta["nome"],
                unidade=meta["unidade"],
                unctad=meta["unctad"],
                id_instalacao=row["id_instalacao"],
                ano=row["ano"],
                tempo_ocioso_medio_horas=float(row["tempo_ocioso_medio_horas"]),
            )
            for row in results
        ]

    # ========================================================================
    # IND-1.07: Arqueação Bruta Média
    # ========================================================================

    async def get_arqueacao_bruta_media(
        self,
        id_instalacao: Optional[str] = None,
        ano: Optional[int] = None,
        ano_inicio: Optional[int] = None,
        ano_fim: Optional[int] = None,
    ) -> List[ArqueacaoBrutaMediaResponse]:
        """Consulta o IND-1.07: Arqueação Bruta Média."""
        results = await self._execute_query(
            query_arqueacao_bruta_media,
            id_instalacao=id_instalacao,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )

        meta = INDICATOR_METADATA["IND-1.07"]
        return [
            ArqueacaoBrutaMediaResponse(
                codigo_indicador=meta["codigo"],
                nome=meta["nome"],
                unidade=meta["unidade"],
                unctad=meta["unctad"],
                id_instalacao=row["id_instalacao"],
                ano=row["ano"],
                arqueacao_bruta_media=float(row["arqueacao_bruta_media"]),
            )
            for row in results
        ]

    # ========================================================================
    # IND-1.08: Comprimento Médio de Navios
    # ========================================================================

    async def get_comprimento_medio_navios(
        self,
        id_instalacao: Optional[str] = None,
        ano: Optional[int] = None,
        ano_inicio: Optional[int] = None,
        ano_fim: Optional[int] = None,
    ) -> List[ComprimentoMedioNavioResponse]:
        """Consulta o IND-1.08: Comprimento Médio de Navios."""
        results = await self._execute_query(
            query_comprimento_medio_navios,
            id_instalacao=id_instalacao,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )

        meta = INDICATOR_METADATA["IND-1.08"]
        return [
            ComprimentoMedioNavioResponse(
                codigo_indicador=meta["codigo"],
                nome=meta["nome"],
                unidade=meta["unidade"],
                unctad=meta["unctad"],
                id_instalacao=row["id_instalacao"],
                ano=row["ano"],
                comprimento_medio_metros=float(row["comprimento_medio_metros"]),
            )
            for row in results
        ]

    # ========================================================================
    # IND-1.09: Calado Máximo Operacional
    # ========================================================================

    async def get_calado_maximo_operacional(
        self,
        id_instalacao: Optional[str] = None,
    ) -> List[CaladoMaximoOperacionalResponse]:
        """Consulta o IND-1.09: Calado Máximo Operacional."""
        results = await self._execute_query(
            query_calado_maximo_operacional,
            id_instalacao=id_instalacao,
        )

        meta = INDICATOR_METADATA["IND-1.09"]
        return [
            CaladoMaximoOperacionalResponse(
                codigo_indicador=meta["codigo"],
                nome=meta["nome"],
                unidade=meta["unidade"],
                unctad=meta["unctad"],
                id_instalacao=row["id_instalacao"],
                calado_maximo_metros=float(row["calado_maximo_metros"]),
            )
            for row in results
        ]

    # ========================================================================
    # IND-1.10: Distribuição por Tipo de Navio
    # ========================================================================

    async def get_distribuicao_tipo_navio(
        self,
        id_instalacao: Optional[str] = None,
        ano: Optional[int] = None,
    ) -> List[DistribuicaoTipoNavioResponse]:
        """Consulta o IND-1.10: Distribuição por Tipo de Navio."""
        results = await self._execute_query(
            query_distribuicao_tipo_navio,
            id_instalacao=id_instalacao,
            ano=ano,
        )

        # Agrupa resultados por instalação/ano
        grouped = {}
        for row in results:
            key = (row["id_instalacao"], row["ano"])
            if key not in grouped:
                meta = INDICATOR_METADATA["IND-1.10"]
                grouped[key] = {
                    "codigo_indicador": meta["codigo"],
                    "nome": meta["nome"],
                    "unidade": meta["unidade"],
                    "unctad": meta["unctad"],
                    "id_instalacao": row["id_instalacao"],
                    "ano": row["ano"],
                    "distribuicao": [],
                }
            grouped[key]["distribuicao"].append(
                TipoNavioDistributionItem(
                    tipo_navegacao=row["tipo_navegacao"],
                    qtd_atracacoes=int(row["qtd_atracacoes"]),
                    percentual=float(row["percentual"]),
                )
            )

        return [DistribuicaoTipoNavioResponse(**v) for v in grouped.values()]

    # ========================================================================
    # IND-1.11: Número de Atracações
    # ========================================================================

    async def get_numero_atracacoes(
        self,
        id_instalacao: Optional[str] = None,
        ano: Optional[int] = None,
        ano_inicio: Optional[int] = None,
        ano_fim: Optional[int] = None,
    ) -> List[NumeroAtracacoesResponse]:
        """Consulta o IND-1.11: Número de Atracações."""
        results = await self._execute_query(
            query_numero_atracacoes,
            id_instalacao=id_instalacao,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )

        meta = INDICATOR_METADATA["IND-1.11"]
        return [
            NumeroAtracacoesResponse(
                codigo_indicador=meta["codigo"],
                nome=meta["nome"],
                unidade=meta["unidade"],
                unctad=meta["unctad"],
                id_instalacao=row["id_instalacao"],
                ano=row["ano"],
                total_atracacoes=int(row["total_atracacoes"]),
            )
            for row in results
        ]

    # ========================================================================
    # IND-1.12: Índice de Paralisação
    # ========================================================================

    async def get_indice_paralisacao(
        self,
        id_instalacao: Optional[str] = None,
        ano: Optional[int] = None,
        ano_inicio: Optional[int] = None,
        ano_fim: Optional[int] = None,
    ) -> List[IndiceParalisacaoResponse]:
        """Consulta o IND-1.12: Índice de Paralisação."""
        results = await self._execute_query(
            query_indice_paralisacao,
            id_instalacao=id_instalacao,
            ano=ano,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )

        meta = INDICATOR_METADATA["IND-1.12"]
        return [
            IndiceParalisacaoResponse(
                codigo_indicador=meta["codigo"],
                nome=meta["nome"],
                unidade=meta["unidade"],
                unctad=meta["unctad"],
                id_instalacao=row["id_instalacao"],
                ano=row["ano"],
                indice_paralisacao_percentual=row.get("indice_paralisacao_percentual"),
            )
            for row in results
        ]

    # ========================================================================
    # Resumo Consolidado
    # ========================================================================

    async def get_resumo(
        self,
        id_instalacao: str,
        ano: int,
    ) -> Optional[OperacoesNaviosResumoResponse]:
        """
        Retorna todos os indicadores consolidados para uma instalação/ano.

        Args:
            id_instalacao: ID da instalação
            ano: Ano de referência

        Returns:
            Resumo consolidado com todos os indicadores
        """
        results = await self._execute_query(
            query_resumo_operacoes_navios,
            id_instalacao=id_instalacao,
            ano=ano,
        )

        if not results:
            return None

        row = results[0]

        indicadores = [
            OperacoesNaviosResumoItem(
                codigo_indicador="IND-1.01",
                nome=INDICATOR_METADATA["IND-1.01"]["nome"],
                valor=float(row["ind_101_tempo_espera_horas"]),
                unidade=INDICATOR_METADATA["IND-1.01"]["unidade"],
            ),
            OperacoesNaviosResumoItem(
                codigo_indicador="IND-1.02",
                nome=INDICATOR_METADATA["IND-1.02"]["nome"],
                valor=float(row["ind_102_tempo_porto_horas"]),
                unidade=INDICATOR_METADATA["IND-1.02"]["unidade"],
            ),
            OperacoesNaviosResumoItem(
                codigo_indicador="IND-1.03",
                nome=INDICATOR_METADATA["IND-1.03"]["nome"],
                valor=float(row["ind_103_tempo_bruto_horas"]),
                unidade=INDICATOR_METADATA["IND-1.03"]["unidade"],
            ),
            OperacoesNaviosResumoItem(
                codigo_indicador="IND-1.04",
                nome=INDICATOR_METADATA["IND-1.04"]["nome"],
                valor=float(row["ind_104_tempo_liquido_horas"]),
                unidade=INDICATOR_METADATA["IND-1.04"]["unidade"],
            ),
            OperacoesNaviosResumoItem(
                codigo_indicador="IND-1.05",
                nome=INDICATOR_METADATA["IND-1.05"]["nome"],
                valor=float(row["ind_105_taxa_ocupacao_pct"]),
                unidade=INDICATOR_METADATA["IND-1.05"]["unidade"],
            ),
            OperacoesNaviosResumoItem(
                codigo_indicador="IND-1.06",
                nome=INDICATOR_METADATA["IND-1.06"]["nome"],
                valor=float(row["ind_106_tempo_ocioso_horas"]),
                unidade=INDICATOR_METADATA["IND-1.06"]["unidade"],
            ),
            OperacoesNaviosResumoItem(
                codigo_indicador="IND-1.07",
                nome=INDICATOR_METADATA["IND-1.07"]["nome"],
                valor=float(row["ind_107_arqueacao_media_gt"]),
                unidade=INDICATOR_METADATA["IND-1.07"]["unidade"],
            ),
            OperacoesNaviosResumoItem(
                codigo_indicador="IND-1.08",
                nome=INDICATOR_METADATA["IND-1.08"]["nome"],
                valor=float(row["ind_108_comprimento_medio_m"]),
                unidade=INDICATOR_METADATA["IND-1.08"]["unidade"],
            ),
            OperacoesNaviosResumoItem(
                codigo_indicador="IND-1.09",
                nome=INDICATOR_METADATA["IND-1.09"]["nome"],
                valor=float(row["ind_109_calado_maximo_m"]),
                unidade=INDICATOR_METADATA["IND-1.09"]["unidade"],
            ),
            OperacoesNaviosResumoItem(
                codigo_indicador="IND-1.11",
                nome=INDICATOR_METADATA["IND-1.11"]["nome"],
                valor=float(row["ind_111_total_atracacoes"]),
                unidade=INDICATOR_METADATA["IND-1.11"]["unidade"],
            ),
            OperacoesNaviosResumoItem(
                codigo_indicador="IND-1.12",
                nome=INDICATOR_METADATA["IND-1.12"]["nome"],
                valor=float(row["ind_112_indice_paralisacao_pct"]),
                unidade=INDICATOR_METADATA["IND-1.12"]["unidade"],
            ),
        ]

        return OperacoesNaviosResumoResponse(
            codigo_indicador="RESUMO-M1",
            nome="Resumo Operações de Navios",
            unidade="Múltiplo",
            unctad=False,
            id_instalacao=id_instalacao,
            ano=ano,
            indicadores=indicadores,
        )


# ============================================================================
# Singleton do serviço
# ============================================================================

_service_instance: Optional[ShipOperationsIndicatorService] = None


def get_indicator_service() -> ShipOperationsIndicatorService:
    """Retorna instância singleton do serviço de indicadores."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ShipOperationsIndicatorService()
    return _service_instance
