#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import asyncio
from typing import Optional
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from jishaku.models import copy_context_with

from tomodachi.core import CogMixin, TomodachiContext
from tomodachi.utils import timestamp
from tomodachi.utils.icons import i
from tomodachi.utils.converters import uint


class Genshin(CogMixin, icon=discord.PartialEmoji(name="cryo", id=853553127541702679)):
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    @commands.command(help="Counts how much time left until your resin refills")
    async def resin(
        self,
        ctx: TomodachiContext,
        current: Optional[uint] = 0,
        needed: Optional[uint] = 160,
        remind: Optional[bool] = False,
    ):
        if current < 0 or current > 160 or needed < current:
            return await ctx.send("You either reached the cap or trying to put invalid amount.")

        delta = timedelta(minutes=((needed - current) * 8))
        humanized = timestamp(datetime.now() + delta)

        to_send = f"You will have **{needed}** resin at {humanized:F}."
        if remind:
            to_send += f"\nReact with {i:slowmode} to create a reminder."
        else:
            return await ctx.send(to_send)

        msg = await ctx.send(to_send)
        await msg.add_reaction(i("slowmode"))

        def check(r, user):
            return user.id == ctx.author.id and r.emoji.id == i("slowmode").id

        try:
            await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
        except asyncio.TimeoutError:
            pass
        else:
            command_string = f"{ctx.prefix}reminder add {delta.seconds}s Genshin Impact: {needed} resin refilled!"
            alt_ctx = await copy_context_with(ctx, author=ctx.author, content=command_string)
            await alt_ctx.command.invoke(alt_ctx)


def setup(bot):
    bot.add_cog(Genshin(bot))
