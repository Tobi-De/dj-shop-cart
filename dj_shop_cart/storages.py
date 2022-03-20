from __future__ import annotations

from dataclasses import dataclass

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

    def load(self) -> list[dict]:
        return self.request.session.get(self.session_key, [])

    def save(self, items: list[dict]) -> None:
        self.request.session[self.session_key] = items
        self.request.session.modified = True

    def clear(self) -> None:
        self.request.session[self.session_key] = []
        self.request.session.modified = True


@dataclass
class DBStorage:
    """
    Save the cart data to the database, use the session for unauthenticated users
    """

    request: HttpRequest

    def load(self) -> list[dict]:
        data = SessionStorage(self.request).load()
        if not self.request.user.is_authenticated:
            return data
        cart, _ = Cart.objects.get_or_create(
            customer=self.request.user, defaults={"items": data}
        )
        return cart.items

    def save(self, items: list[dict]) -> None:
        if not self.request.user.is_authenticated:
            SessionStorage(self.request).save(items)
        else:
            Cart.objects.update_or_create(
                customer=self.request.user,
                defaults={"items": items},
            )

    def clear(self) -> None:
        if not self.request.user.is_authenticated:
            SessionStorage(self.request).clear()
        else:
            Cart.objects.filter(customer=self.request.user).delete()
