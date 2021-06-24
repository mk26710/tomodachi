#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
#  Heavily inspired by https://github.com/Rapptz/RoboDanny <

import discord
from discord.ext import commands
from more_itertools import chunked

from tomodachi.core import CogMixin, TomodachiContext
from tomodachi.utils import helpers
from tomodachi.core.enums import ActionType
from tomodachi.core.actions import Action
from tomodachi.utils.timestamp import timestamp
from tomodachi.utils.converters import EntryID, TimeUnit


def reminders_limit():
    async def predicate(ctx: TomodachiContext):
        async with ctx.bot.pool.acquire() as conn:
            query = "SELECT count(id) FROM actions WHERE author_id = $1 AND sort = 'REMINDER';"
            stmt = await conn.prepare(query)
            count = await stmt.fetchval(ctx.author.id)

        if count >= 250:
            raise commands.CheckFailure("Reached the limit of 250 reminders.")

        return True

    return commands.check(predicate)


class Reminders(CogMixin, icon=discord.PartialEmoji(name=":stopwatch:")):
    @commands.Cog.listener()
    async def on_triggered_action(self, action: Action):
        await self.bot.wait_until_ready()

        if action.sort is not ActionType.REMINDER:
            return

        try:
            channel = self.bot.get_channel(action.id) or await self.bot.fetch_channel(action.channel_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            channel = None

        try:
            author = self.bot.get_user(action.author_id) or await self.bot.fetch_user(action.author_id)
        except discord.NotFound:
            return

        when = timestamp(action.created_at)
        jump_url = "https://discord.com/channels/{0.guild_id}/{0.channel_id}/{0.message_id}".format(action)

        embed = discord.Embed()
        embed.title = f"Reminder #{action.id}" if action.id is not None else "Short Reminder"
        embed.description = f"You asked me on {when:F} [here]({jump_url}) to remind you:\n{action.extra['content']}"
        embed.set_footer(text=f"Reminder for {author}", icon_url=helpers.avatar_or_default(author).url)

        try:
            # in case of channel gets deleted, DM the user
            await (channel or author).send(
                content=f"{author.mention}",
                embed=embed,
                allowed_mentions=discord.AllowedMentions(users=True),
            )
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.group(aliases=["r", "reminders"], help="Time based mentions")
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def reminder(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            await ctx.send(":x: You haven't used any subcommand, please, see help.")

    @reminders_limit()
    @reminder.command(name="add", aliases=["new", "a"], help="Create new reminder")
    async def reminder_add(self, ctx: TomodachiContext, to_wait: TimeUnit, *, text: str = "..."):
        now = helpers.utcnow()
        trigger_at = now + to_wait

        action = Action(
            sort=ActionType.REMINDER,
            trigger_at=trigger_at,
            author_id=ctx.author.id,
            guild_id=ctx.guild.id,
            channel_id=ctx.channel.id,
            message_id=ctx.message.id,
            extra={"content": text},
        )

        action = await self.bot.actions.create_action(action)
        when = timestamp(action.trigger_at)

        identifier = ""
        if action.id:
            identifier = f" (#{action.id})"

        await ctx.send(f":ok_hand: I will remind you about this at {when:F}" + identifier)

    @reminder.command(name="list", aliases=["ls"])
    async def reminder_list(self, ctx: TomodachiContext):
        async with self.bot.db.pool.acquire() as conn:
            query = "SELECT * FROM actions WHERE author_id=$1 AND sort='REMINDER' LIMIT 500;"
            stmt = await conn.prepare(query)
            rows = await stmt.fetch(ctx.author.id)

        actions = tuple(Action(**row) for row in rows)
        if not actions:
            return await ctx.send(":x: You don't have any reminders!")

        lines = []
        for reminder in actions:
            when = timestamp(reminder.trigger_at)
            line = f"**(#{reminder.id})** on {when:F}"
            lines.append(line)

        entries = ["\n".join(chunk) for chunk in chunked(lines, 10)]

        menu = ctx.new_menu(entries)
        menu.embed.set_author(name=f"Requested by {ctx.author}", icon_url=helpers.avatar_or_default(ctx.author).url)

        await menu.start(ctx)

    @reminder.command(name="info", aliases=["check", "view"], help="Shows content of the specified reminder")
    async def reminder_info(self, ctx: TomodachiContext, reminder_id: EntryID):
        async with self.bot.db.pool.acquire() as conn:
            query = "SELECT * FROM actions WHERE author_id=$1 AND id=$2 AND sort='REMINDER' LIMIT 1;"
            row = await conn.fetchrow(query, ctx.author.id, reminder_id)

        if not row:
            return await ctx.send(f":x: You don't have reminder with ID `#{reminder_id}`.")

        action = Action(**row)

        embed = discord.Embed()
        embed.title = f"Reminder #{action.id}"
        embed.description = f"{action.extra['content'][0:2000]}"
        embed.timestamp = action.trigger_at
        embed.set_footer(text=f"{ctx.author}", icon_url=helpers.avatar_or_default(ctx.author).url)

        await ctx.send(embed=embed, delete_after=120)

    @reminder.command(name="remove", aliases=["rmv", "delete", "del"], help="Remove some reminder from your list")
    async def reminder_remove(self, ctx: TomodachiContext, reminder_id: EntryID):
        async with self.bot.db.pool.acquire() as conn:
            query = "DELETE FROM actions WHERE author_id=$1 AND id=$2 AND sort='REMINDER' RETURNING true;"
            value = await conn.fetchval(query, ctx.author.id, reminder_id)

        if not value:
            return await ctx.send(f":x: Nothing happened. Most likely you don't have a reminder `#{reminder_id}`.")

        await self.bot.actions.reschedule()
        await ctx.send(f":ok_hand: Successfully deleted `#{reminder_id}` reminder.")

    @reminder.command(name="purge", aliases=["clear"])
    async def reminder_purge(self, ctx: TomodachiContext):
        async with self.bot.db.pool.acquire() as conn:
            query = """WITH deleted AS (DELETE FROM actions WHERE author_id=$1 AND sort='REMINDER' RETURNING *) 
                SELECT count(*) 
                FROM deleted;"""
            stmt = await conn.prepare(query)
            count: int = await stmt.fetchval(ctx.author.id)

        if not count:
            return await ctx.send(":x: Nothing happened. Looks like you have no reminders.")

        await self.bot.actions.reschedule()
        await ctx.send(f":ok_hand: Deleted `{count}` reminder(s) from your list.")


def setup(bot):
    bot.add_cog(Reminders(bot))
