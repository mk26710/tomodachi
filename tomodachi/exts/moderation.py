#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import asyncio
from typing import Union, Optional

import discord
from discord.ext import commands

from tomodachi.core import TomodachiContext, Tomodachi

MemberUser = Union[discord.Member, discord.User]


class Moderation(commands.Cog):
    def __init__(self, bot: Tomodachi):
        self.bot = bot
        self._event = asyncio.Event()

    async def cog_check(self, ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    @commands.has_guild_permissions(ban_members=True)
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.command(aliases=("permaban",), help="Permanently bans a user from the server")
    async def ban(self, ctx: TomodachiContext, target: Union[MemberUser], *, reason: str = None):
        reason = reason or "No reason provided."

        await ctx.guild.ban(target, reason=f"{ctx.author} ({ctx.author.id}): {reason}")
        await ctx.send(f":ok_hand: **{target}** (`{target.id}`) was banned for: `{reason}`")

    @commands.has_guild_permissions(kick_members=True)
    @commands.bot_has_guild_permissions(kick_members=True)
    @commands.command(help="Kicks a member from the server")
    async def kick(self, ctx: TomodachiContext, target: discord.Member, *, reason: str = None):
        reason = reason or "No reason provided."

        await ctx.guild.kick(target, reason=f"{ctx.author} ({ctx.author.id}): {reason}")
        await ctx.send(f":ok_hand: **{target}** (`{target.id}`) was kicked for: `{reason}`")

    # fmt: off
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_guild_permissions(manage_messages=True)
    @commands.command(aliases=("purge", "prune"), help="Deletes specified amount of messages", description="Messages of a specified user will be deleted if target was provided")  # noqa
    # fmt: on
    async def clear(self, ctx: TomodachiContext, target: Optional[Union[MemberUser]] = None, amount: int = 50):
        if amount > 1000:
            return await ctx.send(f":x: You can bulk delete only up to `1000` messages!")

        def check(m):
            if isinstance(target, (discord.Member, discord.User)):
                return m.author.id == target.id
            return True

        info = await ctx.send(f"{ctx.icon['loading']} Processing...")
        deleted = await ctx.channel.purge(limit=amount, check=check, before=info.created_at)

        await info.edit(content=f":ok_hand: Deleted `{len(deleted)}` messages")


def setup(bot):
    bot.add_cog(Moderation(bot))
