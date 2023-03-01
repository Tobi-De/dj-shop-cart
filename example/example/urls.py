from __future__ import annotations

from core.views import add_product, decrement_product, empty_cart, index, remove_product
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("", index, name="index"),
    path("add-product/", add_product, name="add_product"),
    path("decrement-product/", decrement_product, name="decrement_product"),
    path("remove-product/<str:item_id>", remove_product, name="remove_product"),
    path("empty-cart/", empty_cart, name="empty_cart"),
    path("admin/", admin.site.urls),
]
