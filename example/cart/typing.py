from typing import Protocol, runtime_checkable, TypeVar, List

from django.db import models
from django.http import HttpRequest


@runtime_checkable
class IsDataclass(Protocol):
    __dataclass_fields__: dict


Variant = str | int | dict | set | list | tuple | IsDataclass

DjangoModelType = TypeVar("DjangoModelType", bound=models.Model)


class Storage(Protocol):
    request: HttpRequest

    def load(self) -> List[dict]:
        ...

    def save(self, items: List[dict]) -> None:
        ...

    def clear(self) -> None:
        ...
