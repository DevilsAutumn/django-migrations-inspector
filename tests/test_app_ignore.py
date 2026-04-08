"""Tests for default non-project app filtering."""

from __future__ import annotations

from django.apps import apps

from django_migration_inspector.django_adapter.app_ignore import (
    build_ignored_app_labels,
    should_ignore_app,
)


def test_default_ignore_logic_excludes_tooling_app() -> None:
    ignored_app_labels = build_ignored_app_labels()

    assert "django_migration_inspector" in ignored_app_labels


def test_default_ignore_logic_keeps_fixture_project_apps() -> None:
    analytics_app = apps.get_app_config("analytics")
    billing_app = apps.get_app_config("billing")

    assert should_ignore_app(analytics_app) is False
    assert should_ignore_app(billing_app) is False
