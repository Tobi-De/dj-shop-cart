from __future__ import annotations

import inspect
from typing import Any

from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string


def import_class(path: str) -> Any:
    value = import_string(path)
    if not inspect.isclass(value):
        raise ImproperlyConfigured(f"Specified `{value}` is not a class.")
    return value
