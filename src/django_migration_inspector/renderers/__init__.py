"""Report renderer helpers."""

from __future__ import annotations

from django_migration_inspector.domain.enums import OutputFormat

from .base import GraphReportRenderer, RiskReportRenderer, RollbackReportRenderer
from .dot import DotGraphReportRenderer
from .json import JsonGraphReportRenderer
from .mermaid import MermaidGraphReportRenderer
from .risk_json import JsonRiskReportRenderer
from .risk_text import RiskTextRenderOptions, TextRiskReportRenderer
from .rollback_json import JsonRollbackReportRenderer
from .rollback_text import RollbackTextRenderOptions, TextRollbackReportRenderer
from .text import GraphTextRenderOptions, TextGraphReportRenderer

__all__ = [
    "GraphReportRenderer",
    "GraphTextRenderOptions",
    "RiskReportRenderer",
    "RiskTextRenderOptions",
    "RollbackReportRenderer",
    "RollbackTextRenderOptions",
    "get_graph_report_renderer",
    "get_risk_report_renderer",
    "get_rollback_report_renderer",
]


def get_graph_report_renderer(
    output_format: OutputFormat,
    *,
    text_options: GraphTextRenderOptions | None = None,
) -> GraphReportRenderer:
    """Return the renderer for the selected output format."""

    if output_format is OutputFormat.JSON:
        return JsonGraphReportRenderer()
    if output_format is OutputFormat.MERMAID:
        return MermaidGraphReportRenderer()
    if output_format is OutputFormat.DOT:
        return DotGraphReportRenderer()
    return TextGraphReportRenderer(options=text_options or GraphTextRenderOptions())


def get_risk_report_renderer(
    output_format: OutputFormat,
    *,
    text_options: RiskTextRenderOptions | None = None,
) -> RiskReportRenderer:
    """Return the renderer for the selected risk output format."""

    if output_format is OutputFormat.JSON:
        return JsonRiskReportRenderer()
    return TextRiskReportRenderer(options=text_options or RiskTextRenderOptions())


def get_rollback_report_renderer(
    output_format: OutputFormat,
    *,
    text_options: RollbackTextRenderOptions | None = None,
) -> RollbackReportRenderer:
    """Return the renderer for the selected rollback output format."""

    if output_format is OutputFormat.JSON:
        return JsonRollbackReportRenderer()
    return TextRollbackReportRenderer(options=text_options or RollbackTextRenderOptions())
