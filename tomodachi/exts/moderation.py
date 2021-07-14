#  Copyright (c) 2020 — present, kodamio.
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING, List, Union, Optional
from datetime import datetime

import discord
from discord.embeds import EmptyEmbed
from discord.ext import menus, commands

from tomodachi.core import CogMixin, TomodachiContext, checks
from tomodachi.utils import i, helpers, timestamp
from tomodachi.core.enums import InfractionType
from tomodachi.utils.converters import BannedUser, TimeUnit, uint

if TYPE_CHECKING:
    from tomodachi.core.infractions import Infraction

MemberUser = Union[discord.Member, discord.User]


class MySource(menus.ListPageSource):
    def __init__(self, data: List[Infraction]):
        super().__init__(data, per_page=10)
        self.header = f"{'ID': <6} | {'Type': <10} | {'Intruder ID': <18} | {'Moderator ID': <18} | {'Timestamp (UTC)': <20} | Reason"
        self.border = f"{'-'*7}|{'-'*12}|{'-'*20}|{'-'*20}|{'-'*22}|{'-'*10}"

    @staticmethod
    def make_row(entry: Infraction):
        human_timestamp = entry.created_at.strftime("%Y-%m-%d %H:%M:%S")
        reason = textwrap.shorten(entry.reason, 47)
        return f"{str(entry.id): <6} | {entry.inf_type.name: <10} | {str(entry.target_id): <18} | {str(entry.mod_id): <18} | {human_timestamp: <20} | {reason}"

    async def format_page(self, menu: menus.MenuPages, entries: List[Infraction]):
        rows = [self.make_row(entry) for entry in entries]
        table = "```\n{0}\n```".format("\n".join([self.header, self.border, *rows]))
        page = f"Page {menu.current_page+1}/{self.get_max_pages()}"
        return f"{table}{page}"


class InfractionSearchFlags(commands.FlagConverter, prefix="--", delimiter=""):
    target: Optional[MemberUser]
    mod: Optional[MemberUser]
    id: Optional[int]


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
                    mod_id=self.bot.user.id,
                    target_id=obj.id,
                    expires_at=None,
                    reason=reason,
                    create_action=False,
                )
            except (discord.Forbidden, discord.HTTPException):
                return  # todo: once modlogs are created, log this to inform mods about failure

    @commands.command(aliases=["permaban"])
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.check_any(commands.has_guild_permissions(ban_members=True), checks.is_mod())
    async def ban(self, ctx: TomodachiContext, target: MemberUser, *, reason: str = None):
        """Permanently bans a user from the server"""
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

    @commands.command()
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.check_any(commands.has_guild_permissions(ban_members=True), checks.is_mod())
    async def tempban(self, ctx: TomodachiContext, target: MemberUser, duration: TimeUnit, *, reason: str = None):
        """Bans a user for specified period of time"""
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

    @commands.command()
    @commands.bot_has_guild_permissions(kick_members=True)
    @commands.check_any(commands.has_guild_permissions(kick_members=True), checks.is_mod())
    async def kick(self, ctx: TomodachiContext, target: discord.Member, *, reason: str = None):
        """Kicks a member from the server"""
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

    @commands.command()
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.check_any(commands.has_guild_permissions(ban_members=True), checks.is_mod())
    async def unban(self, ctx: TomodachiContext, target: BannedUser, *, reason: str = None):
        """Removes a ban from specified user"""
        reason = reason or "No reason."
        await ctx.guild.unban(target, reason=self.make_audit_reason(f"{ctx.author} ({ctx.author.id})", reason))

        inf = await self.bot.infractions.create(
            inf_type=InfractionType.UNBAN,
            guild_id=ctx.guild.id,
            mod_id=ctx.author.id,
            target_id=target.id,
            reason=reason,
            create_action=False,
        )

        await ctx.send(f":ok_hand: **{target}** (`{target.id}`) was unbanned for: `{reason}` (`#{inf.id}`)")

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

    @commands.group(aliases=["infraction", "inf"])
    @commands.check_any(
        commands.has_guild_permissions(kick_members=True),
        commands.has_guild_permissions(ban_members=True),
        checks.is_mod(),
    )
    async def infractions(self, ctx: TomodachiContext):
        """Group of commands to manage infractions"""
        if not ctx.subcommand_passed:
            await ctx.send_help("infractions")

    @infractions.command(name="info")
    @commands.cooldown(1, 5.0, commands.BucketType.guild)
    async def infractions_info(self, ctx: TomodachiContext, infraction_id: uint):
        """Provides full information on some specific infraction."""
        data = await self.bot.infractions.get(ctx.guild.id, inf_id=infraction_id)
        if not data:
            return await ctx.send(":x: Nothing was found for this query.")
        inf = data[0]

        target = await self.bot.get_or_fetch_user(inf.target_id)
        moderator = await self.bot.get_or_fetch_user(inf.mod_id)

        embed = discord.Embed(colour=discord.Colour.blurple())
        embed.set_thumbnail(url=getattr(target.avatar, "url", EmptyEmbed))
        embed.set_footer(text=f"#{inf.id}")
        embed.add_field(name="Reason", value=textwrap.shorten(inf.reason, width=1000), inline=False)

        title = helpers.infraction_by_formats.get(inf.inf_type).format(moderator.name, target.name)
        icon_url = getattr(moderator.avatar, "url", EmptyEmbed)
        embed.set_author(name=title, icon_url=icon_url)

        embed.add_field(name="Moderator", value=f"{moderator}", inline=False)
        embed.add_field(name="Moderator ID", value=f"{moderator.id}", inline=False)

        embed.add_field(name="Intruder", value=f"{target}", inline=False)
        embed.add_field(name="Intruder ID", value=f"{target.id}", inline=False)

        if inf.created_at:
            when_created = timestamp(inf.created_at)
            embed.add_field(name="Creation date", value=f"{when_created:F}", inline=False)

        if inf.expires_at:
            when_expires = timestamp(inf.expires_at)
            embed.add_field(name="Expire date", value=f"{when_expires:F}", inline=False)

        if inf.action_id and inf.expires_at:
            embed.add_field(name="Active", value="Yes", inline=False)
        elif not inf.action_id and inf.expires_at:
            embed.add_field(name="Active", value="No", inline=False)

        await ctx.send(embed=embed)

    @infractions.command(name="search")
    async def infractions_search(self, ctx: TomodachiContext, *, flags: InfractionSearchFlags):
        """Searches through infractions history.

        This command uses a command line syntax. You will be able to review up to 500 infraction records.

        Available options:
        `--id [number]` — unique infraction identifier
        `--mod [user]` — moderator of the infraction
        `--target [user]` — intruder

        Some examples:
        `%prefix%infractions search --target 576322791129743361 --mod @Tomodachi#9184`
        `%prefix%infractions search --target 576322791129743361`
        `%prefix%infractions search --mod @Tomodachi#9184`
        `%prefix%infractions search --id 12345`

        If you don't specify any flags, you will get information about the last 500 infractions on the server."""
        inf_ls = await self.bot.infractions.get(
            ctx.guild.id,
            inf_id=flags.id,
            target_id=getattr(flags.target, "id", None),
            mod_id=getattr(flags.mod, "id", None),
        )

        if not inf_ls:
            return await ctx.send(":x: Nothing was found!")

        src = MySource(inf_ls)
        menu = menus.MenuPages(src, clear_reactions_after=True)
        await menu.start(ctx)


def setup(bot):
    bot.add_cog(Moderation(bot))
