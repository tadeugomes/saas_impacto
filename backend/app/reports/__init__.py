"""Relatórios exportáveis em DOCX."""
from .docx_generator import DOCXGenerator
from .report_service import ReportService
from .templates import MODULE_TEMPLATES

__all__ = ['DOCXGenerator', 'ReportService', 'MODULE_TEMPLATES']
