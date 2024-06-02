from __future__ import annotations

from django.http import HttpRequest

from .cart import get_cart


def cart(request: HttpRequest) -> dict:
    return {"cart": get_cart(request)}
