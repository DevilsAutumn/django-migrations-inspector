"""Integration tests for the graph inspection service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, cast

from django.db.migrations.graph import MigrationGraph
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.migration import Migration
from pytest_django.plugin import DjangoDbBlocker

from django_migration_inspector.analyzers import GraphIntelligenceAnalyzer
from django_migration_inspector.config import InspectConfig
from django_migration_inspector.django_adapter.graph import build_graph_snapshot
from django_migration_inspector.domain.models import MigrationGraphSnapshot
from django_migration_inspector.exceptions import MigrationInspectionError
from django_migration_inspector.renderers.text import TextGraphReportRenderer
from django_migration_inspector.services import build_default_inspect_service


@dataclass(slots=True)
class _LoaderStub:
    disk_migrations: dict[tuple[str, str], Migration]
    graph: MigrationGraph


def _build_squashed_migration_snapshot() -> MigrationGraphSnapshot:
    class SquashedMigration(Migration):
        replaces: ClassVar[list[tuple[str, str]]] = [("trips", "0001_initial")]

    replaced_migration = Migration(name="0001_initial", app_label="trips")
    squashed_migration = SquashedMigration(name="0001_squashed_0002", app_label="trips")

    graph = MigrationGraph()
    graph.add_node(("trips", "0001_squashed_0002"), squashed_migration)
    loader = _LoaderStub(
        disk_migrations={
            ("trips", "0001_initial"): replaced_migration,
            ("trips", "0001_squashed_0002"): squashed_migration,
        },
        graph=graph,
    )

    return build_graph_snapshot(
        loader=cast(MigrationLoader, loader),
        ignored_app_labels=frozenset(),
    )


def test_graph_service_detects_merge_nodes_and_multiple_heads(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    service = build_default_inspect_service()

    with django_db_blocker.unblock():
        report = service.inspect_graph(InspectConfig())

    assert report.total_migrations == 11
    assert [merge_node.identifier for merge_node in report.merge_nodes] == [
        "inventory.0003_merge_0002_add_sku_0002_add_status"
    ]
    assert len(report.multiple_head_apps) == 1
    assert report.multiple_head_apps[0].app_label == "analytics"
    assert [head.identifier for head in report.multiple_head_apps[0].heads] == [
        "analytics.0002_add_payload",
        "analytics.0002_add_source",
    ]


def test_graph_service_can_filter_to_one_app(django_db_blocker: DjangoDbBlocker) -> None:
    service = build_default_inspect_service()

    with django_db_blocker.unblock():
        report = service.inspect_graph(InspectConfig(app_label="analytics"))

    assert report.selected_app_label == "analytics"
    assert report.total_apps == 1
    assert report.total_migrations == 3
    assert [leaf.identifier for leaf in report.leaf_nodes] == [
        "analytics.0002_add_payload",
        "analytics.0002_add_source",
    ]


def test_graph_service_rejects_ignored_app_label(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    service = build_default_inspect_service()

    with django_db_blocker.unblock():
        try:
            service.inspect_graph(InspectConfig(app_label="django_migration_inspector"))
        except MigrationInspectionError as error:
            assert "ignored because it is not a user project app" in str(error)
        else:
            raise AssertionError("Expected ignored app label to be rejected.")


def test_build_graph_snapshot_uses_active_graph_nodes_for_squashed_migrations() -> None:
    snapshot = _build_squashed_migration_snapshot()

    assert [node.key.identifier for node in snapshot.nodes] == ["trips.0001_squashed_0002"]
    assert [replacement.identifier for replacement in snapshot.nodes[0].replaces] == [
        "trips.0001_initial"
    ]


def test_graph_text_renderer_surfaces_squashed_migrations() -> None:
    snapshot = _build_squashed_migration_snapshot()
    report = GraphIntelligenceAnalyzer().analyze(
        snapshot,
        database_alias="default",
    )

    rendered = TextGraphReportRenderer().render(report)

    assert "1 squashed migration is active in this graph." in rendered
    assert "Squashed migrations:" not in rendered
    assert "replaces trips.0001_initial" not in rendered
