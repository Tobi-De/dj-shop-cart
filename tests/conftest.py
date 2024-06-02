from __future__ import annotations

from importlib import import_module

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.base import SessionBase
from django.test import RequestFactory

from dj_shop_cart.cart import Cart, get_cart
from dj_shop_cart.storages import CacheStorage, DBStorage, SessionStorage
from tests.factories import ProductFactory

User = get_user_model()

PREFIXED_CART_KEY = "dj_shop_cart_a"


@pytest.fixture()
def session(settings) -> SessionBase:
    engine = import_module(settings.SESSION_ENGINE)
    return engine.SessionStore()


@pytest.fixture()
def cart(rf: RequestFactory, session: SessionBase, settings) -> Cart:
    settings.CART_STORAGE_BACKEND = "dj_shop_cart.storages.SessionStorage"
    request = rf.get("/")
    request.user = AnonymousUser()
    request.session = session
    return get_cart(request)


@pytest.fixture()
def prefixed_cart(rf: RequestFactory, session: SessionBase, settings) -> Cart:
    settings.CART_STORAGE_BACKEND = "dj_shop_cart.storages.SessionStorage"
    request = rf.get("/")
    request.user = AnonymousUser()
    request.session = session
    return get_cart(request, prefix=PREFIXED_CART_KEY)


@pytest.fixture()
def cart_db(rf: RequestFactory, user: User, session: SessionBase, settings):
    settings.CART_STORAGE_BACKEND = "dj_shop_cart.storages.DBStorage"
    request = rf.get("/")
    request.user = user
    request.session = session
    return get_cart(request)


@pytest.fixture()
def product():
    return ProductFactory()


@pytest.fixture()
def user(django_user_model: type[User]):
    return django_user_model.objects.create(username="someone", password="password")


@pytest.fixture()
def session_storage(rf: RequestFactory, session: SessionBase):
    request = rf.get("/")
    request.session = session
    return SessionStorage(request)


@pytest.fixture()
def db_storage(rf: RequestFactory, session: SessionBase, user: User):
    request = rf.get("/")
    request.session = session
    request.user = user
    return DBStorage(request)


@pytest.fixture()
def cache_storage_auth(rf: RequestFactory, user: User):
    request = rf.get("/")
    request.user = user
    return CacheStorage(request)


@pytest.fixture()
def cache_storage(rf: RequestFactory, session: SessionBase):
    request = rf.get("/")
    request.user = AnonymousUser()
    request.session = session
    return CacheStorage(request)
