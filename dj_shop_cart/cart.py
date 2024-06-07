from __future__ import annotations

import contextlib
import itertools
from collections.abc import Iterator
from functools import cached_property
from typing import TypeVar, cast
from uuid import uuid4

from attrs import Factory, asdict, define, field
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.http import HttpRequest

from .conf import conf
from .modifiers import cart_modifiers_pool
from .protocols import Numeric, Storage
from .utils import import_class

__all__ = ("Cart", "CartItem", "get_cart_class", "get_cart")

DjangoModel = TypeVar("DjangoModel", bound=models.Model)
DEFAULT_CART_PREFIX = "default"


@define(kw_only=True)
class CartItem:
    id: str = field(factory=uuid4, converter=str)
    quantity: int = field(eq=False, converter=int)
    variant: str | None = field(default=None)
    product_pk: str = field(converter=str)
    product_model_path: str
    metadata: dict = field(factory=dict, eq=False)

    @cached_property
    def product(self) -> DjangoModel:
        model = cast(type[DjangoModel], import_class(self.product_model_path))
        if func := getattr(model, "get_cart_object", None):
            # this is a hack to allow to use a product that is not a django
            # model instance / instance not already save in db
            return func(self)  # noqa
        return model.objects.get(pk=self.product_pk)

    @property
    def subtotal(self) -> Numeric:
        return self.price * self.quantity

    @property
    def price(self) -> Numeric:
        return getattr(self.product, conf.CART_PRODUCT_GET_PRICE_METHOD)(self)

    @classmethod
    def from_product(
        cls,
        product: DjangoModel,
        quantity: int,
        variant: str | None = None,
        metadata: dict | None = None,
    ) -> CartItem:
        metadata = metadata or {}
        return cls(
            quantity=quantity,
            variant=variant,
            product_pk=product.pk,
            product_model_path=f"{product.__class__.__module__}.{product.__class__.__name__}",
            metadata=metadata,
        )


