#  Copyright (c) 2020 — present, Kirill M.
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import Union

import discord
from discord.ext import commands

from tomodachi.core import CogMixin
from tomodachi.utils import helpers, timestamp
from tomodachi.core.enums import ActionType, InfractionType
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

    async def _disable_audit_infractions(self, guild_id: int):
        async with self.bot.cache.settings.fresh(guild_id):
            async with self.bot.db.pool.acquire() as conn:
                query = "update mod_settings set audit_infractions=false where guild_id=$1;"
                await conn.execute(query, guild_id)

    @commands.Cog.listener()
    async def on_mod_action(
        self,
        type: InfractionType,
        action: discord.AuditLogAction,
        guild: discord.Guild,
        user: Union[discord.User, discord.Member],
    ):
        settings = await self.bot.cache.settings.get(guild.id)
        if not settings.audit_infractions:
            return

        if not guild.me.guild_permissions.view_audit_log:
            return await self._disable_audit_infractions(guild.id)

        audits = await guild.audit_logs(limit=1, oldest_first=False, action=action).flatten()
        if not audits:
            raise Exception(f"Audit entry was not found for {action.name} of {user.id}")  # noqa
        entry = audits[0]

        # ignore actions of tomodachi bot
        if entry.user.id == self.bot.user.id:
            return

        await self.bot.infractions.create(
            inf_type=type,
            expires_at=None,
            guild_id=guild.id,
            mod_id=entry.user.id,
            target_id=entry.target.id,
            reason=entry.reason or f"Manual {action.name} with no reason.",  # noqa
            create_action=False,
        )

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        self.bot.dispatch(
            "mod_action",
            type=InfractionType.PERMABAN,
            action=discord.AuditLogAction.ban,
            guild=guild,
            user=user,
        )

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        self.bot.dispatch(
            "mod_action",
            type=InfractionType.UNBAN,
            action=discord.AuditLogAction.unban,
            guild=guild,
            user=user,
        )


def setup(bot):
    bot.add_cog(Events(bot))
