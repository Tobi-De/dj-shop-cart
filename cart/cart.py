from __future__ import annotations

import itertools
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Iterator, TypeVar

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.http import HttpRequest

from . import conf
from .protocols import Storage
from .storages import DBStorage, SessionStorage
from .utils import Variant, check_variant_type, get_module

__all__ = ("Cart", "get_cart_manager_class")

Product = TypeVar("Product", bound=models.Model)


@dataclass(slots=True)
class CartItem:
    price: Decimal = field(compare=False)
    quantity: int = field(compare=False)
    variant: Variant | None = None
    _product_pk: str | None = None
    _product_class_path: str | None = None

    @property
    def product_pk(self) -> str | None:
        return self._product_pk

    @property
    def product(self) -> Product:
        ProductClass: type[Product] = get_module(self._product_class_path)  # noqa
        return ProductClass.objects.get(pk=self._product_pk)

    @property
    def subtotal(self) -> Decimal:
        return self.price * self.quantity

    @classmethod
    def from_product(
        cls,
        product: Product,
        price: Decimal | str,
        quantity: int,
        variant: Variant | None = None,
    ) -> CartItem:
        instance = cls(
            price=Decimal(str(price)), quantity=int(quantity), variant=variant
        )
        instance._product_pk = str(product.pk)
        instance._product_class_path = (
            f"{product.__class__.__module__}.{product.__class__.__name__}"
        )
        return instance

    def as_dict(self) -> dict:
        data = asdict(self)
        data["price"] = str(self.price)
        return data


@dataclass(slots=True)
class Cart:
    request: HttpRequest
    storage: Storage | None = None
    _items: list[CartItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.storage:
            # The first thing we do is get back the data from the session because the user could
            # authenticate himself after adding items to his cart, if we choose directly the db as
            # the storage we could lose data previously store in the session. Data in the session
            # have priority over the data in the database, so we migrate the data from the session to
            # the db if needed
            self.storage = SessionStorage(self.request)
            if conf.PERSIST_CART_TO_DB and self.request.user.is_authenticated:
                data = self.storage.load()
                self.storage = DBStorage(self.request)
                self.storage.save(data)
        assert isinstance(self.storage, Storage)
        self._items = [CartItem(**item) for item in self.storage.load()]

    def __len__(self) -> int:
        return self.unique_count

    def __iter__(self) -> Iterator:
        yield from self._items

    def __contains__(self, item: CartItem) -> bool:
        return item in self._items

    @property
    def total(self) -> Decimal:
        return sum(item.subtotal for item in self._items)

    @property
    def is_empty(self) -> bool:
        return self.unique_count == 0

    @property
    def count(self) -> int:
        """
        The number of items in cart, that's the sum of quantities.
        """
        return sum(item.quantity for item in self._items)

    @property
    def unique_count(self) -> int:
        """
        The number of unique items in cart, regardless of the quantity.
        """
        return len(self._items)

    @property
    def products(self) -> list[Product]:
        """
        The list of associated products.
        """
        return [item.product for item in self._items]

    def find(self, **criteria: dict) -> list[CartItem]:
        """
        Returns a list of cart items matching the given criteria.
        """

        def get_item_dict(item: CartItem) -> dict:
            return {key: getattr(item, key) for key in criteria}

        return [item for item in self._items if get_item_dict(item) == criteria]

    def find_one(self, **criteria: dict) -> CartItem | None:
        """
        Returns the cart item matching the given criteria, if no match is found return None.
        """
        try:
            return self.find(**criteria)[0]
        except IndexError:
            return None

    def add(
        self,
        product: Product,
        *,
        price: Decimal | str,
        quantity: int = 1,
        variant: Variant | callable[[Product], Variant] | None = None,
        override_quantity: bool = False,
    ) -> CartItem:
        """
        Add a new item to the cart.
        :param product: An instance of a database product
        :param price: The price of the product
        :param quantity: The quantity that will be added to the cart
        :param variant:  Variant details of the product
        :param override_quantity: Add or override quantity if the item is already in  the cart
        :return: An instance of the item added
        """
        if callable(variant):
            variant = variant(product)
        if variant:
            check_variant_type(variant)
        price = Decimal(str(price))
        quantity = int(quantity)
        assert quantity >= 1, "Can't add an item with a quantity less than 1"
        item = self.find_one(product=product, variant=variant)
        if not item:
            item = CartItem.from_product(
                product=product, price=price, quantity=0, variant=variant
            )
            self._items.append(item)
        self.before_add(item=item)
        if override_quantity:
            item.quantity = quantity
        else:
            item.quantity += quantity
        self.save()
        self.after_add(item=item)
        return item

    def remove(
        self,
        product: Product,
        *,
        quantity: int | None = None,
        variant: Variant | None = None,
    ) -> CartItem | None:
        """
        Remove an item from the cart entirely or partially based on the quantity
        :param product: An instance of a database product
        :param quantity: The quantity of the product to remove from the cart
        :param variant: Variant details of the product
        :return: The removed item with updated quantity if it exists
        """
        if variant:
            check_variant_type(variant)
        item = self.find_one(product=product, variant=variant)
        self.before_remove(item=item)
        if not item:
            return None
        if quantity:
            item.quantity -= int(quantity)
        else:
            item.quantity = 0
        if item.quantity <= 0:
            self._items.pop(self._items.index(item))
        self.after_remove(item=item)
        self.save()
        return item

    def save(self) -> None:
        data = [item.as_dict() for item in self._items]
        self.storage.save(data)

    def empty(self) -> None:
        self._items = []
        self.storage.clear()
        self.save()

    def variants_group_by_product(self) -> dict:
        """
        Return a dictionary with the products ids as keys and a list of variant as values.
        """
        return {
            key: list(items)
            for key, items in itertools.groupby(
                self._items, lambda item: item.product_pk
            )
        }

    def before_add(self, item: CartItem) -> None:
        pass

    def after_add(self, item: CartItem) -> None:
        pass

    def before_remove(self, item: CartItem | None = None) -> None:
        pass

    def after_remove(self, item: CartItem | None = None) -> None:
        pass


def get_cart_manager_class() -> type[Cart]:
    """
    Returns the app
    """
    if not conf.CART_MANAGER_CLASS:
        return Cart
    klass = get_module(conf.CART_MANAGER_CLASS)
    if not issubclass(klass, Cart):
        raise ImproperlyConfigured(
            "The `CART_MANAGER_CLASS` settings must point to a subclass of the `Cart` class."
        )
    return klass
