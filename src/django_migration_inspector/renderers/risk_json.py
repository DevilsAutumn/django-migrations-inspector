"""JSON renderer for risk assessment reports."""

from __future__ import annotations

import json
from dataclasses import dataclass

from django_migration_inspector.domain.reports import RiskAssessmentReport


@dataclass(slots=True)
class JsonRiskReportRenderer:
    """Serialize risk reports into deterministic JSON."""

    indent: int = 2

    def render(self, report: RiskAssessmentReport) -> str:
        """Render the risk report into JSON."""

        return json.dumps(report.to_json_dict(), indent=self.indent) + "\n"
