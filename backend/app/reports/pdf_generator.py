"""Gerador PDF básico para exports de indicador/módulo."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any, Iterable

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors


class PDFGenerator:
    """Monta relatórios rápidos em PDF para indicadores."""

    @staticmethod
    def _coerce_data_rows(result: Iterable[dict[str, Any]]) -> list[list[Any]]:
        rows: list[list[Any]] = [["Município", "Ano", "Valor"]]
        for item in result:
            rows.append(
                [
                    item.get("nome_municipio", item.get("id_municipio", "")),
                    item.get("ano", ""),
                    item.get("valor", item.get("total", 0)),
                ]
            )
        return rows

    def build(
        self,
        title: str,
        subtitle: str,
        rows: Iterable[dict[str, Any]],
        output_name: str,
    ) -> tuple[BytesIO, str]:
        """Cria PDF e retorna payload + filename."""
        buffer = BytesIO()
        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(buffer, pagesize=A4, title=title)

        table = Table(
            self._coerce_data_rows(rows),
            hAlign="LEFT",
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        story = [
            Paragraph(title, styles["Heading1"]),
            Paragraph(subtitle, styles["Normal"]),
            Spacer(1, 12),
            table,
            Spacer(1, 20),
            Paragraph(
                f"Gerado por SaaS Impacto Portuário em {datetime.now().isoformat()}",
                styles["Normal"],
            ),
        ]
        doc.build(story)
        buffer.seek(0)
        return buffer, output_name
