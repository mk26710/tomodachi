#  Copyright (c) 2020 — present, snezhniy.
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from aioredis.client import Redis, ConnectionPool

    from tomodachi.core.bot import Tomodachi


@runtime_checkable
class CacheProto(Protocol):
    bot: Tomodachi
    pool: ConnectionPool
    redis: Redis
