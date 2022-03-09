from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.base import SessionBase
from django.test import RequestFactory

from dj_shop_cart.cart import get_cart_manager_class
from dj_shop_cart.storages import DBStorage, SessionStorage
from tests.factories import ProductFactory
from tests.models import Product

pytestmark = pytest.mark.django_db

Cart = get_cart_manager_class()
User = get_user_model()


# TODO test with custom dj_shop_cart manager class
#   test with variants


def test_cart_init_session_storage(cart: Cart):
    assert isinstance(cart.storage, SessionStorage)
    assert len(cart) == cart.unique_count == cart.count == 0


def test_cart_init_db_storage(cart_db: Cart, settings):
    assert isinstance(cart_db.storage, DBStorage)
    assert len(cart_db) == cart_db.unique_count == cart_db.count == 0


def add_product_to_cart(cart: Cart):
    product = ProductFactory()
    cart.add(product, price=product.price, quantity=10)
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
    cart.add(product_a, price=product_a.price, quantity=10)
    cart.add(product_b, price=product_b.price, quantity=5)
    cart.add(product_a, price=product_a.price, quantity=10)
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
    cart.add(product, price=product.price, quantity=5)
    cart.add(product, price=product.price, quantity=5, override_quantity=True)
    assert len(cart) == cart.unique_count == 1
    assert cart.count == 5


def test_cart_add_override_quantity_session_storage(cart: Cart):
    add_product_override_quantity(cart=cart)


def test_cart_add_override_quantity_db_storage(cart_db: Cart):
    add_product_override_quantity(cart=cart_db)


def cart_is_empty(cart: Cart):
    assert cart.is_empty
    product = ProductFactory()
    cart.add(product, price=product.price, quantity=2)
    assert not cart.is_empty


def test_cart_is_empty_session_storage(cart: Cart):
    cart_is_empty(cart=cart)


def test_cart_is_empty_db_storage(cart_db):
    cart_is_empty(cart=cart_db)


def test_migrate_cart_from_session_to_db(
    cart: Cart, session: SessionBase, rf: RequestFactory, user: User, product: Product
):
    request = rf.get("/")
    request.user = user
    request.session = session
    cart.add(product, price=product.price, quantity=5)
    assert isinstance(cart.storage, SessionStorage)
    cart = Cart.new(request)
    assert isinstance(cart.storage, DBStorage)
    assert product in cart.products


def cart_remove_product(cart: Cart):
    product = ProductFactory()
    cart.remove(product, quantity=1)
    assert cart.is_empty
    cart.add(product, price=product.price, quantity=10)
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
    cart.add(product, price=product.price, quantity=10)
    cart.empty()
    assert cart.is_empty
    assert len(cart) == cart.count == cart.unique_count == 0


def test_empty_cart_session_storage(cart: Cart):
    empty_cart(cart=cart)


def test_empty_cart_db_storage(cart_db: Cart):
    empty_cart(cart=cart_db)


def test_cart_item_subtotal(cart: Cart, product: Product):
    cart.add(product, price=product.price, quantity=2)
    assert [item.subtotal for item in cart][0] == product.price * 2
    assert cart.total == product.price * 2


def test_cart_total(cart: Cart):
    product_a = ProductFactory()
    product_b = ProductFactory()
    cart.add(product_a, price=product_a.price, quantity=10)
    cart.add(product_b, price=product_b.price, quantity=5)
    assert cart.total == (product_a.price * 10) + (product_b.price * 5)


def test_add_product_variant_func(cart: Cart, product: Product):
    def get_variant(product):
        return product.name

    variant = get_variant(product)
    cart.add(product, price=product.price, quantity=5, variant=get_variant)
    assert cart.find_one(product=product).variant == variant


def test_cart_multiple_variants(cart: Cart, product: Product):
    variant_a = "imavarianta"
    variant_b = "imamvariantb"
    cart.add(product, price=product.price, quantity=2, variant=variant_a)
    cart.add(product, price=product.price, quantity=5, variant=variant_b)
    assert cart.unique_count == len(cart) == 2
    assert cart.find_one(product=product, variant=variant_a).quantity == 2
    assert cart.find_one(product=product, variant=variant_b).quantity == 5
    assert cart.count == 7


def test_cart_variants_group_by_product(cart: Cart, product: Product):
    variant_a = "imavarianta"
    variant_b = "imamvariantb"
    item_a = cart.add(product, price=product.price, quantity=2, variant=variant_a)
    item_b = cart.add(product, price=product.price, quantity=5, variant=variant_b)
    assert cart.variants_group_by_product() == {str(product.pk): [item_a, item_b]}


def test_cart_item_with_metadata(cart: Cart, product: Product):
    metadata = {"comment": "for some reason this item is special"}
    cart.add(product, price=product.price, quantity=2, metadata=metadata)
    assert metadata == cart.find_one(product=product).metadata
