from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.base import SessionBase
from django.core.cache import cache

from dj_shop_cart.cart import DEFAULT_CART_PREFIX
from dj_shop_cart.conf import conf
from dj_shop_cart.models import Cart
from dj_shop_cart.storages import CacheStorage, DBStorage, SessionStorage

pytestmark = pytest.mark.django_db

User = get_user_model()

data = {
    DEFAULT_CART_PREFIX: {"items": [{"1": "item1"}], "metadata": {"1": "metadata1"}}
}


def test_session_storage_load(session_storage: SessionStorage, session: SessionBase):
    assert len(session_storage.load()) == 0
    session[conf.CART_SESSION_KEY] = data
    assert session_storage.load() == data


def test_session_storage_save(session_storage: SessionStorage, session: SessionBase):
    session_storage.save(data)
    assert session[conf.CART_SESSION_KEY] == data


def test_session_storage_clear(session_storage: SessionStorage, session: SessionBase):
    session[conf.CART_SESSION_KEY] = data
    session_storage.clear()
    assert session.get(conf.CART_SESSION_KEY) is None
    assert not session_storage.load()


def test_db_storage_load_from_session(
    db_storage: DBStorage, session: SessionBase, user: User
):
    session[conf.CART_SESSION_KEY] = data
    assert db_storage.load() == data


def test_db_storage_load(db_storage: DBStorage, user: User):
    assert len(db_storage.load()) == 0
    Cart.objects.update_or_create(
        customer=user,
        defaults={"data": data},
    )
    assert db_storage.load() == data


def test_db_storage_save(db_storage: DBStorage, user: User):
    db_storage.save(data)
    assert db_storage.load() == data


def test_db_storage_empty(db_storage: DBStorage):
    db_storage.save(data)
    assert db_storage.load() == data
    db_storage.clear()
    assert len(db_storage.load()) == 0


def test_cache_storage_load(cache_storage: CacheStorage):
    assert len(cache_storage.load()) == 0
    cache.set(cache_storage._cart_id, data, timeout=None)
    assert cache_storage.load() == data


def test_cache_storage_save(cache_storage: CacheStorage):
    cache_storage.save(data)
    assert cache.get(cache_storage._cart_id) == data


def test_cache_storage_clear(cache_storage: CacheStorage):
    cache.set(cache_storage._cart_id, data, timeout=None)
    cache_storage.clear()
    assert cache.get(cache_storage._cart_id) is None
    assert not cache_storage.load()


def test_cache_storage_load_auth(cache_storage_auth: CacheStorage):
    assert len(cache_storage_auth.load()) == 0
    cache.set(cache_storage_auth._cart_id, data, timeout=None)
    assert cache_storage_auth.load() == data


def test_cache_storage_save_auth(cache_storage_auth: CacheStorage):
    cache_storage_auth.save(data)
    assert cache.get(cache_storage_auth._cart_id) == data


def test_cache_storage_clear_auth(cache_storage_auth: CacheStorage):
    cache.set(cache_storage_auth._cart_id, data, timeout=None)
    cache_storage_auth.clear()
    assert cache.get(cache_storage_auth._cart_id) is None
    assert not cache_storage_auth.load()
