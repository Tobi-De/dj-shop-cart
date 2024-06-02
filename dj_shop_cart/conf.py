from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .utils import import_class

if TYPE_CHECKING:
    from .modifiers import CartModifier


class Settings:
    """
    Shadow Django's settings with a little logic
    """

    @property
    def CART_SESSION_KEY(self) -> str:
        return getattr(settings, "CART_SESSION_KEY", "CART-ID")

    @property
    def CART_CACHE_TIMEOUT(self) -> int:
        # default to 5 days
        return getattr(settings, "CART_CACHE_TIMEOUT", 60 * 60 * 24 * 5)

    @property
    def CART_MODIFIERS(self) -> list[type[CartModifier]]:
        from .modifiers import CartModifier

        cart_modifiers = getattr(settings, "CART_MODIFIERS", [])
        modifiers_classes = []

        for value in cart_modifiers:
            modifier: type[CartModifier] = import_class(value)

            if not issubclass(modifier, CartModifier):
                raise ImproperlyConfigured(
                    f"Modifier `{modifier}` must subclass `{CartModifier}`."
                )

            modifiers_classes.append(modifier)
        return modifiers_classes

    @property
    def CART_PRODUCT_GET_PRICE_METHOD(self) -> str:
        return getattr(settings, "CART_PRODUCT_GET_PRICE_METHOD", "get_price")

    @property
    def CART_STORAGE_BACKEND(self) -> object:
        backend = getattr(settings, "CART_STORAGE_BACKEND", None)
        if backend == "dj_shop_cart.storages.DBStorage":
            assert (
                "dj_shop_cart" in settings.INSTALLED_APPS
            ), "You need to add dj_shop_cart to INSTALLED_APPS to use the DBStorage"
        return import_class(backend or "dj_shop_cart.storages.SessionStorage")

    @property
    def app_is_installed(self) -> bool:
        return "dj_shop_cart" in settings.INSTALLED_APPS


conf = Settings()
