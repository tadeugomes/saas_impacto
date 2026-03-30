"""Gerador XLSX para exports de indicadores e módulos."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any, Iterable

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter


class XLSXGenerator:
    """Cria arquivos XLSX com abas de resultados."""

    @staticmethod
    def _normalize_cell(value: Any) -> Any:
        if value is None or value == "":
            return ""
        return value

    def build_single_indicator(
        self,
        code: str,
        rows: Iterable[dict[str, Any]],
        output_name: str,
    ) -> tuple[BytesIO, str]:
        wb = Workbook()
        ws = wb.active
        ws.title = code[:31]
        ws.append(["Indicador", "Município", "Ano", "Valor", "Data exportação"])
        header_font = Font(bold=True)
        for cell in ws[1]:
            cell.font = header_font

        for row in rows:
            ws.append(
                [
                    code,
                    row.get("nome_municipio", row.get("id_municipio", "")),
                    row.get("ano", ""),
                    self._normalize_cell(row.get("valor", row.get("total", 0))),
                    datetime.now().strftime("%Y-%m-%d"),
                ]
            )

        self._auto_size(ws)
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer, output_name

    def build_module(
        self,
        module_code: str,
        dataset: dict[str, list[dict[str, Any]]],
        output_name: str,
    ) -> tuple[BytesIO, str]:
        wb = Workbook()
        summary = wb.active
        summary.title = "Resumo"
        summary.append(["Código", "Registros"])
        summary.append(["Módulo", module_code])
        for code, rows in dataset.items():
            summary.append([code, len(rows)])
        self._auto_size(summary)

        for code, rows in dataset.items():
            ws = wb.create_sheet(title=code[:31])
            ws.append(["Município", "Ano", "Valor"])
            for row in rows:
                ws.append(
                    [
                        row.get("nome_municipio", row.get("id_municipio", "")),
                        row.get("ano", ""),
                        row.get("valor", row.get("total", 0)),
                    ]
                )
            self._auto_size(ws)

        if "Sheet" in wb.sheetnames:
            wb.remove(wb["Sheet"])

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer, output_name

    def build_module_11(
        self,
        dataset: dict[str, list[dict[str, Any]]],
        output_name: str,
        id_instalacao: str = "",
    ) -> tuple[BytesIO, str]:
        """Excel do Módulo 11 com aba Resultados + Ficha Técnica."""
        from app.reports.templates import MODULE_TEMPLATES

        wb = Workbook()
        bold = Font(bold=True)
        title_font = Font(bold=True, size=14)
        section_font = Font(bold=True, size=12)

        # ── Aba 1: Resultados ────────────────────────────────────────
        ws = wb.active
        ws.title = "Resultados"

        ws.append([f"Previsão de Movimentação — {id_instalacao}"])
        ws["A1"].font = title_font
        ws.append([f"Exportado em {datetime.now().strftime('%d/%m/%Y %H:%M')}"])
        ws.append([])

        # Forecast (IND-11.01)
        forecast_data = dataset.get("IND-11.01", [{}])
        forecast = forecast_data[0] if forecast_data else {}
        forecast_obj = forecast.get("forecast", {})
        previsoes = forecast_obj.get("previsoes_anuais", []) if isinstance(forecast_obj, dict) else []

        if previsoes:
            ws.append(["PROJEÇÃO DE TONELAGEM — 5 ANOS"])
            ws[f"A{ws.max_row}"].font = section_font
            headers = ["Ano", "Tonelagem Anual", "Média Mensal", "IC 95% Inferior", "IC 95% Superior", "Confiança"]
            ws.append(headers)
            for cell in ws[ws.max_row]:
                cell.font = bold
            for i, p in enumerate(previsoes):
                conf = "Alta" if i == 0 else ("Média" if i <= 2 else "Baixa")
                ws.append([
                    p.get("ano", ""),
                    p.get("tonelagem_anual", ""),
                    p.get("tonelagem_media_mensal", ""),
                    p.get("ic_95_inferior", ""),
                    p.get("ic_95_superior", ""),
                    conf,
                ])
            ws.append([])

        # Cenários (IND-11.02)
        scenario_data = dataset.get("IND-11.02", [{}])
        scenario = scenario_data[0] if scenario_data else {}
        cenarios = scenario.get("cenarios", [])

        if cenarios:
            ws.append(["CENÁRIOS — 5 ANOS"])
            ws[f"A{ws.max_row}"].font = section_font
            headers = ["Cenário", "Ano", "Tonelagem Anual", "Variação Acum. (%)", "Crescimento Anual (%)"]
            ws.append(headers)
            for cell in ws[ws.max_row]:
                cell.font = bold
            for c in cenarios:
                nome = c.get("cenario", "")
                cagr = c.get("cagr_pct", "")
                var_acum = c.get("variacao_acumulada_pct", "")
                anuais = c.get("previsoes_anuais", [])
                for j, a in enumerate(anuais):
                    ws.append([
                        nome if j == 0 else "",
                        a.get("ano", ""),
                        a.get("tonelagem_anual", ""),
                        var_acum if j == 0 else "",
                        cagr if j == 0 else "",
                    ])
            ws.append([])

        # Drivers (IND-11.03)
        drivers_data = dataset.get("IND-11.03", [{}])
        drivers = drivers_data[0] if drivers_data else {}
        blocos = drivers.get("blocos", [])

        if blocos:
            ws.append(["FATORES QUE INFLUENCIAM A PREVISÃO"])
            ws[f"A{ws.max_row}"].font = section_font
            headers = ["Categoria", "Importância (%)", "Nº Variáveis"]
            ws.append(headers)
            for cell in ws[ws.max_row]:
                cell.font = bold
            for b in blocos:
                ws.append([
                    b.get("bloco", ""),
                    b.get("importancia_pct", ""),
                    b.get("n_features", ""),
                ])
            ws.append([])

        # Backtesting (IND-11.04)
        backtest_data = dataset.get("IND-11.04", [{}])
        backtest = backtest_data[0] if backtest_data else {}
        horizontes = backtest.get("horizontes", {})

        if horizontes:
            ws.append(["VALIDAÇÃO DO MODELO — PRECISÃO POR PERÍODO"])
            ws[f"A{ws.max_row}"].font = section_font
            headers = ["Período", "Erro (%)", "Erro Médio (ton)", "Desvio (ton)", "Avaliação"]
            ws.append(headers)
            for cell in ws[ws.max_row]:
                cell.font = bold
            for key, val in horizontes.items():
                h = val if isinstance(val, dict) else {}
                mape = h.get("mape_pct")
                label = "Excelente" if mape and mape < 5 else "Bom" if mape and mape < 10 else "Aceitável" if mape and mape < 15 else "Fraco" if mape else "—"
                ws.append([
                    key,
                    mape if mape is not None else "",
                    h.get("mae", ""),
                    h.get("rmse", ""),
                    label,
                ])
            ws.append([])

        # Interpretação (se disponível)
        interp = forecast.get("interpretacao", {})
        resumo = interp.get("resumo_executivo", "") if isinstance(interp, dict) else ""
        if resumo:
            ws.append(["RESUMO EXECUTIVO"])
            ws[f"A{ws.max_row}"].font = section_font
            ws.append([resumo])
            ws.append([])

        self._auto_size(ws)

        # ── Aba 2: Ficha Técnica ─────────────────────────────────────
        ft = wb.create_sheet(title="Ficha Técnica")

        ft.append(["FICHA TÉCNICA DO MODELO DE PREVISÃO"])
        ft["A1"].font = title_font
        ft.append([])

        template = MODULE_TEMPLATES.get("IND-11", {})
        notas = template.get("methodological_notes", [])

        ficha = [
            ("Modelo", "Séries Temporais com Variáveis Exógenas"),
            ("Horizonte de Previsão", "60 meses (5 anos)"),
            ("Frequência", "Mensal"),
            ("Variável Alvo", "Tonelagem mensal movimentada (ANTAQ)"),
            ("", ""),
            ("CATEGORIAS DE DADOS UTILIZADAS", ""),
            ("1. Histórico", "Padrões sazonais e tendências da própria série de movimentação"),
            ("2. Macroeconomia", "Câmbio (PTAX), atividade econômica (IBC-Br), juros (Selic), inflação (IPCA)"),
            ("3. Operação", "Número de navios, tempo de espera, calado, taxa de ocupação"),
            ("4. Safra", "Projeções de produção agrícola (CONAB) para commodities exportadas"),
            ("5. Clima", "Precipitação (INMET), índice El Niño (NOAA), nível de rio (ANA)"),
            ("", ""),
            ("MEDIDAS DE QUALIDADE", ""),
            ("Precisão", "Erro percentual médio (walk-forward 12 meses)"),
            ("Classificação", "Excelente (<5%), Bom (5-10%), Aceitável (10-15%), Fraco (>15%)"),
            ("Intervalos de Confiança", "80% e 95%, calculados a partir da distribuição dos resíduos"),
            ("", ""),
            ("CENÁRIOS", ""),
            ("Base", "Projeção central do modelo com variáveis exógenas no cenário tendencial"),
            ("Otimista", "Desvio positivo com convergência de 20% ao ano para a tendência base"),
            ("Pessimista", "Desvio negativo com convergência de 20% ao ano para a tendência base"),
            ("", ""),
            ("FONTES DE DADOS", ""),
            ("Movimentação", "ANTAQ — Sistema de Desempenho Portuário"),
            ("Macroeconomia", "BACEN — Sistema Gerenciador de Séries Temporais"),
            ("Safra", "CONAB — Acompanhamento de Safra Brasileira"),
            ("Clima", "INMET, NOAA, ANA"),
            ("", ""),
            ("LIMITAÇÕES", ""),
            ("Horizonte", "Projeções para anos 4-5 têm incerteza significativamente maior que anos 1-2"),
            ("Mudanças estruturais", "Novas infraestruturas, regulações ou eventos extremos não são captados"),
            ("Dados futuros", "Variáveis exógenas futuras são projetadas via cenário base (não observadas)"),
            ("", ""),
            ("NOTA", "Este relatório apresenta capacidades preditivas do modelo. "
             "Os parâmetros internos, critérios de seleção e hiperparâmetros são propriedade intelectual "
             "e não são divulgados neste documento."),
        ]

        for item in ficha:
            ft.append(list(item))
            # Bold the first column (labels)
            if item[0]:
                ft[f"A{ft.max_row}"].font = bold
            # Section headers in section_font
            if item[0] and not item[1]:
                ft[f"A{ft.max_row}"].font = section_font

        ft.append([])
        if notas:
            ft.append(["NOTAS METODOLÓGICAS ADICIONAIS"])
            ft[f"A{ft.max_row}"].font = section_font
            for nota in notas:
                ft.append([f"• {nota}"])

        self._auto_size(ft)

        if "Sheet" in wb.sheetnames:
            wb.remove(wb["Sheet"])

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer, output_name

    @staticmethod
    def _auto_size(ws) -> None:
        for col_idx in range(1, ws.max_column + 1):
            max_len = 0
            column = get_column_letter(col_idx)
            for row in ws.iter_rows(min_col=col_idx, max_col=col_idx):
                for cell in row:
                    try:
                        max_len = max(max_len, len(str(cell.value or "")))
                    except Exception:
                        pass
            ws.column_dimensions[column].width = max(10, min(max_len + 2, 50))
