"""JSON renderer for rollback simulation reports."""

from __future__ import annotations

import json
from dataclasses import dataclass

from django_migration_inspector.domain.reports import RollbackSimulationReport


@dataclass(slots=True)
class JsonRollbackReportRenderer:
    """Serialize rollback simulation reports into deterministic JSON."""

    indent: int = 2

    def render(self, report: RollbackSimulationReport) -> str:
        """Render the rollback report into JSON."""

        return json.dumps(report.to_json_dict(), indent=self.indent) + "\n"
