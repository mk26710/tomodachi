#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from typing import TYPE_CHECKING
from contextlib import asynccontextmanager

import orjson
import aioredis

from tomodachi.core.models import Settings
from tomodachi.core.exceptions import CacheFail, CacheMiss

if TYPE_CHECKING:
    from tomodachi.core.bot import Tomodachi


class Cache:
    def __init__(self, bot: Tomodachi) -> None:
        self.bot = bot
        self.redis = aioredis.from_url(bot.config.REDIS_URI, decode_responses=True)

    @asynccontextmanager
    async def fresh_cache(self, guild_id: int):
        try:
            yield None
        finally:
            await self.refresh_settings(guild_id)

    async def refresh_settings(self, guild_id: int):
        async with self.bot.db.pool.acquire() as conn:
            query = """select
                g.guild_id,
                g.prefix,
                g.lang,
                ms.mute_role,
                ms.mod_roles,
                ms.audit_infractions,
                ms.dm_targets
            from guilds g
                left join mod_settings ms on g.guild_id = ms.guild_id
            where g.guild_id = $1;"""
            record = await conn.fetchrow(query, guild_id)

        if not record:
            raise CacheFail(f"{guild_id} doesn't exist in the mod_settings table.")

        await self.redis.set(f"MS-{guild_id}", orjson.dumps(dict(record)))

    @asynccontextmanager
    async def settings(self, guild_id: int):
        settings = await self.get_settings(guild_id)
        yield settings

    async def get_settings(self, guild_id: int, *, refresh: bool = True):
        data = await self.redis.get(f"MS-{guild_id}")
        if not data:
            if not refresh:
                raise CacheMiss(f"There's no cached mod_settings for {guild_id}")

            await self.refresh_settings(guild_id)
            data = await self.redis.get(f"MS-{guild_id}")

        return Settings(**orjson.loads(data))
