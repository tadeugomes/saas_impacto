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
