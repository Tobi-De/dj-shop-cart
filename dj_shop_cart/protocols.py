from __future__ import annotations

from typing import ClassVar, Protocol, runtime_checkable

from django.http import HttpRequest


@runtime_checkable
class Storage(Protocol):
    request: HttpRequest
    depends_on: ClassVar[type[Storage] | None]

    def load(self) -> list[dict]:
        ...

    def save(self, items: list[dict]) -> None:
        ...

    def clear(self) -> None:
        ...
