from __future__ import annotations

from dataclasses import dataclass

from django.http import HttpRequest

from . import settings
from .models import Cart


@dataclass
class SessionStorage:
    request: HttpRequest
    session_key: str = settings.CART_SESSION_KEY

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
    request: HttpRequest

    def load(self) -> list[dict]:
        cart = Cart.objects.get_or_create(
            customer=self.request.user, defaults={"items": []}
        )
        return cart.items

    def save(self, items: list[dict]) -> None:
        Cart.objects.update_or_create(
            customer=self.request.user,
            default={"items": items},
        )

    def clear(self) -> None:
        Cart.objects.filter(customer=self.request.user).delete()