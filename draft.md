re
## Features

- Basic shopping cart operations, add item, remove, decrement, get_total, empty
- An effective Cart objects, can be looped though, get easily the length  of
- can be used with authenticated and anonymous users
- In case of an authenticated user, can be persisted across sessions
- simple coupon management system
- hooks to do custom actions on add, remove and empty actions
- context processor to add cart to context
- example showing how to make a middleware if needed
- configurable cart session id from django settings
- support product variation, and a way to identify uniquely production or customize the verification
- customizable add behaviors, override_quantity
- item have price
- example to write a template tags to make cart available in template
- example of how to check availability


## Not doing

- order are leave to the user
- payment processing is up to the user

```python


# settings

CART_SESSIONS_ID = "CART-ID"

# views
from example.cart import Cart
from shop.products.models import Product


def add_to_cart(request, product_id):
    product = get_objects_or_404(Product.objects.all, pk=product_id)
    ...
    cart = Cart(request)
    cart.add(product=product, quantity=quantity, price=product.price)
    ...

```
