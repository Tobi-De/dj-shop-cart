from __future__ import annotations

import uuid
from dataclasses import dataclass

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.base import SessionBase
from django.test import RequestFactory

from dj_shop_cart.cart import CartItem, get_cart, Cart
from dj_shop_cart.modifiers import CartModifier, cart_modifiers_pool
from dj_shop_cart.storages import DBStorage, SessionStorage
from tests.factories import ProductFactory
from tests.models import Product

from .conftest import PREFIXED_CART_KEY

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_cart_init_session_storage(cart: Cart):
    assert isinstance(cart.storage, SessionStorage)
    assert len(cart) == cart.unique_count == cart.count == 0


def test_cart_init_db_storage(cart_db: Cart, settings):
    assert isinstance(cart_db.storage, DBStorage)
    assert len(cart_db) == cart_db.unique_count == cart_db.count == 0


def add_product_to_cart(cart: Cart):
    product = ProductFactory()
    cart.add(product, quantity=10)
    assert len(cart) == cart.unique_count == 1
    assert cart.count == 10
    assert cart.find_one(product=product).product == product
    assert product in cart.products


def test_cart_add_session_storage(cart: Cart):
    add_product_to_cart(cart=cart)


def test_cart_add_db_storage(cart_db: Cart):
    add_product_to_cart(cart=cart_db)


def add_product_multiple_to_cart(cart: Cart):
    product_a = ProductFactory()
    product_b = ProductFactory()
    cart.add(product_a, quantity=10)
    cart.add(product_b, quantity=5)
    cart.add(product_a, quantity=10)
    assert len(cart) == cart.unique_count == 2
    assert cart.count == 25
    assert product_a in cart.products
    assert product_a in cart.products
    assert cart.find_one(product=product_a).quantity == 20
    assert cart.find_one(product=product_b).quantity == 5


def test_cart_add_multiple_session_storage(cart: Cart):
    add_product_multiple_to_cart(cart=cart)


def test_cart_add_multiple_db_storage(cart_db: Cart):
    add_product_multiple_to_cart(cart=cart_db)


def add_product_override_quantity(cart: Cart):
    product = ProductFactory()
    cart.add(product, quantity=5)
    cart.add(product, quantity=5, override_quantity=True)
    assert len(cart) == cart.unique_count == 1
    assert cart.count == 5


def test_cart_add_override_quantity_session_storage(cart: Cart):
    add_product_override_quantity(cart=cart)


def test_cart_add_override_quantity_db_storage(cart_db: Cart):
    add_product_override_quantity(cart=cart_db)


def test_cart_increase_quantity(cart: Cart):
    product = ProductFactory()
    item = cart.add(product, quantity=10)
    item = cart.increase(item.id, quantity=10)
    assert item.quantity == 20


def test_cart_increase_quantity_fake_item(cart: Cart):
    item = cart.increase(str(uuid.uuid4()), quantity=10)
    assert item is None


def cart_is_empty(cart: Cart):
    assert cart.is_empty
    product = ProductFactory()
    cart.add(product, quantity=2)
    assert not cart.is_empty


def test_cart_is_empty_session_storage(cart: Cart):
    cart_is_empty(cart=cart)


def test_cart_is_empty_db_storage(cart_db):
    cart_is_empty(cart=cart_db)

def test_cart_empty_clear_metadata(cart: Cart):
    product = ProductFactory()
    cart.add(product=product, quantity=2, metadata={"something": 1})
    cart.update_metadata({"something": 1})
    cart.empty(clear_metadata=True)
    assert cart.is_empty
    assert not cart.metadata

def test_cart_empty_not_clear_metadata(cart: Cart):
    product = ProductFactory()
    cart.add(product=product, quantity=2, metadata={"something": 1})
    cart.update_metadata({"something": 1})
    cart.empty(clear_metadata=False)
    assert cart.is_empty
    assert cart.metadata["something"] == 1


def cart_remove_product(cart: Cart):
    product = ProductFactory()
    item = cart.add(product, quantity=10)
    assert cart.count == 10
    cart.remove(item.id, quantity=2)
    assert cart.count == 8
    cart.remove(item.id)
    assert cart.is_empty


def test_cart_remove_session_storage(cart: Cart):
    cart_remove_product(cart)


def test_cart_remove_db_storage(cart_db: Cart):
    cart_remove_product(cart_db)


def empty_cart(cart: Cart):
    product = ProductFactory()
    cart.add(product, quantity=10)
    cart.empty()
    assert cart.is_empty
    assert len(cart) == cart.count == cart.unique_count == 0


def test_empty_cart_session_storage(cart: Cart):
    empty_cart(cart=cart)


def test_empty_cart_db_storage(cart_db: Cart):
    empty_cart(cart=cart_db)


