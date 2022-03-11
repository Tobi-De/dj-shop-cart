from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from django.db.models.manager import BaseManager
from django.http import HttpRequest

if TYPE_CHECKING:
    from .cart import CartItem


@runtime_checkable
class Storage(Protocol):
    request: HttpRequest

    def load(self) -> list[dict]:
        ...

    def save(self, items: list[dict]) -> None:
        ...

    def clear(self) -> None:
        ...


# fixme
@runtime_checkable
class Product(Protocol):
    pk: Any
    objects: BaseManager

    def get_price(self, item: CartItem):
        ...
