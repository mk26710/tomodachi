#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

import discord
from discord.ext import commands

from tomodachi.core import CogMixin


class Default(CogMixin, icon=discord.PartialEmoji(name=":file_folder:")):
    @commands.command()
    async def hello(self, ctx: commands.Context):
        await ctx.send(f"Hello, {ctx.author.name}! I'm {ctx.bot.user.name}.")


def setup(bot):
    bot.add_cog(Default(bot))
