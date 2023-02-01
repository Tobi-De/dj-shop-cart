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
