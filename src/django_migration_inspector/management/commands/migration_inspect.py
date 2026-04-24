"""Django management command entry point for migration inspection."""

from __future__ import annotations

import shutil
from argparse import ArgumentParser
from pathlib import Path
from pydoc import pager

from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError
from django.db.migrations.exceptions import (
    AmbiguityError,
    BadMigrationError,
    CircularDependencyError,
    InconsistentMigrationHistory,
    InvalidBasesError,
    InvalidMigrationPlan,
    IrreversibleError,
    MigrationSchemaMissing,
    NodeNotFoundError,
)
from django.db.utils import DatabaseError as DjangoDatabaseError
from django.utils.connection import ConnectionDoesNotExist

from django_migration_inspector.config import InspectConfig, RiskConfig, RollbackConfig
from django_migration_inspector.domain.enums import OutputFormat, RiskAnalysisScope, RiskSeverity
from django_migration_inspector.domain.reports import GraphInspectionReport
from django_migration_inspector.exceptions import DjangoMigrationInspectorError
from django_migration_inspector.renderers import (
    GraphTextRenderOptions,
    RiskTextRenderOptions,
    RollbackTextRenderOptions,
    get_graph_report_renderer,
    get_risk_report_renderer,
    get_rollback_report_renderer,
)
from django_migration_inspector.services import (
    build_default_inspect_service,
    build_default_risk_service,
    build_default_rollback_service,
)

SIMPLE_MODES = ("inspect", "risk", "audit", "rollback")
FAIL_ON_SEVERITY_CHOICES = (
    RiskSeverity.MEDIUM.value,
    RiskSeverity.HIGH.value,
    RiskSeverity.CRITICAL.value,
)
SEVERITY_RANK = {
    RiskSeverity.NONE: 0,
    RiskSeverity.LOW: 1,
    RiskSeverity.MEDIUM: 2,
    RiskSeverity.HIGH: 3,
    RiskSeverity.CRITICAL: 4,
}
MIGRATION_GRAPH_ERRORS = (
    AmbiguityError,
    BadMigrationError,
    CircularDependencyError,
    InconsistentMigrationHistory,
    InvalidBasesError,
    InvalidMigrationPlan,
    IrreversibleError,
    MigrationSchemaMissing,
    NodeNotFoundError,
)


