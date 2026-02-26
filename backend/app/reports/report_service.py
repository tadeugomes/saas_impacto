"""
Serviço de geração de relatórios DOCX.

Orquestra a consulta de dados e geração de documentos Word.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from collections.abc import Mapping
from io import BytesIO

from .docx_generator import DOCXGenerator
from .templates import get_module_template, format_value


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
            "correlacao_tonelagem_pib",
            "correlacao_tonelagem_empregos",
            "correlacao_comercio_pib",
            "elasticidade_tonelagem_pib",
            "participacao_pib_regional_pct",
            "crescimento_relativo_uf_pct",
            "razao_emprego_total_portuario",
            "indice_concentracao_portuaria",
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

    # ------------------------------------------------------------------
    # Relatórios de análises causais (Módulo 5)
    # ------------------------------------------------------------------

    def generate_impact_analysis_report(
        self,
        analysis: Mapping[str, Any] | object,
    ) -> tuple[BytesIO, str]:
        """
        Gera um relatório DOCX para uma análise causal (DiD / IV / Panel IV / etc).

        Aceita um objeto do tipo Pydantic ORM/dict com as chaves normalmente
        retornadas por `EconomicImpactAnalysisDetailResponse`.
        """
        analysis_data = self._coerce_mapping(analysis)
        result_summary = dict(self._coerce_mapping(analysis_data.get("result_summary") or {}))
        result_full, artifact_warnings = self._resolve_result_full(analysis_data)
        request_params = self._coerce_mapping(analysis_data.get("request_params") or {})

        if artifact_warnings:
            warnings = list(result_summary.get("warnings", []))
            warnings.extend(artifact_warnings)
            result_summary["warnings"] = warnings

        analysis_id = str(analysis_data.get("id") or "desconhecida")
        method = str(analysis_data.get("method") or "did").lower()
        status = str(analysis_data.get("status") or "desconhecido").lower()

        self.generator = DOCXGenerator()
        title = f"Análise de Impacto Econômico — {method.upper()}"
        subtitle = f"ID: {analysis_id} | status: {status}"
        self.generator.add_header(title=title, subtitle=subtitle)

        self._add_impact_executive_summary(result_summary, request_params)
        self._add_impact_method_section(method)
        self._add_impact_metadata_section(analysis_data, request_params)
        self._add_impact_configuration_section(method, request_params, analysis_data)
        self._add_impact_limitations_section(method, result_summary, result_full)

        if status == "failed":
            self.generator.add_section("Falha na Execução", level=2)
            self.generator.add_text(
                f"Mensagem de erro: {analysis_data.get('error_message') or 'Não informado'}",
                italic=True,
            )
            doc_bytes = self.generator.save()
            return doc_bytes, f"analise_{analysis_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"

        outcomes = self._extract_outcomes(request_params, result_full)
        if not outcomes:
            self.generator.add_section("Resultado", level=2)
            self.generator.add_text("A análise não retornou outcomes para exportação.")
            doc_bytes = self.generator.save()
            return doc_bytes, f"analise_{analysis_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"

        self._add_impact_summary_section(method, outcomes, result_summary, result_full)
        self._add_impact_results_section(method, outcomes, result_full, result_summary)
        self._add_impact_diagnostics_section(method, outcomes, result_full)
        self._add_impact_quality_section(result_full)

        doc_bytes = self.generator.save()
        filename = f"analise_{method}_{analysis_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        return doc_bytes, filename

    def _resolve_result_full(
        self,
        analysis: Mapping[str, Any],
    ) -> tuple[Mapping[str, Any], list[str]]:
        """Resolve `result_full`, com fallback em `artifact_path` quando necessário."""
        inline_result = self._coerce_mapping(analysis.get("result_full") or {})
        if inline_result:
            return inline_result, []

        artifact_path = analysis.get("artifact_path")
        if not artifact_path:
            return {}, []

        loaded, warnings = self._load_result_from_artifact(str(artifact_path))
        return loaded, warnings

    def _load_result_from_artifact(self, artifact_path: str) -> tuple[Mapping[str, Any], list[str]]:
        """Carrega JSON do `artifact_path` e retorna payload e avisos operacionais."""
        path = (artifact_path or "").strip()
        if not path:
            return {}, ["artifact_path vazio; sem payload inline disponível."]

        if path.startswith("file://"):
            path = path[7:]

        if path.startswith("gs://"):
            return self._load_gcs_artifact(path)

        local_path = Path(path).expanduser()
        if not local_path.is_absolute():
            local_path = local_path.resolve()

        if not local_path.exists():
            return {}, [f"artifact_path não encontrado: {path}"]

        try:
            with local_path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:  # noqa: BLE001
            return {}, [f"Falha ao ler artifact_path {path}: {exc}"]

        if isinstance(payload, dict):
            return payload, []
        return {}, [f"artifact_path com formato inválido (não é JSON object): {path}"]

    def _load_gcs_artifact(self, artifact_path: str) -> tuple[Mapping[str, Any], list[str]]:
        """Carrega JSON de URI GCS (`gs://bucket/objeto`) sem quebrar ausência de SDK."""
        # Dependência opcional para manter compatibilidade; sem SDK, alerta amigável.
        try:
            from google.cloud import storage  # type: ignore
        except Exception:
            return {}, [
                "Dependência google-cloud-storage não instalada: resultado completo não carregado."
            ]

        try:
            _, bucket_and_blob = artifact_path.split("gs://", 1)
            bucket_name, blob_name = bucket_and_blob.split("/", 1)
        except ValueError as exc:
            return {}, [f"artifact_path inválido para GCS: {artifact_path} ({exc})"]

        try:
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            content = blob.download_as_text()
            payload = json.loads(content)
        except Exception as exc:  # noqa: BLE001
            return {}, [f"Falha ao carregar artifact_path GCS {artifact_path}: {exc}"]

        if isinstance(payload, dict):
            return payload, []
        return {}, [f"artifact_path GCS com formato inválido (não é JSON object): {artifact_path}"]

    def _add_impact_executive_summary(
        self,
        result_summary: Mapping[str, Any],
        request_params: Mapping[str, Any],
    ) -> None:
        """Painel executivo inicial com indicadores-chave."""
        self.generator.add_section("Resumo Executivo", level=2)

        treatment_year = request_params.get("treatment_year", "N/A")
        outcome = result_summary.get("outcome", "N/A")
        coef = result_summary.get("coef")
        p_value = result_summary.get("p_value")
        n_obs = result_summary.get("n_obs")

        rows = [
            ["Outcome principal", str(outcome)],
            ["Método", str(request_params.get("method", "—"))],
            ["Ano de tratamento", str(treatment_year)],
            ["Coeficiente", self._fmt(coef)],
            ["P-valor", self._fmt(p_value)],
            ["N observações", self._fmt(n_obs)],
        ]
        self.generator.add_indicator_table(["Item", "Valor"], rows)
        self.generator.add_text("Observação: coeficiente > 0 sugere efeito positivo do tratamento estimado.", italic=True)

    def _add_impact_method_section(self, method: str) -> None:
        """Explica a metodologia aplicada em linguagem interpretável."""
        self.generator.add_section("Metodologia", level=2)
        method = (method or "").lower()

        method_text = {
            "did": (
                "Diferenças-em-Diferenças com efeitos fixos (unidade e período), "
                "incluindo teste de tendências paralelas."
            ),
            "iv": (
                "Variáveis Instrumentais (2SLS) com diagnóstico de primeiro estágio e forma "
                "reduzida para robustez."
            ),
            "panel_iv": (
                "Panel IV com within-transformation e efeitos de tempo, incluindo especificações "
                "alternativas e robustez."
            ),
            "event_study": (
                "Event Study TWFE com coeficientes por período relativo ao tratamento (lead/lag)."
            ),
            "compare": (
                "Comparação entre estimativas de múltiplos métodos (DiD e IV), com recomendação de consistência."
            ),
        }.get(method, f"Método selecionado: {method}")

        interpretation = {
            "did": (
                "Adequado para cenários com grupos tratados e controle sob suposição de "
                "tendências paralelas."
            ),
            "iv": (
                "Interpretação depende da validade do instrumento: relevância, independência e "
                "ausência de efeitos diretos no outcome além do tratamento."
            ),
            "panel_iv": (
                "Busca robustez em painel com efeitos fixos por município/ano e variações de especificação."
            ),
            "event_study": (
                "Usado para avaliar dinâmica antes/depois do tratamento e investigar "
                "plausibilidade de causalidade por período."
            ),
            "compare": (
                "Recomendado para validar estabilidade de achado entre estratégias com suposições diferentes."
            ),
        }.get(method, "Método selecionado para a análise.")

        self.generator.add_text(method_text, italic=True)
        self.generator.add_text(f"Interpretação: {interpretation}")

    def _add_impact_configuration_section(
        self,
        method: str,
        request_params: Mapping[str, Any],
        analysis: Mapping[str, Any],
    ) -> None:
        """Registra parâmetros técnicos e opções de estimação."""
        self.generator.add_section("Configuração do Estudo", level=2)

        control_ids = request_params.get("control_ids")
        treated_ids = request_params.get("treated_ids")
        outcomes = request_params.get("outcomes")
        controls = request_params.get("controls")
        instrument = request_params.get("instrument")
        use_mart = request_params.get("use_mart")
        warnings = self._coerce_mapping(analysis.get("result_summary") or {}).get("warnings")
        if isinstance(warnings, list):
            warning_text = ", ".join(str(w) for w in warnings)
        elif warnings is None:
            warning_text = "N/A"
        else:
            warning_text = str(warnings)

        rows = [
            ["Método", str(method)],
            ["Escopo", str(request_params.get("scope", "N/A"))],
            [
                "Janela",
                f"{request_params.get('ano_inicio', 'N/A')} a {request_params.get('ano_fim', 'N/A')}",
            ],
            ["Municípios tratados", f"{len(treated_ids)}" if isinstance(treated_ids, list) else "N/A"],
            [
                "Municípios controle",
                (
                    f"{len(control_ids)}"
                    if isinstance(control_ids, list)
                    else "todos os demais"
                    if method in {"did", "event_study", "compare"}
                    else "N/A"
                ),
            ],
            ["Outcome(s)", ", ".join(outcomes) if isinstance(outcomes, list) else "N/A"],
            ["Controles", ", ".join(controls) if isinstance(controls, list) else "sem controles"],
            ["Instrumento", str(instrument) if instrument else "não informado"],
            ["Mart", "habilitado" if use_mart is True else "desabilitado" if use_mart is False else "N/A"],
            [
                "Fonte de resultado",
                (
                    "inline (result_full)"
                    if analysis.get("result_full")
                    else ("artifact_path" if analysis.get("artifact_path") else "N/A")
                ),
            ],
            ["Warnings", warning_text],
        ]

        self.generator.add_indicator_table(["Parâmetro", "Valor"], rows)

    def _add_impact_limitations_section(
        self,
        method: str,
        result_summary: Mapping[str, Any],
        result_full: Mapping[str, Any],
    ) -> None:
        """Regras de leitura e limitações da análise para reduzir risco de má-interpretação."""
        self.generator.add_section("Limitações e Interpretação", level=2)

        common = [
            "As estimativas dependem da qualidade/atualização dos dados de base.",
            "Não substitui evidência institucional, regulatória ou qualitativa local.",
            "O relatório foca evidência estatística e não declara causalidade causal definitiva.",
        ]

        method = (method or "").lower()
        method_limit = {
            "did": "Validação de tendência paralela é requisito central; sem isso, a inferência perde força.",
            "iv": "A validade do instrumento é crítica; viés pode ocorrer se houver efeito direto ou weak instrument.",
            "panel_iv": (
                "A interpretação depende da força do instrumento e da estabilidade das especificações "
                "alternativas."
            ),
            "event_study": (
                "Poucos períodos pré-tratamento reduzem a confiança na validação de ausência de "
                "viés antecipatório."
            ),
            "compare": "A recomendação é mais forte se métodos com premissas distintas convergirem.",
        }.get(method)

        bullets = [*common]
        if method_limit:
            bullets.append(method_limit)

        coef = result_summary.get("coef")
        if isinstance(coef, (int, float)):
            if coef > 0:
                bullets.append("Coeficiente positivo → efeito estimado favorável ao outcome após tratamento.")
            elif coef < 0:
                bullets.append("Coeficiente negativo → efeito estimado desfavorável ao outcome após tratamento.")

        p_value = result_summary.get("p_value")
        if isinstance(p_value, (int, float)):
            if p_value <= 0.01:
                bullets.append("P-valor muito baixo (< 1%): forte evidência estatística no desenho adotado.")
            elif p_value <= 0.05:
                bullets.append("P-valor baixo (< 5%): evidência estatística consistente no desenho adotado.")
            elif p_value <= 0.10:
                bullets.append("P-valor moderado (< 10%): relação estatística fraca; recomenda cautela.")
            else:
                bullets.append("P-valor >= 10%: ausência de evidência forte; resultado pode ser compatível com ruído.")

        n_obs = result_summary.get("n_obs")
        if isinstance(n_obs, (int, float)) and n_obs < 30:
            bullets.append("Poucas observações: variações podem ser sensíveis a outliers.")

        self.generator.add_bullet_list(bullets)

        # complemento técnico opcional, quando o engine forneceu metadados do modelo
        for outcome in result_full:
            payload = self._coerce_mapping(result_full.get(outcome))
            if not payload:
                continue
            model_info = self._coerce_mapping(payload.get("model_info"))
            formula = model_info.get("formula")
            if isinstance(formula, str) and formula:
                self.generator.add_text(f"Fórmula utilizada ({outcome}): {formula}")

    def _add_impact_quality_section(
        self,
        result_full: Mapping[str, Any],
    ) -> None:
        """Tabela textual com alertas de qualidade/diagnóstico recuperados do payload."""
        self.generator.add_section("Qualidade e Validação", level=2)

        warnings: list[str] = []
        for outcome, payload in result_full.items():
            payload_map = self._coerce_mapping(payload)
            if not payload_map:
                continue
            for key in ("warnings", "parallel_trends", "first_stage", "reduced_form", "placebo"):
                section = self._coerce_mapping(payload_map.get(key))
                warning = section.get("warning")
                interpretation = section.get("interpretation")
                if isinstance(warning, str):
                    warnings.append(f"{outcome} [{key}]: {warning}")
                if isinstance(interpretation, str):
                    warnings.append(f"{outcome} [{key}]: {interpretation}")

            first_stage = self._coerce_mapping(payload_map.get("first_stage"))
            if first_stage:
                f_stat = first_stage.get("f_stat")
                p_value = first_stage.get("f_pvalue")
                if isinstance(f_stat, (int, float)):
                    warnings.append(f"{outcome}: first-stage F={f_stat:.4f}")
                if isinstance(p_value, (int, float)):
                    warnings.append(f"{outcome}: first-stage p-value={p_value:.4f}")

            comparison = self._coerce_mapping(payload_map.get("comparison"))
            if comparison:
                consistency = comparison.get("consistency_assessment")
                if isinstance(consistency, Mapping):
                    status = consistency.get("status")
                    if status:
                        warnings.append(f"{outcome}: consistência={status}")

        if warnings:
            self.generator.add_bullet_list(list(dict.fromkeys(warnings)))
        else:
            self.generator.add_text("Sem alertas metodológicos adicionais identificados.")

    def _add_impact_metadata_section(
        self,
        analysis: Mapping[str, Any],
        request_params: Mapping[str, Any],
    ) -> None:
        """Adiciona metadados operacionais da análise (escopo, período, IDs etc.)."""
        self.generator.add_section("Metadados da Análise", level=2)

        treatment_year = request_params.get("treatment_year", "—")
        ano_inicio = request_params.get("ano_inicio", "—")
        ano_fim = request_params.get("ano_fim", "—")
        scope = request_params.get("scope", "—")
        method = analysis.get("method", "—")
        status = analysis.get("status", "—")

        treated_count = (
            len(request_params.get("treated_ids") or [])
            if isinstance(request_params.get("treated_ids"), list)
            else "—"
        )
        control_count = (
            len(request_params.get("control_ids") or [])
            if isinstance(request_params.get("control_ids"), list)
            else "—"
        )

        summary_cards = [
            {"label": "Método", "value": str(method).upper()},
            {"label": "Status", "value": str(status)},
            {"label": "Janela", "value": f"{ano_inicio} a {ano_fim}"},
            {"label": "Tratamento", "value": f"Ano {treatment_year}"},
            {"label": "Escopo", "value": str(scope)},
            {"label": "Municípios", "value": f"{treated_count} tratados / {control_count} controle"},
        ]
        self.generator.add_summary_cards(summary_cards)

        result_summary = self._coerce_mapping(analysis.get("result_summary") or {})
        if result_summary:
            self.generator.add_text("Resumo disponível:", bold=True)
            for row in self._format_summary_lines(result_summary):
                self.generator.add_text(row)

    def _format_summary_lines(self, result_summary: Mapping[str, Any]) -> list[str]:
        """Renderiza campos-chave do resultado resumido em texto corrido."""
        lines: list[str] = []
        for key in ("outcome", "coef", "std_err", "p_value", "ci_lower", "ci_upper", "n_obs", "warnings"):
            if key not in result_summary or result_summary.get(key) is None:
                continue
            value = result_summary[key]
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            lines.append(f"{key}: {value}")
        if not lines:
            lines.append("Sem métricas executivas em result_summary.")
        return lines

    def _extract_outcomes(
        self,
        request_params: Mapping[str, Any],
        result_full: Mapping[str, Any],
    ) -> list[str]:
        """Retorna lista de outcomes a exibir, com fallback para chaves de result_full."""
        outcomes = request_params.get("outcomes")
        if isinstance(outcomes, list) and outcomes:
            return [str(x) for x in outcomes]
        return [str(k) for k in result_full.keys() if str(k) not in {"did", "comparison"}]

    def _add_impact_summary_section(
        self,
        method: str,
        outcomes: list[str],
        result_summary: Mapping[str, Any],
        result_full: Mapping[str, Any],
    ) -> None:
        """Tabela principal com estimativas agregadas da análise."""
        self.generator.add_section("Resultado Principal", level=2)

        headers = ["Outcome", "Método", "Coef", "Erro Padrão", "P-valor", "IC 95% (inf, sup)", "N obs"]
        rows: list[list[str]] = []

        method = method.lower()
        if method == "compare":
            rows.extend(self._rows_for_compare(outcomes, result_full))
        else:
            rows.extend(self._rows_for_standard(method, outcomes, result_full))

        if not rows:
            outcome_cards = [{"label": "Observação", "value": "Sem resultados numéricos no payload principal."}]
            if result_summary:
                for key in ("coef", "std_err", "p_value", "ci_lower", "ci_upper", "n_obs"):
                    if key in result_summary and result_summary[key] is not None:
                        outcome_cards.append({"label": key, "value": str(result_summary[key])})
            self.generator.add_summary_cards(outcome_cards)
            return

        self.generator.add_indicator_table(headers, rows)

    def _rows_for_standard(
        self,
        method: str,
        outcomes: list[str],
        result_full: Mapping[str, Any],
    ) -> list[list[str]]:
        """Resumo para métodos não comparativos (DiD/IV/Panel IV/Event Study)."""
        rows: list[list[str]] = []
        for outcome in outcomes:
            payload = self._coerce_mapping(result_full.get(outcome) or {})
            if not payload:
                continue

            if method == "event_study":
                at_treatment = self._extract_event_study_att(payload)
                if at_treatment:
                    rows.append(self._build_row(outcome, "event_study", at_treatment))
                    continue

            main = self._extract_main_result(payload)
            if main:
                rows.append(self._build_row(outcome, method, main))

            # fallback para método sem dicionário de coeficiente (ex.: payload parcial)
            elif payload.get("coefficients"):
                first_coef = payload["coefficients"][0] if payload["coefficients"] else {}
                rows.append(self._build_row(outcome, method, first_coef))

        return rows

    def _rows_for_compare(
        self,
        outcomes: list[str],
        result_full: Mapping[str, Any],
    ) -> list[list[str]]:
        """Resumo de outputs de `compare` com tabela de métodos e recomendação."""
        rows: list[list[str]] = []
        did_results = self._coerce_mapping(result_full.get("did") or {})
        comparison = self._coerce_mapping(result_full.get("comparison") or {})

        for outcome in outcomes:
            did_payload = self._coerce_mapping(did_results.get(outcome) or {})
            if did_payload:
                main = self._extract_main_result(did_payload)
                if main:
                    rows.append(self._build_row(outcome, "DiD", main))

            comp_payload = self._coerce_mapping(comparison.get(outcome) or {})
            table_rows = self._coerce_value(comp_payload.get("comparison_table"), [])
            if isinstance(table_rows, list):
                for item in table_rows:
                    item_map = self._coerce_mapping(item)
                    rows.append(
                        [
                            outcome,
                            str(item_map.get("Method", "Método")),
                            self._fmt(item_map.get("Estimate")),
                            self._fmt(item_map.get("SE")),
                            self._fmt(item_map.get("P_Value")),
                            self._fmt_ci(item_map.get("CI_Lower"), item_map.get("CI_Upper")),
                            self._fmt(item_map.get("n_obs")),
                        ]
                    )

            if comp_payload and not table_rows:
                rows.append(
                    [
                        outcome,
                        "compare",
                        self._fmt(comp_payload.get("recommended_estimate")),
                        "—",
                        "—",
                        "—",
                        "—",
                    ]
                )
        return rows

    def _add_impact_results_section(
        self,
        method: str,
        outcomes: list[str],
        result_full: Mapping[str, Any],
        result_summary: Mapping[str, Any],
    ) -> None:
        """Tabelas de detalhe por outcome (inclui séries de Event Study quando aplicável)."""
        self.generator.add_section("Detalhes por Outcome", level=2)

        method = method.lower()
        if method == "event_study":
            for outcome in outcomes:
                payload = self._coerce_mapping(result_full.get(outcome) or {})
                self.generator.add_text(f"{outcome}", bold=True)
                coefficients = self._coerce_value(payload.get("coefficients"), [])
                if coefficients:
                    headers = ["Rel. Time", "Coef", "SE", "P-valor", "IC 95% inf", "IC 95% sup", "Período", "Signif. 10%"]
                    rows = [
                        [
                            str(item.get("rel_time", "")),
                            self._fmt(item.get("coef")),
                            self._fmt(item.get("se")),
                            self._fmt(item.get("pvalue")),
                            self._fmt(item.get("ci_lower")),
                            self._fmt(item.get("ci_upper")),
                            str(item.get("period", "")),
                            str(item.get("significant_10pct", "")),
                        ]
                        for item in coefficients
                    ]
                    self.generator.add_indicator_table(headers, rows)
                    chart_bytes = self._build_event_study_chart_png(coefficients)
                    if chart_bytes:
                        self.generator.add_chart_image(chart_bytes, f"Event Study - {outcome}")
                    else:
                        self.generator.add_chart_placeholder(f"Event Study - {outcome}")
                else:
                    self.generator.add_text("Sem coeficientes por período.")

        elif method == "compare":
            for outcome in outcomes:
                comp_payload = self._coerce_mapping(
                    self._coerce_mapping(result_full.get("comparison") or {}).get(outcome) or {}
                )
                self.generator.add_text(f"{outcome}", bold=True)
                if comp_payload:
                    consistency = comp_payload.get("consistency_assessment")
                    if consistency:
                        self.generator.add_text(f"Avaliação: {consistency}")
                    recommendation = comp_payload.get("recommended_estimate")
                    if recommendation:
                        self.generator.add_text(f"Recomendação: {recommendation}")
                    interpretation = comp_payload.get("interpretation_notes")
                    if interpretation:
                        self.generator.add_text(f"Interpretação: {interpretation}")
                    table_rows = self._coerce_value(comp_payload.get("comparison_table"), [])
                    if isinstance(table_rows, list) and table_rows:
                        headers = [
                            "Método", "Estimate", "SE", "CI inf", "CI sup", "P-valor", "Significativo", "Observações"
                        ]
                        rows = [
                            [
                                str(item.get("Method", "")),
                                self._fmt(item.get("Estimate")),
                                self._fmt(item.get("SE")),
                                self._fmt(item.get("CI_Lower")),
                                self._fmt(item.get("CI_Upper")),
                                self._fmt(item.get("P_Value")),
                                str(item.get("Significant", "")),
                                str(item.get("Notes", "")),
                            ]
                            for item in table_rows
                        ]
                        self.generator.add_indicator_table(headers, rows)
                else:
                    self.generator.add_text("Sem comparação metodológica disponível.")
        else:
            for outcome in outcomes:
                self.generator.add_text(f"{outcome}", bold=True)
                payload = self._coerce_mapping(result_full.get(outcome) or {})
                if not payload:
                    self.generator.add_text("Sem detalhamento adicional disponível.")
                    continue
                main = self._extract_main_result(payload)
                if not main:
                    self.generator.add_text("Sem detalhamento adicional disponível.")
                    continue
                rows = [[k, self._fmt(v)] for k, v in main.items() if isinstance(v, (int, float, str))]
                if rows:
                    self.generator.add_indicator_table(["Campo", "Valor"], rows)
                else:
                    self.generator.add_text("Sem detalhamento adicional disponível.")

    def _build_event_study_chart_png(
        self,
        coefficients: list[dict[str, Any]],
    ) -> bytes | None:
        """Monta gráfico de Event Study em memória (PNG), quando matplotlib estiver disponível."""
        try:
            from matplotlib import pyplot as plt  # type: ignore
        except Exception:
            return None

        points = []
        for raw_item in coefficients:
            item = self._coerce_mapping(raw_item)
            rel_time = item.get("rel_time")
            coef = (
                item.get("coef")
                if item.get("coef") is not None
                else item.get("att")
                if item.get("att") is not None
                else item.get("estimate")
            )
            if not isinstance(rel_time, (int, float)) or not isinstance(coef, (int, float)):
                continue
            points.append((int(rel_time), float(coef)))

        if len(points) < 2:
            return None

        x, y = zip(*sorted(points))

        try:
            plt.figure(figsize=(6.0, 3.8))
            plt.plot(x, y, marker="o", linewidth=2, color="#1f77b4")
            plt.axhline(0, linewidth=1, linestyle="--", color="gray")
            plt.axvline(0, linewidth=1, linestyle=":", color="black")
            plt.title("Evolução do efeito por período")
            plt.xlabel("Período relativo ao tratamento")
            plt.ylabel("Coeficiente")
            plt.grid(axis="both", alpha=0.2)

            from io import BytesIO

            buffer = BytesIO()
            plt.tight_layout()
            plt.savefig(buffer, format="png", dpi=120)
            plt.close()
            buffer.seek(0)
            return buffer.getvalue()
        except Exception:
            plt.close()
            return None

    def _add_impact_diagnostics_section(
        self,
        method: str,
        outcomes: list[str],
        result_full: Mapping[str, Any],
    ) -> None:
        """Reúne notas de diagnóstico para análise causal."""
        self.generator.add_section("Diagnóstico", level=2)

        warnings: list[str] = []
        if method == "compare":
            for outcome in outcomes:
                comp_payload = self._coerce_mapping(
                    self._coerce_mapping(result_full.get("comparison") or {}).get(outcome) or {}
                )
                interp = comp_payload.get("interpretation_notes")
                if isinstance(interp, str):
                    warnings.append(f"{outcome}: {interp}")
        else:
            for outcome in outcomes:
                payload = self._coerce_mapping(result_full.get(outcome) or {})
                for key in ("parallel_trends", "first_stage", "reduced_form", "model_info"):
                    section = self._coerce_mapping(payload.get(key) or {})
                    if not section:
                        continue
                    warning = section.get("warning") or section.get("interpretation")
                    if warning:
                        warnings.append(f"{outcome} [{key}]: {warning}")

        if warnings:
            self.generator.add_bullet_list(warnings)
        else:
            self.generator.add_text("Nenhum alerta metodológico adicional identificado.")

    def _extract_main_result(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        """Extrai bloco principal numérico do payload causal."""
        main = payload.get("main_result")
        if isinstance(main, Mapping):
            return main
        return payload

    def _extract_event_study_att(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        """Retorna o coeficiente do período de tratamento para event study (rel_time=0)."""
        coefficients = self._coerce_value(payload.get("coefficients"), [])
        if not isinstance(coefficients, list):
            return {}
        for item in coefficients:
            if self._coerce_mapping(item).get("rel_time") == 0:
                return self._coerce_mapping(item)
        # Fallback: primeiro coeficiente quando não existe rel_time=0 explícito
        if coefficients:
            return self._coerce_mapping(coefficients[0])
        return {}

    def _build_row(
        self,
        outcome: str,
        method: str,
        payload: Mapping[str, Any],
    ) -> list[str]:
        """Normaliza uma linha de resultado principal para tabela."""
        return [
            outcome,
            str(method),
            self._fmt(payload.get("coef", payload.get("att"))),
            self._fmt(payload.get("std_err")),
            self._fmt(payload.get("p_value")),
            self._fmt_ci(payload.get("ci_lower"), payload.get("ci_upper")),
            self._fmt(payload.get("n_obs")),
        ]

    @staticmethod
    def _fmt(value: Any) -> str:
        """Formata número com casas úteis para o relatório."""
        if value is None:
            return "—"
        if isinstance(value, bool):
            return "Sim" if value else "Não"
        if isinstance(value, (int, float)):
            return f"{value:.4f}" if isinstance(value, float) else str(value)
        return str(value)

    @staticmethod
    def _fmt_ci(lower: Any, upper: Any) -> str:
        """Formata intervalo de confiança como faixa textual."""
        if lower is None and upper is None:
            return "—"
        return f"{ReportService._fmt(lower)} ; {ReportService._fmt(upper)}"

    @staticmethod
    def _coerce_mapping(value: Any) -> Mapping[str, Any]:
        """Converte objetos variados para dicionário legível por `[]`."""
        if isinstance(value, Mapping):
            return value
        if hasattr(value, "model_dump"):
            dumped = value.model_dump()
            return dumped if isinstance(dumped, Mapping) else {}
        if hasattr(value, "dict"):
            dumped = value.dict()
            return dumped if isinstance(dumped, Mapping) else {}
        if value is None:
            return {}
        # fallback seguro para valores inesperados
        return {}

    @staticmethod
    def _coerce_value(value: Any, fallback: Any) -> Any:
        """Retorna value quando não nulo, caso contrário fallback."""
        return fallback if value is None else value
