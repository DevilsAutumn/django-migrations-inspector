"""Django management command entry point for migration inspection."""

from __future__ import annotations

import shutil
from argparse import ArgumentParser
from pathlib import Path
from pydoc import pager

from django.core.management.base import BaseCommand, CommandError

from django_migration_inspector.config import InspectConfig, RiskConfig, RollbackConfig
from django_migration_inspector.domain.enums import OutputFormat, RiskAnalysisScope
from django_migration_inspector.exceptions import DjangoMigrationInspectorError
from django_migration_inspector.renderers import (
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


class Command(BaseCommand):
    """Inspect the Django migration graph and emit a stable report."""

    help = (
        "Inspect the Django migration graph and report merge nodes, multiple heads, "
        "root and leaf migrations, and dependency hotspots."
    )

    def add_arguments(self, parser: ArgumentParser) -> None:
        mode_group = parser.add_mutually_exclusive_group()
        parser.add_argument(
            "--format",
            choices=[output_format.value for output_format in OutputFormat],
            default=OutputFormat.TEXT.value,
            help="Output renderer to use.",
        )
        parser.add_argument(
            "--database",
            default="default",
            help="Django database alias used for migration state loading.",
        )
        parser.add_argument(
            "--output",
            default=None,
            help="Write the rendered report to a file instead of stdout.",
        )
        parser.add_argument(
            "--pager",
            choices=("auto", "on", "off"),
            default="auto",
            help="Page long text output when printing to an interactive terminal.",
        )
        parser.add_argument(
            "--app",
            dest="app_label",
            default=None,
            help="Limit the report to one Django app label.",
        )
        mode_group.add_argument(
            "--risk",
            action="store_true",
            help="Analyze the pending forward migration plan and report deployment risk.",
        )
        mode_group.add_argument(
            "--risk-history",
            action="store_true",
            help="Audit all visible migrations on disk and report historical risk.",
        )
        mode_group.add_argument(
            "--rollback",
            nargs=2,
            metavar=("APP_LABEL", "MIGRATION_NAME"),
            help=(
                "Simulate rollback to the requested migration target. Use 'zero' as the "
                "migration name to simulate unapplying the entire app."
            ),
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="For rollback text output, include detailed step and concern listings.",
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

    def handle(self, *args: object, **options: object) -> str | None:
        del args

        try:
            output_format = OutputFormat(str(options["format"]))
            risk_mode = bool(options["risk"])
            risk_history_mode = bool(options["risk_history"])
            rollback_mode = options["rollback"]
            database_alias = str(options["database"])
            output_path = self._normalize_optional_string(options["output"])
            pager_mode = str(options["pager"])
            raw_app_label = options["app_label"]
            app_label = None if raw_app_label in (None, "") else str(raw_app_label)
            verbose = bool(options["verbose"])
            show_operations = bool(options["show_operations"])
            why_app = self._normalize_optional_string(options["why_app"])

            self._validate_mode_specific_options(
                output_format=output_format,
                rollback_mode=rollback_mode,
                verbose=verbose,
                show_operations=show_operations,
                why_app=why_app,
            )

            if risk_mode or risk_history_mode:
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
                        if risk_history_mode
                        else RiskAnalysisScope.PENDING
                    ),
                )
                risk_service = build_default_risk_service()
                risk_report = risk_service.inspect_risk(config=risk_config)
                risk_renderer = get_risk_report_renderer(output_format=output_format)
                self._emit_rendered_output(
                    rendered_output=risk_renderer.render(risk_report),
                    output_format=output_format,
                    output_path=output_path,
                    pager_mode=pager_mode,
                )
            elif rollback_mode is not None:
                if app_label is not None:
                    raise CommandError("--app cannot be used together with --rollback.")
                if output_format in {OutputFormat.MERMAID, OutputFormat.DOT}:
                    raise CommandError(
                        "--rollback currently supports only text and json output formats."
                    )
                if not isinstance(rollback_mode, (list, tuple)) or len(rollback_mode) != 2:
                    raise CommandError(
                        "--rollback expects exactly two values: APP_LABEL and MIGRATION_NAME."
                    )
                target_app_label = str(rollback_mode[0])
                target_migration_name = str(rollback_mode[1])
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
                        verbose=verbose or show_operations,
                        show_operations=show_operations,
                        why_app=why_app,
                    ),
                )
                self._emit_rendered_output(
                    rendered_output=rollback_renderer.render(rollback_report),
                    output_format=output_format,
                    output_path=output_path,
                    pager_mode=pager_mode,
                )
            else:
                inspect_config = InspectConfig(
                    output_format=output_format,
                    database_alias=database_alias,
                    app_label=app_label,
                )
                graph_service = build_default_inspect_service()
                graph_report = graph_service.inspect_graph(config=inspect_config)
                graph_renderer = get_graph_report_renderer(output_format=output_format)
                self._emit_rendered_output(
                    rendered_output=graph_renderer.render(graph_report),
                    output_format=output_format,
                    output_path=output_path,
                    pager_mode=pager_mode,
                )
        except DjangoMigrationInspectorError as error:
            raise CommandError(str(error)) from error

        return None

    def _normalize_optional_string(self, raw_value: object) -> str | None:
        if raw_value in (None, ""):
            return None
        return str(raw_value)

    def _validate_mode_specific_options(
        self,
        *,
        output_format: OutputFormat,
        rollback_mode: object,
        verbose: bool,
        show_operations: bool,
        why_app: str | None,
    ) -> None:
        if rollback_mode is not None:
            if output_format is OutputFormat.JSON and (
                verbose or show_operations or why_app is not None
            ):
                raise CommandError(
                    "--verbose, --show-operations, and --why-app are available only for "
                    "text rollback output."
                )
            return

        if verbose or show_operations or why_app is not None:
            raise CommandError(
                "--verbose, --show-operations, and --why-app can only be used together "
                "with --rollback."
            )

    def _emit_rendered_output(
        self,
        *,
        rendered_output: str,
        output_format: OutputFormat,
        output_path: str | None,
        pager_mode: str,
    ) -> None:
        if output_path is not None:
            Path(output_path).write_text(rendered_output, encoding="utf-8")
            return

        if output_format is OutputFormat.TEXT and self._should_page_output(
            rendered_output=rendered_output,
            pager_mode=pager_mode,
        ):
            pager(rendered_output)
            return

        self.stdout.write(rendered_output, ending="")

    def _should_page_output(self, *, rendered_output: str, pager_mode: str) -> bool:
        if pager_mode == "off":
            return False
        if pager_mode == "on":
            return True

        is_tty = bool(getattr(self.stdout, "isatty", lambda: False)())
        if not is_tty:
            return False

        terminal_lines = shutil.get_terminal_size((80, 24)).lines
        return rendered_output.count("\n") > max(terminal_lines - 2, 20)
