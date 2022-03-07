from __future__ import annotations

from importlib import import_module

Variant = str | int | dict | set


def check_variant_type(variant: Variant) -> None:
    if not isinstance(variant, Variant):
        raise ValueError(f"{variant} does not have an allowed type")


def get_module(path: str):
    package, module = path.rsplit(".", 1)
    return getattr(import_module(package), module)
