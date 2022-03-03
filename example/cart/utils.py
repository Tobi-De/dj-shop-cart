from __future__ import annotations

from importlib import import_module

from .protocols import IsDataclass

Variant = str | int | dict | set | list | tuple | IsDataclass


def check_variant_type(variant: Variant) -> None:
    if not isinstance(variant, Variant):
        raise ValueError(f"{variant} does not have an allowed type")


def get_module(path: str):
    package, module = path.rsplit(".", 1)
    return getattr(import_module(package), module)
