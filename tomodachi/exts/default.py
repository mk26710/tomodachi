#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

import discord
from discord.ext import commands

from tomodachi.core import CogMixin, TomodachiContext, is_manager


class Default(CogMixin):
    @commands.command()
    async def hello(self, ctx: commands.Context):
        await ctx.send(f"Hello, {ctx.author.name}! I'm {ctx.bot.user.name}.")

    @commands.guild_only()
    @commands.check_any(is_manager(), commands.is_owner())
    @commands.group(help="Group of configuration commands")
    async def config(self, ctx: TomodachiContext):
        if not ctx.invoked_subcommand:
            await ctx.send(f"See `{ctx.prefix}help config` to learn about subcommands.")

    @config.command(help="Changes prefix of a bot in this server")
    async def prefix(self, ctx: TomodachiContext, new_prefix: str = None):
        if not new_prefix:
            current_prefix = self.bot.prefixes.get(ctx.guild.id, self.bot.config.DEFAULT_PREFIX)
            return await ctx.send(f"Prefix in this server is `{discord.utils.escape_markdown(current_prefix)}`")

        prefix = await self.bot.update_prefix(ctx.guild.id, new_prefix)
        await ctx.send(f"Updated prefix in the server to `{discord.utils.escape_markdown(prefix)}`")


def setup(bot):
    bot.add_cog(Default(bot))
