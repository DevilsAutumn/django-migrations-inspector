"""Django settings for the fixture project."""

from __future__ import annotations

SECRET_KEY = "django-migration-inspector-tests"
DEBUG = True
USE_TZ = True
ROOT_URLCONF = "tests.fixtures.test_project.urls"
MIDDLEWARE: list[str] = []
INSTALLED_APPS = [
    "django_migration_inspector",
    "tests.fixtures.test_project.test_apps.analytics",
    "tests.fixtures.test_project.test_apps.catalog",
    "tests.fixtures.test_project.test_apps.inventory",
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

