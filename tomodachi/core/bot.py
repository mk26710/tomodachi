#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import logging
from typing import Union, Optional

import aiohttp
import discord
from discord.ext import commands

import config
from tomodachi.utils import AniList, make_intents, make_cache_policy
from tomodachi.core.icons import Icons
from tomodachi.core.context import TomodachiContext
from tomodachi.utils.database import db

__all__ = ["Tomodachi"]


class Tomodachi(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            max_messages=150,
            command_prefix=self.get_prefix,
            intents=make_intents(),
            member_cache_flags=make_cache_policy(),
            owner_ids=config.OWNER_IDS,
        )
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()  # noqa

        self.session: aiohttp.ClientSession = kwargs.pop("extra_session")
        self.ROOT_DIR: Union[str, bytes] = kwargs.pop("ROOT_DIR")

        # Alias to config module
        self.config = config

        # Database shortcuts
        self.db = db
        self.pool = db.pool

        self.prefixes = {}
        # tuple with user ids
        self.blacklist = ()

        # Alias to Icons singleton
        self.icon = Icons()
        # Faster access to support guild data
        self.support_guild: Optional[discord.Guild] = None
        self.traceback_log: Optional[discord.TextChannel] = None

        # Global rate limit cooldowns mapping
        self.global_rate_limit = commands.CooldownMapping.from_cooldown(10, 10, commands.BucketType.user)

        self.loop.create_task(self.once_ready())

        # Fetch custom prefixes and blacklisted users
        self.loop.create_task(self.fetch_blacklist())
        self.loop.create_task(self.fetch_prefixes())

    async def close(self):
        if not self.session.closed:
            await self.session.close()

        await self.db.disconnect()
        await super().close()

    async def get_prefix(self, message: discord.Message):
        return [
            f"<@!{self.user.id}> ",
            f"<@{self.user.id}> ",
            self.prefixes.get(message.guild.id) or config.DEFAULT_PREFIX,
        ]

    async def update_prefix(self, guild_id: int, new_prefix: str):
        prefix = await self.db.update_prefix(guild_id, new_prefix)
        self.prefixes[guild_id] = prefix
        return self.prefixes[guild_id]

    async def get_context(self, message, *, cls=None) -> Union[TomodachiContext, commands.Context]:
        return await super().get_context(message, cls=cls or TomodachiContext)

    async def process_commands(self, message: discord.Message):
        if message.author.bot:
            return

        if message.author.id in self.blacklist:
            return

        ctx = await self.get_context(message)

        bucket = self.global_rate_limit.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()

        if retry_after and ctx.author.id != self.owner_id:
            return await message.channel.send(
                content=f"You are being globally rate limited. Please, wait `{retry_after:.2f}` seconds.",
                delete_after=retry_after,
            )

        await self.invoke(ctx)

    async def fetch_prefixes(self):
        await self.db.wait_until_connected()

        async with self.pool.acquire() as conn:
            records = await conn.fetch("SELECT guild_id, prefix FROM guilds;")

        self.prefixes.update({k: v for k, v in map(tuple, records)})

    async def fetch_blacklist(self):
        await self.db.wait_until_connected()

        async with self.pool.acquire() as conn:
            records = await conn.fetch("SELECT DISTINCT * FROM blacklisted;")

        self.blacklist = tuple(r["user_id"] for r in records)

    async def once_ready(self):
        await self.wait_until_ready()

        for guild in self.guilds:
            self.loop.create_task(self.db.store_guild(guild.id))

        self.support_guild = support_guild = await self.fetch_guild(config.SUPPORT_GUILD_ID)
        support_channels = await support_guild.fetch_channels()
        self.traceback_log = discord.utils.get(support_channels, name="traceback")

        await self.icon.setup(support_guild.emojis)
        await AniList.setup(self.session)

        for ext in config.EXTENSIONS:
            self.load_extension(f"tomodachi.exts.{ext}")
            logging.info(f"loaded {ext}")
