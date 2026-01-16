"""
Serviço de geração de relatórios DOCX.

Orquestra a consulta de dados e geração de documentos Word.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from .docx_generator import DOCXGenerator
from .templates import MODULE_TEMPLATES, get_module_template, format_value


class ReportService:
    """Serviço para geração de relatórios de módulos."""

    def __init__(self):
        """Inicializa o serviço."""
        self.generator = None

    def _get_label_from_data(self, item: Dict[str, Any]) -> str:
        """Extrai o label (nome) de um item de dados."""
        return (
            item.get("nome_municipio") or
            item.get("municipio") or
            item.get("porto_atracacao") or
            item.get("id_instalacao") or
            item.get("id_municipio") or
            "N/A"
        )

    def _get_value_from_data(self, item: Dict[str, Any], value_field: str) -> Any:
        """Extrai o valor de um item de dados."""
        return (
            item.get(value_field) or
            item.get("valor") or
            item.get("total") or
            item.get("value") or
            0
        )

    def generate_module_report(
        self,
        module_code: str,
        data: Dict[str, List[Dict[str, Any]]],
        porto: str = "",
        ano: Optional[int] = None,
    ) -> tuple[bytes, str]:
        """
        Gera um relatório DOCX completo para um módulo.

        Args:
            module_code: Código do módulo (IND-1, IND-2, etc.)
            data: Dicionário com dados dos indicadores {indicator_code: [items]}
            porto: Nome do porto/filtro
            ano: Ano dos dados

        Returns:
            Tupla (bytes_do_documento, nome_arquivo)
        """
        self.generator = DOCXGenerator()
        template = get_module_template(module_code)

        if not template:
            raise ValueError(f"Módulo {module_code} não encontrado")

        # Cabeçalho
        self.generator.add_header(
            title=template["name"],
            subtitle=template["description"],
            porto=porto,
            ano=ano,
        )

        # Resumo executivo com cards de totais
        self._add_summary_section(module_code, data, template)

        # Tabela detalhada de indicadores
        self._add_detailed_table(module_code, data, template)

        # Notas metodológicas
        self._add_methodological_notes(module_code)

        # Gera o documento
        doc_bytes = self.generator.save()
        filename = self.generator.get_filename(template["name"], porto, ano)

        return doc_bytes, filename

    def _add_summary_section(
        self,
        module_code: str,
        data: Dict[str, List[Dict[str, Any]]],
        template: Dict,
    ):
        """Adiciona seção de resumo executivo."""
        self.generator.add_section("Resumo Executivo", level=2)

        # Cria cards com os valores agregados por indicador
        for indicator_def in template["indicators"]:
            indicator_code = indicator_def["code"]
            items = data.get(indicator_code, [])

            if not items:
                continue

            # Título do indicador
            self.generator.add_text(
                f"{indicator_code} - {indicator_def['name']}",
                bold=True,
            )

            # Calcula total/valor agregado
            value_field = self._guess_value_field(items[0])
            total = sum(
                self._get_value_from_data(item, value_field) or 0
                for item in items
                if isinstance(self._get_value_from_data(item, value_field), (int, float))
            )

            # Mostra resumo
            if total > 0 or len(items) > 0:
                count_text = f"{len(items)} registro(s)"
                if isinstance(total, (int, float)) and total > 0:
                    count_text += f" | Total: {format_value(total, indicator_def['unit'])}"
                self.generator.add_text(count_text, italic=True)

    def _add_detailed_table(
        self,
        module_code: str,
        data: Dict[str, List[Dict[str, Any]]],
        template: Dict,
    ):
        """Adiciona tabela detalhada com todos os dados."""
        self.generator.add_section("Dados Detalhados", level=2)

        # Cabeçalhos da tabela
        headers = ["Indicador", "Local", "Ano", "Unidade", "Valor"]

        # Monta linhas da tabela
        rows = []
        for indicator_def in template["indicators"]:
            indicator_code = indicator_def["code"]
            items = data.get(indicator_code, [])

            if not items:
                # Linha indicando ausência de dados
                rows.append([
                    indicator_code,
                    "-",
                    "-",
                    indicator_def["unit"],
                    "Sem dados",
                ])
                continue

            # Adiciona até 10 linhas por indicador (para não ficar muito grande)
            for item in items[:10]:
                value_field = self._guess_value_field(item)
                value = self._get_value_from_data(item, value_field)

                rows.append([
                    indicator_code,
                    self._get_label_from_data(item),
                    str(item.get("ano", "-")),
                    indicator_def["unit"],
                    format_value(value, indicator_def["unit"]),
                ])

            if len(items) > 10:
                rows.append([
                    "",
                    f"... ({len(items) - 10} registros adicionais)",
                    "",
                    "",
                    "",
                ])

        if rows:
            self.generator.add_indicator_table(headers, rows)
        else:
            self.generator.add_text("Nenhum dado disponível para o período selecionado.")

    def _add_methodological_notes(self, module_code: str):
        """Adiciona notas metodológicas."""
        self.generator.add_page_break()
        self.generator.add_section("Notas Metodológicas", level=2)

        notes = [
            "Fonte de dados: ANTAQ (Agência Nacional de Transportes Aquaviários), "
            "IBGE, RAIS, Comex Stat e outras fontes oficiais.",
            "Os indicadores seguem metodologia harmonizada com padrões internacionais (UNCTAD).",
            "Valores podem estar sujeitos a revisão conforme atualização das fontes de dados.",
            "Para mais informações, consulte a documentação técnica do sistema.",
        ]

        self.generator.add_bullet_list(notes)

    def _guess_value_field(self, item: Dict[str, Any]) -> str:
        """Tenta identificar o campo de valor em um item."""
        # Campos comuns em ordem de prioridade
        possible_fields = [
            "valor",
            "total",
            "valor_exportacoes_usd",
            "valor_importacoes_usd",
            "balanca_comercial_usd",
            "peso_liquido_exportacoes_kg",
            "peso_liquido_importacoes_kg",
            "market_share_pct",
            "valor_medio_usd_kg",
            "tonelagem_total",
            "carga_media_atracacao",
            "produtividade_ton_hora",
            "percentual",
            "indice_sazonalidade",
            "empregos_portuarios",
            "percentual_feminino",
            "taxa_temporario",
            "salario_medio",
            "massa_salarial_anual",
            "ton_por_empregado",
            "pib_por_empregado_portuario",
            "idade_media",
            "participacao_emprego_local",
            "pib_municipal",
            "pib_per_capita",
            "populacao",
            "pib_servicos_percentual",
            "pib_industria_percentual",
            "intensidade_portuaria",
            "intensidade_comercial",
            "concentracao_emprego_pct",
            "concentracao_salarial_pct",
            "crescimento_pib_percentual",
            "crescimento_tonelagem_pct",
            "crescimento_empregos_pct",
            "crescimento_comercio_pct",
            "arrecadacao_icms",
            "arrecadacao_iss",
            "receita_total",
            "receita_per_capita",
            "crescimento_receita_pct",
            "icms_por_tonelada",
            "indice_eficiencia",
            "indice_relevancia",
            "indice_integracao",
            "indice_concentracao",
        ]

        for field in possible_fields:
            if field in item and item[field] is not None:
                return field

        return "valor"  # Default

    def generate_single_indicator_report(
        self,
        module_code: str,
        indicator_code: str,
        data: List[Dict[str, Any]],
        porto: str = "",
        ano: Optional[int] = None,
    ) -> tuple[bytes, str]:
        """
        Gera um relatório DOCX para um único indicador.

        Args:
            module_code: Código do módulo
            indicator_code: Código do indicador
            data: Lista de itens do indicador
            porto: Nome do porto/filtro
            ano: Ano dos dados

        Returns:
            Tupla (bytes_do_documento, nome_arquivo)
        """
        self.generator = DOCXGenerator()
        template = get_module_template(module_code)

        if not template:
            raise ValueError(f"Módulo {module_code} não encontrado")

        # Encontra o indicador no template
        indicator_def = None
        for ind in template["indicators"]:
            if ind["code"] == indicator_code:
                indicator_def = ind
                break

        if not indicator_def:
            raise ValueError(f"Indicador {indicator_code} não encontrado no módulo")

        # Cabeçalho
        self.generator.add_header(
            title=f"{indicator_code} - {indicator_def['name']}",
            subtitle=template["description"],
            porto=porto,
            ano=ano,
        )

        # Descrição do indicador
        self.generator.add_text(
            f"Descrição: {indicator_def['description']}",
            italic=True,
        )
        self.generator.add_text(f"Unidade: {indicator_def['unit']}")
        self.generator.add_text("")  # Espaçamento

        # Tabela de dados
        if data:
            headers = ["Local", "Ano", "Valor"]
            value_field = self._guess_value_field(data[0])

            rows = []
            for item in data[:50]:  # Limita a 50 linhas
                rows.append([
                    self._get_label_from_data(item),
                    str(item.get("ano", "-")),
                    format_value(
                        self._get_value_from_data(item, value_field),
                        indicator_def["unit"]
                    ),
                ])

            self.generator.add_indicator_table(headers, rows)
        else:
            self.generator.add_text("Nenhum dado disponível para o período selecionado.")

        # Notas
        self._add_methodological_notes(module_code)

        doc_bytes = self.generator.save()
        filename = f"{indicator_code}_{porto or 'todos'}_{ano or 'todos'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"

        return doc_bytes, filename
