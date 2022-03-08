from __future__ import annotations

from importlib import import_module

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.base import SessionBase
from django.test import RequestFactory

from cart.api import get_cart_manager_class
from tests.factories import ProductFactory

User = get_user_model()
Cart = get_cart_manager_class()


@pytest.fixture()
def session(settings) -> SessionBase:
    engine = import_module(settings.SESSION_ENGINE)
    SessionStore: type[SessionBase] = engine.SessionStore  # noqa
    return SessionStore()


@pytest.fixture()
def cart(rf: RequestFactory, session: SessionBase, settings) -> Cart:
    request = rf.get("/")
    request.user = AnonymousUser()
    request.session = session
    return Cart.new(request)


# TODO changing the settings directly in the fixture doesn't affect the cart
#   initialization


@pytest.fixture()
def cart_db(rf: RequestFactory, user: User, session: SessionBase):
    request = rf.get("/")
    request.user = user
    request.session = session
    return Cart.new(request)


@pytest.fixture()
def product():
    return ProductFactory()


@pytest.fixture()
def user(django_user_model: type[User]):
    return django_user_model.objects.create(username="someone", password="password")
