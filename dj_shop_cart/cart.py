from __future__ import annotations

import itertools
from decimal import Decimal
from typing import Iterator, TypeVar, Union

from attrs import Factory, asdict, define, field
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.http import HttpRequest

from .conf import conf
from .protocols import Storage
from .utils import get_module

__all__ = ("Cart", "CartItem", "get_cart_class")

Product = TypeVar("Product", bound=models.Model)
Variant = Union[str, int, dict, set]


@define(kw_only=True)
class CartItem:
    quantity: int = field(eq=False, converter=int)
    variant: Variant | None = field(default=None)
    product_pk: str = field(converter=str)
    product_class_path: str
    metadata: dict = field(factory=dict, eq=False)

    @property
    def product(self) -> Product:
        ProductClass: type[Product] = get_module(self.product_class_path)
        return ProductClass.objects.get(pk=self.product_pk)

    @property
    def subtotal(self) -> Decimal:
        return self.price * self.quantity

    @property
    def price(self) -> Decimal:
        return getattr(self.product, conf.CART_PRODUCT_GET_PRICE_METHOD)(self)

    @classmethod
    def from_product(
        cls,
        product: Product,
        /,
        *,
        quantity: int,
        variant: Variant | None = None,
        metadata: dict | None = None,
    ) -> CartItem:
        product_class_path = (
            f"{product.__class__.__module__}.{product.__class__.__name__}"
        )
        metadata = metadata or {}
        return cls(
            quantity=quantity,
            variant=variant,
            product_pk=product.pk,
            product_class_path=product_class_path,
            metadata=metadata,
        )


@define(kw_only=True)
class Cart:
    request: HttpRequest
    storage: Storage
    _items: list[CartItem] = Factory(list)

    def __len__(self) -> int:
        return self.unique_count

    def __iter__(self) -> Iterator[CartItem]:
        yield from self._items

    def __contains__(self, item: CartItem) -> bool:
        return item in self._items

    @property
    def total(self) -> Decimal:
        return Decimal(sum(item.subtotal for item in self._items))

    @property
    def is_empty(self) -> bool:
        return self.unique_count == 0

    @property
    def count(self) -> int:
        """
        The number of items in the cart, that's the sum of quantities.
        """
        return sum(item.quantity for item in self._items)

    @property
    def unique_count(self) -> int:
        """
        The number of unique items in the cart, regardless of the quantity.
        """
        return len(self._items)

    @property
    def products(self) -> list[Product]:
        """
        The list of associated products.
        """
        return [item.product for item in self._items]

    def find(self, **criteria) -> list[CartItem]:
        """
        Returns a list of cart items matching the given criteria.
        """

        def get_item_dict(item: CartItem) -> dict:
            return {key: getattr(item, key) for key in criteria}

        return [item for item in self._items if get_item_dict(item) == criteria]

    def find_one(self, **criteria) -> CartItem | None:
        """
        Returns the first cart item that matches the given criteria, if no match is found return None.
        """
        try:
            return self.find(**criteria)[0]
        except IndexError:
            return None

    def add(
        self,
        product: Product,
        *,
        quantity: int = 1,
        variant: Variant | None = None,
        metadata: dict | None = None,
        override_quantity: bool = False,
    ) -> CartItem:
        """
        Add a new item to the cart

        :param product: An instance of a database product
        :param quantity: The quantity that will be added to the dj_shop_cart
        :param variant:  Variant details of the product
        :param metadata: Optional metadata that is attached to the item, this dictionary can contain
            anything that you would want to attach to the created item in cart, the only requirements about
            it is that it needs to be json serializable
        :param override_quantity: If true will overwrite the quantity of the item if it already exists
        :return: An instance of the item added
        """
        quantity = int(quantity)
        assert quantity >= 1, f"Item quantity must be greater than 1: {quantity}"
        item = self.find_one(product=product, variant=variant)
        if not item:
            item = CartItem.from_product(
                product, quantity=0, variant=variant, metadata=metadata
            )
            self._items.append(item)
        self.before_add(item=item, quantity=quantity)
        if override_quantity:
            item.quantity = quantity
        else:
            item.quantity += quantity
        self.after_add(item=item)
        self.save()
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
        :return: The removed item with an updated quantity or None
        """
        item = self.find_one(product=product, variant=variant)
        self.before_remove(item=item, quantity=quantity)
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
        data = [asdict(item) for item in self._items]
        self.storage.save(data)

    def empty(self) -> None:
        self._items = []
        self.storage.clear()

    def variants_group_by_product(self) -> dict[str, list[CartItem]]:
        """
        Return a dictionary with the products ids as keys and a list of variant as values.
        """
        return {
            key: list(items)
            for key, items in itertools.groupby(
                self._items, lambda item: item.product_pk
            )
        }

    def before_add(self, item: CartItem, quantity: int) -> None:
        pass

    def after_add(self, item: CartItem) -> None:
        pass

    def before_remove(
        self, item: CartItem | None = None, quantity: int | None = None
    ) -> None:
        pass

    def after_remove(self, item: CartItem | None = None) -> None:
        pass

    @classmethod
    def new(cls, request: HttpRequest) -> Cart:
        """Appropriately create a new cart instance. This builder load existing cart if needed."""
        storage = get_module(conf.CART_STORAGE_BACKEND)(request)
        instance = cls(request=request, storage=storage)
        instance._items = [CartItem(**item) for item in storage.load()]
        return instance


def get_cart_class() -> type[Cart]:
    """
    Returns the correct cart manager class
    """
    klass = get_module(conf.CART_CLASS)
    if not issubclass(klass, Cart):
        raise ImproperlyConfigured(
            "The `CART_CLASS` settings must be a subclass of the `Cart` class."
        )
    return klass
