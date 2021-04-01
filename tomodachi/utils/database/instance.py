#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

import asyncio
import typing

from databases import Database, DatabaseURL

from config import POSTGRES_DSN

__all__ = ["db"]


class TomodachiDatabase(Database):
    SUPPORTED_BACKENDS = {
        "postgresql": "databases.backends.postgres:PostgresBackend",
    }

    def __init__(self, url: typing.Union[str, "DatabaseURL"], **options: typing.Any):
        super().__init__(url, **options)
        self._connection_established = asyncio.Event()

    @property
    def pool(self):
        return self._backend._pool  # noqa

    async def wait_until_connected(self):
        await self._connection_established.wait()

    async def connect(self) -> None:
        await super(TomodachiDatabase, self).connect()
        self._connection_established.set()


db = TomodachiDatabase(POSTGRES_DSN)
