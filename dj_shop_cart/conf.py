from __future__ import annotations

from django.conf import settings


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
    def CART_CLASS(self) -> str:
        return getattr(settings, "CART_CLASS", "dj_shop_cart.cart.Cart")

    @property
    def CART_PRODUCT_GET_PRICE_METHOD(self) -> str:
        return getattr(settings, "CART_PRODUCT_GET_PRICE_METHOD", "get_price")

    @property
    def CART_STORAGE_BACKEND(self) -> str:
        backend = getattr(settings, "CART_STORAGE_BACKEND", None)
        if backend == "dj_shop_cart.storages.DBStorage":
            assert (
                "dj_shop_cart" in settings.INSTALLED_APPS
            ), "You need to add dj_shop_cart to INSTALLED_APPS to use the DBStorage"
        return backend or "dj_shop_cart.storages.SessionStorage"

    @property
    def app_is_installed(self) -> bool:
        return "dj_shop_cart" in settings.INSTALLED_APPS


conf = Settings()
