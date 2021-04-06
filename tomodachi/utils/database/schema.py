#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from sqlalchemy import Table, MetaData, Column, func, cast
from sqlalchemy.dialects.postgresql import BIGINT, VARCHAR, TIMESTAMP, TEXT

__all__ = ["metadata", "guilds", "reminders", "blacklisted"]

metadata = MetaData()

guilds = Table(
    "guilds",
    metadata,
    Column("guild_id", BIGINT, autoincrement=False, primary_key=True, index=True, nullable=False),
    Column("prefix", VARCHAR(16), server_default=None),
    Column("lang", VARCHAR(16), server_default="en_US", nullable=False),
    Column("tz", VARCHAR(32), server_default="UTC", nullable=False),
)

reminders = Table(
    "reminders",
    metadata,
    Column("id", BIGINT, autoincrement=True, primary_key=True, index=True, nullable=False),
    Column("created_at", TIMESTAMP, index=True, server_default=cast(func.CURRENT_TIMESTAMP(), TIMESTAMP)),
    Column("trigger_at", TIMESTAMP, index=True, server_default=cast(func.CURRENT_TIMESTAMP(), TIMESTAMP)),
    Column("author_id", BIGINT, index=True, nullable=False),
    Column("guild_id", BIGINT),
    Column("channel_id", BIGINT, nullable=False),
    Column("message_id", BIGINT, nullable=False),
    Column("contents", TEXT, server_default="..."),
)

blacklisted = Table(
    "blacklisted",
    metadata,
    Column("user_id", BIGINT, autoincrement=False, primary_key=True, index=True, nullable=False),
    Column("reason", TEXT, server_default="because"),
)
