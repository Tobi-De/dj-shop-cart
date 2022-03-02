from django.conf import settings

CART_SESSION_KEY: str = getattr(settings, "CART_SESSION_KEY", "CART-ID")
CART_PRODUCT_MODEL: str = settings.CART_PRODUCT_MODEL
CART_MANAGER_CLASS: str | None = getattr(settings, "CART_MANAGER_CLASS", None)
PERSIST_CART_TO_DB: bool = False  # "cart" in settings.INSTALLED_APPS
