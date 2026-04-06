"""Integration tests for the risk analysis service and command."""

from __future__ import annotations

import json
from io import StringIO

from django.core.management import call_command
from pytest_django.plugin import DjangoDbBlocker

from django_migration_inspector.config import InspectConfig
from django_migration_inspector.domain.enums import RiskSeverity
from django_migration_inspector.services import build_default_risk_service


def test_risk_service_detects_destructive_and_irreversible_steps(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    service = build_default_risk_service()

    with django_db_blocker.unblock():
        report = service.inspect_risk(InspectConfig())

    assert report.pending_migration_count == 11
    assert report.overall_severity is RiskSeverity.HIGH
    assert report.rollback_safe is False
    assert any(finding.operation_name == "RemoveField" for finding in report.findings)
    assert any(finding.operation_name == "RunPython" for finding in report.findings)


def test_management_command_renders_risk_json(django_db_blocker: DjangoDbBlocker) -> None:
    output = StringIO()

    with django_db_blocker.unblock():
        call_command("migration_inspect", "--risk", "--format", "json", stdout=output)

    report = json.loads(output.getvalue())
    assert report["report_type"] == "risk_assessment"
    assert report["overall_severity"] == "high"
    assert report["rollback_safe"] is False
    assert any(finding["operation_name"] == "RunPython" for finding in report["findings"])


def test_management_command_renders_risk_text_for_one_app(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    output = StringIO()

    with django_db_blocker.unblock():
        call_command("migration_inspect", "--risk", "--app", "billing", stdout=output)

    rendered = output.getvalue()
    assert "Overall risk: HIGH" in rendered
    assert "Rollback safe: NO" in rendered
    assert "billing.0002_remove_reference" in rendered
    assert "billing.0003_irreversible_cleanup" in rendered


def test_management_command_rejects_visual_risk_format(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    output = StringIO()

    with django_db_blocker.unblock():
        try:
            call_command(
                "migration_inspect",
                "--risk",
                "--format",
                "mermaid",
                stdout=output,
            )
        except Exception as error:
            assert "supports only text and json" in str(error)
        else:
            raise AssertionError("Expected risk mode with Mermaid output to fail.")