def test_cart_item_subtotal(cart: Cart, product: Product):
    cart.add(product, quantity=2)
    assert [item.subtotal for item in cart][0] == product.price * 2
    assert cart.total == product.price * 2


def test_cart_total(cart: Cart):
    product_a = ProductFactory()
    product_b = ProductFactory()
    cart.add(product_a, quantity=10)
    cart.add(product_b, quantity=5)
    assert cart.total == (product_a.price * 10) + (product_b.price * 5)


def test_cart_multiple_variants(cart: Cart, product: Product):
    variant_a = "imavarianta"
    variant_b = "imamvariantb"
    cart.add(product, quantity=2, variant=variant_a)
    cart.add(product, quantity=5, variant=variant_b)
    assert cart.unique_count == len(cart) == 2
    assert cart.find_one(product=product, variant=variant_a).quantity == 2
    assert cart.find_one(product=product, variant=variant_b).quantity == 5
    assert cart.count == 7


def test_cart_variants_group_by_product(cart: Cart, product: Product):
    variant_a = "imavarianta"
    variant_b = "imamvariantb"
    item_a = cart.add(product, quantity=2, variant=variant_a)
    item_b = cart.add(product, quantity=5, variant=variant_b)
    assert cart.variants_group_by_product() == {str(product.pk): [item_a, item_b]}


def test_cart_item_with_metadata(cart: Cart, product: Product):
    metadata = {"comment": "for some reason this item is special"}
    cart.add(product, quantity=2, metadata=metadata)
    assert metadata == cart.find_one(product=product).metadata


def test_prefixed_cart(cart: Cart, prefixed_cart: Cart):
    product = ProductFactory()
    product_2 = ProductFactory()
    cart.add(product, quantity=2)
    prefixed_cart.add(product_2, quantity=2)
    assert cart.count == 2
    assert prefixed_cart.count == 2
    assert product_2 not in cart.products
    assert product not in prefixed_cart.products


def test_cart_with_metadata(cart: Cart, product: Product):
    metadata = {"comment": "for some reason this cart is special"}
    cart.update_metadata(metadata)
    cart.add(product, quantity=2, metadata=metadata)
    assert metadata == cart.metadata


def test_prefixed_cart_with_metadata(
    rf: RequestFactory, session: SessionBase, settings
):
    settings.CART_STORAGE_BACKEND = "dj_shop_cart.storages.SessionStorage"

    metadata = {"simple_cart": "metadata for simple cart"}
    metadata_2 = {"prefixed_cart": "metadata for prefixed cart"}

    user = AnonymousUser()

    first_request = rf.get("/")
    first_request.user = user
    first_request.session = session

    cart = get_cart(first_request)
    cart.update_metadata(metadata)

    prefixed_cart = get_cart(first_request, prefix=PREFIXED_CART_KEY)
    prefixed_cart.update_metadata(metadata_2)

    # reload both carts
    second_request = rf.get("/")
    second_request.user = user
    second_request.session = session

    new_cart = get_cart(second_request)
    new_prefixed_cart = get_cart(second_request, prefix=PREFIXED_CART_KEY)

    assert new_cart.metadata == metadata
    assert new_prefixed_cart.metadata == metadata_2


class TestModifier(CartModifier):
    def before_add(self, cart, item, quantity):
        print("is run")
        item.metadata["hooks"] = ["before_add"]

    def after_add(self, cart, item):
        item.metadata["hooks"] = item.metadata["hooks"] + ["after_add"]

    def before_remove(self, cart, item=None, quantity=None):
        if item:
            item.metadata["hooks"] = item.metadata["hooks"] + ["before_remove"]

    def after_remove(self, cart, item=None):
        item.metadata["hooks"] = item.metadata["hooks"] + ["after_remove"]


def test_cart_custom_modifier(rf, session, cart, product, monkeypatch):
    monkeypatch.setattr(cart_modifiers_pool, "get_modifiers", lambda: [TestModifier()])
    request = rf.get("/")
    request.user = AnonymousUser()
    request.session = session
    item = cart.add(product)
    assert "before_add" in item.metadata["hooks"]
    assert "after_add" in item.metadata["hooks"]
    item = cart.remove(item.id)
    assert "before_remove" in item.metadata["hooks"]
    assert "after_remove" in item.metadata["hooks"]


db = {}


@dataclass
class P:
    pk: str
    name: str

    @classmethod
    def get_cart_object(cls, item: CartItem):
        return db[item.product_pk]


def test_add_not_django_model(rf, session, cart):
    p_pk = str(uuid.uuid4())
    p = P(name="product not in db", pk=p_pk)
    db[p_pk] = p

    cart.add(p, quantity=1)
    assert p == list(cart)[0].product
