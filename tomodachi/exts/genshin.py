#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from typing import Callable, Optional, Coroutine
from datetime import datetime, timedelta

import discord
from discord.ext import commands

from tomodachi.core import CogMixin, TomodachiContext
from tomodachi.utils import timestamp
from tomodachi.exts.reminders import Reminder
from tomodachi.utils.converters import uint


class CreateReminderView(discord.ui.View):
    def __init__(self, callback: Callable[[discord.Interaction], Coroutine], *, timeout=60.0):
        self.callback = callback

        super().__init__(timeout=timeout)

    @discord.ui.button(label="Remind me about that")
    async def btn(self, _, interaction: discord.Interaction):
        await self.callback(interaction, self.stop)


class Genshin(CogMixin, icon=discord.PartialEmoji(name="cryo", id=853553127541702679)):
    def reminder_callback(self, message: discord.Message, delta: timedelta, amount: int):
        async def callback(interaction: discord.Interaction, stop: Callable):
            if interaction.user.id != message.author.id:
                return await interaction.response.send("You can't interact with others buttons!", ephemeral=True)

            now = datetime.utcnow()
            trigger_at = now + delta

            reminder = Reminder(
                created_at=now,
                trigger_at=trigger_at,
                author_id=message.author.id,
                guild_id=message.guild.id,
                channel_id=message.channel.id,
                message_id=message.id,
                contents=f"Genshin Impact: you now have {amount} resin!",
            )

            reminder = await self.bot.get_cog("Reminders").create_reminder(reminder)

            identifier = ""
            if reminder.id:
                identifier = f" (#{reminder.id})"

            when = timestamp(trigger_at)

            await interaction.response.send_message(
                f":ok_hand: I will remind you about this on {when}{identifier}", ephemeral=True
            )
            stop()

        return callback

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

        delta = timedelta(minutes=((needed - current) * 8))
        humanized = timestamp(datetime.now() + delta)

        if not remind:
            await ctx.send(f"You will have {needed} resin **{humanized:R}**.")
        else:
            view = CreateReminderView(self.reminder_callback(ctx.message, delta, needed))
            await ctx.send(f"You will have {needed} resin **{humanized:R}**.", view=view)


def setup(bot):
    bot.add_cog(Genshin(bot))
