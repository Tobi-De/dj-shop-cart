from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.base import SessionBase

from dj_shop_cart.conf import conf
from dj_shop_cart.models import Cart
from dj_shop_cart.storages import DBStorage, SessionStorage

pytestmark = pytest.mark.django_db

User = get_user_model()

items = [{"1": "item1"}]


def test_session_storage_load(session_storage: SessionStorage, session: SessionBase):
    assert len(session_storage.load()) == 0
    session[conf.CART_SESSION_KEY] = items
    assert session_storage.load() == items


def test_session_storage_save(session_storage: SessionStorage, session: SessionBase):
    session_storage.save(items)
    assert session[conf.CART_SESSION_KEY] == items


def test_session_storage_clear(session_storage: SessionStorage, session: SessionBase):
    session[conf.CART_SESSION_KEY] = items
    session_storage.clear()
    assert session[conf.CART_SESSION_KEY] == []
    assert not session_storage.load()


def test_db_storage_load_from_session(
    db_storage: DBStorage, session: SessionBase, user: User
):
    session[conf.CART_SESSION_KEY] = items
    assert db_storage.load() == items


def test_db_storage_load(db_storage: DBStorage, user: User):
    assert len(db_storage.load()) == 0
    Cart.objects.update_or_create(
        customer=db_storage.request.user, defaults={"items": items}
    )
    assert db_storage.load() == items


def test_db_storage_save(db_storage: DBStorage, user: User):
    db_storage.save(items)
    assert db_storage.load() == items


def test_db_storage_empty(db_storage: DBStorage):
    db_storage.save(items)
    assert db_storage.load() == items
    db_storage.clear()
    assert len(db_storage.load()) == 0
