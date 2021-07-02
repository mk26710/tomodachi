#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import Union

import discord
from discord.ext import commands
from datetime import timedelta

from tomodachi.core import CogMixin
from tomodachi.utils import helpers, timestamp
from tomodachi.core.enums import ActionType, InfractionType
from tomodachi.core.actions import Action


class Events(CogMixin):
    async def _disable_infractions_from_audit(self, guild_id: int):
        async with self.bot.cache.fresh_cache(guild_id):
            async with self.bot.db.pool.acquire() as conn:
                query = "update mod_settings set audit_infractions=false where guild_id=$1;"
                await conn.execute(query, guild_id)

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

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: Union[discord.User, discord.Member]):
        now = helpers.utcnow()
        settings = await self.bot.cache.get_settings(guild.id)

        if not settings.audit_infractions:
            return

        # If bot doesn't have permissions to read audit logs
        # better to disable infractions from manual actions
        if not guild.me.guild_permissions.view_audit_log:
            return await self._disable_infractions_from_audit(guild.id)

        # for safety, fetch only entries that were created in past 5 minutes
        entries = await guild.audit_logs(
            action=discord.AuditLogAction.ban,
            after=now - timedelta(minutes=5),
            oldest_first=False,
            limit=1,
        ).flatten()

        if not entries:
            return
        entry = entries[0]

        if entry.target.id != user.id:
            raise Exception("Fetched audit entry is not about the banned user.")

        await self.bot.infractions.create(
            inf_type=InfractionType.PERMABAN,
            expires_at=None,
            guild_id=guild.id,
            mod_id=entry.user.id,
            target_id=entry.target.id,
            reason=entry.reason or "Manual ban with no reason.",
            create_action=False,
        )

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        now = helpers.utcnow()
        settings = await self.bot.cache.get_settings(guild.id)

        if not settings.audit_infractions:
            return

        if not guild.me.guild_permissions.view_audit_log:
            return await self._disable_infractions_from_audit(guild.id)

        entries = await guild.audit_logs(
            after=now - timedelta(minutes=5),
            action=discord.AuditLogAction.unban,
            oldest_first=False,
            limit=1,
        ).flatten()

        if not entries:
            return
        entry = entries[0]

        if entry.target.id != user.id:
            raise Exception("Fetched audit entry is not about the unbanned user.")

        await self.bot.infractions.create(
            inf_type=InfractionType.UNBAN,
            expires_at=None,
            guild_id=guild.id,
            mod_id=entry.user.id,
            target_id=entry.target.id,
            reason="Manual unban.",
            create_action=False,
        )


def setup(bot):
    bot.add_cog(Events(bot))
