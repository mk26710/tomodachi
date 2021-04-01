#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

import discord
from discord.ext import commands
from sqlalchemy.dialects.postgresql import insert

from tomodachi.core import Tomodachi
from tomodachi.utils.database import guilds


class Events(commands.Cog):
    def __init__(self, bot: Tomodachi):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        stmt = insert(guilds).values(guild_id=guild.id).on_conflict_do_nothing()
        await self.bot.db.execute(stmt)


def setup(bot):
    bot.add_cog(Events(bot))
