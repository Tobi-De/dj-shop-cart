from __future__ import annotations

from typing import Protocol, runtime_checkable

from django.http import HttpRequest


@runtime_checkable
class Storage(Protocol):
    request: HttpRequest

    def load(self) -> list[dict]:
        ...

    def save(self, items: list[dict]) -> None:
        ...

    def clear(self) -> None:
        ...
