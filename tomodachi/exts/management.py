#  Copyright (c) 2020 — present, snezhniy.
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from typing import Optional

import discord
from discord.ext import commands

from tomodachi.core import checks
from tomodachi.utils import i
from tomodachi.core.cog import CogMixin
from tomodachi.core.context import TomodachiContext


class Management(CogMixin, icon=discord.PartialEmoji.from_str("\N{HAMMER AND WRENCH}")):
    @commands.guild_only()
    @commands.check_any(checks.is_manager(), commands.is_owner())
    @commands.group(help="Group of configuration commands", aliases=["cfg"])
    async def config(self, ctx: TomodachiContext):
        if not ctx.invoked_subcommand:
            await ctx.send(f"See `{ctx.prefix}help config` to learn about subcommands.")

    @config.command(help="Changes prefix of a bot in this server")
    async def prefix(self, ctx: TomodachiContext, new_prefix: str = None):
        settings = await ctx.settings()

        if not new_prefix:
            current_prefix = settings.prefix or self.bot.config.DEFAULT_PREFIX
            return await ctx.send(f"Prefix in this server is `{current_prefix}`")

        prefix = await self.bot.update_prefix(ctx.guild.id, new_prefix)
        await ctx.send(f"Updated prefix in the server to `{prefix}`")

    @config.command(aliases=["dm_targets", "dm_intruders"])
    async def dm_on_mod_actions(self, ctx: TomodachiContext, mode: Optional[bool] = None):
        """Enable or disable DMs on moderation actions

        If mode is not specified you'll see current setting value"""
        settings = await ctx.settings()

        if mode is None:
            if settings.dm_targets is True:
                msg = f"{i:roundedCheck} Users receive messages on moderation actions."
            else:
                msg = ":x: Users don't receive messages on moderation actions."
            return await ctx.send(msg)

        if mode is settings.dm_targets:
            return await ctx.send(":warning: The mode you have provided is the same as current one.")

        async with self.bot.cache.settings.fresh(ctx.guild.id):
            async with self.bot.db.pool.acquire() as conn:
                query = "update mod_settings set dm_targets=$2 where guild_id=$1 returning dm_targets;"
                new_dm_targets = await conn.fetchval(query, ctx.guild.id, mode)

        if new_dm_targets is True:
            msg = f"{i:roundedCheck} Users will receive DMs on moderation actions."
        else:
            msg = ":x: Users will not receive DMs on moderation actions."
        await ctx.send(msg)

    @config.group()
    async def mod_roles(self, ctx: TomodachiContext):
        if not ctx.invoked_subcommand:
            settings = await ctx.settings()
            roles = [ctx.guild.get_role(r_id) or discord.Object(id=r_id) for r_id in settings.mod_roles]

            embed = discord.Embed()
            embed.color = 0x5865F2
            embed.description = "\n".join(getattr(r, "mention", "deleted-role") + f" (`{r.id}`)" for r in roles)
            embed.title = f"Mod Roles | {ctx.guild.name}"

            await ctx.send(embed=embed)

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
            e = discord.Embed()
            e.color = 0x2ECC71
            e.description = "\n".join(f"+ {r.mention} (`{r.id}`)" for r in to_add)
            e.title = f"Mod Roles Added | {ctx.guild.name}"

            await ctx.send(embed=e)

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
            e = discord.Embed()
            e.color = 0xFF0000
            e.description = "\n".join(f"- {r.mention} (`{r.id}`)" for r in to_delete)
            e.title = f"No longer Mod Roles | {ctx.guild.name}"

            await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(Management(bot))
