"""JSON renderer for graph inspection reports."""

from __future__ import annotations

import json
from dataclasses import dataclass

from django_migration_inspector.domain.reports import GraphInspectionReport


@dataclass(slots=True)
class JsonGraphReportRenderer:
    """Serialize graph reports into deterministic JSON."""

    indent: int = 2

    def render(self, report: GraphInspectionReport) -> str:
        """Render the graph report into JSON."""

        return json.dumps(report.to_json_dict(), indent=self.indent) + "\n"

