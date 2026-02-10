# dj-shop-cart

A simple and flexible cart manager for your django projects.

[![pypi](https://badge.fury.io/py/dj-shop-cart.svg)](https://pypi.org/project/dj-shop-cart/)
[![python](https://img.shields.io/pypi/pyversions/dj-shop-cart)](https://github.com/Tobi-De/dj-shop-cart)
[![django](https://img.shields.io/pypi/djversions/dj-shop-cart)](https://github.com/Tobi-De/dj-shop-cart)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg?)](https://github.com/Tobi-De/dj-shop-cart/blob/master/LICENSE)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

✨📚✨ [Read the full documentation](https://tobi-de.github.io/dj-shop-cart/)

## Features

- Add, remove, decrement and clear items from cart
- Authenticated users cart can be saved to database
- Write custom methods to easily hook into the items add / remove flow
- Custom **get_price** method to ensure that the cart always have an up-to-date products price
- Each item in the cart hold a reference to the associated product
- Metadata data can be attached to cart items
- Supports specification of product variation details
- Available context processor for easy access to the user cart in all your django templates
- Swappable backend storage, with session and database provided by default


## Installation

Install **dj-shop-cart** with pip or poetry.

```bash
  pip install dj-shop-cart
```

## Quickstart

```python3

# settings.py

TEMPLATES = [
    {
        "OPTIONS": {
            "context_processors": [
                ...,
                "dj_shop_cart.context_processors.cart", # If you want access to the cart instance in all templates
            ],
        },
    }
]

# models.py

from django.db import models
from dj_shop_cart.cart import CartItem
from dj_shop_cart.protocols import Numeric

class Product(models.Model):
    ...

    def get_price(self, item:CartItem) -> Numeric:
        """The only requirements of the dj_shop_cart package apart from the fact that the products you add
        to the cart must be instances of django based models. You can use a different name for this method
        but be sure to update the corresponding setting (see Configuration). Even if you change the name the
        function signature should match this one.
        """


# views.py

from dj_shop_cart.cart import Cart
from django.http import HttpRequest
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404

from .models import Product


@require_POST
def add_product(request: HttpRequest, product_id:int):
    product = get_object_or_404(Product.objects.all(), pk=product_id)
    quantity = int(request.POST.get("quantity"))
    cart = Cart.new(request)
    cart.add(product, quantity=quantity)
    ...


@require_POST
def remove_product(request: HttpRequest):
    item_id = request.POST.get("item_id")
    quantity = int(request.POST.get("quantity"))
    cart = Cart.new(request)
    cart.remove(item_id=item_id, quantity=quantity)
    ...


@require_POST
def empty_cart(request: HttpRequest):
    Cart.new(request).empty()
    ...

```

## Used By

This project is used by the following companies:

- [Fêmy bien être](https://www.femybienetre.com/)
- [Bjørn Art](https://bjornart.dk/)

## Development

uv is required to set up a virtualenv, install it then run the following:

```sh
uv sync
uv run pre-commit install --install-hooks
```

Tests can then be run quickly in that environment:

```sh
uv run pytest
```

## Feedback

If you have any feedback, please reach out to me at tobidegnon@proton.me.
