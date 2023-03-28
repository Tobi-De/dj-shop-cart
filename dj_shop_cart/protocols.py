from __future__ import annotations

from typing import Protocol

from django.http import HttpRequest


class Storage(Protocol):
    request: HttpRequest

    def load(self) -> dict:
        ...

    def save(self, data: dict) -> None:
        ...

    def clear(self) -> None:
        ...


class Numeric(Protocol):
    def __add__(self, *args, **kwargs) -> Numeric:
        ...

    def __sub__(self, *args, **kwargs) -> Numeric:
        ...

    def __mul__(self, *args, **kwargs) -> Numeric:
        ...

    def __truediv__(self, *args, **kwargs) -> Numeric:
        ...

    def __floordiv__(self, *args, **kwargs) -> Numeric:
        ...

    def __mod__(self, *args, **kwargs) -> Numeric:
        ...

    def __pow__(self, *args, **kwargs) -> Numeric:
        ...

    def __lt__(self, *args, **kwargs) -> bool:
        ...

    def __le__(self, *args, **kwargs) -> bool:
        ...

    def __eq__(self, *args, **kwargs) -> bool:
        ...

    def __ne__(self, *args, **kwargs) -> bool:
        ...

    def __gt__(self, *args, **kwargs) -> bool:
        ...

    def __ge__(self, *args, **kwargs) -> bool:
        ...
