from core.views import add_product, increase_product, empty_cart, index, remove_product
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("", index, name="index"),
    path("add-product/", add_product, name="add_product"),
    path("increase-product/", increase_product, name="increase_product"),
    path("remove-product/", remove_product, name="remove_product"),
    path("empty-cart/", empty_cart, name="empty_cart"),
    path("admin/", admin.site.urls),
]
