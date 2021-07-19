#  Copyright (c) 2020 — present, snezhniy.
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import asyncio
import logging
from typing import Union, Optional
from contextlib import suppress

import aiohttp
import discord
from discord.ext import commands

import config
import tomodachi.utils.database.instance
from tomodachi.utils import AniList, i, make_intents
from tomodachi.core.cache import Cache
from tomodachi.core.actions import ActionScheduler
from tomodachi.core.context import TomodachiContext
from tomodachi.core.exceptions import AlreadyBlacklisted
from tomodachi.core.infractions import Infractions

__all__ = ["Tomodachi"]


class Tomodachi(commands.AutoShardedBot):
    db = tomodachi.utils.database.instance.db

    def __init__(self, *, session: aiohttp.ClientSession, root_dir: Union[str, bytes]):
        super().__init__(
            max_messages=150,
            command_prefix=self.get_prefix,
            intents=make_intents(),
            owner_ids=config.OWNER_IDS,
        )
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()  # noqa

        self.session = session
        self.ROOT_DIR = root_dir
        self.config = config

        # Database related
        self.cache = Cache(self)
        self.actions = ActionScheduler(self)
        self.infractions = Infractions(self)
        # list with user ids
        self.blacklist = []

        # Faster access to support guild data
        self.support_guild: Optional[discord.Guild] = None
        self.logger = discord.Webhook.from_url(config.LOGGER_HOOK, session=session)

        # Global rate limit cooldowns mapping
        self.rate_limits = commands.CooldownMapping.from_cooldown(10, 10, commands.BucketType.user)

        # After init tasks
        self.loop.create_task(self.__ainit__())
        self.loop.create_task(self.once_ready())
        self.loop.create_task(self.load_extensions())

    async def __ainit__(self):
        await AniList.setup(self.session)
        await self.fetch_blacklist()

    async def close(self):
        self.actions.task.cancel()

        if not self.session.closed:
            await self.session.close()

        await self.db.disconnect()
        await self.cache.close()
        await super().close()

    async def get_prefix(self, message: discord.Message):
        settings = await self.cache.settings.get(message.guild.id)
        prefix = settings.prefix or config.DEFAULT_PREFIX
        return [f"<@!{self.user.id}> ", f"<@{self.user.id}> ", prefix]

    async def update_prefix(self, guild_id: int, new_prefix: str):
        async with self.cache.settings.fresh(guild_id):
            prefix = await self.db.update_prefix(guild_id, new_prefix)
        return prefix

    async def get_context(self, message, *, cls=None) -> Union[TomodachiContext, commands.Context]:
        return await super().get_context(message, cls=cls or TomodachiContext)

    async def process_commands(self, message: discord.Message):
        if message.author.bot:
            return

        if message.author.id in self.blacklist:
            return

        ctx = await self.get_context(message)
        if ctx.command is None:
            return

        bucket = self.rate_limits.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()

        if retry_after:
            # not being detected by the global error handler
            # probably have to figure out why and how to fix
            # raise commands.CommandOnCooldown(bucket, retry_after)

            # in order to prevent spamming from the bot, we block
            # the user until they are able to use commands again
            asyncio.create_task(self.temp_block(ctx.author.id, retry_after))
            return await ctx.reply(f"You are being rate limited for `{retry_after:.2f}` seconds.")

        await self.invoke(ctx)

    async def temp_block(self, user_id: int, delay: Union[float, int]):
        """Temporary adds a user by their ID to the bot's blacklist"""
        if user_id in self.blacklist:
            raise AlreadyBlacklisted(f"{user_id} is already blacklisted, failed to blacklist them temporarily.")

        self.blacklist.append(user_id)
        if delay:
            await asyncio.sleep(delay)

        with suppress(ValueError):
            self.blacklist.remove(user_id)

    async def fetch_blacklist(self):
        async with self.db.pool.acquire() as conn:
            records = await conn.fetch("SELECT DISTINCT * FROM blacklisted;")

        self.blacklist = [r["user_id"] for r in records]

    async def load_extensions(self):
        await self.wait_until_ready()

        for ext in config.EXTENSIONS:
            self.load_extension(f"tomodachi.exts.{ext}")
            logging.info(f"loaded {ext}")

    async def once_ready(self):
        await self.wait_until_ready()

        for guild in self.guilds:
            self.loop.create_task(self.db.store_guild(guild.id))

        self.support_guild = await self.fetch_guild(config.SUPPORT_GUILD_ID)
        emojis = await self.support_guild.fetch_emojis()
        await i.setup(emojis)

    async def get_or_fetch_user(self, user_id: int) -> discord.User:
        """Retrives a discord.User object from cache or fetches it if not cached"""
        return self.get_user(user_id) or (await self.fetch_user(user_id))

    async def get_or_fetch_member(self, guild: discord.Guild, user_id: int):
        """Retrives a discord.Member oject from cache or fetches it if not cached"""
        return guild.get_member(user_id) or (await guild.fetch_member(user_id))

    async def get_or_fetch_guild(self, guild_id: int) -> discord.Guild:
        """Retrives a discord.Guild oject from cache or fetches it if not cached"""
        return self.get_guild(guild_id) or (await self.fetch_guild(guild_id))
