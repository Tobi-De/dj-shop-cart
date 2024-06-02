from __future__ import annotations

from typing import TYPE_CHECKING

from .conf import conf

if TYPE_CHECKING:
    from .cart import Cart, CartItem


class CartModifier:
    def before_add(self, cart: Cart, item: CartItem, quantity: int) -> None: ...

    def after_add(self, cart: Cart, item: CartItem) -> None: ...

    def before_remove(
        self, cart: Cart, item: CartItem, quantity: int | None = None
    ) -> None: ...

    def after_remove(self, cart: Cart, item: CartItem) -> None: ...


class CartModifiersPool:
    """
    Pool for storing modifier instances.
    """

    def __init__(self) -> None:
        self._modifiers: list[CartModifier] | None = None

    def get_modifiers(self) -> list[CartModifier]:
        """
        Returns modifier instances.

        Returns:
            list: Modifier instances
        """
        if self._modifiers is None:
            self._modifiers = [M() for M in conf.CART_MODIFIERS]
        return self._modifiers


cart_modifiers_pool = CartModifiersPool()
