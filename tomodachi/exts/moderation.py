#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from typing import Union, Optional

import discord
from discord.ext import commands

from tomodachi.core import CogMixin, TomodachiContext
from tomodachi.utils import i, helpers, timestamp
from tomodachi.core.enums import ActionType
from tomodachi.core.actions import Action
from tomodachi.utils.converters import TimeUnit

MemberUser = Union[discord.Member, discord.User]


class Moderation(CogMixin, icon=discord.PartialEmoji(name="discord_certified_moderator", id=853548115756187648)):
    async def cog_check(self, ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    @commands.Cog.listener()
    async def on_triggered_action(self, action: Action):
        await self.bot.wait_until_ready()

        if action.sort is not ActionType.TEMPBAN:
            return

        guild = self.bot.get_guild(action.guild_id) or await self.bot.fetch_guild(action.guild_id)
        target = self.bot.get_user(action.extra["target_id"]) or await self.bot.fetch_user(action.extra["target_id"])

        await guild.unban(target, reason=f"Ban #{action.id} expired.")

    @commands.has_guild_permissions(ban_members=True)
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.command(aliases=["permaban"], help="Permanently bans a user from the server")
    async def ban(self, ctx: TomodachiContext, target: MemberUser, *, reason: str = "No reason."):
        await ctx.guild.ban(target, reason=f"{ctx.author} ({ctx.author.id}): {reason}")
        await ctx.send(f":ok_hand: **{target}** (`{target.id}`) was banned for: `{reason}`")

    @commands.has_guild_permissions(ban_members=True)
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.command(help="Bans a user for specified period time")
    async def tempban(
        self, ctx: TomodachiContext, target: MemberUser, duration: TimeUnit, *, reason: str = "No reason."
    ):
        unban_at = helpers.utcnow() + duration
        when = timestamp(unban_at)

        action = Action(
            sort=ActionType.TEMPBAN,
            trigger_at=unban_at,
            author_id=ctx.author.id,
            guild_id=ctx.guild.id,
            channel_id=ctx.channel.id,
            message_id=ctx.message.id,
            extra={"target_id": target.id, "reason": reason},
        )
        await self.bot.actions.create_action(action)

        await ctx.guild.ban(target, reason=f"[Until {unban_at}] {ctx.author} ({ctx.author.id}): {reason}")
        await ctx.send(
            f":ok_hand: **{target}** (`{target.id}`) was temporarily banned until **{when:F}** for: {reason}"
        )

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
    @commands.command(aliases=["purge", "prune"], help="Deletes specified amount of messages", description="Messages of a specified user will be deleted if target was provided")  # noqa
    # fmt: on
    async def clear(self, ctx: TomodachiContext, target: Optional[MemberUser] = None, amount: int = 50):
        if amount > 1000:
            return await ctx.send(f":x: You can bulk delete only up to `1000` messages!")

        def check(m):
            if isinstance(target, (discord.Member, discord.User)):
                return m.author.id == target.id
            return True

        info = await ctx.send(f"{i:loading} Processing...")
        deleted = await ctx.channel.purge(limit=amount, check=check, before=info.created_at)

        await info.edit(content=f":ok_hand: Deleted `{len(deleted)}` messages")


def setup(bot):
    bot.add_cog(Moderation(bot))
