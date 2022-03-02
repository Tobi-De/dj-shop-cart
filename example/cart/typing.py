from typing import Protocol, runtime_checkable, TypeVar

from django.db import models


@runtime_checkable
class IsDataclass(Protocol):
    __dataclass_fields__: dict


Variant = str | int | dict | set | IsDataclass

DjangoModelType = TypeVar("DjangoModelType", bound=models.Model)
