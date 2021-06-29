#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from typing import TYPE_CHECKING, Union, Optional
from datetime import datetime

import discord
from discord.ext import commands

from tomodachi.core import CogMixin, TomodachiContext, checks
from tomodachi.utils import i, helpers, timestamp
from tomodachi.core.enums import InfractionType
from tomodachi.utils.converters import TimeUnit

if TYPE_CHECKING:
    from tomodachi.core.infractions import Infraction

MemberUser = Union[discord.Member, discord.User]


class Moderation(CogMixin, icon=discord.PartialEmoji(name="discord_certified_moderator", id=853548115756187648)):
    async def cog_check(self, ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    @staticmethod
    def make_audit_reason(mod: str, _reason: str, *, until: datetime = None) -> str:
        reason = f"[{mod}] "
        if until:
            reason += f"[Expiring {until}] "
        reason += _reason

        return reason if len(reason) <= 512 else f"{reason[0:509]}..."

    @commands.Cog.listener()
    async def on_expired_infraction(self, infraction: Infraction):
        await self.bot.wait_until_ready()

        # created target object
        obj = discord.Object(id=infraction.target_id)

        try:
            guild = await self.bot.get_or_fetch_guild(infraction.guild_id)
        except (discord.Forbidden, discord.HTTPException):
            return

        if infraction.inf_type is InfractionType.TEMPBAN:
            try:
                reason = f"Infraction #{infraction.id} has expired."
                await guild.unban(user=obj, reason=reason)
                await self.bot.infractions.create(
                    inf_type=InfractionType.UNBAN,
                    guild_id=guild.id,
                    target_id=obj.id,
                    expires_at=None,
                    reason=reason,
                    create_action=False,
                )
            except (discord.Forbidden, discord.HTTPException):
                return  # todo: once modlogs are created, log this to inform mods about failure

    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.check_any(commands.has_guild_permissions(ban_members=True), checks.is_mod())
    @commands.command(aliases=["permaban"], help="Permanently bans a user from the server")
    async def ban(self, ctx: TomodachiContext, target: MemberUser, *, reason: str = None):
        reason = reason or "No reason."

        try:
            await ctx.guild.ban(target, reason=self.make_audit_reason(f"{ctx.author} ({ctx.author.id})", reason))
        except (discord.Forbidden, discord.HTTPException):
            raise

        inf = await self.bot.infractions.create(
            inf_type=InfractionType.PERMABAN,
            expires_at=None,
            guild_id=ctx.guild.id,
            mod_id=ctx.author.id,
            target_id=target.id,
            reason=reason,
            create_action=False,
        )
        content = f":ok_hand: **{target}** (`{target.id}`) was banned for: `{reason}` (`#{inf.id}`)"

        await ctx.send(content)

    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.check_any(commands.has_guild_permissions(ban_members=True), checks.is_mod())
    @commands.command(help="Bans a user for specified period time")
    async def tempban(self, ctx: TomodachiContext, target: MemberUser, duration: TimeUnit, *, reason: str = None):
        reason = reason or "No reason."

        unban_at = helpers.utcnow() + duration
        when = timestamp(unban_at)

        try:
            audit_reason = self.make_audit_reason(f"{ctx.author} ({ctx.author.id})", reason, until=unban_at)
            await ctx.guild.ban(target, reason=audit_reason)
        except (discord.Forbidden, discord.HTTPException):
            raise

        inf = await self.bot.infractions.create(
            inf_type=InfractionType.TEMPBAN,
            expires_at=unban_at,
            guild_id=ctx.guild.id,
            mod_id=ctx.author.id,
            target_id=target.id,
            reason=reason,
        )
        content = (
            f":ok_hand: **{target}** (`{target.id}`) was temp-banned until **{when:F}** for: `{reason}` (`#{inf.id}`)"
        )

        await ctx.send(content)

    @commands.bot_has_guild_permissions(kick_members=True)
    @commands.check_any(commands.has_guild_permissions(kick_members=True), checks.is_mod())
    @commands.command(help="Kicks a member from the server")
    async def kick(self, ctx: TomodachiContext, target: discord.Member, *, reason: str = None):
        reason = reason or "No reason."

        try:
            await target.kick(reason=self.make_audit_reason(f"{ctx.author} ({ctx.author.id})", reason))
        except (discord.Forbidden, discord.HTTPException):
            raise

        inf = await self.bot.infractions.create(
            inf_type=InfractionType.KICK,
            guild_id=ctx.guild.id,
            mod_id=ctx.author.id,
            target_id=target.id,
            reason=reason,
            create_action=False,
        )
        content = f":ok_hand: **{target}** (`{target.id}`) was kicked for: `{reason}` (`#{inf.id}`)"

        await ctx.send(content)

    # fmt: off
    @commands.bot_has_guild_permissions(manage_messages=True)
    @commands.check_any(commands.has_guild_permissions(manage_messages=True), checks.is_mod())
    @commands.command(aliases=["purge", "prune"], help="Deletes specified amount of messages", description="Messages of a specified user will be deleted if target was provided")  # noqa
    # fmt: on
    async def clear(self, ctx: TomodachiContext, target: Optional[MemberUser] = None, amount: int = 50):
        if amount > 1000:
            return await ctx.send(":x: You can bulk delete only up to `1000` messages!")

        def check(m):
            if isinstance(target, (discord.Member, discord.User)):
                return m.author.id == target.id
            return True

        info = await ctx.send(f"{i:loading} Processing...")
        deleted = await ctx.channel.purge(limit=amount, check=check, before=info.created_at)

        await info.edit(content=f":ok_hand: Deleted `{len(deleted)}` messages")


def setup(bot):
    bot.add_cog(Moderation(bot))
