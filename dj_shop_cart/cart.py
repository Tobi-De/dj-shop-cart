from __future__ import annotations

import itertools
from decimal import Decimal
from typing import Iterator, Type, TypeVar, Union, cast
from uuid import uuid4

from attrs import Factory, asdict, define, field
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.db import models
from django.http import HttpRequest

from .conf import conf
from .protocols import Storage
from .utils import get_module

__all__ = ("Cart", "CartItem", "get_cart_class")

ProductModel = TypeVar("ProductModel", bound=models.Model)
Variant = Union[str, int, dict, set]
DEFAULT_CART_PREFIX = "default"


@define(kw_only=True)
class CartItem:
    id: str = field(factory=uuid4, converter=str)
    quantity: int = field(eq=False, converter=int)
    variant: Variant | None = field(default=None)
    product_pk: str = field(converter=str)
    product_model_path: str
    metadata: dict = field(factory=dict, eq=False)

    @property
    def product(self) -> ProductModel:
        model = cast(Type[ProductModel], get_module(self.product_model_path))
        return model.objects.get(pk=self.product_pk)

    @property
    def subtotal(self) -> Decimal:
        return self.price * self.quantity

    @property
    def price(self) -> Decimal:
        return getattr(self.product, conf.CART_PRODUCT_GET_PRICE_METHOD)(self)

    @classmethod
    def from_product(
        cls,
        product: ProductModel,
        /,
        *,
        quantity: int,
        variant: Variant | None = None,
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
    request: HttpRequest
    storage: Storage
    prefix: str = field(default=DEFAULT_CART_PREFIX)
    _items: list[CartItem] = Factory(list)

    def __len__(self) -> int:
        return self.unique_count

    def __iter__(self) -> Iterator[CartItem]:
        yield from self._items

    def __contains__(self, item: CartItem) -> bool:
        return item in self

    @property
    def total(self) -> Decimal:
        return Decimal(sum(item.subtotal for item in self))

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
    def products(self) -> list[ProductModel]:
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
        product: ProductModel,
        *,
        quantity: int = 1,
        variant: Variant | None = None,
        override_quantity: bool = False,
        metadata: dict | None = None,
    ) -> CartItem:
        """
        Add a new item to the cart

        :param product: An instance of a database product
        :param quantity: The quantity that will be added to the dj_shop_cart
        :param variant:  Variant details of the product
        :param override_quantity: If true will overwrite the quantity of the item if it already exists
        :param metadata: Optional metadata that is attached to the item, this dictionary can contain
            anything that you would want to attach to the created item in cart, the only requirements about
            it is that it needs to be json serializable
        :return: An instance of the item added
        """
        quantity = int(quantity)
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
        self.before_add(item=item, quantity=quantity)
        if override_quantity:
            item.quantity = quantity
        else:
            item.quantity += quantity
        self.after_add(item=item)
        self.save()
        return item

    def increase(self, item_id: str, quantity: int = 1) -> CartItem | None:
        quantity = int(quantity)
        assert (
            quantity >= 1
        ), f"Item quantity must be greater than or equal to 1: {quantity}"
        item = self.find_one(id=item_id)
        self.before_add(item=item, quantity=quantity)
        if not item:
            return None
        item.quantity += quantity
        self.after_add(item=item)
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
        self.before_remove(item=item, quantity=quantity)
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
        data[self.prefix] = items
        self.storage.save(data)

    def empty(self, prefix: str = DEFAULT_CART_PREFIX) -> None:
        self._items = []
        data = self.storage.load()
        try:
            data.pop(prefix)
        except KeyError:
            pass
        self.storage.save(data)

    def empty_all(self) -> None:
        self._items = []
        self.storage.clear()

    def variants_group_by_product(self) -> dict[str, list[CartItem]]:
        """
        Return a dictionary with the products ids as keys and a list of variant as values.
        """
        return {
            key: list(items)
            for key, items in itertools.groupby(self, lambda item: item.product_pk)
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
    def new(cls, request: HttpRequest, prefix: str = DEFAULT_CART_PREFIX) -> Cart:
        """Appropriately create a new cart instance. This builder load existing cart if needed."""
        storage = get_module(conf.CART_STORAGE_BACKEND)(request)
        instance = cls(request=request, storage=storage, prefix=prefix)
        try:
            data = storage.load().get(prefix, [])
        except AttributeError:
            # this is a hack to support the old storage backend mechanism which was saving everything in a list
            data = {DEFAULT_CART_PREFIX: storage.load()}
            storage.clear()
        for val in data:
            try:
                item = CartItem(**val)
                _ = item.product
            except ObjectDoesNotExist:
                # If the product associated with the item is no longer in the database, we skip it
                continue
            instance._items.append(item)
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
