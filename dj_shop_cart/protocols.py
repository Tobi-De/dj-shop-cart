from __future__ import annotations

from decimal import Decimal
from django.http import HttpRequest

try:
    from typing import Protocol, Union
except ImportError:
    from typing_extensions import Protocol


Numeric = Union[float, int, Decimal]


class Storage(Protocol):
    request: HttpRequest

    def load(self) -> dict:
        ...

    def save(self, data: dict) -> None:
        ...

    def clear(self) -> None:
        ...
