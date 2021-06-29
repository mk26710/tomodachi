#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from typing import Union, Literal
from datetime import datetime

from arrow import Arrow

__all__ = ["timestamp", "TimestampFormattingFlags"]

TimestampFormattingFlags = Literal["", "f", "F", "d", "D", "t", "T", "R"]


class timestamp:
    def __init__(self, value: Union[datetime, Arrow, int, float]) -> None:
        if isinstance(value, (int, float)):
            self.value = int(value)

        elif isinstance(value, Arrow):
            self.value = value.int_timestamp

        elif isinstance(value, datetime):
            self.value = int(value.timestamp())

    def __format__(self, format_spec: TimestampFormattingFlags) -> str:
        if not format_spec:
            return f"<t:{self.value}>"

        return f"<t:{self.value}:{format_spec}>"
