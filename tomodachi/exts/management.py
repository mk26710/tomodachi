#  Copyright (c) 2020 — present, Kirill M.
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from typing import Optional

import discord
from discord.ext import commands

from tomodachi.core import checks
from tomodachi.core.cog import CogMixin
from tomodachi.core.context import TomodachiContext
from tomodachi.utils.humanbool import humanbool


class Management(CogMixin, icon="\N{HAMMER AND WRENCH}", colour=0xF4900C):
    @commands.guild_only()
    @commands.check_any(checks.is_manager(), commands.is_owner())
    @commands.group(help="Group of configuration commands", aliases=["cfg"])
    async def config(self, ctx: TomodachiContext):
        if not ctx.invoked_subcommand:
            await ctx.send_help("config")

    @config.command(help="Changes prefix of a bot in this server")
    async def prefix(self, ctx: TomodachiContext, new_prefix: str = None):
        """Controls bot’s prefix.

        If new prefix is not provided, current prefix will be shown."""
        settings = await ctx.settings()
        prefix = settings.prefix or self.bot.config.DEFAULT_PREFIX

        if (not new_prefix) or (prefix == new_prefix):
            await ctx.send(f"\U0001F50E Current prefix is `{prefix}`.")
            return

        prefix = await self.bot.update_prefix(ctx.guild.id, new_prefix)
        await ctx.send(f"\U0001F44C The prefix has been changed to `{prefix}`.")

    @config.command(aliases=["dm_targets", "dm_intruders"])
    async def dm_on_mod_actions(self, ctx: TomodachiContext, mode: Optional[bool] = None):
        """Controls DMs on moderation actions.

        If mode is not specified, current mode will be shown."""
        settings = await ctx.settings()

        if (mode is None) or (mode is settings.dm_targets):
            await ctx.send(f"\U0001F50E DMs on moderation actions are currently **{humanbool(settings.dm_targets)}**.")
            return

        async with self.bot.cache.settings.fresh(ctx.guild.id):
            async with self.bot.db.pool.acquire() as conn:
                query = "update mod_settings set dm_targets=$2 where guild_id=$1 returning dm_targets;"
                result = await conn.fetchval(query, ctx.guild.id, mode)

        await ctx.send(f"\U0001F44C DMs on moderation actions has been **{humanbool(result)}**.")

    @config.group()
    async def mod_roles(self, ctx: TomodachiContext):
        if not ctx.invoked_subcommand:
            settings = await ctx.settings()
            roles = [ctx.guild.get_role(r_id) or discord.Object(id=r_id) for r_id in settings.mod_roles]
            if not roles:
                await ctx.send("\U0001F50E There are no moderators roles configured.")
                return

            e = discord.Embed(
                colour=discord.Colour.blurple(),
                description="\n".join(getattr(r, "mention", "deleted-role") + f" (`{r.id}`)" for r in roles),
            )

            await ctx.send("\U0001F50E List of moderators roles:", embed=e)

    @mod_roles.command(name="add")
    async def mod_roles_add(self, ctx: TomodachiContext, roles: commands.Greedy[discord.Role]):
        settings = await ctx.settings()

        to_add = [r for r in set(roles) if r.id not in settings.mod_roles]
        if not to_add:
            return await ctx.send(":x: Nothing changed. Make sure that provided roles aren't Mod Roles already!")

        async with self.bot.cache.settings.fresh(ctx.guild.id):
            async with self.bot.db.pool.acquire() as conn:
                query = """insert into mod_settings as ms (guild_id, mod_roles) values ($1, $2)
                    on conflict (guild_id) do update set mod_roles = ms.mod_roles || $2::bigint[]
                    returning true;"""

                is_added = await conn.fetchval(query, ctx.guild.id, [r.id for r in to_add])

        if is_added:
            e = discord.Embed(
                colour=discord.Colour.green(),
                description="\n".join(f"+ {r.mention} (`{r.id}`)" for r in to_add),
            )

            await ctx.send("\U0001F44C Added to moderators roles:", embed=e)

    @mod_roles.command(name="remove", aliases=["rmv", "delete", "del"])
    async def mod_roles_remove(self, ctx: TomodachiContext, roles: commands.Greedy[discord.Role]):
        settings = await ctx.settings()

        to_delete = [r for r in set(roles) if r.id in settings.mod_roles]
        if not to_delete:
            return await ctx.send(":x: Provided roles are not Mod Roles.")

        async with self.bot.cache.settings.fresh(ctx.guild.id):
            async with self.bot.db.pool.acquire() as conn:
                query = """update mod_settings as ms
                    set mod_roles = (select array(select unnest(ms.mod_roles) except select unnest($2::bigint[])))
                    where guild_id = $1
                    returning true;"""

                removed = await conn.fetchval(query, ctx.guild.id, [r.id for r in to_delete])

        if removed:
            e = discord.Embed(
                colour=discord.Colour.red(),
                description="\n".join(f"- {r.mention} (`{r.id}`)" for r in to_delete),
            )

            await ctx.send("\U0001F44C Removed from moderators roles:", embed=e)

    @config.command(aliases=["automatic_infractions", "audit_infractions"])
    async def auto_infractions(self, ctx: TomodachiContext, mode: bool = None):
        """Control infractions creation based on audit logs."""
        settings = await ctx.settings()

        if (mode is None) or (mode == settings.audit_infractions):
            await ctx.send(
                f"\U0001f50e Automatic Infractions are currently **{humanbool(settings.audit_infractions)}**."
            )
            return

        async with self.bot.cache.settings.fresh(ctx.guild.id):
            async with self.bot.db.pool.acquire() as conn:
                query = """update mod_settings as ms
                    set audit_infractions=$2
                    where guild_id=$1
                    returning ms.audit_infractions;"""
                result = await conn.fetchval(query, ctx.guild.id, mode)

        await ctx.send(f"\U0001F44C Automatic Infractions has been **{humanbool(result)}**.")


def setup(bot):
    bot.add_cog(Management(bot))
