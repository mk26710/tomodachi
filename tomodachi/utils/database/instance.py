#  Copyright (c) 2020 — present, Kirill M.
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Union, Optional

from databases import Database

from config import POSTGRES_DSN

if TYPE_CHECKING:
    from databases import DatabaseURL
    from asyncpg.pool import Pool

__all__ = ["db"]


class TomodachiDatabase(Database):
    SUPPORTED_BACKENDS = {
        "postgresql": "databases.backends.postgres:PostgresBackend",
    }

    def __init__(self, url: Union[str, DatabaseURL], **options: Any):
        super().__init__(url, **options)
        self.connection_created = asyncio.Event()

    @property
    def pool(self) -> Optional[Pool]:
        return self._backend._pool  # noqa

    async def connect(self) -> None:
        await super(TomodachiDatabase, self).connect()
        self.connection_created.set()

    async def disconnect(self) -> None:
        self.connection_created.clear()
        await super().disconnect()

    async def store_guild(self, /, guild_id: int):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                query = "insert into guilds(guild_id) values ($1) on conflict do nothing returning true;"
                inserted = await conn.fetchval(query, guild_id)
                if inserted:
                    query = "insert into mod_settings(guild_id) values ($1) on conflict do nothing;"
                    await conn.execute(query, guild_id)

    async def update_prefix(self, /, guild_id: int, new_prefix: str):
        async with self.pool.acquire() as conn:
            query = "UPDATE guilds SET prefix = $1 WHERE guild_id = $2 RETURNING prefix;"
            prefix = await conn.fetchval(query, new_prefix, guild_id)
        return prefix


db = TomodachiDatabase(POSTGRES_DSN)
