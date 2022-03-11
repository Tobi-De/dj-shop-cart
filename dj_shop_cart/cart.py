from __future__ import annotations

import itertools
from decimal import Decimal
from typing import Iterator

from attrs import Factory, asdict, define, field
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest

from . import conf
from .protocols import Product, Storage
from .storages import DBStorage, SessionStorage
from .utils import Variant, check_variant_type, get_module

__all__ = ("Cart", "CartItem", "get_cart_manager_class")


@define(kw_only=True)
class CartItem:
    quantity: int = field(eq=False, converter=int)
    variant: Variant | None = field(default=None)
    product_pk: str = field(converter=str)
    product_class_path: str
    metadata: dict = field(factory=dict, eq=False)

    @property
    def product(self) -> Product:
        ProductClass: type[Product] = get_module(self.product_class_path)  # noqa
        return ProductClass.objects.get(pk=self.product_pk)

    @property
    def subtotal(self) -> Decimal:
        return self.price * self.quantity

    @property
    def price(self) -> Decimal:
        return self.product.get_price(self)

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
        The number of items in dj_shop_cart, that's the sum of quantities.
        """
        return sum(item.quantity for item in self._items)

    @property
    def unique_count(self) -> int:
        """
        The number of unique items in dj_shop_cart, regardless of the quantity.
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
        Returns a list of dj_shop_cart items matching the given criteria.
        """

        def get_item_dict(item: CartItem) -> dict:
            return {key: getattr(item, key) for key in criteria}

        return [item for item in self._items if get_item_dict(item) == criteria]

    def find_one(self, **criteria) -> CartItem | None:
        """
        Returns the dj_shop_cart item matching the given criteria, if no match is found return None.
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
        Add a new item to the dj_shop_cart
        :param product: An instance of a database product
        :param quantity: The quantity that will be added to the dj_shop_cart
        :param variant:  Variant details of the product
        :param metadata: Optional metadata that is attached to the item, this dictionary can contain
        anything that you would want to attach to the created item in dj_shop_cart, the only requirements about
        it is that it needs to be json serializable
        :param override_quantity: Add or override quantity if the item is already in  the dj_shop_cart
        :return: An instance of the item added
        """
        if variant:
            check_variant_type(variant)
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
        Remove an item from the dj_shop_cart entirely or partially based on the quantity
        :param product: An instance of a database product
        :param quantity: The quantity of the product to remove from the dj_shop_cart
        :param variant: Variant details of the product
        :return: The removed item with an updated quantity or None
        """
        if variant:
            check_variant_type(variant)
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
        self.save()

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
    def new(cls, request: HttpRequest, /, *, storage: Storage | None = None) -> Cart:
        """Appropriately create a new dj_shop_cart instance"""
        if not storage:
            # The first thing we do is get back the data from the session because the user could
            # authenticate himself after adding items to his dj_shop_cart, if we choose directly the db as
            # the storage we could lose data previously store in the session. Data in the session
            # have priority over the data in the database, so we migrate the data from the session to
            # the db if needed
            storage = SessionStorage(request)
            if conf.PERSIST_CART_TO_DB and request.user.is_authenticated:
                data = storage.load()
                storage = DBStorage(request)
                # we should overwrite the data in db only if the session data is empty
                if data:
                    storage.save(data)
        assert isinstance(storage, Storage)
        instance = cls(request=request, storage=storage)  # noqa
        instance._items = [CartItem(**item) for item in storage.load()]
        return instance


def get_cart_manager_class() -> type[Cart]:
    """
    Returns the correct dj_shop_cart manager class
    """
    if not conf.CART_MANAGER_CLASS:
        return Cart
    klass = get_module(conf.CART_MANAGER_CLASS)
    if not issubclass(klass, Cart):
        raise ImproperlyConfigured(
            "The `CART_MANAGER_CLASS` settings must refer to a subclass of the `Cart` class."
        )
    return klass