@define(kw_only=True)
class Cart:
    storage: Storage
    prefix: str = field(default=DEFAULT_CART_PREFIX)
    _metadata: dict = field(factory=dict)
    _items: list[CartItem] = Factory(list)

    def __len__(self) -> int:
        return self.unique_count

    def __iter__(self) -> Iterator[CartItem]:
        yield from self._items

    def __contains__(self, item: CartItem) -> bool:
        return item in self

    @property
    def items(self) -> list[CartItem]:
        return self._items

    @property
    def total(self) -> Numeric:
        return sum(item.subtotal for item in self)

    @property
    def is_empty(self) -> bool:
        return self.unique_count == 0

    @property
    def count(self) -> int:
        """
        The number of items in the cart, that's the sum of quantities.
        """
        return sum(item.quantity for item in self)

    @property
    def unique_count(self) -> int:
        """
        The number of unique items in the cart, regardless of the quantity.
        """
        return len(self._items)

    @property
    def products(self) -> list[DjangoModel]:
        """
        The list of associated products.
        """
        return [item.product for item in self]

    def find(self, **criteria) -> list[CartItem]:
        """
        Returns a list of cart items matching the given criteria.
        """

        def get_item_dict(item: CartItem) -> dict:
            return {key: getattr(item, key) for key in criteria}

        return [item for item in self if get_item_dict(item) == criteria]

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
        product: DjangoModel,
        *,
        quantity: int = 1,
        variant: str | None = None,
        override_quantity: bool = False,
        metadata: dict | None = None,
    ) -> CartItem:
        """
        Add a new item to the cart

        :param product: An instance of a database product
        :param quantity: The quantity that will be added to the dj_shop_cart (default to 1)
        :param variant:  Variant details of the product
        :param override_quantity: If true will overwrite the quantity of the item if it already exists
        :param metadata: Optional metadata that is attached to the item, this dictionary can contain
            anything that you would want to attach to the created item in cart, the only requirements about
            it is that it needs to be json serializable
        :return: An instance of the item added
        """
        assert (
            quantity >= 1
        ), f"Item quantity must be greater than or equal to 1: {quantity}"
        item = self.find_one(product=product, variant=variant)
        if not item:
            item = CartItem.from_product(
                product, quantity=0, variant=variant, metadata=metadata
            )
            self._items.append(item)
        if metadata:
            item.metadata.update(metadata)

        for modifier in cart_modifiers_pool.get_modifiers():
            modifier.before_add(cart=self, item=item, quantity=quantity)

        if override_quantity:
            item.quantity = quantity
        else:
            item.quantity += quantity

        for modifier in cart_modifiers_pool.get_modifiers():
            modifier.after_add(cart=self, item=item)

        self.save()
        return item

    def increase(
        self,
        item_id: str,
        *,
        quantity: int = 1,
    ) -> CartItem | None:
        """
        Increase the quantity of an item already in the cart

        :param item_id: The cart item id
        :param quantity: The quantity to add
        :return: The updated item  or None
        """
        item = self.find_one(id=item_id)
        if not item:
            return

        for modifier in cart_modifiers_pool.get_modifiers():
            modifier.before_add(cart=self, item=item, quantity=quantity)

        item.quantity += quantity

        for modifier in cart_modifiers_pool.get_modifiers():
            modifier.after_add(cart=self, item=item)

        self.save()
        return item

    def remove(
        self,
        item_id: str,
        *,
        quantity: int | None = None,
    ) -> CartItem | None:
        """
        Remove an item from the cart entirely or partially based on the quantity

        :param item_id: The cart item id
        :param quantity: The quantity of the product to remove from the cart
        :return: The removed item with an updated quantity or None
        """
        item = self.find_one(id=item_id)
        if not item:
            return None

        for modifier in cart_modifiers_pool.get_modifiers():
            modifier.before_remove(cart=self, item=item, quantity=quantity)

        if quantity:
            item.quantity -= int(quantity)
        else:
            item.quantity = 0
        if item.quantity <= 0:
            self._items.pop(self._items.index(item))

        for modifier in cart_modifiers_pool.get_modifiers():
            modifier.after_remove(cart=self, item=item)

        self.save()
        return item

    def save(self) -> None:
        items = []
        for item in self._items:
            try:
                _ = item.product
            except ObjectDoesNotExist:
                # If the product associated with the item is no longer in the database, we skip it
                continue
            items.append(asdict(item))
        # load storage old data to avoid overwriting
        data = self.storage.load()
        data[self.prefix] = {"items": items, "metadata": self.metadata}
        self.storage.save(data)

    def variants_group_by_product(self) -> dict[str, list[CartItem]]:
        """
        Return a dictionary with the products ids as keys and a list of variant as values.
        """
        return {
            key: list(items)
            for key, items in itertools.groupby(self, lambda item: item.product_pk)
        }

    @property
    def metadata(self) -> dict:
        return self._metadata

    def update_metadata(self, metadata: dict) -> None:
        self._metadata.update(metadata)
        self.save()

    def clear_metadata(self, *keys: list[str]) -> None:
        if keys:
            for key in keys:
                self._metadata.pop(key, None)
        else:
            self._metadata = {}
        self.save()

    def empty(self, clear_metadata: bool = True) -> None:
        """Delete all items in the cart, and optionally clear the metadata."""
        self._items = []
        if clear_metadata:
            self._metadata = {}
        data = self.storage.load()
        data[self.prefix] = {"items": self._items, "metadata": self.metadata}
        self.storage.save(data)

    def empty_all(self) -> None:
        """Empty all carts for the current user"""
        self.storage.clear()

    @classmethod
    def new(cls, storage: Storage, prefix: str = DEFAULT_CART_PREFIX) -> Cart:
        """Appropriately create a new cart instance. This builder load existing cart if needed."""
        instance = cls(storage=storage, prefix=prefix)
        try:
            data = storage.load().get(prefix, {})
        except AttributeError:
            data = {}

        metadata = data.get("metadata", {})
        items = data.get("items", [])
        for val in items:
            try:
                item = CartItem(**val)
                _ = item.product
            except ObjectDoesNotExist:
                # If the product associated with the item is no longer in the database, we skip it
                continue
            instance._items.append(item)
        instance._metadata = metadata
        return instance


def get_cart(request: HttpRequest, prefix: str = DEFAULT_CART_PREFIX) -> Cart:
    storage = conf.CART_STORAGE_BACKEND(request)
    return Cart.new(storage=storage, prefix=prefix)


def get_cart_class() -> type[Cart]:
    """
    Returns the correct cart manager class
    """
    return Cart
