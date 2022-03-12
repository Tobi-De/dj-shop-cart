# dj-shop-cart

A simple and flexible cart manager for your django projects.

[![pypi](https://badge.fury.io/py/dj-shop-cart.svg)](https://pypi.org/project/dj-shop-cart/)
[![python](https://img.shields.io/pypi/pyversions/dj-shop-cart)](https://github.com/Tobi-De/dj-shop-cart)
[![MIT License](https://img.shields.io/apm/l/atomic-design-ui.svg?)](https://github.com/Tobi-De/dj-shop-cart/blob/master/LICENSE)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**This is a work in progress, expect api breaking changes, pin the exact version you are using**

## Features

- Add, remove, decrement and clear items from cart
- Authenticated users cart can be saved to database
- Write custom methods to easily hook into the items add / remove flow
- Custom **get_price** method to ensure that the cart always have an up-to-date products price
- Each item in the cart hold a reference to the associated product
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

# models.py

from django.db import models
from dj_shop_cart.cart import CartItem
from decimal import Decimal

class Product(models.Model):
    ...

    def get_price(self, item:CartItem)->Decimal:
        """The only requirements of the dj_shop_cart package apart from the fact that the products you add
        to the cart must be instances of django based models. You can use a different name for this method
        but be sure to update the corresponding setting (see Configuration). Even if you change the name the
        function signature should match this one.
        """


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

## Configuration

Configure the cart behaviour in your Django settings. All settings are optional.

| Name                   | Type | Description                                                                                                       | Default   |
|------------------------|------|-------------------------------------------------------------------------------------------------------------------|-----------|
| CART_SESSION_KEY       | str  | The key used to store the cart in session                                                                            | CART-ID   |
| CART_MANAGER_CLASS     | str  | The path to a custom **Cart** manager class. The custom class need to be a subclass of **dj_shop_cart.cart.Cart** | None      |
| CART_PRODUCT_GET_PRICE | str  | The method name to use to dynamically get the price on the product instance                                       | get_price |

## Development

Poetry is required (not really, you can set up the environment however you want and install the requirements
manually) to set up a virtualenv, install it then run the following:

```sh
poetry install
pre-commit install --install-hooks
```

Tests can then be run quickly in that environment:

```sh
pytest
```

## Feedback

If you have any feedback, please reach out to me at degnonfrancis@gmail.com

## Todos

- Add api reference in readme
- Add Used by section to readme
- More examples
- Complete the example project
- Write more tests
