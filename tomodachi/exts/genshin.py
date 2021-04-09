#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

import asyncio
from typing import Optional
from datetime import timedelta

import humanize
from discord.ext import commands
from jishaku.models import copy_context_with

from tomodachi.core import CogMixin, TomodachiContext
from tomodachi.utils.converters import uint


class Genshin(CogMixin):
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    @commands.command(help="Counts how much time left until your resin refills")
    async def resin(
        self,
        ctx: TomodachiContext,
        current: Optional[uint] = 0,
        needed: Optional[uint] = 160,
        remind: Optional[bool] = True,
    ):
        if current < 0 or current > 160 or needed < current:
            return await ctx.send("You either reached the cap or trying to put invalid amount.")

        to_wait = timedelta(minutes=((needed - current) * 8))
        h_delta = await asyncio.to_thread(humanize.precisedelta, to_wait)

        await ctx.send(f"You will have {needed} resin **in {h_delta}**.")

        if not remind:
            return

        emoji = ctx.icon("slowmode")

        msg = await ctx.send(f"React with {emoji} to create a reminder!")
        await msg.add_reaction(emoji)

        def check(reaction, user):
            return user.id == ctx.author.id and reaction.emoji.id == emoji.id and reaction.message.id == msg.id

        try:
            await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
        except asyncio.TimeoutError:
            pass
        else:
            command_string = f"{ctx.prefix}reminder add {to_wait.seconds}s Genshin Impact: {needed} resin refilled!"
            alt_ctx = await copy_context_with(ctx, author=ctx.author, content=command_string)
            await alt_ctx.command.invoke(alt_ctx)
        finally:
            await msg.delete()


def setup(bot):
    bot.add_cog(Genshin(bot))
