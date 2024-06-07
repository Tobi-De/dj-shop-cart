# dj-shop-cart

A simple and flexible cart manager for your django projects.

[![pypi](https://badge.fury.io/py/dj-shop-cart.svg)](https://pypi.org/project/dj-shop-cart/)
[![python](https://img.shields.io/pypi/pyversions/dj-shop-cart)](https://github.com/Tobi-De/dj-shop-cart)
[![django](https://img.shields.io/pypi/djversions/dj-shop-cart)](https://github.com/Tobi-De/dj-shop-cart)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg?)](https://github.com/Tobi-De/dj-shop-cart/blob/master/LICENSE)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## {octicon}`zap;1em;sd-text-danger` Features

- Add, remove, increase quantities, and clear items from the shopping cart.
- Manage multiple carts for the same user by using prefixes.
- Attach metadata to both cart items and the cart itself.
- Support adding different variants of the same product to a cart.
- Write custom modifiers to hook into the item addition/removal flow.
- Save authenticated users' carts to the database.
- Implement a custom **get_price** method to ensure that the cart always has up-to-date product prices.
- Maintain a reference to the associated product for each item in the cart.
- Provide a context processor for easy access to the user's cart in all Django templates.
- Offer swappable backend storage, with session and database options provided by default.


## {octicon}`package;1em;sd-text-danger` Installation

Install **dj-shop-cart** with your favorite package manager:

```bash
  pip install dj-shop-cart
```

## {octicon}`rocket;1em;sd-text-danger` Quickstart

```python3
from dj_shop_cart.cart import get_cart
from django.http import HttpRequest
from django.views.decorators.http import require_POST

from .models import Product

@require_POST
def add_product(request: HttpRequest):
    product = get_object_or_404(Product, pk=request.POST['product_id'])
    cart = get_cart(request)
    cart.add(product, quantity=int(request.POST['quantity']))
    ...
```
