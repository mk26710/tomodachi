#  Copyright (c) 2020 — present, snezhniy.
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import asyncio

import discord
from discord.ext import commands
from asyncpg.exceptions import UniqueViolationError

from tomodachi.core import CogMixin, TomodachiContext
from tomodachi.utils.icons import i


class Owner(CogMixin, icon=discord.PartialEmoji(name="developer", id=853555901050781696)):
    def __init__(self, /, tomodachi):
        super().__init__(tomodachi)
        self.deletion_emoji_detector = i.store["fuck"]

    async def cog_check(self, ctx: TomodachiContext):
        return await self.bot.is_owner(ctx.author)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if self.deletion_emoji_detector.id == payload.emoji.id and payload.user_id == self.bot.owner_id:
            c = self.bot.get_channel(payload.channel_id) or await self.bot.fetch_channel(payload.channel_id)
            m = await c.fetch_message(payload.message_id)

            if m.author.id == self.bot.user.id:
                await m.delete()

    @commands.command(aliases=["block", "bl"])
    async def blacklist(self, ctx: TomodachiContext, target: discord.User, *, reason: str = "Just because."):
        async with self.bot.db.pool.acquire() as conn:
            async with conn.transaction():
                query = "INSERT INTO blacklisted (user_id, reason) VALUES ($1, $2);"

                try:
                    await conn.execute(query, target.id, reason)
                except UniqueViolationError:
                    await ctx.send(f":thinking_face: **{target}** (`{target.id}`) is already blacklisted.")
                else:
                    await ctx.send(f":ok_hand: **{target}** (`{target.id}`) is blacklisted now.")

            await self.bot.fetch_blacklist()

    @commands.command(aliases=["unblock", "unbl"])
    async def unblacklist(self, ctx: TomodachiContext, target: discord.User):
        async with self.bot.db.pool.acquire() as conn:
            query = "DELETE FROM blacklisted WHERE user_id = $1 RETURNING true;"
            value = await conn.fetchval(query, target.id)

        if value:
            await self.bot.fetch_blacklist()
            await ctx.send(f":ok_hand: **{target}** (`{target.id}`) is not blacklisted anymore.")
        else:
            await ctx.send(f":thinking_face: **{target}** (`{target.id}`) is not on the blacklist.")

    @commands.command()
    async def steal_avatar(self, ctx: TomodachiContext, user: discord.User):
        """Sets someone's avatar as bots' avatar"""
        if not user.avatar:
            return await ctx.send("that entity doesnt have avatar")

        embed = discord.Embed(colour=0x2F3136)
        embed.set_image(url=user.avatar.url)

        await ctx.send(embed=embed, content="Are you sure that you want me to use this as avatar?\nSay `yes` or `no`.")

        def check(m):
            return m.author.id == ctx.author.id and str(m.content).lower() in ("yes", "no")

        try:
            message = await self.bot.wait_for("message", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("Timed out.")
        else:
            if message.content.lower() == "yes":
                b = await user.avatar.read()

                await self.bot.user.edit(avatar=b)
                await ctx.send(":ok_hand:")
            else:
                await ctx.send("Aborted.")


def setup(bot):
    bot.add_cog(Owner(bot))
