#  Copyright (c) 2020 — present, Kirill M.
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from tomodachi.core.context import TomodachiContext

__all__ = ["is_manager", "is_mod", "reminders_limit"]


def is_manager():
    async def predicate(ctx: TomodachiContext):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()

        m: discord.Member = ctx.author

        if not m.guild_permissions.manage_guild:
            raise commands.CheckFailure(f"{m} ({m.id}) has insufficient permissions to run this command")

        return True

    return commands.check(predicate)


def is_mod():
    async def predicate(ctx: TomodachiContext):
        settings = await ctx.bot.cache.settings.get(ctx.guild.id)
        author_roles = [r.id for r in ctx.author.roles]

        return any(r_id in author_roles for r_id in settings.mod_roles)

    return commands.check(predicate)


def reminders_limit():
    async def predicate(ctx: TomodachiContext):
        async with ctx.bot.db.pool.acquire() as conn:
            query = "SELECT count(id) FROM actions WHERE author_id = $1 AND action_type = 'REMINDER';"
            stmt = await conn.prepare(query)
            count = await stmt.fetchval(ctx.author.id)

        if count >= 250:
            raise commands.CheckFailure("Reached the limit of 250 reminders.")

        return True

    return commands.check(predicate)
