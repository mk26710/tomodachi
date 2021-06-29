#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from tomodachi.core.context import TomodachiContext

__all__ = ["is_manager", "is_mod"]


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
        query = "select mod_roles from mod_settings where guild_id=$1;"
        author_roles = [r.id for r in ctx.author.roles]
        mod_roles = await ctx.bot.db.pool.fetchval(query, ctx.guild.id)
        if not mod_roles:
            return False

        return any(r_id in author_roles for r_id in mod_roles)

    return commands.check(predicate)
