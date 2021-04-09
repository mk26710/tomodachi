#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
#  Heavily inspired by https://github.com/Rapptz/RoboDanny <

import asyncio
from typing import Optional
from datetime import datetime

import attr
import discord
import humanize
from loguru import logger
from sqlalchemy import text
from discord.ext import commands
from more_itertools import chunked

from tomodachi.core import CogMixin, TomodachiContext
from tomodachi.utils.database import reminders as table
from tomodachi.utils.converters import EntryID, TimeUnit


def reminders_limit():
    async def predicate(ctx: TomodachiContext):
        async with ctx.bot.pool.acquire() as conn:
            query = "SELECT count(id) FROM reminders WHERE author_id = $1;"
            stmt = await conn.prepare(query)
            count = await stmt.fetchval(ctx.author.id)

        if count >= 250:
            raise commands.CheckFailure("Reached the limit of 250 reminders.")

        return True

    return commands.check(predicate)


@attr.s(slots=True)
class Reminder:
    # Required attrs that needs to be passed in the constructor
    trigger_at = attr.ib(type=datetime)
    author_id = attr.ib(type=int)
    channel_id = attr.ib(type=int)
    message_id = attr.ib(type=int)

    # Attrs with default values
    id = attr.ib(type=int, default=None)
    guild_id = attr.ib(type=int, default=None)
    contents = attr.ib(type=str, default="...", repr=False)
    created_at = attr.ib(type=datetime, default=attr.Factory(datetime.utcnow))


