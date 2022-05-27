# dj-shop-cart

A simple and flexible cart manager for your django projects.

[![pypi](https://badge.fury.io/py/dj-shop-cart.svg)](https://pypi.org/project/dj-shop-cart/)
[![python](https://img.shields.io/pypi/pyversions/dj-shop-cart)](https://github.com/Tobi-De/dj-shop-cart)
[![django](https://img.shields.io/pypi/djversions/dj-shop-cart)](https://github.com/Tobi-De/dj-shop-cart)
[![MIT License](https://img.shields.io/apm/l/atomic-design-ui.svg?)](https://github.com/Tobi-De/dj-shop-cart/blob/master/LICENSE)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

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

## Usage/Examples

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

from dj_shop_cart.cart import get_cart_class
from django.http import HttpRequest
from django.views.decorators.http import require_POST

# This function has nothing to do with the package itself
from .helpers import collect_params

Cart = get_cart_class()


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

Configure the cart behaviour in your Django settings. All settings are optional and must be strings if defined.

| Name                          | Description                                                                                                                                                        | Default                              |
|-------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------|
| CART_SESSION_KEY              | The key used to store the cart in session                                                                                                                          | `CART-ID`                            |
| CART_CLASS                    | The path to the `Cart` class to use. If you are using a custom class it must subclass `dj_shop_cart.cart.Cart`                                                     | `dj_shop_cart.cart.Cart`             |
| CART_PRODUCT_GET_PRICE_METHOD | The method name to use to dynamically get the price on the product instance                                                                                        | `get_price`                          |
| CART_STORAGE_BACKEND          | The path to the storage backend to use. If you define a custom storage backend, it should follow the `Storage` protocol, see the **Backend Storage section** below | `dj_shop_cart.storages.SessionStorage` |

## API Reference

### Instantiate a new cart

```python
from dj_shop_cart.cart import get_cart_class
from django.http import HttpRequest

Cart = get_cart_class()

def view(request:HttpRequest):
    cart = Cart.new(request)
    ...
```

The `new` method create a new cart and load existing data via the specified storage backend.

### Add a product to the cart

```python
cart.add(product, quantity=20)
```

Parameters

 - **product**: An instance of a database product.
 - **quantity**: The quantity to add.
 - **variant**:  The product variation details, when specified, are used to uniquely identify items in the cart related to the same product,
                 can be a python dictionary, a set, an integer or a string.
 - **override_quantity** : Default to `False`, if `True` instead of adding to the existing quantity, will override it
 - **metadata**: Optional metadata that is attached to the item, this dictionary can contain
                anything that you would want to attach to the created item in cart, the only requirements about
                it is that it needs to be json serializable.

Returns a `CartItem`.

### Remove / Decrement a product from the cart

```python
# Remove 10 from the quantity
cart.remove(product, quantity=10)
# Remove the whole item
cart.remove(product)
```

Parameters

- **product** : An instance of a database product.
- **quantity** :  An optional quantity of the product to remove from the cart.
  Indicate if you do not want to delete the item completely, if the quantity ends up being zero after the quantity is decreased, the item is completely removed.
- **variant** : Variant details of the product.

Returns a `CartItem` or `None` if no item to remove was found.

### Empty the cart

```python
cart.empty()
```
This method take no arguments.

### Additional Properties of the cart object

```python
def my_view(request):
    cart = Cart.new(request)
    # by looping through the cart, we return all the CartItem objects.
    for item in cart:
        print(item.subtotal)

    item = cart.find()[0]
    # you can use the in operator to check if a CartItem is in the basket, perhaps for a manually built one.
    assert item in cart

    # calling len on the cart returns the number of unique items in the cart, regardless of the quantity.
    print(len(cart))
```

- **total** : The total cost of the cart.
- **is_empty** : A boolean value indicating whether the cart is empty or not.
- **count** :  The number of items in the cart, that's the sum of quantities.
- **unique_count** : The number of unique items in the cart, regardless of the quantity.
- **products** : A list of associated products.
- **find(\*\*criteria)** : Returns a list of cart items matching the given criteria.
- **find_one(\*\*criteria)** : Returns the first cart item that matches the given criteria, if no match is found return None.
- **variants_group_by_product()** :  Return a dictionary with the products ids as keys and a list of variant as values.

### Custom Cart Class

````python
# settings.py
CART_CLASS = "your_project.somewhere_in_your_project.Cart"

# somewhere_in_your_project.py
from dj_shop_cart.cart import CartItem, Cart as DjCart


class Cart(DjCart):

    def before_add(self, item: CartItem, quantity: int) -> None:
        pass

    def after_add(self, item: CartItem) -> None:
        pass

    def before_remove(self, item: CartItem | None = None, quantity: int | None = None) -> None:
        pass

    def after_remove(self, item: CartItem | None = None) -> None:
        pass
````
The 4 methods defined in the class above are custom hooks that you can override to customize the `Add/Remove` process.

### Properties of `CartItem`

- **price** : The item price calculated via the `get_price` method.
- **subtotal** : Item price x quantity.
- **product** : The associated product.
- **variant** : Variant info specified when the product was added to the cart, default to `None`, is used to compare items in the cart.
- **metadata** : A dictionary containing the metadata specified when the product was added to the cart, not used when comparing two cart items.

## Storage Backend

The storage backend are used to store the cart items data. Two backends are provided by default, `SessionStorage` and
`DBStorage`.

### SessionStorage

```python
# settings.py

CART_STORAGE_BACKEND = "dj_shop_cart.storages.SessionStorage"
```

This is the default backend used when no one is specified. It uses the django sessions app to store carts in the user
session. Carts only live for the duration of the user session and each new session generates a new cart.

### DBStorage

```python
# settings.py

INSTALLED_APPS = [
    ...,
    "dj_shop_cart",
    ...,
]

CART_STORAGE_BACKEND = "dj_shop_cart.storages.DBStorage"
```

This backend persists users carts in the database but only when they are authenticated. There is no point in saving
a cart that is linked to a user with no account in your system, your database will be filled with carts that
can't be associated with a specific user. This backend works by using `SessionStorage` when users are not authenticated,
and then saving their cart to the database when the user authenticates. There is always only one Cart object associated with
a user at a time, so be sure to empty the cart after the checkout process to avoid reusing data from a previously processed
cart. Cart objects in the database are not automatically deleted.

### Custom storage backend

You can also create your own custom storage backend, a redis storage backend for example. You can also import and use
the provided backend storages when building your own (like the DBStorage does). You don't need to inherit a specific class,
all you need to do is write a class that defines some specific methods and attributes, a class that follows a protocol.
Now that your custom storage backend is ready, all you have to do is specify it via the `CART_STORAGE_BACKEND` settings.
The protocol to be implemented is described as follows:

```python
from typing import Protocol

from django.http import HttpRequest

class Storage(Protocol):
    request: HttpRequest

    def load(self) -> list[dict]:
        ...

    def save(self, items: list[dict]) -> None:
        ...

    def clear(self) -> None:
        ...
```



## Used By

This project is used by the following companies:

- [Fêmy bien être](https://www.femybienetre.com/)

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

## Credits

Thanks to [Jetbrains](https://jb.gg/OpenSource) for providing an Open Source license for this project.

![JetBrains Logo (Main) logo](https://resources.jetbrains.com/storage/products/company/brand/logos/jb_beam.png)

## Todos

- Add an example for a custom redis backend
- Complete the example project
- Write more tests
