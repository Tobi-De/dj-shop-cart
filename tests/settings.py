from __future__ import annotations

from typing import Any

SECRET_KEY = "NOTASECRET"

ALLOWED_HOSTS: list[str] = []

DATABASES: dict[str, dict[str, Any]] = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "tests",
    "dj_shop_cart",
]

MIDDLEWARE: list[str] = []

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "OPTIONS": {"context_processors": []},
    }
]

USE_TZ = True