class Reminders(CogMixin):
    def __init__(self, /, tomodachi):
        super().__init__(tomodachi)
        self.cond = asyncio.Condition()
        self.task = asyncio.create_task(self.dispatcher())
        self.active: Optional[Reminder] = None

    def cog_unload(self):
        self.task.cancel()

    async def dispatcher(self):
        async with self.cond:
            logger.log("REMINDERS", "Getting reminder...")
            reminder = self.active = await self.get_reminder()

            if not reminder:
                logger.log("REMINDERS", "Reminder not found, pausing the task...")
                await self.cond.wait()
                await self.reschedule()

            logger.log("REMINDERS", f"Reminder #{reminder.id} found, sleeping until expires...")
            now = datetime.utcnow()
            if reminder.trigger_at >= now:
                await discord.utils.sleep_until(reminder.trigger_at)

            await self.trigger_reminder(reminder)
            logger.log("REMINDERS", "Triggered the reminder event")
            await self.reschedule()

    async def reschedule(self):
        if not self.task.cancelled() or self.task.done():
            logger.log("REMINDERS", "Cancelling dispatcher...")
            self.task.cancel()

        logger.log("REMINDERS", "Starting dispatcher...")
        self.task = asyncio.create_task(self.dispatcher())

        async with self.cond:
            logger.log("REMINDERS", "Notifying waiting thread...")
            self.cond.notify_all()

    async def get_reminder(self):
        async with self.bot.pool.acquire() as conn:
            query = """SELECT * 
                FROM reminders 
                WHERE (CURRENT_TIMESTAMP + '28 days'::interval) > reminders.trigger_at
                ORDER BY reminders.trigger_at 
                LIMIT 1;"""
            stmt = await conn.prepare(query)
            record = await stmt.fetchrow()

        if not record:
            return None

        return Reminder(**record)

    async def trigger_reminder(self, reminder: Reminder):
        await self.bot.pool.execute("DELETE FROM reminders WHERE id = $1;", reminder.id)
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

        async with self.bot.db.transaction():
            query = table.insert().returning(text("*"))
            values = attr.asdict(reminder, filter=lambda _, v: v is not None)
            inserted_row = await self.bot.db.fetch_one(query, values)

        reminder = Reminder(**inserted_row)
        # Once the new reminder created dispatcher has to be restarted
        # but only if the currently active reminder happens later than new
        if (self.active and self.active.trigger_at >= reminder.trigger_at) or self.active is None:
            logger.log("REMINDERS", "New reminder triggers earlier, rescheduling")
            asyncio.create_task(self.reschedule())

        return reminder

    @commands.Cog.listener()
    async def on_triggered_reminder(self, reminder: Reminder):
        await self.bot.wait_until_ready()

        try:
            channel = self.bot.get_channel(reminder.id) or await self.bot.fetch_channel(reminder.channel_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            channel = None

        try:
            author = self.bot.get_user(reminder.author_id) or await self.bot.fetch_user(reminder.author_id)
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

        try:
            # in case of channel gets deleted, DM the user
            await (channel or author).send(
                content=f"{author.mention}",
                embed=embed,
                allowed_mentions=discord.AllowedMentions(users=True),
            )
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.group(aliases=("r", "reminders"), help="Time based mentions")
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def reminder(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            await ctx.send(":x: You haven't used any subcommand, please, see help.")

    @commands.is_owner()
    @reminder.command(name="active")
    async def reminder_get_active(self, ctx: TomodachiContext):
        await ctx.send(f"Current active reminder: {self.active}")

    @reminders_limit()
    @reminder.command(name="add", aliases=("new", "a"), help="Create new reminder")
    async def reminder_add(self, ctx: TomodachiContext, to_wait: TimeUnit, *, text: str = "..."):
        now = datetime.utcnow()
        trigger_at = now + to_wait

        reminder = Reminder(
            created_at=now,
            trigger_at=trigger_at,
            author_id=ctx.author.id,
            guild_id=ctx.guild.id,
            channel_id=ctx.channel.id,
            message_id=ctx.message.id,
            contents=text,
        )

        reminder = await self.create_reminder(reminder)

        delta = reminder.trigger_at - reminder.created_at
        when = await asyncio.to_thread(humanize.precisedelta, delta, format="%0.0f")

        identifier = ""
        if reminder.id:
            identifier = f" (#{reminder.id})"

        await ctx.send(f":ok_hand: I will remind you about this in {when}" + identifier)

    @reminder.command(name="list", aliases=["ls"])
    async def reminder_list(self, ctx: TomodachiContext):
        now = datetime.utcnow()

        query = table.select().where(table.c.author_id == ctx.author.id).order_by(table.c.trigger_at).limit(500)
        rows = await self.bot.db.fetch_all(query)

        reminders = tuple(Reminder(**row) for row in rows)
        if not reminders:
            return await ctx.send(":x: You don't have any reminders!")

        lines = []
        for reminder in reminders:
            when = await asyncio.to_thread(humanize.precisedelta, reminder.trigger_at - now, format="%0.0f")
            line = f"**(#{reminder.id})** in {when}"
            lines.append(line)

        entries = ["\n".join(chunk) for chunk in chunked(lines, 10)]

        menu = ctx.new_menu(entries)
        menu.embed.set_author(name=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)

        await menu.start(ctx)

    @reminder.command(name="info", aliases=["check", "view"], help="Shows content of the specified reminder")
    async def reminder_info(self, ctx: TomodachiContext, reminder_id: EntryID):
        query = table.select().where(table.c.author_id == ctx.author.id).where(table.c.id == reminder_id)

        row = await self.bot.db.fetch_one(query)
        if not row:
            return await ctx.send(f":x: You don't have reminder with ID `#{reminder_id}`.")

        reminder = Reminder(**row)

        embed = discord.Embed()
        embed.title = f"Reminder #{reminder.id}"
        embed.description = f"{reminder.contents[0:2000]}"
        embed.timestamp = reminder.trigger_at
        embed.set_footer(text=f"{ctx.author}", icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed, delete_after=120.0)

    @reminder.command(name="remove", aliases=["rmv", "delete", "del"], help="Remove some reminder from your list")
    async def reminder_remove(self, ctx: TomodachiContext, reminder_id: EntryID):
        query = (
            table.delete()
            .where(table.c.author_id == ctx.author.id)
            .where(table.c.id == reminder_id)
            .returning(text("*"))
        )

        is_deleted = await self.bot.db.fetch_val(query)
        if not is_deleted:
            return await ctx.send(f":x: Nothing happened. Most likely you don't have a reminder `#{reminder_id}`.")

        await self.reschedule()
        await ctx.send(f":ok_hand: Successfully delete `#{reminder_id}` reminder.")

    @reminder.command(name="purge", aliases=["clear"])
    async def reminder_purge(self, ctx: TomodachiContext):
        query = table.delete().where(table.c.author_id == ctx.author.id).returning(table.c.id)

        rows = await self.bot.db.fetch_all(query)
        count = len(rows)
        if not count:
            return await ctx.send(":x: Nothing happened. Looks like you have no reminders.")

        await self.reschedule()
        await ctx.send(f":ok_hand: Deleted `{count}` reminder(s) from your list.")


def setup(bot):
    bot.add_cog(Reminders(bot))
