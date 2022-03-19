from __future__ import annotations

from django.conf import settings

CART_SESSION_KEY: str = getattr(settings, "CART_SESSION_KEY", "CART-ID")
CART_CUSTOM_CLASS: str | None = getattr(settings, "CART_CUSTOM_CLASS", None)
CART_PERSIST_TO_DB: bool = "dj_shop_cart" in settings.INSTALLED_APPS
CART_PRODUCT_GET_PRICE_METHOD: str = getattr(
    settings, "CART_PRODUCT_GET_PRICE_METHOD", "get_price"
)
CART_CUSTOM_STORAGE_BACKEND: str = getattr(
    settings, "CART_CUSTOM_STORAGE_BACKEND", None
)
