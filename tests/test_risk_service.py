"""Integration tests for the risk analysis service and command."""

from __future__ import annotations

import json
from io import StringIO

from django.core.management import call_command
from pytest_django.plugin import DjangoDbBlocker

from django_migration_inspector.config import RiskConfig
from django_migration_inspector.domain.enums import RiskAnalysisScope, RiskSeverity
from django_migration_inspector.domain.plans import ForwardMigrationPlan
from django_migration_inspector.domain.reports import RiskAssessmentReport
from django_migration_inspector.renderers.risk_text import TextRiskReportRenderer
from django_migration_inspector.services import build_default_risk_service


def test_risk_service_detects_destructive_and_irreversible_steps(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    service = build_default_risk_service()

    with django_db_blocker.unblock():
        report = service.inspect_risk(RiskConfig())

    assert report.pending_migration_count == 11
    assert report.analysis_scope is RiskAnalysisScope.PENDING
    assert report.overall_severity is RiskSeverity.HIGH
    assert report.rollback_safe is False
    assert any(finding.operation_name == "RemoveField" for finding in report.findings)
    assert any(finding.operation_name == "RunPython" for finding in report.findings)


def test_management_command_renders_risk_json(django_db_blocker: DjangoDbBlocker) -> None:
    output = StringIO()

    with django_db_blocker.unblock():
        call_command("migration_inspect", "risk", "--json", stdout=output)

    report = json.loads(output.getvalue())
    assert report["report_type"] == "risk_assessment"
    assert report["analysis_scope"] == "pending"
    assert report["affected_app_labels"]
    assert report["overall_severity"] == "high"
    assert report["rollback_safe"] is False
    assert any(finding["operation_name"] == "RunPython" for finding in report["findings"])


def test_management_command_supports_risk_subcommand(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    output = StringIO()

    with django_db_blocker.unblock():
        call_command("migration_inspect", "risk", "--app", "billing", stdout=output)

    rendered = output.getvalue()
    assert "Scope: billing" in rendered
    assert "Decision: ROLLBACK BLOCKED" in rendered
    assert "Pending migrations:" in rendered


def test_management_command_supports_audit_subcommand_json(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    output = StringIO()

    with django_db_blocker.unblock():
        call_command("migration_inspect", "audit", "--json", stdout=output)

    report = json.loads(output.getvalue())
    assert report["report_type"] == "risk_assessment"
    assert report["analysis_scope"] == "history"


def test_management_command_renders_risk_text_for_one_app(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    output = StringIO()

    with django_db_blocker.unblock():
        call_command("migration_inspect", "risk", "--app", "billing", stdout=output)

    rendered = output.getvalue()
    assert "Decision: ROLLBACK BLOCKED" in rendered
    assert "Summary:" in rendered
    assert "contains destructive schema changes" in rendered
    assert "billing.0002_remove_reference" in rendered
    assert "billing.0003_irreversible_cleanup" in rendered


def test_management_command_renders_historical_risk_json(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    output = StringIO()

    with django_db_blocker.unblock():
        call_command(
            "migration_inspect",
            "audit",
            "--app",
            "billing",
            "--json",
            stdout=output,
        )

    report = json.loads(output.getvalue())
    assert report["analysis_scope"] == "history"
    assert "billing" in report["affected_app_labels"]
    assert report["analyzed_migration_count"] >= 3
    assert report["pending_migration_count"] == 0
    assert any(finding["operation_name"] == "RemoveField" for finding in report["findings"])


def test_management_command_rejects_visual_risk_format(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    output = StringIO()

    with django_db_blocker.unblock():
        try:
            call_command(
                "migration_inspect",
                "risk",
                "--format",
                "mermaid",
                stdout=output,
            )
        except Exception as error:
            assert "supports only text and json" in str(error)
        else:
            raise AssertionError("Expected risk mode with Mermaid output to fail.")


def test_management_command_rejects_legacy_risk_flag(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    output = StringIO()

    with django_db_blocker.unblock():
        try:
            call_command("migration_inspect", "--risk", stdout=output)
        except Exception as error:
            assert "unrecognized arguments: --risk" in str(error)
        else:
            raise AssertionError("Expected legacy risk flag syntax to fail.")


def test_text_risk_renderer_explains_empty_pending_plan() -> None:
    renderer = TextRiskReportRenderer()
    report = RiskAssessmentReport(
        database_alias="default",
        selected_app_label="billing",
        overall_severity=RiskSeverity.NONE,
        rollback_safe=True,
        findings=(),
        plan=ForwardMigrationPlan(
            database_alias="default",
            selected_app_label="billing",
            scope=RiskAnalysisScope.PENDING,
            target_leaf_nodes=(),
            steps=(),
        ),
    )

    rendered = renderer.render(report)

    assert "Decision: CLEAR" in rendered
    assert "Pending migrations: 0" in rendered
    assert "No pending migrations need review in the selected scope." in rendered
    assert "migration_inspect audit" in rendered
