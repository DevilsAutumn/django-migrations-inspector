"""Django management command entry point for migration inspection."""

from __future__ import annotations

from argparse import ArgumentParser

from django.core.management.base import BaseCommand, CommandError

from django_migration_inspector.config import InspectConfig
from django_migration_inspector.domain.enums import OutputFormat
from django_migration_inspector.exceptions import DjangoMigrationInspectorError
from django_migration_inspector.renderers import (
    get_graph_report_renderer,
    get_risk_report_renderer,
)
from django_migration_inspector.services import (
    build_default_inspect_service,
    build_default_risk_service,
)


class Command(BaseCommand):
    """Inspect the Django migration graph and emit a stable report."""

    help = (
        "Inspect the Django migration graph and report merge nodes, multiple heads, "
        "root and leaf migrations, and dependency hotspots."
    )

    def add_arguments(self, parser: ArgumentParser) -> None:
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
            "--app",
            dest="app_label",
            default=None,
            help="Limit the report to one Django app label.",
        )
        parser.add_argument(
            "--risk",
            action="store_true",
            help="Analyze the pending forward migration plan and report deployment risk.",
        )

    def handle(self, *args: object, **options: object) -> str | None:
        del args

        try:
            output_format = OutputFormat(str(options["format"]))
            risk_mode = bool(options["risk"])
            database_alias = str(options["database"])
            raw_app_label = options["app_label"]
            app_label = None if raw_app_label in (None, "") else str(raw_app_label)
            config = InspectConfig(
                output_format=output_format,
                database_alias=database_alias,
                app_label=app_label,
            )
            if risk_mode:
                if output_format in {OutputFormat.MERMAID, OutputFormat.DOT}:
                    raise CommandError(
                        "--risk currently supports only text and json output formats."
                    )
                risk_service = build_default_risk_service()
                risk_report = risk_service.inspect_risk(config=config)
                risk_renderer = get_risk_report_renderer(output_format=output_format)
                self.stdout.write(risk_renderer.render(risk_report), ending="")
            else:
                graph_service = build_default_inspect_service()
                graph_report = graph_service.inspect_graph(config=config)
                graph_renderer = get_graph_report_renderer(output_format=output_format)
                self.stdout.write(graph_renderer.render(graph_report), ending="")
        except DjangoMigrationInspectorError as error:
            raise CommandError(str(error)) from error

        return None
