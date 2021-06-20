from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union, Iterable, Optional, DefaultDict
from collections import defaultdict
from discord import Emoji, PartialEmoji

if TYPE_CHECKING:
    StoreItem = Union[Emoji, PartialEmoji]

__all__ = ["i"]


class IconMeta(type):
    def __call__(cls, arg: Any) -> Optional[StoreItem]:
        return cls.store[arg]

    def __getitem__(cls, item: Any) -> Optional[StoreItem]:
        return cls.store[item]

    def __format__(cls, format_spec: str) -> str:
        return f"{cls.store[format_spec]}"


class i(metaclass=IconMeta):  # noqa
    default = PartialEmoji(name="\N{WHITE QUESTION MARK ORNAMENT}")
    store: DefaultDict[str, StoreItem] = defaultdict(lambda: default)

    @classmethod
    async def setup(cls, emojis: Iterable[StoreItem]):
        cls.store.clear()

        for e in emojis:
            cls.store[e.name] = e