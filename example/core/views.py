from __future__ import annotations

from cart.cart import get_cart_manager_class
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Product, ProductVariant

Cart = get_cart_manager_class()


def get_variant(request):
    if request.POST["product_variant"]:
        product_variant = get_object_or_404(
            ProductVariant, id=request.POST["product_variant"]
        )
        variant = {"size": product_variant.size, "color": product_variant.color}
    else:
        variant = None
    return variant


def index(request):
    return render(request, "index.html", {"product": Product.objects.all()})


@require_POST
def add_product(request):
    cart = Cart(request)
    product = get_object_or_404(Product.objects.all(), id=request.POST["product"])
    variant = get_variant(request)
    quantity = int(request.POST.get("quantity", 0))
    cart.add(product, variant=variant, price=product.price, quantity=quantity)
    return redirect("index")


@require_POST
def decrement_product(request):
    cart = Cart(request)
    product = get_object_or_404(Product.objects.all(), id=request.POST["product"])
    quantity = int(request.POST.get("quantity", 0))
    cart.add(
        product, variant=get_variant(request), price=product.price, quantity=quantity
    )
    return redirect("index")


@require_POST
def remove_product(request):
    cart = Cart(request)
    product = get_object_or_404(Product.objects.all(), id=request.POST["product"])
    cart.remove(product, variant=get_variant(request))
    return redirect("index")


@require_POST
def empty_cart(request):
    cart = Cart(request)
    cart.empty()
    return redirect("index")
