from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Optional, cast

from django.http import HttpRequest

from . import conf
from .protocols import Storage
from .utils import get_module

if conf.CART_PERSIST_TO_DB:
    from .models import Cart


OptionalStorageType = ClassVar[Optional[type[Storage]]]


@dataclass
class SessionStorage:
    request: HttpRequest
    session_key: str = conf.CART_SESSION_KEY
    depends_on: OptionalStorageType = None

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
    depends_on: OptionalStorageType = SessionStorage

    def load(self) -> list[dict]:
        cart, _ = Cart.objects.get_or_create(
            customer=self.request.user, defaults={"items": []}
        )
        return cart.items

    def save(self, items: list[dict]) -> None:
        Cart.objects.update_or_create(
            customer=self.request.user,
            defaults={"items": items},
        )

    def clear(self) -> None:
        Cart.objects.filter(customer=self.request.user).delete()


def storage_factory(request: HttpRequest, storage_class: type[Storage]) -> Storage:
    storage = storage_class(request)  # noqa
    if not storage_class.depends_on:
        return storage
    data = storage_class.depends_on(request).load()
    if data:
        storage.save(data)
    return storage


def get_storage_class(request: HttpRequest) -> type[Storage]:
    if conf.CART_CUSTOM_STORAGE_BACKEND:
        return cast(type[Storage], get_module(conf.CART_CUSTOM_STORAGE_BACKEND))
    if conf.CART_PERSIST_TO_DB and request.user.is_authenticated:
        return DBStorage
    return SessionStorage
