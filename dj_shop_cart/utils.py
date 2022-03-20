from __future__ import annotations

from importlib import import_module


def get_module(path: str) -> type:
    package, module = path.rsplit(".", 1)
    return getattr(import_module(package), module)
