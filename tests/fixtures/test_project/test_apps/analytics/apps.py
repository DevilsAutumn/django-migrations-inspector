"""App configuration for the analytics fixture app."""

from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    """Register the analytics fixture app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.fixtures.test_project.test_apps.analytics"
    label = "analytics"

