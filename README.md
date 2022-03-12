# dj-shop-cart

A simple and flexible cart manager for your django projects.

[![pypi](https://badge.fury.io/py/dj-shop-cart.svg)](https://pypi.org/project/dj-shop-cart/)
[![python](https://img.shields.io/pypi/pyversions/dj-shop-cart)](https://github.com/Tobi-De/dj-shop-cart)
[![MIT License](https://img.shields.io/apm/l/atomic-design-ui.svg?)](https://github.com/Tobi-De/dj-shop-cart/blob/master/LICENSE)

**This is a work in progress, expect api breaking changes, pin the exact version you are using**

## Features

- Add, remove, decrement and clear items from cart
- Authenticated users cart can be saved to database
- Write custom methods to easily hook into the items add / remove flow
- Custom **get_price** method to ensure that the cart always have an up-to-date products price
- Access to your django database **Product** instance from the cart items
- Metadata data can be attached to cart items
- Supports specification of product variation details
- Available context processor for easy access to the user cart in all your django templates


## Installation

Install **dj-shop-cart** with pip or poetry.

```bash
  pip install dj-shop-cart
```

## Usage/Examples

```python3

# settings.py

INSTALLED_APPS = [
    ...,
    "dj_shop_cart", # If you want the cart to be stored in the database when users are authenticated
    ...,
]

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

# views.py

from dj_shop_cart.cart import get_cart_manager_class
from django.http import HttpRequest
from django.views.decorators.http import require_POST

from .helpers import collect_params

Cart = get_cart_manager_class()


@require_POST
def add_product(request: HttpRequest):
    product, quantity = collect_params(request)
    cart = Cart.new(request)
    cart.add(product, quantity=quantity)
    ...


@require_POST
def remove_product(request: HttpRequest):
    product, quantity = collect_params(request)
    cart = Cart.new(request)
    cart.remove(product, quantity=quantity)
    ...


@require_POST
def empty_cart(request: HttpRequest):
    Cart.new(request).empty()
    ...

```



## Feedback

If you have any feedback, please reach out to me at degnonfrancis@gmail.com

## Todos

- More examples
- Add api reference
- Add Used by section to readme
- Write more tests
- Add local dev section to readme
