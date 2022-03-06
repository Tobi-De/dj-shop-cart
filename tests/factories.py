from __future__ import annotations

from factory import Faker
from factory.django import DjangoModelFactory

from tests.models import Product


class ProductFactory(DjangoModelFactory):
    name = Faker("name")
    description = ""
    price = Faker("pydecimal", positive=True, left_digits=3, right_digits=2)

    class Meta:
        model = Product
