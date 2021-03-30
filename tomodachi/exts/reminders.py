#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

import asyncio
import logging
from dataclasses import dataclass, fields
from datetime import datetime, timedelta
from typing import Mapping, Optional

import discord
import humanize
from discord.ext import commands, tasks

from tomodachi.core import Tomodachi, TomodachiContext


@dataclass(frozen=True)
class Reminder:
    id: Optional[int]  # None in cases when being created by a user
    created_at: datetime
    trigger_at: datetime
    author_id: int
    guild_id: Optional[int]
    channel_id: int
    message_id: int
    contents: str

    @classmethod
    def from_dict(cls, data: Mapping):
        class_fields = {f.name for f in fields(cls)}
        kwargs = {k: v for k, v in data.items() if k in class_fields}

        for field in class_fields:
            kwarg = kwargs.get(field)
            if not kwarg:
                kwargs |= {field: None}

        return Reminder(**kwargs)


class Reminders(commands.Cog):
    def __init__(self, bot: Tomodachi):
        self.bot = bot
        # this Event will be sort of a "pause" for the dispatcher loop
        self.reminder_created = asyncio.Event()
        self.dispatcher.start()

    def cog_unload(self):
        self.dispatcher.cancel()

    @commands.Cog.listener()
    async def on_triggered_reminder(self, reminder: Reminder):
        await self.bot.wait_until_ready()

        try:
            channel = self.bot.get_channel(reminder.id) or await self.bot.fetch_channel(reminder.channel_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return

        try:
            author = self.bot.get_user(reminder.author_id) or self.bot.fetch_user(reminder.author_id)
        except discord.NotFound:
            return

        now = datetime.utcnow()
        delta = now - reminder.created_at
        when = await asyncio.to_thread(humanize.naturaldelta, delta)

        jump_url = "https://discord.com/channels/{0.guild_id}/{0.channel_id}/{0.message_id}".format(reminder)

        embed = discord.Embed()
        embed.title = f"Reminder #{reminder.id}" if reminder.id is not None else "Short Reminder"
        embed.description = f"You asked me {when} ago [here]({jump_url}) to remind you of:\n\n{reminder.contents}"
        embed.set_footer(text=f"Reminder for {author}", icon_url=f"{author.avatar_url}")

        await channel.send(f"{author.mention}", embed=embed, allowed_mentions=discord.AllowedMentions(users=True))

    @tasks.loop()
    async def dispatcher(self):
        logging.debug("FETCHING REMINDERS...")
        reminder = await self.get_reminder()

        if not reminder:
            logging.debug(f"DISPATCHER HAVE NOT FOUND ANY REMINDERS, CANCELLING THE TASK...")
            # If there's no reminder, we wait for it's creation
            await self.reminder_created.wait()
            self.dispatcher.cancel()
        else:
            logging.debug(f"DISPATCHER FOUND A REMINDER #{reminder.id}, SLEEPING UNTIL EXPIRES...")
            now = datetime.utcnow()
            if reminder.trigger_at >= now:
                await discord.utils.sleep_until(reminder.trigger_at)

            logging.debug(f"TRIGGERING EVENT FOR #{reminder.id}")
            await self.trigger_reminder(reminder)
            self.reminder_created.clear()

    async def get_reminder(self):
        async with self.bot.pg.pool.acquire() as conn:
            query = (
                "SELECT * FROM reminders WHERE trigger_at < (current_date + $1::interval) ORDER BY trigger_at LIMIT 1;"
            )
            stmt = await conn.prepare(query)
            record = await stmt.fetchrow(timedelta(days=7))

        if not record:
            return None

        return Reminder.from_dict(record)

    async def trigger_reminder(self, reminder: Reminder):
        await self.bot.pg.pool.execute("DELETE FROM reminders WHERE id = $1;", reminder.id)
        self.bot.dispatch("triggered_reminder", reminder=reminder)

    async def trigger_short_reminder(self, seconds, reminder: Reminder):
        await asyncio.sleep(seconds)
        self.bot.dispatch("triggered_reminder", reminder=reminder)

    async def create_reminder(self, reminder: Reminder):
        now = datetime.utcnow()
        delta = (reminder.trigger_at - now).total_seconds()

        if delta <= 60:
            asyncio.create_task(self.trigger_short_reminder(delta, reminder))
            return reminder

        async with self.bot.pg.pool.acquire() as con:
            async with con.transaction():
                query = (
                    "INSERT INTO reminders (trigger_at, author_id, guild_id, channel_id, message_id, contents) "
                    "VALUES ($1, $2, $3, $4, $5, $6) RETURNING *;"
                )

                inserted_row = await con.fetchrow(
                    query,
                    reminder.trigger_at,
                    reminder.author_id,
                    reminder.guild_id,
                    reminder.channel_id,
                    reminder.message_id,
                    reminder.contents,
                )

        reminder = Reminder.from_dict(inserted_row)

        # Once the new reminder created dispatcher has to be restarted
        self.dispatcher.restart()
        self.reminder_created.set()

        return reminder

    @commands.group(aliases=("r", "reminders"))
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def reminder(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            await ctx.send(":x: You haven't used any subcommand, please, see help.")

    @reminder.command(name="add")
    async def reminder_add(self, ctx: TomodachiContext, seconds_to_wait: int, *, text: str):
        now = datetime.utcnow()
        trigger_at = now + timedelta(seconds=seconds_to_wait)

        reminder = Reminder.from_dict(
            {
                "created_at": now,
                "trigger_at": trigger_at,
                "author_id": ctx.author.id,
                "guild_id": ctx.guild.id,
                "channel_id": ctx.channel.id,
                "message_id": ctx.message.id,
                "contents": text,
            }
        )

        reminder = await self.create_reminder(reminder)

        delta = reminder.trigger_at - reminder.created_at
        when = await asyncio.to_thread(humanize.naturaldelta, delta)

        identifier = ""
        if reminder.id:
            identifier = f" (#{reminder.id})"

        await ctx.send(f":ok_hand: I will remind you about this in {when}" + identifier)


def setup(bot):
    bot.add_cog(Reminders(bot))