class Command(BaseCommand):
    """Inspect the Django migration graph and emit a stable report."""

    help = "Inspect Django migrations with graph, deploy-risk, audit, and rollback modes."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "mode",
            nargs="?",
            choices=SIMPLE_MODES,
            default="inspect",
            help="Preferred mode: inspect, risk, audit, or rollback.",
        )
        parser.add_argument(
            "mode_args",
            nargs="*",
            metavar="ARG",
            help=(
                "Additional arguments for the selected mode. "
                "rollback expects APP_LABEL MIGRATION_NAME."
            ),
        )
        parser.add_argument(
            "--format",
            choices=[output_format.value for output_format in OutputFormat],
            default=OutputFormat.TEXT.value,
            help="Output renderer to use.",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Shortcut for --format json.",
        )
        parser.add_argument(
            "--database",
            default="default",
            help="Django database alias used for migration state loading.",
        )
        parser.add_argument(
            "--offline",
            action="store_true",
            help=(
                "Load migration files without connecting to the database. "
                "Supported for inspect and audit modes only."
            ),
        )
        parser.add_argument(
            "--output",
            default=None,
            help="Write the rendered report to a file instead of stdout.",
        )
        parser.add_argument(
            "--app",
            dest="app_label",
            default=None,
            help="Limit the report to one Django app label.",
        )
        parser.add_argument(
            "--details",
            action="store_true",
            help="For text output, include the full detailed listing for the selected mode.",
        )
        parser.add_argument(
            "--show-operations",
            action="store_true",
            help="For rollback text output, include reverse operations for each rollback step.",
        )
        parser.add_argument(
            "--why-app",
            default=None,
            help="For rollback text output, explain why the selected app is included.",
        )
        parser.add_argument(
            "--fail-on-severity",
            choices=FAIL_ON_SEVERITY_CHOICES,
            default=None,
            help=("Exit non-zero when risk, audit, or rollback severity meets this threshold."),
        )
        parser.add_argument(
            "--fail-on-multiple-heads",
            action="store_true",
            help="Exit non-zero when inspect mode finds multiple heads in any app.",
        )

    def handle(self, *args: object, **options: object) -> str | None:
        del args

        try:
            raw_mode_args = options["mode_args"]
            if not isinstance(raw_mode_args, (list, tuple)):
                raise CommandError("Unexpected command arguments received from argparse.")
            output_format = self._resolve_output_format(
                raw_format=str(options["format"]),
                json_mode=bool(options["json"]),
            )
            requested_mode, rollback_target = self._resolve_requested_mode(
                mode=self._normalize_optional_string(options["mode"]),
                mode_args=tuple(str(value) for value in raw_mode_args),
            )
            database_alias = str(options["database"])
            offline = bool(options["offline"])
            output_path = self._normalize_optional_string(options["output"])
            raw_app_label = options["app_label"]
            app_label = None if raw_app_label in (None, "") else str(raw_app_label)
            details = bool(options["details"])
            show_operations = bool(options["show_operations"])
            why_app = self._normalize_optional_string(options["why_app"])
            fail_on_severity = self._resolve_fail_on_severity(options["fail_on_severity"])
            fail_on_multiple_heads = bool(options["fail_on_multiple_heads"])

            self._validate_mode_specific_options(
                output_format=output_format,
                requested_mode=requested_mode,
                details=details,
                show_operations=show_operations,
                why_app=why_app,
                offline=offline,
                fail_on_severity=fail_on_severity,
                fail_on_multiple_heads=fail_on_multiple_heads,
            )

            if requested_mode in {"risk", "audit"}:
                if output_format in {OutputFormat.MERMAID, OutputFormat.DOT}:
                    raise CommandError(
                        "Risk analysis currently supports only text and json output formats."
                    )
                risk_config = RiskConfig(
                    output_format=output_format,
                    database_alias=database_alias,
                    app_label=app_label,
                    scope=(
                        RiskAnalysisScope.HISTORY
                        if requested_mode == "audit"
                        else RiskAnalysisScope.PENDING
                    ),
                    offline=offline,
                )
                risk_service = build_default_risk_service()
                risk_report = risk_service.inspect_risk(config=risk_config)
                risk_renderer = get_risk_report_renderer(
                    output_format=output_format,
                    text_options=RiskTextRenderOptions(details=details),
                )
                self._emit_rendered_output(
                    rendered_output=risk_renderer.render(risk_report),
                    output_format=output_format,
                    output_path=output_path,
                )
                self._raise_for_severity_policy(
                    overall_severity=risk_report.overall_severity,
                    fail_on_severity=fail_on_severity,
                )
            elif requested_mode == "rollback":
                if app_label is not None:
                    raise CommandError("--app cannot be used together with rollback mode.")
                if output_format in {OutputFormat.MERMAID, OutputFormat.DOT}:
                    raise CommandError(
                        "Rollback mode currently supports only text and json output formats."
                    )
                if rollback_target is None:
                    raise CommandError(
                        "Rollback mode expects exactly two values: APP_LABEL and MIGRATION_NAME."
                    )
                target_app_label, target_migration_name = rollback_target
                rollback_config = RollbackConfig(
                    output_format=output_format,
                    database_alias=database_alias,
                    target_app_label=target_app_label,
                    target_migration_name=target_migration_name,
                )
                rollback_service = build_default_rollback_service()
                rollback_report = rollback_service.inspect_rollback(config=rollback_config)
                if why_app is not None and why_app not in rollback_report.plan.affected_app_labels:
                    raise CommandError(f"App {why_app!r} is not part of the current rollback plan.")
                rollback_renderer = get_rollback_report_renderer(
                    output_format=output_format,
                    text_options=RollbackTextRenderOptions(
                        details=details or show_operations,
                        show_operations=show_operations,
                        why_app=why_app,
                    ),
                )
                self._emit_rendered_output(
                    rendered_output=rollback_renderer.render(rollback_report),
                    output_format=output_format,
                    output_path=output_path,
                )
                self._raise_for_severity_policy(
                    overall_severity=rollback_report.overall_severity,
                    fail_on_severity=fail_on_severity,
                )
            else:
                inspect_config = InspectConfig(
                    output_format=output_format,
                    database_alias=database_alias,
                    app_label=app_label,
                    offline=offline,
                )
                graph_service = build_default_inspect_service()
                graph_report = graph_service.inspect_graph(config=inspect_config)
                graph_renderer = get_graph_report_renderer(
                    output_format=output_format,
                    text_options=GraphTextRenderOptions(details=details),
                )
                self._emit_rendered_output(
                    rendered_output=graph_renderer.render(graph_report),
                    output_format=output_format,
                    output_path=output_path,
                )
                self._raise_for_multiple_heads_policy(
                    graph_report=graph_report,
                    fail_on_multiple_heads=fail_on_multiple_heads,
                )
        except DjangoMigrationInspectorError as error:
            raise CommandError(str(error)) from error
        except ConnectionDoesNotExist as error:
            raise CommandError(
                f"Unknown database alias. Check your Django DATABASES setting. {error}"
            ) from error
        except ImproperlyConfigured as error:
            raise CommandError(f"Django is not configured correctly: {error}") from error
        except MIGRATION_GRAPH_ERRORS as error:
            raise CommandError(
                "Django could not load a consistent migration graph. "
                f"Fix the migration files first, then run this command again. Details: {error}"
            ) from error
        except DjangoDatabaseError as error:
            raise CommandError(
                f"Django hit a database error while reading migration state. Details: {error}"
            ) from error
        except (ImportError, SyntaxError) as error:
            raise CommandError(
                "Django could not import one of the project or migration modules. "
                f"Fix the import error first, then run this command again. Details: {error}"
            ) from error
        except OSError as error:
            raise CommandError(
                "Django could not read one of the project or migration files. "
                f"Fix the filesystem error first, then run this command again. Details: {error}"
            ) from error

        return None

    def _normalize_optional_string(self, raw_value: object) -> str | None:
        if raw_value in (None, ""):
            return None
        return str(raw_value)

    def _resolve_output_format(
        self,
        *,
        raw_format: str,
        json_mode: bool,
    ) -> OutputFormat:
        output_format = OutputFormat(raw_format)
        if not json_mode:
            return output_format
        if output_format is not OutputFormat.TEXT:
            raise CommandError("--json cannot be combined with --format.")
        return OutputFormat.JSON

    def _resolve_requested_mode(
        self,
        *,
        mode: str | None,
        mode_args: tuple[str, ...],
    ) -> tuple[str, tuple[str, str] | None]:
        if mode == "inspect" or mode is None:
            if mode_args:
                raise CommandError("Inspect mode does not accept positional arguments.")
            return ("inspect", None)

        if mode == "risk":
            if mode_args:
                raise CommandError("Risk mode does not accept positional arguments.")
            return ("risk", None)

        if mode == "audit":
            if mode_args:
                raise CommandError("Audit mode does not accept positional arguments.")
            return ("audit", None)

        if mode == "rollback":
            if len(mode_args) != 2:
                raise CommandError(
                    "Rollback mode expects exactly two positional arguments: "
                    "APP_LABEL and MIGRATION_NAME."
                )
            return (mode, (mode_args[0], mode_args[1]))

        raise CommandError("Unable to determine the requested command mode.")

    def _resolve_fail_on_severity(self, raw_value: object) -> RiskSeverity | None:
        value = self._normalize_optional_string(raw_value)
        if value is None:
            return None
        return RiskSeverity(value)

    def _validate_mode_specific_options(
        self,
        *,
        output_format: OutputFormat,
        requested_mode: str,
        details: bool,
        show_operations: bool,
        why_app: str | None,
        offline: bool,
        fail_on_severity: RiskSeverity | None,
        fail_on_multiple_heads: bool,
    ) -> None:
        if requested_mode == "rollback":
            if offline:
                raise CommandError(
                    "--offline cannot be used with rollback because rollback simulation needs "
                    "the current applied migration state from the database."
                )
            if output_format is OutputFormat.JSON and (details or show_operations or why_app):
                raise CommandError(
                    "--details, --show-operations, and --why-app are available only for "
                    "text rollback output."
                )
            if fail_on_multiple_heads:
                raise CommandError("--fail-on-multiple-heads is available only for inspect mode.")
            return

        if requested_mode == "risk" and offline:
            raise CommandError(
                "--offline cannot be used with risk because pending migrations depend on the "
                "current applied migration state from the database. Use `audit --offline` for a "
                "file-only migration review."
            )

        if requested_mode in {"risk", "audit", "inspect"}:
            if show_operations or why_app is not None:
                raise CommandError(
                    "--show-operations and --why-app can only be used together with rollback mode."
                )
            if output_format is not OutputFormat.TEXT and details:
                raise CommandError("--details is available only for text output.")
            if requested_mode == "inspect" and fail_on_severity is not None:
                raise CommandError(
                    "--fail-on-severity is available only for risk, audit, and rollback modes."
                )
            if requested_mode in {"risk", "audit"} and fail_on_multiple_heads:
                raise CommandError("--fail-on-multiple-heads is available only for inspect mode.")
            return

        if details or show_operations or why_app is not None:
            raise CommandError(
                "--details, --show-operations, and --why-app can only be used with "
                "inspect, risk, audit, or rollback mode."
            )

    def _raise_for_severity_policy(
        self,
        *,
        overall_severity: RiskSeverity,
        fail_on_severity: RiskSeverity | None,
    ) -> None:
        if fail_on_severity is None:
            return
        if SEVERITY_RANK[overall_severity] < SEVERITY_RANK[fail_on_severity]:
            return
        raise CommandError(
            "Migration inspection policy failed: "
            f"overall severity is {overall_severity.value}, threshold is {fail_on_severity.value}."
        )

    def _raise_for_multiple_heads_policy(
        self,
        *,
        graph_report: GraphInspectionReport,
        fail_on_multiple_heads: bool,
    ) -> None:
        if not fail_on_multiple_heads or not graph_report.multiple_head_apps:
            return

        app_labels = ", ".join(
            app_head_group.app_label for app_head_group in graph_report.multiple_head_apps
        )
        raise CommandError(
            f"Migration inspection policy failed: multiple migration heads found in {app_labels}."
        )

    def _emit_rendered_output(
        self,
        *,
        rendered_output: str,
        output_format: OutputFormat,
        output_path: str | None,
    ) -> None:
        if output_path is not None:
            try:
                Path(output_path).expanduser().write_text(rendered_output, encoding="utf-8")
            except OSError as error:
                raise CommandError(
                    f"Could not write migration report to {output_path!r}: {error}"
                ) from error
            return

        if output_format is OutputFormat.TEXT and self._should_page_output(
            rendered_output=rendered_output,
        ):
            pager(rendered_output)
            return

        self.stdout.write(rendered_output, ending="")

    def _should_page_output(self, *, rendered_output: str) -> bool:
        is_tty = bool(getattr(self.stdout, "isatty", lambda: False)())
        if not is_tty:
            return False

        terminal_lines = shutil.get_terminal_size((80, 24)).lines
        return rendered_output.count("\n") > max(terminal_lines - 2, 20)
