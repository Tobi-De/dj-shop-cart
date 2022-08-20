from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.template import loader
from django.http import HttpResponse

from dj_shop_cart.cart import get_cart_class

from .models import Product, ProductVariant

Cart = get_cart_class()


def get_variant(product_variant):
    if product_variant != "":
        product_variant = get_object_or_404(
            ProductVariant, id=product_variant
        )
        variant = {"color": product_variant.color}
    else:
        variant = None
    return variant


def index(request):
    cart = Cart.new(request)

    template = loader.get_template('core/index.html')
    products = []
    for product in Product.objects.all().values():
        product["variants"] = list(ProductVariant.objects.filter(product_id = product["id"]))
        products.append(product)
    context = {
        "cart": cart,
        "products": products,
        "total": cart.total,
    }
    return HttpResponse(template.render(context, request))


@require_POST
def add_product(request):
    cart = Cart.new(request)
    product = get_object_or_404(Product.objects.all(), name=request.POST.get("product"))
    variant = get_variant(request.POST.get("product_variant"))
    quantity = int(request.POST.get("quantity"))
    cart.add(product, variant=variant, quantity=quantity)
    return redirect("index")


@require_POST
def increase_product(request):
    cart = Cart.new(request)
    cart.increase(request.POST.get("id"), quantity=+1)
    return redirect("index")


@require_POST
def remove_product(request):
    cart = Cart.new(request)
    cart.remove(request.POST.get("id"))
    return redirect("index")


@require_POST
def empty_cart(request):
    cart = Cart.new(request)
    cart.empty()
    return redirect("index")
