#  Copyright (c) 2020 — present, snezhniy.
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

import discord
from discord.ext import commands

from tomodachi.core import CogMixin
from tomodachi.utils import helpers, timestamp
from tomodachi.core.enums import ActionType
from tomodachi.core.actions import Action


class Events(CogMixin):
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await self.bot.db.store_guild(guild.id)

    @commands.Cog.listener()
    async def on_triggered_action(self, action: Action):
        await self.bot.wait_until_ready()

        if action.action_type is not ActionType.REMINDER:
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


def setup(bot):
    bot.add_cog(Events(bot))
