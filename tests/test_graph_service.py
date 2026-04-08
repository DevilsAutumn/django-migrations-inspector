"""Integration tests for the graph inspection service."""

from __future__ import annotations

from pytest_django.plugin import DjangoDbBlocker

from django_migration_inspector.config import InspectConfig
from django_migration_inspector.exceptions import MigrationInspectionError
from django_migration_inspector.services import build_default_inspect_service


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
