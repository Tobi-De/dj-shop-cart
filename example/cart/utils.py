from importlib import import_module
from typing import cast

from django.core.exceptions import ImproperlyConfigured
from django.db import models

from . import settings
from .typing import DjangoModelType


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
