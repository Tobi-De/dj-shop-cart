from __future__ import annotations

from dataclasses import dataclass

from django.core.cache import cache
from django.http import HttpRequest

from .conf import conf

if conf.app_is_installed:
    from .models import Cart


@dataclass
class SessionStorage:
    """
    Save the cart data to the user session
    """

    request: HttpRequest
    session_key: str = conf.CART_SESSION_KEY

    def load(self) -> dict:
        return self.request.session.get(self.session_key, {})

    def save(self, data: dict) -> None:
        self.request.session[self.session_key] = data
        self.request.session.modified = True

    def clear(self) -> None:
        self.request.session.pop(self.session_key, None)
        self.request.session.modified = True


@dataclass
class DBStorage:
    """
    Save the cart data to the database, use the session for unauthenticated users
    """

    request: HttpRequest

    def load(self) -> dict:
        data = SessionStorage(self.request).load()
        if not self.request.user.is_authenticated:
            return data
        cart, _ = Cart.objects.get_or_create(
            customer=self.request.user, defaults={"items": data}
        )
        return cart.items

    def save(self, data: dict) -> None:
        if not self.request.user.is_authenticated:
            SessionStorage(self.request).save(data)
        else:
            Cart.objects.update_or_create(
                customer=self.request.user,
                defaults={"items": data},
            )

    def clear(self) -> None:
        if not self.request.user.is_authenticated:
            SessionStorage(self.request).clear()
        else:
            Cart.objects.filter(customer=self.request.user).delete()


@dataclass
class CacheStorage:
    """Use django cache backend to store cart details"""

    request: HttpRequest
    timeout: int = conf.CART_CACHE_TIMEOUT
    _cache_key: str = conf.CART_SESSION_KEY

    @property
    def _cart_id(self) -> str:
        id_ = (
            str(self.request.user.pk)
            if self.request.user.is_authenticated
            else str(self.request.session.session_key)
        )
        return f"{self._cache_key}-{id_}"

    def load(self) -> list[dict]:
        return cache.get(self._cart_id, {})

    def save(self, data: dict) -> None:
        cache.set(self._cart_id, data, timeout=self.timeout)

    def clear(self) -> None:
        cache.delete(self._cart_id)
