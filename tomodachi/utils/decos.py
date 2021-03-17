#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import asyncio
import functools
from typing import Callable

__all__ = ["to_thread"]


def to_thread(func: Callable):
    """Asynchronously run function in a separate thread."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        partial = functools.partial(func, *args, **kwargs)
        coro = asyncio.to_thread(partial)
        return await coro

    return wrapper
