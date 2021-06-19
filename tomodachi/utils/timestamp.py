from __future__ import annotations

from typing import Union, Literal
from datetime import datetime

from arrow import Arrow

TimestampFormats = Literal["", "f", "F", "d", "D", "t", "T", "R"]


class timestamp:
    def __init__(self, value: Union[datetime, Arrow, int, float]) -> None:
        if isinstance(value, (int, float)):
            self.value = int(value)

        elif isinstance(value, Arrow):
            self.value = value.int_timestamp

        elif isinstance(value, datetime):
            self.value = int(value.timestamp())

    def __format__(self, format_spec: TimestampFormats) -> str:
        return f"<t:{self.value}:{format_spec}>"
