# Usage

## Configuration

Configure the cart behaviour in your Django settings. All settings are optional and must be strings if defined.

| Name                          | Description                                                                                                                                                        | Default                              |
|-------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------|
| CART_SESSION_KEY              | The key used to store the cart in session                                                                                                                          | `CART-ID`                            |
| CART_CLASS                    | The path to the `Cart` class to use. If you are using a custom class it must subclass `dj_shop_cart.cart.Cart`                                                     | `dj_shop_cart.cart.Cart`             |
| CART_PRODUCT_GET_PRICE_METHOD | The method name to use to dynamically get the price on the product instance                                                                                        | `get_price`                          |
| CART_STORAGE_BACKEND          | The path to the storage backend to use. If you define a custom storage backend, it should follow the `Storage` protocol, see the **Backend Storage section** below | `dj_shop_cart.storages.SessionStorage` |
| CART_CACHE_TIMEOUT            | The cache timeout when using the **CartStorage** backend, default to 5 days.                                                                                       | 60 * 60 * 24 * 5                     |

## Examples

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

### Increase an item quantity

```python
cart.increase(item_id, quantity=20)
```

This method increase the quantity of an item that is already in the cart. It triggers the same `before_add`
and `after_add` hooks as the `cart.add` method. You can think of this as a shortcut to `cart.add` for
product that are already in the cart.

Parameters

 - **item_id**:  The cart item id.
 - **quantity**: The quantity to add.

Returns a `CartItem` or `None` if no item to increase was found.

### Remove / Decrement a product from the cart

```python
# Remove 10 from the quantity
cart.remove(item_id, quantity=10)
# Remove the whole item
cart.remove(item_id)
```

Parameters

- **item_id** : The cart item id.
- **quantity** :  An optional quantity of the product to remove from the cart.
  Indicate if you do not want to delete the item completely, if the quantity ends up being zero after the quantity is decreased, the item is completely removed.
- **variant** : Variant details of the product.

Returns a `CartItem` or `None` if no item to remove was found.

**Note**: An item is automatically removed from the cart when the associated database product is no longer available (delete from the database).

### Empty the cart

```python
cart.empty()
```
This method take no arguments.

### Attributes of a `Cart` instance

```python
def my_view(request):
    cart = Cart.new(request)
    # by looping through the cart, we return all the CartItem objects.
    for item in cart:
        print(item.subtotal)

    # find items based on product_pk, cart item id, variant details, quantity, etc.
    item = cart.find_one(product_pk=1)
    assert item in cart

    # the number of items in the cart
    print(cart.count)

    # the number of unique items
    print(cart.unique_count)

    # calling len on the cart returns the number of unique items in the cart, regardless of the quantity.
    print(len(cart))

    # attach some metadata to the cart
    cart.update_metadata({"discount": "10%"})

```

- **total** : The total cost of the cart.
- **is_empty** : A boolean value indicating whether the cart is empty or not.
- **count** :  The number of items in the cart, that's the sum of quantities.
- **unique_count** : The number of unique items in the cart, regardless of the quantity.
- **products** : A list of associated products.
- **metadata** : A dictionary containing the metadata of the cart.
- **empty(clear_metadata=True)** : Empty the cart. Takes an optional argument `clear_metadata` that defaults to `True`, if set to `False` the metadata of the cart will not be cleared.
- **update_metadata(metadata:dict)** : Update the metadata of the cart.
- **clear_metadata(\*keys:list[str])** : Clear the metadata of the cart. Takes an optional list of keys to clear, if no keys are specified, all metadata is cleared.
- **find(\*\*criteria)** : Returns a list of cart items matching the given criteria.
- **find_one(\*\*criteria)** : Returns the first cart item that matches the given criteria, if no match is found return None.
- **variants_group_by_product()** :  Return a dictionary with the products ids as keys and a list of variant as values.

### Classmethods of `Cart`

- **new(request:HttpRequest, prefix="default")** : Create a new cart instance and load existing data from the storage backend.
- **empty_all(request:HttpRequest)** : Empty all carts for the current user.

## Multiple Carts

You can manage multiple carts at the same time with the same storage using the `prefix` argument of the `Cart.new` method.

```python
cart_a = Cart.new(request, prefix="cart_a")
cart_a.add(product_a, quantity=10)
assert product_a in cart_a

cart_b = Cart.new(request, prefix="cart_b")
cart_b.add(product_b, quantity=10)
assert product_b in cart_b

assert product_a not in cart_b
assert product_b not in cart_a
```
A little tip if you don't want to have to remember to pass the right prefix each time you instantiate a new cart,
use the `partial` method from the `functools` module.

```python
from functools import partial

get_cart_a = partial(Cart.new, prefix="cart_a")
cart_a = get_cart_a(request)
cart_a.add(product_a, quantity=10)
```
### Cart Modifiers

### Properties of `CartItem`

- **id** : A unique id for the item.
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
session. Carts only live for the duration of the user session and each new session generates a new cart. By default, django
stores the session in the database, but you can [configure your session engine to use your cache backend](https://docs.djangoproject.com/en/dev/topics/http/sessions/#using-cached-sessions) to speed things up,
especially if you're using something like redis or memcached as your cache backend.


### CacheStorage

```python
# settings.py

CART_STORAGE_BACKEND = "dj_shop_cart.storages.CacheStorage"
```

This is the recommended backend if you want to store your customers' shopping carts (especially authenticated ones) beyond the duration of their
sessions. This backend stores the cart details using [Django's cache framework which](https://docs.djangoproject.com/en/dev/topics/cache/), depending on how it is configured, could be
much faster than **SessionStorage** and **DBStorage** which are both database dependent. There are a few things to keep in mind when using this backend:

- This backend storage handles both authenticated and unauthenticated users.
- Unauthenticated users' cart details are retained after the end of the current user's session but there is no way to identify that a cart belongs to a specific unauthenticated user between sessions, so if an unauthenticated user lives without login-in the cart data is lost.
- There is a timeout after which the data in a cart will be automatically deleted, the default value is 5 days, and it can be configured with the **CART_CACHE_TIMEOUT** settings.

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

