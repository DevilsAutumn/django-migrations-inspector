"""Report renderer helpers."""

from __future__ import annotations

from django_migration_inspector.domain.enums import OutputFormat

from .base import GraphReportRenderer
from .dot import DotGraphReportRenderer
from .json import JsonGraphReportRenderer
from .mermaid import MermaidGraphReportRenderer
from .text import TextGraphReportRenderer

__all__ = ["GraphReportRenderer", "get_graph_report_renderer"]


def get_graph_report_renderer(output_format: OutputFormat) -> GraphReportRenderer:
    """Return the renderer for the selected output format."""

    if output_format is OutputFormat.JSON:
        return JsonGraphReportRenderer()
    if output_format is OutputFormat.MERMAID:
        return MermaidGraphReportRenderer()
    if output_format is OutputFormat.DOT:
        return DotGraphReportRenderer()
    return TextGraphReportRenderer()
