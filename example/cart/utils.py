from __future__ import annotations

from importlib import import_module
from typing import TypeVar, cast

from django.core.exceptions import ImproperlyConfigured
from django.db import models

from . import settings
from .protocols import IsDataclass

Variant = str | int | dict | set | list | tuple | IsDataclass

DjangoModelType = TypeVar("DjangoModelType", bound=models.Model)


def check_variant_type(variant: Variant) -> None:
    if not isinstance(variant, Variant):
        raise ValueError(f"{variant} does not have an allowed type")


def get_module(path: str):
    package, module = path.rsplit(".", 1)
    return getattr(import_module(package), module)


def get_product_model() -> DjangoModelType:
    """
    Returns the product model that is used by the cart.
    """
    klass = get_module(settings.CART_PRODUCT_MODEL)
    if not issubclass(klass, models.Model):
        raise ImproperlyConfigured(
            "The `CART_PRODUCT_MODEL` settings must point to a django model."
        )
    return cast(DjangoModelType, klass)
