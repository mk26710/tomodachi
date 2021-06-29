#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from typing import Optional

import discord
from discord.ext import commands

from tomodachi.core import checks
from tomodachi.core.cog import CogMixin
from tomodachi.core.models import ModSettings
from tomodachi.core.context import TomodachiContext


class Management(CogMixin):
    async def get_mod_settings(self, guild_id: int) -> Optional[ModSettings]:
        async with self.bot.db.pool.acquire() as conn:
            query = "select * from mod_settings where guild_id = $1;"
            record = await conn.fetchrow(query, guild_id)

        return ModSettings(**record) if record else None

    @commands.guild_only()
    @commands.check_any(checks.is_manager(), commands.is_owner())
    @commands.group(help="Group of configuration commands", aliases=["cfg"])
    async def config(self, ctx: TomodachiContext):
        if not ctx.invoked_subcommand:
            await ctx.send(f"See `{ctx.prefix}help config` to learn about subcommands.")

    @config.command(help="Changes prefix of a bot in this server")
    async def prefix(self, ctx: TomodachiContext, new_prefix: str = None):
        if not new_prefix:
            current_prefix = self.bot.prefixes.get(ctx.guild.id) or self.bot.config.DEFAULT_PREFIX
            return await ctx.send(f"Prefix in this server is `{current_prefix}`")

        prefix = await self.bot.update_prefix(ctx.guild.id, new_prefix)
        await ctx.send(f"Updated prefix in the server to `{prefix}`")

    @config.group()
    async def mod_roles(self, ctx: TomodachiContext):
        if not ctx.invoked_subcommand:
            settings = await self.get_mod_settings(ctx.guild.id)
            roles = [ctx.guild.get_role(r_id) or discord.Object(id=r_id) for r_id in settings.mod_roles]

            embed = discord.Embed()
            embed.color = 0x5865F2
            embed.description = "\n".join(getattr(r, "mention", "deleted-role") + f" (`{r.id}`)" for r in roles)
            embed.title = f"Mod Roles | {ctx.guild.name}"

            await ctx.send(embed=embed)

    @mod_roles.command(name="add")
    async def mod_roles_add(self, ctx: TomodachiContext, roles: commands.Greedy[discord.Role]):
        settings = await self.get_mod_settings(ctx.guild.id)

        to_add = [r for r in set(roles) if r.id not in settings.mod_roles]
        if not to_add:
            return await ctx.send(":x: Nothing changed. Make sure that provided roles aren't Mod Roles already!")

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
        settings = await self.get_mod_settings(ctx.guild.id)

        to_delete = [r for r in set(roles) if r.id in settings.mod_roles]
        await ctx.send(f"{to_delete=}")
        if not to_delete:
            return await ctx.send(f":x: Provided roles are not Mod Roles.")

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
