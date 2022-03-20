from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from dj_shop_cart.cart import get_cart_class
from dj_shop_cart.storages import DBStorage, SessionStorage
from tests.factories import ProductFactory
from tests.models import Product

pytestmark = pytest.mark.django_db

Cart = get_cart_class()
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


def cart_is_empty(cart: Cart):
    assert cart.is_empty
    product = ProductFactory()
    cart.add(product, quantity=2)
    assert not cart.is_empty


def test_cart_is_empty_session_storage(cart: Cart):
    cart_is_empty(cart=cart)


def test_cart_is_empty_db_storage(cart_db):
    cart_is_empty(cart=cart_db)


def cart_remove_product(cart: Cart):
    product = ProductFactory()
    cart.remove(product, quantity=1)
    assert cart.is_empty
    cart.add(product, quantity=10)
    assert cart.count == 10
    cart.remove(product, quantity=2)
    assert cart.count == 8
    cart.remove(product)
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


def test_cart_custom_manager(rf, session, custom_cart_manager, product):
    request = rf.get("/")
    request.user = AnonymousUser()
    request.session = session
    cart = custom_cart_manager.new(request)
    item = cart.add(product)
    assert "before_add" in item.metadata["hooks"]
    assert "after_add" in item.metadata["hooks"]
    item = cart.remove(product)
    assert "before_remove" in item.metadata["hooks"]
    assert "after_remove" in item.metadata["hooks"]
