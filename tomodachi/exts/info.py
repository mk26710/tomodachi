#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

import io
from collections import Counter
from datetime import datetime, timezone
from typing import Union

import arrow
import discord
import humanize
from aiohttp import ClientResponseError
from discord.ext import flags, commands

from tomodachi.core import CogMixin, TomodachiContext
from tomodachi.utils import HUMANIZED_ACTIVITY, make_progress_bar, helpers


class Info(CogMixin):
    @commands.cooldown(1, 3, commands.BucketType.user)
    @flags.add_flag("--steal", "-s", action="store_true")
    @commands.command(cls=flags.FlagCommand, aliases=["avy", "av"], help="Provides you an avatar of some discord user")
    async def avatar(self, ctx: TomodachiContext, user: discord.User = None, **options):
        user = user or ctx.author

        urls = " | ".join(f"[{ext}]({user.avatar.with_static_format(format=ext)})" for ext in ("png", "jpeg", "webp"))
        if user.avatar.is_animated():
            urls += f" | [gif]({user.avatar.url})"

        embed = discord.Embed(
            colour=0x2F3136,
            description=urls,
            title=f"{user} ({user.id})",
        )
        embed.set_image(url=f"{user.avatar.url}")

        if not options["steal"]:
            return await ctx.send(embed=embed)

        buf = io.BytesIO()
        await user.avatar.save(buf)

        ext = ".gif" if user.avatar.is_animated() else ".png"
        f = discord.File(buf, user.name + user.discriminator + ext)

        await ctx.send(content=f"Re-uploaded avatar of {user} (`{user.id}`)", file=f)

    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.command(aliases=["ui", "memberinfo", "mi"], help="Shows general information about discord users")
    async def userinfo(self, ctx: TomodachiContext, user: Union[discord.Member, discord.User] = None):
        # if target user not specified use author
        user = user or ctx.author

        embed = discord.Embed(colour=0x5865F2)
        embed.set_thumbnail(url=f"{user.avatar.url}")

        embed.add_field(name="Username", value=f"{user}")
        embed.add_field(name="ID", value=f"{user.id}")

        if user.public_flags.value > 0:
            embed.add_field(name="Badges", value="\n".join(helpers.humanize_flags(user.public_flags)), inline=False)

        if isinstance(user, discord.Member):
            embed.colour = user.colour

            for activity in user.activities:
                if isinstance(activity, discord.Spotify):
                    track_url = f"https://open.spotify.com/track/{activity.track_id}"
                    artists = ", ".join(activity.artists)
                    value = f"[{artists} — {activity.title}]({track_url})"

                    embed.add_field(name="Listening", value=value, inline=False)

                else:
                    embed.add_field(name=f"{HUMANIZED_ACTIVITY[activity.type]}", value=f"{activity.name}", inline=False)

            if len(user.roles) > 1:
                roles = ", ".join(reversed(tuple(r.mention for r in user.roles if "everyone" not in r.name)))
                embed.add_field(name="Roles", value=roles, inline=False)

            joined_at = arrow.get(user.joined_at)
            joined = "%s (`%s`)" % (humanize.naturaltime(arrow.utcnow() - joined_at), joined_at)
            embed.add_field(name="Join date", value=f"{self.bot.icon('slowmode')} {joined}", inline=False)

        created_at = arrow.get(user.created_at)
        created = "%s (`%s`)" % (humanize.naturaltime(arrow.utcnow() - created_at), created_at)
        embed.add_field(name="Creation date", value=f"{self.bot.icon('slowmode')} {created}", inline=False)

        if await self.bot.is_owner(user):
            embed.description = f"{ctx.icon['developer']} **Bot Admin**"

        await ctx.send(embed=embed)

    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.command(aliases=["si"], help="Brief information about discord servers that I am a part of")
    async def serverinfo(self, ctx: TomodachiContext, server: discord.Guild = None):
        guild = server or ctx.guild

        embed = discord.Embed(title=f"{guild.name} ({guild.id})")
        embed.description = f"{ctx.icon['owner']} {guild.owner} (`{guild.owner_id}`)"
        if guild.description:
            embed.description = f"{guild.description}\n\n{embed.description}"

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        features = ""
        for feature in guild.features:
            feature = str(feature).replace("_", " ").lower().title()
            features = f"{features}\n{ctx.icon['roundedcheck']} {feature}"

        if features:
            embed.add_field(name="Features", value=features)

        statuses_count = Counter(m.status.name for m in guild.members)
        statuses = " ".join(f"{ctx.icon[s]} {c}" for s, c in statuses_count.most_common())
        if statuses:
            embed.add_field(name="Members", value=statuses)

        specials_count = Counter(f.name for m in guild.members for f in m.public_flags.all())
        flagged_members = " ".join(f"{ctx.icon[f]} {c}" for f, c in specials_count.most_common())
        if flagged_members:
            embed.add_field(name="Flags Stats", value=flagged_members, inline=False)

        created_at = arrow.get(guild.created_at)
        created = "%s (`%s`)" % (humanize.naturaltime(arrow.utcnow() - created_at), created_at)
        embed.add_field(name="Server creation date", value=f"{ctx.icon['slowmode']} {created}", inline=False)

        await ctx.send(embed=embed)

    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.command(aliases=["spot"], help="Checks what discord user is listening to")
    async def spotify(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        activity = discord.utils.find(lambda a: isinstance(a, discord.Spotify), member.activities)

        if not activity:
            return await ctx.send(f"{member} is not using Spotify right now.")

        track_url = f"https://open.spotify.com/track/{activity.track_id}"

        current_pos = datetime.utcnow() - activity.start
        bar = make_progress_bar(
            current_pos.seconds,
            activity.duration.seconds,
            length=18,
            in_brackets=True,
            emptiness="#",
        )
        elapsed = "%02d:%02d" % divmod(current_pos.seconds, 60)
        duration = "%02d:%02d" % divmod(activity.duration.seconds, 60)
        progression = f"{elapsed} `{bar}` {duration}"

        e = discord.Embed(colour=0x1ED760)
        e.set_author(name=f"{ctx.author.name}", icon_url=self.bot.icon("spotify").url)
        e.add_field(name="Title", value=f"[{activity.title}]({track_url})")
        e.add_field(name="Artists", value=", ".join(activity.artists))
        e.add_field(name="Album", value=f"{activity.album}")
        e.add_field(name="Player", value=progression, inline=False)
        e.set_image(url=activity.album_cover_url)

        await ctx.send(embed=e)

    @commands.cooldown(1, 3.0, commands.BucketType.user)
    @commands.command()
    async def pypi(self, ctx: TomodachiContext, pkg: str = None):
        """Lookup for a package on PyPI"""
        if not pkg:
            return await ctx.send(":x: You have to provide a package name.")

        url = f"https://pypi.org/pypi/{pkg}/json"
        async with self.bot.session.get(url) as resp:
            try:
                resp.raise_for_status()
            except ClientResponseError:
                return await ctx.send(f":x: Package `{pkg}` not found")
            else:
                data = await resp.json()
                info = data["info"]

        embed = discord.Embed(
            description=info["summary"],
            title=f"{pkg} {info['version']}",
            url=info["package_url"],
        )

        embed.add_field(name="Author", value=info["author"] or "not provided", inline=False)
        embed.add_field(name="Author Email", value=info["author_email"] or "not provided", inline=False)
        embed.add_field(name="License", value=info["license"] or "not provided", inline=False)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Info(bot))
