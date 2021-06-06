#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import asyncio

import discord
from asyncpg.exceptions import UniqueViolationError
from discord.ext import commands

from tomodachi.core import CogMixin, TomodachiContext
from tomodachi.utils.database import blacklisted


class Owner(CogMixin):
    def __init__(self, /, tomodachi):
        super().__init__(tomodachi)
        self.deletion_emoji_detector = self.bot.icon("fuck")

    async def cog_check(self, ctx: TomodachiContext):
        return await self.bot.is_owner(ctx.author)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if self.deletion_emoji_detector.id == payload.emoji.id and payload.user_id == self.bot.owner_id:
            c = self.bot.get_channel(payload.channel_id) or await self.bot.fetch_channel(payload.channel_id)
            m = await c.fetch_message(payload.message_id)

            if m.author.id == self.bot.user.id:
                await m.delete()

    @commands.command()
    async def block(self, ctx: TomodachiContext, target: discord.User, *, reason: str = None):
        try:
            query = blacklisted.insert().values(user_id=target.id, reason=reason or "Because...")
            await self.bot.db.execute(query)
        except UniqueViolationError:
            await ctx.send("user is blocked already")
        else:
            await self.bot.fetch_blacklist()
            await ctx.send(":ok_hand:")

    @commands.command()
    async def unblock(self, ctx: TomodachiContext, target: discord.User):
        query = blacklisted.delete().where(blacklisted.c.user_id == target.id).returning()
        await self.bot.db.execute(query)
        await self.bot.fetch_blacklist()
        await ctx.send(":ok_hand:")

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
