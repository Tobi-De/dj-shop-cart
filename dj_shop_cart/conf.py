from __future__ import annotations

from django.conf import settings

CART_SESSION_KEY: str = getattr(settings, "CART_SESSION_KEY", "CART-ID")
CART_MANAGER_CLASS: str | None = getattr(settings, "CART_MANAGER_CLASS", None)
CART_PERSIST_TO_DB: bool = "dj_shop_cart" in settings.INSTALLED_APPS
CART_PRODUCT_GET_PRICE: str = getattr(settings, "CART_PRODUCT_GET_PRICE", "get_price")
