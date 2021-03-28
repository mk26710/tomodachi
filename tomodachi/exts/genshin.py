#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

import asyncio
from datetime import timedelta

import humanize
from discord.ext import commands

from tomodachi.core import Tomodachi, TomodachiContext
from tomodachi.utils.converters import uint


class Genshin(commands.Cog):
    def __init__(self, bot: Tomodachi):
        self.bot = bot

    @commands.cooldown(1, 5.0, commands.BucketType.user)
    @commands.command(help="Counts how much time left until your resin refills")
    async def resin(self, ctx: TomodachiContext, current: uint = 0, needed: uint = 160):
        if current < 0 or current > 160 or needed < current:
            return await ctx.send("You either reached the cap or trying to put invalid amount.")

        to_wait = timedelta(minutes=((needed - current) * 8))
        h_delta = await asyncio.to_thread(humanize.precisedelta, to_wait)

        await ctx.send(f"You need to wait {h_delta} until you reach `{needed}` resin")


def setup(bot):
    bot.add_cog(Genshin(bot))
