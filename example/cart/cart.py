import itertools
from dataclasses import dataclass, field, asdict
from decimal import Decimal
from typing import Union, List, Type

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest

from . import models
from . import settings
from .typing import Variant
from .utils import get_module, get_product_model

__all__ = ("Cart", "CartItem", "get_cart_manager_class")

Product = get_product_model()


@dataclass(slots=True)
class CartItem:
    product_pk: str
    price: Decimal
    quantity: int = field(compare=False)
    variant: None | Variant = None

    @property
    def product(self) -> Product:
        return Product.objects.get(pk=self.product_pk)

    @property
    def subtotal(self) -> Decimal:
        return self.price * self.quantity


@dataclass
class Cart:
    request: HttpRequest
    _items: List[CartItem] = field(default_factory=list)
    _persist_to_db: bool = False

    def __post_init__(self):
        self._persist_to_db = (
                settings.PERSIST_CART_TO_DB and self.request.user.is_authenticated
        )
        if self._persist_to_db:
            obj, _ = models.Cart.objects.get_or_create(
                customer=self.request.user, defaults={"items": []}
            )
            items = obj.items
        else:
            items = self.request.session.get(settings.CART_SESSION_KEY, [])
        self._items = [CartItem(**v) for v in items]

    def __len__(self):
        return self.unique_count

    def __iter__(self):
        for item in self._items:
            yield item

    def __contains__(self, el: Product | set[Product, Variant]):
        """
        Checks if a given product or set of product and variant is in the cart.
        """
        if isinstance(el, set):
            assert len(el) != 2, "The len of the set must be exactly 2"
            return el in ({item.product, item.variant} for item in self)
        return el in self.products

    @property
    def total(self) -> Decimal:
        return sum([item.subtotal for item in self._items])

    @property
    def is_empty(self) -> bool:
        return self.unique_count == 0

    @property
    def count(self):
        """
        The number of items in cart, that's the sum of quantities.
        """
        return sum([item.quantity for item in self._items])

    @property
    def unique_count(self):
        """
        The number of unique items in cart, regardless of the quantity.
        """
        return len(self._items)

    @property
    def products(self):
        """
        The list of associated products.
        """
        return Product.objects.filter(pk__in={item.product_pk for item in self._items})

    def find(self) -> list[CartItem]:
        """
        Returns cart items base on the product and or variant
        """

    def find_first(self) -> CartItem | None:
        """
        Does the same thing as find but returns the first element or None
        """

    def add(
        self,
        product: Type[Product],
        *,
        price: Union[Decimal, str],
        quantity: int = 1,
        variant: Variant | None = None,
        override_quantity=False,
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
        if variant:
            assert isinstance(
                variant, Variant
            ), f"{variant} does not have an allowed type"
        item = CartItem(
            product_pk=str(product.pk),
            price=Decimal(str(price)),
            quantity=int(quantity),
            variant=variant,
        )
        self.before_add(item=item)
        try:
            item = self._items[self._items.index(item)]
        except ValueError:
            self._items.append(item)
        else:
            if override_quantity:
                item.quantity = item.quantity
            else:
                item += item.quantity
        self.save()
        self.after_add(item=item)
        return item

    def remove(
        self,
        product: Type[Product],
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
        item = None
        for item_ in self._items:
            if item_.product == product and item_.variant == variant:
                item = item_
        if item:
            self.before_remove(item=item)
            if quantity:
                item.quantity -= quantity
            else:
                self._items.pop(self._items.index(item))
        self.after_remove(item)
        self.save()
        return item

    def save(self) -> None:
        data = [asdict(item) for item in self._items]
        if self._persist_to_db:
            models.Cart.objects.update_or_create(
                customer=self.request.user,
                default={"items": data},
            )
        else:
            self.request.session[settings.CART_SESSION_KEY] = data
            self.request.session.modified = True

    def empty(self) -> None:
        if self._persist_to_db:
            models.Cart.objects.filter(customer=self.request.user).delete()
        else:
            self.request.session[settings.CART_SESSION_KEY] = []
            self.request.session.modified = True

    def variants_groupby_product(self) -> dict:
        """
        Return a dictonary with the products ids as keys and a list of variant as values
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

    def before_remove(self, item: CartItem) -> None:
        pass

    def after_remove(self, item: CartItem) -> None:
        pass


def get_cart_manager_class() -> Type[Cart]:
    """
    Returns the app
    """
    if not settings.CART_MANAGER_CLASS:
        return Cart
    klass = get_module(settings.CART_MANAGER_CLASS)
    if not issubclass(klass, Cart):
        raise ImproperlyConfigured(
            "The `CART_MANAGER_CLASS` settings must point to a subclass of the `Cart` class."
        )
    return klass
